// The "binary" abstraction: place-value columns (powers of two) filling with bits as a number is
// converted. Slots: columns -> the list of place values (e.g. [8,4,2,1]); output -> the bits decided
// so far (same order as columns); remainder -> the shrinking number; current -> the place being
// considered. Pure and data-driven, like the others — the powers come from the program's own state.

export function binaryModel(abstraction, state) {
  const bind = abstraction?.bind ?? {};
  const slotToVar = {};
  for (const [varName, slot] of Object.entries(bind)) slotToVar[slot] = varName;

  const has = (slot) => slotToVar[slot] && Object.prototype.hasOwnProperty.call(state, slotToVar[slot]);
  const arr = (slot) => (Array.isArray(state[slotToVar[slot]]) ? state[slotToVar[slot]] : []);

  const places = arr("columns");
  const bits = arr("output");
  const remainder = has("remainder") ? state[slotToVar.remainder] : null;
  const current = has("current") ? state[slotToVar.current] : null;

  const columns = places.map((place, i) => ({
    place,
    bit: i < bits.length ? bits[i] : null,
    decided: i < bits.length,
    active: place === current,
  }));

  return { kind: "binary", remainder, current, columns, value: bits.join("") };
}
