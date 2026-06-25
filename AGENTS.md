# AGENTS.md — what this is & how to work it

Entry point for anyone (human or coding agent) opening this repo cold. Start here.

## What this is

**GlassBox** — a static instrument that turns the black box of program execution into a *glass box you can
watch*. Every lesson is a small Python program; we trace it with `sys.settrace` at build time and ship the
trace as schema-validated JSON to a player that steps through it. Stepping through the code **is** the act
that builds the abstraction in front of the learner, one element at a time.

**The core guarantee:** the state shown at each line is **real CPython output**, not a hand-drawn slide. A
hand-authored slide can lie about what a variable holds; a real execution trace cannot. *That guarantee is
the product* — the same "verification is the product" stance as its sibling portals, except here the
adjudicator is the Python interpreter itself.

It is **provider-agnostic**: a from-first-principles tour of how computers actually work (programs & state,
data, systems & networks). It is **not** tied to, and must not name, any specific course, exam, or
standards body — a build gate enforces this (`scripts/validate/scan-text.mjs`).

## Tech stack

- **Astro 7**, `output: "static"` — pages in `src/pages/`, layout/components in `src/components/`.
- **Svelte 5** islands (`src/islands/`, runes), hydrated `client:visible`. The player executes nothing.
- **Vanilla ES modules** (`src/lib/`) — `withBase.js` + data-driven abstraction renderers.
- **CSS custom properties** (`src/styles/portal.css`) — no CSS framework. Self-hosted fonts via `@fontsource`.
- **Python tracer** (`tracer/`, a `uv` package, stdlib-only core) — the build-time producer. Runs locally.
- **Ajv** JSON-Schema validation (`schemas/`, draft 2020-12). The build fails loud.
- No database, no server, no client-side execution. Generated trace data is committed to the repo.

## Build & run

```bash
npm install                # Node >= 22
npm run prepare:traces     # tracer -> derived/*.trace.json, then the schema + scan gates (run locally)
npm run dev:preview        # local dev server served from / (convenient for previewing)
npm run build              # astro build -> dist/

uv --project tracer run pytest   # the tracer's golden-trace test suite (the heart; keep it green)
```

`prepare:traces` regenerates the committed `derived/` traces from `lessons/` + the tracer, then runs the
gates. **CI does NOT run the tracer** — it runs a pure `astro build` over the committed JSON. So: edit a
lesson → `prepare:traces` locally → commit the regenerated `derived/` → push.

## How it works (the factory invariant)

```
lessons/<topic>/*.lesson.yaml  →  sys.settrace tracer (Python)  →  derived/<topic>/*.trace.json
   (authored: source + notes)      (build-time producer)            (schema-valid, COMMITTED)
                                                                          │
                                              Ajv + scan gates ──────────┤  (fail loud)
                                                                          ▼
                                                          Svelte player (steps the JSON; runs nothing)
```

- **The tracer** (`tracer/src/glassbox_tracer/`) is a pure function `(source, inputs) → trace`. On each
  `line` event in the lesson's own frame it snapshots in-scope locals + cumulative stdout. Deterministic,
  inspectable, small. It is the heart of the project; get it bulletproof before authoring lessons.
- **The content layer** (`lessons/*.lesson.toml`) adds human meaning — per-step notes, the abstraction
  spec, the problem statement — kept **separate** from the trace and merged by step index at build time.
- **The player** (`src/islands/TracePlayer.svelte`) is a dumb stepper: code pane (current line lit, and
  every executable line clickable to jump to its step), a right pane toggling generic-state ⇄
  domain-abstraction (both from the same trace), the step note, register tabs, a scrubber + arrow keys,
  and a provenance badge.

## Repo map

```
lessons/<topic>/   AUTHORED lesson TOML (source + notes + abstraction) — the human layer
derived/<topic>/   GENERATED trace JSON (committed; schema-valid) — what the player eats
tracer/            the producer: a uv package; src/glassbox_tracer/{trace,snapshot,build}.py + tests/
schemas/           JSON-Schema contracts (draft 2020-12, additionalProperties:false)
scripts/validate/  validate-traces.mjs (Ajv gate) + scan-text.mjs (provider-agnostic gate)
src/               Astro app: pages/, components/, islands/ (Svelte), lib/ (vanilla ES), styles/
.github/workflows/deploy.yml   push to main -> astro build -> GitHub Pages (Pages disabled until reviewed)
```

## Provenance & honesty (non-negotiable)

1. **The trace is the product.** `derived/` comes only from the tracer; humans write only in `lessons/`.
   The two are merged at build, never co-mingled at authoring time.
2. **Execution-derived vs. author-asserted is explicit.** Every trace declares `derivation_source`; real
   `sys.settrace` output is `execution-derived`, a hand-authored process model is `author-asserted`. The
   gate cross-checks the claim against `provenance.trace_source` and fails on a contradiction.
3. **Author notes are claims, not facts.** A note ("this finds the maximum") is author-asserted by
   definition; the player renders notes and state in visually distinct registers so prose never
   masquerades as execution output.
4. **Schemas are contracts.** A mismatch means one side is wrong — fix it explicitly; never silence the gate.
5. **Static, local-first.** No runtime backend, no client-side Python. The tracer runs locally (supervised);
   CI is a pure `astro build` over committed JSON.
6. **Provider-agnostic.** No course/exam/standards-body names anywhere shipped. `scan-text.mjs` enforces it.

## Deploy

Push to `main` → GitHub Actions runs `astro build` → GitHub Pages. Project base path is `/glassbox` (see
`astro.config.mjs`). Pages is **disabled until Phase 0 is reviewed**; enable it in repo Settings → Pages
(Source: GitHub Actions) when ready.

## Status

**Phase 0** — the `swap` vertical slice (three registers: buggy / procedural / idiomatic) proving the
instrument end to end. The remaining anchors and the data / systems-&-networks topics come next. See
`DECISIONS.md` for the decision log and the open Phase-1 question (network sims: traced vs. hand-authored).
