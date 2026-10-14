"""Numeric byte-order examples; hostinfo performs DNS only when explicitly requested."""
import socket
import sys


def number(text, base, limit):
    digits = text[2:] if base == 16 and text.lower().startswith('0x') else text
    allowed = '0123456789abcdef'[:base]
    if not digits or any(c.lower() not in allowed for c in digits):
        raise ValueError('invalid input')
    value = int(digits, base)
    if value > limit:
        raise ValueError('invalid input')
    return value


def hostinfo(host):
    for entry in socket.getaddrinfo(host, None, socket.AF_INET, socket.SOCK_STREAM):
        print(socket.inet_ntop(socket.AF_INET, socket.inet_pton(socket.AF_INET, entry[4][0])))


def main(args):
    if not args:
        for text in ['107.212.122.205', '64.12.149.13', '107.212.96.29',
                     '0.0.0.128', '255.255.255.0', '10.1.1.64']:
            print(f'{text} = 0x{int.from_bytes(socket.inet_pton(socket.AF_INET, text), "big"):08X}')
        print('port=1024 wire=' + (1024).to_bytes(2, 'big').hex(' '))
        hostinfo('127.0.0.1')
        return
    if len(args) != 2:
        raise ValueError('usage: ch11_address MODE VALUE')
    mode, text = args
    if mode == 'hostinfo':
        hostinfo(text)
    elif mode in ('hex2dd', 'dd2hex'):
        value = number(text, 16 if mode == 'hex2dd' else 10, 65535)
        value = int.from_bytes(value.to_bytes(2, 'big'), 'big')
        print(value if mode == 'hex2dd' else hex(value))
    elif mode == 'ipv4hex':
        print(f'0x{int.from_bytes(socket.inet_pton(socket.AF_INET, text), "big"):08X}')
    elif mode == 'hexipv4':
        print(socket.inet_ntop(socket.AF_INET, number(text, 16, 2**32-1).to_bytes(4, 'big')))
    else:
        raise ValueError('invalid input')


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except (ValueError, OSError) as error:
        print(error, file=sys.stderr)
        sys.exit(2)
