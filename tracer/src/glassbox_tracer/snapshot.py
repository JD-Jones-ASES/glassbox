"""JSON-safe serialization of a frame's locals for one trace step.

Honest by construction: any value that is not natively JSON-serializable is coerced to a tagged
`repr()` placeholder AND recorded in the step's ``value_flags``, so the player can never imply that a
displayed value is something it is not. Non-finite floats (nan/inf) are coerced too — they are not
valid JSON. Tuples render as arrays (flagged, since the tuple-ness is lost). Sets render as a
deterministic, element-sorted repr placeholder (so the byte output does not depend on PYTHONHASHSEED).
Dunder names (``__builtins__``, ``__name__``, …) are dropped — they are interpreter bookkeeping.

Object identity. Mutable containers (list, dict) are interned to small, stable integer ids held for the
whole trace (mirroring the frame ids in ``trace.py``). When two variables in the *same* snapshot are the
same object — the aliasing trap — they share an id, surfaced in the step's ``refs`` map so the player can
show "both names point at #2". A lone container carries no id (it would be noise), so scalar-only lessons
(swap) and per-frame single-name containers (functions) keep an empty ``refs`` and byte-identical output.
A container reachable from itself (a cycle) emits a ``{"__ref__": id}`` back-edge instead of recursing
forever. A dict with any non-string key renders as a tagged ``__map__`` entries list so no entry is lost
to a ``repr()`` key collision (``{1: 'a', '1': 'b'}`` must keep BOTH).
"""

from __future__ import annotations

import math
import re
from collections import Counter

# CPython object reprs embed a heap address (`<function f at 0x...>`) that varies per run. Strip it so
# traces stay deterministic (and don't churn in git). The name/kind is what's pedagogically useful.
_ADDR = re.compile(r" at 0x[0-9A-Fa-f]+")


class Interner:
    """Stable small-int ids for objects, assigned in first-encounter order and held for the whole
    trace (so the same list keeps its id across steps and across the names that alias it). Mirrors the
    frame-id interner in ``trace.py``. Never evicts: in straight-line lesson code containers outlive the
    trace, so id() recycling is a non-issue in practice."""

    def __init__(self) -> None:
        self._ids: dict[int, int] = {}
        self._n = 0

    def oid(self, value) -> int:
        key = id(value)
        if key not in self._ids:
            self._n += 1
            self._ids[key] = self._n
        return self._ids[key]


def _is_dunder(name: str) -> bool:
    return name.startswith("__")


def _set_repr(value) -> str:
    """Deterministic repr for a set/frozenset: elements sorted by their (address-free) repr, so the
    byte output is independent of PYTHONHASHSEED — which would otherwise reorder set reprs per run and
    churn the committed traces."""
    items = sorted(_ADDR.sub("", repr(x)) for x in value)
    body = ", ".join(items)
    if isinstance(value, frozenset):
        return f"frozenset({{{body}}})" if items else "frozenset()"
    return f"{{{body}}}" if items else "set()"


def _coerce(value, path: str, flags: dict, refs: dict, interner: Interner, seen: frozenset,
            cycle_oids: set):
    """Return a JSON-safe version of ``value``; record coercions in ``flags`` and container object ids
    in ``refs``. ``seen`` is the set of object ids on the current descent path (cycle detection)."""
    # bool first: it is an int subclass but should stay true/false.
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            flags[path] = "non-finite-float"
            return {"__repr__": repr(value), "__unserializable__": True}
        return value
    if isinstance(value, str):
        return value
    if isinstance(value, (list, dict)):
        oid = interner.oid(value)
        refs[path] = oid
        if id(value) in seen:
            cycle_oids.add(oid)
            flags[path] = "cycle"
            return {"__ref__": oid}
        seen = seen | {id(value)}  # path-scoped: siblings sharing a non-cyclic object are NOT a cycle
        if isinstance(value, list):
            return [_coerce(v, f"{path}[{i}]", flags, refs, interner, seen, cycle_oids)
                    for i, v in enumerate(value)]
        return _coerce_dict(value, path, flags, refs, interner, seen, cycle_oids)
    if isinstance(value, tuple):
        flags[path] = "tuple-as-array"
        return [_coerce(v, f"{path}[{i}]", flags, refs, interner, seen, cycle_oids)
                for i, v in enumerate(value)]
    if isinstance(value, (set, frozenset)):
        flags[path] = "repr-coerced"
        return {"__repr__": _set_repr(value), "__unserializable__": True}
    # Anything else (object, function, …) -> tagged, address-free repr placeholder.
    flags[path] = "repr-coerced"
    return {"__repr__": _ADDR.sub("", repr(value)), "__unserializable__": True}


def _coerce_dict(value: dict, path: str, flags: dict, refs: dict, interner: Interner,
                 seen: frozenset, cycle_oids: set):
    # All-string keys -> a plain JSON object (the common case; no flag, byte-identical to before).
    if all(isinstance(k, str) for k in value):
        return {k: _coerce(v, f"{path}.{k}", flags, refs, interner, seen, cycle_oids)
                for k, v in value.items()}
    # Any non-string key -> a tagged entries list so no entry is lost to a repr() key collision
    # (1 and "1" both repr to "1"; a plain object would silently drop one). Keys keep their typed repr;
    # the entry count is preserved.
    flags[path] = "dict-nonstring-keys"
    entries = []
    for i, (k, v) in enumerate(value.items()):
        key_repr = k if isinstance(k, str) else _ADDR.sub("", repr(k))
        entries.append([key_repr,
                        _coerce(v, f"{path}.[{i}]", flags, refs, interner, seen, cycle_oids)])
    return {"__map__": True, "entries": entries}


def safe_value(value, interner: Interner | None = None) -> tuple[object, dict]:
    """JSON-safe a single value (e.g. a function's return value). Returns ``(value, value_flags)``.
    Coercion reasons ARE reported (previously the return value's flags were dropped)."""
    if interner is None:
        interner = Interner()
    flags: dict = {}
    refs: dict = {}
    cycle_oids: set = set()
    coerced = _coerce(value, "<value>", flags, refs, interner, frozenset(), cycle_oids)
    return coerced, flags


def snapshot_locals(local_vars: dict, interner: Interner | None = None) -> tuple[dict, dict, dict]:
    """Snapshot in-scope locals into ``(state, value_flags, refs)``.

    ``state`` is a JSON-safe dict in variable-definition order; ``value_flags`` maps any coerced
    variable path to the reason and is empty for clean primitive state (the common case). ``refs`` maps
    a variable path to a small object id, but ONLY where it carries information: a container shared by
    two names in this snapshot (aliasing) or the target of a cycle back-edge. A lone container's id is
    dropped as noise, so scalar-only and single-name-container snapshots keep ``refs`` empty.
    """
    if interner is None:
        interner = Interner()
    state: dict = {}
    flags: dict = {}
    refs: dict = {}
    cycle_oids: set = set()
    for name, value in local_vars.items():
        if _is_dunder(name):
            continue
        state[name] = _coerce(value, name, flags, refs, interner, frozenset(), cycle_oids)
    counts = Counter(refs.values())
    kept = {p: o for p, o in refs.items() if counts[o] >= 2 or o in cycle_oids}
    return state, flags, kept
