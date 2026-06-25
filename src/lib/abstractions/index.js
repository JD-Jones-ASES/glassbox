// Abstraction registry. Keyed by abstraction.type; returns a view-model the player renders, or null
// when there is no renderer for the type (the player then falls back to the generic state view).
import { cupsModel } from "./cups.js";
import { pilesModel } from "./piles.js";
import { binaryModel } from "./binary.js";
import { networkModel } from "./network.js";
import { ganttModel } from "./gantt.js";

const REGISTRY = {
  cups: cupsModel,
  piles: pilesModel,
  binary: binaryModel,
  network: networkModel,
  gantt: ganttModel,
};

export function abstractionModel(abstraction, state) {
  if (!abstraction || !abstraction.type) return null;
  const fn = REGISTRY[abstraction.type];
  return fn ? fn(abstraction, state) : null;
}
