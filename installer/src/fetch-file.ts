import { mkdir, writeFile } from "node:fs/promises";
import { dirname } from "node:path";
import { DEFAULT_REF, REPO } from "./manifest.js";

export function rawUrl(path: string, ref: string = DEFAULT_REF): string {
  return `https://raw.githubusercontent.com/${REPO}/${ref}/${path}`;
}

// raw.githubusercontent.com returns a 404 page (not a thrown error) for a missing file or a bad
// ref -- without an explicit ok-check that text would get written to disk as if it were real
// content, so every caller goes through this rather than a bare fetch().
export async function fetchRepoFile(path: string, ref: string = DEFAULT_REF): Promise<string> {
  const url = rawUrl(path, ref);
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Failed to fetch ${path} (ref "${ref}"): HTTP ${response.status} from ${url}`);
  }
  return response.text();
}

export async function writeFileEnsuringDir(destPath: string, contents: string): Promise<void> {
  await mkdir(dirname(destPath), { recursive: true });
  await writeFile(destPath, contents, "utf8");
}

// Fetches every `src` path (repo-relative) and writes it under `destDir`, keyed by its own
// basename -- the shape every platform install module needs (a flat list of files, one dir).
export async function fetchAllInto(
  srcPaths: string[],
  destDir: string,
  ref: string = DEFAULT_REF,
): Promise<string[]> {
  const written: string[] = [];
  for (const src of srcPaths) {
    const contents = await fetchRepoFile(src, ref);
    const basename = src.slice(src.lastIndexOf("/") + 1);
    const destPath = `${destDir}/${basename}`;
    await writeFileEnsuringDir(destPath, contents);
    written.push(destPath);
  }
  return written;
}
