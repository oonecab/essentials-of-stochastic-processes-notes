#!/usr/bin/env python3
"""Job-state reference model. The C companion supplies the actual POSIX shell."""
from dataclasses import dataclass


@dataclass
class Job:
    pid: int
    jid: int
    state: str


def transition(job, event):
    if event == "stop":
        job.state = "stopped"
    elif event == "bg":
        job.state = "background"
    elif event == "fg":
        job.state = "foreground"
    elif event in ("exit", "signal"):
        job.state = "reaped"
    else:
        raise ValueError("unknown job event")


def main():
    job = Job(100, 1, "foreground")
    for event, state in [("stop", "stopped"), ("bg", "background"),
                         ("fg", "foreground"), ("exit", "reaped")]:
        transition(job, event)
        if job.state != state:
            raise RuntimeError(f"job transition failed: {event} -> {job.state}")
    jobs = {job.jid: job}
    del jobs[job.jid]
    if jobs:
        raise RuntimeError("reaped job remains registered")
    print("shell foreground-completed jobs=0")


if __name__ == "__main__":
    main()
