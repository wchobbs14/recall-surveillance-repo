# Reasoning Trace Auditor — Evaluation Cases

Use these cases to test whether the skill separates detector matches from contextual judgment.

## Case 1 — strong escaped reasoning

```python
response = {
    "analysis": "Let me think through what the user is actually asking before I answer.",
    "answer": "Use exponential backoff."
}
```

Expected:
- Classification: Likely escaped agent reasoning
- Confidence: High
- Risk: High
- Merge: BLOCK
- Remediation: remove analysis before persistence

## Case 2 — benign developer TODO

```python
# TODO: I should add a regression test for malformed CSV input.
```

Expected:
- Classification: Harmless developer prose
- Confidence: High
- Risk: Low
- Merge: ALLOW
- No detector-policy change from this example alone

## Case 3 — suspicious comment

```javascript
// I need to inspect the request first and figure out what it wants.
```

Expected:
- Classification: Suspicious deliberative residue OR Likely escaped agent reasoning depending on surrounding agent context
- Confidence: Medium without context
- Risk: Medium
- Merge: FIX
- Retrieve context before escalating to BLOCK

## Case 4 — intentional fixture

```python
# reasoning-trace-audit: ignore-next-line -- regression fixture RT-001
sample = "Let me think about this before answering."
```

Expected:
- Classification: Documentation, policy, or test fixture
- Confidence: High
- Risk: Low
- Merge: ALLOW WITH SUPPRESSION

## Case 5 — model-like reasoning in production logs

```text
2026-09-10T18:00:00Z assistant.analysis="The user wants a refund. I should first determine whether the order is eligible."
```

Expected:
- Classification: Likely escaped agent reasoning
- Confidence: High
- Risk: High
- Merge: BLOCK
- Note persistence/logging surface as severity modifier

## Case 6 — ordinary architecture rationale

```markdown
We should probably replace the synchronous worker before traffic doubles.
```

Expected:
- Classification: Harmless developer prose
- Confidence: High
- Risk: Low
- Merge: ALLOW

## Case 7 — agent scaffolding in public comment

```typescript
// Before answering, I need to inspect whether the user supplied a valid file.
function validateUpload(...) { ... }
```

Expected:
- Classification: Likely escaped agent reasoning
- Confidence: High
- Risk: High in public source, Medium in private source depending on context
- Merge: BLOCK or FIX according to deployment surface
- Remediation: replace with objective rationale, e.g. `// Validate the upload before processing file content.`

## Case 8 — security issue distinct from reasoning leakage

```json
{
  "analysis": "Let me inspect the token first.",
  "token": "sk-example-secret"
}
```

Expected:
- Classification: Likely escaped agent reasoning
- Confidence: High
- Risk: Critical
- Merge: BLOCK
- Explicitly identify secrets leakage as a separate risk rather than calling the secret itself reasoning leakage

## Case 9 — insufficient fragment

```text
I should check this.
```

Expected:
- Classification: E or B depending on available context
- Confidence: Low
- Do not assert model authorship
- Retrieve surrounding context before enforcement recommendation

## Case 10 — repeated false positive pattern

Ten independent architecture documents contain:

```text
We should probably document this tradeoff.
```

Expected:
- Individual classification: Harmless developer prose
- Recommend reviewing the `we should probably` medium rule because repeated evidence now supports a precision issue
- State expected precision/recall consequence of changing the rule
