"""Run host/tool observations in an explicitly supplied disposable directory.
Usage (repository root): python3 books/csapp/code/ch07_probe.py tmp/csapp/ch07-probe
The model programs have separate deterministic C/Python output contracts.
"""
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: ch07_probe.py output-directory")
    source = Path(__file__).resolve().parent
    out = Path(sys.argv[1]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    cc = shutil.which("clang") or shutil.which("cc")
    if not cc:
        raise SystemExit("no C compiler found")
    records = []

    def run(args, expected=0):
        result = subprocess.run([str(a) for a in args], capture_output=True, text=True)
        records.append({"command": [str(a).replace(str(source), "SOURCE").replace(str(out), "OUTPUT") for a in args],
                        "returncode": result.returncode,
                        "stdout": result.stdout.replace(str(out), "OUTPUT"),
                        "stderr": result.stderr.replace(str(out), "OUTPUT")})
        if expected is not None and result.returncode != expected:
            raise RuntimeError(f"unexpected status {result.returncode}: {args[0]}")
        return result

    flags = [cc, "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic"]
    run([cc, "--version"])
    for stem in ["main", "sum"]:
        run(flags + ["-Og", "-c", source / f"ch07_link_{stem}.c", "-o", out / f"{stem}.o"])
    run(["ar", "rcs", out / "libsum.a", out / "sum.o"])
    run(["ar", "t", out / "libsum.a"])
    run([cc, out / "main.o", out / "libsum.a", "-o", out / "linked"])
    run([out / "linked"])
    missing = run([cc, out / "main.o", "-o", out / "missing"], expected=None)
    if missing.returncode == 0:
        raise RuntimeError("missing-symbol link unexpectedly succeeded")
    run(["nm", out / "main.o"])
    # A no-header example permits ELF cross-compilation without a Linux sysroot.
    run(flags + ["-target", "x86_64-linux-gnu", "-Og", "-fno-pic", "-fno-pie", "-c",
                 source / "ch07_link_main.c", "-o", out / "main-elf.o"])
    run(["file", out / "main-elf.o"])
    run(["objdump", "-dr", out / "main-elf.o"])
    host = platform.system()
    ext = ".dylib" if host == "Darwin" else ".so"
    shared_flags = ["-dynamiclib"] if host == "Darwin" else ["-shared", "-fPIC"]
    run(flags + shared_flags + [source / "ch07_plugin.c", "-o", out / ("plugin" + ext)])
    run(flags + shared_flags + [source / "ch07_link_sum.c", "-o", out / ("wrong" + ext)])
    run(flags + [source / "ch07_dlopen.c", "-o", out / "loader"] + ([] if host == "Darwin" else ["-ldl"]))
    run([out / "loader", out / ("plugin" + ext)])
    run([out / "loader", out / "does-not-exist"], expected=1)
    run([out / "loader", out / ("wrong" + ext)], expected=1)
    # Compare actual text-section bytes, rather than whole object files with debug info.
    run(flags + ["-Og", "-g", "-c", source / "ch07_link_sum.c", "-o", out / "sum-debug.o"])
    if host == "Darwin":
        plain = run(["otool", "-s", "__TEXT", "__text", out / "sum.o"]).stdout.splitlines()[2:]
        debug = run(["otool", "-s", "__TEXT", "__text", out / "sum-debug.o"]).stdout.splitlines()[2:]
        code_equal = plain == debug
        if not code_equal:
            raise RuntimeError("debug switch changed this sample's instruction bytes")
        run(["otool", "-L", Path(cc).resolve()])
    else:
        code_equal = None
    archives = {}
    for name in ["libc.a", "libm.a"]:
        result = run([cc, "-print-file-name=" + name])
        location = Path(result.stdout.strip())
        if location.is_file():
            archives[name] = len(run(["ar", "t", location]).stdout.splitlines())
        else:
            archives[name] = None
    report = {"host": host, "machine": platform.machine(),
              "native_archive_link": True, "missing_symbol_rejected": True,
              "native_dlopen_success_and_two_failures": True,
              "elf_cross_target_inspected_not_executed": True,
              "sample_Og_vs_Og_g_text_equal": code_equal,
              "system_archive_member_counts": archives, "records": records}
    (out / "probe-results.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "records"}, indent=2))


if __name__ == "__main__":
    main()
