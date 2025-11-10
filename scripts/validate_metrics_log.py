#!/usr/bin/env python3
"""Validate metrics JSONL file for format consistency.

Checks:
 1. Each line parseable as JSON.
 2. Required timestamp field present and matches ISO8601 UTC microseconds + 'Z'.
 3. No embedded newlines inside JSON objects (implicit by line iteration).
 4. total_cost_usd numeric and <= reasonable upper bound (e.g., 1.0 USD per event).
Exit code 0 on success, non-zero on failures.
"""
from __future__ import annotations
import sys, re, json, math, pathlib

TS_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$")
MAX_SINGLE_EVENT_COST = 1.0  # adjust if higher cost events expected

DEF_PATH = pathlib.Path("logs/metrics.jsonl")


def validate_line(obj: dict, idx: int, errors: list[str]):
    # timestamp
    ts = obj.get("timestamp")
    if not ts:
        errors.append(f"Line {idx}: missing timestamp")
    else:
        if not TS_PATTERN.match(ts):
            errors.append(f"Line {idx}: bad timestamp format '{ts}'")
    # cost (optional)
    if "total_cost_usd" in obj:
        v = obj["total_cost_usd"]
        try:
            num = float(v)
            if math.isinf(num) or math.isnan(num):
                errors.append(f"Line {idx}: cost NaN/Inf")
            elif num < 0:
                errors.append(f"Line {idx}: negative cost {num}")
            elif num > MAX_SINGLE_EVENT_COST:
                errors.append(f"Line {idx}: suspiciously high cost {num} > {MAX_SINGLE_EVENT_COST}")
        except Exception:
            errors.append(f"Line {idx}: cost not numeric '{v}'")


def main():
    path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else DEF_PATH
    if not path.exists():
        print(f"File not found: {path}", file=sys.stderr)
        return 2
    errors: list[str] = []
    line_count = 0
    with path.open("r", encoding="utf-8") as f:
        for idx, raw in enumerate(f, start=1):
            raw = raw.strip()
            if not raw:
                continue
            line_count += 1
            try:
                obj = json.loads(raw)
            except Exception as e:
                errors.append(f"Line {idx}: JSON parse error: {e}")
                continue
            validate_line(obj, idx, errors)
    if errors:
        print("Validation FAILED:\n" + "\n".join(errors))
        return 1
    print(f"Validation OK: {line_count} lines")
    return 0

if __name__ == "__main__":
    sys.exit(main())
