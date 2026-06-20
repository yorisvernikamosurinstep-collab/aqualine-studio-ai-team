import streamlit as st
import requests
import json
import os
import csv
from datetime import datetime
from io import StringIO

import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ui_settings import inject_global_font_css

st.set_page_config(page_title="Report Generator — AQUALINE", layout="wide", initial_sidebar_state="expanded")

# 🔐 กันเข้าหน้านี้ตรงผ่าน URL โดยไม่ผ่านด่านล็อกอินที่หน้าแรก
from auth_guard import require_auth
require_auth()

# 🧭 PAGE-VISIT MARKER — ใช้โดยหน้า "งานบริษัทอาควาไลน์" เพื่อรู้ว่าผู้ใช้เปิดหน้าใหม่จริง
st.session_state["_active_page"] = __file__

# ฟอนต์/ขนาดตัวอักษรที่ผู้ใช้กำหนดเอง (หน้า Design UX/UI) — ใช้ร่วมกันทุกหน้า
st.markdown(inject_global_font_css(), unsafe_allow_html=True)

if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("🔑 ไม่พบ GOOGLE_API_KEY ใน secrets.toml"); st.stop()

# อัตราแลกเปลี่ยน USD→THB — ดึงจาก secrets.toml เดียวกับ ai_team.py (single source of truth)
USD_TO_THB = float(st.secrets.get("USD_TO_THB", "35.0"))

ANALYTICS_FILE = "analytics_data.json"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=IBM+Plex+Sans+Thai:wght@300;400;600;700&display=swap');
*,*::before,*::after{box-sizing:border-box;}
.stApp{background:#070b12;color:#cbd5e1;font-family:'IBM Plex Sans Thai',sans-serif;}
[data-testid="stSidebar"]{background:#0d1117!important;border-right:1px solid #1e293b!important;}
.page-header{background:linear-gradient(90deg,#0d1117,#0f172a,#0d1117);border-bottom:1px solid #1e293b;
  padding:20px 28px;display:flex;align-items:center;gap:16px;margin-bottom:24px;}
.page-title{font-family:'IBM Plex Mono',monospace;font-size:20px;font-weight:700;color:#f1f5f9;}
.page-sub{font-size:11px;color:#475569;font-family:'IBM Plex Mono',monospace;margin-top:3px;}
.section-title{font-family:'IBM Plex Mono',monospace;font-size:13px;font-weight:700;color:#94a3b8;
  letter-spacing:1px;text-transform:uppercase;margin:20px 0 12px;padding-bottom:6px;border-bottom:1px solid #1e293b;}
.tpl-card{background:rgba(15,23,42,.8);border:1px solid #1e293b;border-radius:10px;padding:14px;margin-bottom:8px;transition:border-color .2s;}
.tpl-card:hover{border-color:#38bdf8;}
.tpl-title{font-size:13px;font-weight:700;color:#e2e8f0;margin-bottom:3px;}
.tpl-desc{font-size:11px;color:#475569;}
.stat-pill{display:inline-flex;align-items:center;gap:6px;background:rgba(15,23,42,.8);
  border:1px solid #1e293b;border-radius:20px;padding:4px 12px;font-size:11px;margin:3px;}
</style>
""", unsafe_allow_html=True)

# ─── Data helpers ───
def load_analytics():
    if os.path.exists(ANALYTICS_FILE):
        try:
            with open(ANALYTICS_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return {"sessions": [], "agent_usage": {}, "project_count": {}, "weekly": {}}

@st.cache_data(ttl=60, show_spinner=False)
def get_model(k):
    try:
        r = requests.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={k}", timeout=8)
        if r.status_code == 200:
            avail = [m["name"] for m in r.json().get("models",[]) if "generateContent" in m.get("supportedGenerationMethods",[])]
            for p in ["models/gemini-2.5-flash-preview-05-20","models/gemini-2.5-flash","models/gemini-1.5-flash-latest","models/gemini-1.5-flash"]:
                if p in avail: return p
    except: pass
    return "models/gemini-1.5-flash"

def call_gemini(prompt, max_tokens=4096):
    model = get_model(API_KEY)
    try:
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={API_KEY}",
            json={"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"temperature":0.6,"maxOutputTokens":max_tokens}},
            timeout=120)
        if resp.status_code == 200:
            return resp.json()["candidates"][0]["content"]["parts"][0].get("text","")
        return f"❌ API Error {resp.status_code}"
    except Exception as e:
        return f"❌ {str(e)[:100]}"

# AGENT_NAMES ดึงจาก AGENT_META (agent_default_personas.py) — single source of truth
# เพิ่ม/แก้ agent ที่ AGENT_META ที่เดียว หน้านี้จะเห็นผลตามอัตโนมัติ (รวม A26)
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent_default_personas import AGENT_META

AGENT_NAMES = {aid: m["name"] for aid, m in AGENT_META.items()}

# ─── Session state ───
for k, v in [("rg_type","📊 Project Summary"), ("rg_report",""), ("rg_ts",""), ("rg_saved",[]), ("rg_show_raw",False)]:
    if k not in st.session_state: st.session_state[k] = v

# ─── Sidebar ───
with st.sidebar:
    st.markdown("<style>[data-testid='stSidebarNav']{display:none}</style>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center;padding:14px 0 8px'><div style='font-family:IBM Plex Mono,monospace;font-size:13px;font-weight:700;color:#f1f5f9'>AQUALINE</div><div style='font-size:10px;color:#334155;font-family:IBM Plex Mono,monospace'>AI LIVE CHAT</div></div>", unsafe_allow_html=True)
    st.markdown("---")
    st.page_link("ai_team.py",                          label="🤖 AI Special Team")
    st.page_link("pages/1_งานบริษัทอาควาไลน์.py",        label="🏢 งานบริษัทอาควาไลน์")
    st.page_link("pages/2_คุยกับ_AI_Agent.py",           label="💬 คุยกับ AI Agent")
    st.page_link("pages/3_Live_Chat.py",                label="💬 Live Chat")
    st.page_link("pages/4_สร้าง_Brief_ด่วน.py",          label="📝 สร้าง Brief ด่วน")
    st.page_link("pages/5_Workflow_Builder.py",         label="🏭 Content Factory")
    st.page_link("pages/6_ประวัติการประชุม.py",          label="🕐 ประวัติการประชุม")
    st.page_link("pages/7_สถิติการใช้งาน.py",            label="📈 สถิติการใช้งาน")
    st.page_link("pages/8_แฟ้มงาน.py",                   label="📁 แฟ้มงาน")
    st.page_link("pages/9_คลัง_Prompt.py",               label="📚 คลัง Prompt")
    st.page_link("pages/10_Dashboard.py",               label="📊 Dashboard")
    st.page_link("pages/11_Budget_Cost_Manager.py",     label="💰 Budget & Cost")
    st.page_link("pages/12_Report_Generator.py",        label="📄 Report Generator")
    st.page_link("pages/13_Agent_Persona_Editor.py",    label="🧬 Agent Persona Editor")
    st.page_link("pages/14_Settings_Config.py",         label="⚙️ Settings & Config")
    st.page_link("pages/15_KONEX.py",                   label="🧠 KONEX")
    st.page_link("pages/16_Design_UX_UI.py",            label="🎨 Design UX/UI")

# ─── Header ───
st.markdown("""
<div class="page-header">
  <div style='font-size:36px'>📄</div>
  <div>
    <div class="page-title">REPORT GENERATOR</div>
    <div class="page-sub">สร้างรายงาน Meeting Log · Project Summary · Export PDF/HTML/MD/JSON</div>
  </div>
</div>""", unsafe_allow_html=True)

# ─── Load data ───
analytics   = load_analytics()
sessions    = analytics.get("sessions", [])
agent_usage = analytics.get("agent_usage", {})

# ══════════════════════════════════════════════════════════════════
# REPORT TYPE
# ══════════════════════════════════════════════════════════════════
REPORT_TYPES = {
    "📊 Project Summary":        "สรุปภาพรวม Project, Sessions, Agent, Cost, KPI",
    "📝 Meeting Log Report":     "รวม Meeting Log จาก Sessions ทุกอันของ Project",
    "🤖 Agent Performance":      "วิเคราะห์ Agent แต่ละตัว: ใช้บ่อยแค่ไหน, ทำงานอะไร",
    "💰 Cost & Budget Report":   "Breakdown ค่าใช้จ่าย AI ตาม Project/Agent/Model",
    "📈 Weekly Progress":        "สรุปความคืบหน้า และแผนสัปดาห์หน้า",
    "✍️ Custom Report":          "กำหนด Prompt เองให้ AI เขียนรายงาน",
}

st.markdown("<div class='section-title'>📋 เลือกประเภทรายงาน</div>", unsafe_allow_html=True)
cols_t = st.columns(3)
for i, (rtype, rdesc) in enumerate(REPORT_TYPES.items()):
    with cols_t[i % 3]:
        is_sel = st.session_state.rg_type == rtype
        st.markdown(f"""<div class="tpl-card" style='{"border-color:#38bdf8;background:rgba(56,189,248,.05)" if is_sel else ""}'>
<div class="tpl-title">{"✅ " if is_sel else ""}{rtype}</div>
<div class="tpl-desc">{rdesc}</div></div>""", unsafe_allow_html=True)
        if st.button("เลือก", key=f"rt_{i}", use_container_width=True):
            st.session_state.rg_type = rtype; st.rerun()

st.markdown("---")

# ══════════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════════
col_cfg, col_data = st.columns([1.5, 1])

with col_cfg:
    st.markdown("<div class='section-title'>⚙️ ตั้งค่า</div>", unsafe_allow_html=True)
    all_projects = sorted(set(s.get("project","") for s in sessions if s.get("project","")))
    sel_projects  = st.multiselect("📂 Project:", all_projects,
                                    default=all_projects[:min(3,len(all_projects))], key="rg_projs")
    lang   = st.selectbox("🌐 ภาษา:", ["ภาษาไทย","English","Bilingual"], key="rg_lang")
    detail = st.select_slider("📏 ความละเอียด:", ["กระชับ","ปานกลาง","ละเอียด"], value="ปานกลาง", key="rg_detail")
    inc_cost   = st.checkbox("💰 รวมค่าใช้จ่าย", value=True, key="rg_inc_cost")
    inc_agents = st.checkbox("🤖 รวมรายการ Agent", value=True, key="rg_inc_agents")
    inc_log    = st.checkbox("📝 รวม Meeting Log", value=True, key="rg_inc_log")
    if "Custom" in st.session_state.rg_type:
        custom_p = st.text_area("✍️ Custom Prompt:", height=100, key="rg_custom_p",
                                 placeholder="สรุปผลงานทีม AQUALINE เดือนนี้ พร้อม KPI...")

with col_data:
    st.markdown("<div class='section-title'>📊 ข้อมูลที่จะรวม</div>", unsafe_allow_html=True)
    filt_s = [s for s in sessions if s.get("project","") in sel_projects] if sel_projects else sessions
    total_tok  = sum(s.get("tokens",0) for s in filt_s)
    total_cost = sum(s.get("cost_usd",0) for s in filt_s)
    all_a_used = set(a for s in filt_s for a in s.get("agents_used",[]))
    for lbl, val, color in [
        ("📁 Sessions", str(len(filt_s)), "#38bdf8"),
        ("🤖 Agents", str(len(all_a_used)), "#a78bfa"),
        ("⚡ Tokens", f"{total_tok:,}", "#34d399"),
        ("💰 Cost", f"${total_cost:.4f}", "#fbbf24"),
    ]:
        st.markdown(f"<span class='stat-pill'><span style='color:{color}'>{lbl}</span><b style='color:{color}'>{val}</b></span>", unsafe_allow_html=True)

    if not all_projects:
        st.warning("ยังไม่มีข้อมูล — รันงานจากหน้าหลักก่อนครับ")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════
# GENERATE
# ══════════════════════════════════════════════════════════════════
if st.button("🚀 Generate Report ด้วย AI", use_container_width=True, type="primary"):
    # Build context
    ctx = [f"# AQUALINE STUDIO Data\nวันที่: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n",
           f"Sessions: {len(filt_s)} | Tokens: {total_tok:,} | Cost: ${total_cost:.4f} (฿{total_cost*USD_TO_THB:.2f})\n\n"]
    if inc_agents and all_a_used:
        ctx.append("## Agent Usage:\n")
        ac = {}
        for s in filt_s:
            for a in s.get("agents_used",[]): ac[a] = ac.get(a,0)+1
        for aid, cnt in sorted(ac.items(), key=lambda x: x[1], reverse=True):
            ctx.append(f"- {aid} {AGENT_NAMES.get(aid,'')}: {cnt} ครั้ง\n")
        ctx.append("\n")
    if inc_cost:
        ctx.append("## Cost by Project:\n")
        pc = {}
        for s in filt_s: pc[s.get("project","?")] = pc.get(s.get("project","?"),0)+s.get("cost_usd",0)
        for p,c in sorted(pc.items(), key=lambda x:x[1], reverse=True):
            ctx.append(f"- {p}: ${c:.4f} (฿{c*USD_TO_THB:.2f})\n")
        ctx.append("\n")
    if inc_log:
        ctx.append("## Meeting Logs:\n")
        for s in filt_s[:10]:
            if s.get("log"):
                ctx.append(f"### {s.get('project','?')} ({s.get('timestamp','')[:16]})\n{s['log'][:1500]}\n\n")
    ctx.append("## Sessions:\n")
    for s in filt_s[:25]:
        ctx.append(f"- {s.get('project','?')} | {s.get('timestamp','')[:16]} | {s.get('tokens',0):,}tok | {', '.join(s.get('agents_used',[]))}\n")

    detail_map = {"กระชับ":"300-500 คำ","ปานกลาง":"500-1000 คำ","ละเอียด":"1000-2000 คำ"}
    lang_map   = {"ภาษาไทย":"ตอบเป็นภาษาไทย","English":"Answer in English","Bilingual":"ตอบทั้งไทยและอังกฤษ"}
    task_map   = {
        "📊 Project Summary":    "สรุปภาพรวมทุก Project พร้อม KPI, ความสำเร็จ, Recommendation",
        "📝 Meeting Log Report": "รวม Meeting Log ทุก Session เป็น Report อย่างเป็นทางการ พร้อม Key Decisions และ Action Items",
        "🤖 Agent Performance":  "วิเคราะห์ประสิทธิภาพแต่ละ Agent ให้คะแนน และ Recommendation",
        "💰 Cost & Budget Report":"สร้าง Cost Report ละเอียด พร้อม Breakdown และคำแนะนำลดต้นทุน",
        "📈 Weekly Progress":    "สร้าง Weekly Progress Report สรุปสิ่งที่ทำ และแผนหน้า",
    }
    if "Custom" in st.session_state.rg_type:
        task = st.session_state.get("rg_custom_p","สรุปภาพรวม")
    else:
        task = task_map.get(st.session_state.rg_type, "สรุปภาพรวม")

    prompt = "".join(ctx) + f"\n---\nสร้าง {st.session_state.rg_type} สำหรับ AQUALINE STUDIO\nงาน: {task}\nความละเอียด: {detail_map[detail]}\nภาษา: {lang_map[lang]}\nใช้ Markdown formatting ให้สวยงาม"
    with st.spinner("🔄 AI กำลังสร้างรายงาน..."):
        result = call_gemini(prompt, max_tokens=4096)
    st.session_state.rg_report = result
    st.session_state.rg_ts     = datetime.now().strftime("%d/%m/%Y %H:%M")
    st.success("✅ สร้างรายงานเรียบร้อย!")
    st.rerun()

# ══════════════════════════════════════════════════════════════════
# DISPLAY + EXPORT
# ══════════════════════════════════════════════════════════════════
if st.session_state.rg_report:
    rpt  = st.session_state.rg_report
    rts  = st.session_state.rg_ts
    rtyp = st.session_state.rg_type

    st.markdown(f"""
    <div style='background:rgba(15,23,42,.9);border:1px solid rgba(56,189,248,.2);border-radius:12px;padding:20px;margin-bottom:16px'>
      <div style='display:flex;justify-content:space-between;margin-bottom:12px'>
        <div style='font-family:IBM Plex Mono,monospace;font-size:11px;color:#38bdf8'>📄 {rtyp}</div>
        <div style='font-size:10px;color:#475569'>{rts}</div>
      </div>""", unsafe_allow_html=True)
    st.markdown(rpt)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── Export buttons ──
    st.markdown("<div class='section-title'>📥 Export รายงาน</div>", unsafe_allow_html=True)
    ts_fn = datetime.now().strftime("%Y%m%d_%H%M")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.download_button("📄 TXT", data=rpt.encode("utf-8"),
            file_name=f"report_{ts_fn}.txt", mime="text/plain", use_container_width=True, key="dl_txt")
    with c2:
        md = f"# {rtyp}\nสร้างเมื่อ: {rts}\n\n---\n\n{rpt}"
        st.download_button("📝 Markdown", data=md.encode("utf-8"),
            file_name=f"report_{ts_fn}.md", mime="text/markdown", use_container_width=True, key="dl_md")
    with c3:
        jrpt = json.dumps({"report_type":rtyp,"generated_at":rts,"sessions":len(filt_s),
                            "tokens":total_tok,"cost_usd":round(total_cost,6),"cost_thb":round(total_cost*USD_TO_THB,2),
                            "report":rpt}, ensure_ascii=False, indent=2)
        st.download_button("📦 JSON", data=jrpt.encode("utf-8"),
            file_name=f"report_{ts_fn}.json", mime="application/json", use_container_width=True, key="dl_json")
    with c4:
        html = f"""<!DOCTYPE html><html lang="th"><head><meta charset="UTF-8">
<title>{rtyp}</title>
<style>body{{font-family:Sarabun,sans-serif;max-width:900px;margin:40px auto;padding:0 24px;color:#1a1a2e;line-height:1.8}}
h1{{color:#1e3a5f;border-bottom:3px solid #38bdf8;padding-bottom:8px}}
h2{{color:#1e3a5f;border-bottom:1px solid #ddd;padding-bottom:4px}}
h3{{color:#2d4a6e}} pre,code{{background:#f5f5f5;padding:12px;border-radius:6px}}
table{{border-collapse:collapse;width:100%}} td,th{{border:1px solid #ddd;padding:8px}}
th{{background:#e8f4fd}} .hdr{{background:#1e3a5f;color:white;padding:20px;border-radius:8px;margin-bottom:24px}}
@media print{{body{{margin:0}}}}</style></head><body>
<div class="hdr"><h1 style="color:white;border:none;margin:0">{rtyp}</h1>
<div style="font-size:12px;margin-top:6px;opacity:.8">AQUALINE STUDIO · {rts} · {len(filt_s)} sessions · ${total_cost:.4f}</div></div>
<div id="content">{rpt.replace(chr(10),'<br>').replace('## ','<h2>').replace('# ','<h1>').replace('### ','<h3>')}</div>
<footer style="margin-top:40px;font-size:11px;color:#999;border-top:1px solid #eee;padding-top:10px">
Generated by AQUALINE STUDIO Report Generator · {rts}</footer></body></html>"""
        st.download_button("🌐 HTML (Print→PDF)", data=html.encode("utf-8"),
            file_name=f"report_{ts_fn}.html", mime="text/html", use_container_width=True, key="dl_html")

    st.markdown("---")
    cl1, cl2, cl3 = st.columns(3)
    with cl1:
        if st.button("🔄 สร้างใหม่", use_container_width=True):
            st.session_state.rg_report = ""; st.rerun()
    with cl2:
        if st.button("💾 บันทึกรายงานนี้", use_container_width=True):
            st.session_state.rg_saved.append({"type":rtyp,"ts":rts,"text":rpt})
            st.success("✅ บันทึกแล้ว!")
    with cl3:
        if st.button("📋 แสดง Raw Text", use_container_width=True):
            st.session_state.rg_show_raw = not st.session_state.rg_show_raw; st.rerun()

    if st.session_state.rg_show_raw:
        st.text_area("Raw Text:", value=rpt, height=400, key="rg_raw")
else:
    st.markdown("""
    <div style='text-align:center;padding:60px;color:#334155;font-family:IBM Plex Mono,monospace;font-size:12px;
      border:1px dashed #1e293b;border-radius:12px'>
      <div style='font-size:48px;margin-bottom:16px'>📄</div>
      <div>เลือกประเภทรายงาน ตั้งค่า แล้วกด "Generate Report"</div>
      <div style='margin-top:8px;font-size:10px'>รองรับ Export: TXT · Markdown · JSON · HTML (พิมพ์เป็น PDF)</div>
    </div>""", unsafe_allow_html=True)

# ── Saved reports ──
if st.session_state.rg_saved:
    st.markdown("---")
    st.markdown("<div class='section-title'>📚 รายงานที่บันทึกไว้</div>", unsafe_allow_html=True)
    for i, rep in enumerate(reversed(st.session_state.rg_saved)):
        ri = len(st.session_state.rg_saved) - 1 - i
        with st.expander(f"📄 {rep['type']} — {rep['ts']}"):
            st.markdown(rep["text"])
            sc1, sc2 = st.columns(2)
            with sc1:
                st.download_button("📥 Download MD", data=rep["text"].encode("utf-8"),
                    file_name=f"saved_report_{i}.md", mime="text/markdown", key=f"sv_dl_{i}")
            with sc2:
                if st.button("🗑️ ลบ", key=f"sv_del_{i}"):
                    st.session_state.rg_saved.pop(ri); st.rerun()
