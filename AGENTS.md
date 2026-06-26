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
src/               Astro app: pages/, components/ (LessonNav), islands/ (Svelte player), lib/ (withBase + curriculum manifest + abstractions), styles/
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

Adding a lesson is the common task; it touches data, never the engine. The house pattern is **two
registers, buggy-first** (`naive` shown as "Buggy", then `procedural`/`idiomatic`) so the learner watches
the bug fail before seeing it fixed — the most valuable register. (Exceptions where the bug only lands
after a baseline — `functions`, `speedup` — keep their own order.)

1. **Author** `lessons/<topic>/<register>.lesson.toml` — `id`, `title`, `register`
   (`naive|procedural|idiomatic|clever`), `problem`, `author`, `created`, a `source` (TOML multi-line
   string of real Python), and `[[notes]]` keyed by step index. Optional:
   - `[abstraction]` (`type` + a `bind` mapping variables → that renderer's slots). Skip it to ride the
     generic variables table — most newer lessons do.
   - `domain_model = "author-asserted-simulation"` — **required** when the program is a toy model of a
     real-world process (a network/dns/gantt sim); the build gate fails without it for those abstractions.
   - `[[checkpoints]]` (`step` + optional `ask`) — surfaces a custom prediction question at that step
     **when the learner is in Predict mode**. Author one where a scalar state-delta is predictable and
     the wrong guess is instructive; network/structural lessons (the insight is visual) can skip it.
     A checkpoint may not sit on the last step (nothing to predict). It never stores an answer — the real
     next state adjudicates (ADR-0011).
2. **Generate, reading the steps off the trace.** Run the tracer over your source first to read the real
   step indices before writing notes/checkpoints — the trace is the ground truth, never guess indices.
   `npm run trace` writes `derived/<topic>/<register>.trace.json`; `npm run prepare:traces` then runs the
   schema + scan gates. (`uv --project tracer run python -c "from glassbox_tracer.trace import trace; ..."`
   is the quick way to dump step/line/state.)
3. **Page + manifest.** Add `src/pages/lessons/<topic>.astro` (import the trace JSON, mount
   `<TracePlayer registers={[...]} client:visible />`, write a short worked explanation, and drop a
   `<LessonNav slug="<topic>" position="top"/>` just inside `<Base>` and `position="bottom"` just before
   `</Base>`). Then add the lesson to the right module in `src/lib/curriculum.js` —
   `{ slug, title, blurb, prereqs: [...], kind }`. **The catalog is the manifest**: the lessons index
   (numbered syllabus), the home "Start here" (`firstLesson()`), and every page's breadcrumb + prerequisite
   callout + prev/next all render from `curriculum.js`, in array order — there is no hand-maintained
   `pillars` list anymore (ADR-0012). Curriculum metadata lives *only* here, never in the lesson TOML (whose
   schema is `additionalProperties:false` and feeds the trace pipeline). **Astro whitespace gotcha:** a space
   next to an inline element (`<code>`, `<a>`, `<strong>`) is dropped if a newline falls between them — keep
   the element and its adjacent word on the SAME line (this bit the `speedup` page:
   `<strong>Speedup</strong>\nmeasures` rendered as "Speedupmeasures").
4. **New abstraction?** Only if the generic state view / call-stack chrome isn't enough. Add
   `src/lib/abstractions/<type>.js` (a pure `(abstraction, state) → viewModel`), register it in
   `src/lib/abstractions/index.js`, and add one `{:else if … model.kind === "<type>"}` branch + scoped
   styles in `src/islands/TracePlayer.svelte`. Existing renderers: `cups`, `piles` (source / cursor /
   `cursor_index` / pile_a–c), `binary`, `network` (topology/current/path/route/down/packets/arrived),
   `gantt` (lane chart), `water` (bar+water histogram), `scan` (a walk with a running value + live
   comparison); functions use the built-in call-stack chrome — no renderer. Many lessons ride the generic
   variables table.
5. **Milestone?** A milestone is an ordinary lesson with `milestone: true` in its manifest entry; the
   syllabus badges it. Use it for an integrative problem that combines several earlier ideas (FizzBuzz,
   collecting rainwater).

**Glossary.** Terms live in `src/lib/glossary.js` (`{ slug, term, category, short, body, related, lessons }`
+ helpers). To define a term, add an entry; to use it in prose, wrap the word with
`<Term s="<slug>">word</Term>` (manual, so code blocks never get false popups). The site-wide hover/focus
popup (a script in `src/layouts/Base.astro`) and the `/glossary/` page read the module; `relatedLessons`
links back via `curriculum.js`. Keep the inline `<Term>` on the same line as its neighbours (the whitespace
gotcha).

The engine (`tracer/`) should rarely change. If it must, keep the `swap` and `partition-procedural` traces
byte-identical (`partition-buggy` carries aliasing `refs` by design; ADR-0009) and add a golden test in
`tracer/tests/`; `uv --project tracer run pytest` must stay green.

## Current state (v1.0.0)

GlassBox is a finished v1.0.0 course; the engine, player, schemas, and gates are stable. Expect to add
**content** (`lessons/`, `derived/`, `src/pages/lessons/`, a `curriculum.js` entry, glossary terms), not
change the engine. The development history is in [`CHANGELOG.md`](./CHANGELOG.md); the architecture decision
log is [`DECISIONS.md`](./DECISIONS.md).

**The course** — 32 lessons in one ordered path of nine modules, browsable at `/lessons/` as a numbered
syllabus and navigable lesson-to-lesson (manifest-driven; ADR-0012). Every lesson is execution-derived and
buggy-first; most carry a prediction checkpoint. Four are integrative **milestone** projects (★).

- **0 · Foundations** — values, datatypes (`//` vs `/`), conversion (`int()` vs `round()`).
- **1 · Arithmetic** — arithmetic (precedence), exponent (`^` is XOR), modulo (clock wrap).
- **2 · Comparisons & booleans** — comparison (a stored bool), truthiness, booleanops (`x == 1 or 2` → `2`).
- **3 · Decisions** — ifelse (two ifs both run), elifladder (first true branch wins), fizzbuzz ★.
- **4 · Programs & state** — swap (cups), accumulate (=vs+=), runningmax ★, search, filter, palindrome ★,
  rainwater ★ (water viz).
- **5 · Mutability & aliasing** — aliasing (`b = a` shares one list), partition (piles).
- **6 · Functions** — functions (call stack; forgot-`return`), parameters (positional order).
- **7 · Data & representation** — binary, bindecimal, rle, overflow, roundoff.
- **8 · Systems & networks** — routing, faulttolerance, multipacket, speedup (all
  `domain_model = author-asserted-simulation`).

**Learner modes** — watch; predict (call the next state, the real trace adjudicates — ADR-0011);
find-the-line.

**Renderers** — cups, piles, binary, network, gantt, water, scan; the call-stack chrome for functions; the
generic variables table for everything else.

**Glossary** — ~86 cross-linked terms at `/glossary/`, with a site-wide hover/focus definition popup.

**Deploy** — push to `main` → `.github/workflows/deploy.yml` builds and publishes to GitHub Pages
(base path `/glassbox`).

**Deferred by design (not gaps):** the construct-the-viz exercise mode; an internet-vs-web composite and a
standalone DNS lesson (would reuse `network.js`); weak-guarantee "reveals" (metadata, lossy/lossless,
bandwidth) that sit outside the execution-derived core; and a transfer-measurement rubric over the
predict / find-the-line modes.
