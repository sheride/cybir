---
status: partial
phase: 02-core-mathematics
source: [02-VERIFICATION.md]
started: 2026-04-12T00:00:00Z
updated: 2026-04-12T00:00:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. Snapshot integration test — bit-for-bit equivalence with original code
expected: Run `conda run -n cytools python tests/generate_snapshots.py` (requires original `extended_kahler_cone.py` at cornell-dev path), then `pytest tests/test_integration.py -v`. All integration tests should pass, confirming wall-crossing, GV computation, and classification produce identical results to the original code on real h11=2 polytope data.
result: [pending]

## Summary

total: 1
passed: 0
issues: 0
pending: 1
skipped: 0
blocked: 0

## Gaps
