# GlassBox

*Watch code actually run.*

GlassBox turns the black box of program execution into a **glass box you can watch**. Every lesson is a
small Python program; we trace it with `sys.settrace` and ship the trace to a player that lets you step
through it line by line, watching the variables change. The catch that makes it honest: **the state shown
at each line is real CPython output**, produced at build time — never a hand-drawn slide that could quietly
lie about what a variable holds.

It's a from-first-principles tour of how computers actually work — programs & state, data, and systems &
networks — built for the moment a learner's mental model collides with what the machine actually does. A
student who "gets it" in conversation will still write `a = b; b = a` to swap two values. GlassBox makes the
gap between *what you think happens* and *what actually happens* visible and undeniable, with no human in
the loop asserting who's right. CPython delivers the verdict.

## The idea

One screen does two things at once: the **code** with the current line lit, and a **state** pane that
toggles between a generic variable view and a domain metaphor (e.g. two cups you're swapping) — both driven
by the *same* trace data. The toggle is the lesson: those two things you're looking at are the same thing at
two zoom levels. And every lesson ships in multiple **registers** — including the *buggy* one a real student
writes — so you can watch the wrong mental model fail in the state pane, shown by the interpreter, not
asserted by a teacher.

## Stack

Static [Astro](https://astro.build) site with [Svelte](https://svelte.dev) islands, deployed to GitHub
Pages. A build-time Python tracer (`sys.settrace`) is the single producer for the whole portal; its output
is schema-validated JSON that a dumb player steps through. The frontend never runs Python.

```bash
npm install
npm run prepare:traces   # run the tracer + validation gates locally
npm run dev:preview      # preview at http://localhost:4321/
npm run build            # static build -> dist/
```

See [`AGENTS.md`](./AGENTS.md) for the architecture and working agreement, and [`DECISIONS.md`](./DECISIONS.md)
for the decision log.

## Status

**A full beginner course, built.** The tracer handles straight-line code, loops, lists, dicts, multi-frame
functions (calls, returns, recursion), and object identity/aliasing. **Twenty-eight lessons run as one
ordered path of nine modules** — from `values`, types, arithmetic, comparisons & booleans and the if/elif
ladder, through the original spine (swap, partition, accumulate, search, filter, functions), into data
representation (binary, run-length encoding, overflow, roundoff) and traced network/parallelism sims
(routing, fault tolerance, multipacket, speedup). Each ships with a *buggy* register that fails in front of
you, and most with a checkpoint for **Predict** mode. Navigation is a numbered syllabus driven by a single
curriculum manifest, with per-lesson breadcrumb, prerequisite callouts, and prev/next. See
[`AGENTS.md`](./AGENTS.md) for the architecture, the "how to add a lesson" recipe, and the roadmap.

## License

Code under the [MIT License](./LICENSE); educational content under
[CC BY-SA 4.0](./LICENSE-content.md).
