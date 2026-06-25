"""GlassBox tracer: a build-time `sys.settrace` producer.

`(source, inputs) -> schema-valid JSON execution trace`. Stdlib-only, pure, deterministic. Its output
IS CPython's behavior, so a trace can never drift from reality — that is the whole pedagogical contract.
Invariants live in /AGENTS.md; the trace schema in /schemas/trace.schema.json.
"""

__version__ = "0.1.0"


class BuildError(Exception):
    """Loud, named build failure. The message must identify the offending lesson path / step."""
