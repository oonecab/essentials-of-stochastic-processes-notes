"""Real loopback TCP, bounded payload; sequential roles fit kernel buffers."""
import socket


def main():
    sent = b'ab\nx\0y\ntail'
    with socket.socket() as listener:
        listener.settimeout(2)
        listener.bind(('127.0.0.1', 0))
        listener.listen(1)
        with socket.create_connection(listener.getsockname(), timeout=2) as client:
            server, _ = listener.accept()
            with server:
                server.settimeout(2)
                client.sendall(sent[:2])
                client.sendall(sent[2:])
                client.shutdown(socket.SHUT_WR)
                count = 0
                while block := server.recv(3):
                    count += len(block)
                    if count > len(sent):
                        raise RuntimeError('unexpected data')
                    server.sendall(block)
                if count != len(sent):
                    raise RuntimeError('truncated stream')
                server.shutdown(socket.SHUT_WR)
                result = b''
                while block := client.recv(16):
                    result += block
                    if len(result) > len(sent):
                        raise RuntimeError('unexpected echo')
                if result != sent:
                    raise RuntimeError('echo differs')
    print('echo bytes=11 binary=preserved half-close=EOF listener=separate')


if __name__ == '__main__':
    main()
