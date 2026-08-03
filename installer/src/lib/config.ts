// Port of config.py's write_default_data_root() -- a single-line TOML file, simple enough to
// reimplement directly rather than round-trip through Python for something this small.
import { mkdir, writeFile } from "node:fs/promises";
import { homedir } from "node:os";
import { dirname, resolve } from "node:path";

export function configPath(): string {
  const xdg = process.env.XDG_CONFIG_HOME;
  const base = xdg ? resolve(xdg) : resolve(homedir(), ".config");
  return resolve(base, "jobtracker", "config.toml");
}

export async function writeDefaultDataRoot(target: string): Promise<string> {
  const path = configPath();
  await mkdir(dirname(path), { recursive: true });
  await writeFile(path, `data_root = "${resolve(target)}"\n`, "utf8");
  return path;
}
