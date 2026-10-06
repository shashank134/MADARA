"""Terminal tool — runs recon/analysis CLIs (subfinder, httpx, nuclei, semgrep,
ffuf, etc.). Destructive patterns require explicit confirmation via a hook.

NOTE: this scaffold runs commands as-is for local use. Before pointing it at
anything shared, add: an allowlist of binaries, a working-dir jail, and a
confirm-gate on state-changing flags. See the `confirm` stub below."""
from __future__ import annotations
import shlex
import subprocess
from typing import Any

# Binaries the agent may invoke without confirmation (read-only recon/analysis).
SAFE_BINARIES = {
    "subfinder", "amass", "dnsx", "httpx", "naabu", "katana", "gau",
    "waybackurls", "nuclei", "ffuf", "semgrep", "whatweb", "curl", "jq",
    "grep", "cat", "ls", "nmap",
}


class TerminalTool:
    name = "run_command"
    description = (
        "Run a recon/analysis shell command and return stdout/stderr. "
        "Read-only recon binaries run directly; anything else is held for "
        "confirmation."
    )
    input_schema = {
        "type": "object",
        "properties": {"command": {"type": "string"}},
        "required": ["command"],
        "additionalProperties": False,
    }

    def __init__(self, confirm=None, timeout: int = 300):
        # confirm(cmd:str)->bool  — wire this to your approval UI / hook.
        self.confirm = confirm or (lambda cmd: False)
        self.timeout = timeout

    def run(self, command: str) -> dict[str, Any]:
        try:
            binary = shlex.split(command)[0]
        except ValueError as e:
            return {"error": "parse_error", "detail": str(e)}
        if binary not in SAFE_BINARIES and not self.confirm(command):
            return {"error": "needs_confirmation",
                    "detail": f"'{binary}' is not in SAFE_BINARIES; confirmation denied."}
        try:
            p = subprocess.run(command, shell=True, capture_output=True,
                               text=True, timeout=self.timeout)
        except subprocess.TimeoutExpired:
            return {"error": "timeout", "detail": f"exceeded {self.timeout}s"}
        return {"returncode": p.returncode,
                "stdout": p.stdout[:20000], "stderr": p.stderr[:5000]}
