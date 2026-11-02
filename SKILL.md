---
name: technical-impact-presentation
description: Generate a customer "Technical Impact Presentation" (TIP / POV / POV-summary deck) from a Dynatrace PowerPoint template plus an optional example deck and a success-criteria table, populated with LIVE tenant data pulled via dtctl, with deep-links to specific tenant views where screenshots should be pasted. Runs MANDATORY dtctl + Dynatrace MCP preflight validation, auto-detects dark vs light slide layouts to prevent invisible text, and finishes with a visibility/link/brand QA pass. Use when someone asks to build a "Technical Impact Presentation", "TIP deck", "POV summary", "technical impact review", or "impact deck for <customer>". Requires dtctl authenticated to the customer's Gen3 tenant and (recommended) the Dynatrace MCP server connected.
---

# Technical Impact Presentation (TIP) Builder

Builds a branded, customer-facing **Technical Impact Presentation** that maps a customer's
**success criteria** to what Dynatrace delivered, backed by **live tenant numbers** and
**deep-links to the exact views to screenshot**. Derives brand rules from the
[dynatrace-pptx-skill](../dynatrace-pptx-skill/SKILL.md) — read that first for colors/fonts.

> **Golden rule:** never fabricate metrics. Every number on a slide must come from a dtctl
> query run in this session. If a criterion is "In Process", say so — honesty beats polish.

## Inputs you need from the user

| Input | Required | Notes |
|-------|----------|-------|
| DT PowerPoint **template** (`.pptx`) | yes | The base deck; its layouts/theme are inherited. |
| **Example** filled deck (`.pptx`) | optional | Mirror its slide flow (e.g., a prior customer's POV). |
| **Success criteria** (image/table/text) | yes | The content spine — use case · purpose · how-done-today · status. |
| **Tenant** / dtctl context | yes | e.g. `<tenant-id>` → `dtctl --context <ctx>`. |
| Presenter name / date | optional | Defaults to the authed user + current month. |

## Pipeline (run in order)

### 1 — PREFLIGHT VALIDATION (mandatory, do not skip)
Both checks must pass before building. Run the dtctl check, then the MCP check.

**1a. dtctl validation** — run `scripts/preflight.sh <context>`:
```bash
bash scripts/preflight.sh <dtctl-context>
```
It verifies: current context, `auth whoami` (token not expired), read access (a trivial DQL),
write access (needed if you'll upload dashboards), and lists installed app IDs (needed for
deep-links). If the token is expired it prints the re-auth command — tell the user to run
`!dtctl auth login --context <ctx>` in-session (OAuth is interactive; you can't do it).

**1b. Dynatrace MCP validation** — *you* (the agent) must confirm the Dynatrace MCP server is
reachable, because scripts can't call MCP. Invoke one lightweight MCP read tool, e.g.
`get_dql_knowledgebase` or `list_strato_components` (names look like `mcp__<server>__<tool>`).
- Pass → note "MCP: connected" and use it to validate/author DQL and dashboards.
- Fail/absent → note "MCP: unavailable — proceeding dtctl-only" and continue (MCP is
  recommended, not required). Do **not** silently assume it works.

Record both results on a short preflight line before proceeding, e.g.
`Preflight ✓ dtctl(read+write, 47 apps) · MCP(connected)`.

### 2 — GATHER LIVE TENANT DATA
Run `scripts/gather_tenant_data.sh <context>` to pull the headline stats (hosts, services,
process groups/instances, K8s clusters/namespaces/workloads, spans/2h, logs/2h, distinct
problems/7d), the installed **app IDs** (for deep-links), and candidate **entity IDs** (top
services, host groups, DB systems) for premium links. Capture the output; you'll paste these
numbers into the config. Add any criterion-specific queries you need (e.g. `db.system`,
Oracle/MSSQL services, Azure regions, gen_ai spans).

### 3 — BUILD THE CONFIG
Copy `references/example_config.json` and edit it for this customer: cover, exec overview,
customer POV (4 cards), timeline, the success-criteria rows, one **feature** entry per
criterion (+ value-adds), value summary, closing. Each feature = `{title, done, status,
bullets[], url, capture}`. `url` = a real app deep-link (`<base>/<appId>` from step 1/2);
`capture` = one line telling the user exactly what to screenshot.

Deep-link base = `https://<tenant>.apps.dynatrace.com/ui/apps/`. Common app IDs (confirm per
tenant via step 1): `dynatrace.infraops`, `dynatrace.discovery.coverage`,
`dynatrace.classic.smartscape`, `dynatrace.services`, `dynatrace.distributedtracing`,
`dynatrace.database.overview`, `dynatrace.clouds`, `dynatrace.automations` (Workflows/ServiceNow),
`dynatrace.davis.problems` (Problems), `dynatrace.logs`, `dynatrace.kubernetes`,
`dynatrace.devobs.debugger` (Live Debugger), `dynatrace.dashboards`,
`dynatrace.security.vulnerabilities`.

### 4 — GENERATE THE DECK
```bash
python3 scripts/build_tip.py config.json
```
`build_tip.py` loads the template, deletes the skeleton slides **properly** (drops relationships
so there are no duplicate parts / corruption), rebuilds from the template layouts, and
**auto-detects per-layout whether the background is dark or light** — choosing white text on
dark cover/section slides and navy text on light content slides automatically. Custom cards,
timeline nodes, link-boxes and tables are always dark-filled with light text, so they read on
any slide.

### 5 — QA (mandatory)
```bash
python3 scripts/qa_tip.py "<output>.pptx"
```
Fails loudly on: white-on-light (invisible) text, broken/empty hyperlinks, leftover skeleton
text ("Use Case 1", "Customer Name", "Lorem"), empty tables. Fix and re-run until clean. If
LibreOffice/`soffice` is available, also export a PDF and eyeball it; if not, tell the user to
open the file and confirm text fit on dense slides.

### 6 — DELIVER
Give the absolute path + `file://` link. Offer to `open` it. Summarize the slide outline, the
metrics used, and the per-slide screenshot links.

## Deck blueprint (default flow)
Cover → Agenda → Executive Overview → Customer Point of View (4 cards) → POV Timeline →
Success-Criteria table → **section divider** → one feature slide per success criterion →
value-add slides (Problems/RCA, Logs, Kubernetes, Live Debugger, Dashboards delivered, Security)
→ **section divider** → Results scorecard → Value Delivered & Next Steps → Thank You.

Each feature slide: title + status chip (✅ Completed / 🔄 In Process) + 3–4 value bullets +
a teal "SCREENSHOT PLACEHOLDER" box on the right with the capture instruction and the clickable
deep-link.

## Hard-won lessons baked into the scripts (do not regress)
1. **Light vs dark layouts.** DT "Technical Impact" templates ship **light (white) content
   layouts** and **dark cover/section layouts** (full-bleed image). White text on a light slide
   is invisible. `build_tip.py` auto-detects (a full-bleed picture or dark solid fill ⇒ dark)
   and colors text accordingly. Never hard-code white text on content layouts.
2. **Delete slides properly.** Removing `sldId` entries alone orphans slide parts and causes
   duplicate-name zip corruption. Always `prs.part.drop_rel(rId)` **and** remove the `sldId`.
3. **Brand term swaps are case-sensitive.** e.g. replace visible **`Davis`** → **`Dynatrace
   Intelligence`** but leave lowercase `davis` inside app-ID URLs (`dynatrace.davis.problems`)
   intact, or you break the links. `qa_tip.py` won't flag URLs.
4. **Real app IDs only.** Pull them from `dtctl get apps` (step 1) — don't guess. `dynatrace.
   database.overview` (not `dynatrace.databases`), `dynatrace.davis.problems`, etc.
5. **Status honesty.** Keep the customer's Completed/In-Process flags; color In-Process amber.

## Sharing this skill
It's self-contained in this directory. To share: copy
`~/.claude/skills/technical-impact-presentation/` to a teammate's `~/.claude/skills/` (or
`~/.agents/skills/`), or commit it to a shared skills repo. No external dependencies beyond
`python-pptx` (`pip3 install python-pptx`) and `dtctl`.
