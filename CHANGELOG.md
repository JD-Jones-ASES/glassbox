# Changelog

The project's development history lives here so `AGENTS.md` can stay a timeless entry point. The
architecture *decisions* behind each step are logged in [`DECISIONS.md`](./DECISIONS.md) (ADR-0001…0012).

## v1.0.0 — 2026-06-26

First public release: a from-first-principles CS course taught by tracing **real CPython execution**.

**What's in it**

- **32 lessons across 9 modules** — Foundations (values, types, conversion) · Arithmetic (precedence,
  powers, modulo) · Comparisons & booleans · Decisions (if / elif ladder) · Programs & state · Mutability &
  aliasing · Functions · Data & representation · Systems & networks. Every lesson is execution-derived and
  ships **buggy-first**; most carry a prediction checkpoint.
- **4 milestone projects** that combine several ideas — FizzBuzz, running maximum, palindrome check, and
  collecting rainwater (with a bespoke water visualization).
- **Prediction–evidence–revision learner modes** — *watch*, *predict* (call the next state, adjudicated by
  the real trace), and *find the line*.
- **Manifest-driven course navigation** — a numbered syllabus, per-lesson breadcrumb + prerequisites, and
  prev/next, all from `src/lib/curriculum.js`.
- **An interlinked glossary** (~86 terms across programming / data / networking / complexity) with a
  site-wide hover/focus quick-definition popup; key terms are tagged inline across the lessons.
- **Abstraction renderers** — cups, piles (with an index cursor), binary, network, gantt, water, scan; many
  lessons ride the generic state view.
- **Two-axis provenance** (`derivation_source` + `domain_model`) and serialization hardening (object
  identity via `refs`, typed dict keys, cycle back-edges, deterministic set reprs).

**How it got here (condensed)**

- **Phase 0–1** — the `sys.settrace` tracer as a deterministic build-time producer, the JSON-Schema
  contracts, and the honesty model: provenance + value-coercion flags, object identity, and the two-axis
  `domain_model` split (ADR-0001…0010).
- **Phase 2** — the prediction loop: checkpoints adjudicated against the real next state, never an authored
  answer (ADR-0011).
- **Phase 3** — content to rigorous coverage (iteration, search, representation limits, packet
  switching, parallel speedup).
- **Phase 4 / this release** — granular foundations (values → types → math → logic → decisions),
  manifest-driven progression navigation (ADR-0012), the four milestone projects, register/visualization
  polish, and the interlinked glossary.
