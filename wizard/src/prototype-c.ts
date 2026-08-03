#!/usr/bin/env node
// Prototype C -- smart single-line parsing, narrative feel. Rethinks the interaction model itself
// (not just grouping) to minimize total keystrokes: compensation floor and location each collapse
// a Y/N-then-detail pair into one free-text prompt with parsing; "other" hard gates are entered as
// repeated "name: condition" lines until a blank line; resume import accepts multiple
// comma-separated paths in one prompt instead of a loop.
import * as p from "@clack/prompts";
import { homedir } from "node:os";
import { join } from "node:path";
import { runAgentInstallStep } from "./lib/agent-step.js";
import { writeDefaultDataRoot } from "./lib/config.js";
import type { HardGate } from "./lib/hard-gates.js";
import { writeHardGates } from "./lib/hard-gates.js";
import { resolveTarget } from "./lib/paths.js";
import { readRubricDimensions } from "./lib/rubric.js";
import { importResumeFile, resolveImportSource } from "./lib/resume-import.js";
import { isJobtrackerDataDir, runScaffold } from "./lib/scaffold.js";

const DEFAULT_DATA_DIR = join(homedir(), "JobTracker");
const COMP_PATTERN = /^([\d,]+)\s*(\/\s*(hr|yr|hour|year))?$/i;

async function stepDataDirectory(): Promise<string> {
  const targetStr = await p.text({
    message: "Job-search data directory?",
    initialValue: DEFAULT_DATA_DIR,
  });
  if (p.isCancel(targetStr)) process.exit(1);
  const target = resolveTarget(targetStr);

  if (isJobtrackerDataDir(target)) {
    const reinit = await p.confirm({
      message: `${target} already exists -- reset it to fresh templates? (your applications database is untouched either way)`,
      initialValue: false,
    });
    if (!p.isCancel(reinit) && reinit) {
      const result = runScaffold(target, true);
      if (result.output) p.log.message(result.output);
      p.log.success(`Reinitialized ${target}.`);
    } else {
      p.log.info(`Using ${target} as-is.`);
    }
  } else {
    const result = runScaffold(target, false);
    if (result.output) p.log.message(result.output);
    p.log.success(`Created ${target}.`);
  }

  return target;
}

function parseCompFloor(raw: string): HardGate | null {
  const trimmed = raw.trim();
  if (!trimmed) return null;
  const match = trimmed.match(COMP_PATTERN);
  if (!match) return null;
  const amount = Number(match[1].replace(/,/g, ""));
  if (!Number.isFinite(amount)) return null;
  const unit = (match[3] ?? "yr").toLowerCase();
  const isHourly = unit.startsWith("h");
  const formatted = amount.toLocaleString("en-US");
  const condition = isHourly
    ? `hourly rate disclosed AND < $${formatted}/hr`
    : `base salary disclosed AND < $${formatted}`;
  return { name: "Compensation floor", condition, rejectMessage: "Below comp floor" };
}

async function stepHardGates(target: string): Promise<void> {
  p.log.step("Hard gates -- postings that fail any of these get auto-rejected before scoring.");
  const gates: HardGate[] = [];

  const compRaw = await p.text({
    message: "Compensation floor? e.g. 150000/yr or 75/hr -- blank to skip",
    initialValue: "",
    validate: (v) =>
      (v ?? "").trim() === "" || COMP_PATTERN.test((v ?? "").trim())
        ? undefined
        : "e.g. 150000/yr or 75/hr",
  });
  if (!p.isCancel(compRaw)) {
    const gate = parseCompFloor(compRaw);
    if (gate) gates.push(gate);
  }

  const locationRaw = await p.text({
    message: "Location/remote requirement? (e.g. 'fully remote, or hybrid near Austin, TX') -- blank to skip",
    initialValue: "",
  });
  if (!p.isCancel(locationRaw) && locationRaw.trim()) {
    gates.push({ name: "Location", condition: locationRaw.trim(), rejectMessage: "Location doesn't work" });
  }

  p.log.info('Any other hard requirements? One per line as "name: condition", blank line to finish.');
  // eslint-disable-next-line no-constant-condition
  while (true) {
    const line = await p.text({ message: "name: condition (blank to finish)", initialValue: "" });
    if (p.isCancel(line) || !line.trim()) break;
    const idx = line.indexOf(":");
    if (idx === -1) {
      p.log.warn('Expected "name: condition" -- skipped that line.');
      continue;
    }
    const name = line.slice(0, idx).trim();
    const condition = line.slice(idx + 1).trim();
    if (!name || !condition) {
      p.log.warn('Expected "name: condition" -- skipped that line.');
      continue;
    }
    gates.push({ name, condition, rejectMessage: `Fails: ${name}` });
  }

  const wrote = await writeHardGates(target, gates);
  if (gates.length > 0 && wrote) {
    p.log.success(`Wrote ${gates.length} hard gate(s) to PREFERENCES.md.`);
  } else {
    p.log.info("No hard gates set -- illustrative placeholders left in PREFERENCES.md.");
  }
}

async function stepRubricWeights(target: string): Promise<boolean> {
  const dims = await readRubricDimensions(target);
  const summary =
    dims.length > 0
      ? dims.map((d) => `${d.name} -- ${d.weight}%`).join("\n")
      : "(couldn't find dimension headings in RUBRIC.md to summarize)";
  p.note(summary, "Rubric weights");

  const keep = await p.confirm({ message: "Keep these defaults for now?", initialValue: true });
  return !p.isCancel(keep) && keep;
}

async function stepResumeImport(target: string): Promise<string[]> {
  const imported: string[] = [];
  const raw = await p.text({
    message: "Resume/LinkedIn export/work-history docs to import? Comma-separated paths, blank to skip",
    initialValue: "",
  });
  if (p.isCancel(raw) || !raw.trim()) return imported;

  const paths = raw
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);

  for (const pathStr of paths) {
    const src = resolveImportSource(pathStr);
    if (!src) {
      p.log.warn(`No file found at ${pathStr} -- skipped.`);
      continue;
    }
    const dest = await importResumeFile(target, src);
    imported.push(dest);
    p.log.success(`Imported -> ${dest}`);
  }

  return imported;
}

async function main() {
  p.intro("jobtracker setup (prototype C -- smart parsing)");

  const target = await stepDataDirectory();
  const configPath = await writeDefaultDataRoot(target);
  p.log.success(`Remembered ${target} as your default data directory (${configPath}).`);

  await stepHardGates(target);
  const keptDefaultRubric = await stepRubricWeights(target);
  const imported = await stepResumeImport(target);
  await runAgentInstallStep(target);

  p.note(
    [
      `Data directory: ${target}`,
      `Hard gates: see PREFERENCES.md`,
      imported.length > 0 ? `Imported ${imported.length} file(s): ${imported.join(", ")}` : "Resume import: skipped",
      keptDefaultRubric ? "Rubric weights: kept at the scaffolded defaults." : "Rubric weights: customize in RUBRIC.md",
    ].join("\n"),
    "Summary",
  );

  p.outro(
    "Next step: open your coding agent in this directory and run the `resume-onboarding` skill " +
      "to build your evidence ledger" +
      (imported.length > 0 ? ", using what you imported just now." : "."),
  );
}

main().catch((err) => {
  p.log.error(err instanceof Error ? err.message : String(err));
  process.exitCode = 1;
});
