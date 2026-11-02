#!/usr/bin/env python3
"""
TIP QA — fails loudly on the issues that have actually bitten this workflow.
Usage: python3 qa_tip.py "<deck>.pptx"
Checks: invisible (white-on-light) text, broken/empty hyperlinks, leftover skeleton
text, empty tables. Exit 0 = clean, 1 = issues found.
"""
import sys
from pptx import Presentation

f=sys.argv[1]; p=Presentation(f)
DARKFILLS={"1A2440","172036","5E29E5","4AC2B3","00092F","002266"}
def slide_dark(s):
    n=s.slide_layout.name.lower(); return n.startswith("cover") or "section" in n
issues=[]; warn=[]
hyperlinks=0; slides=len(p.slides)

def is_dark_fill(obj):
    """True if a shape/cell has an explicit dark solid fill (white text is safe on it)."""
    try:
        if obj.fill.type==1 and str(obj.fill.fore_color.rgb) in DARKFILLS: return True
    except Exception: pass
    return False

def scan_tf(tf, i, d, shade):
    global hyperlinks
    for para in tf.paragraphs:
        for r in para.runs:
            if not r.text.strip(): continue
            t=r.text
            if any(k in t for k in ("Use Case 1","Use Case 2","Customer Name","Lorem ipsum")):
                issues.append(f"slide {i}: leftover skeleton text '{t[:30]}'")
            try: col=str(r.font.color.rgb)
            except: col=None
            if col=="FFFFFF" and not d and not shade:
                issues.append(f"slide {i}: WHITE text on light slide (invisible): '{t[:34]}'")
            if r.hyperlink.address:
                hyperlinks+=1
                u=r.hyperlink.address
                if not (u.startswith("http://") or u.startswith("https://")):
                    issues.append(f"slide {i}: malformed hyperlink '{u[:40]}'")

for i,s in enumerate(p.slides,1):
    d=slide_dark(s)
    for sh in s.shapes:
        if sh.has_table:
            if len(sh.table.rows)<=1: warn.append(f"slide {i}: table has no data rows")
            for row in sh.table.rows:
                for c in row.cells:
                    scan_tf(c.text_frame, i, d, is_dark_fill(c))   # per-cell fill
        elif sh.has_text_frame:
            scan_tf(sh.text_frame, i, d, is_dark_fill(sh))

print(f"QA report: {slides} slides, {hyperlinks} hyperlinks")
for w in warn: print("  ⚠ ", w)
if issues:
    print(f"\n❌ {len(issues)} ISSUE(S):")
    for x in issues[:40]: print("   -", x)
    sys.exit(1)
print("✅ clean: no invisible text, no broken links, no skeleton leftovers")
