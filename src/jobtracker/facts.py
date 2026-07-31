"""Facts validation, parsing, and filtering for the job tracker (see cli.py)."""
import json
import sys
from pathlib import Path

NUMERIC_FACT_KEYS = {
    "pay_annual_min", "pay_annual_max", "pay_hourly_min", "pay_hourly_max",
    "years_experience_min", "years_experience_max",
}
CATEGORICAL_FACTS = {
    "work_format": {"Remote", "Hybrid", "Onsite"},
    "employment_type": {"Full-time", "Part-time", "Internship", "Temporary"},
    "pay_structure": {"W2", "1099 Contract", "C2C", "Unpaid", "Stipend"},
    "cover_letter_requested": {"Yes", "No"},
}
# Facts every scored listing ought to carry, so the absence of a value is never ambiguous.
# The convention that makes this work: an explicit null means "checked, the posting doesn't disclose
# it", while a missing key means "never captured". Those are different things, and conflating them is
# the kind of gap that can silently hide across many records if it isn't kept explicit.
# Warn-only by design: a sparse posting must never block a score from being logged.
REQUIRED_FACT_KEYS = [
    "work_format", "location", "employment_type",
    "years_experience_min", "pay_annual_min", "pay_annual_max",
    "cover_letter_requested",
]
FACT_FILTER_OPS = ["!=", ">=", "<=", ">", "<", "="]  # longest first so ">=" doesn't split on "="


def validate_facts(facts):
    """Enforce type/vocabulary only on the keys we've committed to a convention for. Everything
    else in facts is unvalidated free-form data, by design."""
    errors = []
    for key in NUMERIC_FACT_KEYS:
        if key in facts and facts[key] is not None and not isinstance(facts[key], (int, float)):
            errors.append(
                f"'{key}' must be a plain number, got {facts[key]!r} "
                f"({type(facts[key]).__name__}); strip \"$\"/commas, e.g. 90000 not \"$90,000\""
            )
    for key, allowed in CATEGORICAL_FACTS.items():
        if key in facts and facts[key] is not None and facts[key] not in allowed:
            errors.append(
                f"'{key}' must be exactly one of {sorted(allowed)}, got {facts[key]!r}; "
                f"put any nuance in a '{key}_note' field instead"
            )
    if errors:
        print("Invalid facts:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(1)


def warn_missing_required_facts(facts):
    """Nudge (never block) when a scored posting is missing a fact we've committed to capturing."""
    missing = [k for k in REQUIRED_FACT_KEYS if k not in (facts or {})]
    if missing:
        print(
            f"Warning: required fact(s) not captured: {', '.join(missing)}. Set a value, or null "
            "to record that the posting doesn't disclose it.",
            file=sys.stderr,
        )


def load_facts_arg(facts_str, facts_file):
    """Parse --facts/--facts-file into a validated dict, or None if neither was given."""
    if facts_file:
        raw = Path(facts_file).read_text()
    elif facts_str:
        raw = facts_str
    else:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in --facts/--facts-file: {e}", file=sys.stderr)
        sys.exit(1)
    if not isinstance(data, dict):
        print("--facts/--facts-file must be a JSON object, e.g. {\"work_format\": \"Remote\"}", file=sys.stderr)
        sys.exit(1)
    validate_facts(data)
    return data


def parse_fact_filter(spec):
    for op in FACT_FILTER_OPS:
        idx = spec.find(op)
        if idx > 0:
            return spec[:idx], op, spec[idx + len(op):]
    print(f"--fact must be KEY<op>VALUE (op one of {', '.join(FACT_FILTER_OPS)}), got '{spec}'", file=sys.stderr)
    sys.exit(1)


def fact_matches(record_value, op, raw_value):
    if record_value is None:
        return False
    try:
        rv, fv = float(record_value), float(raw_value)
        return {"=": rv == fv, "!=": rv != fv, ">": rv > fv, "<": rv < fv, ">=": rv >= fv, "<=": rv <= fv}[op]
    except (TypeError, ValueError):
        pass
    if op == "=":
        return str(record_value) == raw_value
    if op == "!=":
        return str(record_value) != raw_value
    print(f"Operator '{op}' needs a numeric fact; '{record_value}' isn't one (only = and != work on text)", file=sys.stderr)
    sys.exit(1)


def all_fact_keys(records):
    keys = set()
    for r in records:
        keys.update((r.get("facts") or {}).keys())
    return keys
