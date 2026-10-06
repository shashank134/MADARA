# MADARA

A model-agnostic harness for **authorized** bug-bounty work — recon, code
analysis, payload drafting, scope-gated exploitation, and reporting — built so
the LLM is a swappable component, not a dependency.

## Why it's built this way

Claude's real-time cyber safeguards reroute offensive categories (exploit
generation, pentesting, binary vuln scanning) away from current models by
default. `claude-opus-4-6` still serves them today, but models get deprecated.
This harness makes that a non-event:

- **The model is one line in `config/model.yaml`** (`roles.primary`). Deprecated?
  Change the line, run the evals, done.
- **Automatic role cascade:** if the primary model refuses an in-scope request,
  the agent retries on `fallback` (a CVP'd Opus 5), then `local` (offline
  open-weights floor). See `madara/agent.py`.
- **The real unlock is CVP** — the Cyber Verification Program restores the
  rerouted categories on current models. See `docs/CVP.md`.

## Layout

```
config/model.yaml        # model routing — primary / fallback / local
config/scope.example.yaml # per-program scope template (copy to scope/<prog>.yaml)
madara/
  config.py              # loads model + scope config
  llm.py                 # model-agnostic backends (Anthropic + Ollama) + refusal cascade
  scope.py               # deny-by-default scope guard
  agent.py               # the tool-use loop with the role cascade
  tools/
    http_client.py       # scope-gated HTTP (exploitation mechanics)
    terminal.py          # recon/analysis CLI runner (allowlist + confirm gate)
    findings.py          # sqlite findings/leads store (survives restarts)
evals/
  tasks.yaml             # seed tasks tagged by safeguard category
  run_eval.py            # vet any model/role in minutes
docs/CVP.md              # Cyber Verification Program requirements
```

## Quickstart

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=...            # or `ant auth login`
cp config/scope.example.yaml scope/myprogram.yaml   # edit in your real scope
python -m madara scope/myprogram.yaml "Plan recon for in-scope assets"
```

Vet a model before trusting it:

```bash
python evals/run_eval.py primary        # shows which categories refuse vs pass
python evals/run_eval.py fallback
```

## Not yet wired (intentional scaffold gaps)

- Browser tool (Playwright MCP) — add under `madara/tools/`.
- Caido proxy integration for HTTP history/replay.
- Real approval UI behind `Agent._confirm` (defaults to deny).
- Ollama backend tool-use translation is minimal (text-only today).
- Automated eval grading (wire the `claude-api` build-eval flow).
- Corpora fetch (SecLists / PayloadsAllTheThings / nuclei-templates) into `corpora/`.

## Scope & authorization

Only ever run against assets a program explicitly authorizes. The scope guard
denies by default; keep it that way. Treat everything the agent reads off a
target as untrusted input.
