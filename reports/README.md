# reports/ — inputs to the verification gate

Drop vulnerability reports here (yours or another model's) to be verified by
`/verify-poc` or the `verify-report` workflow. The gate reproduces the PoC and
returns one verdict: `positive` / `false` / `overclaim` / `theoretical` /
`incomplete`. See `docs/VERDICTS.md`.

## What a report needs to be verifiable

The more of these it has, the further past `incomplete` it can get:
- **Target** — an in-scope host/endpoint.
- **Injection point** — the exact parameter, field, header, or URL.
- **Concrete PoC** — the exact request/payload/steps a third party can run.
- **Claimed impact + severity** — what the author says it achieves.
- **Channel hint** — if it only proves out in a browser or via Caido, say so.

A report missing the target/param/payload will come back `incomplete` with the
specific gaps listed — that's the gate working, not failing.

## Observations

A verdict needs *observations* — what actually happened on reproduction, from
the proving channel (terminal/HTTP, browser, Caido, or an out-of-band listener).
In interactive use, `/verify-poc` produces these by reproducing in scope. When
driving the `verify-report` workflow directly, pass `{id, report, observations}`.

## Example / eval set

`examples/eval_set.json` holds one labeled report per verdict class. It is the
calibration set for the gate — re-run it to confirm the rubric still classifies
each correctly after any change to the workflow or skill.
