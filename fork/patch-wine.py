#!/usr/bin/env python3
"""Fork-only: disable the setup's Wine refusal (setup/main.cpp).

The upstream check refuses to run the Windows setup under Wine. This fork only
ever edits the *definition* of runningUnderWine() in setup/main.cpp: every
caller (the silent installer and the wizard) goes through it, so one body
replacement disables the check everywhere.

The patched source is never committed: the workflow applies this on a CI
checkout before building, so `git merge upstream/main` stays conflict-free
forever (everything this fork adds lives in fork/ and .github/workflows/).

Usage:
  python3 fork/patch-wine.py           # apply (idempotent)
  python3 fork/patch-wine.py --check   # 0 when the source is patchable or already patched
"""
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
MAIN_CPP = REPO / "setup" / "main.cpp"

HEAD = re.compile(r"bool runningUnderWine\(\) \{\n")
CLOSE = re.compile(r"\n\}\n")
PATCHED_BODY = (
    "bool runningUnderWine() {\n"
    "    /* FORK PATCH (fork/patch-wine.py): the Wine check is disabled so the\n"
    "     * setup can run on Linux under Wine. See fork/README.md. */\n"
    "    return false;\n"
    "}\n"
)


def patched_text(text):
    head = HEAD.search(text)
    if not head:
        raise ValueError("runningUnderWine() not found in setup/main.cpp; the patch needs an update")
    tail = CLOSE.search(text, head.end())
    if not tail:
        raise ValueError("Unbalanced braces in runningUnderWine()")
    return text[: head.start()] + PATCHED_BODY + text[tail.end():]


def is_patched(text):
    return "FORK PATCH (fork/patch-wine.py)" in text


def main():
    check = "--check" in sys.argv[1:]
    text = MAIN_CPP.read_text(encoding="utf-8")
    if is_patched(text):
        print("fork/patch-wine.py: setup/main.cpp is already patched")
        return 0
    result = patched_text(text)
    if check:
        print("fork/patch-wine.py: check ok (setup/main.cpp is patchable)")
        return 0
    MAIN_CPP.write_text(result, encoding="utf-8")
    print("fork/patch-wine.py: applied (the Wine check now reports false)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ValueError as error:
        print(f"fork/patch-wine.py: {error}", file=sys.stderr)
        sys.exit(1)
