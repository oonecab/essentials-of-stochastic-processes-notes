import struct
import sys
for u in range(256):
    signed = sum(((u >> i) & 1) * (-(1 << 7) if i == 7 else (1 << i)) for i in range(8))
    print(f"u={u} signed={signed} plus1={(u + 1) % 256}")
print("bytes=" + (0x12345678).to_bytes(4, sys.byteorder).hex())
print("double1=" + struct.pack(">d", 1.0).hex())
a, b, c = 1.0e16, -1.0e16, 1.0
print(f"grouping={(a + b) + c:.0f},{a + (b + c):.0f}")
