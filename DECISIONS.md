# DECISIONS — architecture decision log

Newest at the bottom. Each entry: context → decision → consequences. Keep terse; this is a contract, not a
manual.

---

## ADR-0001 — Mirror the Spengler Portal stack; do not invent a new one (2026-06-25)

**Context.** GlassBox is the third technical project in the line `RealStats → Mechanic → this`. Two sibling
repos already encode the house stack and methodology.

**Decision.** Mirror the Spengler Portal (`Decline`) exactly: **Astro 7** `output: "static"`,
`trailingSlash: "always"`, **Svelte 5** islands hydrated `client:visible`, vanilla ES modules + CSS custom
properties (no framework), **Ajv** (draft 2020-12, `additionalProperties:false`) as the validation gate,
`base = /glassbox` with a `LOCAL_ROOT=1` preview escape hatch. Carry `Mechanic`'s producer/audit discipline
(a deterministic build-time producer whose output is ground truth).

**Consequences.** No bespoke build system to maintain; an agent fluent in the siblings is fluent here.

## ADR-0002 — The `sys.settrace` tracer is the build-time producer (2026-06-25)

**Context.** The pedagogical contract is that displayed state is real execution output. We need a producer
whose output cannot drift from reality.

**Decision.** A pure Python function `(source, inputs) → trace` built on `sys.settrace`, packaged as a `uv`
package (`tracer/`) shaped like `Mechanic/pipeline` — `pyproject.toml` console entry point, `src/` modules,
`tests/` (pytest), a `BuildError` raised with context, deterministic (no wall-clock, no randomness). The
whole tracer is **stdlib-only and pure** — the merge orchestrator (`build.py`) reads authored TOML via
stdlib `tomllib`, so there are no third-party Python deps. The tracer is the structural analogue of Mechanic's SymPy stage and earns
the same audit rigor; it must be bulletproof (golden-trace tests pass) before any lesson is authored.

**Consequences.** Traces are CPython's actual behavior. The frontend never runs Python; the day we want a
"trace your own code" sandbox, Pyodide can run the same tracer client-side and emit the same JSON.

## ADR-0003 — One trace schema, hardened with an explicit honesty model (2026-06-25)

**Context.** Most lessons are traced Python (execution-derived). A few processes resist being modeled as
code and may ship as hand-authored process traces, and some claims (e.g. "what's recoverable" in lossy
compression) are author assertions, not execution facts. A polished animation must not imply a guarantee
the engine didn't produce.

**Decision.** A single `schemas/trace.schema.json`. Adopt Mechanic's author-asserted-vs-derived split:
top-level `derivation_source` (`execution-derived | author-asserted | hybrid`) + `provenance`
(`language`, `trace_source`, `tracer_version`, `author`, `created`); per-step `step_provenance` and
`value_flags` (the "tainted symbol" idea at step granularity, plus honesty about `repr()`-coerced values).
The Ajv gate cross-checks `provenance.trace_source` against `derivation_source` and fails on a
contradiction (the Spengler drift-killer pattern). A `checkpoint` flag is reserved for the future quiz
primitive (data model only; no UI in v1).

**Consequences.** Trust is by construction and visible to the reader (per-lesson badge + `/verification/`).

## ADR-0004 — Provider-agnostic, enforced by a build gate (2026-06-25)

**Context.** The project must not name any specific course, exam, or standards body. Discipline alone leaks.

**Decision.** Reframe the content as a neutral "how computers actually work" curriculum (pillars: Programs
& State, Data, Systems & Networks). The original course-mapped founding brief is kept **gitignored**
(`PROJECT_BRIEF.md`) as internal reference. A build gate (`scripts/validate/scan-text.mjs`) greps all
committed content for banned terms and fails the build on a hit.

**Consequences.** The constraint is enforced, not hoped for. Internal pedagogy mapping stays private.

## ADR-0005 — Authoring in TOML, notes merged by step index (2026-06-25)

**Context.** The human layer (source + per-step notes + abstraction spec) must stay separate from the pure
trace, and source is multi-line Python. We also want the producer to stay dependency-free.

**Decision.** Author each register as `lessons/<topic>/<register>.lesson.toml` (TOML multi-line string for
`source`, comments allowed) — parsed with stdlib `tomllib`, so the tracer needs no third-party deps.
`build.py` traces the source, then merges notes keyed by step index and attaches the
abstraction/problem/provenance, emitting `derived/<topic>/<register>.trace.json`. (`tomllib` is read-only,
which suits an input format; YAML was rejected to avoid a pyyaml build dependency.)

**Consequences.** Editing `source` shifts step indices, so notes must be re-checked on any source change —
mitigated by always re-running `prepare:traces`. For larger lessons we may later key notes by line+intent.

## ADR-0006 — Network processes are modeled as traced Python sims (2026-06-25)

**Context.** The "Systems & Networks" processes (packet routing, DNS resolution, parallelism & speedup)
could be hand-authored as `author-asserted` process traces or modeled as small Python simulations and
traced like any other lesson. This was the one open question carried out of Phase 0.

**Decision (owner, 2026-06-25).** Model them as **traced Python sims**. A packet router, a DNS resolver, a
work scheduler are each tens of lines of Python whose state is the process state (packet positions, the
`name → IP` walk, which tasks are done per tick). They run through the same `sys.settrace` producer, so the
network lessons keep the **execution-derived** guarantee and the routing / DNS / Gantt animations fall out
of the same trace data — one tracer, one schema, one player for the whole portal. Hand-authored
`author-asserted` traces remain the rare fallback for a process that genuinely resists being modeled as code.

**Consequences.** The data/network material is "more traces," not a second codebase. The abstraction
renderers grow (a network graph, a Gantt lane chart); the spine is unchanged.

## ADR-0007 — Code lines are clickable, mapped to steps (2026-06-25)

**Context.** The player stepped via a scrubber, prev/next, and arrow keys. A learner reading the code often
wants to ask "what does *this* line do" directly.

**Decision (owner request, 2026-06-25).** Every executable source line is a button: clicking it jumps to the
step that highlights that line, updating the state/abstraction/note in sync — the same destination the arrow
keys reach, offered as an alternative. Where a line runs more than once (loops, once we have them), clicking
it again walks to its next execution, wrapping around. Blank/comment lines (no corresponding step) are not
clickable. Keyboard stepping and the scrubber are unchanged.

**Consequences.** Generic across all lessons (it reads `trace[].line`); no per-lesson authoring. The loop
behavior is forward-looking — the swap anchors are straight-line, so each line maps to one step today.
