// The "scan" abstraction: a list being walked while a running value (e.g. max-so-far) is maintained,
// with the live comparison between the current item and that running value spelled out — so it adds
// something the generic variables table doesn't. Slots:
//   source  -> the list being walked        current -> the current item value
//   best    -> the running value (max so far / running total / …)
// The comparison shown is `current > best` (the running-maximum question); both registers expose it.

export function scanModel(abstraction, state) {
  const bind = abstraction?.bind ?? {};
  const slotToVar = {};
  for (const [v, slot] of Object.entries(bind)) slotToVar[slot] = v;

  const src = state[slotToVar.source];
  const items = Array.isArray(src) ? src : [];
  const has = (slot) => slotToVar[slot] && Object.prototype.hasOwnProperty.call(state, slotToVar[slot]);
  const current = has("current") ? state[slotToVar.current] : undefined;
  const best = has("best") ? state[slotToVar.best] : undefined;

  // Highlight the first item equal to the current value (the loop variable is a value, not an index).
  const activeIndex = has("current") ? items.findIndex((x) => x === current) : -1;

  const cmp =
    has("current") && has("best") && typeof current === "number" && typeof best === "number"
      ? { current, best, beats: current > best }
      : null;

  return {
    kind: "scan",
    items: items.map((v, i) => ({ value: v, active: i === activeIndex })),
    currentName: slotToVar.current,
    bestName: slotToVar.best,
    best: has("best") ? best : null,
    cmp,
  };
}
