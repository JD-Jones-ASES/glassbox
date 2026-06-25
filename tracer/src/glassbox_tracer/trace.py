"""The heart: run a small Python program under ``sys.settrace`` and capture, per line, the program
state AFTER that line executes — across function calls.

Single frame (straight-line code). Each step shows the state its highlighted line produced, by pairing
the line with the next snapshot of the SAME frame; the frame's own return event closes its last line.
CPython fires a ``line`` event BEFORE a line runs, so pairing line L with the next same-frame snapshot
is what makes the converging final state (the whole point of swap) visible.

Multiple frames (functions). A ``call`` step shows a function being entered with its arguments; ``line``
steps inside show that frame's locals; a ``return`` step shows the value handed back. ``depth`` tracks
nesting so the player can render a call stack. Pairing is PER FRAME (matched by frame identity), so a
caller line that calls a function still shows its own frame's state once the call returns — e.g.
``m = find_max(xs)`` shows ``m`` set on the caller's next line.

Pure and deterministic: no wall-clock, no randomness. Executes only the supplied source, scoped to a
fixed filename so library / interpreter frames are never captured.
"""

from __future__ import annotations

import io
import sys
from contextlib import redirect_stdout

from .snapshot import Interner, safe_value, snapshot_locals

FILENAME = "<lesson>"


def trace(source: str, inputs: dict | None = None) -> list[dict]:
    """Execute ``source`` and return an ordered list of step dicts.

    Each step: ``{step, line, event[, frame, depth], state, stdout[, return_value][, value_flags]}``.
    ``frame``/``depth`` appear only when meaningful (inside a function, or on a call/return). ``inputs``
    predefine names in the program's global scope; they appear in ``state`` like any other variable.
    """
    code = compile(source, FILENAME, "exec")
    g: dict = {"__name__": "__lesson__"}
    if inputs:
        g.update(inputs)
    out = io.StringIO()

    raw: list[dict] = []          # ordered events across all frames
    frame_ids: dict[int, int] = {}  # id(frame) -> stable small int (survives recursion)
    next_fid = [0]
    depth = [0]
    interner = Interner()         # object ids for mutable containers, stable across the whole trace

    def fid(frame) -> int:
        key = id(frame)
        if key not in frame_ids:
            next_fid[0] += 1
            frame_ids[key] = next_fid[0]
        return frame_ids[key]

    def _tracer(frame, event, arg):
        if frame.f_code.co_filename != FILENAME:
            return None  # never descend into library / interpreter frames
        name = frame.f_code.co_name
        if event == "call":
            snap, flags, refs = snapshot_locals(frame.f_locals, interner)
            raw.append({"kind": "call", "fid": fid(frame), "name": name, "depth": depth[0],
                        "line": frame.f_lineno, "snap": snap, "flags": flags, "refs": refs,
                        "stdout": out.getvalue()})
            depth[0] += 1
            return _tracer
        if event == "line":
            snap, flags, refs = snapshot_locals(frame.f_locals, interner)
            raw.append({"kind": "line", "fid": fid(frame), "name": name, "depth": depth[0] - 1,
                        "line": frame.f_lineno, "snap": snap, "flags": flags, "refs": refs,
                        "stdout": out.getvalue()})
            return _tracer
        if event == "return":
            snap, flags, refs = snapshot_locals(frame.f_locals, interner)
            ret, ret_flags = safe_value(arg, interner)
            for k, reason in ret_flags.items():  # don't drop the return value's coercion reasons
                flags[k.replace("<value>", "return_value", 1)] = reason
            raw.append({"kind": "return", "fid": fid(frame), "name": name, "depth": depth[0] - 1,
                        "line": frame.f_lineno, "snap": snap, "flags": flags, "refs": refs,
                        "stdout": out.getvalue(), "ret": ret})
            depth[0] -= 1
            return _tracer
        return _tracer

    sys.settrace(_tracer)
    try:
        with redirect_stdout(out):
            exec(code, g)
    finally:
        sys.settrace(None)

    # Build display steps in natural reading order. A line's "after" state is the next snapshot of its
    # OWN frame, so we emit a line step only when that snapshot arrives — which means a line that calls a
    # function is emitted AFTER the call has expanded and returned (def -> call -> compute -> return ->
    # the caller's assignment lands). The "<module>" frame's call/return are interpreter bookkeeping and
    # are not shown, but the module return still flushes the last module line's final state.
    steps: list[dict] = []
    pending: dict[int, dict] = {}  # fid -> a line event awaiting its after-snapshot

    def emit(event, line, name, depth_i, snap, flags, refs, stdout, ret=None):
        step: dict = {"step": len(steps), "line": line, "event": event}
        if depth_i > 0 or event in ("call", "return"):
            step["frame"] = name
            step["depth"] = depth_i
        step["state"] = snap
        step["stdout"] = stdout
        if event == "return":
            step["return_value"] = ret
        if flags:
            step["value_flags"] = flags
        if refs:  # only present when aliasing/cycles make object identity meaningful
            step["refs"] = refs
        steps.append(step)

    for e in raw:
        prev = pending.pop(e["fid"], None)
        if prev is not None:
            # `e` is the next snapshot of prev's frame -> prev line's "after" state (snap/flags/refs
            # all describe that same successor snapshot).
            emit("line", prev["line"], prev["name"], prev["depth"], e["snap"], e["flags"], e["refs"],
                 e["stdout"])
        if e["kind"] == "line":
            pending[e["fid"]] = e
        elif e["name"] != "<module>":  # a call / return on a real function frame
            emit(e["kind"], e["line"], e["name"], e["depth"], e["snap"], e["flags"], e["refs"],
                 e["stdout"], ret=e.get("ret"))
    return steps
