"""Real HTTP expectation handshakes for the Chapter 11/12 teaching servers.

The client keeps its sending direction open while awaiting a final response.
These checks intentionally do not replace that wait with a complete body or EOF.
"""
from pathlib import Path
import hashlib
import json
import os
import select
import signal
import socket
import subprocess
import sys
import time


BODY = b'a=2&b=3'
POST_HEAD = (b'POST /cgi-bin/adder HTTP/1.1\r\nHost: localhost\r\n'
             b'Content-Type: application/x-www-form-urlencoded\r\n'
             b'Content-Length: 7\r\n')
EXPECT_HEAD = POST_HEAD + b'Expect: 100-continue\r\n\r\n'


def _cases():
    """Expected statuses are independent protocol fixtures, not parser outputs."""
    return [
        ('expect_headers_only', [EXPECT_HEAD], 417, False),
        ('expect_split_header', [EXPECT_HEAD[:-2], EXPECT_HEAD[-2:]], 417, False),
        ('expect_complete_message', [EXPECT_HEAD + BODY], 417, False),
        ('expect_mixed_case', [EXPECT_HEAD.replace(b'Expect:', b'eXpEcT:')], 417, False),
        ('expect_unsupported_value', [EXPECT_HEAD.replace(b'100-continue', b'other')], 417, False),
        ('expect_head_response', [EXPECT_HEAD.replace(b'POST ', b'HEAD ', 1)], 417, True),
        ('ordinary_split_post', [POST_HEAD + b'\r\na=2', b'&b=3'], 200, False),
        ('ordinary_split_header', [POST_HEAD, b'\r\n' + BODY], 200, False),
        ('ordinary_complete_post', [POST_HEAD + b'\r\n' + BODY], 200, False),
        ('length_trailing_sp', [POST_HEAD.replace(b'Length: 7\r\n', b'Length: 7 \r\n') + b'\r\n' + BODY], 200, False),
        ('length_trailing_tab', [POST_HEAD.replace(b'Length: 7\r\n', b'Length: 7\t\r\n') + b'\r\n' + BODY], 200, False),
        ('length_both_ows', [POST_HEAD.replace(b'Length: 7\r\n', b'Length:\t7 \t\r\n') + b'\r\n' + BODY], 200, False),
        ('type_trailing_sp', [POST_HEAD.replace(b'urlencoded\r\n', b'urlencoded \r\n') + b'\r\n' + BODY], 200, False),
        ('type_trailing_tab', [POST_HEAD.replace(b'urlencoded\r\n', b'urlencoded\t\r\n') + b'\r\n' + BODY], 200, False),
        ('expect_ows', [EXPECT_HEAD.replace(b'100-continue\r\n', b'\t100-continue \t\r\n')], 417, False),
        ('expect_no_host', [EXPECT_HEAD.replace(b'Host: localhost\r\n', b'')], 400, False),
        ('expect_empty_host', [EXPECT_HEAD.replace(b'Host: localhost', b'Host: \t')], 400, False),
        ('expect_duplicate_host', [EXPECT_HEAD.replace(b'Host: localhost\r\n', b'Host: localhost\r\nHost: other\r\n')], 400, False),
        ('bad_whitespace_before_colon', [POST_HEAD.replace(b'Content-Length:', b'Content-Length :') + b'\r\n' + BODY], 400, False),
        ('bad_value_control', [POST_HEAD + b'X-Test: a\x0bb\r\n\r\n' + BODY], 400, False),
        ('expect_bad_length', [EXPECT_HEAD.replace(b'Length: 7', b'Length: seven')], {'C': 400, 'Python': 413}, False),
        ('bad_length_interior_space', [POST_HEAD.replace(b'Length: 7', b'Length: 0 7') + b'\r\n' + BODY], {'C': 400, 'Python': 413}, False),
        ('duplicate_length', [POST_HEAD + b'Content-Length: 7\r\nExpect: 100-continue\r\n\r\n'], 400, False),
        ('invalid_field', [POST_HEAD + b'Broken field\r\nExpect: 100-continue\r\n\r\n'], 400, False),
        ('nul_in_header', [POST_HEAD + b'X-Test: a\0b\r\nExpect: 100-continue\r\n\r\n'], 400, False),
        ('extra_body', [POST_HEAD + b'\r\n' + BODY + b'x'], 400, False),
        ('duplicate_expect', [POST_HEAD + b'Expect: 100-continue\r\nExpect: other\r\n\r\n'], {'C': 417, 'Python': 400}, False),
        ('transfer_encoding', [POST_HEAD + b'Transfer-Encoding: chunked\r\nExpect: 100-continue\r\n\r\n'], {'C': 400, 'Python': 501}, False),
        ('oversize_length', [POST_HEAD.replace(b'Length: 7', b'Length: 4097') + b'\r\n'], {'C': 400, 'Python': 413}, False),
        ('oversize_header', [POST_HEAD + b'X-Padding: ' + b'a' * 8200 + b'\r\n\r\n'], 400, False),
    ]


def _stop_owned_process(process):
    if process.poll() is None:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=3)


def _launch(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, start_new_session=True)
    try:
        if not select.select([process.stdout], [], [], 5)[0]:
            raise AssertionError('server did not announce its loopback listener')
        line = process.stdout.readline().split()
        if line[:2] != ['LISTEN', '127.0.0.1']:
            raise AssertionError(f'invalid listener announcement: {line!r}')
        return process, int(line[2])
    except BaseException:
        _stop_owned_process(process)
        process.communicate()
        raise


def _exchange(port, parts, wanted, head_only):
    with socket.create_connection(('127.0.0.1', port), timeout=3) as client:
        # The entire reply must arrive before the old 2-second C read timeout.
        for part in parts[:-1]:
            client.sendall(part)
            if select.select([client], [], [], 0.075)[0]:
                raise AssertionError('response or closure before the request was decidable')
        started = time.monotonic()
        client.sendall(parts[-1])
        response = bytearray()
        deadline = started + 1.5
        while True:
            left = deadline - time.monotonic()
            if left <= 0:
                raise AssertionError('no complete final response within 1.5 seconds')
            client.settimeout(left)
            try:
                block = client.recv(65536)
            except TimeoutError as error:
                raise AssertionError('no final response while client withheld body and EOF') from error
            if not block:
                break
            response.extend(block)
            if len(response) > 200000:
                raise AssertionError('unbounded response')
        elapsed = time.monotonic() - started
        if b'\r\n\r\n' not in response:
            raise AssertionError(f'no complete HTTP response: {bytes(response)!r}')
        header, payload = bytes(response).split(b'\r\n\r\n', 1)
        lines = header.split(b'\r\n')
        status = int(lines[0].split()[1])
        fields = dict(line.split(b': ', 1) for line in lines[1:])
        length = int(fields[b'Content-Length'])
        assert status == wanted, (status, wanted, bytes(response))
        assert fields[b'Connection'].lower() == b'close'
        assert len(payload) == (0 if head_only else length), (header, payload)
        if wanted == 200:
            assert payload == b'<p>2 + 3 = 5</p>\n'
        elif wanted == 417:
            assert payload == (b'' if head_only else b'Expectation Failed')
        return {'status': status, 'seconds': round(elapsed, 4),
                'body_bytes': len(payload), 'write_side_remained_open': True}


def check_http_review(base, run, compiler='clang'):
    """Compile C with sanitizers, exercise four models and Python, persist evidence."""
    base, run = Path(base).resolve(), Path(run).resolve()
    run.mkdir(parents=True, exist_ok=True)
    root = run / 'root'
    root.mkdir(exist_ok=True)
    (root / 'home.html').write_text('<p>HTTP handshake fixture</p>\n')
    binary = run / 'servers'
    command = [compiler, '-std=c11', '-Wall', '-Wextra', '-Werror', '-pedantic',
               '-pthread', '-fsanitize=address,undefined', str(base/'code/ch12_servers.c'),
               '-o', str(binary)]
    compiled = subprocess.run(command, capture_output=True, text=True, timeout=30)
    (run/'compile.txt').write_text(compiled.stdout + compiled.stderr)
    if compiled.returncode:
        raise AssertionError(f'HTTP regression compilation failed: {compiled.stderr}')
    # The proxy still uses request_size, whose result must mean message framing
    # completion, even when the HTTP responder can already reject Expect.
    framing = run/'framing.c'
    framing.write_text('''#define main original_http_main
#include SOURCE
#undef main
int main(void) {
    const char *header = HEADER;
    const char *complete = COMPLETE;
    size_t expected = 0, n = strlen(header);
    for (size_t i = 0; i <= n; ++i)
        if (request_size(header, i, &expected) != 0) return 1;
    if (expected != n + 7) return 2;
    if (request_size(complete, n + 3, &expected) != 0 || expected != n + 7) return 3;
    if (request_size(complete, n + 7, &expected) != 1 || expected != n + 7) return 4;
    const char *bad = "POST / HTTP/1.0\\r\\nContent-Length: 7\\r\\nContent-Length: 7\\r\\n\\r\\n";
    if (request_size(bad, strlen(bad), &expected) != -1) return 5;
    return 0;
}
'''.replace('SOURCE', json.dumps(str(base/'code/ch11_http.c')))
        .replace('HEADER', json.dumps(EXPECT_HEAD.decode()))
        .replace('COMPLETE', json.dumps((EXPECT_HEAD + BODY).decode())))
    framing_binary = run/'framing'
    framing_compile = subprocess.run([compiler, '-std=c11', '-Wall', '-Wextra', '-Werror',
                                      '-pedantic', '-fsanitize=address,undefined', str(framing),
                                      '-o', str(framing_binary)], capture_output=True, text=True, timeout=30)
    (run/'framing-compile.txt').write_text(framing_compile.stdout + framing_compile.stderr)
    if framing_compile.returncode:
        raise AssertionError(f'framing compatibility compilation failed: {framing_compile.stderr}')
    framing_run = subprocess.run([str(framing_binary)], capture_output=True, text=True, timeout=5)
    (run/'framing.txt').write_text(framing_run.stdout + framing_run.stderr)
    if framing_run.returncode:
        raise AssertionError(f'framing compatibility failed: {framing_run.returncode}: {framing_run.stderr}')
    driver = run/'python_server.py'
    driver.write_text('''import importlib.util, socket, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("http_companion", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
with socket.socket() as listener:
    listener.bind(("127.0.0.1", 0)); listener.listen(16); listener.settimeout(10)
    print("LISTEN 127.0.0.1", listener.getsockname()[1], flush=True)
    for _ in range(int(sys.argv[3])):
        connection, _ = listener.accept()
        with connection:
            module.handle(connection, Path(sys.argv[2]))
''')
    cases, results, errors = _cases(), [], []
    for mode in ['process', 'select', 'thread', 'pool', 'Python']:
        command = ([sys.executable, str(driver), str(base/'code/ch11_http.py'), str(root), str(len(cases))]
                   if mode == 'Python' else
                   [str(binary), '--serve', mode, str(root), '0', str(len(cases))])
        process, port = _launch(command)
        try:
            for name, parts, wanted, head_only in cases:
                wanted = wanted['Python' if mode == 'Python' else 'C'] if isinstance(wanted, dict) else wanted
                record = {'mode': mode, 'case': name}
                try:
                    record.update(_exchange(port, parts, wanted, head_only))
                    record['passed'] = True
                except (AssertionError, OSError, ValueError) as error:
                    record.update(passed=False, error=str(error))
                    errors.append(f'{mode}/{name}: {error}')
                results.append(record)
            stdout, stderr = process.communicate(timeout=8)
            (run/f'{mode}-server.txt').write_text(stdout + stderr)
            if process.returncode or 'Sanitizer' in stderr or 'runtime error:' in stderr:
                errors.append(f'{mode}: server exit {process.returncode}: {stderr}')
        finally:
            _stop_owned_process(process)
            process.communicate()
    report = {'status': 'failed' if errors else 'passed', 'cases': len(results),
              'passed': sum(item['passed'] for item in results), 'results': results,
              'errors': errors,
              'source_sha256': {name: hashlib.sha256((base/name).read_bytes()).hexdigest()
                                for name in ['code/ch11_http.c', 'code/ch11_http.py', 'code/ch12_servers.c']},
              'framing_compatibility': 'all header prefixes, partial/complete body, duplicate length passed',
              'scope': 'actual loopback sockets, no client half-close, four C modes plus Python; ASan/UBSan C'}
    (run/'report.json').write_text(json.dumps(report, indent=2) + '\n')
    if errors:
        raise AssertionError('; '.join(errors))
    return report
