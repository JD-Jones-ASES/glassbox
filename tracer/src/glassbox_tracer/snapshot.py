"""JSON-safe serialization of a frame's locals for one trace step.

Honest by construction: any value that is not natively JSON-serializable is coerced to a tagged
`repr()` placeholder AND recorded in the step's ``value_flags``, so the player can never imply that a
displayed value is something it is not. Non-finite floats (nan/inf) are coerced too — they are not
valid JSON. Tuples render as arrays (flagged, since the tuple-ness is lost). Dunder names
(``__builtins__``, ``__name__``, …) are dropped — they are interpreter bookkeeping, not lesson state.
"""

from __future__ import annotations

import math
import re

# CPython object reprs embed a heap address (`<function f at 0x...>`) that varies per run. Strip it so
# traces stay deterministic (and don't churn in git). The name/kind is what's pedagogically useful.
_ADDR = re.compile(r" at 0x[0-9A-Fa-f]+")


def _is_dunder(name: str) -> bool:
    return name.startswith("__")


def _coerce(value, path: str, flags: dict[str, str]):
    """Return a JSON-safe version of ``value``; on any coercion, record ``path -> reason`` in flags."""
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
    if isinstance(value, list):
        return [_coerce(v, f"{path}[{i}]", flags) for i, v in enumerate(value)]
    if isinstance(value, tuple):
        flags[path] = "tuple-as-array"
        return [_coerce(v, f"{path}[{i}]", flags) for i, v in enumerate(value)]
    if isinstance(value, dict):
        out: dict = {}
        for k, v in value.items():
            key = k if isinstance(k, str) else repr(k)
            if not isinstance(k, str):
                flags[path] = "dict-key-coerced"
            out[key] = _coerce(v, f"{path}.{key}", flags)
        return out
    # Anything else (set, object, function, …) -> tagged, address-free repr placeholder.
    flags[path] = "repr-coerced"
    return {"__repr__": _ADDR.sub("", repr(value)), "__unserializable__": True}


def safe_value(value) -> tuple[object, dict]:
    """JSON-safe a single value (e.g. a function's return value). Returns ``(value, value_flags)``."""
    flags: dict = {}
    return _coerce(value, "<value>", flags), flags


def snapshot_locals(local_vars: dict) -> tuple[dict, dict]:
    """Snapshot in-scope locals into ``(state, value_flags)``.

    ``state`` is a JSON-safe dict in variable-definition order; ``value_flags`` maps any coerced
    variable path to the reason and is empty for clean primitive state (the common case).
    """
    state: dict = {}
    flags: dict = {}
    for name, value in local_vars.items():
        if _is_dunder(name):
            continue
        state[name] = _coerce(value, name, flags)
    return state, flags
