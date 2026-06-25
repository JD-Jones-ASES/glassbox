<script>
  // The dumb stepper. It executes nothing — it steps through pre-baked, schema-validated traces.
  // Props: `registers` = an array of trace objects (one per register: buggy / procedural / idiomatic).
  import { abstractionModel } from "../lib/abstractions/index.js";

  let { registers = [] } = $props();

  const DISPLAY = { naive: "Buggy", procedural: "Procedural", idiomatic: "Idiomatic", clever: "Clever" };

  let regIdx = $state(0);
  let step = $state(0);
  let view = $state("abstraction"); // "abstraction" | "generic"

  const current = $derived(registers[regIdx] ?? null);
  const steps = $derived(current ? current.trace : []);
  const stepCount = $derived(steps.length);
  const safeStep = $derived(Math.max(0, Math.min(step, stepCount - 1)));
  const cur = $derived(steps[safeStep] ?? null);
  const sourceLines = $derived(current ? current.source.replace(/\n$/, "").split("\n") : []);
  const model = $derived(current && cur ? abstractionModel(current.abstraction, cur.state) : null);
  const stateEntries = $derived(cur ? Object.entries(cur.state) : []);
  const isFinal = $derived(safeStep === stepCount - 1);
  // Source lines that correspond to at least one step are clickable (blank/comment lines are not).
  const linesWithSteps = $derived(new Set(steps.map((s) => s.line)));
  const hasAbstraction = $derived(!!(current && current.abstraction));
  // Reconstruct the call stack at the current step (so it's correct after a jump/scrub). The current
  // step's own call still counts (we're in the new frame); a return only pops once we've stepped past it.
  const callStack = $derived.by(() => {
    const stack = ["module"];
    for (let i = 0; i <= safeStep && i < steps.length; i++) {
      const s = steps[i];
      if (s.event === "call") stack.push(s.frame);
      else if (s.event === "return" && i < safeStep && stack.length > 1) stack.pop();
    }
    return stack;
  });

  function selectRegister(i) {
    regIdx = i;
    const max = registers[i].trace.length - 1;
    if (step > max) step = max;
  }
  function go(delta) {
    step = Math.max(0, Math.min(stepCount - 1, safeStep + delta));
  }
  // Jump to the step that highlights a clicked line. If that line runs more than once (e.g. a loop),
  // clicking it again while already there walks to its next execution, wrapping around.
  function goToLine(line) {
    const occ = [];
    steps.forEach((s, i) => { if (s.line === line) occ.push(i); });
    if (occ.length === 0) return;
    if (cur && cur.line === line && occ.length > 1) {
      const pos = occ.indexOf(safeStep);
      step = occ[(pos + 1) % occ.length];
    } else if (!cur || cur.line !== line) {
      step = occ[0];
    }
  }
  function onKey(e) {
    if (e.key === "ArrowRight" || e.key === "ArrowDown") { go(1); e.preventDefault(); }
    else if (e.key === "ArrowLeft" || e.key === "ArrowUp") { go(-1); e.preventDefault(); }
    else if (e.key === "Home") { step = 0; e.preventDefault(); }
    else if (e.key === "End") { step = stepCount - 1; e.preventDefault(); }
  }
  function fmtValue(v) {
    if (v && typeof v === "object" && v.__unserializable__) return v.__repr__;
    if (typeof v === "string") return '"' + v + '"';
    return JSON.stringify(v);
  }
  function fmtChip(v) {
    if (v && typeof v === "object" && v.__unserializable__) return v.__repr__;
    return typeof v === "string" ? v : JSON.stringify(v);
  }
</script>

{#if current}
  <!-- svelte-ignore a11y_no_noninteractive_tabindex -->
  <section class="player" tabindex="0" onkeydown={onKey} aria-label="Trace player. Use arrow keys to step.">
    <!-- register tabs -->
    <div class="tabs" role="tablist" aria-label="Solution registers">
      {#each registers as r, i}
        <button
          role="tab"
          aria-selected={i === regIdx}
          class="tab"
          class:active={i === regIdx}
          class:buggy={r.register === "naive"}
          onclick={() => selectRegister(i)}
        >{DISPLAY[r.register] ?? r.register}</button>
      {/each}
    </div>

    <p class="problem">{current.problem}</p>

    {#if callStack.length > 1}
      <div class="callstack" aria-label="Call stack">
        {#each callStack as fr, i}<span class="frame-chip" class:top={i === callStack.length - 1}>{fr === "module" ? "module" : fr + "()"}</span>{#if i < callStack.length - 1}<span class="sep">›</span>{/if}{/each}
      </div>
    {/if}

    <div class="grid">
      <!-- code pane -->
      <div class="pane code-pane">
        <div class="pane-head">
          <span>{current.title}</span>
          <span class="prov badge {current.derivation_source === 'execution-derived' ? 'derived' : 'asserted'}">
            <span class="led"></span>
            {current.derivation_source === "execution-derived"
              ? "execution-derived · CPython"
              : "author-asserted"}
          </span>
        </div>
        <pre class="code"><code>{#each sourceLines as ln, i}{#if linesWithSteps.has(i + 1)}<button type="button" class="line clk" class:hl={cur && cur.line === i + 1} onclick={() => goToLine(i + 1)} title={`Jump to line ${i + 1}`}><span class="ln">{i + 1}</span>{ln || " "}</button>{:else}<span class="line" class:hl={cur && cur.line === i + 1}><span class="ln">{i + 1}</span>{ln || " "}</span>{/if}{/each}</code></pre>
      </div>

      <!-- state / abstraction pane -->
      <div class="pane state-pane">
        <div class="pane-head">
          {#if hasAbstraction}
            <div class="toggle" role="tablist" aria-label="State view">
              <button role="tab" aria-selected={view === "abstraction"} class:active={view === "abstraction"} onclick={() => (view = "abstraction")}>Abstraction</button>
              <button role="tab" aria-selected={view === "generic"} class:active={view === "generic"} onclick={() => (view = "generic")}>Variables</button>
            </div>
            <span class="same-thing">same data, two zoom levels</span>
          {:else}
            <span class="state-label">{cur && cur.frame ? cur.frame + "() locals" : "variables"}</span>
          {/if}
        </div>

        {#if cur && cur.event === "call"}
          <div class="frame-event call">→ entering <code>{cur.frame}()</code></div>
        {:else if cur && cur.event === "return"}
          <div class="frame-event return">← <code>{cur.frame}()</code> returns <span class="retval">{fmtValue(cur.return_value)}</span></div>
        {/if}

        {#if view === "abstraction" && model && model.kind === "cups"}
          <div class="cups">
            {#each model.cups as c}
              <figure class="cup" class:spare={c.isSpare} class:absent={!c.present}>
                <svg viewBox="0 0 80 112" role="img" aria-label={`${c.label}: ${c.present ? (c.liquid ?? fmtValue(c.value)) : "no cup yet"}`}>
                  <path class="glass" d="M15 7 H65 L58 99 Q40 109 22 99 Z" />
                  {#if c.present && c.liquid}
                    <path class="fill" style={`fill:${c.color}`} d="M20.5 52 H59.5 L57 98 Q40 107 23 98 Z" />
                  {/if}
                </svg>
                <figcaption>
                  <span class="cup-label">{c.label}</span>
                  <code class="var">{c.varName}</code>
                  <span class="liquid">{c.present ? (c.liquid ?? fmtValue(c.value)) : "—"}</span>
                </figcaption>
              </figure>
            {/each}
          </div>
        {:else if view === "abstraction" && model && model.kind === "piles"}
          <div class="piles">
            {#if model.source}
              <div class="piles-source">
                <code class="src-label">{model.source.name}</code>
                <div class="chips">
                  {#each model.source.items as it}<span class="chip src">{fmtChip(it)}</span>{/each}
                </div>
              </div>
            {/if}
            {#if model.cursor}
              <div class="piles-cursor"><code>{model.cursor.name}</code> = <span class="chip cur">{fmtChip(model.cursor.value)}</span></div>
            {/if}
            <div class="piles-cols">
              {#each model.piles as p, pi}
                <div class="pile" class:a={pi === 0} class:b={pi === 1}>
                  <div class="pile-head">{p.label}</div>
                  <div class="pile-items">
                    {#if p.items.length === 0}<span class="empty-pile">empty</span>{:else}{#each p.items as it}<span class="chip">{fmtChip(it)}</span>{/each}{/if}
                  </div>
                </div>
              {/each}
            </div>
          </div>
        {:else if view === "abstraction" && model && model.kind === "binary"}
          <div class="binary">
            <div class="bin-remainder">remaining: <span class="chip cur">{fmtChip(model.remainder)}</span></div>
            <div class="bin-columns">
              {#each model.columns as col}
                <div class="bin-col" class:active={col.active} class:on={col.bit === 1}>
                  <div class="bin-place">{col.place}</div>
                  <div class="bin-bit">{col.decided ? col.bit : "·"}</div>
                </div>
              {/each}
            </div>
            <div class="bin-result">= <code>{model.value || "—"}</code><span class="bin-base">binary</span></div>
          </div>
        {:else if view === "abstraction" && model && model.kind === "network"}
          <div class="network">
            <svg viewBox="0 0 100 100" class="net-svg" role="img" aria-label="Network graph">
              {#each model.edges as e}
                <line class="net-edge" class:on={e.on} x1={model.pos[e.a].x} y1={model.pos[e.a].y} x2={model.pos[e.b].x} y2={model.pos[e.b].y} />
              {/each}
              {#each model.nodes as n}
                <g class="net-node" class:current={n === model.current} class:visited={model.path.includes(n)} class:dest={n === model.dest}>
                  <circle cx={model.pos[n].x} cy={model.pos[n].y} r="8.5" />
                  <text x={model.pos[n].x} y={model.pos[n].y} dy="0.34em" text-anchor="middle">{n}</text>
                </g>
              {/each}
            </svg>
            <div class="net-path">path: <code>{model.path.length ? model.path.join(" → ") : "—"}</code></div>
          </div>
        {:else}
          <table class="vars">
            <thead><tr><th>variable</th><th>value</th></tr></thead>
            <tbody>
              {#if stateEntries.length === 0}
                <tr><td colspan="2" class="muted">no variables yet</td></tr>
              {:else}
                {#each stateEntries as [k, v]}
                  <tr><td><code>{k}</code></td><td><code>{fmtValue(v)}</code></td></tr>
                {/each}
              {/if}
            </tbody>
          </table>
        {/if}
      </div>
    </div>

    <!-- note (author-asserted meaning, kept visually distinct from execution output) -->
    {#if cur && cur.note}
      <p class="note"><span class="note-tag">note</span>{cur.note}</p>
    {/if}

    <!-- controls -->
    <div class="controls">
      <button class="nav" onclick={() => go(-1)} disabled={safeStep === 0} aria-label="Previous step">‹</button>
      <input
        class="scrub"
        type="range"
        min="0"
        max={stepCount - 1}
        bind:value={step}
        aria-label="Step"
      />
      <button class="nav" onclick={() => go(1)} disabled={isFinal} aria-label="Next step">›</button>
      <span class="counter">step {safeStep + 1} / {stepCount}</span>
    </div>
    <p class="hint">Click a line, drag the slider, or use the <kbd>←</kbd> <kbd>→</kbd> keys.</p>
  </section>
{/if}

<style>
  .player {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    box-shadow: var(--shadow);
    padding: 0.9rem 1rem 1.1rem;
    outline: none;
  }
  .player:focus-visible { box-shadow: var(--shadow), 0 0 0 3px var(--live-wash); }

  .tabs { display: flex; gap: 0.4rem; flex-wrap: wrap; margin-bottom: 0.8rem; }
  .tab {
    font-family: var(--font-display); font-weight: 600; font-size: 0.85rem;
    padding: 0.32rem 0.8rem; border-radius: 999px;
    border: 1px solid var(--border-strong); background: var(--surface-2); color: var(--ink-soft);
    cursor: pointer;
  }
  .tab:hover { color: var(--ink); }
  .tab.active { background: var(--live); border-color: var(--live); color: #fff; }
  .tab.buggy.active { background: var(--asserted); border-color: var(--asserted); }

  .problem { margin: 0 0 0.9rem; color: var(--ink-soft); font-size: 0.98rem; }

  .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.8rem; }
  @media (max-width: 720px) { .grid { grid-template-columns: 1fr; } }

  .pane {
    border: 1px solid var(--border); border-radius: var(--radius-sm);
    background: var(--surface-2); overflow: hidden; min-height: 16rem;
    display: flex; flex-direction: column;
  }
  .pane-head {
    display: flex; align-items: center; justify-content: space-between; gap: 0.5rem;
    padding: 0.5rem 0.7rem; border-bottom: 1px solid var(--border);
    font-family: var(--font-display); font-size: 0.82rem; color: var(--ink-soft);
  }

  .prov { font-size: 0.68rem; }

  .code { margin: 0; padding: 0.6rem 0; overflow-x: auto; font-family: var(--font-mono); font-size: 0.92rem; }
  .code code { display: block; }
  .line {
    display: block; width: 100%; padding: 0.08rem 0.8rem 0.08rem 0; white-space: pre;
    border-left: 3px solid transparent; text-align: left;
  }
  /* clickable lines are real buttons; strip the chrome so they read as code, keep the affordance */
  button.line {
    font: inherit; color: inherit; background: none; border-top: 0; border-right: 0; border-bottom: 0;
    cursor: pointer;
  }
  button.line:hover { background: var(--surface); }
  button.line:focus-visible { outline: 2px solid var(--live); outline-offset: -2px; }
  .line .ln {
    display: inline-block; width: 2.2rem; padding-right: 0.9rem; text-align: right;
    color: var(--ink-faint); user-select: none;
  }
  .line.hl { background: var(--line-hl); border-left-color: var(--line-hl-edge); }
  button.line.hl:hover { background: var(--line-hl); }

  .toggle { display: inline-flex; border: 1px solid var(--border-strong); border-radius: 999px; overflow: hidden; }
  .toggle button {
    font-family: var(--font-display); font-size: 0.78rem; font-weight: 600;
    padding: 0.22rem 0.7rem; border: 0; background: transparent; color: var(--ink-soft); cursor: pointer;
  }
  .toggle button.active { background: var(--live); color: #fff; }
  .same-thing { font-size: 0.72rem; color: var(--ink-faint); font-style: italic; }
  .state-label { font-family: var(--font-mono); font-size: 0.78rem; color: var(--ink-faint); }

  .callstack { display: flex; align-items: center; gap: 0.35rem; flex-wrap: wrap; margin: -0.2rem 0 0.9rem; font-family: var(--font-mono); font-size: 0.78rem; }
  .frame-chip { padding: 0.1rem 0.5rem; border-radius: 6px; background: var(--surface-2); border: 1px solid var(--border); color: var(--ink-soft); }
  .frame-chip.top { background: var(--live-wash); border-color: var(--live); color: var(--live-ink); font-weight: 600; }
  .callstack .sep { color: var(--ink-faint); }

  .frame-event { margin: 0.55rem 0.7rem 0; padding: 0.4rem 0.6rem; border-radius: var(--radius-sm); font-size: 0.88rem; font-family: var(--font-mono); }
  .frame-event code { font-size: 0.86rem; }
  .frame-event.call { background: var(--live-wash); color: var(--live-ink); }
  .frame-event.return { background: var(--surface-2); color: var(--ink); border: 1px solid var(--live); }
  .frame-event.return .retval { color: var(--live-ink); font-weight: 700; }

  .cups { display: flex; gap: 1rem; justify-content: center; align-items: flex-end; padding: 1.4rem 0.6rem; flex-wrap: wrap; }
  .cup { margin: 0; text-align: center; width: 84px; }
  .cup svg { width: 84px; height: 116px; }
  .glass { fill: var(--surface); stroke: var(--border-strong); stroke-width: 2; }
  .cup.spare .glass { stroke-dasharray: 4 3; }
  .cup.absent { opacity: 0.4; }
  .fill { stroke: rgba(0, 0, 0, 0.12); stroke-width: 1; }
  .cup figcaption { display: flex; flex-direction: column; gap: 0.12rem; margin-top: 0.3rem; }
  .cup-label { font-family: var(--font-display); font-size: 0.8rem; font-weight: 600; }
  .cup .var { font-size: 0.72rem; color: var(--ink-faint); }
  .cup .liquid { font-size: 0.82rem; color: var(--ink); }

  .piles { padding: 0.9rem 0.8rem; display: flex; flex-direction: column; gap: 0.85rem; }
  .piles-source { display: flex; align-items: center; gap: 0.6rem; flex-wrap: wrap; }
  .src-label { font-size: 0.76rem; color: var(--ink-faint); }
  .chips { display: flex; gap: 0.3rem; flex-wrap: wrap; }
  .chip {
    font-family: var(--font-mono); font-size: 0.85rem; padding: 0.1rem 0.5rem; border-radius: 6px;
    background: var(--surface); border: 1px solid var(--border-strong); color: var(--ink);
  }
  .chip.src { color: var(--ink-soft); }
  .chip.cur { background: var(--live); border-color: var(--live); color: #fff; }
  .piles-cursor { font-size: 0.85rem; color: var(--ink-soft); display: flex; align-items: center; gap: 0.4rem; }
  .piles-cols { display: grid; grid-template-columns: 1fr 1fr; gap: 0.7rem; }
  .pile { border: 1px solid var(--border); border-radius: var(--radius-sm); background: var(--surface); overflow: hidden; }
  .pile-head {
    padding: 0.32rem 0.6rem; font-family: var(--font-display); font-size: 0.82rem; font-weight: 600;
    border-bottom: 1px solid var(--border);
  }
  .pile.a .pile-head { background: var(--live-wash); color: var(--live-ink); }
  .pile.b .pile-head { background: var(--asserted-wash); color: var(--asserted); }
  .pile-items {
    padding: 0.5rem 0.6rem; display: flex; gap: 0.3rem; flex-wrap: wrap; min-height: 2.6rem;
    align-content: flex-start;
  }
  .pile.a .pile-items .chip { border-color: var(--live); }
  .pile.b .pile-items .chip { border-color: var(--asserted); }
  .empty-pile { color: var(--ink-faint); font-size: 0.78rem; font-style: italic; }

  .binary { padding: 1.2rem 0.8rem; display: flex; flex-direction: column; gap: 1rem; align-items: center; }
  .bin-remainder { font-family: var(--font-mono); font-size: 0.85rem; color: var(--ink-soft); }
  .bin-columns { display: flex; gap: 0.5rem; }
  .bin-col { width: 3rem; border: 1px solid var(--border-strong); border-radius: var(--radius-sm); overflow: hidden; text-align: center; background: var(--surface); }
  .bin-col.active { border-color: var(--live); box-shadow: 0 0 0 2px var(--live-wash); }
  .bin-place { font-family: var(--font-mono); font-size: 0.76rem; padding: 0.25rem 0; background: var(--surface-2); color: var(--ink-faint); border-bottom: 1px solid var(--border); }
  .bin-bit { font-family: var(--font-mono); font-size: 1.35rem; font-weight: 700; padding: 0.5rem 0; color: var(--ink-faint); }
  .bin-col.on .bin-bit { color: var(--live-ink); background: var(--live-wash); }
  .bin-result { font-family: var(--font-mono); font-size: 1.05rem; display: flex; align-items: center; gap: 0.5rem; }
  .bin-result code { font-size: 1.15rem; letter-spacing: 0.1em; color: var(--ink); }
  .bin-base { font-size: 0.68rem; color: var(--ink-faint); }

  .network { padding: 0.7rem; display: flex; flex-direction: column; gap: 0.5rem; align-items: center; }
  .net-svg { width: 100%; max-width: 15rem; height: auto; aspect-ratio: 1 / 1; }
  .net-edge { stroke: var(--border-strong); stroke-width: 1.2; }
  .net-edge.on { stroke: var(--live); stroke-width: 2.6; }
  .net-node circle { fill: var(--surface); stroke: var(--border-strong); stroke-width: 1.5; }
  .net-node text { font-family: var(--font-mono); font-size: 6px; fill: var(--ink); font-weight: 700; }
  .net-node.visited circle { fill: var(--live-wash); stroke: var(--live); }
  .net-node.current circle { fill: var(--live); stroke: var(--live); }
  .net-node.current text { fill: #fff; }
  .net-node.dest circle { stroke-dasharray: 2.2 1.6; }
  .net-path { font-family: var(--font-mono); font-size: 0.85rem; color: var(--ink-soft); }
  .net-path code { color: var(--live-ink); }

  @media (prefers-reduced-motion: no-preference) {
    .fill { transition: d 0.25s ease, fill 0.25s ease; }
    .line.hl { transition: background 0.15s ease; }
  }

  .vars { width: 100%; border-collapse: collapse; font-family: var(--font-mono); font-size: 0.9rem; }
  .vars th { text-align: left; font-weight: 500; color: var(--ink-faint); font-size: 0.74rem; padding: 0.5rem 0.8rem; }
  .vars td { padding: 0.34rem 0.8rem; border-top: 1px solid var(--border); }
  .vars td:first-child { color: var(--live-ink); }
  .muted { color: var(--ink-faint); font-style: italic; }

  .note {
    margin: 0.85rem 0 0; padding: 0.6rem 0.8rem; background: var(--asserted-wash);
    border-left: 3px solid var(--asserted); border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
    color: var(--ink); font-size: 0.95rem;
  }
  .note-tag {
    font-family: var(--font-mono); font-size: 0.66rem; text-transform: uppercase; letter-spacing: 0.05em;
    color: var(--asserted); margin-right: 0.55rem; vertical-align: 0.06em;
  }

  .controls { display: flex; align-items: center; gap: 0.7rem; margin-top: 1rem; }
  .nav {
    font-size: 1.2rem; line-height: 1; width: 2.1rem; height: 2.1rem; border-radius: 50%;
    border: 1px solid var(--border-strong); background: var(--surface-2); color: var(--ink); cursor: pointer;
  }
  .nav:disabled { opacity: 0.4; cursor: default; }
  .scrub { flex: 1; accent-color: var(--live); }
  .counter { font-family: var(--font-mono); font-size: 0.8rem; color: var(--ink-soft); white-space: nowrap; }
  .hint { margin: 0.55rem 0 0; font-size: 0.78rem; color: var(--ink-faint); text-align: center; }
  .hint kbd {
    font-family: var(--font-mono); font-size: 0.72rem; padding: 0.04rem 0.32rem;
    border: 1px solid var(--border-strong); border-radius: 4px; background: var(--surface-2);
  }
</style>
