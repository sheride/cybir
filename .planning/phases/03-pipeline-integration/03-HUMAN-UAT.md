---
status: partial
phase: 03-pipeline-integration
source: [03-VERIFICATION.md]
started: 2026-04-12T00:00:00Z
updated: 2026-04-12T00:00:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. BFS produces identical phase graphs to original code
expected: construct_phases on h11=2 and h11=3 CYTools objects produces identical phase graphs (same number of phases, same contractions, same connectivity) as the original dbrane-tools code
result: [pending]

### 2. Weyl expansion matches original on test cases
expected: expand_weyl on test cases with symmetric flops produces the same hyperextended cone as the original code
result: [pending]

### 3. Example notebooks run end-to-end
expected: Both h11_2_walkthrough.ipynb and h11_3_walkthrough.ipynb execute without errors in the cytools kernel and produce expected outputs
result: [pending]

## Summary

total: 3
passed: 0
issues: 0
pending: 3
skipped: 0
blocked: 0

## Gaps
