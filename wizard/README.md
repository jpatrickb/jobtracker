# jobtracker setup wizard -- prototypes

Three TypeScript rewrites of `jobtracker setup` (today implemented in Python at
`src/jobtracker/wizard.py`, using a `curses`-based menu that renders poorly in constrained
terminals), built with `@clack/prompts` for comparison. **Not published, not wired into the real
install flow yet** -- this is scratch work for picking a direction before that integration happens.

Each prototype is fully real: it creates an actual jobtracker data directory (by shelling out to
the already-installed `jobtracker init` CLI), writes real `PREFERENCES.md`/config content, and can
run the real agent-install phase (importing `jobtracker-agents`'s install functions directly,
in-process). Nothing here is a mockup.

## The three variants

- **`prototype-a.ts` -- direct port.** Same exact sequence/content as today's Python wizard, just
  rebuilt with `@clack/prompts`. Isolates "was it the rendering, or the flow itself" by changing
  only the rendering layer.
- **`prototype-b.ts` -- grouped, fewer prompts, same info.** Hard gates become one multiselect with
  conditional follow-ups instead of a sequential Y/N-then-detail drill; resume import drops the
  redundant "Add another?" confirm.
- **`prototype-c.ts` -- smart single-line parsing.** Compensation floor and location each collapse
  into one free-text prompt with parsing instead of Y/N-then-detail pairs; other hard gates are
  entered as repeated `name: condition` lines; resume import takes comma-separated paths in one go.

## Running one

```bash
npm install
npm run build
node dist/prototype-a.js   # or prototype-b.js / prototype-c.js
```

Requires `jobtracker` (the Python CLI) already installed and on PATH -- `pip install jobtracker` or
`uv tool install jobtracker` first, same as the real `jobtracker setup` would need.
