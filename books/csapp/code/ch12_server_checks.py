"""Bounded loopback acceptance of the actual C concurrency implementations.
Uses temporary files and ephemeral ports. No dependency on outside HTTP/DNS.
This is protocol/socket evidence; real-browser evidence is recorded separately.
"""
from pathlib import Path
import concurrent.futures
import os
import socket
import subprocess
import tempfile
import time

CODE = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise RuntimeError(f'server check failed: {message!r}')


def read_all(sock):
    data = b''
    while True:
        chunk = sock.recv(65536)
        if not chunk:
            return data
        data += chunk
        if len(data) > 200000:
            raise AssertionError('unbounded response')


def check_complete_home_response(answer):
    header, separator, body = answer.partition(b'\r\n\r\n')
    require(separator, answer)
    lines = header.split(b'\r\n')
    require(lines[0] == b'HTTP/1.0 200 OK', lines[0])
    lengths = [line.split(b':', 1)[1].strip() for line in lines[1:]
               if line.split(b':', 1)[0].lower() == b'content-length']
    require(len(lengths) == 1 and int(lengths[0]) == len(body), (lengths, body))
    require(body == b'<h1>Concurrent Tiny</h1>\n', body)


def connect(port):
    s = socket.create_connection(('127.0.0.1', port), timeout=6)
    s.settimeout(6)
    return s


def launch(binary, mode, root, count, extra=()):
    p = subprocess.Popen([str(binary), '--serve', mode, str(root), '0', str(count), *map(str, extra)],
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    line = p.stdout.readline().split()
    if line[:2] != ['LISTEN', '127.0.0.1']:
        raise AssertionError((mode, line, p.communicate(timeout=3)))
    return p, int(line[2])


def finish(p):
    out, err = p.communicate(timeout=12)
    require(p.returncode == 0, (p.returncode, out, err))
    require('Sanitizer' not in err and 'runtime error:' not in err, err)
    return err


def compile_window_server(root):
    """Exercise the real event loop with an explicit short acceptance deadline.

    The normal command still passes now_ms()+120000. No source substitution or
    environment setting changes that default; only this harness supplies 700 ms.
    """
    source = root / 'window_server.c'
    source.write_text(r'''
#define CH12_SERVER_MAIN chapter12_example_main
#include "SOURCE"
int main(int argc,char **argv) {
    if(argc!=6)return 2;
    (void)signal(SIGPIPE,SIG_IGN);
    int listener=listen_loopback(0);if(listener<0)return 2;
    int rc=event_loop(listener,argv[3],atoi(argv[5]),!strcmp(argv[2],"echo"),now_ms()+700);
    if(fcntl(listener,F_GETFD)!=-1 || errno!=EBADF)return 3;
    return rc;
}
'''.replace('SOURCE', str(CODE/'ch12_servers.c')))
    binary = root / 'window_server'
    subprocess.run(['clang', '-std=c11', '-Wall', '-Wextra', '-Werror', '-pedantic',
                    '-pthread', '-fsanitize=address,undefined', str(source),
                    '-o', str(binary)], check=True)
    return binary


def check_window_cases(binary, root):
    """Keep one accepted client alive across window expiry, then drain it."""
    results = []
    for mode, stalled in [('select', False), ('echo', False), ('select', True)]:
        p, port = launch(binary, mode, root, 2)
        client = connect(port)
        started = time.monotonic()
        try:
            prefix = b'partial' if mode == 'echo' else b'GET / HTTP/1.0\r\n'
            client.sendall(prefix)
            time.sleep(.95)
            require(p.poll() is None, (mode, 'accepted client discarded at window expiry'))
            try:
                late = socket.create_connection(('127.0.0.1', port), timeout=1)
            except ConnectionRefusedError:
                pass
            else:
                late.close()
                raise AssertionError((mode, 'listener still accepts after its window'))
            if not stalled:
                client.sendall(b' line\n' if mode == 'echo' else b'Host: localhost\r\n\r\n')
                if mode == 'echo':
                    client.shutdown(socket.SHUT_WR)
                answer = read_all(client)
                if mode == 'echo':
                    require(answer == b'partial line\n', answer)
                else:
                    check_complete_home_response(answer)
            else:
                answer = read_all(client)
                require(answer == b'', answer)
                require(2.5 <= time.monotonic()-started <= 6, 'client deadline lost')
            out, err = p.communicate(timeout=5)
            # Expiry before the requested count remains a partial-run result.
            require(p.returncode == 1, (p.returncode, out, err))
            require(not err, err)
            results.append({'mode': mode, 'stalled': stalled,
                            'seconds': round(time.monotonic()-started, 3),
                            'late_connection_refused': True, 'returncode': p.returncode})
        finally:
            client.close()
            if p.poll() is None:
                p.kill()
            p.communicate(timeout=5)
    return results


def main():
    with tempfile.TemporaryDirectory(prefix='csapp-ch12-') as directory:
        root = Path(directory)
        (root / 'home.html').write_text('<h1>Concurrent Tiny</h1>\n')
        binary = root / 'servers'
        subprocess.run(['clang', '-std=c11', '-Wall', '-Wextra', '-Werror', '-pedantic',
                        '-pthread', '-fsanitize=address,undefined', str(CODE/'ch12_servers.c'),
                        '-o', str(binary)], check=True)
        request = b'GET / HTTP/1.0\r\nHost: localhost\r\n\r\n'
        completed_modes = slow_client_cases = 0
        for mode in ['process', 'select', 'thread', 'pool']:
            p, port = launch(binary, mode, root, 2)
            slow = connect(port)
            slow.sendall(b'GET / HTTP/1.0\r\n')
            # The one-worker pool deliberately needs queue pressure to grow;
            # its first test completes both requests together.
            fast = connect(port)
            fast.sendall(request)
            if mode != 'pool':
                answer = read_all(fast)
                check_complete_home_response(answer)
                slow.sendall(b'Host: localhost\r\n\r\n')
            else:
                slow.sendall(b'Host: localhost\r\n\r\n')
                answer = read_all(fast)
                check_complete_home_response(answer)
            answer = read_all(slow)
            check_complete_home_response(answer)
            slow.close(); fast.close(); finish(p)
            completed_modes += 1
            slow_client_cases += mode != 'pool'
        p, port = launch(binary, 'pool', root, 12)
        clients = [connect(port) for _ in range(12)]
        for client in clients:
            client.sendall(b'GET / HTTP/1.0\r\n')
        time.sleep(.15)
        for client in clients:
            client.sendall(b'Host: localhost\r\n\r\n')
        for client in clients:
            answer = read_all(client)
            check_complete_home_response(answer)
            client.close()
        events = finish(p)
        require('pool grow 1 -> 2' in events and 'pool shrink target=' in events, events)
        p, port = launch(binary, 'echo', root, 2)
        a, b = connect(port), connect(port)
        a.sendall(b'partial')
        b.sendall(b'one\ntwo\n')
        b.shutdown(socket.SHUT_WR)
        answer = read_all(b)
        require(answer == b'one\ntwo\n', answer)
        a.sendall(b' line\nlast')
        a.shutdown(socket.SHUT_WR)
        answer = read_all(a)
        require(answer == b'partial line\nlast', answer)
        a.close(); b.close(); finish(p)
        for mode in ['proxy-serial', 'proxy']:
            upstream, origin_port = launch(binary, 'thread', root, 1)
            url = f'http://127.0.0.1:{origin_port}/'
            blocked = url + 'blocked'
            filt, log = root/'filter.txt', root/'proxy.log'
            filt.write_text(blocked+'\n')
            p, port = launch(binary, mode, root, 2, (filt, log))
            for target, status in [(blocked,b'403 Forbidden'),(url,b'200 OK')]:
                with connect(port) as client:
                    client.sendall(f'GET {target} HTTP/1.0\r\nHost: localhost\r\n\r\n'.encode())
                    answer = read_all(client)
                    require(status in answer, answer)
            finish(p); finish(upstream)
            records = log.read_text()
            require('BLOCK '+blocked in records and 'ALLOW '+url in records, records)
        check_window_cases(compile_window_server(root), root)
        print(f'servers modes={completed_modes} slow_client={slow_client_cases} pool_growth_shrink=YES')
        print('echo partial_lines=YES buffered_lines=YES eof_tail=YES')
        print('proxy sequential_and_threads=YES filter=YES log=YES')


if __name__ == '__main__':
    main()
