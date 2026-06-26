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

## ADR-0008 — Multi-frame tracing: per-frame "state after line" + call/return (2026-06-25)

**Context.** Functions are the spine of everything above the basics, and they were the hardest mechanical
problem: a call pushes a new frame with its own locals, and the existing tracer only modelled one frame.
Getting this right makes functions, conditionals, and the granular function-variant lessons pure layering.

**Decision.** The tracer follows every frame whose code is the lesson's own (filename-scoped), tracking a
call stack. It emits `call` and `return` steps (with the bound arguments and the returned value) plus a
`depth`, and carries `frame`/`depth`/`return_value` in the schema. The "state after the line" rule is made
**per frame**: a line's displayed state is the next snapshot of *its own* frame, so a line is emitted only
when that snapshot arrives — which means a caller line that invokes a function is shown *after* the call has
expanded and returned (`def → call → compute → return → the caller's assignment lands`). The `<module>`
frame's own call/return are suppressed (interpreter bookkeeping), so single-frame lessons (swap, partition)
produce byte-identical traces. Object reprs are stripped of heap addresses (`<function f at 0x..>` →
`<function f>`) to stay deterministic. Recursion, default arguments, and fall-off-the-end `None` all work.

**Consequences.** The player renders a call-stack breadcrumb and call/return callouts. The call stack *is*
the abstraction for function lessons (no bespoke renderer needed). A richer "all frames' locals at once"
view is possible later but deliberately deferred.

## ADR-0009 — Object identity (`refs`) + serialization hardening (2026-06-25)

**Context.** The snapshot serialized every container by value, so two names bound to the *same* list showed
as two equal-but-separate arrays. The `partition/buggy` lesson is *explicitly about aliasing*
(`evens = odds = []`), yet its trace could not show the shared identity — the bug lived only in author
prose, a thesis violation (the whole point is that CPython, not the teacher, delivers the verdict). A 5-agent
audit also confirmed four latent serialization holes: dropped return-value coercion flags, silent dict-key
collision (`{1:'a','1':'b'}` losing an entry), unbounded recursion on cyclic structures, and
PYTHONHASHSEED-dependent set reprs that would churn committed traces.

**Decision.** Intern mutable containers (list, dict) to small, stable integer object ids held for the whole
trace (mirroring the frame-id interner). Emit a per-step `refs` map (variable path → id) **only where
identity carries information** — a container shared by ≥2 names in that snapshot, or a cycle target — so
scalar-only lessons (swap) and per-frame single-name containers (functions) keep `refs` empty and
byte-identical step output. Equal ids in one step mean the *same* object. A self-referential container emits
a `{__ref__: id}` back-edge (path-scoped `seen` set) instead of recursing. A dict with any non-string key
renders as a tagged `{__map__, entries}` list so no entry is lost to a `repr()` key collision. Sets render
as a deterministic, element-sorted repr. Return-value coercion flags are now captured under a
`return_value` path. The tracer stays stdlib-only, pure, deterministic.

**Consequences.** `partition/buggy` now *shows* one list under two names (`evens #2`, `odds #2`); only that
trace's data changes (procedural stays byte-identical). The player gains `#id` badges, a `coerced` tag for
`value_flags`, and back-edge/typed-map rendering. The back-edge primitive is reusable for future
linked-structure/graph lessons.

## ADR-0010 — `domain_model`: a second, orthogonal provenance axis (2026-06-25)

**Context.** ADR-0003's single `derivation_source` conflated two different confidences. The routing sim is a
*real* `sys.settrace` execution (so it earned `execution-derived`), but its hardcoded `A→B→D` path is a
hand-built *model* of real routing — running the model perfectly says nothing about whether the model is
faithful. The lesson's own note ("real routers choose each next hop on the fly… different packets take
different routes") claims behavior the code never exhibits, while wearing the same green
`execution-derived · CPython` badge as a literal swap. The single flag let the metaphor borrow the
interpreter's authority. ADR-0006 ("network sims keep the execution-derived guarantee") papered over exactly
this — true of the *trace*, silently borrowed for the *domain*.

**Decision.** Add an orthogonal top-level `domain_model` enum
(`execution-derived | author-asserted-simulation | real-world-data`). `derivation_source` keeps its job
(*how the state was produced*); `domain_model` answers *the program's relationship to its real-world
subject*. A swap/partition/functions/binary lesson is `execution-derived` on both axes (the program **is**
the subject). A routing/DNS/Gantt sim is `execution-derived` (trace) **and** `author-asserted-simulation`
(model). `build.py` defaults to `execution-derived` with a TOML opt-in; `validate-traces.mjs` **fails loud**
if a `network`/`gantt`/`dns` abstraction tries to ship as `execution-derived` on the domain axis (forcing a
conscious claim). The player shows a second amber `model: author-asserted` chip; `/verification` gains a
two-axis legend; the public "a real trace cannot lie" wording is softened to "every displayed execution
claim is derived from CPython; coercions, omissions, and modeled interpretations are explicitly marked."

**Consequences.** Amends ADR-0003 and ADR-0006. The honesty claim is now defensible for sims: the animation
is real, the world-fidelity is an author's claim, and the two are visibly separate. Future Systems/Networks
lessons inherit `author-asserted-simulation`.

## ADR-0011 — The prediction loop adjudicates against the trace; authors pose the question, never the answer (2026-06-25)

**Context.** Phase 2 makes the pedagogical product the prediction–evidence–revision loop, not just the
trace. A checkpoint asks the learner to predict the next step's state before revealing it. The trap to avoid:
storing an author's "correct answer" and grading against it — that reintroduces exactly the hand-authored
claim the whole project exists to eliminate (a note can lie about what a variable holds; the loop must not).

**Decision.** A `checkpoint: true` step gates *forward* motion only (Prev/Home/scrubber stay free for
review) and asks the learner to predict the **next** step's state. The **sole adjudicator is
`trace[safeStep + 1].state`** — the real execution output already in the shipped JSON. The player diffs the
learner's structured prediction against it and reports only mechanical facts ("you predicted `b = juice`;
CPython produced `b = milk`"); interpretation stays in the visually-distinct author note. Authors may pose
the *question* via a `[[checkpoints]]` table (`step` + optional `ask`), merged in `build.py` like notes, and
a checkpoint may not sit on the last step (nothing to predict). No answer is ever authored or stored. The
prediction input is structured (typed value per visible variable + an "introduce a variable" row) so it is
machine-checkable with no NLP and no backend; the one free-text field (the "fix your model" sentence) is
recorded and shown back but **never graded**. Reserved-but-unused since ADR-0003, the `checkpoint` flag now
has a UI; `checkpoint_prompt` is added to the trace schema.

**Consequences.** Quiz/checkpoint behavior needs no separate system — it is a thin, static layer over the
existing step data, and the "trace is the product" guarantee extends cleanly to "the trace is also the answer
key." The "hide one corner of the triangle" exercise modes (Phase 2.2) follow the same rule: identify-the-line
adjudicates against `steps[k].line`, construct-the-viz against the pure `abstractionModel()` output.

## ADR-0012 — Course progression via a UI-layer curriculum manifest (2026-06-26)

**Context.** The lessons index was a flat grid of "pillar" cards hardcoded in `index.astro`, with no notion
of order, prerequisites, or position — the catalog read as a pile, not a path. As the lesson count grew
(15 → 28), the owner wanted the *natural progression* of topics shown and lesson-to-lesson navigation. The
obvious place to encode order — the lesson TOML — is the wrong one: its schema is `additionalProperties:false`
and feeds the trace pipeline, so curriculum fields there would ripple through `schema → build.py →
trace.schema` and entangle pedagogy ordering with the honesty-critical producer.

**Decision.** Keep all curriculum metadata in a single **UI-layer** module, `src/lib/curriculum.js`
(`modules` → ordered `lessons` with `{ slug, title, blurb, prereqs, kind }`, plus helpers `flatLessons`,
`neighbors`, `prereqsOf`, `firstLesson`, `breadcrumbFor`). Order is array position at both levels. Three
consumers read it: the lessons index renders a **numbered syllabus** (modules as sections, continuous course
numbering, a connector-line path, `kind`-driven provenance pills); the home "Start here" is `firstLesson()`;
and a reusable `src/components/LessonNav.astro` gives every lesson page a breadcrumb (`Module · Step N of M`),
an advisory "Best after" prerequisite callout, and prev/next. The lesson TOML, schemas, `build.py`, and the
TracePlayer are **untouched**. Existing slugs/URLs are unchanged; `partition` is re-homed into a new
Mutability module as a manifest move only (its TOML and committed trace are byte-identical).

**Consequences.** The course is reorderable as data — adding a lesson is a TOML + page + one manifest entry;
the trace "is the product" pipeline stays pure. Prereqs are a soft callout, not a hard gate (no auth/state on
a static site). Completion tracking (localStorage) and a visual prerequisite-DAG map are forward-looking
adds over the same manifest. A future `[slug].astro` dynamic route could collapse the per-page `LessonNav`
insertion to one file, deferred to avoid rewiring each page's trace-JSON imports.
