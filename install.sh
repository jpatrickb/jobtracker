#!/usr/bin/env bash
# Thin convenience installer for jobtracker: curl -fsSL <pages-url>/install.sh | bash
#
# This is NOT a git-clone-based installer -- jobtracker is a single small wheel with no native
# dependencies, so that heavier model doesn't apply here. This script always prefers uv (installing
# it first if it isn't already on PATH) and only falls back to a bare system pip if uv genuinely
# isn't available -- most current Linux distros (Debian/Ubuntu 23.04+, etc.) ship a PEP 668
# "externally-managed-environment" Python that refuses a plain `pip install` outright, and uv's
# isolated tool installs sidestep that entirely. `pip install jobtracker` / `uv tool install
# jobtracker` remain the real, documented install paths (see README) -- this is just a shortcut.
#
# NOTE: this always installs tip-of-main via whatever `jobtracker` build is on PyPI at the time
# uv/pip resolve it -- there's no version pinning here. Both uv and pip treat an already-installed
# package as satisfied and do nothing by default, even when a newer version exists on PyPI, so
# re-running this script would otherwise silently keep whatever was installed the first time --
# `--reinstall`/`--upgrade` below force resolving against the current PyPI version every time.
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

pip_fallback() {
  # Last resort, only reached when uv genuinely isn't available. A plain `pip install` errors
  # outright on a PEP 668 "externally-managed-environment" Python (the default on current
  # Debian/Ubuntu) -- retry with the override pip's own error message recommends once that
  # specific error is confirmed, rather than reaching for it unconditionally on every platform.
  pip_bin="$(command -v pip || command -v pip3)"
  log "uv isn't available; falling back to $pip_bin..."
  if pip_output=$("$pip_bin" install --user --upgrade jobtracker 2>&1); then
    echo "$pip_output"
    return 0
  fi
  echo "$pip_output"
  if echo "$pip_output" | grep -q "externally-managed-environment"; then
    log "System pip is externally managed (PEP 668) -- retrying with --break-system-packages..."
    "$pip_bin" install --user --upgrade --break-system-packages jobtracker
  else
    return 1
  fi
}

if command -v uv >/dev/null 2>&1; then
  log "Found uv on PATH, installing jobtracker with it..."
  uv tool install --reinstall jobtracker
else
  log "uv not found on PATH, installing it first..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ensure_uv_on_path
  if command -v uv >/dev/null 2>&1; then
    log "Installing jobtracker with uv..."
    uv tool install --reinstall jobtracker
  elif command -v pip >/dev/null 2>&1 || command -v pip3 >/dev/null 2>&1; then
    pip_fallback
  else
    echo "Couldn't install uv, and no pip/pip3 found either. Install Python (with pip), or uv," >&2
    echo "and re-run this script." >&2
    exit 1
  fi
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
