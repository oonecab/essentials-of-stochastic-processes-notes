#!/usr/bin/env python3
"""Compare every live HTTPS response with the packaged release fingerprint."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from zoneinfo import ZoneInfo

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("manifest", type=Path)
parser.add_argument("output", type=Path)
parser.add_argument("--address", default="39.106.147.77")
args = parser.parse_args()
manifest = json.loads(args.manifest.read_text())
domain = manifest["domain"]
base = "https://" + domain
records = []


def request(path, scheme="https", method="GET"):
    port = 443 if scheme == "https" else 80
    with tempfile.TemporaryDirectory(prefix="weiss-http-") as temp:
        body, headers = Path(temp) / "body", Path(temp) / "headers"
        result = subprocess.run([
            "curl", "--silent", "--show-error", "--noproxy", "*",
            "--resolve", f"{domain}:{port}:{args.address}", "--max-time", "15",
            "--request", method, "--output", str(body), "--dump-header", str(headers),
            "--write-out", "%{http_code} %{remote_ip}", f"{scheme}://{domain}{path}"
        ], capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stderr.strip())
        status, address = result.stdout.split()
        data = body.read_bytes()
        fields = {}
        for line in headers.read_text().splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                fields[key.lower()] = value.strip()
        return {"path": path, "method": method, "scheme": scheme, "status": int(status),
                "remote_ip": address, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                "headers": fields}


for file in manifest["files"]:
    row = request("/" + file["path"])
    row["expected_sha256"] = file["sha256"]
    row["match"] = row["status"] == 200 and row["sha256"] == file["sha256"]
    records.append(row)
    print(file["path"], row["status"], "MATCH" if row["match"] else "FAIL")
overview = next(f for f in manifest["files"] if f["path"] == "book_overview.html")
root = request("/")
root["match"] = root["status"] == 200 and root["sha256"] == overview["sha256"]
http = request("/", scheme="http")
restrictions = [request(path) for path in ("/.git/config", "/deploy/release.json", "/missing-page.html", "/c/")]
restrictions.append(request("/", method="POST"))
expected = [404, 404, 404, 403, 403]
restriction_passed = all(row["status"] == status for row, status in zip(restrictions, expected))
report = {"checked_at": datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(),
          "release_id": manifest["release_id"], "address": args.address, "base_url": base,
          "files": records, "root": root, "public_http": http, "restrictions": restrictions,
          "all_file_hashes_match": all(r["match"] for r in records),
          "restriction_checks_passed": restriction_passed}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"files_checked": len(records), "all_hashes_match": report["all_file_hashes_match"],
                  "root_match": root["match"], "http_status": http["status"],
                  "restriction_checks_passed": restriction_passed, "output": str(args.output)}, ensure_ascii=False))
if not report["all_file_hashes_match"] or not root["match"] or not restriction_passed:
    raise SystemExit(1)
