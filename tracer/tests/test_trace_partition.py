"""Golden traces for the partition anchor — the loop/list proof that the engine generalizes past
straight-line swap, and that the clickable-line loop-walk has real repeated lines to walk.
"""

from glassbox_tracer.trace import trace

PROCEDURAL = (
    "nums = [3, 8, 5, 2]\n"
    "evens = []\n"
    "odds = []\n"
    "for n in nums:\n"
    "    if n % 2 == 0:\n"
    "        evens.append(n)\n"
    "    else:\n"
    "        odds.append(n)\n"
)
BUGGY = (
    "nums = [3, 8, 5, 2]\n"
    "evens = odds = []\n"
    "for n in nums:\n"
    "    if n % 2 == 0:\n"
    "        evens.append(n)\n"
    "    else:\n"
    "        odds.append(n)\n"
)


def test_procedural_partition_final_state():
    steps = trace(PROCEDURAL)
    assert steps[-1]["state"]["evens"] == [8, 2]
    assert steps[-1]["state"]["odds"] == [3, 5]


def test_loop_line_recurs_for_clickable_walk():
    # the `for` line (line 4) fires once per item plus the final exit check -> the loop-walk has
    # multiple steps to cycle through when a learner clicks that line repeatedly.
    steps = trace(PROCEDURAL)
    for_steps = [s for s in steps if s["line"] == 4]
    assert len(for_steps) == 5  # 4 items + the exit check


def test_n_advances_through_items_in_order():
    steps = trace(PROCEDURAL)
    seen_n = [s["state"]["n"] for s in steps if "n" in s["state"]]
    assert seen_n[0] == 3
    assert {3, 8, 5, 2} <= set(seen_n)


def test_aliasing_bug_makes_both_piles_identical():
    steps = trace(BUGGY)
    final = steps[-1]["state"]
    # evens = odds = [] aliases one list, so both names accumulate every number.
    assert final["evens"] == [3, 8, 5, 2]
    assert final["odds"] == [3, 8, 5, 2]
    # and they track identically at every step where both exist.
    for s in steps:
        st = s["state"]
        if "evens" in st and "odds" in st:
            assert st["evens"] == st["odds"]


def test_lists_serialize_as_arrays_without_flags():
    for src in (PROCEDURAL, BUGGY):
        for s in trace(src):
            assert "value_flags" not in s
            assert isinstance(s["state"].get("nums"), list)
