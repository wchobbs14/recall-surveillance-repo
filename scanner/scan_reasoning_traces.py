#!/usr/bin/env python3
import argparse
import fnmatch
import json
import os
import re
import sys
from pathlib import Path

TEXT_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs", ".rb", ".php", ".c", ".h", ".cpp", ".hpp",
    ".cs", ".swift", ".kt", ".kts", ".scala", ".sh", ".bash", ".zsh", ".fish", ".ps1", ".sql", ".html", ".css",
    ".scss", ".sass", ".less", ".vue", ".svelte", ".md", ".mdx", ".rst", ".txt", ".json", ".jsonl", ".yaml", ".yml",
    ".toml", ".ini", ".cfg", ".conf", ".xml", ".graphql", ".gql", ".env", ".example"
}


def load_policy(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def excluded(relpath: str, globs):
    rel = relpath.replace(os.sep, "/")
    return any(fnmatch.fnmatch(rel, g) or fnmatch.fnmatch("/" + rel, g) for g in globs)


def looks_textual(path: Path, binary_exts):
    if path.suffix.lower() in binary_exts:
        return False
    if path.suffix.lower() in TEXT_EXTENSIONS or path.name in {"Dockerfile", "Makefile", "Procfile", ".env", ".gitignore"}:
        return True
    try:
        chunk = path.read_bytes()[:4096]
    except OSError:
        return False
    if b"\x00" in chunk:
        return False
    return True


def classify_context(path: Path, line: str):
    s = line.lstrip()
    ext = path.suffix.lower()
    if ext in {".md", ".mdx", ".rst", ".txt"}:
        return "documentation"
    if s.startswith(("#", "//", "/*", "*", "--", ";")):
        return "comment"
    if '"""' in line or "'''" in line:
        return "docstring-or-string"
    if ext in {".json", ".jsonl", ".yaml", ".yml", ".toml", ".xml"}:
        return "structured-data"
    return "code-or-string"


def scan_file(path: Path, relpath: str, compiled, suppression_token: str):
    findings = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return findings
    suppress_next = False
    for idx, line in enumerate(lines, start=1):
        if suppression_token in line:
            suppress_next = True
            continue
        if suppress_next:
            suppress_next = False
            continue
        for severity, rules in compiled.items():
            for rule_id, rx in rules:
                m = rx.search(line)
                if m:
                    findings.append({
                        "file": relpath,
                        "line": idx,
                        "severity": severity,
                        "rule": rule_id,
                        "context": classify_context(path, line),
                        "excerpt": line.strip()[:500]
                    })
    return findings


def main():
    parser = argparse.ArgumentParser(description="Scan a repository for plausible escaped reasoning traces.")
    parser.add_argument("root", nargs="?", default=".")
    parser.add_argument("--policy", default=None)
    parser.add_argument("--json-out", default="reasoning-trace-report.json")
    parser.add_argument("--fail-on", choices=["high", "medium", "none"], default="high")
    parser.add_argument("--files-from", default=None, help="Optional newline-separated relative paths to scan (e.g. PR changed files).")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    policy_path = Path(args.policy).resolve() if args.policy else Path(__file__).with_name("patterns.json")
    policy = load_policy(policy_path)
    compiled = {
        sev: [(r["id"], re.compile(r["pattern"])) for r in policy.get(sev, [])]
        for sev in ("high", "medium")
    }
    excludes = policy.get("exclude_globs", [])
    binary_exts = set(policy.get("binary_extensions", []))
    suppression = policy.get("suppression_token", "reasoning-trace-audit: ignore-next-line")

    if args.files_from:
        candidates = []
        for raw in Path(args.files_from).read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            p = root / raw
            if p.exists() and p.is_file():
                candidates.append(p)
    else:
        candidates = [p for p in root.rglob("*") if p.is_file()]

    findings = []
    scanned = 0
    for p in candidates:
        rel = p.relative_to(root).as_posix()
        if excluded(rel, excludes) or not looks_textual(p, binary_exts):
            continue
        scanned += 1
        findings.extend(scan_file(p, rel, compiled, suppression))

    rank = {"high": 0, "medium": 1}
    findings.sort(key=lambda f: (rank[f["severity"]], f["file"], f["line"]))
    counts = {"high": sum(f["severity"] == "high" for f in findings), "medium": sum(f["severity"] == "medium" for f in findings)}
    report = {"policy_version": policy.get("version"), "scanned_files": scanned, "counts": counts, "findings": findings}
    Path(args.json_out).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    for f in findings:
        prefix = "ERROR" if f["severity"] == "high" else "WARNING"
        print(f"::{ 'error' if f['severity']=='high' else 'warning' } file={f['file']},line={f['line']}::{prefix} [{f['rule']}] {f['excerpt']}")
    print(f"Scanned {scanned} files: {counts['high']} high, {counts['medium']} medium findings.")

    should_fail = args.fail_on == "high" and counts["high"] > 0
    should_fail = should_fail or (args.fail_on == "medium" and (counts["high"] + counts["medium"] > 0))
    sys.exit(1 if should_fail else 0)


if __name__ == "__main__":
    main()
