# Reasoning Trace Auditor Skill

This skill provides the contextual review layer for the repository's deterministic reasoning-trace scanner.

## Files

- `SKILL.md` — complete skill instructions.
- `evals.md` — ten initial evaluation cases covering true positives, false positives, fixtures, production logs, public-source comments, secrets, and policy tuning.

## Intended use

Use after the scanner reports candidate findings, or invoke directly against a GitHub repository or pull request when a contextual reasoning-trace audit is needed.

Example requests:

- `Run Reasoning Trace Auditor on wchobbs14/Three_Digit_Addition and show only BLOCK and FIX findings.`
- `Audit PR #42 in wchobbs14/Household_Hub for escaped reasoning residue.`
- `Review this reasoning-trace-report.json and tell me which findings should actually block merge.`
- `Run the auditor across my active repos and identify recurrent patterns that suggest an upstream coding-agent or template issue.`

## Decision model

The skill keeps four decisions separate:

1. detector match;
2. contextual classification;
3. risk severity;
4. merge/remediation action.

This prevents a literal phrase match from being treated as proof of private chain-of-thought leakage.

## Recommended pairing

The deterministic scanner remains the CI enforcement layer. The skill should not replace it. Use the skill to review ambiguous findings, tune policy, and investigate systemic patterns across repositories.
