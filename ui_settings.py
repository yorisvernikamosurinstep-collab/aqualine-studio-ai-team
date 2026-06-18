"""
ui_settings.py — ค่าตั้งค่า UI ที่ผู้ใช้ปรับแต่งได้เอง (หน้า "Design UX/UI")
บันทึกถาวรลงไฟล์ ui_settings.json และใช้ร่วมกันทุกหน้าในแอป
(marquee / ชื่อโปรแกรม / ฟอนต์ไทย-อังกฤษ / ธีมของ Knowledge Graph)
"""

import json
import os

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui_settings.json")

# ฟอนต์ที่รองรับภาษาไทยได้ดี (โหลดจาก Google Fonts)
THAI_FONTS = ["IBM Plex Sans Thai", "Sarabun", "Noto Sans Thai", "Prompt", "Kanit", "Mitr", "Pridi"]
# ฟอนต์สำหรับภาษาอังกฤษ/ตัวเลข
ENGLISH_FONTS = ["IBM Plex Mono", "Inter", "Roboto", "Poppins", "Share Tech Mono", "Orbitron", "Courier New", "Montserrat"]

DEFAULTS = {
    # --- ข้อ 7.1: ข้อความวิ่ง (marquee) ---
    "marquee_text": "Design is not just what it looks like and feels like. Design is how it works.",
    "marquee_color": "#ffffff",
    "marquee_speed_sec": 20,

    # --- ข้อ 7.2: ชื่อโปรแกรม ---
    "app_title": "🎯 SURINSTEP 32000",

    # --- ข้อ 7.3: ฟอนต์ ---
    "font_thai": "IBM Plex Sans Thai",
    "font_english": "IBM Plex Mono",
    "font_size_px": 16,
    "font_style": "normal",   # normal | italic

    # --- ข้อ 7.4: ธีม Knowledge Graph (ใช้ร่วมกันทุกหน้า) ---
    "kg_line_color_agent": "#00ccff",
    "kg_line_color_thought": "#7dd3fc",
    "kg_line_width_agent": 2,
    "kg_line_width_thought": 1,
    "kg_speed_multiplier": 1.0,
    "kg_agent_colors": {},   # {aid: "#hex"}
    "kg_agent_names": {},    # {aid: "ชื่อใหม่"}
}


def get_settings() -> dict:
    """โหลดค่าตั้งค่าปัจจุบัน (รวมกับค่า default ที่ขาดไป)"""
    data = {}
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    merged = {**DEFAULTS, **data}
    merged["kg_agent_colors"] = {**DEFAULTS["kg_agent_colors"], **(data.get("kg_agent_colors") or {})}
    merged["kg_agent_names"] = {**DEFAULTS["kg_agent_names"], **(data.get("kg_agent_names") or {})}
    return merged


def save_settings(settings: dict) -> None:
    """บันทึกค่าตั้งค่าถาวรลงไฟล์ ui_settings.json"""
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def reset_settings() -> dict:
    """รีเซ็ตค่าตั้งค่าทั้งหมดกลับเป็นค่าเริ่มต้น"""
    save_settings(dict(DEFAULTS))
    return get_settings()


def get_kg_theme() -> dict:
    """คืนค่า theme dict สำหรับส่งให้ kg_widget.render_full_graph(theme=...) —
    ใช้แบบเดียวกันทุกหน้าเพื่อให้ Knowledge Graph มีหน้าตา/ความเร็วตรงกันทั้งแอป"""
    s = get_settings()
    return {
        "line_color_agent": s["kg_line_color_agent"],
        "line_color_thought": s["kg_line_color_thought"],
        "line_width_agent": s["kg_line_width_agent"],
        "line_width_thought": s["kg_line_width_thought"],
        "speed_multiplier": s["kg_speed_multiplier"],
        "agent_colors": s["kg_agent_colors"],
        "agent_names": s["kg_agent_names"],
    }


def font_css_stack() -> str:
    """สร้าง CSS font-family stack: ฟอนต์อังกฤษก่อน (ครอบคลุมตัวอักษรละติน) แล้วตามด้วยฟอนต์ไทย
    (ตัวอักษรไทยจะ fallback ไปใช้ฟอนต์ไทยโดยอัตโนมัติเพราะฟอนต์อังกฤษส่วนใหญ่ไม่มีกลีฟภาษาไทย)"""
    s = get_settings()
    return f'"{s["font_english"]}", "{s["font_thai"]}", sans-serif'


def google_fonts_import_url() -> str:
    """URL สำหรับ @import ฟอนต์ที่เลือกไว้จาก Google Fonts"""
    s = get_settings()
    fams = sorted({s["font_thai"], s["font_english"]})
    parts = "&".join(f"family={fam.replace(' ', '+')}:wght@300;400;500;600;700;800;900" for fam in fams)
    return f"https://fonts.googleapis.com/css2?{parts}&display=swap"


def inject_global_font_css() -> str:
    """คืน <style> block สำหรับฝังในทุกหน้า เพื่อบังคับใช้ฟอนต์ + ขนาด + style ที่ผู้ใช้เลือก"""
    s = get_settings()
    stack = font_css_stack()
    import_url = google_fonts_import_url()
    italic = "italic" if s.get("font_style") == "italic" else "normal"
    return f"""
<style>
@import url('{import_url}');
html, body, [class*="css"], .stMarkdown, .stText, p, span, div, label, button {{
    font-family: {stack} !important;
    font-style: {italic};
}}
.stMarkdown p, .stMarkdown li {{
    font-size: {s['font_size_px']}px !important;
}}
/* ป้องกันข้อความใน file uploader ทับ/ซ้อนกัน เวลาฟอนต์ที่เลือกมีความกว้างไม่เท่าฟอนต์เดิม */
[data-testid="stFileUploaderDropzone"] {{
    flex-wrap: wrap !important;
    row-gap: 8px !important;
}}
[data-testid="stFileUploaderDropzoneInstructions"] {{
    font-size: 13px !important;
    line-height: 1.4 !important;
    white-space: normal !important;
}}
[data-testid="stFileUploaderDropzone"] button {{
    font-size: 13px !important;
    white-space: nowrap !important;
    flex-shrink: 0 !important;
}}
/* แก้ไอคอนตัวเล็กๆ ของ Streamlit เอง (ลูกศรย่อ/ขยาย sidebar, หัวลูกศรของ st.expander ฯลฯ)
   ไอคอนพวกนี้ใช้ "icon font" พิเศษ (Material Symbols) ที่ map ข้อความ เช่น
   "keyboard_arrow_right" ให้กลายเป็นรูปลูกศรเล็กๆ — กฎ font-family ด้านบนที่บังคับฟอนต์ทั้งแอป
   ไปเขียนทับฟอนต์ไอคอนนี้ด้วย ทำให้ข้อความที่ควรเป็นไอคอนเล็กๆ กลายเป็นตัวอักษรยาวๆ
   ทับซ้อนกับข้อความข้างๆ (เช่น หัวข้อ expander, ปุ่มย่อแถบด้านข้าง) ต้องคืนฟอนต์ไอคอนให้กลับมา */
[data-testid="stIconMaterial"],
[data-testid^="stIcon"],
[class*="stIconMaterial"],
.material-icons,
.material-icons-outlined,
.material-symbols-outlined,
.material-symbols-rounded {{
    font-family: 'Material Symbols Rounded','Material Symbols Outlined','Material Icons' !important;
    font-style: normal !important;
    font-weight: normal !important;
    letter-spacing: normal !important;
    white-space: nowrap !important;
}}
</style>
"""
