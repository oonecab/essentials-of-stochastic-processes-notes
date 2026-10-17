"""Enumerate D_n by breadth-first search; words execute left to right."""
import sys


def enumerate_group(n):
    if type(n) is not int or not 3 <= n <= 12:
        raise ValueError("n must be an integer from 3 through 12")
    # (sign, shift) means vertex x goes to sign*x + shift modulo n.
    states, words = [(1, 0)], [""]
    index = {states[0]: 0}
    edges = []
    head = 0
    while head < len(states):
        sign, shift = states[head]
        destinations = []
        for letter, target in (("r", (sign, (shift + 1) % n)),
                               ("f", (-sign, (-shift) % n))):
            if target not in index:
                index[target] = len(states)
                states.append(target)
                words.append(words[head] + letter)
            destinations.append(index[target])
        edges.append(tuple(destinations))
        head += 1
    return states, words, edges


def main(args):
    if len(args) > 1 or (args and args[0] not in [str(i) for i in range(3, 13)]):
        raise ValueError("usage: cayley.py [3..12]")
    n = int(args[0]) if args else 4
    states, words, edges = enumerate_group(n)
    print(f"D{n}: {len(states)} actions")
    print("id word sign shift r f")
    for i, ((sign, shift), word, (r, f)) in enumerate(zip(states, words, edges)):
        print(i, word or "e", sign, shift, r, f)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except ValueError as error:
        print(error, file=sys.stderr)
        sys.exit(2)
