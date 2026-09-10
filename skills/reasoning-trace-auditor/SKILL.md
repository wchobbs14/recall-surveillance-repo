# Reasoning Trace Auditor

## Purpose

Audit GitHub repositories, pull requests, scanner reports, or supplied code for text that plausibly represents escaped AI deliberation, hidden reasoning, internal agent instructions, or scratchpad artifacts.

This skill is the interpretive layer above the deterministic Reasoning Trace & Agent Artifact Hygiene scanner. The scanner finds textual signatures; this skill determines what those signatures most likely mean in context and what action is warranted.

Do not treat a regex hit as proof of private chain-of-thought leakage.

## Trigger

Use this skill when the user asks to:

- audit a repository or PR for reasoning-trace leakage;
- review findings produced by `scan_reasoning_traces.py`;
- distinguish real reasoning residue from harmless comments/docstrings;
- assess whether suspicious model-like prose should block merge;
- recommend deletion, rewriting, suppression, or policy changes for reasoning-trace findings;
- compare reasoning-trace hygiene across repositories.

## Operating principle

Separate four questions that are often collapsed:

1. **Did the text match a detector rule?** Deterministic fact.
2. **Does the text look like agent/model deliberation?** Interpretive classification.
3. **Would retaining it create meaningful risk?** Severity assessment.
4. **What should happen next?** Remediation decision.

Never promote uncertainty from one layer into certainty at the next.

## Preferred inputs

Use inputs in this order when available:

1. A JSON report from the deterministic scanner.
2. A GitHub PR and its changed-file patches.
3. A repository/path/line reference.
4. A repository-wide GitHub code search for known reasoning signatures.
5. User-supplied code or text.

When GitHub is connected, prefer repository-native reads over asking the user to paste code.

## GitHub workflow

When auditing GitHub content:

1. Identify the exact repository and ref/PR if given.
2. If a PR is given, inspect changed filenames first, then fetch relevant patches or files.
3. If scanner findings provide path + line, fetch enough surrounding context to understand the containing function, class, prompt, fixture, or document section. Start with roughly 15–25 lines on either side; expand only when needed.
4. If no scanner report exists, search for the highest-confidence signatures first, then inspect context around each hit.
5. Do not search vendored dependencies, lockfiles, generated build output, binaries, or paths explicitly excluded by policy unless the user specifically asks.
6. For each finding, determine whether it is introduced by the change under review or merely pre-existing when that distinction is available.

## Classification taxonomy

Assign exactly one primary classification to every finding.

### A. Likely escaped agent reasoning

Use when the text strongly resembles a model or agent narrating hidden deliberation, planning, user interpretation, tool-use planning, uncertainty management, or pre-answer reasoning.

Typical signals:

- `Let me think...`
- `I need to determine what the user wants...`
- `The user asked...`
- `Before answering, I should...`
- `<analysis>...</analysis>`
- explicit `chain of thought`, `scratchpad`, or `internal reasoning` payloads
- multi-sentence first-person deliberation embedded in model output, prompts, logs, fixtures, telemetry, comments, or generated artifacts

Do not require exact wording if the discourse function is clearly the same.

### B. Suspicious deliberative residue

Use when the prose is model-like or process-narrating but could also plausibly be ordinary developer commentary.

Examples:

- `I should probably normalize this first.`
- `We need to figure out why this is failing.`
- `Maybe I should move this validation earlier.`

This category is especially appropriate for isolated comments without user references, analysis tags, model-output context, or surrounding agent language.

### C. Harmless developer prose

Use when the phrase is ordinary human engineering commentary, documentation, TODO language, commit-like prose, or first-person explanation with no meaningful evidence of escaped model deliberation.

Examples:

- `I think this implementation is easier to maintain.`
- `We should replace this API before v2.`
- `TODO: I should add a regression test for this branch.`

Do not recommend blocking merely because first-person language appears.

### D. Documentation, policy, or test fixture

Use when the suspicious phrase is intentionally present as an example, scanner fixture, security-policy example, documentation excerpt, benchmark input, or regression case.

Normally recommend suppression or path exclusion only when the current scanner would otherwise flag the legitimate example repeatedly.

### E. Insufficient context

Use when the available fragment cannot support a responsible classification. Retrieve more context when possible before using this category.

## Confidence

Assign one of:

- **High** — context strongly supports the classification; little plausible alternative interpretation.
- **Medium** — one interpretation is favored but a realistic alternative remains.
- **Low** — classification is provisional; more context would materially change judgment.

Confidence describes the classification, not the risk.

## Risk severity

Assess risk independently of confidence.

### Critical

Use rarely. Appropriate when reasoning-like material appears to contain secrets, credentials, privileged personal data, security-sensitive implementation detail, or another independently sensitive payload that should not be retained.

### High

Appropriate for strong escaped-reasoning signatures in production source, public artifacts, persisted model responses, logs, telemetry, snapshots, prompt/output archives, or code destined for release.

### Medium

Appropriate for suspicious residue that is unlikely to expose sensitive content but reduces hygiene, reveals agent scaffolding, or creates reputational/operational risk.

### Low

Appropriate for harmless developer prose or intentional test/documentation examples.

## Merge recommendation

Assign one of:

- **BLOCK** — do not merge until remediated.
- **FIX** — should be remediated, but does not by itself require a hard gate unless repository policy says otherwise.
- **ALLOW** — no remediation required.
- **ALLOW WITH SUPPRESSION** — legitimate example; add a narrow documented suppression if needed.

Default mapping:

- Likely escaped agent reasoning + High/Critical risk => BLOCK
- Likely escaped agent reasoning + Medium risk => FIX or BLOCK depending on deployment surface
- Suspicious deliberative residue => FIX
- Harmless developer prose => ALLOW
- Documentation/test fixture => ALLOW WITH SUPPRESSION when necessary

A user may define stricter repository policy; follow it explicitly.

## Surface-risk modifiers

Increase severity when a finding occurs in:

- persisted model outputs;
- production logs or telemetry;
- public API responses;
- UI-visible generated artifacts;
- customer-facing markdown/content;
- prompt/output archives;
- snapshots likely to be published or shipped;
- comments/docstrings in public source repositories where the text clearly exposes agent scaffolding.

Reduce severity when it occurs in:

- scanner regression fixtures;
- intentionally quoted documentation;
- security-policy examples;
- synthetic benchmark cases;
- clearly human TODO comments with no model/user framing.

## Remediation hierarchy

Prefer the smallest action that removes the risk without concealing legitimate engineering context.

1. **Delete** escaped reasoning that adds no user- or developer-facing value.
2. **Replace** process narration with an objective statement of behavior, constraint, or rationale.
3. **Move** legitimate rationale into conventional documentation if it is useful but misplaced.
4. **Suppress narrowly** only for intentional examples or unavoidable false positives.
5. **Adjust detector policy** only after repeated evidence that a rule is systematically imprecise.

Do not recommend broad exclusions as the first response to false positives.

### Rewrite rule

When replacing suspicious reasoning prose, transform internal process narration into externally useful rationale.

Bad:

`# I need to check whether the cache exists before I update it.`

Better:

`# Update only existing cache entries; missing entries are initialized elsewhere.`

Bad:

`"Let me inspect the request and figure out what the user wants."`

Better:

Remove it entirely unless the sentence is intentionally user-visible product copy.

## Scanner-policy feedback

After reviewing a batch, assess the detector itself.

Recommend a policy change only when one of these is true:

- the same benign construction repeatedly appears across independent findings;
- a high-confidence leakage pattern is repeatedly missed;
- an exclusion causes material blind spots;
- a suppression pattern is being overused;
- severity mapping consistently disagrees with contextual review.

When recommending a policy change, state:

- current rule;
- observed failure mode;
- proposed change;
- expected precision/recall effect;
- examples that should match after the change;
- examples that should not match.

## Output format

For a single finding, use concise prose plus the finding record below.

For multiple findings, return a table with these columns:

| Repo | Path:line | Classification | Confidence | Risk | Merge | Why | Remediation |
|---|---|---|---|---|---|---|---|

Then provide three short sections:

### Executive assessment

State:

- number of findings reviewed;
- count by classification;
- count of BLOCK / FIX / ALLOW decisions;
- whether the repository appears to have a systemic reasoning-trace problem or isolated hygiene issues.

### Highest-priority actions

Give only the actions that materially reduce risk, ordered by severity.

### Scanner-policy observations

State `No policy change recommended` unless the evidence supports a concrete detector change.

Do not rewrite entire files unless asked. Provide exact replacement text only for the suspicious fragment or immediate comment/docstring when feasible.

## Finding record schema

Use this conceptual schema when structured output is useful:

```json
{
  "repository": "owner/repo",
  "ref": "branch-or-pr",
  "path": "src/example.py",
  "line": 42,
  "detector_rule": "explicit-deliberation",
  "matched_text": "Let me think about...",
  "classification": "likely_escaped_agent_reasoning",
  "confidence": "high",
  "risk": "high",
  "merge_recommendation": "BLOCK",
  "context_rationale": "Narrates user interpretation and next-step planning inside a persisted model response.",
  "remediation": "Delete the reasoning field before persistence; retain only the user-visible answer."
}
```

## Guardrails

- Never claim that a phrase is actual private chain-of-thought solely because it looks model-generated.
- Never infer authorship (human vs model) without evidence.
- Never expose additional sensitive content merely to explain why a finding is sensitive; quote the minimum fragment necessary.
- Never auto-delete or rewrite repository content unless the user explicitly asks for repository changes.
- Never suppress a high-confidence finding merely to make CI pass.
- Never weaken the scanner globally based on one ambiguous example.
- Distinguish reasoning leakage from prompt injection, secrets leakage, PII exposure, and ordinary insecure logging. If another risk is present, name it separately rather than collapsing everything into reasoning-trace hygiene.

## Portfolio mode

When reviewing several repositories:

1. Normalize findings by detector rule and surface type.
2. Deduplicate repeated vendor/generated examples.
3. Rank repositories by unresolved BLOCK findings, then High-risk FIX findings.
4. Identify recurrent patterns that imply a shared generator, coding agent, prompt, or template may be producing the residue.
5. Recommend fixing the upstream generator/template before mass-editing downstream repos when the evidence supports a common source.

End with a compact portfolio summary:

- repos reviewed;
- repos clean;
- repos with BLOCK findings;
- recurrent rule/pattern;
- likely upstream source if evidenced;
- recommended next control action.

## Success criterion

The skill succeeds when it reduces both false negatives and false positives relative to raw grep while preserving an auditable distinction between detector match, contextual interpretation, risk, and enforcement decision.
