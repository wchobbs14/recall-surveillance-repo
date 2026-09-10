# Reasoning Trace & Agent Artifact Hygiene

A lightweight repository control for detecting text that plausibly represents escaped AI deliberation, hidden reasoning, internal agent instructions, or scratchpad content.

## Design

This project separates **detection** from **interpretation**:

- GitHub Actions + a deterministic Python scanner enforce a transparent policy.
- High-confidence patterns fail CI.
- Medium-confidence first-person deliberation produces warnings only by default.
- A model or human reviewer can triage ambiguous findings later.

The scanner is dependency-light: Python 3 standard library only.

## What it scans

The policy currently treats these as high-confidence indicators:

- explicit analysis/scratchpad markers;
- references such as `the user wants` / `the user asked`;
- explicit deliberation such as `let me think`, `let me inspect`, and `let's reason through`;
- pre-answer planning language such as `before answering` and `first, I need to`.

Medium-confidence rules include phrases such as `I should`, `I need to`, and `we should probably`.

The scan is intentionally broader than comments/docstrings because reasoning artifacts can also land in prompt templates, fixtures, structured data, generated markdown, logs, and serialized model responses.

## Files

- `scanner/scan_reasoning_traces.py` — scanner and GitHub annotation output.
- `scanner/patterns.json` — detection policy, exclusions, and severity.
- `scanner/test_scan_reasoning_traces.py` — regression tests.
- `.github/workflows/reasoning-trace-scan.yml` — reusable workflow for caller repositories.

## Run locally

```bash
python3 scanner/scan_reasoning_traces.py . --fail-on high
```

This writes `reasoning-trace-report.json` and exits non-zero only when the configured blocking severity is found.

To make medium findings blocking:

```bash
python3 scanner/scan_reasoning_traces.py . --fail-on medium
```

To report without blocking:

```bash
python3 scanner/scan_reasoning_traces.py . --fail-on none
```

## Suppress a legitimate example

A suppression applies only to the immediately following line:

```python
# reasoning-trace-audit: ignore-next-line -- regression fixture RT-014
example = "Let me think about this case."
```

Always include a reason after the token. Prefer narrow suppressions over broad path exclusions.

## Add to another repository

Create `.github/workflows/reasoning-trace-hygiene.yml`:

```yaml
name: Reasoning Trace Hygiene

on:
  pull_request:
  push:
    branches: [main]
  schedule:
    - cron: '0 10 * * 0'
  workflow_dispatch:

permissions:
  contents: read

jobs:
  audit:
    uses: wchobbs14/recall-surveillance-repo/.github/workflows/reasoning-trace-scan.yml@main
    with:
      fail_on: high
      changed_files_only: true
```

Behavior:

- Pull requests: scan only added/copied/modified/renamed files.
- Push/schedule/manual runs: scan the full repository.
- High findings: annotate and fail.
- Medium findings: annotate but pass.
- Every run uploads a JSON report artifact retained for 30 days.

The sample schedule runs Sundays at 10:00 UTC. Adjust the cron if another portfolio-audit time is preferred.

## Tuning policy

Edit `scanner/patterns.json` centrally. Caller repositories automatically consume the current `main` policy on their next run.

Recommended operating model:

1. Keep high-confidence blocking rules narrow.
2. Observe medium-confidence false positives for 2–3 weeks.
3. Promote only patterns with a strong precision record.
4. Use suppressions for legitimate examples and regression fixtures.
5. Periodically review exclusions so generated or persisted AI output does not silently fall outside coverage.

## Security boundary

This is a hygiene control, not proof that a string is private chain-of-thought. It detects textual signatures that plausibly resemble escaped reasoning or agent scratchpad artifacts. Findings should therefore be interpreted as risk signals, with blocking reserved for high-confidence signatures.
