"""Echo one text line in bounded chunks; exit 3 on I/O failure."""
import sys

def good_echo(src,dst):
    try:
        while True:
            chunk=src.readline(255)
            if chunk=="":
                break
            dst.write(chunk)
            if chunk.endswith("\n"):
                break
        dst.flush()
        return 0
    except (OSError,ValueError):
        return 3

if __name__=="__main__":
    raise SystemExit(good_echo(sys.stdin,sys.stdout))
