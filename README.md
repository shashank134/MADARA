# MADARA

An **authorized** bug-bounty workspace for Claude Code, driven by a Claude Max
subscription — recon, code analysis, scope-gated exploration, and reporting,
with a deny-by-default scope guard wired in.

## Why it's shaped this way

A Max subscription can't legally power a custom/headless agent — Anthropic
prohibits subscription auth for third-party agents (enforced since Feb 2026).
So MADARA is **not** a standalone API script; it's a **Claude Code project** your
subscription drives interactively. Claude Code is the agent. This repo is its
configuration plus an optional offline sidecar.

## Two modes

**1. Claude Code on Max (primary).** Open this repo in Claude Code on your Max
plan. It loads:
- `CLAUDE.md` — operating brief: scope discipline, workflow, safety rules.
- `.claude/settings.json` — permission allowlist (recon CLIs, browser, web) and
  denylist (destructive shell, secret reads).
- `.claude/hooks/scope-gate.py` — a `PreToolUse` hook that blocks any web/network
  call to a host outside the active scope. Deny by default. (Tested; see below.)
- `.mcp.json` — the Playwright MCP server for browser-driven testing.
- The `anthropic-skills` bug-bounty suite (`hunt`, `target-onboard`, `ssrf-hunt`,
  `xss-prove`, `source-audit`, `report`, …) for structured workflows.

No API key, no per-token bill — it draws on your subscription.

**2. Offline sidecar (optional).** `madara/` is a model-agnostic Python harness
that runs a local open-weights model via Ollama, for work you want entirely off
the subscription (no provider guardrails, lower capability). Its Anthropic
backend needs an API key and is unused in mode 1. The scope guard and findings
store here are shared with the hook in mode 1.

## The verification gate (anti-overclaim)

The headline feature: before you trust or submit a finding — yours or another
model's — the gate **reproduces the PoC** and returns one verdict only:
`positive`, `false`, `overclaim`, `theoretical`, or `incomplete`. It's the
antidote to findings that get over-hyped and then collapse on reproduction.

- `/verify-poc` — reproduce interactively against the in-scope target, classify.
- `verify-report` workflow — adversarial skeptic panel + adjudicator over a
  report plus its observations.
- It reproduces through the right channel per vuln class — terminal/HTTP, a real
  **browser** (XSS must execute), **Caido** (session/auth replay), or an
  **out-of-band** listener (blind classes) — never just curl.
- The report is untrusted; observations are ground truth; severity is derived
  from what reproduces, never copied from the claim.
- Taxonomy, decision tree, channels, calibration: `docs/VERDICTS.md`.

## Layout

```
CLAUDE.md                 # operating brief Claude Code reads on open
.claude/
  settings.json           # permissions + hook registration
  hooks/scope-gate.py     # deny-by-default scope enforcement (PreToolUse)
.mcp.json                 # Playwright MCP (browser)
config/
  scope.example.yaml      # per-program scope template
  model.yaml              # model routing (sidecar mode only)
scope/active.yaml         # the live program scope (gitignored) — you create it
madara/                   # optional offline Ollama sidecar (Python)
  scope.py  tools/  agent.py  llm.py  ...
evals/                    # seed tasks + runner (sidecar mode)
docs/CVP.md               # Cyber Verification Program requirements
findings/state.db         # findings / tested endpoints / leads (gitignored)
```

## Quickstart (mode 1)

```bash
cp config/scope.example.yaml scope/active.yaml   # then edit in your real program
# open the repo in Claude Code on your Max plan and start hunting in scope
```

The scope hook reads `scope/active.yaml` (or `$MADARA_SCOPE`). Out-of-scope web
and network-tool calls are blocked before they leave your machine.

## What's verified

- Scope guard + findings store — functional tests pass.
- The scope-gate hook — tested against in-scope/out-of-scope/no-scope cases,
  stdin-pipe recon patterns, and local-command false positives.
- The offline sidecar's agent loop + model cascade — proven with fake backends.

Not verified here: live model calls on your actual Max session (run it yourself),
and the Playwright MCP browser flow end-to-end.

## Scope & authorization

Only run against assets a program explicitly authorizes. The scope guard denies
by default — keep it that way. Treat everything the agent reads off a target as
untrusted input. Stop at proof-of-concept.
