// The "network" abstraction: a node-link graph with a packet hopping along its path. Slots:
//   topology -> an adjacency dict {node: [neighbors]}; current -> the node the packet is at now;
//   path -> the nodes visited so far; route (optional) -> the planned path (first = source, last =
//   destination); down (optional) -> a list of failed nodes, marked dead with their links unusable;
//   packets (optional) -> a list where index i is packet i's current node (drawn as numbered dots, so
//   several packets can be in flight on different routes at once); arrived (optional) -> the order
//   packets reached the destination. Pure and data-driven: the graph comes from the program's own state.
//   Node positions are auto-laid-out on a circle, so no presentational data needs to live in the trace.

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
  const down = slotToVar.down && Array.isArray(state[slotToVar.down]) ? state[slotToVar.down] : [];
  const downSet = new Set(down);
  const source = route[0] ?? path[0] ?? null;
  const dest = route.length ? route[route.length - 1] : null;

  // Which edges are part of the path walked so far (so the template can just read edge.on); an edge
  // touching a failed node is dead (unusable).
  const pathSet = new Set();
  for (let i = 0; i < path.length - 1; i++) pathSet.add([path[i], path[i + 1]].sort().join(" "));
  const edgeObjs = edges.map(([a, b]) => ({
    a, b,
    on: pathSet.has([a, b].sort().join(" ")),
    dead: downSet.has(a) || downSet.has(b),
  }));

  // Multiple in-flight packets: index = packet id, value = the node it sits on now. Cluster packets
  // that share a node so their numbered dots don't stack exactly on top of each other.
  const packetsRaw = slotToVar.packets && Array.isArray(state[slotToVar.packets]) ? state[slotToVar.packets] : [];
  const arrived = slotToVar.arrived && Array.isArray(state[slotToVar.arrived]) ? state[slotToVar.arrived] : [];
  const nodeUse = {};
  const packets = packetsRaw
    .map((node, i) => {
      if (!pos[node]) return null;
      const k = nodeUse[node] ?? 0;
      nodeUse[node] = k + 1;
      const ang = (k / 3) * 2 * Math.PI - Math.PI / 2;
      return { id: i, node, x: pos[node].x + 6.5 * Math.cos(ang), y: pos[node].y + 6.5 * Math.sin(ang) };
    })
    .filter(Boolean);

  return { kind: "network", nodes, edges: edgeObjs, pos, current, path, source, dest, down, packets, arrived };
}
