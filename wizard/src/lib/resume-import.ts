import { existsSync, statSync } from "node:fs";
import { copyFile, mkdir } from "node:fs/promises";
import { basename, join } from "node:path";
import { expandHome } from "./paths.js";

export function resolveImportSource(pathStr: string): string | null {
  const src = expandHome(pathStr);
  if (!existsSync(src) || !statSync(src).isFile()) return null;
  return src;
}

export async function importResumeFile(target: string, srcPath: string): Promise<string> {
  const importsDir = join(target, "resume", "imports");
  await mkdir(importsDir, { recursive: true });
  const dest = join(importsDir, basename(srcPath));
  await copyFile(srcPath, dest);
  return join("resume", "imports", basename(srcPath));
}
