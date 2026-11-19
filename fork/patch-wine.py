#!/usr/bin/env python3
"""Fork-only: make the Windows setup build on the Linux host when it runs under Wine.

Upstream's setup refuses to run under Wine (setup/main.cpp, runningUnderWine()) and,
with that disabled, its engine still runs the Windows compile path (PowerShell,
MSVC Build Tools), which cannot work under Wine.

This fork adds two things to setup/main.cpp:

1. runningUnderWine() reports false, so the silent installer and the wizard get
   past the refusal (the wizard keeps its normal UI and progress).
2. startEngine() detects Wine itself and hands the already unpacked and verified
   payload to the ffny-linux-updater bridge (wine-update-bridge.exe), which
   cross-compiles the game on Linux and writes the install receipts.

The bridge is looked up, in order, at FFNY_BRIDGE, next to this setup, in
<setup dir>\\ffny-tools, in the current directory and in
<install dir>\\..\\..\\ffny-tools.

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

ENGINE_SIGNATURE = "HANDLE startEngine(std::vector<std::wstring> args) {\n"
BRIDGE_PATCH = (
    "// FORK PATCH (fork/patch-wine.py): under Wine the Windows compiler is not\n"
    "// available, so the setup hands its verified payload to the Linux host builder.\n"
    "static fs::path wineUpdateBridge(const std::vector<std::wstring>& args) {\n"
    "    std::vector<fs::path> candidates;\n"
    "    std::vector<wchar_t> value(32768);\n"
    "    DWORD size = GetEnvironmentVariableW(L\"FFNY_BRIDGE\", value.data(), (DWORD)value.size());\n"
    "    if (size && size < value.size()) candidates.emplace_back(std::wstring(value.data(), size));\n"
    "    wchar_t buffer[32768];\n"
    "    if (GetModuleFileNameW(nullptr, buffer, 32768)) {\n"
    "        auto here = fs::path(buffer).parent_path();\n"
    "        candidates.push_back(here / L\"wine-update-bridge.exe\");\n"
    "        candidates.push_back(here / L\"ffny-tools\" / L\"wine-update-bridge.exe\");\n"
    "    }\n"
    "    if (GetCurrentDirectoryW(32768, buffer)) {\n"
    "        auto here = fs::path(buffer);\n"
    "        candidates.push_back(here / L\"wine-update-bridge.exe\");\n"
    "        candidates.push_back(here / L\"ffny-tools\" / L\"wine-update-bridge.exe\");\n"
    "    }\n"
    "    for (size_t i = 0; i + 1 < args.size(); ++i)\n"
    "        if (args[i] == L\"--install-dir\")\n"
    "            candidates.push_back(fs::path(args[i + 1]) / L\"..\" / L\"..\" / L\"ffny-tools\"\n"
    "                                  / L\"wine-update-bridge.exe\");\n"
    "    std::error_code error;\n"
    "    for (const auto& candidate : candidates)\n"
    "        if (fs::is_regular_file(candidate, error)) return candidate;\n"
    "    return {};\n"
    "}\n"
    "\n"
    "HANDLE startEngine(std::vector<std::wstring> args) {\n"
    "    // FORK PATCH (fork/patch-wine.py): build on Linux when running under Wine.\n"
    "    {\n"
    "        HMODULE ntdll = GetModuleHandleW(L\"ntdll.dll\");\n"
    "        if (ntdll && GetProcAddress(ntdll, \"wine_get_version\")) {\n"
    "            auto bridge = wineUpdateBridge(args);\n"
    "            if (bridge.empty())\n"
    "                throw std::runtime_error(\n"
    "                    \"FFNY Online on Linux/Wine builds with ffny-linux-updater. Download it from \"\n"
    "                    \"github.com/N4ML355/ffny-linux-updater, run its setup once, then start this \"\n"
    "                    \"setup from its ffny-tools folder (next to wine-update-bridge.exe) or set \"\n"
    "                    \"FFNY_BRIDGE to that file.\");\n"
    "            std::vector<std::wstring> bridgeArgs{L\"--payload\", payload.wstring()};\n"
    "            bridgeArgs.insert(bridgeArgs.end(), args.begin(), args.end());\n"
    "            bool hasLog = false;\n"
    "            for (const auto& arg : args) if (arg == L\"--log\") hasLog = true;\n"
    "            if (!hasLog) { bridgeArgs.push_back(L\"--log\"); bridgeArgs.push_back(logPath.wstring()); }\n"
    "            nativeLogIfReady(\"Starting the Linux build bridge: \" + narrow(bridge.wstring()));\n"
    "            return spawn(bridge, bridgeArgs);\n"
    "        }\n"
    "    }\n"
)


def patched_text(text):
    head = HEAD.search(text)
    if not head:
        raise ValueError("runningUnderWine() not found in setup/main.cpp; the patch needs an update")
    tail = CLOSE.search(text, head.end())
    if not tail:
        raise ValueError("Unbalanced braces in runningUnderWine()")
    text = text[: head.start()] + PATCHED_BODY + text[tail.end():]
    if text.count(ENGINE_SIGNATURE) != 1:
        raise ValueError("startEngine() not found exactly once in setup/main.cpp; the patch needs an update")
    return text.replace(ENGINE_SIGNATURE, BRIDGE_PATCH, 1)


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
    print("fork/patch-wine.py: applied (Wine hands the payload to the Linux builder)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ValueError as error:
        print(f"fork/patch-wine.py: {error}", file=sys.stderr)
        sys.exit(1)
