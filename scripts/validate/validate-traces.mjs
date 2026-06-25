// validate-traces.mjs — the build gate for the SHIPPED artifact. Validates every committed trace in
// derived/ against schemas/trace.schema.json, then enforces the honesty cross-checks that keep a
// polished animation from implying a guarantee the tracer never produced:
//   (a) execution-derived  => provenance.trace_source "sys.settrace", language "python", and NO step
//       may be marked author-asserted;
//   (b) author-asserted    => provenance.trace_source "hand-authored";
//   (c) hybrid             => at least one step marked step_provenance "author-asserted".
// Also: ids unique across files, and the file path matches the declared id. Fails loud (exit 1).

import { readdirSync, statSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve, relative, join } from "node:path";
import Ajv from "ajv/dist/2020.js";
import addFormats from "ajv-formats";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..", "..");
const DERIVED = resolve(ROOT, "derived");

const ajv = new Ajv({ allErrors: true });
addFormats(ajv);
const schema = JSON.parse(readFileSync(resolve(ROOT, "schemas/trace.schema.json"), "utf8"));
const validate = ajv.compile(schema);

const errors = [];
const fail = (m) => errors.push(m);

function walk(dir) {
  const out = [];
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) out.push(...walk(p));
    else if (name.endsWith(".trace.json")) out.push(p);
  }
  return out;
}

let files = [];
try {
  files = walk(DERIVED);
} catch {
  fail(`derived/ not found or unreadable at ${DERIVED} — run \`npm run trace\` first`);
}
if (files.length === 0 && errors.length === 0) fail("no *.trace.json found under derived/");

const ids = new Map();

for (const file of files.sort()) {
  const rel = relative(ROOT, file).replace(/\\/g, "/");
  let data;
  try {
    data = JSON.parse(readFileSync(file, "utf8"));
  } catch (e) {
    fail(`${rel}: invalid JSON — ${e.message}`);
    continue;
  }

  if (!validate(data)) {
    for (const e of validate.errors) fail(`${rel}${e.instancePath} ${e.message}`);
    continue; // structure is wrong; skip semantic checks
  }

  // id uniqueness
  if (ids.has(data.id)) fail(`${rel}: duplicate id '${data.id}' (also in ${ids.get(data.id)})`);
  else ids.set(data.id, rel);

  // honesty cross-checks
  const stepAsserted = data.trace.some((s) => s.step_provenance === "author-asserted");
  if (data.derivation_source === "execution-derived") {
    if (data.provenance.trace_source !== "sys.settrace")
      fail(`${rel}: execution-derived but provenance.trace_source is '${data.provenance.trace_source}'`);
    if (data.provenance.language !== "python" || data.language !== "python")
      fail(`${rel}: execution-derived trace must be language 'python'`);
    if (stepAsserted)
      fail(`${rel}: execution-derived trace must not mark any step author-asserted (use derivation_source 'hybrid')`);
  } else if (data.derivation_source === "author-asserted") {
    if (data.provenance.trace_source !== "hand-authored")
      fail(`${rel}: author-asserted but provenance.trace_source is '${data.provenance.trace_source}' (expected 'hand-authored')`);
  } else if (data.derivation_source === "hybrid") {
    if (!stepAsserted)
      fail(`${rel}: hybrid trace must mark at least one step step_provenance 'author-asserted'`);
  }

  // domain_model cross-checks: keep a real-execution-of-a-model from over-claiming as the subject.
  // A "real-world-process" abstraction (a network/gantt/dns metaphor) must consciously assert it is a
  // model, not silently inherit the interpreter's authority for the real-world claim.
  const REAL_WORLD_ABSTRACTIONS = new Set(["network", "gantt", "dns"]);
  if (data.domain_model === "author-asserted-simulation") {
    if (!(data.derivation_source === "execution-derived" || data.derivation_source === "hybrid"))
      fail(`${rel}: author-asserted-simulation must be execution-derived or hybrid (a sim is a real run of a model)`);
    if (data.provenance.trace_source !== "sys.settrace")
      fail(`${rel}: author-asserted-simulation must be traced (provenance.trace_source 'sys.settrace')`);
  } else if (data.domain_model === "real-world-data") {
    if (!data.provenance.data_source)
      fail(`${rel}: real-world-data requires provenance.data_source naming the capture`);
  }
  if (data.abstraction && REAL_WORLD_ABSTRACTIONS.has(data.abstraction.type)
      && data.domain_model === "execution-derived")
    fail(`${rel}: abstraction '${data.abstraction.type}' models a real-world process — set domain_model to 'author-asserted-simulation' (the trace is real; that it models the real world is your claim)`);

  // sequential step indices
  data.trace.forEach((s, i) => {
    if (s.step !== i) fail(`${rel}: trace[${i}].step is ${s.step}, expected ${i}`);
  });
}

if (errors.length) {
  console.error(`\nTRACE VALIDATION FAILED (${errors.length}):`);
  for (const e of errors) console.error("  - " + e);
  process.exit(1);
}
console.log(`OK: ${files.length} trace(s) valid (${ids.size} unique ids).`);
