"""Build step: ``lessons/<topic>/<register>.lesson.toml`` -> ``derived/<topic>/<register>.trace.json``.

Reads each authored lesson (TOML, stdlib ``tomllib``), runs the tracer over its ``source``, merges the
authored per-step notes (keyed by step index) and the abstraction / problem / provenance metadata, and
writes a schema-shaped JSON trace. Fails loud (``BuildError``) with the lesson path on any problem.
No third-party deps. Deterministic: stable key order, no wall-clock (``created`` is authored, not stamped).

The authoring contract enforced here is mirrored, for humans, in ``schemas/lesson.schema.json``; the
SHIPPED artifact is validated separately and authoritatively by ``scripts/validate/validate-traces.mjs``.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path

from . import BuildError, __version__
from .trace import trace

REGISTERS = {"naive", "procedural", "idiomatic", "clever"}
DOMAIN_MODELS = {"execution-derived", "author-asserted-simulation", "real-world-data"}
REQUIRED = ("id", "title", "register", "problem", "source", "author", "created")
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def _load_lesson(path: Path) -> dict:
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except OSError as e:
        raise BuildError(f"{path}: cannot read file: {e}") from e
    except tomllib.TOMLDecodeError as e:
        raise BuildError(f"{path}: invalid TOML: {e}") from e


def _validate_lesson(path: Path, lesson: dict) -> None:
    for key in REQUIRED:
        if key not in lesson:
            raise BuildError(f"{path}: missing required field '{key}'")
    if lesson["register"] not in REGISTERS:
        raise BuildError(f"{path}: register {lesson['register']!r} not in {sorted(REGISTERS)}")
    if not isinstance(lesson["source"], str) or not lesson["source"].strip():
        raise BuildError(f"{path}: 'source' must be a non-empty string")
    if not DATE_RE.fullmatch(str(lesson["created"])):
        raise BuildError(f"{path}: 'created' must be YYYY-MM-DD, got {lesson['created']!r}")
    language = lesson.get("language", "python")
    if language != "python":
        raise BuildError(f"{path}: only language='python' is supported in v1 (got {language!r})")
    domain_model = lesson.get("domain_model", "execution-derived")
    if domain_model not in DOMAIN_MODELS:
        raise BuildError(f"{path}: domain_model {domain_model!r} not in {sorted(DOMAIN_MODELS)}")
    for note in lesson.get("notes", []):
        if "step" not in note or "text" not in note:
            raise BuildError(f"{path}: every [[notes]] entry needs 'step' and 'text'")
    abstraction = lesson.get("abstraction")
    if abstraction is not None and "type" not in abstraction:
        raise BuildError(f"{path}: [abstraction] needs a 'type'")


def build_lesson(path: Path) -> dict:
    """Trace one lesson file and return the merged, schema-shaped trace object."""
    lesson = _load_lesson(path)
    _validate_lesson(path, lesson)

    try:
        steps = trace(lesson["source"], lesson.get("inputs"))
    except BuildError:
        raise
    except Exception as e:  # the traced program raised — name the lesson and re-raise loudly
        raise BuildError(f"{path}: tracing failed ({type(e).__name__}: {e})") from e
    if not steps:
        raise BuildError(f"{path}: 'source' produced no executable line events")

    # Merge author notes by step index.
    notes = {int(n["step"]): str(n["text"]) for n in lesson.get("notes", [])}
    out_of_range = sorted(s for s in notes if s < 0 or s >= len(steps))
    if out_of_range:
        raise BuildError(
            f"{path}: note step index out of range {out_of_range} (trace has {len(steps)} steps)"
        )
    for step in steps:
        if step["step"] in notes:
            step["note"] = notes[step["step"]]

    # An abstraction may only bind variables the trace actually surfaces at some point.
    abstraction = lesson.get("abstraction")
    if abstraction and "bind" in abstraction:
        seen: set[str] = set()
        for step in steps:
            seen.update(step["state"].keys())
        missing = [v for v in abstraction["bind"] if v not in seen]
        if missing:
            raise BuildError(
                f"{path}: abstraction.bind names variable(s) never in the trace: {missing}"
            )

    trace_obj: dict = {
        "id": lesson["id"],
        "title": lesson["title"],
        "problem": lesson["problem"],
        "register": lesson["register"],
        "language": "python",
        "derivation_source": "execution-derived",
        "domain_model": lesson.get("domain_model", "execution-derived"),
        "provenance": {
            "language": "python",
            "trace_source": "sys.settrace",
            "tracer_version": __version__,
            "author": str(lesson["author"]),
            "created": str(lesson["created"]),
        },
    }
    if abstraction:
        trace_obj["abstraction"] = abstraction
    trace_obj["source"] = lesson["source"]
    trace_obj["trace"] = steps
    return trace_obj


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="trace-lessons",
        description="Trace authored lessons into schema-shaped JSON traces.",
    )
    parser.add_argument("--lessons-dir", default="lessons")
    parser.add_argument("--out-dir", default="derived")
    parser.add_argument("--topic", default=None, help="only build this topic subdirectory")
    args = parser.parse_args(argv)

    root = Path.cwd()
    lessons_dir = (root / args.lessons_dir).resolve()
    out_dir = (root / args.out_dir).resolve()
    if not lessons_dir.is_dir():
        print(f"error: lessons dir not found: {lessons_dir}", file=sys.stderr)
        return 1

    pattern = f"{args.topic}/*.lesson.toml" if args.topic else "**/*.lesson.toml"
    paths = sorted(lessons_dir.glob(pattern))
    if not paths:
        print(f"error: no *.lesson.toml found under {lessons_dir}", file=sys.stderr)
        return 1

    built = 0
    try:
        for path in paths:
            trace_obj = build_lesson(path)
            rel = path.relative_to(lessons_dir)
            out_path = out_dir / rel.parent / path.name.replace(".lesson.toml", ".trace.json")
            out_path.parent.mkdir(parents=True, exist_ok=True)
            text = json.dumps(trace_obj, indent=2, ensure_ascii=False, allow_nan=False)
            out_path.write_text(text + "\n", encoding="utf-8")
            print(f"  traced {rel.as_posix()} -> "
                  f"{out_path.relative_to(root).as_posix()} ({len(trace_obj['trace'])} steps)")
            built += 1
    except BuildError as e:
        print(f"BUILD FAILED: {e}", file=sys.stderr)
        return 1

    print(f"OK: {built} trace(s) written under {out_dir.relative_to(root).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
