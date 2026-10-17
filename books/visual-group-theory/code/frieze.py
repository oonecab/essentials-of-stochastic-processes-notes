"""Exact affine actions on a frieze. h is a flip, g/G are inverse glides."""
import sys


def evaluate(word):
    if len(word) > 10000 or any(letter not in "hgG" for letter in word):
        raise ValueError("word must contain at most 10000 letters from h,g,G")
    sx, sy, dx = 1, 1, 0
    for letter in word:
        if letter == "h":
            sx, dx = -sx, -dx
        else:
            sy = -sy
            dx += 1 if letter == "g" else -1
    return sx, sy, dx


def main(args):
    if len(args) > 1:
        raise ValueError("usage: frieze.py [word]")
    words = args if args else ["", "h", "g", "G", "gg", "hgh", "hghg", "ghgh"]
    results = [evaluate(word) for word in words]
    print("word sx sy dx")
    for word, (sx, sy, dx) in zip(words, results):
        print(word or "e", sx, sy, dx)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except ValueError as error:
        print(error, file=sys.stderr)
        sys.exit(2)
