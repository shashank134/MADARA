# Cyber Verification Program (CVP) — requirements & how to apply

Pulled from Anthropic's official support docs (Oct 2026). This is your
continuity path: it restores the offensive bug-bounty categories that Claude's
real-time cyber safeguards block by default on current models.

## What the safeguards block by default (no CVP)

On Opus 5 / 5.5, real-time cyber safeguards classify requests. On the **web**,
flagged requests are rerouted to an older model (Opus 4.8). On the **API**,
auto-switching is OFF by default — a flagged request returns HTTP 200 with
`stop_reason: "refusal"` and empty content unless you opt into fallback.

| Rerouted / blocked by default | Stays on Opus 5 / 5.5 |
|---|---|
| Exploit generation | Secure coding |
| Binary-based vulnerability scanning | Source-code vulnerability review |
| Penetration testing | Security issue triage |

## What CVP unlocks

Removes the blocks on **"High-Risk Dual-Use"** activities for vetted parties:
vulnerability exploitation research, offensive security tooling, penetration
testing, exploitability analysis, authorized red teaming.

## What stays blocked for EVERYONE (CVP cannot lift)

"Prohibited use" — mass data exfiltration, ransomware development, and other
activity almost always used maliciously.

## Eligibility

- **Models:** Opus and Sonnet. **NOT** Opus 5.5 / Sonnet 5.5 / Mythos (not in
  CVP yet). Today CVP effectively gets you **Opus 5** with reduced cyber
  restrictions — wire that as the `fallback` role in config/model.yaml.
- **Who applies:** only an **authorized admin** of the organization can submit;
  the option is visible only to admins.
- **Scope:** approval is **organization-specific** and does **not** transfer
  between workspaces. Approve your org, then work in that org's workspace / use
  that org's API key. A personal workspace will still hit blocks.
- **ZDR:** organizations on **Zero Data Retention are ineligible**. CVP requires
  data retention enabled. (Sales-managed ZDR: contact your Anthropic rep.)
- **Platforms:** Claude.ai, Claude Code, Anthropic API, BYOK, Claude on AWS,
  Claude on Google Cloud, Microsoft Foundry. **NOT Amazon Bedrock.**

## How to apply

1. Go to the Verification Portal: **portal.anthropic.com/programs/cvp**
   (first-party: Claude.ai / API / Claude Code; and BYOK).
   - Microsoft Foundry: Cyber Use Case Form, select "Azure" surface; needs Azure
     Tenant ID + Subscription ID.
   - Claude on AWS: Verification Portal with AWS account linking.
   - Claude on Google Cloud: Verification Portal with Google account linking +
     data-retention configuration.
2. Complete **identity verification** (mandatory for all applications).
3. Describe your security work and intended dual-use use cases.
4. Submit. Decision by email, target **within 2 business days**.

## If legitimate work is wrongly blocked

Use Anthropic's **cyber-block false-positive report form** to appeal a wrongful
block or a denied application.

## The solo-hunter catch (read this)

CVP is org-scoped and admin-submitted. As an individual bug-bounty hunter you
have two realistic routes:
1. Register a security entity / org, enable data retention (not ZDR), and apply
   as that org's admin — then do your hunting in that org's workspace.
2. If you hunt under an existing employer/team org, have its admin apply and add
   your use cases.

A purely personal consumer workspace is the one place CVP won't help.

## Sources
- https://support.claude.com/articles/14604842-real-time-cyber-safeguards-on-claude
- https://support.claude.com/en/articles/16049681-why-claude-switched-models-in-your-conversation-with-opus-5-or-opus-5-5
