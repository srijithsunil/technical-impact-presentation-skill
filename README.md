# Technical Impact Presentation (TIP) Skill

A Claude Code / Claude Agent **skill** that builds a branded, customer-facing **Technical
Impact Presentation** (a.k.a. POV summary / technical impact review) for a Dynatrace Proof of
Value — from a PowerPoint template + an optional example deck + the customer's **success
criteria**, populated with **live tenant data** pulled via `dtctl`, and finished with
**deep-links to the exact tenant views** where screenshots should be pasted.

It runs **mandatory dtctl + Dynatrace MCP preflight validation**, auto-detects dark vs light
slide layouts (so text is never invisible), and gates delivery on a visibility/link QA pass.

## Quickstart (teammates)

### 1. Install
Drop this folder into your skills directory:
```bash
cp -R technical-impact-presentation ~/.claude/skills/
#  (or ~/.agents/skills/ )
pip3 install python-pptx          # only hard dependency
```
Claude Code auto-discovers it. Confirm with `/` → look for `technical-impact-presentation`.

### 2. Prerequisites
- **dtctl** authenticated to the customer's Gen3 tenant: `dtctl auth login --context <ctx>`
- **Dynatrace MCP server** connected (recommended, not required)
- A DT **PowerPoint template** (`[TEMPLATE] - Technical Impact Presentation.pptx` or similar)
- The customer's **success criteria** (screenshot, table, or text)

### 3. Run it
Easiest — just ask Claude:
> "Build a Technical Impact Presentation for \<customer\> using this template and success criteria."

Claude will walk the pipeline. Or run the pieces yourself:
```bash
cd ~/.claude/skills/technical-impact-presentation
bash scripts/preflight.sh <dtctl-context>          # 1. validate dtctl (+ validate MCP in chat)
bash scripts/gather_tenant_data.sh <dtctl-context> # 2. pull live stats, app IDs, entity IDs
cp references/example_config.json my_config.json   # 3. edit for your customer
python3 scripts/build_tip.py my_config.json        # 4. generate the deck
python3 scripts/qa_tip.py "<output>.pptx"          # 5. QA gate (must pass)
```

## The pipeline
1. **Preflight (mandatory):** `preflight.sh` validates dtctl context/token/read access/app
   registry; the agent validates the Dynatrace MCP server by calling a lightweight read tool.
2. **Gather:** `gather_tenant_data.sh` pulls headline stats, app IDs (for deep-links) and
   candidate entity IDs. **Never fabricate numbers** — every figure must come from here.
3. **Config:** edit `references/example_config.json` (cover, exec overview, 4-card customer
   POV, timeline, success-criteria rows, one feature per criterion + value-adds, next steps).
4. **Build:** `build_tip.py` — config-driven, auto dark/light text, safe slide deletion.
5. **QA:** `qa_tip.py` fails on invisible text, broken links, or leftover skeleton slides.
6. **Deliver:** path + `file://` link + per-slide screenshot deep-links.

## Why the QA matters (lessons baked in)
- DT "Technical Impact" templates ship **light content layouts** + **dark cover/section
  layouts**. White text on a light slide is invisible — the builder auto-colors per layout.
- Deleting slides naively corrupts the file; the builder drops relationships correctly.
- Brand term swaps are case-sensitive (e.g. `Davis` → `Dynatrace Intelligence`) and must not
  touch lowercase `davis` inside app-ID URLs.
- Use **real** app IDs from `dtctl get apps`, never guessed ones.

## Files
| File | Purpose |
|------|---------|
| `SKILL.md` | Full workflow, validation steps, rules (what Claude reads) |
| `scripts/preflight.sh` | dtctl readiness validation |
| `scripts/gather_tenant_data.sh` | Live tenant stats + app/entity IDs |
| `scripts/build_tip.py` | Config-driven deck builder |
| `scripts/qa_tip.py` | Visibility / link / skeleton QA gate |
| `references/example_config.json` | Generic worked example to copy & edit |

## License / sharing
Internal enablement asset. Contains **no customer data** — populate per engagement from live
`dtctl` output. Safe to share across the SE org.
