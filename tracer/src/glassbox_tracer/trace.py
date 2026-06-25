"""The heart: run a small Python program under ``sys.settrace`` and capture, per line, the program
state AFTER that line executes.

Why the re-pairing. CPython fires a ``line`` event *before* a line runs, so a raw line-event
snapshot shows state BEFORE the line. We want the pedagogical reading "highlight line L, here is the
state it produces", so each step pairs line L with the snapshot taken on arrival at the *next* line
(which reflects L's effect), and a final post-execution snapshot closes the last line. That makes the
converging final state — the entire point of the swap lesson — actually visible.

Pure and deterministic: no wall-clock, no randomness. It executes only the supplied source, scoped to
a fixed filename so library/internal frames are never captured.
"""

from __future__ import annotations

import io
import sys
from contextlib import redirect_stdout

from .snapshot import snapshot_locals

# Source is compiled to this filename so the trace function can scope itself to the lesson's own
# frames and never descend into the interpreter's or the stdlib's code.
FILENAME = "<lesson>"


def trace(source: str, inputs: dict | None = None) -> list[dict]:
    """Execute ``source`` and return an ordered list of step dicts.

    Each step: ``{step, line, event, state, stdout[, value_flags]}``. ``inputs`` predefine names in the
    program's global scope (e.g. a list to search); they appear in ``state`` like any other variable.
    Raises whatever the traced program raises (the caller turns that into a named build failure).
    """
    code = compile(source, FILENAME, "exec")
    g: dict = {"__name__": "__lesson__"}
    if inputs:
        g.update(inputs)

    # raw[i] = (line, state, flags, stdout) captured on ARRIVAL at that line (i.e. BEFORE it runs).
    raw: list[tuple[int, dict, dict, str]] = []
    out = io.StringIO()

    def _tracer(frame, event, arg):
        if frame.f_code.co_filename != FILENAME:
            return None  # never descend into library / interpreter frames
        if event == "line":
            state, flags = snapshot_locals(frame.f_locals)
            raw.append((frame.f_lineno, state, flags, out.getvalue()))
        return _tracer

    sys.settrace(_tracer)
    try:
        with redirect_stdout(out):
            exec(code, g)
    finally:
        sys.settrace(None)

    final_state, final_flags = snapshot_locals(g)
    final_stdout = out.getvalue()

    # Re-pair: step i shows line raw[i].line with the state it PRODUCED — the snapshot captured on
    # arrival at the next line, or the final post-exec snapshot for the last line.
    steps: list[dict] = []
    for i, (line, _state_before, _flags_before, _stdout_before) in enumerate(raw):
        if i + 1 < len(raw):
            _, state, flags, stdout = raw[i + 1]
        else:
            state, flags, stdout = final_state, final_flags, final_stdout
        step: dict = {
            "step": i,
            "line": line,
            "event": "line",
            "state": state,
            "stdout": stdout,
        }
        if flags:
            step["value_flags"] = flags
        steps.append(step)
    return steps
