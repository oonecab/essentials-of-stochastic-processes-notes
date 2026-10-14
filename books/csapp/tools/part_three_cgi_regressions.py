"""Real Chapter 11.8 fork/exec, overlapping requests and SIGCHLD lifecycle checks."""
from pathlib import Path
import hashlib
import json
import os
import re
import select
import signal
import socket
import subprocess
import sys
import time

from part_three_http_review_regressions import _launch, _stop_owned_process


def require(value, message):
    if not value:
        raise AssertionError(message)


def request(port, target='/cgi-bin/adder?a=2&b=3', method='GET', body=b''):
    client = socket.create_connection(('127.0.0.1', port), timeout=3)
    headers = (f'{method} {target} HTTP/1.1\r\nHost: localhost\r\n'
               f'Content-Length: {len(body)}\r\n'
               'Content-Type: application/x-www-form-urlencoded\r\n\r\n').encode()
    client.sendall(headers + body)
    return client


def response(client, status=200, payload=b'<p>2 + 3 = 5</p>\n', head=False, timeout=3):
    client.settimeout(timeout)
    data = bytearray()
    while chunk := client.recv(65536):
        data.extend(chunk)
    header, actual = bytes(data).split(b'\r\n\r\n', 1)
    require(int(header.split()[1]) == status, repr(data))
    values = re.findall(rb'(?mi)^Content-Length: ([0-9]+)\r?$', header)
    require(len(values) == 1 and int(values[0]) == len(payload), repr(data))
    require(actual == (b'' if head else payload), repr(data))
    return {'status': status, 'body_bytes': len(actual), 'eof': True}


def wait_records(directory, count):
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        files = list(directory.glob('pid-*.json'))
        if len(files) == count:
            try:
                return [json.loads(p.read_text()) for p in files]
            except json.JSONDecodeError:
                pass
        time.sleep(0.01)
    raise AssertionError(f'CGI wrappers did not all start: wanted {count}')


def check_cgi_review(base, run, compiler='clang'):
    base, run = Path(base).resolve(), Path(run).resolve()
    run.mkdir(parents=True, exist_ok=True)
    root = run/'root'; root.mkdir(exist_ok=True)
    (root/'home.html').write_bytes(b'parent remains available\n')
    binary, harness = run/'http', run/'lifecycle'
    flags = [compiler, '-std=c11', '-Wall', '-Wextra', '-Werror', '-pedantic',
             '-fsanitize=address,undefined']
    subprocess.run([*flags, str(base/'code/ch11_http.c'), '-o', str(binary)],
                   check=True, capture_output=True, timeout=30)
    driver = run/'lifecycle.c'
    driver.write_text('''#define main included_http_main
#include SOURCE
#undef main
static int count_fds(void) {
    int count = 0;
    for (int fd = 0; fd < 256; ++fd) if (fcntl(fd, F_GETFD) >= 0) ++count;
    return count;
}
int main(int argc, char **argv) {
    if (argc != 4) return 2;
    struct sigaction ignore = {0}, before, after;
    ignore.sa_handler = SIG_IGN; sigemptyset(&ignore.sa_mask);
    if (sigaction(SIGPIPE, &ignore, NULL) || sigaction(SIGCHLD, NULL, &before)) return 3;
    sigset_t block, original, restored;
    sigemptyset(&block); sigaddset(&block, SIGCHLD);
    if (sigprocmask(SIG_BLOCK, &block, &original)) return 4;
    int initial = count_fds();
    int rc = serve_cgi(argv[1], argv[2], atoi(argv[3]));
    if (sigaction(SIGCHLD, NULL, &after) || sigprocmask(SIG_SETMASK, NULL, &restored)) return 5;
    if (before.sa_handler != after.sa_handler || !sigismember(&restored, SIGCHLD)) return 6;
    errno = 0;
    if (waitpid(-1, NULL, WNOHANG) != -1 || errno != ECHILD || count_fds() != initial) return 7;
    if (sigprocmask(SIG_SETMASK, &original, NULL)) return 8;
    puts("LIFECYCLE children=none descriptors=restored SIGCHLD=restored");
    return rc;
}
'''.replace('SOURCE', json.dumps(str(base/'code/ch11_http.c'))))
    subprocess.run([*flags, str(driver), '-o', str(harness)], check=True,
                   capture_output=True, timeout=30)
    results = []
    for language in ['C', 'Python']:
        work = run/language; work.mkdir(exist_ok=True)
        gate = work/'release'
        if gate.exists(): gate.unlink()
        for old in work.glob('pid-*.json'): old.unlink()
        wrapper = work/'cgi-wrapper'
        command = ([str(binary), '--cgi'] if language == 'C' else
                   [sys.executable, str(base/'code/ch11_http.py'), '--cgi'])
        wrapper.write_text(f'#!{sys.executable}\n' + '''import json, os, stat, time
from pathlib import Path
WORK = Path(WORK_PATH)
CGI_COMMAND = COMMAND_VALUE
sockets = []
for fd in range(256):
    try:
        if stat.S_ISSOCK(os.fstat(fd).st_mode): sockets.append(fd)
    except OSError: pass
(WORK / ('pid-' + str(os.getpid()) + '.json')).write_text(json.dumps({'pid': os.getpid(), 'parent': os.getppid(), 'sockets': sockets, 'query': os.environ['QUERY_STRING']}))
if os.environ['QUERY_STRING'].startswith(('a=10&', 'a=11&', 'a=12&')):
    while not (WORK/'release').exists(): time.sleep(0.01)
os.execv(CGI_COMMAND[0], CGI_COMMAND)
'''.replace('WORK_PATH', repr(str(work))).replace('COMMAND_VALUE', repr(command)))
        # The replacement above assigns the actual command without shell parsing.
        wrapper.chmod(0o755)
        process, port = _launch([str(harness), str(root), str(wrapper), '5'])
        clients, records = [], []
        try:
            for value in [10, 11, 12]:
                clients.append(request(port, f'/cgi-bin/adder?a={value}&b=3'))
            records = wait_records(work, 3)
            require(all(r['parent'] == process.pid and r['sockets'] == [1] for r in records), str(records))
            require(all(not select.select([client], [], [], 0.03)[0] for client in clients), 'CGI did not wait at gate')
            start = time.monotonic()
            with request(port, '/') as static:
                item = response(static, payload=b'parent remains available\n')
            item['seconds_while_cgi_waited'] = round(time.monotonic()-start, 4)
            require(item['seconds_while_cgi_waited'] < 1, 'parent blocked waiting for CGI')
            os.kill(process.pid, signal.SIGSTOP)
            gate.write_text('release children while parent is stopped\n')
            for value, client in zip([10, 11, 12], clients):
                response(client, payload=f'<p>{value} + 3 = {value+3}</p>\n'.encode())
            # EOF with a stopped parent proves it already closed every connfd.
            deadline = time.monotonic() + 3
            while time.monotonic() < deadline:
                states = subprocess.run(['ps', '-o', 'stat=', '-p',
                                         ','.join(str(r['pid']) for r in records)],
                                        capture_output=True, text=True, timeout=2).stdout.split()
                if len(states) == 3 and all(state.startswith('Z') for state in states):
                    break
                time.sleep(0.01)
            else:
                raise AssertionError('CGI children did not reach waitable zombie state')
            os.kill(process.pid, signal.SIGCONT)
            with request(port, '/cgi-bin/adder', 'POST', b'a=2&b=3') as post:
                response(post)
            output, errors = process.communicate(timeout=8)
            require(process.returncode == 0 and not errors, f'{output}\n{errors}')
            match = re.search(r'spawned=4 reaped=4 max-batch=(\d+)', output)
            require(match and int(match[1]) >= 3, f'coalesced exits not drained: {output}')
            require('children=none descriptors=restored SIGCHLD=restored' in output, output)
            results.append({'cgi': language, 'overlap': item, 'inherited_descriptors': records,
                            'parent_stopped_eof': True, 'coalesced_reap_batch': int(match[1]),
                            'stdout': output, 'stderr': errors, 'passed': True})
        finally:
            try: os.kill(process.pid, signal.SIGCONT)
            except ProcessLookupError: pass
            gate.write_text('cleanup release\n')
            for client in clients: client.close()
            _stop_owned_process(process); process.communicate()
    # Select a legal schedule: let the actual CGI close stdin before the parent
    # resumes from fork. This detects accidental killing after pipe EPIPE.
    scheduled = run/'scheduled-lifecycle.c'
    scheduled.write_text('''#define _POSIX_C_SOURCE 200809L
#ifdef __APPLE__
#define _DARWIN_C_SOURCE
#endif
#include <sys/types.h>
#include <unistd.h>
#include <time.h>
#include <stdlib.h>
static pid_t scheduled_fork(void) {
    pid_t pid = fork();
    if (pid > 0) {
        const char *marker = getenv("CSAPP_CGI_CLOSED_MARKER");
        for (int i = 0; marker && access(marker, F_OK) && i < 400; ++i) {
            struct timespec delay = {0, 10000000}; nanosleep(&delay, NULL);
        }
    }
    return pid;
}
#define fork scheduled_fork
''' + driver.read_text().replace('#undef main', '#undef main\n#undef fork')
        .replace('if (argc != 4) return 2;',
                 'if (argc != 5 || setenv("CSAPP_CGI_CLOSED_MARKER", argv[4], 1)) return 2;'))
    scheduled_binary = run/'scheduled-lifecycle'
    subprocess.run([*flags, str(scheduled), '-o', str(scheduled_binary)], check=True,
                   capture_output=True, timeout=30)
    early = run/'early-close-cgi'
    early.write_text(f'#!{sys.executable}\n' + '''import json, os, time
from pathlib import Path
method = os.environ['REQUEST_METHOD']
os.close(0)
Path(os.environ['CSAPP_CGI_CLOSED_MARKER']).write_text(json.dumps({'method': method, 'content_length': os.environ['CONTENT_LENGTH'], 'stdin_closed': True}))
time.sleep(0.3)
body = b'CGI rejected body' if method == 'POST' else b'<p>2 + 3 = 5</p>\\n'
status = b'400 Bad Request' if method == 'POST' else b'200 OK'
header = b'HTTP/1.0 ' + status + b'\\r\\nContent-Length: ' + str(len(body)).encode() + b'\\r\\nConnection: close\\r\\n\\r\\n'
os.write(1, header + (b'' if method == 'HEAD' else body))
'''); early.chmod(0o755)
    for method in ['GET', 'HEAD', 'POST']:
        marker = run/('closed-' + method + '.json')
        marker.unlink(missing_ok=True)
        process, port = _launch([str(scheduled_binary), str(root), str(early), '1', str(marker)])
        try:
            with request(port, method=method, body=b'a=2&b=3') as client:
                item = response(client, status=400 if method == 'POST' else 200,
                                payload=b'CGI rejected body' if method == 'POST' else b'<p>2 + 3 = 5</p>\n',
                                head=method == 'HEAD')
            out, err = process.communicate(timeout=8)
            state = json.loads(marker.read_text())
            require(state['content_length'] == ('7' if method == 'POST' else '0'), str(state))
            require(process.returncode == 0 and not err and 'spawned=1 reaped=1' in out, out+err)
            results.append({'case': method + '_cgi_closes_stdin_first', 'response': item,
                            'cgi_input': state, 'passed': True, 'stdout': out})
        finally:
            _stop_owned_process(process); process.communicate()
    # Exercise the published CLI itself, HEAD framing, and a disconnected peer.
    process, port = _launch([str(binary), '--serve-cgi', str(root), '3'])
    try:
        with request(port, method='HEAD') as head:
            response(head, head=True)
        aborted = request(port); aborted.close()
        with request(port) as good:
            response(good)
        out, err = process.communicate(timeout=8)
        require(process.returncode == 0 and not err and 'spawned=3 reaped=3' in out, out+err)
        results.append({'case': 'published_cli_head_peer_close_recovery', 'passed': True, 'stdout': out})
    finally:
        _stop_owned_process(process); process.communicate()
    # Failed exec writes one complete 502, and the handler still owns the child.
    process, port = _launch([str(harness), str(root), str(run/'missing-program'), '2'])
    try:
        with request(port) as bad:
            response(bad, 502, b'Bad Gateway')
        with request(port, '/') as good:
            response(good, payload=b'parent remains available\n')
        out, err = process.communicate(timeout=8)
        require(process.returncode == 0 and not err and 'spawned=1 reaped=1' in out, out+err)
        results.append({'case': 'exec_failure_recovery', 'passed': True, 'stdout': out})
    finally:
        _stop_owned_process(process); process.communicate()
    stalled = run/'stalled-cgi'
    stalled.write_text(f'#!{sys.executable}\nimport time\ntime.sleep(30)\n'); stalled.chmod(0o755)
    process, port = _launch([str(harness), str(root), str(stalled), '2'])
    start = time.monotonic()
    try:
        with request(port) as bad:
            with request(port, '/') as good:
                response(good, payload=b'parent remains available\n')
            bad.settimeout(7)
            require(bad.recv(1) == b'', 'stalled CGI should close without fabricating success')
        out, err = process.communicate(timeout=3)
        elapsed = time.monotonic()-start
        require(4.5 <= elapsed < 7 and process.returncode == 0 and not err and 'spawned=1 reaped=1' in out, out+err)
        results.append({'case': 'cgi_alarm_bound_recovery', 'seconds': round(elapsed, 3),
                        'passed': True, 'stdout': out})
    finally:
        _stop_owned_process(process); process.communicate()
    report = {'status': 'passed', 'cases': len(results), 'results': results,
              'scope': 'C parent with actual C and Python CGI exec; POSIX loopback, ASan/UBSan; explicit lifecycle and signal restoration',
              'source_sha256': {name: hashlib.sha256((base/name).read_bytes()).hexdigest()
                                for name in ['code/ch11_http.c', 'code/ch11_http.py']}}
    (run/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    return report
