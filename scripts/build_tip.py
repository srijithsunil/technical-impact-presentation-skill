#!/usr/bin/env python3
"""
Technical Impact Presentation builder — config-driven, brand-safe.
Usage:  python3 build_tip.py config.json
Bakes in the hard-won lessons: proper slide deletion, and AUTO dark/light text color
per layout so content is never white-on-white.
Requires: pip3 install python-pptx
"""
import sys, json
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
import re

cfg = json.load(open(sys.argv[1]))
prs = Presentation(cfg["template"])

# ---- palette ----
NAVY=RGBColor(0x1A,0x24,0x40); WHITE=RGBColor(0xFF,0xFF,0xFF); TEAL=RGBColor(0x4A,0xC2,0xB3)
GREY=RGBColor(0x6F,0x74,0x7F); LINK=RGBColor(0x3B,0xAC,0xF0); CARD=RGBColor(0x17,0x20,0x36)
PURPLE=RGBColor(0x5E,0x29,0xE5)
INK=RGBColor(0x1A,0x24,0x40); DTEAL=RGBColor(0x1E,0x7D,0x6B); DAMBER=RGBColor(0xB5,0x65,0x1D)

# ---- delete skeleton slides PROPERLY (drop rels so no duplicate parts) ----
sl = prs.slides._sldIdLst
for sid in list(sl):
    prs.part.drop_rel(sid.get(qn('r:id'))); sl.remove(sid)

# ---- layout darkness auto-detection (full-bleed picture or dark solid fill => dark) ----
def layout_is_dark(lay):
    xml = lay.element.xml
    # full-bleed picture in layout
    for sh in lay.shapes:
        try:
            w=Emu(sh.width).inches; h=Emu(sh.height).inches
        except: w=h=0
        if w>8 and h>5 and 'blipFill' in sh.element.xml: return True
    # dark solid background
    m = re.findall(r'<p:bg>.*?srgbClr val="([0-9A-Fa-f]{6})"', xml, re.S)
    if m:
        r,g,b=int(m[0][:2],16),int(m[0][2:4],16),int(m[0][4:],16)
        if (r*0.299+g*0.587+b*0.114) < 110: return True
    return False

L = {l.name: i for i,l in enumerate(prs.slide_layouts)}
DARK = {name: layout_is_dark(prs.slide_layouts[i]) for name,i in L.items()}
def pick(*names):   # first layout name that exists
    for n in names:
        if n in L: return n
    raise SystemExit(f"template missing any of layouts: {names}")

NAME_COVER   = pick("Cover slide 1 presenter","Cover slide","Cover slide 2 presenters")
NAME_SECTION = pick("Section title slide")
NAME_STD     = pick("Standard slide","Dark: standard slide")
NAME_PHOTO   = pick("Standard slide with photo","Dark: standard slide with photo")
NAME_TITLE   = pick("Title Only ","Title Only","Header no line")

def add(name): return prs.slides.add_slide(prs.slide_layouts[L[name]])
def ph(s, idx):
    for p in s.placeholders:
        if p.placeholder_format.idx==idx: return p
def dark(s): return DARK.get(s.slide_layout.name, False)
# semantic colors that adapt to slide darkness
def c_title(s):  return WHITE if dark(s) else INK
def c_body(s):   return WHITE if dark(s) else INK
def c_head(s):   return TEAL  if dark(s) else DTEAL
def c_done(s):   return TEAL  if dark(s) else DTEAL
def c_prog(s):   return RGBColor(0xFF,0xB0,0x20) if dark(s) else DAMBER

def run(p, text, size, color, bold=False, url=None):
    r=p.add_run(); r.text=text; r.font.size=Pt(size); r.font.bold=bold; r.font.color.rgb=color
    if url: r.hyperlink.address=url
    return r
def set_title(s, text, size=24):
    t=ph(s,0); t.text_frame.clear(); run(t.text_frame.paragraphs[0], text, size, c_title(s), True)
def put_bullets(s, idx, items, size=14):
    tf=ph(s,idx).text_frame; tf.clear(); tf.word_wrap=True
    for i,(txt,lvl,role,bold) in enumerate(items):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph(); p.level=lvl; p.space_after=Pt(6)
        col = c_head(s) if role=="head" else (c_done(s) if role=="done" else (c_prog(s) if role=="prog" else c_body(s)))
        run(p, txt, size-(1 if lvl else 0), col, bold or role in("head","done","prog"))

def textbox(s,x,y,w,h):
    tb=s.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h)); tb.text_frame.word_wrap=True; return tb
def para(tf,text,size,color,bold=False,align=PP_ALIGN.LEFT,first=False,url=None,space=4):
    p=tf.paragraphs[0] if first else tf.add_paragraph(); p.alignment=align; p.space_after=Pt(space)
    run(p,text,size,color,bold,url); return p
def card(s,x,y,w,h,fill,line=None):
    sh=s.shapes.add_shape(1,Inches(x),Inches(y),Inches(w),Inches(h))
    sh.fill.solid(); sh.fill.fore_color.rgb=fill
    if line: sh.line.color.rgb=line; sh.line.width=Pt(1)
    else: sh.line.fill.background()
    sh.text_frame.word_wrap=True; return sh

def linkbox(s,url,capture,x=5.95,y=2.7,w=6.9,h=1.9):
    sh=card(s,x,y,w,h,CARD,TEAL); tf=sh.text_frame; tf.vertical_anchor=MSO_ANCHOR.MIDDLE
    tf.margin_left=Inches(0.2); tf.margin_right=Inches(0.2)
    para(tf,"\U0001F4F8  SCREENSHOT PLACEHOLDER",13,TEAL,True,first=True,space=3)
    para(tf,"Capture: "+capture,12,WHITE,space=6)
    para(tf,"\U0001F517  Open this view in Dynatrace →",12,LINK,True,url=url,space=1)
    para(tf,url,8.5,GREY,url=url)

# ===== COVER =====
cov=add(NAME_COVER); c=cfg["cover"]
set_title(cov, c["title"], 40)
if ph(cov,1):
    sub=ph(cov,1); sub.text_frame.clear(); run(sub.text_frame.paragraphs[0], c.get("subtitle",""),20, (TEAL if dark(cov) else PURPLE))
if ph(cov,13) and c.get("presenter"): ph(cov,13).text_frame.text=c["presenter"]
if ph(cov,14) and c.get("date"): ph(cov,14).text_frame.text=c["date"]

# ===== AGENDA =====
if cfg.get("agenda"):
    a=add(NAME_STD); set_title(a,"Agenda")
    put_bullets(a,23,[(t,0,"body",False) for t in cfg["agenda"]],18)

# ===== EXEC OVERVIEW =====
if cfg.get("exec_overview"):
    e=add(NAME_STD); set_title(e,"Executive Overview")
    put_bullets(e,23,[(t,lvl,role,False) for (t,lvl,role) in cfg["exec_overview"]],14)

# ===== CUSTOMER POV (4 cards) =====
if cfg.get("customer_pov"):
    s=add(NAME_TITLE); set_title(s,"Customer Point of View")
    cw=2.95; gap=0.13; x0=0.5; y0=1.6
    for i,(h,b) in enumerate(cfg["customer_pov"][:4]):
        x=x0+i*(cw+gap)
        hb=card(s,x,y0,cw,0.55,TEAL); hb.text_frame.vertical_anchor=MSO_ANCHOR.MIDDLE
        para(hb.text_frame,h,15,NAVY,True,PP_ALIGN.CENTER,first=True)
        bb=card(s,x,y0+0.55,cw,3.9,CARD,TEAL); bb.text_frame.margin_left=Inches(0.12); bb.text_frame.margin_right=Inches(0.12); bb.text_frame.margin_top=Inches(0.12)
        para(bb.text_frame,b,13,WHITE,first=True)

# ===== TIMELINE =====
if cfg.get("timeline"):
    s=add(NAME_TITLE); set_title(s,"POV Timeline & Scope")
    ph_=cfg["timeline"]; n=len(ph_); cw=min(2.3,(12.3-(n-1)*0.2)/n); gap=0.2; x0=0.5
    sp=card(s,0.5,2.45,12.3,0.04,TEAL)
    for i,row in enumerate(ph_):
        wk,ti,de=(row+["",""])[:3]; x=x0+i*(cw+gap)
        nd=s.shapes.add_shape(9,Inches(x+cw/2-0.12),Inches(2.33),Inches(0.26),Inches(0.26)); nd.fill.solid(); nd.fill.fore_color.rgb=TEAL; nd.line.fill.background()
        bx=card(s,x,2.9,cw,2.2,CARD,TEAL)
        para(bx.text_frame,wk,13,TEAL,True,PP_ALIGN.CENTER,first=True,space=2)
        para(bx.text_frame,ti,14,WHITE,True,PP_ALIGN.CENTER,space=4)
        para(bx.text_frame,de,11,GREY,align=PP_ALIGN.CENTER)

# ===== SUCCESS CRITERIA / RESULTS TABLE =====
def criteria_table(title, rows):
    s=add(NAME_STD); set_title(s,title)
    t=s.shapes.add_table(len(rows)+1,3,Inches(0.5),Inches(1.5),Inches(12.3),Inches(5.3)).table
    t.columns[0].width=Inches(3.2); t.columns[1].width=Inches(7.0); t.columns[2].width=Inches(2.1)
    for j,h in enumerate(["Use Case / Feature","Purpose","Status"]):
        cell=t.cell(0,j); cell.fill.solid(); cell.fill.fore_color.rgb=PURPLE
        cell.text=h; r=cell.text_frame.paragraphs[0].runs[0]; r.font.size=Pt(12); r.font.bold=True; r.font.color.rgb=WHITE
    for i,(uc,pu,st,done) in enumerate(rows,1):
        for j,val in enumerate([uc,pu,st]):
            cell=t.cell(i,j); cell.fill.solid(); cell.fill.fore_color.rgb=(NAVY if i%2 else CARD)
            cell.text=str(val); r=cell.text_frame.paragraphs[0].runs[0]; r.font.size=Pt(10.5); r.font.color.rgb=WHITE
            if j==0: r.font.bold=True
            if j==2: r.font.bold=True; r.font.color.rgb=(TEAL if done else RGBColor(0xFF,0xB0,0x20))
    return s
if cfg.get("success_criteria"):
    criteria_table(cfg.get("sc_title","Dynatrace Platform POV — Scope & Success Criteria"), cfg["success_criteria"])

# ===== SECTION DIVIDER =====
def section(title, subtitle=""):
    s=add(NAME_SECTION); t=ph(s,0); t.text_frame.clear(); run(t.text_frame.paragraphs[0],title,32,(WHITE if dark(s) else INK),True)
    if subtitle and ph(s,1):
        sub=ph(s,1); sub.text_frame.clear(); run(sub.text_frame.paragraphs[0],subtitle,18,(TEAL if dark(s) else PURPLE))
    return s
section("Dynatrace in Action","Use cases mapped to the customer's success criteria")

# ===== FEATURE SLIDES =====
for f in cfg.get("features",[]):
    s=add(NAME_PHOTO); set_title(s,f["title"],22)
    done=f.get("done",True); stxt=("✅ " if done else "\U0001F504 ")+f.get("status","")
    items=[(stxt,0,"done" if done else "prog",True)]+[(b,0,"body",False) for b in f.get("bullets",[])]
    put_bullets(s,23,items,13)
    linkbox(s,f["url"],f.get("capture","the relevant view"))

# ===== RESULTS =====
section("POV Results")
if cfg.get("success_criteria"):
    criteria_table("Dynatrace Platform POV — Results Scorecard", cfg["success_criteria"])
if cfg.get("value_summary"):
    s=add(NAME_STD); set_title(s,"Value Delivered & Next Steps")
    put_bullets(s,23,[(t,lvl,role,False) for (t,lvl,role) in cfg["value_summary"]],13)

# ===== CLOSING =====
cl=cfg.get("closing",{"title":"Thank You","subtitle":""})
s=add(NAME_SECTION); t=ph(s,0); t.text_frame.clear(); run(t.text_frame.paragraphs[0],cl.get("title","Thank You"),40,(WHITE if dark(s) else INK),True)
if cl.get("subtitle") and ph(s,1):
    sub=ph(s,1); sub.text_frame.clear(); run(sub.text_frame.paragraphs[0],cl["subtitle"],18,(TEAL if dark(s) else PURPLE))

prs.save(cfg["output"])
print("SAVED:", cfg["output"], "| slides:", len(prs.slides._sldIdLst),
      "| dark layouts:", [n for n,d in DARK.items() if d][:6])
