#!/usr/bin/env bash
# Before/after behavioral snapshot for the jobtracker CLI, since there's no real test suite for
# it. Usage: smoke_test.sh <label>   (e.g. "before", "after-store", "after")
# Then:  diff /tmp/track-smoke-before.txt /tmp/track-smoke-after.txt
#
# Runs the installed `jobtracker` command (override with JOBTRACKER_BIN=... if it's not on PATH) against a
# throwaway temp data root, scaffolded fresh each run with `jobtracker init` and pinned via
# JOBTRACKER_DATA_ROOT so this script's own cwd never matters. Unlike the original tracker/
# smoke_test.sh, there's no applications.json.bak fixture to copy in (this package ships no real
# user data), so a small synthetic dataset is seeded via `jobtracker add` instead. JOBTRACKER_DATA_FILE
# still works exactly the same way (see store.py), but isn't needed here now that `init` exists to
# scaffold a whole root in one step.
set -uo pipefail   # not -e: some commands (stale, ambiguous show) exit nonzero on purpose

label="${1:?usage: smoke_test.sh <label>}"
out="/tmp/track-smoke-$label.txt"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

track_bin="${JOBTRACKER_BIN:-jobtracker}"

: > "$out"

run() {
  echo "=== \$ $* ===" >> "$out"
  "$track_bin" "$@" >> "$out" 2>> "$out"
  echo "--- exit: $? ---" >> "$out"
}

# Scaffold a fresh data root, then pin every subsequent invocation to it.
"$track_bin" init "$work" > /dev/null
export JOBTRACKER_DATA_ROOT="$work"

# --- seed fixture data ---------------------------------------------------------------------
run add --company "FBI" --role "Special Agent (STEM Engineering Background)" --score 82 \
  --band "Good fit" --scorer-version v1 --source LinkedIn \
  --facts '{"work_format": "Onsite", "location": "Multiple US cities", "employment_type": "Full-time", "years_experience_min": 3, "pay_annual_min": 62000, "pay_annual_max": 95000, "cover_letter_requested": "No"}' \
  --notes "seed fixture"
run add --company "Acme Corp" --role "Senior Python Engineer" --score 91 \
  --band "Strong fit" --scorer-version v1 --source "Company careers page" \
  --facts '{"work_format": "Remote", "location": "US", "employment_type": "Full-time", "years_experience_min": 5, "pay_annual_min": 150000, "pay_annual_max": 190000, "cover_letter_requested": "No"}' \
  --notes "seed fixture"
run add --company "Acme Corp" --role "Staff Engineer" --score 74 \
  --band "Good fit" --scorer-version v1 --source "Company careers page" \
  --facts '{"work_format": "Hybrid", "location": "NYC", "employment_type": "Full-time", "years_experience_min": 8, "pay_annual_min": 180000, "pay_annual_max": 220000, "cover_letter_requested": "Yes"}' \
  --notes "seed fixture"

mkdir -p "$work/inbox"
cat > "$work/inbox/globex-devops.md" <<'EOF'
---
url: https://example.com/jobs?currentJobId=555111
---
Globex Devops Engineer
Remote, full-time.
EOF
cat > "$work/inbox/globex-devops-dupe.md" <<'EOF'
---
url: https://example.com/jobs?currentJobId=555111
---
Globex Devops Engineer
Remote, full-time.
EOF

# --- read-only commands ---------------------------------------------------------------------
run list
run list --fields id,company,score,status,facts.work_format
run list --fact work_format=Remote
run search python
run show fbi-special-agent-stem-engineering-background   # exact id
run show fbi-special                                      # unambiguous fragment -> silent resolve
run show acme                                              # deliberately ambiguous -> candidate list, exit 1
run report
run stale
run doctor
run inbox
run inbox-dupes

# --- mutating round trip ---------------------------------------------------------------------
# --date pinned everywhere it's accepted so output never depends on what day this runs. add has no
# --date flag, but its confirmation message doesn't print a date.
run add --company "Smoketest Co" --role "Smoke Tester" --score 50 --band "Test" --scorer-version v0
run update-status smoketest-co-smoke-tester Applied --date 2026-07-15 --note smoke
run set-facts smoketest-co-smoke-tester --facts '{"work_format": "Remote"}'
run rescore smoketest-co-smoke-tester --score 60 --band "Test2" --scorer-version v0 --force --date 2026-07-16
run remove smoketest-co-smoke-tester --force
run list     # should be byte-identical to the very first `list` above
run doctor   # should be byte-identical to the very first `doctor` above

echo "Snapshot: $out"
