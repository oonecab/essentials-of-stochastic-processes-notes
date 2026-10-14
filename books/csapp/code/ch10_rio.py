#!/usr/bin/env python3
"""Byte-count reference model; injected errors are not OS signal execution."""
import errno


class Script:
    def __init__(self, data=b"", steps=()):
        self.data, self.steps = data, iter(steps)
        self.offset = self.calls = 0
        self.output = bytearray()

    def limit(self, n):
        self.calls += 1
        k = next(self.steps, 64)
        if k < 0:
            raise OSError(-k, "injected")
        return min(n, k)

    def read(self, n):
        k = min(self.limit(n), len(self.data) - self.offset)
        b = self.data[self.offset:self.offset + k]
        self.offset += k
        return b

    def write(self, b):
        n = self.limit(len(b))
        self.output.extend(b[:n])
        return n


def readn(get, n):
    result = bytearray()
    while len(result) < n:
        try:
            b = get(n - len(result))
        except InterruptedError:
            continue
        if not b:
            break
        result.extend(b)
    return bytes(result)


def writen(put, data):
    done = 0
    while done < len(data):
        try:
            n = put(data[done:])
        except InterruptedError:
            continue
        if n == 0:
            raise OSError(errno.EIO, "zero write")
        done += n
    return done


class Rio:
    def __init__(self, get):
        self.get, self.buffer = get, b""

    def read(self, n):
        if n == 0:
            return b""
        while not self.buffer:
            try:
                self.buffer = self.get(8)
            except InterruptedError:
                continue
            if not self.buffer:
                return b""
        b, self.buffer = self.buffer[:n], self.buffer[n:]
        return b

    def line(self, capacity):
        if capacity < 2:
            raise OSError(errno.EINVAL, "capacity")
        result = bytearray()
        while len(result) < capacity - 1:
            b = self.read(1)
            if not b:
                break
            result.extend(b)
            if b == b"\n":
                break
        return bytes(result)


def check(value, message):
    if not value:
        raise RuntimeError(message)


def main():
    data = b"A\0B\nCD"
    steps = (-errno.EINTR, 2, 1, 3)
    s = Script(data, steps)
    check(readn(s.read, 9) == data and s.calls == 5, "short read")
    print("readn short+EINTR+EOF bytes=6 calls=5")
    check(readn(s.read, 0) == b"" and s.calls == 5, "zero read")
    w = Script(steps=steps)
    check(writen(w.write, data) == 6 and w.output == data and w.calls == 4, "write")
    print("writen short+EINTR bytes=6 calls=4")
    s = Script(data, (2, -errno.EIO))
    try:
        readn(s.read, 6)
        raise RuntimeError("expected EIO")
    except OSError as e:
        check(e.errno == errno.EIO and s.offset == 2, "partial error")
    for action, expected in [(lambda: writen(Script(steps=(0,)).write, data), errno.EIO),
                             (lambda: readn(Script(data, (-errno.EAGAIN,)).read, 6), errno.EAGAIN)]:
        try:
            action()
            raise RuntimeError("expected failure")
        except OSError as e:
            check(e.errno == expected, "wrong error")
    print("errors partial=2 zero-write=EIO nonblocking=EAGAIN")
    s = Script(b"hi\n\0X\nYZQ")
    r = Rio(s.read)
    check(r.line(16) == b"hi\n" and len(r.buffer) == 5 and s.offset == 8, "read ahead")
    check(readn(r.read, 4) == b"\0X\nY" and r.line(16) == b"ZQ" and r.line(16) == b"", "mixed")
    print("buffer mixed line=3 body=4 tail=2 retained-after-line=5")
    r = Rio(Script(b"abcde\n").read)
    check(r.line(4) == b"abc" and r.line(4) == b"de\n", "long line")
    try:
        r.line(1)
        raise RuntimeError("expected EINVAL")
    except OSError as e:
        check(e.errno == errno.EINVAL, "capacity")
    print("long-line fragments=abc|de\\n capacity1=EINVAL")
    # This final check actually exercises a local POSIX pipe; the earlier
    # cases are deterministic models, with no OS signal delivery claim.
    import os
    rd, wr = os.pipe()
    try:
        check(writen(lambda b: os.write(wr, b), data) == 6, "pipe write")
    finally:
        os.close(wr)
    try:
        check(readn(lambda n: os.read(rd, n), 16) == data, "pipe read/EOF")
    finally:
        os.close(rd)
    print("host-pipe binary=6 EOF=observed")


if __name__ == "__main__":
    main()
