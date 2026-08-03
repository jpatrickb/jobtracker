# Publishing `jobtracker-agents` to npm

Unlike the root package's PyPI flow (`../PUBLISHING.md`), there is no manual release step here at
all once the one-time link below is done. `.github/workflows/publish-installer.yml` runs on every
push to `main` that touches `installer/**`, compares `installer/package.json`'s `version` against
what's currently published, and publishes automatically via npm Trusted Publishing (OIDC) when they
differ. Bumping the version in a normal commit *is* the release step -- merging to `main` is what
ships it.

That workflow only works once the npm package has been linked to this repo. That link is a
one-time, manual step that has to happen on the npm account that will own the `jobtracker-agents`
project. It can't be done from inside this repo or automated by CI.

## One-time setup (do this before the first release)

Do this on the npm account that will own the `jobtracker-agents` project.

1. **Claim the `jobtracker-agents` name on npm.** Trusted Publishing needs an existing project to
   attach to (unlike PyPI, npm has no "pending publisher" flow that reserves a name ahead of the
   first publish) -- so the very first publish has to be a manual `npm publish` from a local
   checkout of `installer/` (`cd installer && npm install && npm run build && npm publish
   --access public`), authenticated with an npm account that has 2FA/automation tokens set up.
2. **Add this repo as a trusted publisher.** On the `jobtracker-agents` project's npm page:
   Settings -> Trusted Publisher -> GitHub Actions, and fill in:
   - Organization or user: `jpatrickb`
   - Repository: `jobtracker`
   - Workflow filename: `publish-installer.yml`
   - Environment name: (leave blank unless you add a GitHub Environment gate later)

   This requires npm CLI >=11.5 support on the publishing side, which `publish-installer.yml`
   already uses (`actions/setup-node`'s bundled npm is current enough by default -- verify with
   `npm --version` in the workflow logs if a publish ever fails with an OIDC-related error).

That's the whole manual part. It's a one-time link between this specific GitHub repo/workflow and
the npm project, and only the npm project owner can set it up.

## Every release after that

1. Bump `version` in `installer/package.json`.
2. Commit and merge to `main` (through whatever PR process the rest of this repo uses).

`publish-installer.yml` picks up the push, builds, compares versions, and publishes automatically.
No `npm publish` to run, no GitHub Release to create, no secrets to manage.
