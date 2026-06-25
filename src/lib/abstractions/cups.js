// The "cups" abstraction: map trace state -> a cups view-model via the lesson's abstraction.bind.
// bind maps a variable name to a slot ("left_cup" | "right_cup" | "counter_cup"); each slot shows that
// variable's current value as a liquid. Data-driven and pure: the Svelte player renders the model, this
// module decides what to show. Add a new abstraction = add a sibling module + register it in index.js.

const SLOTS = [
  { slot: "left_cup", label: "Cup a" },
  { slot: "right_cup", label: "Cup b" },
  { slot: "counter_cup", label: "Spare cup" },
];

// Known liquids -> CSS custom property holding the fill colour (defined in styles/portal.css).
const LIQUID_COLOR = {
  milk: "var(--liquid-milk)",
  juice: "var(--liquid-juice)",
};

export function cupsModel(abstraction, state) {
  const bind = abstraction?.bind ?? {};
  const slotToVar = {};
  for (const [varName, slot] of Object.entries(bind)) slotToVar[slot] = varName;

  const cups = [];
  for (const { slot, label } of SLOTS) {
    const varName = slotToVar[slot];
    if (!varName) continue; // this lesson does not use this slot (e.g. no spare cup)
    const present = Object.prototype.hasOwnProperty.call(state, varName);
    const value = present ? state[varName] : null;
    const liquid = typeof value === "string" ? value : null;
    cups.push({
      slot,
      label,
      varName,
      present,
      value,
      liquid,
      color: liquid && LIQUID_COLOR[liquid] ? LIQUID_COLOR[liquid] : "var(--liquid-unknown)",
      isSpare: slot === "counter_cup",
    });
  }
  return { kind: "cups", cups };
}
