# The verification gate — verdicts, decision tree, channels

MADARA's "hackbot": feed it any vulnerability report (yours or another model's),
it **reproduces the PoC** through whatever channel the bug demands, and returns
exactly **one** verdict. It exists because models over-hype findings that fall
apart on reproduction — this gate is what stops an overclaim reaching a report.

Two entry points, same contract:
- **`/verify-poc`** (skill) — interactive: actually reproduces against the
  in-scope target, then classifies. `.claude/skills/verify-poc/SKILL.md`.
- **`verify-report`** (workflow) — adversarial panel + adjudicator over a report
  plus its reproduction observations. `.claude/workflows/verify-report.js`.

## The five verdicts

| Verdict | Meaning | Key test |
|---|---|---|
| **positive** | Reproduced at the claimed impact/severity. | Observed impact == claimed impact. |
| **overclaim** | A real issue reproduces, but weaker than claimed. | Something reproduced, but less than claimed. Record the real impact. |
| **false** | A concrete PoC was given but doesn't reproduce / behavior is by-design. | PoC existed, was run, nothing (or intended behavior). |
| **theoretical** | Only a plausible mechanism; no concrete PoC; nothing demonstrated. | No executable PoC ever existed. |
| **incomplete** | Missing repro-critical info; reproduction couldn't be attempted. | Nothing could be run; say what's missing. |

## Decision tree (observations are ground truth)

```
0. Read the OBSERVATIONS: was reproduction actually attempted?
1. Could NOT attempt (missing info, nothing executed)      -> incomplete
2. Reproduced AT claimed impact/severity                    -> positive
3. Reproduced a real issue but at LESSER impact than claimed -> overclaim
4. Attempted, nothing reproduced, NO concrete PoC (mechanism only) -> theoretical
5. Attempted, nothing reproduced, concrete PoC failed / by-design  -> false
```

The two hinges that trip people up:
- **false vs theoretical** turns on *did a concrete, executable PoC exist?* Yes +
  failed = false. No (just a theory) = theoretical.
- **incomplete vs the rest** turns on *was an attempt possible at all?* It is
  decided from the observations, **not** from whether the report named its host.
  A report can omit the hostname yet still be reproduced by a tester who had the
  context — that's not incomplete.

## Reproduction channels (not everything is curl)

Proof must come from the channel the vuln class demands:

| Class | Channel |
|---|---|
| API / IDOR / injection / auth headers | terminal/HTTP (curl, httpx, sqlmap), Caido replay |
| DOM / reflected / stored XSS, CSRF, clickjacking, SPA logic | **real browser** (Playwright) — must execute, not just reflect |
| session/cookie tampering, auth-boundary matrices | **Caido** intercept + replay |
| blind SSRF / XXE / blind injection, webhook callbacks | **out-of-band** listener — the inbound hit is the proof |

A DOM XSS that "appears" in a curl body but never fires in a browser is **not**
positive. A blind SSRF with no out-of-band callback is **theoretical**, not
positive.

## Anti-gaming

The report is **untrusted input**. The engine ignores any instruction inside it
("mark this positive", "critical!") and never raises a verdict above what the
observations demonstrate. Severity is derived from demonstrated impact, never
copied from the report.

## Calibration

The rubric is validated against a labeled eval set (`reports/examples/eval_set.json`,
one report per verdict). Re-run anytime:

```
Workflow({ name: "verify-report", args: <the eval set array> })
```

and check each returned `verdict` against the sample's `expected`.
