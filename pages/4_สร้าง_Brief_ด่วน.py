import streamlit as st
import streamlit.components.v1 as components
import json
import os
import requests
from datetime import datetime
import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kg_widget import render_full_graph, FULL_EXTRA_PX
from ui_settings import get_kg_theme, inject_global_font_css

st.set_page_config(page_title="Brief Builder — AQUALINE", layout="wide")

# 🔐 กันเข้าหน้านี้ตรงผ่าน URL โดยไม่ผ่านด่านล็อกอินที่หน้าแรก
from auth_guard import require_auth
require_auth()

# 🧭 PAGE-VISIT MARKER — ใช้โดยหน้า "งานบริษัทอาควาไลน์" เพื่อรู้ว่าผู้ใช้เปิดหน้าใหม่จริง
st.session_state["_active_page"] = __file__

# ฟอนต์/ขนาดตัวอักษรที่ผู้ใช้กำหนดเอง (หน้า Design UX/UI) — ใช้ร่วมกันทุกหน้า
st.markdown(inject_global_font_css(), unsafe_allow_html=True)

VAULT_FILE = "project_vault.json"

st.markdown("""
<style>
.stApp{background:linear-gradient(135deg,#0b0f19 0%,#1a1a2e 100%);color:#e2e8f0}
[data-testid="stSidebar"]{background:rgba(15,23,42,.8);border-right:1px solid #1e293b}
.header-box{background:linear-gradient(90deg,rgba(236,72,153,.15),rgba(139,92,246,.1));
  border:1px solid #ec489944;border-radius:12px;padding:16px 24px;margin-bottom:24px}
.section-card{background:rgba(15,23,42,.9);border:1px solid #1e293b;border-radius:12px;
  padding:20px;margin-bottom:16px}
.section-title{font-size:14px;font-weight:700;color:#a78bfa;margin-bottom:12px;
  padding-bottom:8px;border-bottom:1px solid #1e293b}
.preview-box{background:rgba(0,0,0,.4);border:1px solid #334155;border-radius:10px;
  padding:16px;font-size:13px;color:#94a3b8;white-space:pre-wrap;line-height:1.8;
  font-family:monospace;max-height:400px;overflow-y:auto}
.tag-chip{display:inline-block;background:rgba(139,92,246,.2);border:1px solid #8b5cf644;
  border-radius:20px;padding:3px 12px;font-size:12px;color:#c4b5fd;margin:3px;cursor:pointer}
.example-card{background:rgba(139,92,246,.08);border:1px solid #8b5cf630;border-radius:10px;
  padding:12px 16px;margin-bottom:8px;cursor:pointer;transition:border-color .2s}
.example-card:hover{border-color:#8b5cf6}
.example-title{font-size:13px;font-weight:700;color:#c4b5fd}
.example-desc{font-size:12px;color:#64748b;margin-top:2px}
.ai-box{background:linear-gradient(135deg,rgba(236,72,153,.1),rgba(139,92,246,.1));
  border:1px solid #a78bfa44;border-radius:12px;padding:16px;margin-bottom:16px}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-box">
  <span style='font-size:28px;font-weight:900;color:#fff'>📝 BRIEF BUILDER</span>
  <span style='font-size:13px;color:#f9a8d4;margin-left:16px'>สร้าง Brief ทีละขั้น → Copy ไปใส่หน้าหลัก</span>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# KNOWLEDGE GRAPH (เต็ม) — ใช้ widget เดียวกับหน้าแรก ai_team.py
# ══════════════════════════════════════════════════════════════════
_FULL_KG_HEIGHT = 560
components.html(
    render_full_graph(height=_FULL_KG_HEIGHT, title="AGENT STATUS — LIVE", theme=get_kg_theme()),
    height=_FULL_KG_HEIGHT + FULL_EXTRA_PX, scrolling=False,
)

# ── Example briefs ──
EXAMPLE_BRIEFS = {
    "🚿 ก๊อกน้ำ Premium Launch": {
        "product_name": "AQUALINE Prestige Series",
        "product_url": "https://www.aqualine.co.th/prestige",
        "product_desc": "ก๊อกน้ำสแตนเลส 304 ดีไซน์ Nordic ราคา 3,590฿ รับประกัน 5 ปี ผ่านมาตรฐาน มอก.",
        "target_age": "35-44", "target_gender": "ทุกเพศ", "target_income": "30K-60K",
        "target_location": "กรุงเทพฯ และปริมณฑล",
        "target_persona": "เจ้าของบ้านที่กำลังรีโนเวทห้องน้ำ ห่วงเรื่องคุณภาพและดีไซน์ที่ทนทาน",
        "objective": ["Launch สินค้าใหม่", "สร้าง Brand Awareness", "ยิง Ads"],
        "usp": "ทนทานกว่า 10 ปี, รับประกัน 5 ปี, ดีไซน์รางวัล iF Award 2024, ไม่เป็นคราบง่าย",
        "tone": "Luxury / Premium", "budget": "80,000฿/เดือน", "deadline": "1 มิ.ย. 2569",
        "platform": ["Facebook", "Instagram", "เว็บไซต์"],
        "notes": "ห้ามเปรียบเทียบราคากับคู่แข่งโดยตรง ต้องผ่าน Legal ก่อนโพสต์",
    },
    "🛁 โปรโมชั่น Shopee Sale": {
        "product_name": "AQUALINE ชุดห้องน้ำครบเซ็ต",
        "product_url": "https://shopee.co.th/aqualine",
        "product_desc": "ชุดก๊อกน้ำ+ฝักบัว+ชั้นวางของ ราคาพิเศษ 1,990฿ (ปกติ 3,200฿) ส่งฟรีทั่วไทย",
        "target_age": "25-34", "target_gender": "ทุกเพศ", "target_income": "15K-30K",
        "target_location": "ทั่วประเทศ",
        "target_persona": "คนเช่าคอนโด/อพาร์ทเม้นท์ที่อยากอัพเกรดห้องน้ำในงบจำกัด",
        "objective": ["เพิ่มยอดขาย", "ยิง Ads"],
        "usp": "ประหยัด 38%, ครบเซ็ตใน 1 กล่อง, ติดตั้งง่ายไม่ต้องจ้างช่าง",
        "tone": "Urgent / Promo", "budget": "30,000฿/เดือน", "deadline": "15 พ.ค. 2569",
        "platform": ["Facebook", "TikTok", "LINE OA"],
        "notes": "เน้น Flash Sale จำกัดเวลา ใช้ภาษาสั้นกระชับ ดึงดูด",
    },
    "🏢 B2B โรงแรม/โครงการ": {
        "product_name": "AQUALINE Commercial Grade",
        "product_url": "https://www.aqualine.co.th/commercial",
        "product_desc": "ก๊อกน้ำเกรดโรงแรม 4-5 ดาว ทนทานสูง รองรับการใช้งานหนัก บริการติดตั้งและบำรุงรักษา",
        "target_age": "35-44", "target_gender": "ชาย", "target_income": "60K+",
        "target_location": "กรุงเทพฯ, พัทยา, ภูเก็ต",
        "target_persona": "Procurement Manager โรงแรม/นักพัฒนาอสังหาริมทรัพย์ที่ต้องการซัพพลายเออร์ระยะยาว",
        "objective": ["สร้าง Brand Awareness", "SEO / บทความ"],
        "usp": "รับประกัน 10 ปี, มี Service Team ประจำ, MOQ ยืดหยุ่น, ใบเสนอราคาภายใน 24 ชม.",
        "tone": "Professional", "budget": "50,000฿/เดือน", "deadline": "30 มิ.ย. 2569",
        "platform": ["Google", "เว็บไซต์", "LINE OA"],
        "notes": "เน้น Trust และ Long-term partnership ไม่ใช้ภาษา consumer ทั่วไป",
    },
}

# ── Load vault ──
def load_vault():
    if os.path.exists(VAULT_FILE):
        try:
            with open(VAULT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"Default Project": {"url": "", "brief": "", "knowledge": "", "history": []}}

vault = load_vault()

# ── Session State defaults ──
defaults = {
    "product_name": "", "product_url": "", "product_desc": "",
    "target_age": "ทุกช่วงอายุ", "target_gender": "ทุกเพศ",
    "target_income": "ทุกระดับ", "target_location": "", "target_persona": "",
    "objective": [], "objective_custom": "",
    "usp": "", "tone": "Professional",
    "budget": "", "deadline": "", "platform": [],
    "notes": "", "ai_loading": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── AI Auto-fill ใช้ requests เรียก Anthropic API โดยตรง (ไม่ต้อง pip install anthropic) ──
def ai_autofill(product_info: str):
    """เรียก Claude API ผ่าน requests โดยตรง — ไม่ต้องติดตั้ง anthropic package"""
    api_key = st.secrets.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise ValueError(
            "❌ ไม่พบ ANTHROPIC_API_KEY ใน .streamlit/secrets.toml\n"
            "เพิ่มบรรทัดนี้: ANTHROPIC_API_KEY = 'sk-ant-...'"
        )

    prompt = f"""คุณเป็นผู้เชี่ยวชาญด้านการตลาดสินค้าสุขภัณฑ์และก๊อกน้ำ (AQUALINE)
จากข้อมูลสินค้าด้านล่าง ให้วิเคราะห์และตอบกลับเป็น JSON เท่านั้น ไม่ต้องมีคำอธิบายอื่น

ข้อมูลสินค้า:
{product_info}

ตอบกลับ JSON format นี้เท่านั้น:
{{
  "product_name": "ชื่อสินค้า/แบรนด์",
  "product_desc": "รายละเอียดสั้น 1-2 ประโยค",
  "target_age": "ช่วงอายุ (เช่น 25-34)",
  "target_gender": "เพศ (ทุกเพศ/ชาย/หญิง)",
  "target_income": "ระดับรายได้ (เช่น 30K-60K)",
  "target_location": "พื้นที่เป้าหมาย",
  "target_persona": "คำอธิบาย persona 1-2 ประโยค",
  "objective": ["วัตถุประสงค์1", "วัตถุประสงค์2"],
  "usp": "จุดขายหลัก 2-3 ข้อ คั่นด้วยจุลภาค",
  "tone": "Tone (Professional/Friendly & Warm/Luxury / Premium/Fun & Playful/Educational/Urgent / Promo)",
  "platform": ["Facebook", "Instagram"],
  "notes": "หมายเหตุสำคัญถ้ามี"
}}"""

    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": "claude-haiku-4-5",
            "max_tokens": 1024,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Claude API Error {resp.status_code}: {resp.text[:300]}")

    raw = resp.json()["content"][0]["text"].strip()
    # strip markdown fences ถ้ามี
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


# ── AI Auto-fill section ──
st.markdown('<div class="ai-box">', unsafe_allow_html=True)
st.markdown("### 🤖 AI Auto-fill — กรอกอัตโนมัติด้วย Claude")
st.markdown('<span style="font-size:13px;color:#94a3b8">วางข้อมูลสินค้า URL หรือรายละเอียดคร่าวๆ แล้วให้ AI กรอก Brief ให้อัตโนมัติ</span>', unsafe_allow_html=True)

ai_input = st.text_area(
    "วางข้อมูลสินค้า / URL / คำอธิบายคร่าวๆ:",
    placeholder="เช่น: ก๊อกน้ำสแตนเลส 304 ดีไซน์ Nordic ราคา 3,590฿ รับประกัน 5 ปี สำหรับคนรีโนเวทบ้าน\nหรือ: https://www.aqualine.co.th/prestige-series",
    height=80,
    key="ai_input_text"
)

col_ai1, col_ai2 = st.columns([1, 3])
with col_ai1:
    _has_key = bool(st.secrets.get("ANTHROPIC_API_KEY", ""))
    if not _has_key:
        st.warning("⚠️ ต้องมี ANTHROPIC_API_KEY ใน secrets.toml")
    if st.button("✨ Auto-fill ด้วย AI", type="primary", use_container_width=True,
                 disabled=(not ai_input or not _has_key)):
        if ai_input.strip():
            with st.spinner("🤖 Claude กำลังวิเคราะห์และกรอกข้อมูล..."):
                try:
                    result = ai_autofill(ai_input)
                    field_map = {
                        "product_name": "product_name",
                        "product_desc": "product_desc",
                        "target_location": "target_location",
                        "target_persona": "target_persona",
                        "usp": "usp",
                        "notes": "notes",
                        "objective_custom": "objective_custom",
                    }
                    for k, v in field_map.items():
                        if k in result and result[k]:
                            st.session_state[v] = result[k]

                    age_opts = ["ทุกช่วงอายุ", "18-24", "25-34", "35-44", "45-54", "55+"]
                    if result.get("target_age") in age_opts:
                        st.session_state["target_age"] = result["target_age"]

                    gender_opts = ["ทุกเพศ", "ชาย", "หญิง"]
                    if result.get("target_gender") in gender_opts:
                        st.session_state["target_gender"] = result["target_gender"]

                    income_opts = ["ทุกระดับ", "ต่ำกว่า 15K", "15K-30K", "30K-60K", "60K+"]
                    if result.get("target_income") in income_opts:
                        st.session_state["target_income"] = result["target_income"]

                    tone_opts = ["Professional", "Friendly & Warm", "Luxury / Premium",
                                 "Fun & Playful", "Educational", "Urgent / Promo"]
                    if result.get("tone") in tone_opts:
                        st.session_state["tone"] = result["tone"]

                    valid_obj = ["สร้าง Brand Awareness","เพิ่มยอดขาย","Launch สินค้าใหม่",
                                 "งาน Event / บูถ","คอนเทนต์ Social Media","ยิง Ads",
                                 "SEO / บทความ","วิดีโอ / Reels","ออกแบบกราฟิก",
                                 "สิ่งพิมพ์","LINE OA / CRM","TikTok"]
                    if result.get("objective"):
                        st.session_state["objective"] = [o for o in result["objective"] if o in valid_obj]

                    valid_plat = ["Facebook","Instagram","TikTok","LINE OA","YouTube",
                                  "Google","เว็บไซต์","Offline"]
                    if result.get("platform"):
                        st.session_state["platform"] = [p for p in result["platform"] if p in valid_plat]

                    st.success("✅ AI กรอกข้อมูลเรียบร้อย! ตรวจสอบและแก้ไขด้านล่างได้เลยครับ")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ เกิดข้อผิดพลาด: {e}")

with col_ai2:
    st.markdown('<span style="font-size:12px;color:#64748b">💡 AI จะวิเคราะห์และกรอกทุก field ให้อัตโนมัติ คุณแค่ตรวจสอบและปรับแต่งตามต้องการ</span>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ── Example Briefs ──
with st.expander("💡 ตัวอย่าง Brief สำเร็จรูป — คลิกเพื่อโหลด"):
    st.markdown('<span style="font-size:13px;color:#94a3b8">เลือกตัวอย่างที่ใกล้เคียงกับงานของคุณ แล้วแก้ไขรายละเอียด</span>', unsafe_allow_html=True)
    cols_ex = st.columns(3)
    for i, (title, data) in enumerate(EXAMPLE_BRIEFS.items()):
        with cols_ex[i % 3]:
            st.markdown(f"""<div class="example-card">
<div class="example-title">{title}</div>
<div class="example-desc">{data['product_desc'][:60]}...</div>
</div>""", unsafe_allow_html=True)
            if st.button(f"📂 โหลด", key=f"ex_{i}", use_container_width=True):
                for k, v in data.items():
                    st.session_state[k] = v
                st.success(f"✅ โหลดตัวอย่าง '{title}' แล้ว!")
                st.rerun()

st.markdown("---")

col_form, col_preview = st.columns([1.2, 1])

with col_form:
    st.markdown('<div class="section-card"><div class="section-title">🏷️ 1. ข้อมูลสินค้า / แบรนด์</div>', unsafe_allow_html=True)
    product_name = st.text_input("ชื่อสินค้า / แบรนด์",
        value=st.session_state.get("product_name", ""),
        placeholder="เช่น ก๊อกน้ำรุ่น Prestige Series", key="inp_product_name")
    product_url = st.text_input("URL สินค้า / เว็บไซต์",
        value=st.session_state.get("product_url", ""),
        placeholder="https://www.aqualine.co.th/...", key="inp_product_url")
    product_desc = st.text_area("รายละเอียดสินค้าโดยย่อ",
        value=st.session_state.get("product_desc", ""),
        placeholder="เช่น ก๊อกน้ำสแตนเลส 304 ดีไซน์ modern ราคา 2,990฿",
        height=80, key="inp_product_desc")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card"><div class="section-title">🎯 2. กลุ่มเป้าหมาย</div>', unsafe_allow_html=True)
    col_a, col_b = st.columns(2)
    age_opts    = ["ทุกช่วงอายุ","18-24","25-34","35-44","45-54","55+"]
    gender_opts = ["ทุกเพศ","ชาย","หญิง"]
    income_opts = ["ทุกระดับ","ต่ำกว่า 15K","15K-30K","30K-60K","60K+"]
    with col_a:
        target_age    = st.selectbox("ช่วงอายุ", age_opts,
            index=age_opts.index(st.session_state.get("target_age","ทุกช่วงอายุ")))
        target_gender = st.selectbox("เพศ", gender_opts,
            index=gender_opts.index(st.session_state.get("target_gender","ทุกเพศ")))
    with col_b:
        target_income   = st.selectbox("ระดับรายได้", income_opts,
            index=income_opts.index(st.session_state.get("target_income","ทุกระดับ")))
        target_location = st.text_input("พื้นที่",
            value=st.session_state.get("target_location",""),
            placeholder="เช่น กรุงเทพฯ, ทั่วประเทศ")
    target_persona = st.text_area("Persona (คนที่ซื้อคือใคร?)",
        value=st.session_state.get("target_persona",""),
        placeholder="เช่น เจ้าของบ้านที่กำลังรีโนเวท ห่วงเรื่องคุณภาพและดีไซน์",
        height=60)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card"><div class="section-title">🚀 3. วัตถุประสงค์งานนี้</div>', unsafe_allow_html=True)
    all_objectives = [
        "สร้าง Brand Awareness","เพิ่มยอดขาย","Launch สินค้าใหม่",
        "งาน Event / บูถ","คอนเทนต์ Social Media","ยิง Ads",
        "SEO / บทความ","วิดีโอ / Reels","ออกแบบกราฟิก",
        "สิ่งพิมพ์","LINE OA / CRM","TikTok",
    ]
    default_obj = [o for o in st.session_state.get("objective",[]) if o in all_objectives]
    objective = st.multiselect("เลือกได้หลายข้อ", all_objectives, default=default_obj)
    objective_custom = st.text_input("เพิ่มวัตถุประสงค์อื่นๆ",
        value=st.session_state.get("objective_custom",""),
        placeholder="เช่น เตรียมงาน Thailand Pavilion")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card"><div class="section-title">💬 4. Key Message / จุดขาย</div>', unsafe_allow_html=True)
    tone_opts = ["Professional","Friendly & Warm","Luxury / Premium","Fun & Playful","Educational","Urgent / Promo"]
    usp  = st.text_area("USP (จุดขายหลัก)",
        value=st.session_state.get("usp",""),
        placeholder="เช่น ทนทานกว่า 10 ปี, รับประกัน 5 ปี, ดีไซน์รางวัล iF Award",
        height=70)
    tone = st.selectbox("Tone of Voice", tone_opts,
        index=tone_opts.index(st.session_state.get("tone","Professional")))
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card"><div class="section-title">📅 5. งบประมาณ & ไทม์ไลน์</div>', unsafe_allow_html=True)
    col_c, col_d = st.columns(2)
    with col_c:
        budget   = st.text_input("งบโฆษณา (ถ้ามี)",
            value=st.session_state.get("budget",""), placeholder="เช่น 50,000฿/เดือน")
        deadline = st.text_input("Deadline",
            value=st.session_state.get("deadline",""), placeholder="เช่น 30 พ.ค. 2569")
    with col_d:
        valid_platforms = ["Facebook","Instagram","TikTok","LINE OA","YouTube","Google","เว็บไซต์","Offline"]
        default_plat = [p for p in st.session_state.get("platform",[]) if p in valid_platforms]
        platform = st.multiselect("Platform ที่ใช้", valid_platforms, default=default_plat)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-card"><div class="section-title">📎 6. หมายเหตุเพิ่มเติม / ข้อห้าม</div>', unsafe_allow_html=True)
    notes = st.text_area("เช่น ห้ามเปรียบเทียบคู่แข่งโดยตรง, ต้องผ่าน Legal ก่อนโพสต์",
        value=st.session_state.get("notes",""), height=70)
    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("🔄 ล้างฟอร์มทั้งหมด", use_container_width=True):
        for k, v in defaults.items():
            st.session_state[k] = v
        st.rerun()

with col_preview:
    st.markdown("### 👁️ Preview Brief")

    obj_list  = ", ".join(objective) + (f", {objective_custom}" if objective_custom else "")
    plat_list = ", ".join(platform) if platform else "-"

    brief_text = f"""📋 BRIEF — {product_name or "[ชื่อสินค้า]"}
{"="*50}

🏷️ สินค้า/แบรนด์:
{product_desc or "-"}
URL: {product_url or "-"}

🎯 กลุ่มเป้าหมาย:
• อายุ: {target_age} | เพศ: {target_gender} | รายได้: {target_income}
• พื้นที่: {target_location or "-"}
• Persona: {target_persona or "-"}

🚀 วัตถุประสงค์:
{obj_list or "-"}

💬 Key Message & Tone:
• USP: {usp or "-"}
• Tone: {tone}

📅 Timeline & Budget:
• Deadline: {deadline or "-"}
• งบ: {budget or "-"}
• Platform: {plat_list}

📎 หมายเหตุ:
{notes or "-"}
"""

    st.markdown(f'<div class="preview-box">{brief_text}</div>', unsafe_allow_html=True)
    st.markdown("---")
    st.text_area("📋 คัดลอกจากช่องนี้:", value=brief_text, height=200, key="brief_output")
    st.caption("✅ เลือกข้อความทั้งหมดแล้ว Ctrl+A → Ctrl+C แล้วนำไปวางในหน้าหลัก")
    st.markdown("---")

    st.markdown("### 💾 บันทึกลง Project Vault")
    target_project = st.selectbox("บันทึกลง Project:", list(vault.keys()))
    if st.button("💾 บันทึก Brief นี้ลง Vault", use_container_width=True, type="primary"):
        vault[target_project]["brief"] = brief_text
        vault[target_project]["url"]   = product_url
        with open(VAULT_FILE, "w", encoding="utf-8") as f:
            json.dump(vault, f, ensure_ascii=False, indent=4)
        st.success(f"✅ บันทึกลง '{target_project}' แล้วครับ!")

    st.markdown("---")
    st.markdown("### 📥 Export Brief")
    col_exp1, col_exp2, col_exp3 = st.columns(3)
    with col_exp1:
        st.download_button("📄 Export TXT",
            data=brief_text.encode("utf-8"),
            file_name=f"brief_{(product_name or 'brief').replace(' ','_')}_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain", use_container_width=True)
    with col_exp2:
        brief_md = f"# Brief — {product_name or 'Project'}\n\n" + brief_text
        st.download_button("📝 Export Markdown",
            data=brief_md.encode("utf-8"),
            file_name=f"brief_{(product_name or 'brief').replace(' ','_')}_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown", use_container_width=True)
    with col_exp3:
        brief_json = json.dumps({
            "product_name": product_name, "product_url": product_url,
            "product_desc": product_desc, "target_age": target_age,
            "target_gender": target_gender, "target_income": target_income,
            "target_location": target_location, "target_persona": target_persona,
            "objective": objective, "objective_custom": objective_custom,
            "usp": usp, "tone": tone, "budget": budget,
            "deadline": deadline, "platform": platform, "notes": notes,
            "brief_text": brief_text, "exported_at": datetime.now().isoformat()
        }, ensure_ascii=False, indent=2)
        st.download_button("📦 Export JSON",
            data=brief_json.encode("utf-8"),
            file_name=f"brief_{(product_name or 'brief').replace(' ','_')}_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json", use_container_width=True)
