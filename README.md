# GlassBox

*Watch code actually run.* — v1.0.0

GlassBox turns the black box of program execution into a **glass box you can watch**. Every lesson is a
small Python program; we trace it line by line and let you step through it, watching the variables change.
The catch that makes it honest: **the state shown at each line is real CPython output**, captured at build
time — never a hand-drawn slide that could quietly lie about what a variable holds.

## What it is

A from-first-principles tour of how computers actually work — **32 lessons across nine modules**, from values
and types through arithmetic, booleans, conditionals, loops, functions, mutability, data representation, and
how networks move data. It is built for the moment a learner's mental model collides with what the machine
actually does: a student who "gets it" in conversation will still write `a = b; b = a` to swap two values.
GlassBox makes the gap between *what you think happens* and *what actually happens* visible and undeniable —
with no human in the loop asserting who's right. CPython delivers the verdict.

- **Buggy-first.** Most lessons open with the wrong version a real beginner writes, watched *failing* in the
  state pane, before the fix. The failing version is the most valuable one.
- **Predict, don't just watch.** A *predict* mode asks you to call the next state before it's revealed; the
  real trace is the only judge. There's also a *find-the-line* mode.
- **Milestone projects.** Four lessons (FizzBuzz, running maximum, palindrome, collecting rainwater) combine
  several ideas — rainwater even fills a little skyline with water as it computes.
- **An interlinked glossary.** ~86 terms, from `variable` and `loop` to `truthiness`, `DNS`, and
  *exponential vs polynomial time* — hover any underlined term anywhere on the site for a quick definition.

## How it works

```
lessons/<topic>/*.lesson.toml   →   sys.settrace tracer (Python)   →   derived/*.trace.json   →   Svelte player
   (authored: source + notes)        (build-time producer)             (committed, schema-valid)   (steps it; runs nothing)
```

A build-time Python tracer is the single producer for the whole site; its output is schema-validated JSON
that a "dumb" player steps through. The frontend never runs Python. The player shows the code with the
current line lit and a state pane that toggles between a generic variable view and a domain metaphor (two
cups you're swapping, water filling a histogram) — both driven by the *same* trace. That toggle is the
lesson: the two things you're looking at are the same thing at two zoom levels.

```bash
npm install              # Node >= 22
npm run prepare:traces   # run the tracer + validation gates locally
npm run dev:preview      # preview at http://localhost:4321/
npm run build            # static build -> dist/
```

## How it was made

GlassBox is **AI-authored under an owner-designed verification system**. The interesting part isn't that an
AI wrote the lessons — it's the harness that keeps them honest:

1. **A deterministic producer is ground truth.** The tracer is a pure `(source, inputs) → trace` function;
   it can't drift from reality because it *is* reality (real CPython execution). Author prose is merged in
   only as clearly-marked *claims*, never mixed into the execution record.
2. **Schemas are contracts that fail loud.** Every trace is validated against a JSON Schema; mismatches break
   the build rather than shipping a quiet lie.
3. **Honesty is modeled, not assumed.** Two orthogonal axes — *was this state produced by CPython?* and
   *does the program faithfully model its real-world subject?* — are tracked per lesson and shown to the
   reader as badges. A routing animation is a real trace of a hand-built model, and says so.
4. **Every decision is logged.** [`DECISIONS.md`](./DECISIONS.md) is the architecture decision record;
   [`CHANGELOG.md`](./CHANGELOG.md) is the development history; [`AGENTS.md`](./AGENTS.md) is the cold-start
   guide for the next contributor (human or agent).

The human's job was to design that verification system and hold the line on it — not to hand-write each fact.

## Is the process abstractable?

Yes — and that's the point. The transferable pattern is:

> **Pair generation with a deterministic checker whose output can't drift, mark what's *derived* vs
> *asserted*, and make the verification itself the product.**

Wherever you can *execute or simulate* a subject and snapshot its state, you can build a glass box for it:
other programming topics, spreadsheets, state machines, simple physics or economics models, network
protocols. More broadly, the discipline applies to **any AI-generated artifact where trust matters**: don't
ask the reader to trust the generator — give them a build-time gate that fails loud, a clear line between
what was computed and what was claimed, and a way to check the claim against ground truth. If the
verification is convincing, the content is too.

## License

Code under the [MIT License](./LICENSE); educational content under
[CC BY-SA 4.0](./LICENSE-content.md). AI-authored under an owner-designed verification system.
