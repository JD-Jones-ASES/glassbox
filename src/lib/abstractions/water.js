// The "water" abstraction: a histogram of bar heights with trapped water filled in above each bar.
// For the collecting-rainwater milestone. Pure and data-driven like the other renderers. Slots:
//   heights        -> the bar heights (the terrain)        water -> trapped water per column (same length)
//   current_index  -> the column being processed now       total -> running total of trapped water
// Both registers build a `water` list, so the buggy global-max version visibly overfills the edges.

export function waterModel(abstraction, state) {
  const bind = abstraction?.bind ?? {};
  const slotToVar = {};
  for (const [v, slot] of Object.entries(bind)) slotToVar[slot] = v;

  const heights = Array.isArray(state[slotToVar.heights]) ? state[slotToVar.heights] : [];
  const waterRaw = Array.isArray(state[slotToVar.water]) ? state[slotToVar.water] : [];
  const active = typeof state[slotToVar.current_index] === "number" ? state[slotToVar.current_index] : null;
  const total = typeof state[slotToVar.total] === "number" ? state[slotToVar.total] : null;

  const columns = heights.map((h, i) => {
    const w = typeof waterRaw[i] === "number" && waterRaw[i] > 0 ? waterRaw[i] : 0;
    return { height: typeof h === "number" ? h : 0, water: w, active: i === active };
  });
  const maxH = Math.max(1, ...columns.map((c) => c.height + c.water));
  return { kind: "water", columns, total, maxH };
}
