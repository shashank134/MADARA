#!/usr/bin/env bash
# MADARA — local setup for macOS (Claude Code on a Max subscription).
# Idempotent: safe to re-run. It checks prerequisites, installs the one Python
# dep the scope hook needs, prepares your scope file, and prints next steps.
# It does NOT install Caido (manual) or the full recon toolchain (optional).

set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$(pwd)"
ok(){ printf '  \033[32m✓\033[0m %s\n' "$1"; }
warn(){ printf '  \033[33m!\033[0m %s\n' "$1"; }
have(){ command -v "$1" >/dev/null 2>&1; }

echo "MADARA macOS setup — $ROOT"
echo

echo "[1/5] Core prerequisites"
if have python3; then ok "python3 $(python3 -V 2>&1 | awk '{print $2}')"; else
  warn "python3 missing — install:  brew install python"; fi
if have node && have npx; then ok "node $(node -v)"; else
  warn "node/npx missing (needed for the Playwright browser) — install:  brew install node"; fi
if have claude; then ok "claude CLI present"; else
  warn "Claude Code CLI missing — install it, then run 'claude' and sign in with your Max account"; fi
if have curl; then ok "curl present"; else warn "curl missing (unexpected on macOS)"; fi

echo "[2/5] Python dep for the scope hook (pyyaml, into user site so the hook's python3 finds it)"
if python3 -c 'import yaml' 2>/dev/null; then ok "pyyaml already importable"; else
  python3 -m pip install --user pyyaml >/dev/null 2>&1 && ok "installed pyyaml" \
    || warn "could not install pyyaml — run:  python3 -m pip install --user pyyaml"; fi

echo "[3/5] Scope file"
if [ -f scope/active.yaml ]; then ok "scope/active.yaml exists (leaving it)"; else
  cp config/scope.example.yaml scope/active.yaml && ok "created scope/active.yaml from the example — EDIT IT before testing"; fi

echo "[4/5] Browser (Playwright MCP)"
ok ".mcp.json already registers it; Claude Code launches it via npx on first use"
warn "first run will download Chromium via npx — allow a minute"

echo "[5/5] Optional tooling (not installed by this script)"
cat <<'NOTE'
  - Recon CLIs (optional): install ProjectDiscovery suite ->
      brew install pdtm && pdtm -ia
    (subfinder, httpx, nuclei, katana, naabu ...). Also: brew install sqlmap ffuf
  - Caido (for request intercept/replay): install the Caido desktop app/CLI from
    its site, start it, and create a PAT; the caido-mode skill uses that.
NOTE

echo
echo "Next:"
echo "  1) Edit scope/active.yaml for your target program (apex + wildcard domains)."
echo "  2) In this folder run:  claude"
echo "  3) Verify a finding:    /verify-poc  (paste the report + PoC, or point it at an evidence file)"
echo "     The scope hook blocks out-of-scope hosts automatically."
echo
echo "Done."
