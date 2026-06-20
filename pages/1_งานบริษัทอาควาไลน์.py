import streamlit as st
import streamlit.components.v1 as components
import requests, json, os, time
from datetime import datetime
import pdfplumber
from docx import Document

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agent_default_personas import AGENT_META, DEPARTMENTS, get_agents_by_department, get_department_ids
from kg_widget import render_full_graph, FULL_EXTRA_PX
from ui_settings import get_kg_theme, inject_global_font_css
import product_knowledge as pk
import google_drive_integration as gd
import meeting_engine
import secretary_state
import usage_logger

st.set_page_config(page_title="งานบริษัทอาควาไลน์ — AQUALINE AI TEAM", layout="wide", initial_sidebar_state="expanded")

# 🔐 กันเข้าหน้านี้ตรงผ่าน URL โดยไม่ผ่านด่านล็อกอินที่หน้าแรก
from auth_guard import require_auth
require_auth()

# ฟอนต์/ขนาดตัวอักษรที่ผู้ใช้กำหนดเอง (หน้า Design UX/UI) — ใช้ร่วมกันทุกหน้า
st.markdown(inject_global_font_css(), unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# 🧭 FRESH-VISIT DETECTOR — ต้องเช็กก่อนตั้งค่า marker ของหน้าตัวเองเสมอ
# ถ้าหน้าก่อนหน้านี้ (_active_page) ไม่ใช่ไฟล์นี้ แปลว่าผู้ใช้ "เพิ่งเปิดหน้านี้เข้ามาใหม่"
# (ไม่ใช่แค่ rerun ภายในหน้าเดิมจากการกดปุ่ม/ฟอร์ม) → ใช้เป็นตัวสั่ง trigger งานวิจัยคู่แข่งอัตโนมัติ
# ══════════════════════════════════════════════════════════════════
_prev_active_page = st.session_state.get("_active_page")
IS_FRESH_VISIT = (_prev_active_page != __file__)
st.session_state["_active_page"] = __file__

# ══════════════════════════════════════════════════════════════════
# API KEY
# ══════════════════════════════════════════════════════════════════
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("🔑 ไม่พบ GOOGLE_API_KEY ใน secrets.toml")
    st.stop()

# ══════════════════════════════════════════════════════════════════
# 🏢 COMPANY INFO — เก็บถาวรใน company_info.json
# ══════════════════════════════════════════════════════════════════
COMPANY_FILE = "company_info.json"

DEFAULT_COMPANY = {
    "name": "AQUALINE",
    "website": "https://aqualine.co.th",
    "business": "ผลิตและจำหน่ายหลังคาเมทัลชีท รางน้ำฝน และถังเก็บน้ำ ครบวงจรทั้งสินค้าและบริการติดตั้ง",
    "products": "หลังคาเมทัลชีท, รางน้ำฝน PVC/สแตนเลส, ถังเก็บน้ำบนดิน/ใต้ดิน, อุปกรณ์เสริมหลังคา",
    "target": "เจ้าของบ้าน, ผู้รับเหมา/ช่าง, ร้านวัสดุก่อสร้าง, โครงการบ้านจัดสรร",
    "strength": "คุณภาพวัสดุมาตรฐานสูง, การรับประกันยาว, บริการติดตั้งครบวงจร, ทีมช่างมีประสบการณ์",
    "region": "ประเทศไทย",
    "known_competitors": "",
}

def load_company_info() -> dict:
    info = dict(DEFAULT_COMPANY)
    if os.path.exists(COMPANY_FILE):
        try:
            with open(COMPANY_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            if isinstance(saved, dict):
                info.update(saved)
        except Exception:
            pass
    return info

def save_company_info(info: dict):
    with open(COMPANY_FILE, "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=2)

company = load_company_info()
_company_file_exists = os.path.exists(COMPANY_FILE)

# ══════════════════════════════════════════════════════════════════
# 🤖 GEMINI HELPERS — รูปแบบเดียวกับ pages/15_KONEX.py (Google Search Grounding)
# ══════════════════════════════════════════════════════════════════
@st.cache_data(ttl=300, show_spinner=False)
def get_model(k: str) -> str:
    try:
        r = requests.get(
            f"https://generativelanguage.googleapis.com/v1beta/models?key={k}",
            timeout=10
        )
        if r.status_code == 200:
            avail = [m["name"] for m in r.json().get("models", [])
                     if "generateContent" in m.get("supportedGenerationMethods", [])]
            for p in ["models/gemini-2.5-flash-preview-05-20", "models/gemini-2.5-flash",
                      "models/gemini-1.5-flash-latest", "models/gemini-1.5-flash"]:
                if p in avail:
                    return p
    except Exception:
        pass
    return "models/gemini-1.5-flash"

def _call_gemini_api(payload: dict, timeout: int = 90, max_retries: int = 3) -> str:
    model = get_model(API_KEY)
    url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={API_KEY}"
    for attempt in range(max_retries):
        try:
            resp = requests.post(url, json=payload, timeout=timeout)
            if resp.status_code == 200:
                return resp.json()["candidates"][0]["content"]["parts"][0].get("text", "").strip()
            elif resp.status_code == 429:
                time.sleep(2 ** (attempt + 1))
                continue
            else:
                return f"⚠️ API Error {resp.status_code}: {resp.text[:200]}"
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            return "⚠️ API Timeout — กรุณาลองใหม่"
        except requests.exceptions.ConnectionError:
            return "⚠️ เชื่อมต่อ API ไม่ได้ — ตรวจสอบ internet"
        except (KeyError, IndexError, ValueError) as e:
            return f"⚠️ Parse response ผิดพลาด: {e}"
        except Exception as e:
            return f"⚠️ Unexpected error: {str(e)[:100]}"
    return "⚠️ เรียก API ไม่สำเร็จหลัง retry 3 ครั้ง"

def run_a26_competitor_research(co: dict, topic: str = "") -> str:
    """🕵️ A26 — ฝ่ายเจาะข้อมูลคู่แข่ง: ค้นข้อมูลคู่แข่งจริงผ่าน Google Search Grounding"""
    ctx = f"""ชื่อบริษัท: {co['name']}
เว็บไซต์: {co['website']}
ลักษณะธุรกิจ: {co['business']}
สินค้า/บริการหลัก: {co['products']}
กลุ่มลูกค้าเป้าหมาย: {co['target']}
จุดแข็ง/USP: {co['strength']}
ตลาด/พื้นที่ให้บริการ: {co['region']}
คู่แข่งที่รู้จักอยู่แล้ว: {co['known_competitors'] or 'ไม่ระบุ — ให้ค้นหาเอง'}
หัวข้อพิเศษที่ผู้ใช้ต้องการให้เจาะลึกเป็นพิเศษ: {topic.strip() or 'ไม่ระบุ — ให้ค้นหาภาพรวมตามบริบทบริษัทด้านบน'}"""

    prompt = f"""คุณคือ "ฝ่ายเจาะข้อมูลคู่แข่ง" (Competitor Intelligence) ของบริษัทนี้:

{ctx}

ภารกิจ: ใช้ Google Search ค้นหาข้อมูลคู่แข่งจริงในตลาดปัจจุบันที่แข่งขันโดยตรงกับบริษัทนี้ (อย่างน้อย 3-5 ราย)
ถ้ามี "หัวข้อพิเศษที่ผู้ใช้ต้องการให้เจาะลึก" ด้านบน ให้ให้ความสำคัญกับหัวข้อนั้นเป็นอันดับแรกในการค้นหาและสรุปผล
สำหรับคู่แข่งแต่ละราย สรุปให้ครบ:
1. ชื่อบริษัท/แบรนด์
2. จุดแข็ง-จุดอ่อน
3. ราคา/โปรโมชันที่สังเกตได้ (ถ้าหาข้อมูลได้)
4. ช่องทางการขาย/การตลาดที่ใช้
5. ช่องว่างในตลาดที่เราใช้แข่งได้

ปิดท้ายด้วย "สรุปกลยุทธ์แนะนำ" 2-3 ข้อ
ตอบเป็นภาษาไทย จัดรูปแบบ Markdown หัวข้อชัดเจน ห้ามแต่งข้อมูลเท็จ ถ้าหาไม่พบให้ระบุว่า "ไม่พบข้อมูลที่ยืนยันได้\""""

    return _call_gemini_api(
        payload={
            "contents": [{"parts": [{"text": prompt}]}],
            "tools": [{"google_search": {}}],
            "generationConfig": {"temperature": 0.3, "maxOutputTokens": 4096},
        },
        timeout=90,
    )

# ══════════════════════════════════════════════════════════════════
# 🔄 MANUAL-TRIGGER STATE — A26 จะเริ่มค้นหาเฉพาะตอนผู้ใช้กดปุ่มเท่านั้น
# ══════════════════════════════════════════════════════════════════
RESEARCH_RESULT_KEY = "a26_research_result"
RESEARCH_TS_KEY     = "a26_research_ts"
RESEARCH_STATUS_KEY = "a26_research_status"   # idle | running | done | error

if RESEARCH_STATUS_KEY not in st.session_state:
    st.session_state[RESEARCH_STATUS_KEY] = "idle"
if "a26_research_topic" not in st.session_state:
    st.session_state["a26_research_topic"] = ""

def _compute_a26_phase():
    phase = st.session_state.get(RESEARCH_STATUS_KEY, "idle")
    ts = st.session_state.get(RESEARCH_TS_KEY, "")
    if phase == "running":
        text = "🌐 กำลังค้นหา Google..."
    elif phase == "done":
        text = f"✅ อัปเดตล่าสุด {ts}"
    elif phase == "error":
        text = "⚠️ ค้นหาไม่สำเร็จ — กดปุ่มเพื่อลองใหม่"
    else:
        text = "⏳ รอกดปุ่มเริ่มค้นหา"
    return phase, ts, text

# ══════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
.stApp{background:linear-gradient(135deg,#0b0f19 0%,#1a1a2e 100%);color:#e2e8f0}
[data-testid="stSidebar"]{background:rgba(15,23,42,.8);border-right:1px solid #1e293b}
.header-box{background:linear-gradient(90deg,rgba(56,189,248,.1),rgba(34,211,238,.08));
  border:1px solid #0ea5e944;border-radius:12px;padding:18px 24px;margin-bottom:18px}
.section-title{font-family:'IBM Plex Mono',monospace;font-size:11px;font-weight:700;color:#64748b;
  letter-spacing:2px;text-transform:uppercase;margin:18px 0 8px;padding-bottom:6px;border-bottom:1px solid #1e293b}
.research-card{background:rgba(15,23,42,.9);border:1px solid #1e293b;border-radius:14px;padding:20px 24px;margin-top:6px}
.research-meta{font-size:11px;color:#475569;font-family:'IBM Plex Mono',monospace;margin-bottom:10px}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# SIDEBAR NAV
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

# ══════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<div class="header-box">
  <span style='font-size:26px;font-weight:900;color:#fff'>🏢 งานบริษัทอาควาไลน์</span>
  <span style='font-size:13px;color:#22d3ee;margin-left:16px'>Knowledge Graph แบบ Real-time · ทีม AI 26 ตัวกำลังทำงานร่วมกัน</span>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# 🌐 KNOWLEDGE GRAPH — nodes = 26 agents, edges = การเชื่อมต่อ/การทำงานแบบ real-time
#    (ใช้ widget เดียวกับหน้าแรก ai_team.py — kg_widget.render_full_graph)
#    อยู่ด้านบนสุดของหน้า ตามที่กำหนด
# ══════════════════════════════════════════════════════════════════
a26_phase, a26_ts, a26_status_text = _compute_a26_phase()

st.markdown('<div class="section-title">🌐 Knowledge Graph — เครือข่าย AI Agent แบบ Real-time</div>', unsafe_allow_html=True)

GRAPH_HEIGHT = 560
_kg_html = render_full_graph(
    height=GRAPH_HEIGHT,
    a26_phase=a26_phase,
    a26_status=a26_status_text,
    title="AQUALINE NEURAL NETWORK",
    theme=get_kg_theme(),
)
components.html(_kg_html, height=GRAPH_HEIGHT + FULL_EXTRA_PX, scrolling=False)

# ══════════════════════════════════════════════════════════════════
# 🎯 หัวข้อพิเศษให้ A26 เจาะข้อมูล — พิมพ์ หรือพูดผ่านไมค์
# ══════════════════════════════════════════════════════════════════
st.markdown('<div class="section-title">🎯 อยากให้ A26 เจาะข้อมูลเรื่องอะไรเป็นพิเศษ — พิมพ์หรือพูดผ่านไมค์</div>', unsafe_allow_html=True)

_topic_col1, _topic_col2 = st.columns([5, 2])
with _topic_col1:
    _topic_val = st.text_input(
        "หัวข้อที่ต้องการให้ A26 เจาะข้อมูล",
        value=st.session_state.get("a26_research_topic", ""),
        key="a26_topic_input",
        placeholder="เช่น คู่แข่งโซนภาคเหนือ, ราคาตลาดหลังคาเมทัลชีทปีนี้ ฯลฯ (เว้นว่างได้ถ้าไม่ระบุ)",
        label_visibility="collapsed",
    )
    st.session_state["a26_research_topic"] = _topic_val
with _topic_col2:
    st.caption("🎤 กดปุ่มไมค์ด้านล่างเพื่อพูดแทนการพิมพ์ (รองรับ Chrome เป็นหลัก)")

components.html("""
<div style="font-family:'IBM Plex Mono',monospace;">
  <button id="aq-mic-btn" style="background:#0ea5e9;color:#fff;border:none;border-radius:8px;
    padding:8px 16px;font-size:13px;font-weight:700;cursor:pointer;">🎤 พูดหัวข้อที่ต้องการ</button>
  <span id="aq-mic-status" style="margin-left:10px;font-size:12px;color:#94a3b8;"></span>
</div>
<script>
(function() {
  const btn = document.getElementById('aq-mic-btn');
  const statusEl = document.getElementById('aq-mic-status');
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  btn.onclick = function() {
    if (!SR) {
      statusEl.textContent = '⚠️ เบราว์เซอร์นี้ไม่รองรับการพูด (ลองใช้ Chrome)';
      return;
    }
    const rec = new SR();
    rec.lang = 'th-TH';
    rec.interimResults = false;
    rec.maxAlternatives = 1;
    statusEl.textContent = '🔴 กำลังฟัง... พูดได้เลย';
    try { rec.start(); } catch (e) {}
    rec.onresult = function(e) {
      const txt = e.results[0][0].transcript;
      statusEl.textContent = '✅ ได้ยิน: ' + txt + ' (กำลังกรอกให้อัตโนมัติ)';
      try {
        const doc = window.parent.document;
        const inputs = doc.querySelectorAll('input[type="text"]');
        for (const inp of inputs) {
          const ph = inp.getAttribute('placeholder') || '';
          if (ph.indexOf('คู่แข่งโซนภาคเหนือ') !== -1) {
            const setter = Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype, 'value').set;
            setter.call(inp, txt);
            inp.dispatchEvent(new Event('input', { bubbles: true }));
            break;
          }
        }
      } catch (err) {}
    };
    rec.onerror = function(e) {
      statusEl.textContent = '⚠️ เกิดข้อผิดพลาด: ' + e.error;
    };
    rec.onend = function() {
      if (statusEl.textContent.indexOf('กำลังฟัง') !== -1) {
        statusEl.textContent = '';
      }
    };
  };
})();
</script>
""", height=60)

# ══════════════════════════════════════════════════════════════════
# 📋 FORM: ข้อมูลบริษัท AQUALINE
# ══════════════════════════════════════════════════════════════════
with st.expander("📋 ข้อมูลบริษัท AQUALINE (ใช้เป็นบริบทให้ A26 เจาะข้อมูลคู่แข่ง)", expanded=not _company_file_exists):
    with st.form("company_info_form"):
        c1, c2 = st.columns(2)
        with c1:
            f_name    = st.text_input("ชื่อบริษัท", company["name"])
            f_website = st.text_input("เว็บไซต์", company["website"])
            f_region  = st.text_input("ตลาด/พื้นที่ให้บริการ", company["region"])
            f_target  = st.text_area("กลุ่มลูกค้าเป้าหมาย", company["target"], height=90)
        with c2:
            f_business = st.text_area("ลักษณะธุรกิจ", company["business"], height=90)
            f_products = st.text_area("สินค้า/บริการหลัก", company["products"], height=90)
            f_strength = st.text_area("จุดแข็ง/USP", company["strength"], height=90)
        f_known = st.text_input("คู่แข่งที่รู้จักอยู่แล้ว (คั่นด้วย , ถ้ามี — ไม่บังคับ)", company["known_competitors"])

        submitted = st.form_submit_button("💾 บันทึกข้อมูลบริษัท และเริ่มเจาะข้อมูลคู่แข่งใหม่", use_container_width=True, type="primary")
        if submitted:
            new_info = {
                "name": f_name.strip() or DEFAULT_COMPANY["name"],
                "website": f_website.strip(),
                "business": f_business.strip(),
                "products": f_products.strip(),
                "target": f_target.strip(),
                "strength": f_strength.strip(),
                "region": f_region.strip(),
                "known_competitors": f_known.strip(),
            }
            save_company_info(new_info)
            st.session_state[RESEARCH_STATUS_KEY] = "running"
            st.success("✅ บันทึกข้อมูลบริษัทแล้ว — กำลังเริ่มเจาะข้อมูลคู่แข่งใหม่ด้วยข้อมูลล่าสุด")
            st.rerun()

# ══════════════════════════════════════════════════════════════════
# 📚 KNOWLEDGE HUB — ฐานความรู้สินค้า (แยกตามสินค้า) ป้อนให้ทุกแผนก/agent อ้างอิงตอนประชุม
#    ตอนนี้: อัปโหลดไฟล์/พิมพ์โน้ตเอง (เก็บลง product_knowledge.json)
#    ขั้นต่อไป (#46): เชื่อม Google Drive จริง — ไฟล์จาก Drive จะมาเติมในคลังเดียวกันนี้
# ══════════════════════════════════════════════════════════════════
st.markdown('<div class="section-title">📚 ฐานความรู้สินค้า (Knowledge Hub)</div>', unsafe_allow_html=True)
st.caption("คลังความรู้แยกตามสินค้า — แนบไฟล์ PDF/Word/Excel หรือพิมพ์โน้ตเอง ใช้เป็น \"สมองรวม\" ให้ทุกแผนก/agent "
           "อ้างอิงตอนประชุมและทำงาน")

# ══════════════════════════════════════════════════════════════════
# 🔌 GOOGLE DRIVE CONNECTION — ผู้ใช้ต้องสร้าง Google Cloud Project + OAuth ด้วยตัวเอง
#    โค้ดนี้ไม่สร้างบัญชี/ไม่กดอนุญาตแทนผู้ใช้ — แค่เปิดเบราว์เซอร์ให้ผู้ใช้ login + อนุญาตเอง
# ══════════════════════════════════════════════════════════════════
with st.expander("🔌 การเชื่อมต่อ Google Drive จริง", expanded=not gd.is_connected()):
    if not gd.is_configured():
        st.warning("ยังไม่พบไฟล์ `credentials.json` — ทำตามขั้นตอนนี้ก่อน (ทำครั้งเดียว):")
        st.markdown("""
1. ไปที่ [console.cloud.google.com](https://console.cloud.google.com/) → สร้างโปรเจกต์ใหม่ (เช่น "Aqualine AI Team")
2. เมนู **APIs & Services → Library** → ค้นหา **"Google Drive API"** → กด **Enable**
3. เมนู **APIs & Services → OAuth consent screen** → เลือก **External** → กรอกชื่อแอป/อีเมลติดต่อ → Save
   (ถ้าแอปอยู่โหมด Testing ต้องเพิ่มอีเมล Google ของคุณเป็น **Test user** ในหน้านี้ด้วย ไม่งั้น login ไม่ได้)
4. เมนู **Credentials → Create Credentials → OAuth client ID** → Application type เลือก **Desktop app** → Create
5. ดาวน์โหลดไฟล์ JSON ที่ได้ เปลี่ยนชื่อเป็น `credentials.json` แล้ววางไว้ในโฟลเดอร์เดียวกับ `ai_team.py`
6. เปิด terminal ในโฟลเดอร์โปรเจกต์ แล้วรัน:
   `pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib`
7. รีสตาร์ทแอปนี้ แล้วกลับมาที่ช่องนี้เพื่อกด "เชื่อมต่อ Google Drive"
""")
        st.caption("⚠️ ขั้นตอนนี้ต้องทำเอง — ระบบนี้จะไม่สร้างบัญชี Google หรือกดอนุญาตสิทธิ์แทนคุณ")
    elif not gd.libraries_installed():
        st.error("พบไฟล์ credentials.json แล้ว แต่ยังไม่ได้ติดตั้งไลบรารี — รันคำสั่งนี้ในเครื่องที่รันแอป:")
        st.code("pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib", language="bash")
    elif not gd.is_connected():
        st.info("ตั้งค่าพร้อมแล้ว — กดปุ่มด้านล่างเพื่อเชื่อมต่อ (เบราว์เซอร์จะเปิดให้คุณ login + กด \"อนุญาต\" เอง สิทธิ์อ่านอย่างเดียว)")
        if st.button("🔌 เชื่อมต่อ Google Drive", type="primary"):
            with st.spinner("⏳ กำลังเปิดเบราว์เซอร์ให้ login... (ทำในหน้าต่างที่เปิดขึ้นมา)"):
                _ok, _msg = gd.connect()
            if _ok:
                st.success(_msg)
                st.rerun()
            else:
                st.error(_msg)
    else:
        st.success("✅ เชื่อมต่อ Google Drive แล้ว (สิทธิ์อ่านอย่างเดียว) — วางลิงก์โฟลเดอร์ในแต่ละสินค้าด้านล่าง แล้วกด \"ซิงค์จาก Drive\" ได้เลย")
        if st.button("🔌 ยกเลิกการเชื่อมต่อ"):
            gd.disconnect()
            st.rerun()

_kb_products = pk.get_products()

with st.expander(f"➕ เพิ่มสินค้าใหม่ ({len(_kb_products)} สินค้าในระบบ)", expanded=(len(_kb_products) == 0)):
    _kb_new_col1, _kb_new_col2 = st.columns([4, 1])
    with _kb_new_col1:
        _kb_new_name = st.text_input("ชื่อสินค้า", key="kb_new_product_name",
                                      placeholder="เช่น รางน้ำฝน VG, หลังคาเมทัลชีท ฯลฯ",
                                      label_visibility="collapsed")
    with _kb_new_col2:
        if st.button("➕ เพิ่มสินค้า", use_container_width=True, key="kb_add_product_btn"):
            if _kb_new_name.strip():
                pk.add_product(_kb_new_name.strip())
                st.success(f"✅ เพิ่มสินค้า \"{_kb_new_name.strip()}\" แล้ว")
                st.rerun()
            else:
                st.error("⚠️ กรุณาพิมพ์ชื่อสินค้าก่อน")

if not _kb_products:
    st.markdown("<div style='text-align:center;padding:24px;color:#334155'>ยังไม่มีสินค้าในฐานความรู้ — เพิ่มสินค้าแรกด้านบนเพื่อเริ่มสร้างคลังความรู้</div>", unsafe_allow_html=True)

for _kb_p in _kb_products:
    _kb_chars = pk.total_chars(_kb_p["id"])
    with st.expander(f"📦 {_kb_p['name']} — {len(_kb_p.get('files', []))} ไฟล์ · {_kb_chars:,} ตัวอักษร"):
        _kb_pc1, _kb_pc2, _kb_pc3 = st.columns([3, 1, 1])
        with _kb_pc1:
            st.caption("🔗 ลิงก์โฟลเดอร์ Google Drive ของสินค้านี้")
            _kb_drive_url = st.text_input("Drive folder URL", value=_kb_p.get("drive_folder_url", ""),
                                           key=f"kb_drive_{_kb_p['id']}", label_visibility="collapsed",
                                           placeholder="https://drive.google.com/drive/folders/...")
            if _kb_drive_url != _kb_p.get("drive_folder_url", ""):
                pk.update_product(_kb_p["id"], drive_folder_url=_kb_drive_url)
            if _kb_p.get("drive_last_synced"):
                st.caption(f"🔄 ซิงค์ล่าสุด: {_kb_p['drive_last_synced']}")
        with _kb_pc2:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("🔄 ซิงค์จาก Drive", key=f"kb_sync_{_kb_p['id']}", use_container_width=True,
                         disabled=not (gd.is_connected() and _kb_drive_url.strip())):
                _folder_id = gd.extract_folder_id(_kb_drive_url)
                with st.spinner(f"⏳ กำลังโหลดไฟล์จาก Drive สำหรับ {_kb_p['name']}..."):
                    _drive_files = gd.sync_folder(_folder_id)
                pk.replace_drive_files(_kb_p["id"], _drive_files)
                st.success(f"✅ ซิงค์แล้ว {len(_drive_files)} ไฟล์จาก Drive")
                st.rerun()
        with _kb_pc3:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            if st.button("🗑️ ลบสินค้านี้", key=f"kb_del_product_{_kb_p['id']}", use_container_width=True):
                pk.delete_product(_kb_p["id"])
                st.rerun()
        if not gd.is_connected():
            st.caption("ℹ️ เชื่อมต่อ Google Drive ก่อน (ด้านบน) เพื่อเปิดใช้ปุ่มซิงค์")

        _kb_notes = st.text_area("📝 โน้ต/บริฟสินค้า (พิมพ์ความรู้เพิ่มเองได้ทันที)", value=_kb_p.get("notes", ""),
                                  key=f"kb_notes_{_kb_p['id']}", height=90)
        if _kb_notes != _kb_p.get("notes", ""):
            pk.update_product(_kb_p["id"], notes=_kb_notes)

        _kb_uploaded = st.file_uploader("แนบไฟล์ความรู้ (PDF / Word / Excel / ข้อความ) — อัปโหลดได้หลายไฟล์พร้อมกัน",
                                         type=["pdf", "docx", "xlsx", "txt"], accept_multiple_files=True,
                                         key=f"kb_upload_{_kb_p['id']}")
        if _kb_uploaded:
            _kb_existing_names = {f["filename"] for f in _kb_p.get("files", [])}
            _kb_added_any = False
            for _kb_file in _kb_uploaded:
                if _kb_file.name in _kb_existing_names:
                    continue  # กันโหลดไฟล์ซ้ำซ้อนตอน rerun (ไฟล์เดิมยังอยู่ในตัวอัปโหลด)
                _kb_ext = _kb_file.name.rsplit(".", 1)[-1].lower()
                _kb_text = ""
                try:
                    if _kb_ext == "pdf":
                        with pdfplumber.open(_kb_file) as _kb_pdf:
                            _kb_text = "\n".join(_pg.extract_text() or "" for _pg in _kb_pdf.pages)
                    elif _kb_ext == "docx":
                        _kb_doc = Document(_kb_file)
                        _kb_text = "\n".join(_par.text for _par in _kb_doc.paragraphs)
                    elif _kb_ext == "xlsx":
                        try:
                            import openpyxl
                            _kb_wb = openpyxl.load_workbook(_kb_file, data_only=True)
                            _kb_rows = []
                            for _kb_ws in _kb_wb.worksheets:
                                for _kb_row in _kb_ws.iter_rows(values_only=True):
                                    _kb_rows.append(" | ".join(str(c) for c in _kb_row if c is not None))
                            _kb_text = "\n".join(_kb_rows)
                        except ImportError:
                            st.error("⚠️ อ่านไฟล์ Excel ไม่ได้ — เซิร์ฟเวอร์ยังไม่ได้ติดตั้ง openpyxl (pip install openpyxl)")
                            continue
                    else:  # txt
                        _kb_text = _kb_file.read().decode("utf-8", errors="replace")
                    pk.add_file_to_product(_kb_p["id"], _kb_file.name, _kb_text, source="upload")
                    st.success(f"✅ โหลดความรู้จาก {_kb_file.name} สำเร็จ ({len(_kb_text):,} ตัวอักษร)")
                    _kb_added_any = True
                except Exception as e:
                    st.error(f"❌ อ่าน {_kb_file.name} ไม่สำเร็จ: {str(e)[:150]}")
            if _kb_added_any:
                st.rerun()

        if _kb_p.get("files"):
            _kb_hdr_col1, _kb_hdr_col2 = st.columns([4, 2])
            with _kb_hdr_col1:
                st.markdown("**ไฟล์ความรู้ที่แนบไว้:**")
            with _kb_hdr_col2:
                if st.button("🧹 ทำความสะอาดฐานความรู้ (ลบไฟล์ซ้ำ)", key=f"kb_consolidate_{_kb_p['id']}",
                             use_container_width=True,
                             help="ลบไฟล์ที่เนื้อหาซ้ำกันเป๊ะ และจำกัดไฟล์ที่ Pipeline บันทึกอัตโนมัติให้เหลือแค่ล่าสุด 20 ไฟล์ (Item 5)"):
                    _kb_consolidate_result = pk.consolidate_product_knowledge(_kb_p["id"])
                    st.success(
                        f"✅ ลบไฟล์ซ้ำ {_kb_consolidate_result['removed_duplicates']} ไฟล์ "
                        f"· ตัดไฟล์อัตโนมัติเก่า {_kb_consolidate_result['removed_old_auto']} ไฟล์ "
                        f"· เหลือ {_kb_consolidate_result['remaining_files']} ไฟล์"
                    )
                    st.rerun()
            for _kb_f in _kb_p["files"]:
                _kb_fc1, _kb_fc2 = st.columns([5, 1])
                with _kb_fc1:
                    _kb_src_icon = "🔗" if _kb_f.get("source") == "drive" else ("🤖" if _kb_f.get("source") == "pipeline" else "📄")
                    st.markdown(f"{_kb_src_icon} `{_kb_f['filename']}` — {len(_kb_f.get('text','')):,} ตัวอักษร · เพิ่มเมื่อ {_kb_f.get('added_at','')}")
                with _kb_fc2:
                    if st.button("🗑️", key=f"kb_delfile_{_kb_p['id']}_{_kb_f['filename']}"):
                        pk.delete_file_from_product(_kb_p["id"], _kb_f["filename"])
                        st.rerun()

# ══════════════════════════════════════════════════════════════════
# 🕵️ A26 AUTO COMPETITOR RESEARCH — รันจริงตอนนี้ถ้าสถานะคือ running
# ══════════════════════════════════════════════════════════════════
if st.session_state[RESEARCH_STATUS_KEY] == "running":
    with st.status("🕵️ A26 (ฝ่ายเจาะข้อมูลคู่แข่ง) กำลังวิ่งหาข้อมูลคู่แข่งของ AQUALINE แบบ Real-time...", expanded=True) as status_box:
        st.write("🌐 เชื่อมต่อ Google Search Grounding และวิเคราะห์ตลาดปัจจุบัน...")
        try:
            result = run_a26_competitor_research(company, st.session_state.get("a26_research_topic", ""))
            st.session_state[RESEARCH_RESULT_KEY] = result
            st.session_state[RESEARCH_TS_KEY] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            st.session_state[RESEARCH_STATUS_KEY] = "error" if result.startswith("⚠️") else "done"
            if st.session_state[RESEARCH_STATUS_KEY] == "done":
                status_box.update(label="✅ A26 วิเคราะห์ข้อมูลคู่แข่งเสร็จสิ้น", state="complete", expanded=False)
            else:
                status_box.update(label="⚠️ A26 เจอปัญหาระหว่างค้นหา — กดปุ่ม \"เริ่มเจาะข้อมูลคู่แข่ง\" เพื่อลองใหม่", state="error", expanded=True)
        except Exception as e:
            st.session_state[RESEARCH_RESULT_KEY] = f"⚠️ Unexpected error: {str(e)[:200]}"
            st.session_state[RESEARCH_STATUS_KEY] = "error"
            status_box.update(label="⚠️ เกิดข้อผิดพลาด", state="error", expanded=True)
    # รีเฟรชหน้าทันทีหลังค้นหาเสร็จ เพื่อให้ Knowledge Graph ด้านบนแสดงสถานะล่าสุด (ไม่ใช่ค้างที่ "กำลังค้นหา")
    st.rerun()

# ══════════════════════════════════════════════════════════════════
# 📊 COMPETITOR RESEARCH RESULTS
# ══════════════════════════════════════════════════════════════════
st.markdown('<div class="section-title">🕵️ ผลวิเคราะห์คู่แข่งล่าสุด (A26)</div>', unsafe_allow_html=True)

result_text = st.session_state.get(RESEARCH_RESULT_KEY, "")
ts = st.session_state.get(RESEARCH_TS_KEY, "")

_btn_col, _ = st.columns([1, 3])
with _btn_col:
    if st.button("▶ เริ่มเจาะข้อมูลคู่แข่ง (A26)", disabled=(a26_phase == "running"), use_container_width=True):
        st.session_state[RESEARCH_STATUS_KEY] = "running"
        st.rerun()

if a26_phase == "running":
    st.info("⏳ A26 กำลังวิเคราะห์อยู่ — ผลลัพธ์จะแสดงด้านล่างทันทีที่เสร็จ")
elif result_text:
    st.markdown(f"""<div class="research-card">
<div class="research-meta">🕐 อัปเดตล่าสุด: {ts}</div>
</div>""", unsafe_allow_html=True)
    st.markdown(result_text)
else:
    st.markdown("<div style='text-align:center;padding:40px;color:#334155'>ยังไม่มีผลวิเคราะห์ — กดปุ่ม \"▶ เริ่มเจาะข้อมูลคู่แข่ง (A26)\" ด้านบนเพื่อเริ่มค้นหา</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# 🏛️ DEPARTMENT MEETING — ประชุมแผนกแบบ AI ถกกันจริงแบบ Parallel โดยใช้ฐานความรู้สินค้าเป็น "สมองรวม"
# ══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<div class="section-title">🏛️ ห้องประชุมแผนก — ถกแบบ Parallel จริง พร้อมฐานความรู้สินค้า</div>', unsafe_allow_html=True)

if "meet_results" not in st.session_state:
    st.session_state["meet_results"] = []
if "meet_topic_locked" not in st.session_state:
    st.session_state["meet_topic_locked"] = ""
if "meet_summary" not in st.session_state:
    st.session_state["meet_summary"] = ""
if "meet_final_summary" not in st.session_state:
    st.session_state["meet_final_summary"] = ""

_meet_col1, _meet_col2 = st.columns([3, 1])
with _meet_col1:
    meet_topic = st.text_input(
        "หัวข้อประชุมวันนี้",
        value=st.session_state.get("a26_research_topic", "") or "",
        key="meet_topic_input",
        placeholder="เช่น แผนโปรโมชันหน้าฝนปีนี้, ไอเดียแคมเปญ TikTok ใหม่ ฯลฯ",
    )
with _meet_col2:
    meet_rounds = st.number_input("จำนวนรอบถก", min_value=1, max_value=3, value=2, key="meet_rounds_input")

_dept_ids_all = get_department_ids()
meet_selected_depts = st.multiselect(
    "แผนกที่เข้าร่วมประชุม",
    options=_dept_ids_all,
    default=_dept_ids_all,
    format_func=lambda did: f"{DEPARTMENTS[did]['icon']} {DEPARTMENTS[did]['name']}",
    key="meet_dept_select",
)

_kb_product_options = pk.get_product_names()
meet_selected_products = st.multiselect(
    "ใช้ฐานความรู้สินค้า (ไม่เลือก = ใช้ทุกสินค้า)",
    options=list(_kb_product_options.keys()),
    default=[],
    format_func=lambda pid: _kb_product_options.get(pid, pid),
    key="meet_product_select",
)

_meet_opt_col1, _meet_opt_col2 = st.columns([1, 1])
with _meet_opt_col1:
    meet_smart_filter = st.checkbox(
        "🎯 กรองเฉพาะ Agent ที่เกี่ยวข้องกับหัวข้อ (ลดต้นทุน/เวลา)",
        value=False, key="meet_smart_filter_toggle",
        help="วิเคราะห์คำในหัวข้อก่อนเปิดประชุม แล้วเลือกเฉพาะ Agent ที่เกี่ยวข้อง — ถ้ากรองแล้วเหลือน้อยเกินไปจะใช้ทุกคนเหมือนเดิมโดยอัตโนมัติ (ไม่กระทบทีมถ้าไม่แน่ใจ ปล่อยปิดไว้ได้)",
    )
with _meet_opt_col2:
    _pipeline_save_options = ["(ไม่บันทึกลง Knowledge Hub)"] + list(_kb_product_options.keys())
    meet_pipeline_save_pid = st.selectbox(
        "📦 Pipeline: บันทึกผลลง Knowledge Hub สินค้า (ไม่บังคับ)",
        options=_pipeline_save_options,
        format_func=lambda pid: pid if pid == "(ไม่บันทึกลง Knowledge Hub)" else _kb_product_options.get(pid, pid),
        key="meet_pipeline_save_select",
    )

_meet_run_col, _meet_pipe_col, _meet_clear_col = st.columns([1, 1, 1])
with _meet_run_col:
    meet_start = st.button("🚀 เริ่มประชุมแผนก", type="primary", use_container_width=True,
                            disabled=not (meet_topic.strip() and meet_selected_depts))
with _meet_pipe_col:
    meet_pipeline_start = st.button(
        "⚡ Pipeline อัตโนมัติ (ค้นคู่แข่ง→ประชุม→สรุปมติ)", use_container_width=True,
        disabled=not (meet_topic.strip() and meet_selected_depts),
        help="รันต่อเนื่องในคำสั่งเดียว: A26 ค้นข้อมูลคู่แข่ง → เปิดประชุมแผนก → ประธาน AI สรุปมติ แล้วหยุดรอให้คุณตรวจทาน/ล็อกมติเองด้านล่าง (ไม่แจกงานอัตโนมัติ — บันทึกผลไว้ในเครื่อง/Knowledge Hub เท่านั้น ไม่เขียนกลับ Google Drive)",
    )
with _meet_clear_col:
    if st.button("🗑️ เริ่มประชุมใหม่ (ล้างประวัติ)", use_container_width=True):
        st.session_state["meet_results"] = []
        st.session_state["meet_summary"] = ""
        st.session_state["meet_final_summary"] = ""
        st.session_state["meet_topic_locked"] = ""
        st.rerun()


def _build_meet_agent_ids(_topic):
    _ids = []
    for _did in meet_selected_depts:
        _ids.extend(get_agents_by_department(_did))
    if meet_smart_filter:
        _ids = meeting_engine.select_relevant_agents(_ids, _topic, min_keep=3)
    return _ids


def _run_meeting_rounds(_topic, _knowledge, _model, _n_rounds, _kg_ph, _status_ph, _transcript_ph):
    """รันประชุม N รอบจริง พร้อมบันทึกต้นทุนจริงทุกรอบผ่าน usage_logger — ใช้ร่วมกันทั้งปุ่มประชุมเดี่ยวและ Pipeline"""
    _agent_ids = _build_meet_agent_ids(_topic)
    meeting_ctx_local = ""
    for _round_no in range(1, int(_n_rounds) + 1):
        _status_ph.info(f"🗣️ รอบที่ {_round_no}/{int(_n_rounds)} — ทุกแผนกกำลังถกพร้อมกัน...")

        def _on_agent_done(aid, name, icon, dept_id, text, remaining_ids, round_no,
                            _ph=_kg_ph, _tph=_transcript_ph, _rounds=int(_n_rounds)):
            _label = f"🗣️ รอบ {round_no}/{_rounds} · {icon} {name} ({aid}) ตอบแล้ว — เหลืออีก {len(remaining_ids)} คน"
            with _ph.container():
                _live_html = render_full_graph(
                    height=420,
                    title="AQUALINE NEURAL NETWORK — LIVE MEETING",
                    theme=get_kg_theme(),
                    active_agents=remaining_ids,
                    active_label=_label,
                )
                components.html(_live_html, height=420 + FULL_EXTRA_PX, scrolling=False)
            st.session_state["meet_results"].append(
                {"aid": aid, "name": name, "icon": icon, "dept_id": dept_id, "round": round_no, "text": text}
            )
            with _tph.container():
                for _r in st.session_state["meet_results"]:
                    _d = DEPARTMENTS.get(_r["dept_id"], {})
                    st.markdown(f"**[รอบ {_r['round']}] {_d.get('icon','')} {_d.get('name','')} · {_r['icon']} {_r['name']} ({_r['aid']})**")
                    st.markdown(_r["text"])
                    st.markdown("---")

        _round_results = meeting_engine.run_meeting_round(
            agent_ids=_agent_ids,
            topic=_topic,
            knowledge_text=_knowledge,
            meeting_ctx=meeting_ctx_local,
            round_no=_round_no,
            api_key=API_KEY,
            model_name=_model,
            max_workers=5,
            on_agent_done=_on_agent_done,
        )
        usage_logger.log_meeting_batch(
            [{"amount_thb": r.get("cost_thb", 0),
              "desc": f"{r.get('icon','')} {r.get('name','')} ({r.get('aid','')}) รอบ {_round_no} - {_topic[:50]}"}
             for r in _round_results],
            session=_topic[:60],
        )
        meeting_ctx_local = meeting_engine.format_meeting_log(st.session_state["meet_results"])
    _status_ph.success(f"✅ ประชุมเสร็จสิ้น {int(_n_rounds)} รอบ — {len(st.session_state['meet_results'])} ความเห็นทั้งหมด")


if meet_start:
    meet_knowledge = pk.get_combined_knowledge_text(meet_selected_products or None)
    meet_model = meeting_engine.get_best_model(API_KEY)

    st.session_state["meet_results"] = []
    st.session_state["meet_topic_locked"] = meet_topic.strip()
    st.session_state["meet_summary"] = ""
    st.session_state["meet_final_summary"] = ""

    _kg_live_ph = st.empty()
    _round_status_ph = st.empty()
    _transcript_ph = st.empty()

    _run_meeting_rounds(
        st.session_state["meet_topic_locked"], meet_knowledge, meet_model, meet_rounds,
        _kg_live_ph, _round_status_ph, _transcript_ph,
    )

elif meet_pipeline_start:
    _pipe_topic = meet_topic.strip()
    meet_knowledge = pk.get_combined_knowledge_text(meet_selected_products or None)
    meet_model = meeting_engine.get_best_model(API_KEY)

    st.session_state["meet_results"] = []
    st.session_state["meet_topic_locked"] = _pipe_topic
    st.session_state["meet_summary"] = ""
    st.session_state["meet_final_summary"] = ""

    with st.status("⚡ กำลังรัน Pipeline อัตโนมัติ...", expanded=True) as _pipe_status:
        st.write("🕵️ ขั้นตอน 1/3 — A26 กำลังค้นข้อมูลคู่แข่ง/ตลาดที่เกี่ยวกับหัวข้อนี้...")
        _pipe_research = run_a26_competitor_research(company, _pipe_topic)
        st.session_state[RESEARCH_RESULT_KEY] = _pipe_research
        st.session_state[RESEARCH_TS_KEY] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        st.session_state[RESEARCH_STATUS_KEY] = "error" if _pipe_research.startswith("⚠️") else "done"

        st.write("🏛️ ขั้นตอน 2/3 — เปิดประชุมแผนกพร้อมผลค้นคู่แข่งล่าสุดเป็นข้อมูลประกอบ...")
        _kg_live_ph = st.empty()
        _round_status_ph = st.empty()
        _transcript_ph = st.empty()
        _meet_knowledge_with_research = (
            meet_knowledge + "\n\n[ผลค้นคู่แข่งล่าสุดจาก A26]\n" + _pipe_research
        ) if _pipe_research and not _pipe_research.startswith("⚠️") else meet_knowledge
        _run_meeting_rounds(
            _pipe_topic, _meet_knowledge_with_research, meet_model, meet_rounds,
            _kg_live_ph, _round_status_ph, _transcript_ph,
        )

        st.write("📊 ขั้นตอน 3/3 — ประธาน AI กำลังสรุปมติ...")
        _full_log = meeting_engine.format_meeting_log(st.session_state["meet_results"])
        _pipe_summary = meeting_engine.summarize_meeting(_full_log, _pipe_topic, API_KEY, meet_model)
        st.session_state["meet_summary"] = _pipe_summary

        if meet_pipeline_save_pid != "(ไม่บันทึกลง Knowledge Hub)":
            _save_text = (
                f"# สรุปผลประชุม: {_pipe_topic}\n\n"
                f"## ผลค้นคู่แข่ง (A26)\n{_pipe_research}\n\n"
                f"## บทสรุปมติที่ประชุม\n{_pipe_summary}\n\n"
                f"## บทสนทนาการประชุมฉบับเต็ม\n{_full_log}"
            )
            _save_result = pk.add_file_to_product(
                meet_pipeline_save_pid,
                f"pipeline_{_pipe_topic[:40]}_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
                _save_text, source="pipeline",
            )
            if _save_result.get("skipped_duplicate_of"):
                st.write(f"♻️ เนื้อหาเหมือนกับไฟล์ \"{_save_result['skipped_duplicate_of']}\" ที่มีอยู่แล้ว — ข้ามการบันทึกซ้ำ (Item 5: memory consolidation)")
            else:
                st.write(f"💾 บันทึกผลลง Knowledge Hub: {_kb_product_options.get(meet_pipeline_save_pid, meet_pipeline_save_pid)} แล้ว (บันทึกในเครื่อง ไม่เขียนกลับ Google Drive)")
                # 🧹 Item 5: รวบรวม/ทำความสะอาดฐานความรู้สินค้านี้หลังเพิ่มไฟล์ใหม่ทุกครั้ง
                # (ลบไฟล์ซ้ำที่หลุดมา + จำกัดไฟล์อัตโนมัติจาก Pipeline ไม่ให้บวมเกินไปในระยะยาว)
                pk.consolidate_product_knowledge(meet_pipeline_save_pid)

        _pipe_status.update(
            label="✅ Pipeline เสร็จสมบูรณ์ — เลื่อนลงไปตรวจทานมติ แล้วล็อก/แจกงานต่อด้านล่าง (ยังไม่มีการแจกงานอัตโนมัติ)",
            state="complete", expanded=False,
        )

elif st.session_state.get("meet_results"):
    st.caption(f"💬 ผลประชุมล่าสุด: \"{st.session_state.get('meet_topic_locked','')}\" — {len(st.session_state['meet_results'])} ความเห็น")
    with st.expander("📜 ดูบทสนทนาการประชุมทั้งหมด", expanded=False):
        for _r in st.session_state["meet_results"]:
            _d = DEPARTMENTS.get(_r["dept_id"], {})
            st.markdown(f"**[รอบ {_r['round']}] {_d.get('icon','')} {_d.get('name','')} · {_r['icon']} {_r['name']} ({_r['aid']})**")
            st.markdown(_r["text"])
            st.markdown("---")

# ══════════════════════════════════════════════════════════════════
# 📊 SUMMARIZE MEETING + REBUTTAL/LOCK-IN — ประธาน AI สรุปมติ แล้วผู้บริหารแย้ง/ล็อกได้
# ══════════════════════════════════════════════════════════════════
if st.session_state.get("meet_results"):
    st.markdown('<div class="section-title">📊 สรุปผลประชุม + ข้อโต้แย้ง/ล็อกมติ</div>', unsafe_allow_html=True)

    if st.button("📊 สรุปผลประชุมเป็น Action Plan", use_container_width=True):
        with st.spinner("⏳ ประธานที่ประชุม AI กำลังสรุปมติ..."):
            _full_log = meeting_engine.format_meeting_log(st.session_state["meet_results"])
            _summary = meeting_engine.summarize_meeting(
                _full_log, st.session_state["meet_topic_locked"], API_KEY, meeting_engine.get_best_model(API_KEY)
            )
        st.session_state["meet_summary"] = _summary
        st.rerun()

    if st.session_state.get("meet_summary"):
        st.markdown(st.session_state["meet_summary"])

        st.markdown("**📝 มีข้อโต้แย้ง/อยากปรับมติ พิมพ์ตรงนี้ก่อนล็อก:**")
        rebuttal_text = st.text_area("ข้อโต้แย้ง/ข้อเสนอเพิ่มเติม", key="meet_rebuttal_input", height=100,
                                      placeholder="เช่น งบไม่พอสำหรับแผนนี้ ลดสเกลลงครึ่งหนึ่ง, อยากเน้น TikTok มากกว่า Facebook ฯลฯ")
        _reb_col1, _reb_col2 = st.columns(2)
        with _reb_col1:
            if st.button("🔁 ส่งข้อโต้แย้ง ให้ปรับมติใหม่", use_container_width=True, disabled=not rebuttal_text.strip()):
                with st.spinner("⏳ ประธานที่ประชุม AI กำลังปรับมติตามข้อโต้แย้ง..."):
                    _full_log = meeting_engine.format_meeting_log(st.session_state["meet_results"])
                    _new_summary = meeting_engine.apply_rebuttal(
                        st.session_state["meet_topic_locked"], _full_log, st.session_state["meet_summary"],
                        rebuttal_text, API_KEY, meeting_engine.get_best_model(API_KEY)
                    )
                st.session_state["meet_summary"] = _new_summary
                st.rerun()
        with _reb_col2:
            if st.button("🔒 ล็อกมติฉบับนี้ → ส่งต่อให้เลขานุการแจกงาน", type="primary", use_container_width=True):
                st.session_state["meet_final_summary"] = st.session_state["meet_summary"]
                st.session_state["meet_confirm_dispatch"] = False
                st.success("✅ ล็อกมติแล้ว — เลื่อนลงไปด้านล่างเพื่อให้เลขานุการแจกงานต่อแผนก")
                st.rerun()

# ══════════════════════════════════════════════════════════════════
# 👩‍💼 SECRETARY DISPATCH — แตกมติที่ล็อกแล้วเป็นงานต่อแผนก
# ══════════════════════════════════════════════════════════════════
if st.session_state.get("meet_final_summary"):
    st.markdown('<div class="section-title">👩‍💼 เลขานุการ AI — แจกงานต่อแผนก</div>', unsafe_allow_html=True)
    st.markdown(f"""<div class="research-card">{st.session_state["meet_final_summary"]}</div>""", unsafe_allow_html=True)

    _confirm_dispatch = st.checkbox(
        "✅ ฉันตรวจทานมติข้างต้นแล้ว ยืนยันให้เลขานุการแจกงานจริงไปยังทุกแผนก (ขั้นนี้จะสร้างงานค้างจริงในกระดานงานด้านล่าง)",
        key="meet_confirm_dispatch",
    )
    if st.button("👩‍💼 ส่งต่อให้เลขานุการแจกงาน", type="primary", use_container_width=True, disabled=not _confirm_dispatch):
        with st.spinner("⏳ เลขานุการ AI กำลังแตกมติเป็นงานต่อแผนก..."):
            _breakdown = meeting_engine.secretary_breakdown(
                st.session_state["meet_topic_locked"], st.session_state["meet_final_summary"],
                API_KEY, meeting_engine.get_best_model(API_KEY)
            )
        if _breakdown.get("tasks"):
            secretary_state.add_tasks(_breakdown["tasks"], topic=st.session_state["meet_topic_locked"])
            _note = _breakdown.get("secretary_note", "")
            secretary_state.add_chat_message(
                "secretary",
                f"✅ แจกงานจากมติเรื่อง \"{st.session_state['meet_topic_locked']}\" เรียบร้อย {len(_breakdown['tasks'])} งานค่ะ"
                + (f" {_note}" if _note else "")
            )
            st.success(f"✅ แจกงานแล้ว {len(_breakdown['tasks'])} งาน — ดูที่กระดานงานด้านล่าง")
            st.session_state["meet_final_summary"] = ""
            st.rerun()
        else:
            st.error("⚠️ เลขาแตกงานไม่สำเร็จ — ลองกดใหม่อีกครั้ง")

# ══════════════════════════════════════════════════════════════════
# 💬 SECRETARY 1:1 CHAT — ศูนย์กลางคำถามจากทุกแผนกก่อนเริ่มงาน
# ══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<div class="section-title">💬 แชท 1:1 กับเลขานุการ AI</div>', unsafe_allow_html=True)

_sec_state = secretary_state.load_state()
_pending_qs = secretary_state.get_all_pending_questions()
if _pending_qs:
    st.warning(f"⚠️ มี {len(_pending_qs)} คำถามจากแผนกต่างๆ ที่ยังรอคำตอบจากคุณ — เลื่อนลงไปดูที่กระดานงาน หรือพิมพ์ตอบในแชทด้านล่างได้เลย")

_chat_box = st.container(height=320)
with _chat_box:
    if not _sec_state["chat"]:
        st.caption("ยังไม่มีบทสนทนา — ทักเลขาได้เลย หรือกด \"ส่งต่อให้เลขานุการแจกงาน\" ด้านบนเพื่อเริ่มแจกงาน")
    for _m in _sec_state["chat"]:
        with st.chat_message("user" if _m["role"] == "user" else "assistant"):
            st.markdown(_m["text"])

_chat_input = st.chat_input("พิมพ์คุยกับเลขานุการ...")
if _chat_input:
    secretary_state.add_chat_message("user", _chat_input)
    with st.spinner("⏳ เลขากำลังตอบ..."):
        _reply = meeting_engine.secretary_chat_reply(
            _chat_input, secretary_state.load_state()["chat"], secretary_state.load_state()["tasks"],
            API_KEY, meeting_engine.get_best_model(API_KEY)
        )
    secretary_state.add_chat_message("secretary", _reply)
    st.rerun()

# ══════════════════════════════════════════════════════════════════
# 📋 TASK BOARD — กระดานงานแต่ละแผนก: assigned → in_progress → delivered
# ══════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown('<div class="section-title">📋 กระดานงานแต่ละแผนก</div>', unsafe_allow_html=True)

_board_tasks = secretary_state.load_state()["tasks"]
if not _board_tasks:
    st.markdown("<div style='text-align:center;padding:24px;color:#334155'>ยังไม่มีงานที่แจก — เริ่มประชุมแผนกด้านบน แล้วล็อกมติ ส่งต่อให้เลขานุการแจกงาน</div>", unsafe_allow_html=True)
else:
    _status_label = {"assigned": "🆕 รับงานแล้ว", "in_progress": "🔧 กำลังทำ", "delivered": "✅ ส่งงานแล้ว"}
    _status_order = ["assigned", "in_progress", "delivered"]
    for _did in get_department_ids():
        _dept_tasks = [t for t in _board_tasks if t.get("dept_id") == _did]
        if not _dept_tasks:
            continue
        _dept = DEPARTMENTS[_did]
        with st.expander(f"{_dept['icon']} {_dept['name']} — {len(_dept_tasks)} งาน", expanded=True):
            for _t in _dept_tasks:
                st.markdown(f"**{_t['title']}** &nbsp; <span style='font-size:11px;color:#94a3b8'>เดดไลน์: {_t.get('deadline','-')}</span>", unsafe_allow_html=True)
                if _t.get("detail"):
                    st.caption(_t["detail"])

                _unanswered = [q for q in _t.get("clarifying_questions", []) if q not in _t.get("answers", {})]
                if _unanswered:
                    st.warning("❓ คำถามที่แผนกนี้ต้องถามก่อนเริ่มงาน:\n" + "\n".join(f"- {q}" for q in _unanswered))
                    for _qi, _q in enumerate(_unanswered):
                        _ans_key = f"task_ans_{_t['id']}_{_qi}"
                        _ans_val = st.text_input(f"ตอบ: {_q}", key=_ans_key)
                        if st.button("ส่งคำตอบ", key=f"task_ans_btn_{_t['id']}_{_qi}"):
                            if _ans_val.strip():
                                secretary_state.answer_clarifying_question(_t["id"], _q, _ans_val.strip())
                                secretary_state.add_chat_message("user", f"(ตอบคำถามงาน \"{_t['title']}\"): {_ans_val.strip()}")
                                st.rerun()
                elif _t.get("clarifying_questions"):
                    with st.expander("✅ คำถาม-คำตอบที่ตอบไปแล้ว", expanded=False):
                        for _q, _a in _t.get("answers", {}).items():
                            st.markdown(f"- **{_q}** → {_a}")

                _tb_col1, _tb_col2 = st.columns([3, 1])
                with _tb_col1:
                    _cur_status = _t.get("status", "assigned")
                    _new_status = st.selectbox(
                        "สถานะ", options=_status_order, index=_status_order.index(_cur_status),
                        format_func=lambda s: _status_label[s], key=f"task_status_{_t['id']}", label_visibility="collapsed",
                    )
                    if _new_status != _cur_status:
                        secretary_state.update_task_status(_t["id"], _new_status)
                        st.rerun()
                with _tb_col2:
                    if st.button("🗑️ ลบงาน", key=f"task_del_{_t['id']}", use_container_width=True):
                        secretary_state.delete_task(_t["id"])
                        st.rerun()
                st.markdown("---")
