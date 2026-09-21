#!/usr/bin/env python3
"""Generate workflows/lead-response-workflows.json from workflows/individual/.

The bundle is generated, never hand edited. One source of truth: the individual
files. Run this after changing any workflow, then commit both.

    python3 scripts/build_bundle.py            # write the bundle
    python3 scripts/build_bundle.py --check    # exit 1 if the committed bundle is stale
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
INDIVIDUAL = ROOT / "workflows" / "individual"
BUNDLE = ROOT / "workflows" / "lead-response-workflows.json"

VERSION = "1.3"
BUILT = "2026-09-21"

PLACEHOLDERS = {
    "__WF_ERROR__": "id of the imported 'Core 0: Error Handler'",
    "__WF_SENDSMS__": "id of the imported 'Core 1: Send SMS'",
    "__WF_ALERT__": "id of the imported 'Core 3: Owner Alert'",
    "__WF_PIPELINE__": "id of the imported 'Lead Pipeline'",
    "__OWNER_CELL__": "the business owner mobile number in E.164, e.g. +15551234567",
    "__BUSINESS_NUMBER__": "the Twilio number customers text and call, in E.164",
    "__OWNER_EMAIL__": "the email address owner alerts fall back to",
    "__N8N_HOST__": "your n8n host, e.g. yourname.app.n8n.cloud",
}


def load_workflows():
    """Individual files in filename order, which is import order."""
    files = sorted(INDIVIDUAL.glob("*.json"))
    if not files:
        sys.exit("no workflow files found in workflows/individual/")
    out, bad = [], []
    for f in files:
        try:
            out.append((f, json.loads(f.read_text(encoding="utf-8"))))
        except json.JSONDecodeError as e:
            bad.append(f"  {f.relative_to(ROOT)} is not valid JSON: {e}")
    if bad:
        sys.exit("FAIL: cannot build the bundle.\n" + "\n".join(bad))
    return out


def build():
    workflows = [wf for _, wf in load_workflows()]
    return {
        "package": "Lead Response for home service businesses",
        "version": VERSION,
        "built": BUILT,
        "built_by": "Matthews Automation",
        "install_order": [wf["name"] for wf in workflows],
        "placeholders": PLACEHOLDERS,
        "workflows": workflows,
        "source": (
            "Extracted from a live production install. Credentials stripped, "
            "identifiers replaced with placeholders."
        ),
    }


def serialise(bundle):
    return json.dumps(bundle, indent=2, ensure_ascii=False) + "\n"


def main():
    text = serialise(build())
    if "--check" in sys.argv:
        if not BUNDLE.exists():
            sys.exit("FAIL: the bundle does not exist. Run scripts/build_bundle.py")
        if BUNDLE.read_text(encoding="utf-8") != text:
            sys.exit(
                "FAIL: the committed bundle does not match the individual workflows.\n"
                "      Run: python3 scripts/build_bundle.py  then commit the result."
            )
        print("OK: the bundle matches the individual workflows")
        return
    BUNDLE.write_text(text, encoding="utf-8")
    n = len(build()["workflows"])
    print(f"wrote {BUNDLE.relative_to(ROOT)} with {n} workflows, version {VERSION}")


if __name__ == "__main__":
    main()
