#!/usr/bin/env python3
"""Run the existing HTTPS release verifier against an isolated local Nginx."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import time

from catalog import ROOT
from release_support import extract_release


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-dir", type=Path, required=True)
    args = parser.parse_args()
    for name in ("nginx", "openssl"):
        if not shutil.which(name):
            parser.error(f"Local HTTPS verification requires {name}")
    release = args.release_dir.resolve()
    parent = ROOT / "tmp/release-check"
    parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix=release.name + "-", dir=parent))
    metadata = extract_release(release, work / "site")
    cert, key = work / "test-cert.pem", work / "test-key.pem"
    certificate = subprocess.run(["openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-days", "1",
                                  "-subj", "/CN=localhost", "-addext", "subjectAltName=DNS:localhost",
                                  "-keyout", str(key), "-out", str(cert)], capture_output=True, text=True)
    if certificate.returncode:
        print(certificate.stderr, file=sys.stderr)
        return certificate.returncode
    key.chmod(0o600)
    with socket.socket() as reserved:
        reserved.bind(("127.0.0.1", 0))
        port = reserved.getsockname()[1]
    static = (release / "nginx-static.inc").read_text()
    root_line = "root /srv/reading-notes/current/site;" if metadata.get("schema_version") == 2 else "root /var/www/notes.zzzping.top/current;"
    if static.count(root_line) != 1:
        raise ValueError("Unexpected static root; refusing to start the local server")
    static = static.replace(root_line, f'root "{work / "site"}";')
    (work / "static.inc").write_text(static)
    config = work / "nginx.conf"
    config.write_text(f'''worker_processes 1;
pid "{work / 'nginx.pid'}";
error_log "{work / 'error.log'}";
events {{ worker_connections 64; }}
http {{
    access_log "{work / 'access.log'}";
    server {{
        listen 127.0.0.1:{port} ssl;
        server_name localhost;
        ssl_certificate "{cert}";
        ssl_certificate_key "{key}";
        include "{work / 'static.inc'}";
    }}
}}
''')
    tested = subprocess.run(["nginx", "-t", "-p", str(work) + "/", "-c", str(config)], capture_output=True, text=True)
    if tested.returncode:
        print(tested.stderr, file=sys.stderr)
        return tested.returncode
    output = work / "https-verification.json"
    with (work / "process.log").open("w") as log:
        process = subprocess.Popen(["nginx", "-p", str(work) + "/", "-c", str(config), "-g", "daemon off;"],
                                   stdout=log, stderr=log)
        try:
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError("Temporary Nginx exited; inspect its local error.log")
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                        break
                except OSError:
                    time.sleep(0.1)
            else:
                raise RuntimeError("Temporary Nginx did not start")
            environment = {**os.environ, "SSL_CERT_FILE": str(cert)}
            checked = subprocess.run([sys.executable, ROOT / "deploy/verify_portal.py", "--release-dir", release,
                                      "--origin", f"https://localhost:{port}", "--connect-ip", "127.0.0.1",
                                      "--output", output], cwd=ROOT, env=environment)
            if checked.returncode:
                return checked.returncode
        finally:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
    print(json.dumps({"status": "pass", "release_id": metadata["release_id"],
                      "evidence": output.relative_to(ROOT).as_posix(), "temporary_nginx_stopped": True}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
