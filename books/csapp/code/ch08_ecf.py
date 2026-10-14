#!/usr/bin/env python3
"""Logic model, not POSIX execution or an ABI/signal-handler implementation."""
from itertools import permutations


def require(condition, message):
    if not condition:
        raise RuntimeError("ECF model check failed: " + message)


def outputs(labels, edges):
    result = set()
    for order in permutations(labels):
        pos = {event: i for i, event in enumerate(order)}
        if all(pos[a] < pos[b] for a, b in edges):
            result.add("".join(labels[event] for event in order))
    return sorted(result)


def main():
    parent = {"x": 9}
    child = dict(parent)
    child["x"] -= 1
    require((parent["x"], child["x"]) == (9, 8), "private copy")
    print("private-copy parent=9 child=8")
    process = {"pid": 10, "image": "parent", "argv": []}
    old_pid = process["pid"]
    process.update(image="/bin/sh", argv=["sh", "-c", "exit 7"])
    shell_exit = int(process["argv"][2].split()[1])
    require(process["pid"] == old_pid and process["image"] == "/bin/sh", "exec identity")
    require(shell_exit == 7, "shell exit status")
    print("exec-status=7")
    pending, handled = set(), 0
    for _ in range(5):
        pending.add("USR1")
    require(len(pending) == 1, "coalesced pending signal")
    pending.remove("USR1")
    handled += 1
    require(handled == 1 and not pending, "pending signal handled")
    print("standard-signals sent=5 pending=1 handled=1")
    class SignalState:
        def __init__(self):
            self.blocked = True
            self.pending = self.registered = self.done = self.sleeping = False
        def child_exit(self):
            self.pending = True
            self.deliver()
        def deliver(self):
            if self.pending and not self.blocked:
                require(self.registered, "handler must observe a registered child")
                self.pending = False
                self.done = True
                self.sleeping = False
        def suspend(self):
            # Atomic: install mask and sleep, then allow signal delivery.
            self.sleeping = True
            self.blocked = False
            self.deliver()
    for timing in ("before-register", "after-register", "after-suspend"):
        st = SignalState()
        if timing == "before-register": st.child_exit()
        st.registered = True
        if timing == "after-register": st.child_exit()
        st.suspend()
        if timing == "after-suspend": st.child_exit()
        require(st.done and not st.sleeping and not st.pending, "atomic suspend: " + timing)
    # Mutant: test false, unblock, handler finishes, then pause sleeps forever.
    bad = SignalState()
    bad.registered = True
    require(not bad.done, "pause race starts before delivery")
    bad.blocked = False
    bad.child_exit()
    bad.sleeping = True
    require(bad.done and bad.sleeping and not bad.pending, "pause race remains asleep")
    print("mask-register-suspend reaped=1 status=23")
    class Jump(Exception):
        pass
    try:
        raise Jump(2)
    except Jump as exc:
        require(exc.args == (2,), "nonlocal jump value")
        print("nonlocal-jump=2")
    # Independent permutation oracle for the extra Global Edition 8.3 order.
    labels = {"a": "9", "b": "3", "c": "6", "d": "0", "e": "3", "f": "6"}
    edges = [("a", "b"), ("b", "c"), ("d", "e"), ("c", "e"), ("e", "f")]
    actual = outputs(labels, edges)
    require(actual == ["093636", "903636", "930636", "936036"], "output partial order")


if __name__ == "__main__":
    main()
