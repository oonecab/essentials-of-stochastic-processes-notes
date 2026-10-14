"""Textbook archive scan, using named sets instead of C bit masks."""
MODULES = {
    "p": ({"p"}, {"x1"}),
    "x1": ({"x1"}, {"y"}),
    "x2": ({"x2"}, {"p"}),
    "y": ({"y"}, {"x2"}),
}
ARCHIVES = {"x": ["x2", "x1"], "y": ["y"], "a": ["x2", "y", "x1"]}
BITS = {"p": 1, "x1": 2, "x2": 4, "y": 8}


def run(name, order):
    included, defined, unresolved = [], set(), set()

    def include(member):
        nonlocal unresolved
        defs, uses = MODULES[member]
        included.append(member)
        defined.update(defs)
        unresolved = (unresolved | uses) - defined

    for item in order:
        if item == "p":
            include("p")
            continue
        while True:
            before = len(included)
            for member in ARCHIVES[item]:
                if member not in included and MODULES[member][0] & unresolved:
                    include(member)
            if len(included) == before:
                break
    mask = sum(BITS[symbol] for symbol in unresolved)
    print(name + ":" + "".join(" " + m for m in included)
          + f" | unresolved={mask}")
    return mask


def main():
    for name, order, expected in [
        ("good", "pxyx", 0), ("one-pass", "pxy", 4),
        ("early-archive", "xpy", 2), ("combined", "pa", 0),
        ("empty-input", "", 0), ("unused-libraries", "xy", 0),
    ]:
        if run(name, order) != expected:
            raise RuntimeError(f"incorrect archive extraction: {name}")


if __name__ == "__main__":
    main()
