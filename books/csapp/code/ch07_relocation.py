"""Bounded arithmetic model of R_X86_64_PC32 / R_X86_64_32."""


def relocate(symbol, addend, place, pc_relative):
    if not (0 <= symbol <= 0xffffffff and 0 <= place <= 0xffffffff
            and -(1 << 31) <= addend < (1 << 31)):
        raise ValueError("input outside the model's 32-bit domain")
    value = symbol + addend - (place if pc_relative else 0)
    low, high = (-(1 << 31), (1 << 31) - 1) if pc_relative else (0, 0xffffffff)
    if not low <= value <= high:
        return None
    return (value & 0xffffffff).to_bytes(4, "little")


def main():
    cases = [
        ("sum", 0x4004e8, -4, 0x4004df, True, 5),
        ("swap", 0x4004e8, -4, 0x4004da, True, 10),
        ("7.12A", 0x4004f8, -4, 0x4004ea, True, 10),
        ("7.12B", 0x400500, -4, 0x4004da, True, 34),
        ("array", 0x601018, 0, 0, False, 0x601018),
        ("backward", 0x4004d0, -4, 0x4004df, True, 0xffffffed),
        ("pc-max", 0x7fffffff, 0, 0, True, 0x7fffffff),
        ("pc-min", 0, 0, 0x80000000, True, 0x80000000),
        ("pc-too-high", 0x80000000, 0, 0, True, None),
        ("pc-too-low", 0, -1, 0x80000000, True, None),
        ("abs-max", 0xffffffff, 0, 0, False, 0xffffffff),
        ("abs-overflow", 0xffffffff, 1, 0, False, None),
        ("abs-negative", 0, -1, 0, False, None),
    ]
    for name, symbol, addend, place, relative, expected in cases:
        result = relocate(symbol, addend, place, relative)
        if (None if result is None else int.from_bytes(result, "little")) != expected:
            raise RuntimeError(f"wrong relocation: {name}")
        print(f"{name}:" + (" rejected" if result is None else
                            "".join(f" {byte:02x}" for byte in result)))


if __name__ == "__main__":
    main()
