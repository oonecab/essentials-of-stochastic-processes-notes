import ctypes as ct
class Record(ct.Structure):
    _fields_ = [("c", ct.c_char), ("value", ct.c_long), ("flag", ct.c_short)]
print(f"long={ct.sizeof(ct.c_long)} pointer={ct.sizeof(ct.c_void_p)} int={ct.sizeof(ct.c_int)}")
print(f"record={Record.c.offset},{Record.value.offset},{Record.flag.offset} size={ct.sizeof(Record)}")
a = ((ct.c_int * 3) * 2)((0, 1, 2), (3, 4, 5))
offset = ct.addressof(a[1]) + 2 * ct.sizeof(ct.c_int) - ct.addressof(a)
print(f"array-offset={offset} value={a[1][2]}")
for x in range(-2, 3):
    print(f"affine={x},{3 * x + 7}")
