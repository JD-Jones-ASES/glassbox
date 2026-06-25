"""Golden traces for the three swap registers — the Phase 0 proof of the instrument.

"state after the line executes" semantics: step i highlights source line i+1 (1-indexed) and shows
the program state that line produced. The whole point is that the converging final state is visible.
"""

from glassbox_tracer.trace import trace

BUGGY = "a = 1\nb = 2\na = b\nb = a\n"
PROCEDURAL = "a = 1\nb = 2\ntemp = a\na = b\nb = temp\n"
IDIOMATIC = "a = 1\nb = 2\na, b = b, a\n"


def _states(steps):
    return [s["state"] for s in steps]


def _lines(steps):
    return [s["line"] for s in steps]


def test_buggy_overwrites_and_both_end_equal():
    steps = trace(BUGGY)
    assert _lines(steps) == [1, 2, 3, 4]
    assert _states(steps) == [
        {"a": 1},
        {"a": 1, "b": 2},
        {"a": 2, "b": 2},
        {"a": 2, "b": 2},
    ]
    # The bug, shown by CPython, not asserted: both cups end up holding the same value.
    final = steps[-1]["state"]
    assert final["a"] == final["b"] == 2


def test_procedural_temp_saves_the_swap():
    steps = trace(PROCEDURAL)
    assert _lines(steps) == [1, 2, 3, 4, 5]
    assert _states(steps) == [
        {"a": 1},
        {"a": 1, "b": 2},
        {"a": 1, "b": 2, "temp": 1},
        {"a": 2, "b": 2, "temp": 1},
        {"a": 2, "b": 1, "temp": 1},
    ]


def test_idiomatic_swaps_in_a_single_step():
    steps = trace(IDIOMATIC)
    assert _lines(steps) == [1, 2, 3]
    assert _states(steps) == [
        {"a": 1},
        {"a": 1, "b": 2},
        {"a": 2, "b": 1},  # tuple pack/unpack: both swap "in the air" in one line
    ]


def test_steps_are_sequential_from_zero():
    steps = trace(PROCEDURAL)
    assert [s["step"] for s in steps] == list(range(len(steps)))


def test_int_swaps_have_no_value_flags_and_empty_stdout():
    for src in (BUGGY, PROCEDURAL, IDIOMATIC):
        for s in trace(src):
            assert "value_flags" not in s
            assert s["stdout"] == ""
            assert s["event"] == "line"


def test_trace_is_deterministic():
    assert trace(PROCEDURAL) == trace(PROCEDURAL)
    assert trace(BUGGY) == trace(BUGGY)
