"""Bounded loopback Tiny companion with a real CGI subprocess.

handle(conn, root, log=None) handles one request without closing conn. Callers
own sockets; static root must remain stable while serving. --serve ROOT [SECONDS]
accepts on 127.0.0.1 and an ephemeral port for SECONDS (default 60);
an in-flight request then finishes within its bounded I/O/CGI timeouts.
No arguments run temporary-file and loopback regressions then exit.
"""
import os
from pathlib import Path
import re
import socket
import stat
import subprocess
import sys
import tempfile
import threading
import time
from urllib.parse import parse_qs, urlsplit

HEADER_LIMIT = 8192
BODY_LIMIT = 4096
FILE_LIMIT = 65536
FORM = '''<!doctype html><meta charset="utf-8"><title>Adder</title>
<h1>Two integer adder</h1>
<form action="/cgi-bin/adder" method="get">
<label>A <input name="a" value="15000"></label>
<label>B <input name="b" value="213"></label><button>GET sum</button></form>
<form action="/cgi-bin/adder" method="post">
<label>A <input name="a" value="15000"></label>
<label>B <input name="b" value="213"></label><button>POST sum</button></form>
'''


class RequestError(Exception):
    def __init__(self, status):
        self.status = status


def sum_body(args):
    if '=' in args:
        if re.search(r'%(?![0-9A-Fa-f]{2})', args):
            raise ValueError('malformed percent encoding')
        fields = parse_qs(args, strict_parsing=True, keep_blank_values=True,
                          encoding='ascii', errors='strict', max_num_fields=2)
        if set(fields) != {'a', 'b'} or any(len(v) != 1 for v in fields.values()):
            raise ValueError('need one a and one b')
        values = [fields['a'][0], fields['b'][0]]
    else:
        values = args.split('&')
    if len(values) != 2 or any(not re.fullmatch(r'[+-]?[0-9]{1,7}', v) for v in values):
        raise ValueError('need two decimal integers')
    a, b = map(int, values)
    if max(abs(a), abs(b)) > 1000000:
        raise ValueError('integer out of range')
    return f'<p>{a} + {b} = {a+b}</p>\n'.encode()


def cgi_main():
    method = os.environ.get('REQUEST_METHOD', '')
    if method == 'POST':
        n = int(os.environ.get('CONTENT_LENGTH', '-1'))
        if not 0 <= n <= BODY_LIMIT:
            raise ValueError('invalid body length')
        data = sys.stdin.buffer.read(n)
        if len(data) != n:
            raise ValueError('truncated body')
        args = data.decode('ascii')
    else:
        args = os.environ.get('QUERY_STRING', '')
    body = sum_body(args)
    full_http = os.environ.get('CSAPP_FULL_HTTP') == '1'
    prefix = b'HTTP/1.0 200 OK\r\n' if full_http else b''
    connection = b'Connection: close\r\n' if full_http else b''
    sys.stdout.buffer.write(prefix + b'Content-Type: text/html; charset=utf-8\r\n'
                            + f'Content-Length: {len(body)}\r\n'.encode() + connection
                            + b'\r\n' + (b'' if method == 'HEAD' else body))


def read_request(conn, log=None, state=None):
    deadline = time.monotonic() + 2
    data = bytearray()
    while b'\r\n\r\n' not in data:
        conn.settimeout(max(0.001, deadline-time.monotonic()))
        if time.monotonic() >= deadline:
            raise RequestError(408)
        part = conn.recv(1024)
        if not part:
            raise RequestError(400)
        data.extend(part)
        if state is not None and data.startswith(b'HEAD '):
            state[0] = 'HEAD'
        if len(data) > HEADER_LIMIT + BODY_LIMIT:
            raise RequestError(413)
    head, body = bytes(data).split(b'\r\n\r\n', 1)
    if len(head) + 4 > HEADER_LIMIT or b'\0' in head:
        raise RequestError(400)
    lines = head.decode('ascii').split('\r\n')
    if log is not None:
        log.write('\n'.join(lines) + '\n\n')
        log.flush()
    fields = lines[0].split(' ')
    if len(fields) != 3 or not all(fields):
        raise RequestError(400)
    method, target, version = fields
    if state is not None:
        state[0] = method
    if version not in ('HTTP/1.0', 'HTTP/1.1'):
        raise RequestError(505)
    headers = {}
    for line in lines[1:]:
        name, sep, value = line.partition(':')
        if not sep or not re.fullmatch(r'[A-Za-z0-9-]+', name):
            raise RequestError(400)
        if any((ord(c) < 32 and c != '\t') or ord(c) == 127 for c in value):
            raise RequestError(400)
        name, value = name.lower(), value.strip(' \t')
        if name in headers:
            raise RequestError(400)
        headers[name] = value
    if version == 'HTTP/1.1' and not headers.get('host'):
        raise RequestError(400)
    if 'transfer-encoding' in headers:
        raise RequestError(501)
    length = headers.get('content-length', '0')
    if not re.fullmatch('[0-9]{1,10}', length) or int(length) > BODY_LIMIT:
        raise RequestError(413)
    n = int(length)
    if method == 'POST' and 'content-length' not in headers:
        raise RequestError(411)
    if 'expect' in headers:
        raise RequestError(417)
    while len(body) < n:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise RequestError(408)
        conn.settimeout(remaining)
        part = conn.recv(n-len(body))
        if not part:
            raise RequestError(400)
        body += part
    if len(body) != n:
        raise RequestError(400)
    return method, target, headers, body


def asset(root, name):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', name) or '..' in name:
        raise RequestError(403)
    directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    try:
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    except FileNotFoundError:
        raise RequestError(404) from None
    except OSError:
        raise RequestError(403) from None
    finally:
        os.close(directory)
    with os.fdopen(fd, 'rb') as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > FILE_LIMIT:
            raise RequestError(403)
        body = stream.read(info.st_size)
        if len(body) != info.st_size:
            raise RequestError(500)
    extension = Path(name).suffix.lower()
    kind = {'.html': 'text/html; charset=utf-8', '.txt': 'text/plain; charset=utf-8',
            '.mpg': 'video/mpeg', '.mpeg': 'video/mpeg', '.png': 'image/png',
            '.gif': 'image/gif', '.jpg': 'image/jpeg'}.get(extension, 'application/octet-stream')
    return kind, body


def route(method, target, headers, body, root):
    if method not in ('GET', 'HEAD', 'POST'):
        raise RequestError(501)
    parts = urlsplit(target)
    if parts.scheme or parts.netloc or parts.fragment or not target.startswith('/'):
        raise RequestError(400)
    if parts.path == '/cgi-bin/adder':
        if method == 'POST' and headers.get('content-type') != 'application/x-www-form-urlencoded':
            raise RequestError(415)
        args = body.decode('ascii') if method == 'POST' else parts.query
        sum_body(args)  # Validate before starting the fixed, trusted executable.
        environment = {'REQUEST_METHOD': 'GET' if method == 'HEAD' else method,
                       'QUERY_STRING': parts.query, 'CONTENT_LENGTH': str(len(body)),
                       'CONTENT_TYPE': headers.get('content-type', '')}
        result = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--cgi'],
                                input=body, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                env=environment, timeout=2, check=False)
        if result.returncode or len(result.stdout) > BODY_LIMIT:
            raise RequestError(502)
        cgi_headers, payload = result.stdout.split(b'\r\n\r\n', 1)
        if cgi_headers != (b'Content-Type: text/html; charset=utf-8\r\n'
                           + f'Content-Length: {len(payload)}'.encode()):
            raise RequestError(502)
        return 'text/html; charset=utf-8', payload
    if method == 'POST':
        raise RequestError(405)
    return asset(root, 'home.html' if parts.path == '/' else parts.path[1:])


def handle(conn, root, log=None):
    """Caller closes conn. Returns status; peer-close errors affect this client only."""
    status, method = 200, ''
    state = ['']
    try:
        method, target, headers, body = read_request(conn, log, state)
        kind, payload = route(method, target, headers, body, root)
    except RequestError as error:
        status = error.status
    except (UnicodeError, ValueError):
        status = 400
    except (TimeoutError, socket.timeout):
        status = 408
    except (OSError, subprocess.SubprocessError):
        status = 500
    method = state[0]
    reasons = {200: 'OK', 400: 'Bad Request', 403: 'Forbidden', 404: 'Not Found',
               405: 'Method Not Allowed', 408: 'Request Timeout', 411: 'Length Required',
               413: 'Content Too Large', 415: 'Unsupported Media Type',
               417: 'Expectation Failed', 500: 'Internal Server Error',
               501: 'Not Implemented', 502: 'Bad Gateway', 505: 'HTTP Version Not Supported'}
    if status != 200:
        payload = reasons[status].encode()
        kind = 'text/plain; charset=utf-8'
    response = (f'HTTP/1.0 {status} {reasons[status]}\r\nContent-Type: {kind}\r\n'
                f'Content-Length: {len(payload)}\r\nConnection: close\r\n\r\n').encode()
    try:
        conn.settimeout(2)
        conn.sendall(response + (b'' if method == 'HEAD' else payload))
    except OSError:
        pass
    return status


def exchange(root, request):
    errors = []
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        listener.listen(1)
        listener.settimeout(3)
        def worker():
            try:
                connection, _ = listener.accept()
                with connection:
                    handle(connection, root)
            except BaseException as error:
                errors.append(error)
        thread = threading.Thread(target=worker)
        thread.start()
        try:
            with socket.create_connection(listener.getsockname(), timeout=3) as client:
                for offset in range(0, len(request), 7):
                    client.sendall(request[offset:offset+7])
                client.shutdown(socket.SHUT_WR)
                output = b''
                while part := client.recv(4096):
                    output += part
        finally:
            thread.join(5)
        if thread.is_alive() or errors:
            raise RuntimeError('server did not finish cleanly')
    return output


def selftest():
    with tempfile.TemporaryDirectory(prefix='csapp-ch11-') as root:
        base = Path(root)
        (base / 'home.html').write_text(FORM)
        (base / 'hello.txt').write_bytes(b'hello\0world\n')
        (base / 'empty.txt').write_bytes(b'')
        (base / 'sample.mpg').write_bytes(b'\0\0\x01\xba')  # MIME fixture, not playable video.
        (base / 'link.txt').symlink_to('hello.txt')
        cases = [
            (b'GET /hello.txt HTTP/1.0\r\n\r\n', 200, b'hello\0world\n'),
            (b'HEAD / HTTP/1.1\r\n\r\n', 400, b''),
            (b'HEAD / HTTP/2.0\r\n\r\n', 505, b''),
            (b'HEAD / HTTP/1.0\r\nContent-Length: 0\r\nContent-Length: 0\r\n\r\n', 400, b''),
            (b'GET /empty.txt HTTP/1.0\r\n\r\n', 200, b''),
            (b'HEAD /hello.txt HTTP/1.0\r\n\r\n', 200, b''),
            (b'GET /cgi-bin/adder?15000&213 HTTP/1.0\r\n\r\n', 200, b'<p>15000 + 213 = 15213</p>\n'),
            (b'GET /cgi-bin/adder?a=-4&b=7 HTTP/1.0\r\n\r\n', 200, b'<p>-4 + 7 = 3</p>\n'),
            (b'POST /cgi-bin/adder HTTP/1.0\r\nContent-Type: application/x-www-form-urlencoded\r\nContent-Length: 7\r\n\r\na=2&b=3', 200, b'<p>2 + 3 = 5</p>\n'),
            (b'GET /missing.txt HTTP/1.0\r\n\r\n', 404, b'Not Found'),
            (b'GET /../hello.txt HTTP/1.0\r\n\r\n', 403, b'Forbidden'),
            (b'GET /%2e%2e/hello.txt HTTP/1.0\r\n\r\n', 403, b'Forbidden'),
            (b'GET /link.txt HTTP/1.0\r\n\r\n', 403, b'Forbidden'),
            (b'GET /cgi-bin/adder?a=1&a=2 HTTP/1.0\r\n\r\n', 400, b'Bad Request'),
            (b'GET / HTTP/1.1\r\n\r\n', 400, b'Bad Request'),
            (b'POST /cgi-bin/adder HTTP/1.0\r\n\r\n', 411, b'Length Required'),
            (b'POST /cgi-bin/adder HTTP/1.0\r\nContent-Length: 8\r\n\r\na=2&b=3', 400, b'Bad Request'),
            (b'POST /cgi-bin/adder HTTP/1.0\r\nContent-Length: 0\r\nContent-Length: 0\r\n\r\n', 400, b'Bad Request'),
            (b'POST /cgi-bin/adder HTTP/1.0\r\nTransfer-Encoding: chunked\r\n\r\n', 501, b'Not Implemented'),
        ]
        for request, status, expected in cases:
            response = exchange(root, request)
            header, payload = response.split(b'\r\n\r\n', 1)
            if int(header.split()[1]) != status or payload != expected:
                raise RuntimeError(f'HTTP regression failed: {request!r}: {response!r}')
        response = exchange(root, b'GET /sample.mpg HTTP/1.0\r\n\r\n')
        if b'Content-Type: video/mpeg\r\n' not in response:
            raise RuntimeError('MIME regression')
        print(f'http loopback: {len(cases)+1} cases passed; CGI=exec; temporary-root=removed')


def serve(root, seconds):
    root = Path(root).resolve(strict=True)
    if not root.is_dir() or not 1 <= seconds <= 300:
        raise ValueError('root must be a directory; seconds must be 1..300')
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        listener.listen(16)
        listener.settimeout(0.25)
        print(f'http://127.0.0.1:{listener.getsockname()[1]}/ duration={seconds}s', flush=True)
        end = time.monotonic()+seconds
        while time.monotonic() < end:
            try:
                connection, _ = listener.accept()
            except socket.timeout:
                continue
            with connection:
                handle(connection, root, sys.stdout)


if __name__ == '__main__':
    try:
        if sys.argv[1:] == ['--cgi']:
            cgi_main()
        elif len(sys.argv) in (3, 4) and sys.argv[1] == '--serve':
            serve(sys.argv[2], int(sys.argv[3]) if len(sys.argv) == 4 else 60)
        elif len(sys.argv) == 1:
            selftest()
        else:
            raise ValueError('usage: ch11_http.py [--serve ROOT [SECONDS]]')
    except (ValueError, OSError) as error:
        print(error, file=sys.stderr)
        sys.exit(2)
