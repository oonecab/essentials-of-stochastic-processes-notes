MASK = (1 << 64) - 1
def sum_two(a):
    acc0 = acc1 = 0
    i = 0
    while i + 1 < len(a):
        acc0 = (acc0 + a[i]) & MASK
        acc1 = (acc1 + a[i + 1]) & MASK
        i += 2
    if i < len(a):
        acc0 = (acc0 + a[i]) & MASK
    return (acc0 + acc1) & MASK
values = [i * i + 3 for i in range(65)]
values[0] = MASK
for n in (0, 1, 2, 3, 4, 5, 7, 8, 17, 64, 65):
    result = sum_two(values[:n])
    if result != sum(values[:n]) % (1 << 64):
        raise SystemExit(3)
    print(f"n={n} sum={result}")
