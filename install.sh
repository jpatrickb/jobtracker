#!/usr/bin/env bash
# Thin convenience installer for jobtracker: curl -fsSL <pages-url>/install.sh | bash
#
# This is NOT a git-clone-based installer -- jobtracker is a single small wheel with no native
# dependencies, so that heavier model doesn't apply here. All this script does is pick whichever
# of uv/pip is already on PATH (preferring uv), install jobtracker with it, and hand off to the
# interactive setup wizard. `pip install jobtracker` / `uv tool install jobtracker` remain the
# real, documented install paths (see README) -- this is just a shortcut on top of them.
#
# NOTE: this always installs tip-of-main via whatever `jobtracker` build is on PyPI at the time
# uv/pip resolve it -- there's no version pinning here. That's fine pre-first-PyPI-publish (there's
# only ever one version to get), but revisit once releases start diverging.
#
# -e: fail fast on any unhandled error. Unlike smoke_test.sh (which deliberately omits -e because
# some of its commands are expected to exit nonzero), every command in this script is expected to
# succeed, and a piped `curl | bash` install script should never quietly limp on into calling
# `jobtracker setup` after e.g. an `uv tool install` failure.
# -u: catch typos in variable names.
# -o pipefail: `curl -LsSf https://astral.sh/uv/install.sh | sh` should fail the whole script if
# curl fails, not just the trailing `sh`.
set -euo pipefail

log() {
  echo "==> $*"
}

# Ensure `uv`'s installer-managed location is on PATH for the rest of *this* script, even though
# the installer already updates shell rc files for future sessions (those don't affect us here).
ensure_uv_on_path() {
  if command -v uv >/dev/null 2>&1; then
    return
  fi
  for candidate in "$HOME/.local/bin" "$HOME/.cargo/bin"; do
    if [ -x "$candidate/uv" ]; then
      export PATH="$candidate:$PATH"
      return
    fi
  done
}

if command -v uv >/dev/null 2>&1; then
  log "Found uv on PATH, installing jobtracker with it..."
  uv tool install jobtracker
elif command -v pip >/dev/null 2>&1 || command -v pip3 >/dev/null 2>&1; then
  pip_bin="$(command -v pip || command -v pip3)"
  log "Found $pip_bin on PATH, installing jobtracker with it..."
  "$pip_bin" install --user jobtracker
else
  log "Neither uv nor pip found on PATH. Installing uv first..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ensure_uv_on_path
  if ! command -v uv >/dev/null 2>&1; then
    echo "uv installation succeeded but 'uv' still isn't on PATH. Open a new shell and re-run" >&2
    echo "this script, or run 'uv tool install jobtracker' yourself." >&2
    exit 1
  fi
  log "Installing jobtracker with uv..."
  uv tool install jobtracker
fi

log "jobtracker installed. Launching setup..."

# `curl url | bash` consumes stdin for the piped script itself, so by the time we get here stdin
# is not the user's terminal -- it's either exhausted or not a tty at all. `jobtracker setup` uses
# rich's Confirm/Prompt, which read interactively from stdin, so calling it naively here would
# either hang on a closed pipe or silently fail. Reconnect it to the real terminal via /dev/tty
# when one exists; otherwise, don't try to be clever -- just tell the user the one command to run.
#
# Deliberately not `[ -r /dev/tty ]`: on a process with no controlling terminal at all (e.g.
# `docker run` without `-t`), opening /dev/tty fails with ENXIO, and bash's `test`/`[` builtin
# surfaces that as a hard runtime error rather than a clean false -- which then trips `set -e`
# and kills the whole script instead of falling through to the instructions below. Probing the
# open in a subshell keeps the failed-redirection error (and any fd changes) scoped to that
# subshell, so only its exit status reaches the `elif`, which `set -e` doesn't treat as fatal.
if [ -t 0 ]; then
  jobtracker setup
elif (exec 3</dev/tty) 2>/dev/null; then
  jobtracker setup </dev/tty
else
  echo
  echo "Run 'jobtracker setup' to finish setting up your job-search data directory."
fi
