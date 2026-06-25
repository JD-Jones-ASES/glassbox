"""Snapshot serialization: JSON-safe, honest, dunder-free."""

from glassbox_tracer.snapshot import snapshot_locals


def test_primitives_pass_through():
    state, flags = snapshot_locals({"a": 1, "b": 2.5, "c": "x", "d": True, "e": None})
    assert state == {"a": 1, "b": 2.5, "c": "x", "d": True, "e": None}
    assert flags == {}


def test_dunders_dropped():
    state, flags = snapshot_locals({"__name__": "m", "__builtins__": {}, "x": 1})
    assert state == {"x": 1}
    assert flags == {}


def test_definition_order_preserved():
    state, _ = snapshot_locals({"a": 1, "b": 2, "temp": 3})
    assert list(state.keys()) == ["a", "b", "temp"]


def test_nested_list_passes_through():
    state, flags = snapshot_locals({"xs": [1, 2, [3, 4]]})
    assert state == {"xs": [1, 2, [3, 4]]}
    assert flags == {}


def test_non_finite_floats_coerced_and_flagged():
    state, flags = snapshot_locals({"x": float("nan"), "y": float("inf")})
    assert state["x"]["__unserializable__"] is True
    assert state["y"]["__unserializable__"] is True
    assert flags["x"] == "non-finite-float"
    assert flags["y"] == "non-finite-float"


def test_unserializable_object_flagged():
    state, flags = snapshot_locals({"s": {1, 2, 3}})  # a set is not JSON-native
    assert state["s"]["__unserializable__"] is True
    assert flags["s"] == "repr-coerced"


def test_tuple_becomes_array_and_flagged():
    state, flags = snapshot_locals({"t": (1, 2)})
    assert state["t"] == [1, 2]
    assert flags["t"] == "tuple-as-array"
