import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import os
from datetime import datetime, timedelta

import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ui_settings import inject_global_font_css

st.set_page_config(
    page_title="Dashboard — AQUALINE AI TEAM",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🔐 กันเข้าหน้านี้ตรงผ่าน URL โดยไม่ผ่านด่านล็อกอินที่หน้าแรก
from auth_guard import require_auth
require_auth()

# 🧭 PAGE-VISIT MARKER — ใช้โดยหน้า "งานบริษัทอาควาไลน์" เพื่อรู้ว่าผู้ใช้เปิดหน้าใหม่จริง
st.session_state["_active_page"] = __file__

# ฟอนต์/ขนาดตัวอักษรที่ผู้ใช้กำหนดเอง (หน้า Design UX/UI) — ใช้ร่วมกันทุกหน้า
st.markdown(inject_global_font_css(), unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# API KEY
# ══════════════════════════════════════════════════════════════════
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("🔑 ไม่พบ GOOGLE_API_KEY ใน secrets.toml")
    st.stop()

# อัตราแลกเปลี่ยน USD→THB — ดึงจาก secrets.toml เดียวกับ ai_team.py (single source of truth)
USD_TO_THB = float(st.secrets.get("USD_TO_THB", "35.0"))

# ══════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=IBM+Plex+Sans+Thai:wght@300;400;600;700&display=swap');
*,*::before,*::after{box-sizing:border-box;}
.stApp{background:#070b12;color:#cbd5e1;font-family:'IBM Plex Sans Thai',sans-serif;}
[data-testid="stSidebar"]{background:#0d1117!important;border-right:1px solid #1e293b!important;}

.page-header{background:linear-gradient(90deg,#0d1117,#0f172a,#0d1117);border-bottom:1px solid #1e293b;
  padding:20px 28px;display:flex;align-items:center;gap:16px;position:relative;overflow:hidden;margin-bottom:24px;}
.page-header::after{content:'';position:absolute;inset:0;
  background:repeating-linear-gradient(90deg,transparent,transparent 80px,rgba(56,189,248,.03) 80px,rgba(56,189,248,.03) 81px);
  pointer-events:none;}
.page-title{font-family:'IBM Plex Mono',monospace;font-size:20px;font-weight:700;color:#f1f5f9;}
.page-sub{font-size:11px;color:#475569;font-family:'IBM Plex Mono',monospace;margin-top:3px;}

.kpi-card{background:rgba(15,23,42,.8);border:1px solid #1e293b;border-radius:12px;padding:20px;
  text-align:center;transition:all .2s;}
.kpi-card:hover{border-color:#38bdf8;box-shadow:0 0 20px rgba(56,189,248,.08);}
.kpi-value{font-family:'IBM Plex Mono',monospace;font-size:32px;font-weight:700;color:#38bdf8;line-height:1;}
.kpi-label{font-size:11px;color:#475569;margin-top:6px;font-family:'IBM Plex Mono',monospace;}
.kpi-delta{font-size:10px;margin-top:4px;}
.kpi-delta.up{color:#34d399;}
.kpi-delta.down{color:#f87171;}

.section-title{font-family:'IBM Plex Mono',monospace;font-size:13px;font-weight:700;color:#94a3b8;
  letter-spacing:1px;text-transform:uppercase;margin:20px 0 12px;padding-bottom:6px;border-bottom:1px solid #1e293b;}

.agent-row{display:flex;align-items:center;gap:10px;padding:8px 12px;border-radius:8px;
  background:rgba(15,23,42,.6);border:1px solid #1e293b;margin-bottom:6px;}
.agent-row:hover{border-color:#1e3a5f;}
.agent-row-name{font-size:12px;font-weight:600;color:#e2e8f0;flex:1;}
.agent-row-count{font-family:'IBM Plex Mono',monospace;font-size:11px;color:#38bdf8;}

.activity-item{display:flex;align-items:flex-start;gap:10px;padding:10px 0;
  border-bottom:1px solid rgba(30,41,59,.5);}
.activity-dot{width:6px;height:6px;border-radius:50%;background:#38bdf8;margin-top:5px;flex-shrink:0;}
.activity-text{font-size:12px;color:#94a3b8;line-height:1.5;}
.activity-time{font-family:'IBM Plex Mono',monospace;font-size:10px;color:#334155;margin-top:2px;}

.project-card{background:rgba(15,23,42,.8);border:1px solid #1e293b;border-radius:12px;padding:16px;margin-bottom:10px;}
.project-name{font-size:13px;font-weight:600;color:#e2e8f0;margin-bottom:4px;}
.project-meta{font-size:10px;color:#475569;font-family:'IBM Plex Mono',monospace;margin-bottom:10px;}
.progress-bar-bg{background:#1e293b;border-radius:4px;height:6px;overflow:hidden;}
.progress-bar-fill{height:6px;border-radius:4px;background:linear-gradient(90deg,#38bdf8,#818cf8);}

.cost-bar{background:rgba(15,23,42,.8);border:1px solid #1e293b;border-radius:8px;padding:10px 14px;
  display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;}
.cost-name{font-size:12px;color:#94a3b8;}
.cost-val{font-family:'IBM Plex Mono',monospace;font-size:12px;color:#fbbf24;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# AGENTS (shared) — ดึงจาก AGENT_META (agent_default_personas.py)
# single source of truth: เพิ่ม/แก้ agent ที่ AGENT_META ที่เดียว หน้านี้เห็นผลตามอัตโนมัติ (รวม A26)
# ══════════════════════════════════════════════════════════════════
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent_default_personas import AGENT_META

AGENTS = {
    aid: {"name": m["name"], "icon": m["icon"], "color": m["color"]}
    for aid, m in AGENT_META.items()
}

# ══════════════════════════════════════════════════════════════════
# PERSISTENCE — dashboard_data.json (projects/costs ต้องอยู่ข้าม session ไม่หายตอนปิดเบราว์เซอร์)
# ══════════════════════════════════════════════════════════════════
DASH_DATA_FILE = "dashboard_data.json"

def load_dash_data() -> dict:
    if os.path.exists(DASH_DATA_FILE):
        try:
            with open(DASH_DATA_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
            return {"projects": d.get("projects", []), "costs": d.get("costs", {})}
        except Exception:
            pass
    return {"projects": [], "costs": {}}

def save_dash_data():
    try:
        with open(DASH_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "projects": st.session_state.dash_projects,
                "costs": st.session_state.dash_costs,
            }, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ══════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════
if "dash_sessions"   not in st.session_state: st.session_state.dash_sessions   = []
if "dash_data_loaded" not in st.session_state:
    _persisted = load_dash_data()
    st.session_state.dash_costs    = _persisted["costs"]
    st.session_state.dash_projects = _persisted["projects"]
    st.session_state.dash_data_loaded = True
if "dash_costs"      not in st.session_state: st.session_state.dash_costs      = {}
if "dash_projects"   not in st.session_state: st.session_state.dash_projects   = []
if "dash_activities" not in st.session_state: st.session_state.dash_activities = []
if "lc_messages"     not in st.session_state: st.session_state.lc_messages     = []

# ── ดึง session จาก lc_messages (cross-page) ──
def get_agent_usage() -> dict:
    counts = {}
    for m in st.session_state.get("lc_messages", []):
        aid = m.get("agent_id")
        if aid:
            counts[aid] = counts.get(aid, 0) + 1
    return counts

# ══════════════════════════════════════════════════════════════════
# SIDEBAR NAV
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:14px 0 8px'>
      <div style='font-family:IBM Plex Mono,monospace;font-size:13px;font-weight:700;color:#f1f5f9'>AQUALINE</div>
      <div style='font-size:10px;color:#334155;font-family:IBM Plex Mono,monospace'>AI LIVE CHAT</div>
    </div>""", unsafe_allow_html=True)
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
    st.markdown("---")
    if st.button("🔄 รีเฟรช Dashboard", use_container_width=True):
        st.rerun()

# ══════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<div class="page-header">
  <div style='font-size:36px'>📊</div>
  <div>
    <div class="page-title">DASHBOARD ภาพรวมโปรเจกต์</div>
    <div class="page-sub">Control Tower · ติดตาม KPI · Agent · Cost · กิจกรรม</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# LOAD REAL ANALYTICS DATA
# ══════════════════════════════════════════════════════════════════
ANALYTICS_FILE = "analytics_data.json"

@st.cache_data(ttl=30)
def load_analytics_data():
    if os.path.exists(ANALYTICS_FILE):
        try:
            with open(ANALYTICS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"sessions": [], "agent_usage": {}, "project_count": {}, "weekly": {}}

_analytics = load_analytics_data()
_sessions  = _analytics.get("sessions", [])

# ── KPI จากข้อมูลจริง ──
real_total_sessions  = len(_sessions)
real_total_tokens    = sum(s.get("tokens",   0)   for s in _sessions)
real_total_cost_usd  = sum(s.get("cost_usd", 0.0) for s in _sessions)
real_total_cost_thb  = real_total_cost_usd * USD_TO_THB
real_agent_calls     = sum(len(s.get("agents_used", [])) for s in _sessions)
real_top_agents      = sorted(_analytics.get("agent_usage", {}).items(), key=lambda x: x[1], reverse=True)

# ── delta เทียบกับ 7 วันก่อน ──
from datetime import timezone
_now = datetime.now()
_week_ago = _now - timedelta(days=7)
_recent = [s for s in _sessions if s.get("timestamp","") >= _week_ago.isoformat()]
_older  = [s for s in _sessions if s.get("timestamp","") < _week_ago.isoformat()]
_delta_sessions = len(_recent) - (len(_older) // max(1, (real_total_sessions // max(len(_recent),1))))

# SESSION STATE (สำหรับ Live Chat ที่ยังใช้ session)
usage = get_agent_usage()
total_msgs = len(st.session_state.lc_messages)
user_msgs  = len([m for m in st.session_state.lc_messages if m.get("role") == "user"])
agent_msgs = len([m for m in st.session_state.lc_messages if m.get("role") == "agent"])

# ══════════════════════════════════════════════════════════════════
# KPI CARDS — จากข้อมูลจริง
# ══════════════════════════════════════════════════════════════════
active_agents   = len(usage) or len(_analytics.get("agent_usage", {}))
projects_active = len(st.session_state.dash_projects) or len(_analytics.get("project_count", {}))
total_cost      = real_total_cost_thb + (sum(st.session_state.dash_costs.values()) if st.session_state.dash_costs else 0.0)
col1, col2, col3, col4, col5 = st.columns(5)
kpi_data = [
    (col1, "🤝", str(real_total_sessions),  "Sessions ทั้งหมด",        f"+{len(_recent)} สัปดาห์นี้", "up"),
    (col2, "🤖", str(len(_analytics.get("agent_usage", {})) or active_agents), "Agents ที่ใช้แล้ว", f"/{len(AGENTS)} ทั้งหมด", "up"),
    (col3, "🔢", f"{real_total_tokens:,}",   "Tokens สะสม",             "ประมาณการ", "up"),
    (col4, "💰", f"฿{total_cost:,.2f}",      "ค่า AI สะสม (THB)",      f"${real_total_cost_usd:.4f} USD", "down" if total_cost > 500 else "up"),
    (col5, "⚡", str(real_agent_calls),       "Agent Calls รวม",         f"{len(_recent)} call สัปดาห์นี้", "up"),
]
for col, icon, val, label, delta, direction in kpi_data:
    with col:
        st.markdown(f"""
        <div class="kpi-card">
          <div style='font-size:24px;margin-bottom:4px'>{icon}</div>
          <div class="kpi-value">{val}</div>
          <div class="kpi-label">{label}</div>
          <div class="kpi-delta {direction}">{delta}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# ROW 2 — Agent Usage + Activity Log
# ══════════════════════════════════════════════════════════════════
col_left, col_right = st.columns([1, 1])

with col_left:
    st.markdown("<div class='section-title'>🤖 Agent Usage Ranking</div>", unsafe_allow_html=True)
    # รวม usage จาก analytics_data.json (จากการประชุม) + lc_messages (Live Chat)
    merged_usage = dict(_analytics.get("agent_usage", {}))
    for aid, cnt in usage.items():
        merged_usage[aid] = merged_usage.get(aid, 0) + cnt
    if merged_usage:
        sorted_usage = sorted(merged_usage.items(), key=lambda x: x[1], reverse=True)
        total_calls = sum(merged_usage.values()) or 1
        for aid, cnt in sorted_usage[:10]:
            info = AGENTS.get(aid, {})
            name = info.get("name", aid)
            icon = info.get("icon", "🤖")
            color = info.get("color", "#38bdf8")
            pct = int((cnt / total_calls) * 100)
            st.markdown(f"""
            <div class="agent-row">
              <span style='font-size:18px'>{icon}</span>
              <div class="agent-row-name">{name}</div>
              <div style='width:60px;background:#1e293b;border-radius:3px;height:4px;overflow:hidden'>
                <div style='width:{pct}%;height:4px;background:{color};border-radius:3px'></div>
              </div>
              <div class="agent-row-count">{cnt}ครั้ง</div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='text-align:center;padding:40px 0;color:#334155;font-family:IBM Plex Mono,monospace;font-size:12px'>
          ยังไม่มีข้อมูลการใช้งาน<br>เริ่มคุยกับ Agent ใน Live Chat ก่อนนะครับ
        </div>""", unsafe_allow_html=True)

with col_right:
    st.markdown("<div class='section-title'>📋 กิจกรรมล่าสุด</div>", unsafe_allow_html=True)

    # รวม activity จาก lc_messages จริง
    activities = []
    for m in st.session_state.lc_messages[-15:]:
        role = m.get("role")
        ts   = m.get("time", "")
        if role == "user":
            txt = m.get("content", "")[:60]
            activities.append({"dot": "#38bdf8", "text": f"คุณถาม: {txt}{'...' if len(m.get('content',''))>60 else ''}", "time": ts})
        elif role == "agent":
            aname = m.get("agent_name", "Agent")
            txt   = m.get("content", "")[:50]
            activities.append({"dot": "#34d399", "text": f"{aname} ตอบ: {txt}{'...' if len(m.get('content',''))>50 else ''}", "time": ts})

    if not activities:
        st.markdown("""
        <div style='text-align:center;padding:40px 0;color:#334155;font-family:IBM Plex Mono,monospace;font-size:12px'>
          ยังไม่มีกิจกรรม<br>เริ่มต้นใช้งานระบบก่อนครับ
        </div>""", unsafe_allow_html=True)
    else:
        for act in reversed(activities[-8:]):
            st.markdown(f"""
            <div class="activity-item">
              <div class="activity-dot" style='background:{act["dot"]}'></div>
              <div>
                <div class="activity-text">{act["text"]}</div>
                <div class="activity-time">{act["time"]}</div>
              </div>
            </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# ROW 3 — Active Projects + Cost Breakdown
# ══════════════════════════════════════════════════════════════════
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
col_proj, col_cost = st.columns([1.2, 0.8])

with col_proj:
    st.markdown("<div class='section-title'>🗂️ Projects ที่ Active</div>", unsafe_allow_html=True)

    with st.expander("➕ เพิ่มโปรเจกต์ใหม่", expanded=False):
        p_name = st.text_input("ชื่อโปรเจกต์", key="new_proj_name")
        p_desc = st.text_input("รายละเอียด", key="new_proj_desc")
        p_prog = st.slider("ความคืบหน้า (%)", 0, 100, 30, key="new_proj_prog")
        if st.button("บันทึกโปรเจกต์", key="save_proj"):
            if p_name:
                st.session_state.dash_projects.append({
                    "name": p_name, "desc": p_desc, "progress": p_prog,
                    "date": datetime.now().strftime("%d/%m/%Y"), "status": "active"
                })
                save_dash_data()
                st.success(f"✅ เพิ่ม '{p_name}' แล้ว")
                st.rerun()

    if st.session_state.dash_projects:
        for i, proj in enumerate(st.session_state.dash_projects):
            col_p, col_del = st.columns([5, 1])
            with col_p:
                prog = proj.get("progress", 0)
                color = "#34d399" if prog >= 80 else "#38bdf8" if prog >= 50 else "#fbbf24"
                st.markdown(f"""
                <div class="project-card">
                  <div class="project-name">{proj['name']}</div>
                  <div class="project-meta">{proj.get('desc','')} · {proj.get('date','')}</div>
                  <div style='display:flex;align-items:center;gap:8px'>
                    <div class="progress-bar-bg" style='flex:1'>
                      <div class="progress-bar-fill" style='width:{prog}%;background:{color}'></div>
                    </div>
                    <span style='font-family:IBM Plex Mono,monospace;font-size:11px;color:{color}'>{prog}%</span>
                  </div>
                </div>""", unsafe_allow_html=True)
            with col_del:
                if st.button("🗑️", key=f"del_proj_{i}", help="ลบโปรเจกต์"):
                    st.session_state.dash_projects.pop(i)
                    save_dash_data()
                    st.rerun()
    else:
        st.markdown("""
        <div style='text-align:center;padding:30px;color:#334155;font-family:IBM Plex Mono,monospace;font-size:12px;
          border:1px dashed #1e293b;border-radius:10px'>
          ยังไม่มีโปรเจกต์ — กด "เพิ่มโปรเจกต์ใหม่" ด้านบน
        </div>""", unsafe_allow_html=True)

with col_cost:
    st.markdown("<div class='section-title'>💰 สรุปค่าใช้จ่าย AI</div>", unsafe_allow_html=True)

    model_costs = st.session_state.dash_costs if st.session_state.dash_costs else {
        "Gemini Flash": 0.0,
        "Gemini Pro": 0.0,
    }

    with st.expander("➕ บันทึกค่าใช้จ่าย", expanded=False):
        cost_model = st.selectbox("โมเดล", ["Gemini Flash", "Gemini Pro", "Claude Sonnet", "Claude Opus", "GPT-4o"], key="cost_model_sel")
        cost_amt   = st.number_input("จำนวนเงิน (฿)", min_value=0.0, step=10.0, key="cost_amt_inp")
        if st.button("บันทึก", key="save_cost"):
            st.session_state.dash_costs[cost_model] = st.session_state.dash_costs.get(cost_model, 0.0) + cost_amt
            save_dash_data()
            st.rerun()

    total = sum(model_costs.values())
    for model, amt in model_costs.items():
        st.markdown(f"""
        <div class="cost-bar">
          <span class="cost-name">{model}</span>
          <span class="cost-val">฿{amt:,.2f}</span>
        </div>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div style='background:rgba(56,189,248,.08);border:1px solid rgba(56,189,248,.2);border-radius:8px;
      padding:12px;text-align:center;margin-top:8px'>
      <div style='font-size:10px;color:#475569;font-family:IBM Plex Mono,monospace'>รวมทั้งหมด</div>
      <div style='font-family:IBM Plex Mono,monospace;font-size:24px;font-weight:700;color:#38bdf8'>฿{total:,.2f}</div>
    </div>""", unsafe_allow_html=True)

    if total > 0 and st.button("🗑️ รีเซ็ตค่าใช้จ่าย", key="reset_cost"):
        st.session_state.dash_costs = {}
        save_dash_data()
        st.rerun()

# ══════════════════════════════════════════════════════════════════
# AI ANALYSIS BUTTON
# ══════════════════════════════════════════════════════════════════
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>🧠 วิเคราะห์ด้วย AI</div>", unsafe_allow_html=True)

if st.button("🔍 ให้ AI วิเคราะห์ภาพรวมการใช้งาน", use_container_width=True, type="primary"):
    summary_text = f"""
ข้อมูลการใช้งาน AQUALINE AI TEAM:
- ข้อความทั้งหมด: {total_msgs} ข้อความ (User: {user_msgs}, Agent: {agent_msgs})
- Agent ที่ใช้บ่อยที่สุด: {', '.join([AGENTS.get(a,{}).get('name',a) for a,_ in sorted(usage.items(),key=lambda x:x[1],reverse=True)[:3]]) if usage else 'ยังไม่มีข้อมูล'}
- Projects: {len(st.session_state.dash_projects)} โปรเจกต์
- ค่าใช้จ่าย AI รวม: ฿{total:,.2f}

กรุณาวิเคราะห์รูปแบบการใช้งาน แนะนำ Agent ที่ควรใช้เพิ่ม และให้คำแนะนำเพื่อเพิ่มประสิทธิภาพทีม ตอบเป็นภาษาไทย กระชับ ชัดเจน
"""
    with st.spinner("🔍 AI กำลังวิเคราะห์..."):
        try:
            @st.cache_data(ttl=60, show_spinner=False)
            def get_model(k):
                r = requests.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={k}", timeout=8)
                if r.status_code == 200:
                    avail = [m["name"] for m in r.json().get("models",[]) if "generateContent" in m.get("supportedGenerationMethods",[])]
                    for p in ["models/gemini-2.5-flash-preview-05-20","models/gemini-2.5-flash","models/gemini-1.5-flash-latest","models/gemini-1.5-flash"]:
                        if p in avail: return p
                return "models/gemini-1.5-flash"
            model = get_model(API_KEY)
            resp = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={API_KEY}",
                json={"contents":[{"parts":[{"text":summary_text}]}],"generationConfig":{"temperature":0.6,"maxOutputTokens":2048}},
                timeout=60
            )
            if resp.status_code == 200:
                result = resp.json()["candidates"][0]["content"]["parts"][0].get("text","")
                st.markdown(f"""
                <div style='background:rgba(15,23,42,.9);border:1px solid rgba(56,189,248,.3);border-radius:12px;padding:20px;margin-top:8px'>
                  <div style='font-family:IBM Plex Mono,monospace;font-size:10px;color:#38bdf8;margin-bottom:10px'>🧠 AI ANALYSIS REPORT</div>
                  <div style='font-size:13px;color:#cbd5e1;line-height:1.8;white-space:pre-wrap'>{result}</div>
                </div>""", unsafe_allow_html=True)
            else:
                st.error(f"❌ API Error {resp.status_code}")
        except Exception as e:
            st.error(f"⚠️ {str(e)[:100]}")
# ══════════════════════════════════════════════════════════════════
# EXPORT & FILTER SECTION
# ══════════════════════════════════════════════════════════════════
st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
st.markdown("<div class='section-title'>📥 Export & ตัวกรอง</div>", unsafe_allow_html=True)

# ─── Load analytics_data.json เพื่อ export จริง ───
ANALYTICS_FILE = "analytics_data.json"
def load_analytics_dash():
    if os.path.exists(ANALYTICS_FILE):
        try:
            with open(ANALYTICS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {"sessions": [], "agent_usage": {}, "project_count": {}, "weekly": {}}

analytics_data = load_analytics_dash()
sessions_data  = analytics_data.get("sessions", [])

col_filter1, col_filter2, col_filter3 = st.columns(3)
with col_filter1:
    filter_project = st.text_input("🔍 กรอง Project:", placeholder="ค้นหาชื่อ project...", key="dash_filter_proj")
with col_filter2:
    filter_agent = st.selectbox("🤖 กรอง Agent:", ["ทั้งหมด"] + [f"{aid} {AGENTS.get(aid,{}).get('name','')}" for aid in sorted(AGENTS.keys())], key="dash_filter_agent")
with col_filter3:
    sort_sessions = st.selectbox("🔢 เรียง:", ["ใหม่ → เก่า", "เก่า → ใหม่", "tokens มากสุด", "cost มากสุด"], key="dash_sort")

# Filter sessions
filtered_s = sessions_data.copy()
if filter_project:
    filtered_s = [s for s in filtered_s if filter_project.lower() in s.get("project","").lower()]
if filter_agent != "ทั้งหมด":
    aid_filter = filter_agent.split(" ")[0]
    filtered_s = [s for s in filtered_s if aid_filter in s.get("agents_used", [])]
if sort_sessions == "ใหม่ → เก่า":
    filtered_s = list(reversed(filtered_s))
elif sort_sessions == "tokens มากสุด":
    filtered_s = sorted(filtered_s, key=lambda x: x.get("tokens",0), reverse=True)
elif sort_sessions == "cost มากสุด":
    filtered_s = sorted(filtered_s, key=lambda x: x.get("cost_usd",0), reverse=True)

st.markdown(f"<div style='font-size:12px;color:#475569;margin-bottom:8px'>พบ {len(filtered_s)} session</div>", unsafe_allow_html=True)

# Export buttons
col_ex1, col_ex2, col_ex3, col_ex4 = st.columns(4)
import csv
from io import StringIO

with col_ex1:
    if filtered_s:
        buf = StringIO()
        w = csv.writer(buf)
        w.writerow(["timestamp","project","tokens","cost_usd","cost_thb","agents"])
        for s in filtered_s:
            w.writerow([s.get("timestamp",""), s.get("project",""), s.get("tokens",0),
                        round(s.get("cost_usd",0),6), round(s.get("cost_usd",0)*USD_TO_THB,2),
                        "|".join(s.get("agents_used",[]))])
        st.download_button("📥 Export CSV", data=buf.getvalue().encode("utf-8-sig"),
            file_name=f"dashboard_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv", use_container_width=True, key="dash_csv")

with col_ex2:
    if filtered_s:
        jdata = json.dumps({"exported": datetime.now().isoformat(), "sessions": filtered_s,
                            "projects": st.session_state.dash_projects,
                            "costs": st.session_state.dash_costs}, ensure_ascii=False, indent=2)
        st.download_button("📥 Export JSON", data=jdata.encode("utf-8"),
            file_name=f"dashboard_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json", use_container_width=True, key="dash_json")

with col_ex3:
    # Markdown report
    total_tok = sum(s.get("tokens",0) for s in filtered_s)
    total_cost_exp = sum(s.get("cost_usd",0) for s in filtered_s)
    md_lines = [f"# AQUALINE Dashboard Report\nExported: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n",
                f"**Sessions:** {len(filtered_s)} | **Tokens:** {total_tok:,} | **Cost:** ${total_cost_exp:.4f} / ฿{total_cost_exp*USD_TO_THB:.2f}\n\n",
                f"## Projects Active ({len(st.session_state.dash_projects)})\n"]
    for p in st.session_state.dash_projects:
        md_lines.append(f"- **{p['name']}** — {p.get('progress',0)}% | {p.get('desc','')}\n")
    md_lines.append(f"\n## AI Cost Breakdown\n")
    for m, amt in st.session_state.dash_costs.items():
        md_lines.append(f"- {m}: ฿{amt:,.2f}\n")
    md_lines.append(f"\n## Top Sessions\n")
    for s in filtered_s[:20]:
        md_lines.append(f"- **{s.get('project','?')}** | {s.get('timestamp','')[:16]} | {s.get('tokens',0):,} tokens | ${s.get('cost_usd',0):.4f}\n")
    st.download_button("📥 Export MD", data="".join(md_lines).encode("utf-8"),
        file_name=f"dashboard_{datetime.now().strftime('%Y%m%d')}.md",
        mime="text/markdown", use_container_width=True, key="dash_md")

with col_ex4:
    # Quick stats card
    if st.button("🔄 รีเฟรชข้อมูล", use_container_width=True, key="dash_refresh2"):
        st.cache_data.clear()
        st.rerun()
