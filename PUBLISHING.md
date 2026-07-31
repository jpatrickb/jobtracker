# Publishing jobtracker to PyPI

Releases are automated by `.github/workflows/publish.yml`: publishing a GitHub Release builds the
sdist/wheel and uploads them to PyPI via
[Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (OIDC), no stored API token needed.

That workflow only works once the PyPI project has been linked to this repo.
That link is a one-time, manual step that has to happen on the PyPI account that will own the
`jobtracker` project. It can't be done from inside this repo or automated by CI.

## One-time setup (do this before the first release)

Do this on the PyPI account that will own the `jobtracker` project.

1. **Get the `jobtracker` name registered on PyPI**, one of two ways:
   - **Pending publisher (recommended)**: on pypi.org, go to your account's
     "Publishing" settings and register a *pending* trusted publisher for a project named
     `jobtracker` before it exists. This reserves the name and links the workflow in one step, and
     the first `publish.yml` run creates the project automatically. See PyPI's
     [pending publisher docs](https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/).
   - **Manual first upload**: build locally (`python -m build`) and `twine upload dist/*` once with
     an account API token to claim the name, then add a trusted publisher as described below.
2. **Add this repo as a trusted publisher** (skip if you used the pending-publisher flow above,
   since that already links it). On the existing `jobtracker` project on pypi.org: Settings ->
   Publishing -> Add a new publisher, and fill in:
   - Owner: `jpatrickb`
   - Repository name: `jobtracker`
   - Workflow name: `publish.yml`
   - Environment name: `pypi`

   The environment name must match the `environment: pypi` block in `publish.yml`. Also create a
   GitHub Environment named `pypi` in this repo's Settings -> Environments (no protection rules are
   required, but it's a reasonable place to add required reviewers later if desired).

That's the whole manual part. It's a one-time link between this specific GitHub repo/workflow and the
PyPI project, and only the PyPI project owner can set it up.

## Every release after that

1. Bump the version in `pyproject.toml`.
2. Tag the commit (e.g. `git tag v0.2.0 && git push --tags`).
3. Publish a GitHub Release from that tag.

`publish.yml` picks up the `published` event, builds the package, and uploads it to PyPI
automatically. No secrets to manage, no manual `twine upload`.
