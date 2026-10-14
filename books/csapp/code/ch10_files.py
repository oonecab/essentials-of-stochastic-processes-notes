#!/usr/bin/env python3
"""Open-file-description reference model. Does not invoke fork or dup2."""
from dataclasses import dataclass


@dataclass
class OpenFile:
    data: bytes
    offset: int = 0

    def read(self):
        result = self.data[self.offset:self.offset + 1]
        self.offset += len(result)
        return result


def check(value):
    if not value:
        raise RuntimeError("descriptor reference model failed")


def main():
    a, b = OpenFile(b"foobar"), OpenFile(b"foobar")
    check(a.read() == b"f" and b.read() == b"f")
    independent = "f"
    a = b  # dup2: reference the same open description, not a value copy.
    shared = a.read().decode("ascii")
    check(shared == "o" and b.offset == 2)
    a.offset = 0
    parent = {3: a, 4: b}
    child = dict(parent)  # copied descriptor table; shared description objects.
    check(child[3].read() == b"f")
    child.clear()       # model wait for the child's completed read and exit.
    inherited = parent[3].read().decode("ascii")
    check(inherited == "o" and parent[4].offset == 2)
    print(f"independent={independent} dup2-shared={shared} fork-shared={inherited}")
    print("metadata regular=yes size=6 shared-offset=2")
    del parent[3]
    check(parent[4].read() == b"o")
    print("close-one remaining-byte=o")


if __name__ == "__main__":
    main()
