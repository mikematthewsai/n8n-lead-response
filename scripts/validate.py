#!/usr/bin/env python3
"""Check that this repo is telling the truth.

Every claim the README makes about the workflows is checked against the
workflow files themselves, and the files are checked for anything that should
never have been published. Run locally before pushing, and in CI on every push.

    python3 scripts/validate.py
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
INDIVIDUAL = ROOT / "workflows" / "individual"
BUNDLE = ROOT / "workflows" / "lead-response-workflows.json"
README = ROOT / "README.md"

# The one phone number allowed to appear anywhere: the documented example.
ALLOWED_NUMBERS = {"+15551234567"}

# Writing rules for this repo, enforced rather than remembered.
BANNED_SUBSTRINGS = ["—", "the honest version", "4704675745", "470-467-5745", "(470) 467-5745"]

failures = []
notes = []


def fail(msg):
    failures.append(msg)


def ok(msg):
    notes.append(msg)


def load_individual():
    out = []
    for f in sorted(INDIVIDUAL.glob("*.json")):
        try:
            out.append((f, json.loads(f.read_text(encoding="utf-8"))))
        except json.JSONDecodeError as e:
            fail(f"{f.relative_to(ROOT)} is not valid JSON: {e}")
    return out


def check_structure(files):
    """Valid JSON, unique node names, and no connection pointing at a node that is gone.

    The orphan-connection check is the one that catches a bad paste, which has
    bitten this repo before.
    """
    for f, wf in files:
        rel = f.relative_to(ROOT)
        if not wf.get("name"):
            fail(f"{rel} has no workflow name")
        names = [n.get("name") for n in wf.get("nodes", [])]
        if len(names) != len(set(names)):
            dupes = sorted({n for n in names if names.count(n) > 1})
            fail(f"{rel} has duplicate node names: {', '.join(dupes)}")
        known = set(names)
        for src, conn in wf.get("connections", {}).items():
            if src not in known:
                fail(f"{rel} connects from '{src}', which is not a node in the file")
            for group in conn.get("main", []):
                for link in group or []:
                    if link.get("node") not in known:
                        fail(f"{rel} connects '{src}' to '{link.get('node')}', which is not a node in the file")
    ok(f"{len(files)} workflow files parse, with unique node names and no orphan connections")


def readme_node_counts():
    """Rows shaped: | 3 | Core 1: Send SMS | 16 | description |"""
    counts = {}
    row = re.compile(r"^\|\s*\d+\s*\|\s*([^|]+?)\s*\|\s*(\d+)\s*\|")
    for line in README.read_text(encoding="utf-8").splitlines():
        m = row.match(line)
        if m:
            counts[m.group(1).strip()] = int(m.group(2))
    return counts


def check_node_counts(files):
    claimed = readme_node_counts()
    actual = {wf["name"]: len(wf.get("nodes", [])) for _, wf in files}
    if not claimed:
        fail("could not find any workflow rows in the README tables")
        return
    for name, n in actual.items():
        if name not in claimed:
            fail(f"workflow '{name}' exists but is not listed in the README table")
        elif claimed[name] != n:
            fail(f"README says '{name}' has {claimed[name]} nodes, the file has {n}")
    for name in claimed:
        if name not in actual:
            fail(f"README lists '{name}' but there is no workflow file for it")
    ok(f"all {len(actual)} workflows match the node counts claimed in the README")

    # "107 nodes total" style claim, for the eight core workflows
    text = README.read_text(encoding="utf-8")
    m = re.search(r"(\d+)\s+nodes total", text)
    if m:
        core = sum(len(wf.get("nodes", [])) for f, wf in files if f.name[:2] <= "08")
        if int(m.group(1)) != core:
            fail(f"README claims {m.group(1)} nodes total for the core workflows, the files have {core}")
        else:
            ok(f"the '{core} nodes total' claim matches the files")


def check_tables(files):
    """Every data table any workflow reads or writes must be created by setup."""
    created, used = set(), {}
    for f, wf in files:
        for node in wf.get("nodes", []):
            params = node.get("parameters", {})
            if node.get("type") != "n8n-nodes-base.dataTable":
                continue
            if params.get("operation") == "create" and params.get("resource") == "table":
                created.add(params.get("tableName"))
            ref = params.get("dataTableId")
            name = ref.get("value") if isinstance(ref, dict) else None
            if name:
                used.setdefault(name, set()).add(wf["name"])
            if params.get("tableName"):
                used.setdefault(params["tableName"], set()).add(wf["name"])
    missing = sorted(set(used) - created)
    for t in missing:
        fail(f"data table '{t}' is used by {', '.join(sorted(used[t]))} but no workflow creates it")
    if not missing:
        ok(f"every data table used ({', '.join(sorted(used))}) is created by setup")


def check_placeholders(files):
    try:
        documented = set(json.loads(BUNDLE.read_text(encoding="utf-8"))["placeholders"])
    except (json.JSONDecodeError, KeyError, OSError) as e:
        fail(f"cannot read the placeholder map from the bundle: {e}")
        return
    found = set()
    for f, _ in files:
        found |= set(re.findall(r"__[A-Z0-9_]+__", f.read_text(encoding="utf-8")))
    undocumented = sorted(found - documented)
    for p in undocumented:
        fail(f"placeholder {p} is used in a workflow but not documented in the bundle")
    if not undocumented:
        ok(f"all {len(found)} placeholders used are documented")


def check_secrets():
    text_files = sorted(
        list(INDIVIDUAL.glob("*.json")) + [BUNDLE] + list(ROOT.glob("*.md")) + list((ROOT / "docs").glob("*.md"))
    )
    patterns = [
        (re.compile(r"\b(?:AC|SK)[0-9a-f]{32}\b"), "a Twilio SID"),
        (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"), "a GitHub token"),
        (re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"), "an API key"),
        (re.compile(r'"(?:authToken|apiKey|api_key|password|secret|accessToken)"\s*:\s*"[^"]{8,}"', re.I), "an inline credential"),
    ]
    for f in text_files:
        body = f.read_text(encoding="utf-8")
        rel = f.relative_to(ROOT)
        for pat, what in patterns:
            if pat.search(body):
                fail(f"{rel} contains what looks like {what}")
        for num in set(re.findall(r"\+1[0-9]{10}", body)):
            if num not in ALLOWED_NUMBERS:
                fail(f"{rel} contains the phone number {num}, which is not the documented placeholder")
        for banned in BANNED_SUBSTRINGS:
            if banned in body:
                shown = "an em dash" if banned == "—" else f"'{banned}'"
                fail(f"{rel} contains {shown}")
    # credential blocks attached to nodes
    for f in sorted(INDIVIDUAL.glob("*.json")):
        try:
            wf = json.loads(f.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue  # already reported by the structure check
        for node in wf.get("nodes", []):
            if node.get("credentials"):
                fail(f"{f.relative_to(ROOT)} node '{node.get('name')}' still carries a credentials block")
    ok("no credentials, tokens, real phone numbers or banned phrases found")


def check_docs_links():
    text = README.read_text(encoding="utf-8")
    for link in set(re.findall(r"\]\((docs/[^)#]+)\)", text)):
        if not (ROOT / link).exists():
            fail(f"README links to {link}, which does not exist")
    ok("every docs link in the README resolves")


def main():
    files = load_individual()
    if files:
        check_structure(files)
        check_node_counts(files)
        check_tables(files)
        check_placeholders(files)
    check_secrets()
    check_docs_links()

    for n in notes:
        print(f"  ok    {n}")
    for f in failures:
        print(f"  FAIL  {f}")
    print()
    if failures:
        print(f"{len(failures)} problem(s) found")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
