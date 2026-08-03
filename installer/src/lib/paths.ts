import { homedir } from "node:os";
import { resolve } from "node:path";

export function expandHome(p: string): string {
  if (p === "~") return homedir();
  if (p.startsWith("~/")) return resolve(homedir(), p.slice(2));
  return p;
}

export function resolveTarget(p: string): string {
  return resolve(expandHome(p));
}
