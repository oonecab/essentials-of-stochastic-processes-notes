def speedup(fraction, factor):
    return 1.0 / ((1.0 - fraction) + fraction / factor)


fraction = 0.6
for factor in (1.0, 1.5, 3.0, 10.0):
    print(f"alpha={fraction:.1f} k={factor:.1f} speedup={speedup(fraction, factor):.6f}")
print(f"limit={1.0 / (1.0 - fraction):.6f}")
target, improved_fraction = 4.0, 0.9
denominator = 1.0 / target - (1.0 - improved_fraction)
if denominator <= 0.0:
    raise ValueError("Target has no finite positive solution")
print(f"required-k={improved_fraction / denominator:.6f}")
