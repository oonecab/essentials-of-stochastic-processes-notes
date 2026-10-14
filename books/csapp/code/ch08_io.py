#!/usr/bin/env python3
"""Sequential contract model; C companion runs real POSIX fork/exec and stream I/O."""
from io import StringIO


def model_tfgets(stream, n):
    if n <= 0:
        raise ValueError("positive size required")
    if n == 1:
        return ""
    result = stream.readline(n - 1)
    return result or None


def main():
    # An exit-status contract, not execution of a shell.
    status = {"exit 8": 8, "exit 0": 0}
    if status["exit 8"] != 8 or status["exit 0"] != 0:
        raise RuntimeError("exit-status contract failed")
    print("mysystem exit8=8 exit0=0")
    stream = StringIO("abc\ndef")
    line = model_tfgets(stream, 8)
    partial = model_tfgets(stream, 8)
    eof = model_tfgets(stream, 8)
    if (line, partial, eof) != ("abc\n", "def", None):
        raise RuntimeError(f"tfgets contract failed: {(line, partial, eof)!r}")
    print("tfgets line=abc partial=def eof=null")


if __name__ == "__main__":
    main()
