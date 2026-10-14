stages = (300, 200, 400)
register_ns = 20
serial_ns = sum(stages) + register_ns  # One output register for the entire path.
clock_ns = max(stages) + register_ns  # One register after every pipeline stage.
for n in (1, 4, 10):
    # Build stage occupancy; the last instruction reaches stage 2 at cycle n+2.
    schedule = [(i + stage + 1, i, stage) for i in range(n) for stage in range(3)]
    cycles = max(cycle for cycle, _, _ in schedule)
    print(f"n={n} seq-ns={n * serial_ns} pipe-cycles={cycles} pipe-ns={cycles * clock_ns}")
print("five-stage=4 instructions,1 stall,9 cycles")
