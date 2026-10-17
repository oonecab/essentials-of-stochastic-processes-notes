#!/usr/bin/env python3
"""Three distinct pictures; words execute from left to right."""
import sys

IDENTITY = (0, 1, 2)


def step(state, action):
    if tuple(sorted(state)) != IDENTITY:
        raise ValueError("state must be a permutation of 0, 1, 2")
    if action not in ("a", "b"):
        raise ValueError("actions must be a or b")
    result = list(state)
    left = 0 if action == "a" else 1
    result[left], result[left + 1] = result[left + 1], result[left]
    return tuple(result)


def apply_word(word, state=IDENTITY):
    if tuple(sorted(state)) != IDENTITY:
        raise ValueError("state must be a permutation of 0, 1, 2")
    if any(action not in "ab" for action in word):
        raise ValueError("word must contain only a and b")
    for action in word:
        state = step(state, action)
    return state


def enumerate_actions():
    states, words = [IDENTITY], [""]
    head = 0
    while head < len(states):
        for action in "ab":
            target = step(states[head], action)
            if target not in states:
                states.append(target)
                words.append(words[head] + action)
        head += 1
    return list(zip(words, states))


def format_state(state):
    return "".join("ABC"[value] for value in state)


def main():
    if len(sys.argv) > 2:
        print("usage: actions.py [word of a and b]", file=sys.stderr)
        return 2
    if len(sys.argv) == 2:
        try:
            result = apply_word(sys.argv[1])
        except ValueError as error:
            print(error, file=sys.stderr)
            return 2
        print(format_state(result))
    else:
        for word, state in enumerate_actions():
            print(f"{word or 'e'} {format_state(state)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
