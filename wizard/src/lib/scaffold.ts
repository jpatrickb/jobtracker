// Shells out to the real `jobtracker init` (already a working CLI subcommand) rather than
// reimplementing scaffold() in TS -- that's the one piece that genuinely can't be duplicated
// without keeping the bundled template content (RUBRIC.md, PREFERENCES.md, etc.) in two places.
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { join } from "node:path";

export function isJobtrackerDataDir(target: string): boolean {
  return existsSync(join(target, ".jobtracker"));
}

export interface ScaffoldResult {
  ok: boolean;
  output: string;
}

export function runScaffold(target: string, force: boolean): ScaffoldResult {
  const args = ["init", target];
  if (force) args.push("--force");
  const result = spawnSync("jobtracker", args, { encoding: "utf8" });
  const output = [result.stdout, result.stderr].filter(Boolean).join("\n").trim();
  return { ok: result.status === 0, output };
}
