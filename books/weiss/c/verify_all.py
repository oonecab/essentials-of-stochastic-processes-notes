from pathlib import Path
import subprocess


HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "WEISS_2E_extracted"
figures = {path.name for path in SOURCE.iterdir() if path.is_file()}
c_files = {path.name[:-2] for path in HERE.glob("fig*.c")}
assert len(figures) == 171, f"expected 171 figures, got {len(figures)}"
assert figures == c_files, f"missing={figures - c_files}; extra={c_files - figures}"

arguments = {
    "fig1.2": ["5"],
    "fig1.3": ["0"],
    "fig1.4": ["123"],
    "fig2.9": ["3", "1", "3", "5"],
    "fig2.10": ["48", "18"],
    "fig2.11": ["2", "10"],
}
for number in (5, 6, 7, 8):
    arguments[f"fig2.{number}"] = ["4", "-3", "5", "-2"]

results = {}
for name in sorted(figures):
    executable = HERE / "bin" / name
    assert executable.is_file(), f"missing executable: {executable}"
    result = subprocess.run(
        [str(executable), *arguments.get(name, [])],
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    assert result.returncode == 0, f"{name}: exit={result.returncode}: {result.stderr}"
    assert result.stdout.strip(), f"{name}: empty output"
    results[name] = result.stdout.strip()

assert results["fig1.2"] == "F(5) = 141"
assert results["fig1.3"] == "Bad(0) = 0"
assert results["fig1.4"] == "123"
for number in (5, 6, 7, 8):
    assert "最大子序列和 = 6" in results[f"fig2.{number}"]
assert "位置 2" in results["fig2.9"]
assert results["fig2.10"] == "Gcd = 6"
assert results["fig2.11"] == "Pow = 1024"
for number in (2, 4, 8, 9, 10, 12, 14):
    assert results[f"fig7.{number}"] == "1 2 3 4 5 7 9"
assert results["fig10.40"].split(" = ")[1] == results["fig10.41"].split(" = ")[1]
assert results["fig10.43"] == results["fig10.45"]
assert results["fig10.54"] == results["fig10.55"]
assert "Find(6) is bottom = 1" in results["fig12.24"]
assert "Articulation vertices: 1 3" == results["fig9.67"]

print(f"Verified {len(figures)} source files, executables, and successful demo runs.")
