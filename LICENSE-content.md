# Content License & Provenance

## Original educational content — CC BY-SA 4.0

All **original educational content** in this repository — lesson prose, step notes, problem statements,
abstraction metaphors, and the explanatory pages — is licensed under the
[Creative Commons Attribution-ShareAlike 4.0 International License](https://creativecommons.org/licenses/by-sa/4.0/).

You may share and adapt this material for any purpose, including commercially, provided you give
appropriate credit and license your derivatives under the same terms.

## Code — MIT

All source code (the Python tracer, build scripts, Astro components, Svelte islands, schemas) is licensed
under the [MIT License](./LICENSE).

## Traced source programs

The small Python programs that each lesson traces are original works written for this portal and ship as
CC BY-SA 4.0 content (the `source` field of each lesson). They contain no third-party code.

## Provenance posture — execution-derived vs. author-asserted

This portal's central guarantee is that the **state shown at each line is real CPython output**, produced
at build time by a `sys.settrace` tracer — never a hand-drawn mock-up. Every trace records whether it is:

- **execution-derived** — the variable state came from running the program under CPython, or
- **author-asserted** — a hand-authored process model (e.g. a network simulation) whose state is a human
  claim, dimension-/shape-checked but not proven by execution.

The distinction is carried in the data (`derivation_source` / `step_provenance`), enforced by the build
gate, and surfaced to the reader on the `/verification/` page and a per-lesson badge. A polished animation
never implies a guarantee the engine did not produce. This is **AI-authored under an owner-designed
verification system**: the verification system — not a human-review gate on every line — is the safeguard,
and the build fails loud when a trace's claims don't hold. See `/verification/` and `DECISIONS.md`.
