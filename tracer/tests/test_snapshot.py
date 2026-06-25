"""Snapshot serialization: JSON-safe, honest, dunder-free, identity-aware, deterministic."""

from glassbox_tracer.snapshot import Interner, _set_repr, snapshot_locals


def test_primitives_pass_through():
    state, flags, refs = snapshot_locals({"a": 1, "b": 2.5, "c": "x", "d": True, "e": None})
    assert state == {"a": 1, "b": 2.5, "c": "x", "d": True, "e": None}
    assert flags == {}
    assert refs == {}


def test_dunders_dropped():
    state, flags, _ = snapshot_locals({"__name__": "m", "__builtins__": {}, "x": 1})
    assert state == {"x": 1}
    assert flags == {}


def test_definition_order_preserved():
    state, _, _ = snapshot_locals({"a": 1, "b": 2, "temp": 3})
    assert list(state.keys()) == ["a", "b", "temp"]


def test_nested_list_passes_through():
    state, flags, _ = snapshot_locals({"xs": [1, 2, [3, 4]]})
    assert state == {"xs": [1, 2, [3, 4]]}
    assert flags == {}


def test_lone_container_carries_no_ref():
    # A single name for a list is not aliasing; emitting its id would be noise.
    _, _, refs = snapshot_locals({"xs": [1, 2, 3]})
    assert refs == {}


def test_non_finite_floats_coerced_and_flagged():
    state, flags, _ = snapshot_locals({"x": float("nan"), "y": float("inf")})
    assert state["x"]["__unserializable__"] is True
    assert state["y"]["__unserializable__"] is True
    assert flags["x"] == "non-finite-float"
    assert flags["y"] == "non-finite-float"


def test_set_coerced_flagged_and_deterministic():
    state, flags, _ = snapshot_locals({"s": {3, 1, 2}})
    assert state["s"]["__unserializable__"] is True
    assert flags["s"] == "repr-coerced"
    # sorted-by-repr => independent of PYTHONHASHSEED (would otherwise churn committed traces)
    assert state["s"]["__repr__"] == "{1, 2, 3}"


def test_set_repr_is_sorted_and_seed_independent():
    assert _set_repr({3, 1, 2}) == "{1, 2, 3}"
    assert _set_repr(set()) == "set()"
    assert _set_repr(frozenset({2, 1})) == "frozenset({1, 2})"
    # building the same set in a different insertion order yields identical bytes
    assert _set_repr({"b", "a", "c"}) == _set_repr({"c", "b", "a"})


def test_tuple_becomes_array_and_flagged():
    state, flags, _ = snapshot_locals({"t": (1, 2)})
    assert state["t"] == [1, 2]
    assert flags["t"] == "tuple-as-array"


def test_aliasing_two_names_share_a_ref_id():
    shared = []
    state, _, refs = snapshot_locals({"evens": shared, "odds": shared, "other": []})
    # both equal-and-empty, but evens/odds are the SAME object; `other` is a separate list.
    assert state["evens"] == [] and state["odds"] == []
    assert refs["evens"] == refs["odds"]
    assert "other" not in refs  # lone container => no ref


def test_nonstring_dict_keys_keep_all_entries():
    # 1 and "1" both repr to "1"; a plain object would silently drop one. The tagged map keeps both.
    state, flags, _ = snapshot_locals({"d": {1: "a", "1": "b"}})
    assert state["d"]["__map__"] is True
    assert len(state["d"]["entries"]) == 2
    assert flags["d"] == "dict-nonstring-keys"


def test_string_keyed_dict_stays_a_plain_object():
    state, flags, _ = snapshot_locals({"d": {"A": 1, "B": 2}})
    assert state["d"] == {"A": 1, "B": 2}
    assert flags == {}


def test_cycle_emits_backedge_not_infinite_recursion():
    a = []
    a.append(a)  # a self-referential list would RecursionError without the guard
    state, flags, refs = snapshot_locals({"a": a})
    assert state["a"][0]["__ref__"] == refs["a"]  # back-edge points at a's own id
    assert flags["a[0]"] == "cycle"


def test_shared_interner_gives_stable_ids_across_snapshots():
    interner = Interner()
    shared = []
    _, _, refs1 = snapshot_locals({"x": shared, "y": shared}, interner)
    _, _, refs2 = snapshot_locals({"x": shared, "y": shared}, interner)
    assert refs1["x"] == refs2["x"]  # same object keeps its id across steps
