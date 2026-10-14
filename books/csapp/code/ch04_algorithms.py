"""Index cursor corresponding to the C pointer bubblesort; Python has no pointers."""

def bubble_p(data, count):
    if count < 2:
        return
    last = count - 1
    while last > 0:
        p = 0
        while p < last:
            if data[p + 1] < data[p]:
                t = data[p + 1]
                data[p + 1] = data[p]
                data[p] = t
            p += 1
        last -= 1


def switchv(idx):
    return {0: 0xaaa, 2: 0xbbb, 5: 0xbbb, 3: 0xccc}.get(idx, 0xddd)


if __name__ == '__main__':
    values = [5, -2, 5, 0, -(1 << 63), (1 << 63) - 1]
    bubble_p(values, len(values))
    print('sorted:' + ''.join(f' {x}' for x in values))
    for index in range(-1, 7):
        print(f'idx={index} value=0x{switchv(index):x}')
