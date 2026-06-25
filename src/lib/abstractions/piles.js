// The "piles" abstraction: a source list being sorted into two (or more) piles, with the current item
// called out. Maps trace state -> a piles view-model via the lesson's abstraction.bind. Slots:
//   source   -> the list being iterated      cursor -> the current item value
//   pile_a, pile_b, pile_c -> the destination piles (rendered in that order)
// Pure and data-driven, like cups.js. The renderer reads list-valued state; the aliasing bug surfaces
// naturally because two piles that are the same object always show identical contents.

const PILE_SLOTS = ["pile_a", "pile_b", "pile_c"];

const cap = (s) => (s ? s.charAt(0).toUpperCase() + s.slice(1) : s);

export function pilesModel(abstraction, state) {
  const bind = abstraction?.bind ?? {};
  const labels = abstraction?.labels ?? {};
  const slotToVar = {};
  for (const [varName, slot] of Object.entries(bind)) slotToVar[slot] = varName;

  const sourceVar = slotToVar.source;
  const source =
    sourceVar && Array.isArray(state[sourceVar])
      ? { name: sourceVar, items: state[sourceVar] }
      : null;

  const cursorVar = slotToVar.cursor;
  const cursor =
    cursorVar && Object.prototype.hasOwnProperty.call(state, cursorVar)
      ? { name: cursorVar, value: state[cursorVar] }
      : null;

  const piles = [];
  for (const slot of PILE_SLOTS) {
    const varName = slotToVar[slot];
    if (!varName) continue;
    const present = Object.prototype.hasOwnProperty.call(state, varName);
    const raw = present ? state[varName] : [];
    const items = Array.isArray(raw) ? raw : [raw];
    piles.push({ name: varName, label: labels[varName] ?? cap(varName), items, present });
  }

  return { kind: "piles", source, cursor, piles };
}
