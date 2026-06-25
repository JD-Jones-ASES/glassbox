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

---

### Open question (resolve before Phase 1 "Systems & Networks")

Model network processes (routing, DNS, parallelism) as **traced Python sims** (preferred — preserves the
execution-derived guarantee) or as **hand-authored process traces** (faster to author, `author-asserted`,
weaker guarantee). The schema supports either via `derivation_source`/`step_provenance`. Confirm the
preference with the owner before building Big-picture network lessons.
