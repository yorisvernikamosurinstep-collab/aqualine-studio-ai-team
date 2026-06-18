import os
import sys

import streamlit as st
import streamlit.components.v1 as components

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kg_widget import render_full_graph, FULL_EXTRA_PX
from agent_default_personas import AGENT_META, AGENT_IDS
from ui_settings import (
    get_settings, save_settings, reset_settings,
    THAI_FONTS, ENGLISH_FONTS, inject_global_font_css, DEFAULTS,
)

st.set_page_config(
    page_title="Design UX/UI — AQUALINE",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 🧭 PAGE-VISIT MARKER
st.session_state["_active_page"] = __file__

# ══════════════════════════════════════════════════════════════════
# ฟอนต์/ขนาดตัวอักษรที่ผู้ใช้กำหนดเอง — ใช้ร่วมกันทุกหน้า
# ══════════════════════════════════════════════════════════════════
st.markdown(inject_global_font_css(), unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=IBM+Plex+Sans+Thai:wght@300;400;600;700&display=swap');
*,*::before,*::after{box-sizing:border-box;}
.stApp{background:#070b12;color:#cbd5e1;}
[data-testid="stSidebar"]{background:#0d1117!important;border-right:1px solid #1e293b!important;}
.page-header{background:linear-gradient(90deg,#0d1117,#0f172a,#0d1117);border-bottom:1px solid #1e293b;
  padding:20px 28px;display:flex;align-items:center;gap:16px;position:relative;overflow:hidden;margin-bottom:20px;}
.page-header::after{content:'';position:absolute;inset:0;
  background:repeating-linear-gradient(90deg,transparent,transparent 80px,rgba(56,189,248,.03) 80px,rgba(56,189,248,.03) 81px);pointer-events:none;}
.page-title{font-family:'IBM Plex Mono',monospace;font-size:22px;font-weight:700;color:#f1f5f9;letter-spacing:2px;}
.page-sub{font-size:11px;color:#475569;font-family:'IBM Plex Mono',monospace;margin-top:3px;}
.dux-badge{display:inline-block;padding:2px 10px;border-radius:20px;font-family:'IBM Plex Mono',monospace;
  font-size:10px;font-weight:700;letter-spacing:1px;background:linear-gradient(90deg,#38bdf8,#818cf8);color:#070b12;margin-left:10px;}
.section-title{font-family:'IBM Plex Mono',monospace;font-size:11px;font-weight:700;color:#475569;
  letter-spacing:2px;text-transform:uppercase;margin:26px 0 10px;padding-bottom:5px;border-bottom:1px solid #1e293b;}
.dux-card{background:rgba(15,23,42,.9);border:1px solid #1e293b;border-radius:14px;padding:18px 20px;margin-bottom:6px;}
.dux-agent-head{font-family:'IBM Plex Mono',monospace;font-size:10px;color:#475569;letter-spacing:1px;
  text-transform:uppercase;padding:4px 0;border-bottom:1px solid #1e293b;margin-bottom:4px;}
.stButton > button{border-radius:8px!important;font-family:'IBM Plex Sans Thai',sans-serif!important;}
.streamlit-expanderHeader{font-family:'IBM Plex Mono',monospace!important;font-size:12px!important;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style='text-align:center;padding:14px 0 8px'>
      <div style='font-family:IBM Plex Mono,monospace;font-size:13px;font-weight:700;color:#f1f5f9'>AQUALINE</div>
      <div style='font-size:10px;color:#334155;font-family:IBM Plex Mono,monospace'>DESIGN UX/UI</div>
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

# ══════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<div class="page-header">
  <div style='font-size:38px'>🎨</div>
  <div>
    <div class="page-title">DESIGN UX/UI <span class="dux-badge">ตั้งค่าหน้าตาโปรแกรม</span></div>
    <div class="page-sub">ปรับข้อความวิ่ง · ชื่อโปรแกรม · ฟอนต์ไทย/อังกฤษ · ธีม Knowledge Graph — มีผลทุกหน้าทันทีที่บันทึก</div>
  </div>
</div>
""", unsafe_allow_html=True)

settings = get_settings()

# ══════════════════════════════════════════════════════════════════
# 7.1 — ข้อความวิ่ง (Marquee)
# ══════════════════════════════════════════════════════════════════
st.markdown('<div class="section-title">📜 7.1 ข้อความวิ่งบนสุดของเมนู 1 (Marquee)</div>', unsafe_allow_html=True)
with st.container():
    st.markdown('<div class="dux-card">', unsafe_allow_html=True)
    new_marquee_text = st.text_area(
        "ข้อความที่วิ่งผ่านหน้าจอ", value=settings["marquee_text"],
        key="dux_marquee_text", height=80,
    )
    c1, c2 = st.columns(2)
    with c1:
        new_marquee_color = st.color_picker(
            "สีข้อความ", value=settings["marquee_color"], key="dux_marquee_color",
        )
    with c2:
        new_marquee_speed = st.slider(
            "ความเร็ว (วินาที/รอบ — ตัวเลขน้อย = วิ่งเร็ว)", min_value=5, max_value=60,
            value=int(settings["marquee_speed_sec"]), key="dux_marquee_speed",
        )
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# 7.2 — ชื่อโปรแกรม
# ══════════════════════════════════════════════════════════════════
st.markdown('<div class="section-title">🏷️ 7.2 ชื่อโปรแกรม (แสดงบนหน้าแรก ai_team.py)</div>', unsafe_allow_html=True)
with st.container():
    st.markdown('<div class="dux-card">', unsafe_allow_html=True)
    new_app_title = st.text_input(
        "ชื่อโปรแกรม", value=settings["app_title"], key="dux_app_title",
    )
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# 7.3 — ฟอนต์
# ══════════════════════════════════════════════════════════════════
st.markdown('<div class="section-title">🔤 7.3 ฟอนต์ (มีผลทุกหน้าในโปรแกรม)</div>', unsafe_allow_html=True)
with st.container():
    st.markdown('<div class="dux-card">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        _thai_idx = THAI_FONTS.index(settings["font_thai"]) if settings["font_thai"] in THAI_FONTS else 0
        new_font_thai = st.selectbox(
            "ฟอนต์ภาษาไทย", THAI_FONTS, index=_thai_idx, key="dux_font_thai",
        )
    with c2:
        _en_idx = ENGLISH_FONTS.index(settings["font_english"]) if settings["font_english"] in ENGLISH_FONTS else 0
        new_font_english = st.selectbox(
            "ฟอนต์ภาษาอังกฤษ/ตัวเลข", ENGLISH_FONTS, index=_en_idx, key="dux_font_english",
        )
    c3, c4 = st.columns(2)
    with c3:
        new_font_size = st.slider(
            "ขนาดตัวอักษร (px)", min_value=10, max_value=32,
            value=int(settings["font_size_px"]), key="dux_font_size",
        )
    with c4:
        _style_opts = ["normal", "italic"]
        new_font_style = st.radio(
            "รูปแบบตัวอักษร", _style_opts,
            index=_style_opts.index(settings["font_style"]) if settings["font_style"] in _style_opts else 0,
            key="dux_font_style", horizontal=True,
        )
    st.markdown(
        f'<div style="font-family:\'{new_font_english}\',\'{new_font_thai}\',sans-serif;'
        f'font-size:{new_font_size}px;font-style:{new_font_style};color:#7dd3fc;margin-top:6px;">'
        f'ตัวอย่าง / Preview — AQUALINE AI Team 26 Agents ทำงานร่วมกัน 2026</div>',
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# 7.4 — ธีม Knowledge Graph
# ══════════════════════════════════════════════════════════════════
st.markdown('<div class="section-title">🌐 7.4 ธีม Knowledge Graph (ใช้ร่วมกันทุกหน้าที่มีกราฟ)</div>', unsafe_allow_html=True)
with st.container():
    st.markdown('<div class="dux-card">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        new_kg_line_color_agent = st.color_picker(
            "สีเส้น Agent ↔ Agent", value=settings["kg_line_color_agent"], key="dux_kg_line_color_agent",
        )
        new_kg_line_width_agent = st.slider(
            "ความหนาเส้น Agent ↔ Agent", min_value=1, max_value=8,
            value=int(settings["kg_line_width_agent"]), key="dux_kg_line_width_agent",
        )
    with c2:
        new_kg_line_color_thought = st.color_picker(
            "สีเส้น Agent ↔ ความคิด (Thought)", value=settings["kg_line_color_thought"], key="dux_kg_line_color_thought",
        )
        new_kg_line_width_thought = st.slider(
            "ความหนาเส้น Agent ↔ ความคิด (ควรเล็กกว่าเส้นบน)", min_value=1, max_value=8,
            value=int(settings["kg_line_width_thought"]), key="dux_kg_line_width_thought",
        )
    new_kg_speed = st.slider(
        "ความเร็วการเคลื่อนไหว/อนิเมชันโดยรวม", min_value=0.02, max_value=3.0, step=0.02,
        value=float(settings["kg_speed_multiplier"]), key="dux_kg_speed_multiplier",
    )
    st.markdown('</div>', unsafe_allow_html=True)

    with st.expander("🧬 ปรับแต่งสีและชื่อ Agent รายตัว (26 ตัว)", expanded=False):
        st.markdown(
            '<div class="dux-agent-head">ICON · รหัส/ชื่อเดิม · ชื่อที่ต้องการแสดงในกราฟ · สีของ Agent</div>',
            unsafe_allow_html=True,
        )
        new_agent_colors = {}
        new_agent_names = {}
        existing_colors = settings.get("kg_agent_colors", {}) or {}
        existing_names = settings.get("kg_agent_names", {}) or {}
        for aid in AGENT_IDS:
            meta = AGENT_META[aid]
            col_icon, col_label, col_name, col_color = st.columns([0.6, 2.2, 3, 1.4])
            with col_icon:
                st.markdown(f"<div style='font-size:20px;text-align:center'>{meta.get('icon','🤖')}</div>", unsafe_allow_html=True)
            with col_label:
                st.markdown(
                    f"<div style='padding-top:6px;font-size:12px;color:#94a3b8'>{aid} · {meta['name']}</div>",
                    unsafe_allow_html=True,
                )
            with col_name:
                _name_val = existing_names.get(aid, "")
                new_name = st.text_input(
                    f"ชื่อใหม่ {aid}", value=_name_val, key=f"dux_agent_name_{aid}",
                    placeholder=meta["name"], label_visibility="collapsed",
                )
            with col_color:
                _color_val = existing_colors.get(aid) or meta.get("color", "#3b82f6")
                new_color = st.color_picker(
                    f"สี {aid}", value=_color_val, key=f"dux_agent_color_{aid}",
                    label_visibility="collapsed",
                )
            new_agent_colors[aid] = new_color
            new_agent_names[aid] = new_name

# ══════════════════════════════════════════════════════════════════
# พรีวิว (Live) — ใช้ค่าปัจจุบันในฟอร์ม ยังไม่บันทึก
# ══════════════════════════════════════════════════════════════════
st.markdown('<div class="section-title">👁️ พรีวิวสด — ค่าที่ยังไม่ได้บันทึก</div>', unsafe_allow_html=True)
_preview_theme = {
    "line_color_agent": new_kg_line_color_agent,
    "line_color_thought": new_kg_line_color_thought,
    "line_width_agent": new_kg_line_width_agent,
    "line_width_thought": new_kg_line_width_thought,
    "speed_multiplier": new_kg_speed,
    "agent_colors": new_agent_colors,
    "agent_names": new_agent_names,
}
_PREVIEW_HEIGHT = 480
_preview_html = render_full_graph(
    height=_PREVIEW_HEIGHT, title="พรีวิว — AQUALINE NEURAL NETWORK", theme=_preview_theme,
)
components.html(_preview_html, height=_PREVIEW_HEIGHT + FULL_EXTRA_PX, scrolling=False)

# ══════════════════════════════════════════════════════════════════
# บันทึก / รีเซ็ต
# ══════════════════════════════════════════════════════════════════
st.markdown('<div class="section-title">💾 บันทึกการตั้งค่า</div>', unsafe_allow_html=True)
col_save, col_reset = st.columns(2)
with col_save:
    if st.button("💾 บันทึกการตั้งค่าทั้งหมด", type="primary", use_container_width=True, key="dux_btn_save"):
        new_settings = {
            "marquee_text": new_marquee_text,
            "marquee_color": new_marquee_color,
            "marquee_speed_sec": new_marquee_speed,
            "app_title": new_app_title,
            "font_thai": new_font_thai,
            "font_english": new_font_english,
            "font_size_px": new_font_size,
            "font_style": new_font_style,
            "kg_line_color_agent": new_kg_line_color_agent,
            "kg_line_color_thought": new_kg_line_color_thought,
            "kg_line_width_agent": new_kg_line_width_agent,
            "kg_line_width_thought": new_kg_line_width_thought,
            "kg_speed_multiplier": new_kg_speed,
            "kg_agent_colors": new_agent_colors,
            "kg_agent_names": new_agent_names,
        }
        save_settings(new_settings)
        st.success("✅ บันทึกการตั้งค่าเรียบร้อย — มีผลทุกหน้าทันที (กลับไปหน้าอื่นเพื่อดูผลลัพธ์)")
        st.rerun()
with col_reset:
    if st.button("♻️ คืนค่าเริ่มต้นทั้งหมด", use_container_width=True, key="dux_btn_reset"):
        reset_settings()
        # ล้างค่าวิดเจ็ตที่ค้างอยู่ใน session_state เพื่อให้รีเซ็ตแสดงผลทันที
        _keys_to_clear = [
            "dux_marquee_text", "dux_marquee_color", "dux_marquee_speed",
            "dux_app_title", "dux_font_thai", "dux_font_english",
            "dux_font_size", "dux_font_style",
            "dux_kg_line_color_agent", "dux_kg_line_color_thought",
            "dux_kg_line_width_agent", "dux_kg_line_width_thought",
            "dux_kg_speed_multiplier",
        ]
        for aid in AGENT_IDS:
            _keys_to_clear.append(f"dux_agent_name_{aid}")
            _keys_to_clear.append(f"dux_agent_color_{aid}")
        for k in _keys_to_clear:
            st.session_state.pop(k, None)
        st.success("♻️ คืนค่าเริ่มต้นเรียบร้อย")
        st.rerun()

st.caption("💡 การตั้งค่าทั้งหมดในหน้านี้จะถูกบันทึกลงไฟล์ ui_settings.json และมีผลกับทุกหน้าที่แสดงข้อความวิ่ง / ชื่อโปรแกรม / ฟอนต์ / Knowledge Graph โดยอัตโนมัติ")
