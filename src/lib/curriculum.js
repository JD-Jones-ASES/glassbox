// The course manifest: the single source of truth for lesson ORDER, grouping, and prerequisites.
//
// Why this lives here and not in lessons/*.lesson.toml: the lesson TOML schema is additionalProperties:false
// and feeds the trace pipeline (schema -> build.py -> trace.schema). Curriculum metadata is a UI concern, so
// it stays at the UI layer. The pages (lessons index, home "Start here", and each lesson's LessonNav) read
// this module; the trace pipeline never sees it.
//
// Order is encoded by array position at BOTH levels: module order = the course arc; lesson order within a
// module = step order. `prereqs` is a separate array of earlier lesson slugs so a callout can name a specific
// dependency without forcing strict linearization. Every `slug` must match src/pages/lessons/<slug>.astro and
// derived/<slug>/. `kind` drives the provenance pill ("author-asserted-simulation" for the traced sims).

export const modules = [
  {
    id: "foundations",
    name: "Foundations: values & types",
    blurb: "Before any algorithm: what a value is, the types a beginner meets, and how a name binds to a value.",
    lessons: [
      {
        slug: "values",
        title: "Values and names",
        blurb: "A name points at one value — rebind it and the old value is gone, unless you saved it first.",
        prereqs: [],
        kind: "execution-derived",
      },
      {
        slug: "datatypes",
        title: "Numbers have types: int vs float",
        blurb: "Two ways to divide: // drops the remainder and gives an int, / keeps it and gives a float.",
        prereqs: ["values"],
        kind: "execution-derived",
      },
      {
        slug: "conversion",
        title: "Converting a float to an int",
        blurb: "int() truncates 3.9 to 3; round() gives 4 — watch which one you reach for.",
        prereqs: ["datatypes"],
        kind: "execution-derived",
      },
    ],
  },
  {
    id: "arithmetic",
    name: "Arithmetic & division",
    blurb: "How numbers combine: precedence, the power operator, and modulo — the remainder that wraps around.",
    lessons: [
      {
        slug: "arithmetic",
        title: "Operator precedence: × before +",
        blurb: "Watch 2 + 3 × 4 come out as 14, not 20 — Python does × before +.",
        prereqs: ["datatypes"],
        kind: "execution-derived",
      },
      {
        slug: "exponent",
        title: "Powers: ** not ^",
        blurb: "Watch 2 ^ 3 silently give 1 — in Python ^ is XOR, and ** is the real power operator.",
        prereqs: ["arithmetic"],
        kind: "execution-derived",
      },
      {
        slug: "modulo",
        title: "Modular arithmetic: wrapping around",
        blurb: "Watch 10 + 5 read as 15 o'clock — and % wrap it back to 3.",
        prereqs: ["arithmetic"],
        kind: "execution-derived",
      },
    ],
  },
  {
    id: "logic",
    name: "Comparisons & booleans",
    blurb: "How a program asks a yes/no question: comparisons produce a bool, operators combine them, and most values are truthy or falsy.",
    lessons: [
      {
        slug: "comparison",
        title: "A comparison is a yes/no value",
        blurb: "Store the result of age > 18 — a real bool — and watch > miss the boundary that >= keeps.",
        prereqs: ["datatypes"],
        kind: "execution-derived",
      },
      {
        slug: "truthiness",
        title: "Truthiness: what counts as true",
        blurb: "A non-empty list is truthy but never equals True — watch == True skip the branch you wanted.",
        prereqs: ["comparison"],
        kind: "execution-derived",
      },
      {
        slug: "booleanops",
        title: "and / or / not",
        blurb: "Watch x == 1 or 2 quietly become 2 (always truthy) — and the fix that compares both values.",
        prereqs: ["truthiness"],
        kind: "execution-derived",
      },
    ],
  },
  {
    id: "decisions",
    name: "Decisions: the if / elif ladder",
    blurb: "Putting conditions to work as control flow — where the order of branches is the whole game.",
    lessons: [
      {
        slug: "ifelse",
        title: "Choosing one branch with if / else",
        blurb: "Watch two separate ifs both run, the second clobbering the first — and elif pick just one.",
        prereqs: ["comparison"],
        kind: "execution-derived",
      },
      {
        slug: "elifladder",
        title: "The elif ladder: order matters",
        blurb: "Watch a 95 graded D because the loosest band was tested first — first true branch wins.",
        prereqs: ["ifelse"],
        kind: "execution-derived",
      },
      {
        slug: "fizzbuzz",
        title: "FizzBuzz",
        blurb: "Milestone: loops + if/elif + modulo — and the unreachable branch that grades 15 wrong.",
        prereqs: ["elifladder", "modulo"],
        kind: "execution-derived",
        milestone: true,
      },
    ],
  },
  {
    id: "programs-state",
    name: "Programs & state",
    blurb: "Tiny imperative programs, traced line by line — including the bugs that destroy or mis-store state.",
    lessons: [
      {
        slug: "swap",
        title: "Swapping two values",
        blurb: "Three ways to swap two cups — including the one a beginner writes, watched failing.",
        prereqs: ["values"],
        kind: "execution-derived",
      },
      {
        slug: "accumulate",
        title: "Adding up a list",
        blurb: "Keep a running total — and watch the = vs += bug stop it from ever adding.",
        prereqs: [],
        kind: "execution-derived",
      },
      {
        slug: "runningmax",
        title: "Running maximum",
        blurb: "Milestone: the accumulator + comparison — and a zero seed that breaks on all-negative data.",
        prereqs: ["accumulate", "comparison"],
        kind: "execution-derived",
        milestone: true,
      },
      {
        slug: "search",
        title: "Linear search",
        blurb: "Find where a value lives — and watch the index-vs-value mix-up return the wrong thing.",
        prereqs: [],
        kind: "execution-derived",
      },
      {
        slug: "filter",
        title: "Filtering a list",
        blurb: "Keep the items that pass a test — and watch deleting-while-looping skip an element.",
        prereqs: ["search"],
        kind: "execution-derived",
      },
      {
        slug: "palindrome",
        title: "Palindrome check",
        blurb: "Milestone: strings + indexing + comparison — and pairing the wrong letters.",
        prereqs: ["comparison", "filter"],
        kind: "execution-derived",
        milestone: true,
      },
      {
        slug: "rainwater",
        title: "Collecting rainwater",
        blurb: "Milestone: arrays, loops and min/max combine to trap water between columns — with a cool visual.",
        prereqs: ["filter", "comparison"],
        kind: "execution-derived",
        milestone: true,
      },
    ],
  },
  {
    id: "mutability",
    name: "Mutability & aliasing",
    blurb: "Some values can be changed in place, and two names can point at one object — so changing 'one' changes 'both'.",
    lessons: [
      {
        slug: "aliasing",
        title: "Aliasing: two names, one list",
        blurb: "Watch backup = scores share one list, so appending to one corrupts the other.",
        prereqs: ["values"],
        kind: "execution-derived",
      },
      {
        slug: "partition",
        title: "Sorting into two piles",
        blurb: "Split numbers into evens and odds — and watch a one-character bug merge the piles.",
        prereqs: ["aliasing"],
        kind: "execution-derived",
      },
    ],
  },
  {
    id: "functions",
    name: "Functions",
    blurb: "Packaging an idea you can call: a function opens its own scope, takes parameters, and must hand a value back.",
    lessons: [
      {
        slug: "functions",
        title: "Functions: package an idea you can call",
        blurb: "The same job four ways — see a function open its own scope and hand a value back.",
        prereqs: [],
        kind: "execution-derived",
      },
      {
        slug: "parameters",
        title: "Parameters: order matters",
        blurb: "Watch swapped positional arguments compute −70 left — and keyword arguments fix it.",
        prereqs: ["functions"],
        kind: "execution-derived",
      },
    ],
  },
  {
    id: "data",
    name: "Data & representation",
    blurb: "How computers store information — every bit of it a program you can trace.",
    lessons: [
      {
        slug: "binary",
        title: "Decimal to binary",
        blurb: "Watch 13 fill the powers-of-two columns to become 1101 — place value, traced as real Python.",
        prereqs: [],
        kind: "execution-derived",
      },
      {
        slug: "bindecimal",
        title: "Binary to decimal",
        blurb: "Turn 1101 back into 13 by doubling — and watch the base mix-up read it as eleven hundred.",
        prereqs: ["binary"],
        kind: "execution-derived",
      },
      {
        slug: "rle",
        title: "Run-length encoding",
        blurb: "Compress a row of pixels into (length, colour) pairs — and watch the bug that drops the last run.",
        prereqs: [],
        kind: "execution-derived",
      },
      {
        slug: "overflow",
        title: "Overflow",
        blurb: "Watch an 8-bit counter wrap 255 → 0 — and watch Python's unbounded ints refuse to.",
        prereqs: ["binary", "modulo"],
        kind: "execution-derived",
      },
      {
        slug: "roundoff",
        title: "Roundoff",
        blurb: "Watch 0.1 + 0.2 come out as 0.30000000000000004 — and why == is a trap on floats.",
        prereqs: ["comparison"],
        kind: "execution-derived",
      },
    ],
  },
  {
    id: "systems",
    name: "Systems & networks",
    blurb: "How machines talk — modelled as small simulations and traced like any other program.",
    lessons: [
      {
        slug: "routing",
        title: "Packet switching",
        blurb: "Follow a packet hopping across a network graph from A to D, one hop at a time.",
        prereqs: [],
        kind: "author-asserted-simulation",
      },
      {
        slug: "faulttolerance",
        title: "Fault tolerance",
        blurb: "Fail a node and watch a redundant network reroute — while a single-path one strands the packet.",
        prereqs: ["routing"],
        kind: "author-asserted-simulation",
      },
      {
        slug: "multipacket",
        title: "Packets take different routes",
        blurb: "One message, three packets, three routes — arriving out of order and reassembled by sequence number.",
        prereqs: ["routing"],
        kind: "author-asserted-simulation",
      },
      {
        slug: "speedup",
        title: "Parallel speedup",
        blurb: "Watch two workers halve the time on independent tasks — and a dependency chain refuse to speed up at all.",
        prereqs: [],
        kind: "author-asserted-simulation",
      },
    ],
  },
];

// ---- helpers (so no page ever hardcodes order again) -------------------------------------------------

// Every lesson in course order, each annotated with its module and a continuous 1-based course index.
export function flatLessons() {
  const flat = [];
  let i = 0;
  for (const m of modules) {
    for (const lesson of m.lessons) {
      i += 1;
      flat.push({ ...lesson, moduleId: m.id, moduleName: m.name, courseIndex: i });
    }
  }
  return flat;
}

export function lessonBySlug(slug) {
  return flatLessons().find((l) => l.slug === slug) ?? null;
}

// { prev, next } in course order; either side is null at the ends.
export function neighbors(slug) {
  const flat = flatLessons();
  const idx = flat.findIndex((l) => l.slug === slug);
  if (idx === -1) return { prev: null, next: null };
  return {
    prev: idx > 0 ? flat[idx - 1] : null,
    next: idx < flat.length - 1 ? flat[idx + 1] : null,
  };
}

// Resolved prerequisite lesson objects (skips any unknown slug), for the "Best after" callout.
export function prereqsOf(slug) {
  const lesson = lessonBySlug(slug);
  if (!lesson || !lesson.prereqs) return [];
  return lesson.prereqs.map((s) => lessonBySlug(s)).filter(Boolean);
}

// The course entry point — powers the home "Start here".
export function firstLesson() {
  return flatLessons()[0] ?? null;
}

// { moduleName, stepNumber, stepCount } — position WITHIN the lesson's module, for the breadcrumb.
export function breadcrumbFor(slug) {
  for (const m of modules) {
    const idx = m.lessons.findIndex((l) => l.slug === slug);
    if (idx !== -1) {
      return { moduleName: m.name, stepNumber: idx + 1, stepCount: m.lessons.length };
    }
  }
  return null;
}
