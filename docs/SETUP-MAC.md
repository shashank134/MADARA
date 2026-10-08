# Running MADARA on your Mac (Claude Code on Max)

Everything is in the repo. This gets the verification gate running locally, where
your Caido, your browser sessions, and open network access live.

## 1. Clone the repo and the working branch

```bash
git clone https://github.com/shashank134/MADARA.git
cd MADARA
git checkout claude/local-personal-agent-jdpfik
```

## 2. Install Claude Code and sign in with Max

Install the Claude Code CLI/app, then from the `MADARA` folder:

```bash
claude            # on first run, sign in with your Claude Max account
```

Your Max subscription powers it — no API key needed. (Model choice is whatever
Claude Code exposes on the plan; flagged offensive steps may auto-reroute to an
older model — see `docs/VERDICTS.md` and `CLAUDE.md`.)

## 3. Run the setup script

```bash
bash scripts/setup-mac.sh
```

It checks python3 / node / claude, installs `pyyaml` for the scope hook, and
creates `scope/active.yaml` from the example. It does **not** install Caido or
the recon CLIs — those are optional and listed below.

## 4. Optional tooling

- **Recon CLIs:** `brew install pdtm && pdtm -ia` (subfinder, httpx, nuclei,
  katana…), plus `brew install sqlmap ffuf`.
- **Caido** (request intercept/replay): install from caido.io, start it, create a
  Personal Access Token; the `caido-mode` skill uses it.
- **Browser:** nothing to do — `.mcp.json` launches the Playwright MCP server via
  `npx` on first use (it downloads Chromium once).

## 5. Set your scope

Edit `scope/active.yaml` for the program you're verifying against: apex +
wildcard domains, out-of-scope hosts, rate limit, and the authorization note.
The `PreToolUse` scope hook denies any web/network call outside it.

## 6. Verify a finding

In the `MADARA` folder, run `claude`, then:

```
/verify-poc
```

Paste the report and its PoC, or point it at an evidence file (now that you're
local, `/Users/madara/bb-targets/...` is readable). It reproduces through the
channel the vuln class needs and returns one verdict: `positive`, `false`,
`overclaim`, `theoretical`, or `incomplete`.

Per-finding channel notes for your three:
- **Stored XSS + Cloudflare bypass** → browser (the payload must actually execute
  in a real page; Caido to place the stored input and confirm the WAF-bypassed
  request lands).
- **Web Cache Deception via `__NEXT_DATA__`** → curl/Caido two-request proof
  (authenticated victim request caches the response, a separate unauthenticated
  request retrieves the cached credentials) — watch cache headers (`cf-cache-status`, `age`).
- **xsolla-launcher srcdoc RCE** → browser/launcher reproduction per the evidence
  file; confirm the `srcdoc` sink actually executes, not just that markup is present.

For a batch, the `verify-report` workflow classifies several reports at once from
their observations — see `docs/VERDICTS.md`.

## Note on verdicts

The gate treats the report as untrusted and bases the verdict only on what
reproduces. If a step needs Caido or a browser and you run it, paste the
observed result back; the verdict follows the evidence, never the claim.
