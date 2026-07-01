import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import os
from datetime import datetime

import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ui_settings import inject_global_font_css

st.set_page_config(
    page_title="Settings & Config — AQUALINE",
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
# API KEY — Settings หน้านี้เป็นหน้าตั้งค่า จึงไม่ stop ถ้าไม่มี key
# ══════════════════════════════════════════════════════════════════
STORED_KEY      = st.secrets.get("GOOGLE_API_KEY", "")
STORED_CLAUDE   = st.secrets.get("ANTHROPIC_API_KEY", "")
STORED_ANDRO_ENG = st.secrets.get("ANDROMEDA_ENGINE", "gemini")

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

.setting-card{background:rgba(15,23,42,.8);border:1px solid #1e293b;border-radius:12px;padding:20px;margin-bottom:12px;}
.setting-card-title{font-family:'IBM Plex Mono',monospace;font-size:13px;font-weight:700;color:#e2e8f0;margin-bottom:4px;}
.setting-card-desc{font-size:11px;color:#475569;margin-bottom:12px;}

.model-badge{display:inline-block;padding:3px 10px;border-radius:12px;font-size:11px;
  font-family:'IBM Plex Mono',monospace;border:1px solid;margin:2px;}
.status-ok{color:#34d399;border-color:#34d399;background:rgba(52,211,153,.08);}
.status-err{color:#f87171;border-color:#f87171;background:rgba(248,113,113,.08);}
.status-warn{color:#fbbf24;border-color:#fbbf24;background:rgba(251,191,36,.08);}

.info-row{display:flex;align-items:center;justify-content:space-between;
  padding:8px 0;border-bottom:1px solid rgba(30,41,59,.5);font-size:12px;}
.info-key{color:#475569;font-family:'IBM Plex Mono',monospace;font-size:11px;}
.info-val{color:#94a3b8;font-family:'IBM Plex Mono',monospace;font-size:11px;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# SESSION STATE — เก็บ config ทั้งหมด
# ══════════════════════════════════════════════════════════════════
DEFAULTS = {
    "cfg_default_model":        "gemini-2.5-flash-preview-05-20",
    "cfg_temperature":          0.7,
    "cfg_max_tokens":           8192,
    "cfg_top_p":                0.9,
    "cfg_default_agents":       ["A1","A3","A11"],
    "cfg_default_mode":         "ทีมช่วยกันตอบ",
    "cfg_max_agents_per_turn":  3,
    "cfg_lang":                 "ภาษาไทย",
    "cfg_theme":                "Dark (Default)",
    "cfg_font_size":            "ปกติ (13px)",
    "cfg_show_timestamps":      True,
    "cfg_auto_scroll":          True,
    "cfg_sound_notify":         False,
    "cfg_file_size_limit":      50,
    "cfg_url_auto_read":        True,
    "cfg_url_limit_per_msg":    5,
    "cfg_export_format":        "Markdown",
    "cfg_backup_data":          {},
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════
def test_api_key(key: str) -> tuple[bool, str, list]:
    try:
        r = requests.get(
            f"https://generativelanguage.googleapis.com/v1beta/models?key={key}",
            timeout=10
        )
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])
                      if "generateContent" in m.get("supportedGenerationMethods", [])]
            return True, f"✅ Key ถูกต้อง — พบ {len(models)} โมเดล", models
        elif r.status_code == 400:
            return False, "❌ API Key ไม่ถูกต้อง", []
        elif r.status_code == 403:
            return False, "❌ Key ไม่มีสิทธิ์ใช้ API นี้", []
        else:
            return False, f"❌ HTTP {r.status_code}", []
    except Exception as e:
        return False, f"❌ เชื่อมต่อไม่ได้: {str(e)[:60]}", []

def get_all_session_data() -> dict:
    """รวบรวม session data ทั้งหมดสำหรับ backup"""
    return {
        "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "lc_messages":       st.session_state.get("lc_messages", []),
        "dash_projects":     st.session_state.get("dash_projects", []),
        "dash_costs":        st.session_state.get("dash_costs", {}),
        "bcm_expenses":      st.session_state.get("bcm_expenses", []),
        "bcm_budget_limit":  st.session_state.get("bcm_budget_limit", 5000.0),
        "rg_reports":        st.session_state.get("rg_reports", []),
        "ape_custom_agents": st.session_state.get("ape_custom_agents", {}),
        "config": {k: st.session_state.get(k) for k in DEFAULTS.keys()},
    }

# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("<style>[data-testid='stSidebarNav']{display:none}</style>", unsafe_allow_html=True)
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
    # Quick status
    key_ok = bool(STORED_KEY)
    st.markdown(f"""
    <div style='padding:8px 12px;background:rgba(15,23,42,.8);border:1px solid #1e293b;border-radius:8px;font-size:11px'>
      <div style='color:{"#34d399" if key_ok else "#f87171"};font-family:IBM Plex Mono,monospace'>
        {"✅ API Key พร้อมใช้" if key_ok else "❌ ไม่พบ API Key"}
      </div>
      <div style='color:#334155;font-family:IBM Plex Mono,monospace;margin-top:3px'>
        Model: {st.session_state.cfg_default_model[:20]}
      </div>
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<div class="page-header">
  <div style='font-size:36px'>⚙️</div>
  <div>
    <div class="page-title">SETTINGS & CONFIG</div>
    <div class="page-sub">ตั้งค่า API Key · โมเดล AI · ภาษา · Export/Import · Backup</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════
tab_api, tab_model, tab_agent, tab_ui, tab_data = st.tabs([
    "🔑 API & Keys", "🤖 โมเดล AI", "👥 Agent Default", "🎨 UI & Display", "💾 ข้อมูล & Backup"
])

# ══════════════════════════════════════════════════════════════════
# TAB 1 — API & KEYS
# ══════════════════════════════════════════════════════════════════
with tab_api:
    st.markdown("<div class='section-title'>🔑 Google Gemini API</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="setting-card">
      <div class="setting-card-title">API Key Configuration</div>
      <div class="setting-card-desc">
        Key ถูกเก็บใน <code style='color:#38bdf8'>.streamlit/secrets.toml</code> — ปลอดภัยและไม่ถูก expose ใน code
      </div>
    </div>""", unsafe_allow_html=True)

    # Show masked key
    if STORED_KEY:
        masked = STORED_KEY[:8] + "••••••••••••••••" + STORED_KEY[-4:]
        st.markdown(f"""
        <div style='background:rgba(52,211,153,.06);border:1px solid rgba(52,211,153,.2);border-radius:8px;
          padding:12px 16px;font-family:IBM Plex Mono,monospace;font-size:12px;color:#34d399;margin-bottom:12px'>
          ✅ พบ API Key: {masked}
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='background:rgba(248,113,113,.06);border:1px solid rgba(248,113,113,.2);border-radius:8px;
          padding:12px 16px;font-family:IBM Plex Mono,monospace;font-size:12px;color:#f87171;margin-bottom:12px'>
          ❌ ไม่พบ GOOGLE_API_KEY ใน secrets.toml
        </div>""", unsafe_allow_html=True)

    # Test key
    test_key_input = st.text_input(
        "ทดสอบ API Key (ไม่บังคับ)",
        type="password",
        placeholder="วาง API Key ที่ต้องการทดสอบ",
        key="test_key_inp"
    )
    if st.button("🔍 ทดสอบ Key", key="test_key_btn"):
        key_to_test = test_key_input.strip() or STORED_KEY
        if key_to_test:
            with st.spinner("กำลังทดสอบ..."):
                ok, msg, models = test_api_key(key_to_test)
            if ok:
                st.success(msg)
                st.markdown("<div style='font-size:11px;color:#475569;font-family:IBM Plex Mono,monospace;margin-top:6px'>โมเดลที่ใช้ได้:</div>", unsafe_allow_html=True)
                model_html = "".join([f"<span class='model-badge status-ok'>{m.replace('models/','')}</span>" for m in models[:12]])
                st.markdown(f"<div>{model_html}</div>", unsafe_allow_html=True)
            else:
                st.error(msg)
        else:
            st.warning("⚠️ กรุณาใส่ API Key ก่อน")

    # How to get key
    with st.expander("📖 วิธีขอ Google Gemini API Key"):
        st.markdown("""
        <div style='font-size:12px;color:#94a3b8;line-height:1.8'>
        1. ไปที่ <a href='https://aistudio.google.com/app/apikey' target='_blank' style='color:#38bdf8'>Google AI Studio</a><br>
        2. คลิก <b>Create API Key</b><br>
        3. เลือก Project หรือสร้างใหม่<br>
        4. Copy key แล้วเพิ่มใน <code style='color:#38bdf8'>.streamlit/secrets.toml</code>:<br>
        <pre style='background:rgba(30,41,59,.6);padding:10px;border-radius:6px;margin-top:6px;
          font-family:IBM Plex Mono,monospace;font-size:11px;color:#34d399'>GOOGLE_API_KEY = "AIza..."</pre>
        5. Restart Streamlit server
        </div>""", unsafe_allow_html=True)

    # ── Claude / Anthropic API Section ──────────────────────────────
    st.markdown("<div class='section-title'>🟣 Anthropic Claude API</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="setting-card">
      <div class="setting-card-title">Claude API Key</div>
      <div class="setting-card-desc">
        ใช้โดย <b>Chairman Master</b> และ <b>Andromeda (Claude Mode)</b> — เก็บใน <code style='color:#a78bfa'>.streamlit/secrets.toml</code>
      </div>
    </div>""", unsafe_allow_html=True)

    if STORED_CLAUDE:
        masked_c = STORED_CLAUDE[:10] + "••••••••••" + STORED_CLAUDE[-4:]
        st.markdown(f"""
        <div style='background:rgba(167,139,250,.06);border:1px solid rgba(167,139,250,.2);border-radius:8px;
          padding:12px 16px;font-family:IBM Plex Mono,monospace;font-size:12px;color:#a78bfa;margin-bottom:12px'>
          ✅ พบ Claude Key: {masked_c}
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='background:rgba(248,113,113,.06);border:1px solid rgba(248,113,113,.2);border-radius:8px;
          padding:12px 16px;font-family:IBM Plex Mono,monospace;font-size:12px;color:#f87171;margin-bottom:12px'>
          ❌ ไม่พบ ANTHROPIC_API_KEY — Chairman Master ใช้งานไม่ได้
        </div>""", unsafe_allow_html=True)

    test_claude_inp = st.text_input(
        "ทดสอบ Claude Key (ไม่บังคับ)", type="password",
        placeholder="sk-ant-api03-...", key="test_claude_inp"
    )
    if st.button("🔍 ทดสอบ Claude Key", key="test_claude_btn"):
        key_c = test_claude_inp.strip() or STORED_CLAUDE
        if key_c:
            with st.spinner("ทดสอบ Claude API..."):
                try:
                    r = requests.post(
                        "https://api.anthropic.com/v1/messages",
                        headers={"x-api-key": key_c, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                        json={"model": "claude-haiku-4-5", "max_tokens": 32,
                              "messages": [{"role": "user", "content": "Say OK"}]},
                        timeout=15
                    )
                    if r.status_code == 200:
                        st.success("✅ Claude Key ถูกต้อง — claude-haiku-4-5 พร้อมใช้งาน")
                    else:
                        st.error(f"❌ Claude Error {r.status_code}: {r.text[:200]}")
                except Exception as e:
                    st.error(f"❌ Connection Error: {str(e)[:80]}")
        else:
            st.warning("⚠️ ไม่พบ Claude Key")

    with st.expander("📖 วิธีขอ Anthropic Claude API Key"):
        st.markdown("""
        <div style='font-size:12px;color:#94a3b8;line-height:1.8'>
        1. ไปที่ <a href='https://console.anthropic.com/' target='_blank' style='color:#a78bfa'>console.anthropic.com</a><br>
        2. Login แล้วไปที่ <b>API Keys</b><br>
        3. คลิก <b>Create Key</b><br>
        4. Copy key แล้วเพิ่มใน <code style='color:#a78bfa'>.streamlit/secrets.toml</code>:<br>
        <pre style='background:rgba(30,41,59,.6);padding:10px;border-radius:6px;margin-top:6px;
          font-family:IBM Plex Mono,monospace;font-size:11px;color:#a78bfa'>ANTHROPIC_API_KEY = "sk-ant-api03-..."</pre>
        5. Restart Streamlit server
        </div>""", unsafe_allow_html=True)

    # ── Andromeda Engine Selector ─────────────────────────────────────
    st.markdown("<div class='section-title'>🔭 Andromeda Engine Configuration</div>", unsafe_allow_html=True)

    st.markdown("""
    <div class="setting-card">
      <div class="setting-card-title">เลือก AI Engine สำหรับ Andromeda Pre-Meeting Auditor</div>
      <div class="setting-card-desc">ตั้งค่าใน <code style='color:#38bdf8'>.streamlit/secrets.toml</code> หรือเลือกชั่วคราวด้านล่าง</div>
    </div>""", unsafe_allow_html=True)

    eng_opts  = ["gemini", "claude", "both"]
    eng_labels = {"gemini": "🔵 Gemini Vision (เร็ว + ฟรี)",
                  "claude": "🟣 Claude Vision (แม่นยำ + วิเคราะห์ลึก)",
                  "both":   "⚡ Both — Dual Analysis (ใช้ทั้ง 2 engine พร้อมกัน)"}
    current_eng = STORED_ANDRO_ENG if STORED_ANDRO_ENG in eng_opts else "gemini"
    chosen_eng = st.radio(
        "Andromeda Engine:",
        eng_opts,
        index=eng_opts.index(current_eng),
        format_func=lambda x: eng_labels[x],
        horizontal=True,
        key="andro_eng_radio"
    )
    st.markdown(f"""
    <div style='background:rgba(15,23,42,.8);border:1px solid #1e293b;border-radius:8px;padding:12px 16px;
      font-size:12px;color:#64748b;font-family:IBM Plex Mono,monospace;margin-top:6px'>
      💡 เพื่อให้ถาวร เพิ่มบรรทัดนี้ใน <code style='color:#38bdf8'>.streamlit/secrets.toml</code>:<br>
      <span style='color:#34d399'>ANDROMEDA_ENGINE = "{chosen_eng}"</span>
    </div>""", unsafe_allow_html=True)

    # ── System Info ───────────────────────────────────────────────────
    st.markdown("<div class='section-title'>📊 ข้อมูลระบบ</div>", unsafe_allow_html=True)
    sys_info = [
        ("Streamlit", st.__version__),
        ("Python", f"{__import__('sys').version.split()[0]}"),
        ("App Version", "AQUALINE v9.1 — Andromeda Edition"),
        ("หน้าทั้งหมด", "17 หน้า (+Andromeda)"),
        ("Agent ในระบบ", "26 Agent + Chairman"),
        ("Gemini API", "✅ Ready" if STORED_KEY else "❌ No Key"),
        ("Claude API", "✅ Ready" if STORED_CLAUDE else "❌ No Key"),
        ("Andromeda Engine", eng_labels.get(current_eng, current_eng)),
        ("เวลาปัจจุบัน", datetime.now().strftime("%d/%m/%Y %H:%M")),
    ]
    for key, val in sys_info:
        st.markdown(f"""
        <div class="info-row">
          <span class="info-key">{key}</span>
          <span class="info-val">{val}</span>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# TAB 2 — MODEL SETTINGS
# ══════════════════════════════════════════════════════════════════
with tab_model:
    st.markdown("<div class='section-title'>🤖 เลือกโมเดล AI หลัก</div>", unsafe_allow_html=True)

    # Auto-detect available models
    available_models = []
    if STORED_KEY:
        try:
            r = requests.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={STORED_KEY}", timeout=8)
            if r.status_code == 200:
                available_models = [m["name"].replace("models/","") for m in r.json().get("models",[])
                                    if "generateContent" in m.get("supportedGenerationMethods",[])]
        except:
            pass

    model_options = available_models if available_models else [
        "gemini-2.5-flash-preview-05-20", "gemini-2.5-flash",
        "gemini-1.5-flash-latest", "gemini-1.5-flash",
        "gemini-1.5-pro-latest", "gemini-1.0-pro",
    ]

    preferred = ["gemini-2.5-flash-preview-05-20","gemini-2.5-flash","gemini-1.5-flash-latest","gemini-1.5-flash"]
    sorted_models = sorted(model_options, key=lambda x: (preferred.index(x) if x in preferred else 99, x))

    current_model = st.session_state.cfg_default_model
    if current_model not in sorted_models:
        sorted_models.insert(0, current_model)

    st.markdown("""
    <div class="setting-card">
      <div class="setting-card-title">Default Model</div>
      <div class="setting-card-desc">โมเดลที่ใช้กับทุกหน้า — แนะนำ gemini-2.5-flash-preview เพื่อประสิทธิภาพสูงสุด</div>
    </div>""", unsafe_allow_html=True)

    st.session_state.cfg_default_model = st.selectbox(
        "Default Model",
        sorted_models,
        index=sorted_models.index(current_model) if current_model in sorted_models else 0,
        key="model_sel",
        label_visibility="collapsed"
    )

    # Model info cards
    model_info = {
        "gemini-2.5-flash-preview-05-20": ("⚡ เร็วสุด · คุณภาพสูง · ราคาถูก", "#38bdf8", "แนะนำ"),
        "gemini-2.5-flash":               ("⚡ เร็ว · สมดุลดี", "#38bdf8", ""),
        "gemini-1.5-flash-latest":        ("🔄 เสถียร · ทดสอบแล้ว", "#34d399", ""),
        "gemini-1.5-pro-latest":          ("🔮 ทรงพลัง · ช้ากว่า · แพงกว่า", "#a78bfa", ""),
        "gemini-1.0-pro":                 ("📦 Legacy · เสถียรมาก", "#94a3b8", ""),
    }
    sel_model_key = st.session_state.cfg_default_model
    if sel_model_key in model_info:
        desc, color, badge = model_info[sel_model_key]
        st.markdown(f"""
        <div style='background:rgba(15,23,42,.6);border:1px solid {color}30;border-radius:8px;padding:10px 14px;margin-top:4px'>
          <span style='font-family:IBM Plex Mono,monospace;font-size:11px;color:{color}'>{desc}</span>
          {"<span class='model-badge status-ok' style='margin-left:8px'>⭐ แนะนำ</span>" if badge else ""}
        </div>""", unsafe_allow_html=True)

    st.markdown("<div class='section-title'>⚙️ ค่า Generation Config</div>", unsafe_allow_html=True)
    gc1, gc2, gc3 = st.columns(3)
    with gc1:
        st.session_state.cfg_temperature = st.slider(
            "Temperature", 0.0, 1.0, st.session_state.cfg_temperature, 0.05,
            help="สูง = สร้างสรรค์มากขึ้น, ต่ำ = แม่นยำมากขึ้น",
            key="temp_slider"
        )
    with gc2:
        st.session_state.cfg_max_tokens = st.select_slider(
            "Max Output Tokens",
            options=[1024, 2048, 4096, 8192, 16384, 32768],
            value=st.session_state.cfg_max_tokens,
            key="tokens_slider"
        )
    with gc3:
        st.session_state.cfg_top_p = st.slider(
            "Top-P", 0.5, 1.0, st.session_state.cfg_top_p, 0.05,
            key="top_p_slider"
        )

    temp_desc = "สร้างสรรค์มาก" if st.session_state.cfg_temperature > 0.8 else \
                "สร้างสรรค์" if st.session_state.cfg_temperature > 0.6 else \
                "สมดุล" if st.session_state.cfg_temperature > 0.4 else "แม่นยำ"
    st.markdown(f"""
    <div style='font-size:11px;color:#475569;font-family:IBM Plex Mono,monospace;text-align:center;margin-top:4px'>
      Temperature: {temp_desc} · Tokens: {st.session_state.cfg_max_tokens:,} · Top-P: {st.session_state.cfg_top_p}
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# TAB 3 — AGENT DEFAULTS
# ══════════════════════════════════════════════════════════════════
with tab_agent:
    st.markdown("<div class='section-title'>👥 ตั้งค่า Agent เริ่มต้น</div>", unsafe_allow_html=True)

    # AGENTS_LIST ดึงจาก AGENT_META (agent_default_personas.py) — single source of truth
    # เพิ่ม/แก้ agent ที่ AGENT_META ที่เดียว หน้านี้จะเห็นผลตามอัตโนมัติ (รวม A26)
    import sys as _sys
    _sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from agent_default_personas import AGENT_META

    AGENTS_LIST = {aid: f'{m["icon"]} {m["name"]}' for aid, m in AGENT_META.items()}

    st.session_state.cfg_default_agents = st.multiselect(
        "Agent ที่เปิดใช้งานเมื่อเริ่มต้น",
        list(AGENTS_LIST.keys()),
        default=st.session_state.cfg_default_agents,
        format_func=lambda x: AGENTS_LIST[x],
        key="default_agents_sel"
    )

    ac1, ac2 = st.columns(2)
    with ac1:
        st.session_state.cfg_default_mode = st.selectbox(
            "โหมดตอบเริ่มต้น",
            ["ทีมช่วยกันตอบ","ตอบทีละคน (Round Robin)","ตอบพร้อมกันทั้งทีม"],
            index=["ทีมช่วยกันตอบ","ตอบทีละคน (Round Robin)","ตอบพร้อมกันทั้งทีม"].index(st.session_state.cfg_default_mode),
            key="default_mode_sel"
        )
    with ac2:
        st.session_state.cfg_max_agents_per_turn = st.slider(
            "จำนวน Agent ตอบต่อคำถาม", 1, 8,
            st.session_state.cfg_max_agents_per_turn,
            key="max_agents_cfg"
        )

    # File settings
    st.markdown("<div class='section-title'>📎 ไฟล์แนบ & URL</div>", unsafe_allow_html=True)
    fa1, fa2 = st.columns(2)
    with fa1:
        st.session_state.cfg_file_size_limit = st.slider(
            "ขนาดไฟล์สูงสุด (MB)", 10, 200,
            st.session_state.cfg_file_size_limit, key="file_size_cfg"
        )
        st.session_state.cfg_url_auto_read = st.toggle(
            "อ่าน URL อัตโนมัติ", st.session_state.cfg_url_auto_read, key="url_auto_cfg"
        )
    with fa2:
        st.session_state.cfg_url_limit_per_msg = st.slider(
            "จำนวน URL สูงสุดต่อข้อความ", 1, 10,
            st.session_state.cfg_url_limit_per_msg, key="url_limit_cfg"
        )

# ══════════════════════════════════════════════════════════════════
# TAB 4 — UI & DISPLAY
# ══════════════════════════════════════════════════════════════════
with tab_ui:
    st.markdown("<div class='section-title'>🎨 การแสดงผล</div>", unsafe_allow_html=True)

    ui1, ui2 = st.columns(2)
    with ui1:
        st.session_state.cfg_lang = st.selectbox(
            "ภาษาเริ่มต้น",
            ["ภาษาไทย","English","ไทย-อังกฤษ (Mixed)"],
            index=["ภาษาไทย","English","ไทย-อังกฤษ (Mixed)"].index(st.session_state.cfg_lang),
            key="lang_sel"
        )
        st.session_state.cfg_font_size = st.selectbox(
            "ขนาดตัวอักษร",
            ["เล็ก (11px)","ปกติ (13px)","ใหญ่ (15px)","ใหญ่มาก (17px)"],
            index=["เล็ก (11px)","ปกติ (13px)","ใหญ่ (15px)","ใหญ่มาก (17px)"].index(st.session_state.cfg_font_size),
            key="font_sel"
        )
    with ui2:
        st.session_state.cfg_show_timestamps = st.toggle(
            "แสดงเวลาในแชท", st.session_state.cfg_show_timestamps, key="ts_toggle"
        )
        st.session_state.cfg_auto_scroll = st.toggle(
            "Auto-scroll ไปข้อความล่าสุด", st.session_state.cfg_auto_scroll, key="scroll_toggle"
        )
        st.session_state.cfg_sound_notify = st.toggle(
            "เสียงแจ้งเตือนเมื่อ Agent ตอบ", st.session_state.cfg_sound_notify, key="sound_toggle"
        )

    st.markdown("<div class='section-title'>📥 Export Format</div>", unsafe_allow_html=True)
    st.session_state.cfg_export_format = st.radio(
        "รูปแบบ Export แชท",
        ["Markdown","JSON","ทั้งสองรูปแบบ"],
        index=["Markdown","JSON","ทั้งสองรูปแบบ"].index(st.session_state.cfg_export_format),
        horizontal=True,
        key="export_fmt_radio"
    )

    # Preview font size
    font_px = {"เล็ก (11px)":11,"ปกติ (13px)":13,"ใหญ่ (15px)":15,"ใหญ่มาก (17px)":17}
    px = font_px.get(st.session_state.cfg_font_size, 13)
    st.markdown(f"""
    <div style='background:rgba(15,23,42,.8);border:1px solid #1e293b;border-radius:8px;padding:14px;margin-top:8px'>
      <div style='font-size:10px;color:#334155;font-family:IBM Plex Mono,monospace;margin-bottom:6px'>Preview:</div>
      <div style='font-size:{px}px;color:#cbd5e1;line-height:1.7'>
        สวัสดีครับ นี่คือตัวอย่างข้อความขนาด {px}px — AQUALINE AI TEAM พร้อมช่วยเหลือคุณทุกด้านครับ
      </div>
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# TAB 5 — DATA & BACKUP
# ══════════════════════════════════════════════════════════════════
with tab_data:
    st.markdown("<div class='section-title'>💾 Backup & Export ข้อมูล</div>", unsafe_allow_html=True)

    backup_data = get_all_session_data()
    backup_json = json.dumps(backup_data, ensure_ascii=False, indent=2, default=str)

    col_b1, col_b2 = st.columns(2)
    with col_b1:
        st.markdown("""
        <div class="setting-card">
          <div class="setting-card-title">📥 Export ข้อมูลทั้งหมด</div>
          <div class="setting-card-desc">รวม Chat, Projects, Expenses, Reports, Custom Personas และ Config ทั้งหมด</div>
        </div>""", unsafe_allow_html=True)
        st.download_button(
            "💾 Download Backup (JSON)",
            data=backup_json,
            file_name=f"aqualine_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True,
            key="backup_dl_btn"
        )

    with col_b2:
        st.markdown("""
        <div class="setting-card">
          <div class="setting-card-title">📤 Import / Restore</div>
          <div class="setting-card-desc">โหลด Backup กลับเข้า session — ข้อมูลปัจจุบันจะถูกแทนที่</div>
        </div>""", unsafe_allow_html=True)
        restore_file = st.file_uploader("เลือกไฟล์ Backup", type=["json"], key="restore_file_up")
        if restore_file:
            try:
                imported = json.loads(restore_file.read().decode("utf-8"))
                st.markdown(f"""
                <div style='font-size:11px;color:#fbbf24;font-family:IBM Plex Mono,monospace;margin-bottom:8px'>
                  ⚠️ จะ Restore: Chat {len(imported.get('lc_messages',[]))} ข้อความ,
                  Projects {len(imported.get('dash_projects',[]))},
                  Expenses {len(imported.get('bcm_expenses',[]))},
                  Reports {len(imported.get('rg_reports',[]))}
                </div>""", unsafe_allow_html=True)
                if st.button("✅ Restore ข้อมูล", use_container_width=True, type="primary", key="restore_btn"):
                    for key in ["lc_messages","dash_projects","dash_costs","bcm_expenses",
                                "bcm_budget_limit","rg_reports","ape_custom_agents"]:
                        if key in imported:
                            st.session_state[key] = imported[key]
                    if "config" in imported:
                        for k, v in imported["config"].items():
                            st.session_state[k] = v
                    st.success("✅ Restore สำเร็จ!")
                    st.rerun()
            except Exception as e:
                st.error(f"❌ ไฟล์ไม่ถูกต้อง: {str(e)[:80]}")

    # Data summary
    st.markdown("<div class='section-title'>📊 สรุปข้อมูลใน Session</div>", unsafe_allow_html=True)
    data_rows = [
        ("💬 ข้อความใน Live Chat", len(st.session_state.get("lc_messages", []))),
        ("🗂️ Projects", len(st.session_state.get("dash_projects", []))),
        ("💰 รายการค่าใช้จ่าย", len(st.session_state.get("bcm_expenses", []))),
        ("📄 รายงาน", len(st.session_state.get("rg_reports", []))),
        ("🧬 Custom Personas", len(st.session_state.get("ape_custom_agents", {}))),
    ]
    for label, count in data_rows:
        st.markdown(f"""
        <div class="info-row">
          <span class="info-key">{label}</span>
          <span class="info-val" style='color:{"#38bdf8" if count > 0 else "#334155"}'>{count} รายการ</span>
        </div>""", unsafe_allow_html=True)

    # Clear all data
    st.markdown("<div class='section-title'>🗑️ ล้างข้อมูล</div>", unsafe_allow_html=True)
    st.warning("⚠️ การล้างข้อมูลไม่สามารถย้อนกลับได้ — แนะนำ Backup ก่อนทุกครั้ง")

    clr1, clr2, clr3, clr4 = st.columns(4)
    with clr1:
        if st.button("🗑️ ล้าง Chat", use_container_width=True, key="clr_chat"):
            st.session_state.lc_messages = []
            st.success("✅ ล้าง Chat แล้ว")
    with clr2:
        if st.button("🗑️ ล้าง Expenses", use_container_width=True, key="clr_exp"):
            st.session_state.bcm_expenses = []
            st.success("✅ ล้าง Expenses แล้ว")
    with clr3:
        if st.button("🗑️ ล้าง Reports", use_container_width=True, key="clr_rep"):
            st.session_state.rg_reports = []
            st.success("✅ ล้าง Reports แล้ว")
    with clr4:
        if st.button("💣 ล้างทั้งหมด", use_container_width=True, key="clr_all_data", type="primary"):
            for key in ["lc_messages","dash_projects","dash_costs","bcm_expenses",
                        "rg_reports","ape_custom_agents","lc_reactions","lc_url_contents"]:
                st.session_state[key] = {} if "costs" in key or "contents" in key or "agents" in key else []
            st.success("✅ ล้างข้อมูลทั้งหมดแล้ว")
            st.rerun()