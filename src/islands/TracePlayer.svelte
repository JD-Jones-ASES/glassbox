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

  function selectRegister(i) {
    regIdx = i;
    const max = registers[i].trace.length - 1;
    if (step > max) step = max;
  }
  function go(delta) {
    step = Math.max(0, Math.min(stepCount - 1, safeStep + delta));
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
        <pre class="code"><code>{#each sourceLines as ln, i}<span class="line" class:hl={cur && cur.line === i + 1}><span class="ln">{i + 1}</span>{ln || " "}</span>{/each}</code></pre>
      </div>

      <!-- state / abstraction pane -->
      <div class="pane state-pane">
        <div class="pane-head">
          <div class="toggle" role="tablist" aria-label="State view">
            <button role="tab" aria-selected={view === "abstraction"} class:active={view === "abstraction"} onclick={() => (view = "abstraction")}>Abstraction</button>
            <button role="tab" aria-selected={view === "generic"} class:active={view === "generic"} onclick={() => (view = "generic")}>Variables</button>
          </div>
          <span class="same-thing">same data, two zoom levels</span>
        </div>

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
  .line { display: block; padding: 0.08rem 0.8rem 0.08rem 0; white-space: pre; border-left: 3px solid transparent; }
  .line .ln {
    display: inline-block; width: 2.2rem; padding-right: 0.9rem; text-align: right;
    color: var(--ink-faint); user-select: none;
  }
  .line.hl { background: var(--line-hl); border-left-color: var(--line-hl-edge); }

  .toggle { display: inline-flex; border: 1px solid var(--border-strong); border-radius: 999px; overflow: hidden; }
  .toggle button {
    font-family: var(--font-display); font-size: 0.78rem; font-weight: 600;
    padding: 0.22rem 0.7rem; border: 0; background: transparent; color: var(--ink-soft); cursor: pointer;
  }
  .toggle button.active { background: var(--live); color: #fff; }
  .same-thing { font-size: 0.72rem; color: var(--ink-faint); font-style: italic; }

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
</style>
