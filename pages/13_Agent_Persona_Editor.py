import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import os
from datetime import datetime

st.set_page_config(
    page_title="Agent Persona Editor — AQUALINE",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════════════════════════════
# API KEY
# ══════════════════════════════════════════════════════════════════
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("🔑 ไม่พบ GOOGLE_API_KEY ใน secrets.toml")
    st.stop()

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
  background:repeating-linear-gradient(90deg,transparent,transparent 80px,rgba(56,189,248,.03) 80px,rgba(56,189,248,.03) 81px);pointer-events:none;}
.page-title{font-family:'IBM Plex Mono',monospace;font-size:20px;font-weight:700;color:#f1f5f9;}
.page-sub{font-size:11px;color:#475569;font-family:'IBM Plex Mono',monospace;margin-top:3px;}

.section-title{font-family:'IBM Plex Mono',monospace;font-size:13px;font-weight:700;color:#94a3b8;
  letter-spacing:1px;text-transform:uppercase;margin:20px 0 12px;padding-bottom:6px;border-bottom:1px solid #1e293b;}

.agent-chip{display:inline-block;padding:4px 10px;border-radius:16px;font-size:11px;
  font-family:'IBM Plex Mono',monospace;border:1px solid;margin:2px;cursor:pointer;}

.persona-card{background:rgba(15,23,42,.8);border:1px solid #1e293b;border-radius:12px;padding:16px;margin-bottom:8px;}
.persona-card-title{font-size:13px;font-weight:700;color:#e2e8f0;margin-bottom:4px;}
.persona-card-meta{font-size:10px;color:#475569;font-family:'IBM Plex Mono',monospace;margin-bottom:8px;}
.persona-card-preview{font-size:12px;color:#64748b;line-height:1.5;
  background:rgba(30,41,59,.4);border-radius:6px;padding:8px;border-left:2px solid #38bdf8;}

.test-bubble{background:rgba(15,23,42,.9);border:1px solid rgba(56,189,248,.2);
  border-radius:12px;padding:16px;margin-top:8px;font-size:13px;color:#cbd5e1;line-height:1.8;white-space:pre-wrap;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# PERSONA FILE — shared กับ ai_team.py และทุกหน้า
# ══════════════════════════════════════════════════════════════════
PERSONA_FILE = "agent_personas.json"

def load_personas_from_file() -> dict:
    """โหลด custom personas จากไฟล์ (sync กับ ai_team.py)"""
    if os.path.exists(PERSONA_FILE):
        try:
            with open(PERSONA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_personas_to_file(ape_custom: dict):
    """
    บันทึก personas ลงไฟล์ agent_personas.json
    ai_team.py อ่าน custom_personas เป็น {aid: system_prompt_string}
    แต่หน้านี้เก็บ full dict → แยกเก็บ 2 key:
      - "full"   : full persona dict (สำหรับหน้านี้โหลดกลับมา)
      - per aid  : system_prompt string ตรงๆ (สำหรับ ai_team.py)
    """
    out = {}
    for aid, data in ape_custom.items():
        # ai_team.py ใช้ custom_personas.get(aid, "") → ต้องเป็น string
        out[aid] = data.get("system_prompt", "")
    # เก็บ full data แยกไว้ที่ key พิเศษ ให้หน้านี้โหลดกลับมาได้ครบ
    out["__full__"] = ape_custom
    with open(PERSONA_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

def load_full_personas_from_file() -> dict:
    """โหลด full persona dict กลับมาสำหรับหน้า Editor"""
    raw = load_personas_from_file()
    return raw.get("__full__", {})

# ══════════════════════════════════════════════════════════════════
# DEFAULT AGENTS
# ══════════════════════════════════════════════════════════════════
DEFAULT_AGENTS = {
    "A1":  {"name":"นักกลยุทธ์การตลาด",      "icon":"👨‍💼","role":"วางแผนภาพรวมและจุดขาย",               "color":"#38bdf8"},
    "A2":  {"name":"ผู้จัดการโครงการ",         "icon":"📋", "role":"คุมเป้าหมายและเวลา",                  "color":"#a78bfa"},
    "A3":  {"name":"นักเขียนคำโฆษณา",          "icon":"✍️", "role":"สร้าง Content และ Caption โซเชียล",   "color":"#34d399"},
    "A4":  {"name":"กราฟิกดีไซเนอร์",          "icon":"🎨", "role":"ออกแบบ Visual",                       "color":"#f472b6"},
    "A5":  {"name":"3D Visualizer",              "icon":"🏗️", "role":"เรนเดอร์ภาพสินค้าจริง",              "color":"#fb923c"},
    "A6":  {"name":"ผู้เชี่ยวชาญวิดีโอ",        "icon":"🎬", "role":"สคริปต์และมุมกล้อง",                 "color":"#e879f9"},
    "A7":  {"name":"นักยิงแอด Facebook",         "icon":"📈", "role":"วางแผนสื่อโฆษณา",                    "color":"#38bdf8"},
    "A8":  {"name":"ผู้เชี่ยวชาญ SEO",           "icon":"🌐", "role":"ปรับแต่งเนื้อหาให้ติดอันดับ",        "color":"#34d399"},
    "A9":  {"name":"ฝ่ายบริการลูกค้า",          "icon":"💬", "role":"วางแนวทางตอบคำถาม",                  "color":"#fbbf24"},
    "A10": {"name":"นักวิเคราะห์ข้อมูล",        "icon":"📊", "role":"วิเคราะห์สถิติความคุ้มค่า",          "color":"#a78bfa"},
    "A11": {"name":"ครีเอทีฟไดเรกเตอร์",        "icon":"💡", "role":"คิดไอเดีย Big Idea",                 "color":"#f59e0b"},
    "A12": {"name":"คนเขียนสตอรี่บอร์ด",        "icon":"🎞️", "role":"วางลำดับภาพเล่าเรื่อง",             "color":"#34d399"},
    "A13": {"name":"อาร์ตไดเรกเตอร์",           "icon":"✨", "role":"ควบคุมคุณภาพงานดีไซน์",             "color":"#f472b6"},
    "A14": {"name":"ผู้เชี่ยวชาญ AI Prompt",    "icon":"🤖", "role":"ปรับจูนคำสั่งให้ AI",                "color":"#38bdf8"},
    "A15": {"name":"นักวางระบบอัตโนมัติ",       "icon":"⚙️", "role":"เชื่อมระบบ Automation",              "color":"#94a3b8"},
    "A16": {"name":"นักออกแบบบูธ",              "icon":"🎪", "role":"วางผังงานนิทรรศการ",                 "color":"#fb923c"},
    "A17": {"name":"นักวิจัยตลาด",              "icon":"🔍", "role":"เจาะลึกข้อมูลคู่แข่ง",               "color":"#38bdf8"},
    "A18": {"name":"ฝ่ายตรวจสเปกสินค้า",        "icon":"✅", "role":"ตรวจสอบความถูกต้องทางเทคนิค",       "color":"#34d399"},
    "A19": {"name":"นักขายมือโปร",              "icon":"💰", "role":"สร้างสคริปต์ปิดการขาย",             "color":"#fbbf24"},
    "A20": {"name":"ที่ปรึกษากฎหมาย",           "icon":"⚖️", "role":"ตรวจสอบข้อบังคับและลิขสิทธิ์",      "color":"#f87171"},
    "A21": {"name":"นักเขียนบทความและบล็อก",    "icon":"📝", "role":"เขียนบทความยาว เนื้อหาเชิงลึก",      "color":"#a78bfa"},
    "A22": {"name":"นักวางราคา / Pricing",       "icon":"🧮", "role":"วิเคราะห์ราคา Bundle และ Tier",       "color":"#34d399"},
    "A23": {"name":"ผู้เชี่ยวชาญ LINE OA/CRM",  "icon":"📱", "role":"วางแผน LINE OA, Broadcast, CRM",     "color":"#38bdf8"},
    "A24": {"name":"TikTok & Reels Specialist",   "icon":"🎵", "role":"Hook, Trend, Script TikTok/Reels",    "color":"#f472b6"},
    "A25": {"name":"นักจิตวิทยาการตลาด",        "icon":"🧠", "role":"Psychology ลูกค้า trigger การซื้อ",   "color":"#a78bfa"},
}

# ══════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════
if "ape_custom_agents"  not in st.session_state:
    # โหลดจากไฟล์ทันทีตอนเริ่ม — sync กับ ai_team.py
    st.session_state.ape_custom_agents = load_full_personas_from_file()
if "ape_selected_aid"   not in st.session_state:
    st.session_state.ape_selected_aid  = "A1"
if "ape_test_result"    not in st.session_state:
    st.session_state.ape_test_result   = ""
if "ape_ab_results"     not in st.session_state:
    st.session_state.ape_ab_results    = {}

# ══════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════
@st.cache_data(ttl=60, show_spinner=False)
def get_model(k):
    r = requests.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={k}", timeout=8)
    if r.status_code == 200:
        avail = [m["name"] for m in r.json().get("models",[]) if "generateContent" in m.get("supportedGenerationMethods",[])]
        for p in ["models/gemini-2.5-flash-preview-05-20","models/gemini-2.5-flash","models/gemini-1.5-flash-latest","models/gemini-1.5-flash"]:
            if p in avail: return p
    return "models/gemini-1.5-flash"

def call_agent_with_persona(system_prompt: str, user_msg: str) -> str:
    model = get_model(API_KEY)
    combined = f"{system_prompt}\n\nคำถาม: {user_msg}\n\nตอบในฐานะ persona นี้:"
    resp = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={API_KEY}",
        json={"contents":[{"parts":[{"text":combined}]}],
              "generationConfig":{"temperature":0.75,"maxOutputTokens":2048}},
        timeout=90
    )
    if resp.status_code == 200:
        return resp.json()["candidates"][0]["content"]["parts"][0].get("text","").strip()
    return f"⚠️ API Error {resp.status_code}"

def get_current_persona(aid: str) -> dict:
    custom = st.session_state.ape_custom_agents.get(aid, {})
    default = DEFAULT_AGENTS.get(aid, {})
    return {**default, **custom}

# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:14px 0 8px'>
      <div style='font-family:IBM Plex Mono,monospace;font-size:13px;font-weight:700;color:#f1f5f9'>AQUALINE</div>
      <div style='font-size:10px;color:#334155;font-family:IBM Plex Mono,monospace'>AI LIVE CHAT</div>
    </div>""", unsafe_allow_html=True)
    st.markdown("---")
    st.page_link("ai_team.py",                        label="🤖 AI Special Team")
    st.page_link("pages/8_Workflow_Builder.py",        label="🏭 Content Factory")
    st.page_link("pages/9_Live_Chat.py",               label="💬 Live Chat")
    st.page_link("pages/10_Dashboard.py",              label="📊 Dashboard")
    st.page_link("pages/11_Budget_Cost_Manager.py",    label="💰 Budget & Cost")
    st.page_link("pages/12_Report_Generator.py",       label="📄 Report Generator")
    st.page_link("pages/13_Agent_Persona_Editor.py",   label="🧬 Agent Persona Editor")
    st.page_link("pages/14_Settings_Config.py",        label="⚙️ Settings & Config")
    st.markdown("---")
    st.markdown("<div style='font-size:10px;color:#475569;font-family:IBM Plex Mono,monospace;padding:0 0 6px'>🤖 เลือก Agent</div>", unsafe_allow_html=True)
    aid_options = list(DEFAULT_AGENTS.keys())
    sel_idx = aid_options.index(st.session_state.ape_selected_aid) if st.session_state.ape_selected_aid in aid_options else 0
    for aid in aid_options:
        info    = DEFAULT_AGENTS[aid]
        is_custom = aid in st.session_state.ape_custom_agents
        is_sel  = aid == st.session_state.ape_selected_aid
        badge   = "✏️ " if is_custom else ""
        border  = f"border-left:3px solid {info['color']}" if is_sel else ""
        st.markdown(f"""
        <div style='padding:4px 8px;border-radius:6px;margin-bottom:2px;background:{"rgba(56,189,248,.06)" if is_sel else "transparent"};{border}'>
          <span style='font-size:11px;color:{"#e2e8f0" if is_sel else "#64748b"}'>{info["icon"]} {badge}{info["name"]}</span>
        </div>""", unsafe_allow_html=True)
        if st.button("เลือก", key=f"sel_agent_{aid}", use_container_width=True):
            st.session_state.ape_selected_aid = aid
            st.session_state.ape_test_result  = ""
            st.rerun()

# ══════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<div class="page-header">
  <div style='font-size:36px'>🧬</div>
  <div>
    <div class="page-title">AGENT PERSONA EDITOR</div>
    <div class="page-sub">แก้ไข System Prompt · สร้าง Custom Persona · A/B Test · ทดสอบ 25 Agent</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Sync Status Banner ──
_synced_count = len(st.session_state.ape_custom_agents)
if _synced_count > 0:
    _names = ", ".join(
        st.session_state.ape_custom_agents[k].get("name", k)
        for k in list(st.session_state.ape_custom_agents.keys())[:5]
    )
    if _synced_count > 5:
        _names += f" +{_synced_count - 5} อื่นๆ"
    st.markdown(f"""
<div style='background:rgba(52,211,153,.08);border:1px solid rgba(52,211,153,.3);border-radius:10px;
  padding:10px 16px;margin-bottom:16px;display:flex;align-items:center;gap:10px'>
  <span style='font-size:18px'>🔗</span>
  <div>
    <span style='font-size:12px;font-weight:700;color:#34d399'>SYNCED กับ AI Team ทุกหน้า</span>
    <span style='font-size:11px;color:#64748b;margin-left:8px'>{_synced_count} Custom Persona: {_names}</span>
  </div>
</div>
""", unsafe_allow_html=True)
else:
    st.markdown("""
<div style='background:rgba(71,85,105,.08);border:1px solid #334155;border-radius:10px;
  padding:10px 16px;margin-bottom:16px;display:flex;align-items:center;gap:10px'>
  <span style='font-size:18px'>💡</span>
  <span style='font-size:12px;color:#64748b'>ยังไม่มี Custom Persona — Agent ทั้งหมดใช้ Default · บันทึก Persona แรกเพื่อเริ่ม Sync</span>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# MAIN EDITOR
# ══════════════════════════════════════════════════════════════════
aid      = st.session_state.ape_selected_aid
persona  = get_current_persona(aid)
is_custom = aid in st.session_state.ape_custom_agents
color    = persona.get("color", "#38bdf8")

# Agent info header
st.markdown(f"""
<div style='display:flex;align-items:center;gap:14px;padding:12px 18px;background:rgba(15,23,42,.8);
  border:1px solid {color}40;border-radius:12px;margin-bottom:16px'>
  <div style='font-size:40px'>{persona.get("icon","🤖")}</div>
  <div>
    <div style='font-family:IBM Plex Mono,monospace;font-size:16px;font-weight:700;color:{color}'>{persona["name"]}</div>
    <div style='font-size:11px;color:#475569;margin-top:2px'>{persona.get("role","")}</div>
    <div style='margin-top:4px'>
      {"<span style='font-family:IBM Plex Mono,monospace;font-size:10px;background:rgba(251,191,36,.1);border:1px solid rgba(251,191,36,.3);color:#fbbf24;padding:2px 8px;border-radius:10px'>✏️ CUSTOM PERSONA</span>" if is_custom else "<span style='font-family:IBM Plex Mono,monospace;font-size:10px;background:rgba(52,211,153,.1);border:1px solid rgba(52,211,153,.3);color:#34d399;padding:2px 8px;border-radius:10px'>✅ DEFAULT</span>"}
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

col_edit, col_test = st.columns([1, 1])

# ══════════════════════════════════════════════════════════════════
# EDITOR COLUMN
# ══════════════════════════════════════════════════════════════════
with col_edit:
    st.markdown("<div class='section-title'>✏️ แก้ไข Persona</div>", unsafe_allow_html=True)

    custom = st.session_state.ape_custom_agents.get(aid, {})

    new_name = st.text_input("ชื่อ Agent", value=custom.get("name", persona["name"]), key="edit_name")
    new_role = st.text_input("บทบาท (Role)", value=custom.get("role", persona.get("role","")), key="edit_role")
    new_icon = st.text_input("Icon (Emoji)", value=custom.get("icon", persona.get("icon","🤖")), key="edit_icon")

    # Color picker
    color_options = {"#38bdf8":"Sky Blue","#a78bfa":"Purple","#34d399":"Emerald",
                     "#f472b6":"Pink","#fb923c":"Orange","#fbbf24":"Amber",
                     "#f87171":"Red","#e879f9":"Fuchsia","#94a3b8":"Slate"}
    new_color = st.selectbox("สีประจำตัว", list(color_options.keys()),
        format_func=lambda x: f"● {color_options[x]}",
        index=list(color_options.keys()).index(custom.get("color", color)) if custom.get("color", color) in color_options else 0,
        key="edit_color")

    # System Prompt
    default_system = f"""คุณคือ {persona['name']} — สมาชิกของ AQUALINE AI TEAM
    
## ความเชี่ยวชาญ
{persona.get('role','')}

## บุคลิก
- พูดเหมือนที่ปรึกษาระดับสูงกำลังนั่งคุยกับลูกค้า
- คิดลึก วิเคราะห์จริง ไม่ตอบกว้างๆ ผิวเผิน
- ตอบภาษาไทย เข้าใจง่าย"""

    new_system = st.text_area(
        "System Prompt",
        value=custom.get("system_prompt", default_system),
        height=250,
        key="edit_system",
        help="กำหนด personality, ความเชี่ยวชาญ, และสไตล์การตอบของ Agent นี้"
    )

    # Tone & Style
    st.markdown("<div style='font-size:11px;color:#475569;font-family:IBM Plex Mono,monospace;margin-bottom:4px'>🎭 Tone & Style</div>", unsafe_allow_html=True)
    tone_options = ["เป็นทางการ (Formal)","กึ่งทางการ (Semi-formal)","เป็นกันเอง (Casual)",
                    "มืออาชีพแบบ Startup","เข้มข้นวิเคราะห์","สร้างสรรค์ Creative"]
    new_tone = st.selectbox("Tone", tone_options,
        index=tone_options.index(custom.get("tone", "กึ่งทางการ (Semi-formal)")) if custom.get("tone") in tone_options else 1,
        key="edit_tone", label_visibility="collapsed")

    # Expertise tags
    st.markdown("<div style='font-size:11px;color:#475569;font-family:IBM Plex Mono,monospace;margin-bottom:4px'>🏷️ ความเชี่ยวชาญเพิ่มเติม</div>", unsafe_allow_html=True)
    expertise_tags = st.multiselect(
        "เลือกความเชี่ยวชาญ",
        ["การตลาด","โฆษณา","SEO","Social Media","Copywriting","Branding",
         "Data Analytics","AI/ML","Automation","Sales","CRM","E-commerce",
         "Creative Direction","Video Production","Graphic Design","3D","Legal","Finance"],
        default=custom.get("expertise", []),
        key="edit_expertise",
        label_visibility="collapsed"
    )

    ec1, ec2, ec3 = st.columns(3)
    with ec1:
        if st.button("💾 บันทึก Persona", use_container_width=True, type="primary", key="save_persona"):
            st.session_state.ape_custom_agents[aid] = {
                "name":          new_name,
                "role":          new_role,
                "icon":          new_icon,
                "color":         new_color,
                "system_prompt": new_system,
                "tone":          new_tone,
                "expertise":     expertise_tags,
                "updated_at":    datetime.now().strftime("%d/%m/%Y %H:%M"),
            }
            # ✅ sync ลงไฟล์ → ai_team.py และทุกหน้าอ่านได้ทันที
            save_personas_to_file(st.session_state.ape_custom_agents)
            st.success(f"✅ บันทึก & Sync แล้ว — {new_name} มีผลกับ AI Team ทุกหน้าทันที!")
            st.rerun()
    with ec2:
        if st.button("🔄 รีเซ็ต Default", use_container_width=True, key="reset_persona"):
            if aid in st.session_state.ape_custom_agents:
                del st.session_state.ape_custom_agents[aid]
                # ✅ sync ลงไฟล์หลังรีเซ็ต
                save_personas_to_file(st.session_state.ape_custom_agents)
                st.success(f"✅ รีเซ็ต {persona['name']} กลับ Default แล้ว — Sync ทุกหน้าแล้ว")
                st.rerun()
    with ec3:
        if st.button("📋 Copy Prompt", use_container_width=True, key="copy_prompt"):
            st.code(new_system, language="text")

# ══════════════════════════════════════════════════════════════════
# TEST COLUMN
# ══════════════════════════════════════════════════════════════════
with col_test:
    st.markdown("<div class='section-title'>🧪 ทดสอบ Persona</div>", unsafe_allow_html=True)

    test_q = st.text_area(
        "คำถามทดสอบ",
        placeholder="ทดสอบดูว่า Agent ตอบแบบไหน เช่น 'แนะนำกลยุทธ์การตลาดสำหรับสินค้า FMCG'",
        height=100,
        key="test_question"
    )

    tc1, tc2 = st.columns(2)
    with tc1:
        if st.button("▶️ ทดสอบ Persona นี้", use_container_width=True, type="primary", key="test_btn"):
            if test_q.strip():
                cur_persona = get_current_persona(aid)
                custom_p    = st.session_state.ape_custom_agents.get(aid, {})
                sys_prompt  = custom_p.get("system_prompt", f"คุณคือ {cur_persona['name']} ผู้เชี่ยวชาญด้าน {cur_persona.get('role','')} ตอบภาษาไทย")
                with st.spinner("⏳ Agent กำลังตอบ..."):
                    result = call_agent_with_persona(sys_prompt, test_q)
                    st.session_state.ape_test_result = result
                    st.rerun()
            else:
                st.warning("⚠️ กรุณาพิมพ์คำถามก่อน")

    with tc2:
        if st.button("🔬 A/B Test vs Default", use_container_width=True, key="ab_test_btn"):
            if test_q.strip() and is_custom:
                custom_sys  = st.session_state.ape_custom_agents[aid].get("system_prompt","")
                default_sys = f"คุณคือ {DEFAULT_AGENTS[aid]['name']} ผู้เชี่ยวชาญด้าน {DEFAULT_AGENTS[aid].get('role','')} ตอบภาษาไทยกระชับ"
                with st.spinner("⏳ กำลังทดสอบ A/B..."):
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                        fa = executor.submit(call_agent_with_persona, custom_sys,  test_q)
                        fb = executor.submit(call_agent_with_persona, default_sys, test_q)
                        r_a = fa.result()
                        r_b = fb.result()
                    st.session_state.ape_ab_results = {"A": r_a, "B": r_b, "q": test_q}
                    st.rerun()
            elif not is_custom:
                st.info("💡 ต้องบันทึก Custom Persona ก่อนถึงจะ A/B Test ได้")
            else:
                st.warning("⚠️ กรุณาพิมพ์คำถามก่อน")

    # Test result
    if st.session_state.ape_test_result:
        cur_persona = get_current_persona(aid)
        st.markdown(f"""
        <div class="test-bubble">
          <div style='font-family:IBM Plex Mono,monospace;font-size:10px;color:{cur_persona.get("color","#38bdf8")};margin-bottom:8px'>
            {cur_persona.get("icon","🤖")} {cur_persona["name"]} ตอบว่า:
          </div>
          {st.session_state.ape_test_result.replace(chr(10), '<br>')}
        </div>""", unsafe_allow_html=True)

    # A/B results
    if st.session_state.ape_ab_results:
        ab = st.session_state.ape_ab_results
        st.markdown(f"""
        <div style='font-size:11px;color:#fbbf24;font-family:IBM Plex Mono,monospace;margin-top:12px;margin-bottom:6px'>
          🔬 A/B Test — คำถาม: {ab.get('q','')[:50]}
        </div>""", unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(f"""
            <div style='background:rgba(56,189,248,.06);border:1px solid rgba(56,189,248,.2);border-radius:8px;padding:12px'>
              <div style='font-family:IBM Plex Mono,monospace;font-size:10px;color:#38bdf8;margin-bottom:6px'>✏️ CUSTOM PERSONA</div>
              <div style='font-size:11px;color:#cbd5e1;line-height:1.6'>{ab['A'][:400].replace(chr(10),'<br>')}{'...' if len(ab['A'])>400 else ''}</div>
            </div>""", unsafe_allow_html=True)
        with col_b:
            st.markdown(f"""
            <div style='background:rgba(52,211,153,.06);border:1px solid rgba(52,211,153,.2);border-radius:8px;padding:12px'>
              <div style='font-family:IBM Plex Mono,monospace;font-size:10px;color:#34d399;margin-bottom:6px'>✅ DEFAULT PERSONA</div>
              <div style='font-size:11px;color:#cbd5e1;line-height:1.6'>{ab['B'][:400].replace(chr(10),'<br>')}{'...' if len(ab['B'])>400 else ''}</div>
            </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# ALL CUSTOM PERSONAS SUMMARY
# ══════════════════════════════════════════════════════════════════
if st.session_state.ape_custom_agents:
    st.markdown("<div class='section-title'>📋 Custom Personas ทั้งหมด</div>", unsafe_allow_html=True)
    for caid, cp in st.session_state.ape_custom_agents.items():
        default_info = DEFAULT_AGENTS.get(caid, {})
        col_pc, col_psel, col_pdel = st.columns([5, 1, 1])
        with col_pc:
            st.markdown(f"""
            <div class="persona-card">
              <div style='display:flex;align-items:center;gap:8px;margin-bottom:4px'>
                <span style='font-size:22px'>{cp.get("icon",default_info.get("icon","🤖"))}</span>
                <div>
                  <div class="persona-card-title">{cp.get("name",caid)}</div>
                  <div class="persona-card-meta">{caid} · อัปเดต {cp.get("updated_at","")}</div>
                </div>
              </div>
              <div class="persona-card-preview">{cp.get("system_prompt","")[:150]}{'...' if len(cp.get("system_prompt",""))>150 else ''}</div>
            </div>""", unsafe_allow_html=True)
        with col_psel:
            if st.button("✏️", key=f"goto_{caid}", help="แก้ไข Persona นี้"):
                st.session_state.ape_selected_aid = caid
                st.rerun()
        with col_pdel:
            if st.button("🗑️", key=f"del_persona_{caid}", help="ลบ Custom Persona"):
                del st.session_state.ape_custom_agents[caid]
                # ✅ sync ลงไฟล์หลังลบ
                save_personas_to_file(st.session_state.ape_custom_agents)
                st.rerun()

    # Export all custom personas
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    ec1, ec2 = st.columns(2)
    with ec1:
        export_data = json.dumps(st.session_state.ape_custom_agents, ensure_ascii=False, indent=2)
        st.download_button(
            "📥 Export Personas (JSON)",
            data=export_data,
            file_name=f"aqualine_personas_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
            use_container_width=True,
            key="export_personas_btn"
        )
    with ec2:
        uploaded = st.file_uploader("📥 Import Personas (JSON)", type=["json"], key="import_personas_up")
        if uploaded:
            try:
                imported = json.loads(uploaded.read().decode("utf-8"))
                # รองรับทั้ง format เก่า (full dict) และ format ใหม่ (มี __full__)
                if "__full__" in imported:
                    imported = imported["__full__"]
                st.session_state.ape_custom_agents.update(imported)
                # ✅ sync ลงไฟล์ทันที
                save_personas_to_file(st.session_state.ape_custom_agents)
                st.success(f"✅ Import {len(imported)} persona แล้ว — Sync ทุกหน้าแล้ว")
                st.rerun()
            except Exception as e:
                st.error(f"❌ ไฟล์ไม่ถูกต้อง: {e}")