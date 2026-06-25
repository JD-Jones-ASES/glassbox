// The "gantt" abstraction: a lane chart for scheduling across workers. Slots:
//   lanes -> a list (one per worker) of task blocks, each block [name, start, end];
//   speedup / sequential_time / parallel_time (optional) -> the live speedup payload.
// Blocks are scaled to the longest finish time so the two registers (parallel vs a dependency chain)
// are visually comparable: independent work packs tight, a chain staggers across the whole timeline.

export function ganttModel(abstraction, state) {
  const bind = abstraction?.bind ?? {};
  const slotToVar = {};
  for (const [varName, slot] of Object.entries(bind)) slotToVar[slot] = varName;

  const rawLanes = (slotToVar.lanes && state[slotToVar.lanes]) || [];
  const lanes = (Array.isArray(rawLanes) ? rawLanes : []).map((lane, i) => ({
    worker: i,
    blocks: (Array.isArray(lane) ? lane : [])
      .filter((b) => Array.isArray(b) && b.length >= 3)
      .map((b) => ({ name: b[0], start: b[1], end: b[2] })),
  }));

  let maxTime = 1;
  for (const lane of lanes) for (const b of lane.blocks) if (b.end > maxTime) maxTime = b.end;

  const num = (slot) => (slotToVar[slot] != null && typeof state[slotToVar[slot]] === "number" ? state[slotToVar[slot]] : null);
  return {
    kind: "gantt",
    lanes,
    maxTime,
    speedup: num("speedup"),
    seqTime: num("sequential_time"),
    parTime: num("parallel_time"),
  };
}
