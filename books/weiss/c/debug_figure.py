"""Build one figure with debug symbols for the VS Code launch configuration."""

from pathlib import Path
import re
import subprocess
import sys


HERE = Path(__file__).resolve().parent
DEBUG_FLAGS = "-std=c11 -Wall -Wextra -Werror -pedantic -O0 -g"


def main() -> int:
    if len(sys.argv) != 2:
        print("用法：python3 debug_figure.py fig3.10", file=sys.stderr)
        return 2

    figure = sys.argv[1].strip()
    source = HERE / f"{figure}.c"
    if not re.fullmatch(r"fig(?:[0-9]+|PG)\.[0-9]+[a-z]?", figure) or not source.is_file():
        print(f"不存在图例入口：{figure}（请输入 fig3.10 这样的名称）", file=sys.stderr)
        return 2

    build = subprocess.run(
        ["make", "-B", f"CFLAGS={DEBUG_FLAGS}", f"bin/{figure}"],
        cwd=HERE,
        check=False,
    )
    if build.returncode != 0:
        return build.returncode

    debug_link = HERE / "bin" / "debug-figure"
    if debug_link.is_symlink():
        debug_link.unlink()
    elif debug_link.exists():
        print(f"调试入口已被其他文件占用：{debug_link}", file=sys.stderr)
        return 2
    debug_link.symlink_to(figure)
    print(f"调试入口：{debug_link} -> {figure}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
