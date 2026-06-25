# AGENTS.md — what this is & how to work it

Entry point for anyone (human or coding agent) opening this repo cold. Start here.

## What this is

**GlassBox** — a static instrument that turns the black box of program execution into a *glass box you can
watch*. Every lesson is a small Python program; we trace it with `sys.settrace` at build time and ship the
trace as schema-validated JSON to a player that steps through it. Stepping through the code **is** the act
that builds the abstraction in front of the learner, one element at a time.

**The core guarantee:** the state shown at each line is **real CPython output**, not a hand-drawn slide.
Every displayed execution claim is derived from CPython; coercions, omissions, and modeled interpretations
are marked explicitly rather than hidden. *That honesty is the product* — the same "verification is the
product" stance as its sibling portals, except here the adjudicator is the Python interpreter itself.

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
lessons/<topic>/*.lesson.toml  →  sys.settrace tracer (Python)  →  derived/<topic>/*.trace.json
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
2. **Two honest axes, kept separate (ADR-0009/0010).** `derivation_source` answers *did CPython produce
   this state?* (`execution-derived` vs `author-asserted`). `domain_model` answers *does the program
   faithfully model its real-world subject?* — `execution-derived` (a swap IS a swap) vs
   `author-asserted-simulation` (a routing sim is a real run of a hand-built model) vs `real-world-data`.
   A trace can be execution-derived AND an author-asserted simulation at once; the gate fails if a
   network/gantt/dns abstraction tries to pass as `execution-derived` on the domain axis. Object identity
   is explicit too: equal `refs` ids in a step mean the *same* object (aliasing), not just equal values.
3. **Author notes are claims, not facts.** A note ("this finds the maximum") is author-asserted by
   definition; the player renders notes and state in visually distinct registers so prose never
   masquerades as execution output.
4. **Schemas are contracts.** A mismatch means one side is wrong — fix it explicitly; never silence the gate.
5. **Static, local-first.** No runtime backend, no client-side Python. The tracer runs locally (supervised);
   CI is a pure `astro build` over committed JSON.
6. **Provider-agnostic.** No course/exam/standards-body names anywhere shipped. `scan-text.mjs` enforces it.

## Deploy

Push to `main` → GitHub Actions runs `astro build` → GitHub Pages. Project base path is `/glassbox` (see
`astro.config.mjs`). The repo is private and Pages is **not yet enabled**; turn it on in repo Settings →
Pages (Source: GitHub Actions) when the owner is ready to go public.

## Extending GlassBox (how to add the next lesson)

Adding a lesson is the common task; it touches data, never the engine:

1. **Author** `lessons/<topic>/<register>.lesson.toml` — `id`, `title`, `register`
   (`naive|procedural|idiomatic|clever`), `problem`, `author`, `created`, a `source` (TOML multi-line
   string of real Python), an optional `[abstraction]` (`type` + a `bind` mapping variables to that
   abstraction's slots), and `[[notes]]` keyed by step index.
2. **Generate, reading the steps off the trace.** Run the tracer over your source first to read the real
   step indices before writing notes — the trace is the ground truth, never guess indices. `npm run trace`
   writes `derived/<topic>/<register>.trace.json`; `npm run prepare:traces` then runs the schema + scan gates.
3. **Page + catalog.** Add `src/pages/lessons/<topic>.astro` (import the trace JSON, mount
   `<TracePlayer registers={[...]} client:visible />`, write a short worked explanation) and a line in the
   `pillars` list in `src/pages/lessons/index.astro`. (Watch Astro's whitespace: keep an inline `<code>`/
   `<a>` on the same line as the word before it, or the space is dropped.)
4. **New abstraction?** Only if the generic state view / call-stack chrome isn't enough. Add
   `src/lib/abstractions/<type>.js` (a pure `(abstraction, state) → viewModel`), register it in
   `src/lib/abstractions/index.js`, and add one `{:else if … model.kind === "<type>"}` branch + scoped
   styles in `src/islands/TracePlayer.svelte`. Existing renderers: `cups`, `piles`, `binary`, `network`
   (functions use the built-in call-stack chrome — no renderer).

The engine (`tracer/`) should rarely change. If it must, keep the `swap` and `partition-procedural` traces
byte-identical (`partition-buggy` carries aliasing `refs` by design; ADR-0009) and add a golden test in
`tracer/tests/`; `uv --project tracer run pytest` must stay green.

## Status & roadmap

**The spine is built, and the trust foundation is hardened (Phase 1, ADR-0009/0010).** The tracer handles
straight-line code, loops, lists, and **multi-frame functions** (call/return, depth, return values,
recursion, defaults; ADR-0008), now with **object identity** (`refs` make aliasing visible — the
`partition-buggy` repair), a **two-axis provenance** model (`derivation_source` + `domain_model`; routing is
a real trace of an author-asserted model), and serialization hardening (typed dict keys, cycle back-edges,
deterministic set reprs, captured return-value flags). Five lessons (11 registers) across three pillars,
browsable from `/lessons/`:

- **Programs & State** — `swap` (cups), `partition` (piles; loops + aliasing bug, now shown via `refs`),
  `functions` (call stack; four registers incl. the forgot-`return` bug).
- **Data** — `binary` (place-value columns).
- **Systems & Networks** — `routing` (node-link graph; a traced packet sim, ADR-0006).

**Next, in rough priority** (the roadmap is now sequenced: engine/honesty → interaction → content):
- *Phase 2 — the prediction–evidence–revision loop (the pedagogical product):* the `checkpoint` primitive
  (gate a step, predict the next state, reveal the delta, correct the model — adjudicated only by the real
  next state), then the "hide one corner of the triangle" exercise modes. Build before net-new lessons.
- *Phase 3 — content to rigorous, exam-relevant coverage (P0+P1, all execution-derived, each with a buggy
  register):* fault tolerance (kill a node mid-trace, reuse `network.js`), multi-packet + reassembly +
  internet-vs-web, run-length encoding (the compression bridge), accumulate / running total; then overflow
  vs. roundoff, linear search, build/filter, binary→decimal, sequential-vs-parallel speedup (new Gantt
  renderer). Granular pedagogical lessons and weak-guarantee "reveals" are deferred.
- *Deferred features:* Pages go-live; a transfer-measurement rubric riding the exercise modes.
