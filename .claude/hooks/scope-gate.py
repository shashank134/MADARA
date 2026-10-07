#!/usr/bin/env python3
"""Claude Code PreToolUse hook: deny-by-default scope enforcement.

Reads the PreToolUse JSON on stdin, pulls any target host(s) out of the tool
call, and checks them against the ACTIVE program scope (reusing the tested
madara.scope.ScopeGuard). Out-of-scope -> permissionDecision "deny".

Active scope file: $MADARA_SCOPE, else scope/active.yaml under the project.

Scope is checked for:
  - WebFetch / browser tools: the url/uri argument.
  - Bash: ONLY when the command's binary is a known network tool (curl, nuclei,
    subfinder, ...). Other commands (cat, echo, git, python, ls) are not scanned,
    so a filename like README.md or a domain mentioned in text is never treated
    as a live target. This is defence-in-depth for an authorized engagement, not
    a sandbox; keep the permission allow/deny lists as the primary control.
Common infra hosts (package registries, git) are always allowed.
"""
import json
import os
import re
import shlex
import sys
from urllib.parse import urlparse

PROJECT = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
sys.path.insert(0, PROJECT)

# Bash commands are scope-checked only when the binary at a command position is
# one of these. Kept to unambiguous tool names — common English words like
# "host"/"ping"/"dig" are deliberately excluded to avoid matching prose.
NETWORK_TOOLS = {
    "curl", "wget", "httpx", "httprobe", "nuclei", "ffuf", "feroxbuster",
    "gobuster", "dirsearch", "subfinder", "amass", "dnsx", "naabu", "nmap",
    "masscan", "katana", "hakrawler", "gau", "waybackurls", "whatweb",
    "wafw00f", "nikto", "sqlmap", "dalfox",
}
SHELL_OPS = {"|", "||", "&&", ";", "&", "(", ")", "{", "}"}
INFRA_ALLOW = {
    "github.com", "raw.githubusercontent.com", "objects.githubusercontent.com",
    "pypi.org", "files.pythonhosted.org", "registry.npmjs.org", "npmjs.com",
    "go.dev", "proxy.golang.org", "sum.golang.org",
}
# Final-label values that mean "this is a filename", not a host.
FILE_EXTS = {
    "md", "py", "js", "ts", "json", "yaml", "yml", "txt", "sh", "html", "htm",
    "css", "go", "rs", "c", "h", "cpp", "java", "rb", "php", "xml", "toml",
    "ini", "cfg", "conf", "log", "csv", "tsv", "db", "sqlite", "png", "jpg",
    "jpeg", "gif", "svg", "pdf", "zip", "tar", "gz", "lock", "env", "pem", "key",
}
URL_KEYS = ("url", "uri", "href", "target")
_DOMAIN = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$", re.I)


def _allow():
    sys.exit(0)  # no decision; normal permission flow continues


def _deny(reason: str):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}))
    sys.exit(0)


def _host_of(token: str) -> str | None:
    """Return a hostname if `token` denotes one, else None."""
    token = token.strip().strip('"').strip("'")
    if "://" in token:
        h = urlparse(token).hostname
        return h.lower() if h else None
    if "/" in token:
        return None  # a path, not a bare host
    if _DOMAIN.match(token):
        last = token.rsplit(".", 1)[-1].lower()
        if last in FILE_EXTS or not last.isalpha() or len(last) < 2:
            return None
        return token.lower()
    return None


def candidate_hosts(tool_name: str, tool_input: dict) -> list[str]:
    hosts: list[str] = []
    for k in URL_KEYS:
        v = tool_input.get(k)
        if isinstance(v, str):
            h = _host_of(v)
            if h:
                hosts.append(h)
    if tool_name == "Bash":
        cmd = tool_input.get("command", "")
        try:
            parts = shlex.split(cmd)
        except ValueError:
            parts = cmd.split()
        # Trigger only when a network tool appears at a COMMAND POSITION (first
        # token, or just after a shell operator) — so a tool name sitting in a
        # commit message or string doesn't trigger. Once triggered, scan every
        # token for host-like strings (catches `echo host | httpx` stdin pipes).
        # KNOWN LIMITS (best-effort, not a sandbox): targets inside a file passed
        # by path (`-l targets.txt`) are invisible; a domain in a header/string
        # alongside a network tool may over-block. Permission lists are primary.
        triggered, expect_cmd = False, True
        for tok in parts:
            if tok in SHELL_OPS:
                expect_cmd = True
                continue
            if expect_cmd and os.path.basename(tok) in NETWORK_TOOLS:
                triggered = True
            expect_cmd = False
        if triggered:
            for tok in parts:
                h = _host_of(tok)
                if h:
                    hosts.append(h)
    out, seen = [], set()
    for h in hosts:
        h = h.rstrip(".")
        if h in INFRA_ALLOW or h in seen:
            continue
        seen.add(h)
        out.append(h)
    return out


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        _allow()
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {}) or {}

    hosts = candidate_hosts(tool_name, tool_input)
    if not hosts:
        _allow()

    scope_path = os.environ.get("MADARA_SCOPE") or os.path.join(PROJECT, "scope", "active.yaml")
    if not os.path.exists(scope_path):
        _deny(f"No active scope loaded (looked for {scope_path}). This call targets "
              f"{', '.join(hosts)}. Copy a scope file to scope/active.yaml or set "
              f"MADARA_SCOPE before hitting external hosts.")

    try:
        from madara.config import Scope
        from madara.scope import ScopeGuard, OutOfScope
        guard = ScopeGuard(Scope.load(scope_path))
    except Exception as e:
        _deny(f"Scope file could not be loaded ({e}); blocking external call to "
              f"{', '.join(hosts)} until scope is valid.")

    for h in hosts:
        try:
            guard.check_url(f"https://{h}/")
        except OutOfScope as e:
            _deny(f"{e}  (tool: {tool_name})")
    _allow()


if __name__ == "__main__":
    main()
