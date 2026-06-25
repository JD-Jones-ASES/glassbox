// The "network" abstraction: a node-link graph with a packet hopping along its path. Slots:
//   topology -> an adjacency dict {node: [neighbors]}; current -> the node the packet is at now;
//   path -> the nodes visited so far; route (optional) -> the planned path (first = source, last =
//   destination). Pure and data-driven: the graph comes from the program's own state. Node positions
//   are auto-laid-out on a circle, so no presentational data needs to live in the trace.

export function networkModel(abstraction, state) {
  const bind = abstraction?.bind ?? {};
  const slotToVar = {};
  for (const [varName, slot] of Object.entries(bind)) slotToVar[slot] = varName;

  const adj = (slotToVar.topology && state[slotToVar.topology]) || {};
  const nodes = Object.keys(adj);

  // Undirected edges, de-duplicated.
  const seen = new Set();
  const edges = [];
  for (const a of nodes) {
    for (const b of adj[a] || []) {
      const key = [a, b].sort().join(" ");
      if (!seen.has(key)) {
        seen.add(key);
        edges.push([a, b]);
      }
    }
  }

  // Circular layout in a 100x100 viewBox.
  const pos = {};
  const n = nodes.length || 1;
  nodes.forEach((node, i) => {
    const ang = (i / n) * 2 * Math.PI - Math.PI / 2;
    pos[node] = { x: 50 + 34 * Math.cos(ang), y: 50 + 34 * Math.sin(ang) };
  });

  const current = slotToVar.current ? state[slotToVar.current] : null;
  const path = slotToVar.path && Array.isArray(state[slotToVar.path]) ? state[slotToVar.path] : [];
  const route = slotToVar.route && Array.isArray(state[slotToVar.route]) ? state[slotToVar.route] : [];
  const source = route[0] ?? path[0] ?? null;
  const dest = route.length ? route[route.length - 1] : null;

  // Which edges are part of the path walked so far (so the template can just read edge.on).
  const pathSet = new Set();
  for (let i = 0; i < path.length - 1; i++) pathSet.add([path[i], path[i + 1]].sort().join(" "));
  const edgeObjs = edges.map(([a, b]) => ({ a, b, on: pathSet.has([a, b].sort().join(" ")) }));

  return { kind: "network", nodes, edges: edgeObjs, pos, current, path, source, dest };
}
