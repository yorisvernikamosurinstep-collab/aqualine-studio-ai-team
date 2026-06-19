import streamlit as st
import json
import os
import io
import zipfile
from datetime import datetime

import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ui_settings import inject_global_font_css

st.set_page_config(page_title="Prompt Library — AQUALINE", layout="wide")

# 🔐 กันเข้าหน้านี้ตรงผ่าน URL โดยไม่ผ่านด่านล็อกอินที่หน้าแรก
from auth_guard import require_auth
require_auth()

# 🧭 PAGE-VISIT MARKER — ใช้โดยหน้า "งานบริษัทอาควาไลน์" เพื่อรู้ว่าผู้ใช้เปิดหน้าใหม่จริง
st.session_state["_active_page"] = __file__

# ฟอนต์/ขนาดตัวอักษรที่ผู้ใช้กำหนดเอง (หน้า Design UX/UI) — ใช้ร่วมกันทุกหน้า
st.markdown(inject_global_font_css(), unsafe_allow_html=True)

PROMPT_FILE = "prompt_library.json"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=IBM+Plex+Sans+Thai:wght@300;400;600;700&display=swap');
*,*::before,*::after{box-sizing:border-box;}
.stApp{background:linear-gradient(135deg,#0b0f19 0%,#1a1a2e 100%);color:#e2e8f0;font-family:'IBM Plex Sans Thai',sans-serif;}
[data-testid="stSidebar"]{background:rgba(15,23,42,.8);border-right:1px solid #1e293b;}
.header-box{background:linear-gradient(90deg,rgba(16,185,129,.15),rgba(6,182,212,.1));
  border:1px solid #10b98144;border-radius:12px;padding:16px 24px;margin-bottom:24px;}
.prompt-card{background:rgba(15,23,42,.9);border:1px solid #1e293b;border-radius:12px;
  padding:16px;margin-bottom:10px;transition:all .2s;}
.prompt-card:hover{border-color:#10b98144;box-shadow:0 0 12px rgba(16,185,129,.1);}
.prompt-title{font-size:14px;font-weight:700;color:#34d399;margin-bottom:4px;}
.prompt-tag{display:inline-block;background:rgba(16,185,129,.15);border:1px solid #10b98133;
  border-radius:20px;padding:2px 10px;font-size:11px;color:#6ee7b7;margin:2px;}
.prompt-body{font-size:12px;color:#94a3b8;margin-top:8px;background:rgba(0,0,0,.3);
  border-radius:8px;padding:10px;white-space:pre-wrap;max-height:100px;
  overflow-y:auto;font-family:monospace;}
.cat-badge{background:rgba(99,102,241,.2);border:1px solid #6366f133;border-radius:20px;
  padding:2px 10px;font-size:11px;color:#a5b4fc;margin-right:6px;}

/* rating stars */
.star-on  {color:#fbbf24;font-size:18px;cursor:pointer;}
.star-off {color:#1e293b;font-size:18px;cursor:pointer;}
.rating-row{display:flex;gap:2px;align-items:center;}

.stButton>button{font-family:'IBM Plex Mono',monospace!important;font-size:12px!important;font-weight:600!important;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-box">
  <span style='font-size:28px;font-weight:900;color:#fff'>📚 PROMPT LIBRARY</span>
  <span style='font-size:13px;color:#34d399;margin-left:16px'>คลัง Prompt สำเร็จรูป บันทึก &amp; ใช้ซ้ำได้</span>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# DEFAULT PROMPTS
# ══════════════════════════════════════════════════════════════════
DEFAULT_PROMPTS = [
    {"id":"d1","title":"Facebook Ad Copy — สินค้าบ้าน","category":"Ads",
     "tags":["Facebook","Copy","บ้าน"],"rating":0,
     "prompt":"เขียน Facebook Ad Copy สำหรับสินค้าตกแต่งบ้านพรีเมียม\nFormat: Headline (6 คำ) + Primary Text (3 ย่อหน้า) + CTA\nTone: Warm & Aspirational\nเน้น: คุณภาพ ความสวยงาม และความคุ้มค่าระยะยาว",
     "created":"2569-05-01","uses":0},
    {"id":"d2","title":"TikTok Hook 3 วิแรก","category":"Video",
     "tags":["TikTok","Hook","Viral"],"rating":0,
     "prompt":"สร้าง Hook สำหรับ TikTok/Reels 3 วิแรก จำนวน 5 แบบ\nรูปแบบ: [ตัวเลขน่าตกใจ] / [คำถามกระตุ้น] / [ข้อเท็จจริงที่ไม่รู้] / [ท้าทาย] / [Before-After]\nสินค้า: [ใส่ชื่อสินค้า]\nกลุ่มเป้าหมาย: [ใส่กลุ่มเป้าหมาย]",
     "created":"2569-05-01","uses":0},
    {"id":"d3","title":"Email Marketing — ลูกค้าเก่า","category":"CRM",
     "tags":["Email","LINE OA","Retention"],"rating":0,
     "prompt":"เขียน Email/LINE Broadcast สำหรับลูกค้าเก่าที่ไม่ได้ซื้อ 3 เดือน\nโครงสร้าง: Subject line (เปิดอ่าน) + Personalized greeting + ข้อเสนอพิเศษ + CTA\nTone: Friendly & Exclusive\nอย่าลืม: บอกว่าโปรนี้มีแค่ XX วัน",
     "created":"2569-05-01","uses":0},
    {"id":"d4","title":"Product Description — SEO Optimized","category":"SEO",
     "tags":["SEO","Product Page","เว็บไซต์"],"rating":0,
     "prompt":"เขียน Product Description สำหรับหน้าเว็บไซต์ SEO-Optimized\nความยาว: 200-300 คำ\nต้องมี: Keyword หลัก (ใส่ keyword), Feature 3 ข้อ, Benefit 3 ข้อ, Spec สำคัญ, CTA\nFormat: ย่อหน้าสั้นอ่านง่าย + Bullet points",
     "created":"2569-05-01","uses":0},
    {"id":"d5","title":"Sales Script — ปิดการขายทางโทรศัพท์","category":"Sales",
     "tags":["Sales","Script","โทรศัพท์"],"rating":0,
     "prompt":"เขียน Sales Script สำหรับโทรปิดการขายสินค้า [ชื่อสินค้า]\nโครงสร้าง:\n1. Opening (แนะนำตัว 15 วิ)\n2. Pain Point Discovery (ถาม 2-3 คำถาม)\n3. Pitch (เชื่อมสินค้ากับ pain)\n4. Handle Objections (ราคาแพง / ขอคิดก่อน)\n5. Close (CTA ชัดเจน)\nTone: Professional แต่ไม่กดดัน",
     "created":"2569-05-01","uses":0},
    {"id":"d6","title":"Instagram Caption — Lifestyle","category":"Social",
     "tags":["Instagram","Caption","Lifestyle"],"rating":0,
     "prompt":"เขียน Instagram Caption สไตล์ Lifestyle สำหรับสินค้า [ชื่อสินค้า]\nความยาว: 3-4 ประโยค\nโครงสร้าง: Hook 1 บรรทัด → เล่าเรื่อง Lifestyle → เชื่อมสินค้า → CTA อ่อนๆ\nปิดด้วย Hashtag 5-8 อัน\nTone: Aspirational & Warm",
     "created":"2569-05-01","uses":0},
    {"id":"d7","title":"Competitor Analysis Brief","category":"Research",
     "tags":["Research","คู่แข่ง","Strategy"],"rating":0,
     "prompt":"วิเคราะห์คู่แข่งในตลาด [ชื่อตลาด/สินค้า]\nครอบคลุม:\n1. คู่แข่งหลัก 3-5 ราย (ชื่อ, จุดขาย, ราคา)\n2. สิ่งที่คู่แข่งทำได้ดี\n3. ช่องว่างในตลาด (Gap) ที่เราจะเข้าได้\n4. แนะนำ Positioning สำหรับแบรนด์เรา\nอ้างอิง URL ถ้าหาได้",
     "created":"2569-05-01","uses":0},
    {"id":"d8","title":"Pricing Strategy — Bundle Offer","category":"Pricing",
     "tags":["Pricing","Bundle","Promo"],"rating":0,
     "prompt":"วางแผน Pricing Strategy และ Bundle Offer สำหรับ [ชื่อสินค้า]\nราคาปัจจุบัน: [ราคา]\nคู่แข่งขาย: [ราคาคู่แข่ง]\nต้องการ:\n1. โครงสร้างราคา 3 Tier (Basic / Standard / Premium)\n2. Bundle ที่แนะนำ 2-3 แบบ\n3. เหตุผลทางจิตวิทยาที่ทำให้คนรู้สึกคุ้ม\n4. Flash Sale / Early Bird Strategy",
     "created":"2569-05-01","uses":0},
]

# ══════════════════════════════════════════════════════════════════
# LOAD / SAVE
# ══════════════════════════════════════════════════════════════════
def load_prompts():
    if os.path.exists(PROMPT_FILE):
        try:
            with open(PROMPT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # migrate: ensure rating field exists
                for p in data:
                    if "rating" not in p:
                        p["rating"] = 0
                return data
        except: pass
    save_prompts(DEFAULT_PROMPTS)
    return DEFAULT_PROMPTS

def save_prompts(prompts):
    with open(PROMPT_FILE, "w", encoding="utf-8") as f:
        json.dump(prompts, f, ensure_ascii=False, indent=2)

if "prompts" not in st.session_state:
    st.session_state.prompts = load_prompts()

prompts = st.session_state.prompts

# ══════════════════════════════════════════════════════════════════
# IMPORT / EXPORT HELPERS
# ══════════════════════════════════════════════════════════════════
def export_prompts_json() -> bytes:
    """Export ทั้งคลังเป็น JSON bytes"""
    export_data = {
        "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total": len(st.session_state.prompts),
        "prompts": st.session_state.prompts,
    }
    return json.dumps(export_data, ensure_ascii=False, indent=2).encode("utf-8")

def export_prompts_txt() -> bytes:
    """Export เป็น plain text ไฟล์เดียว"""
    lines = [f"AQUALINE PROMPT LIBRARY EXPORT\nวันที่: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n{'='*60}\n"]
    for p in st.session_state.prompts:
        stars = "⭐" * p.get("rating", 0)
        lines.append(f"[{p['category']}] {p['title']} {stars}")
        lines.append(f"Tags: {', '.join(p.get('tags', []))}")
        lines.append(f"ใช้แล้ว: {p.get('uses',0)} ครั้ง")
        lines.append("-" * 40)
        lines.append(p["prompt"])
        lines.append("\n")
    return "\n".join(lines).encode("utf-8")

def export_prompts_zip() -> bytes:
    """Export แต่ละ prompt เป็นไฟล์ .txt ใน ZIP"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in st.session_state.prompts:
            safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in p["title"])
            fname = f"{p['category']}/{safe_name}.txt"
            content = f"Title: {p['title']}\nCategory: {p['category']}\nTags: {', '.join(p.get('tags',[]))}\nRating: {'⭐'*p.get('rating',0)} ({p.get('rating',0)}/5)\nUses: {p.get('uses',0)}\n\n{p['prompt']}"
            zf.writestr(fname, content.encode("utf-8"))
        # README
        zf.writestr("README.txt", f"AQUALINE Prompt Library Export\nExported: {datetime.now().strftime('%Y-%m-%d %H:%M')}\nTotal prompts: {len(st.session_state.prompts)}\n".encode("utf-8"))
    buf.seek(0)
    return buf.read()

def import_prompts_from_json(raw: bytes) -> tuple[int, str]:
    """Import จาก JSON ที่ export ไว้ — คืน (จำนวนที่เพิ่ม, error)"""
    try:
        data = json.loads(raw.decode("utf-8"))
        incoming = data.get("prompts", data) if isinstance(data, dict) else data
        if not isinstance(incoming, list):
            return 0, "รูปแบบ JSON ไม่ถูกต้อง"
        existing_ids = {p["id"] for p in st.session_state.prompts}
        added = 0
        for p in incoming:
            if not isinstance(p, dict): continue
            if "title" not in p or "prompt" not in p: continue
            # สร้าง id ใหม่ถ้าซ้ำ
            if p.get("id","") in existing_ids:
                p["id"] = f"imp_{datetime.now().strftime('%Y%m%d%H%M%S')}_{added}"
            if "rating" not in p: p["rating"] = 0
            if "category" not in p: p["category"] = "Import"
            if "tags" not in p: p["tags"] = []
            if "uses" not in p: p["uses"] = 0
            if "created" not in p: p["created"] = datetime.now().strftime("%Y-%m-%d")
            st.session_state.prompts.append(p)
            existing_ids.add(p["id"])
            added += 1
        save_prompts(st.session_state.prompts)
        return added, ""
    except Exception as e:
        return 0, str(e)[:100]

# ── Stats ──
categories = list(set(p["category"] for p in prompts))
avg_rating = sum(p.get("rating",0) for p in prompts if p.get("rating",0)>0)
rated_count = sum(1 for p in prompts if p.get("rating",0)>0)
avg_str = f"{avg_rating/rated_count:.1f}" if rated_count else "—"

c1, c2, c3, c4 = st.columns(4)
for col, num, lbl in [
    (c1, str(len(prompts)),          "Prompt ทั้งหมด"),
    (c2, str(len(categories)),       "หมวดหมู่"),
    (c3, str(sum(p.get("uses",0) for p in prompts)), "ครั้งที่ใช้รวม"),
    (c4, avg_str,                    "คะแนน Rating เฉลี่ย"),
]:
    col.markdown(f"""<div style='background:rgba(15,23,42,.8);border:1px solid #1e293b;border-radius:10px;
  padding:14px;text-align:center'>
  <div style='font-size:28px;font-weight:900;color:#34d399'>{num}</div>
  <div style='font-size:12px;color:#64748b'>{lbl}</div>
</div>""", unsafe_allow_html=True)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════
tab_lib, tab_add, tab_impexp = st.tabs(["📚 คลัง Prompt", "➕ เพิ่ม Prompt ใหม่", "📤 Import / Export"])

# ── TAB: LIBRARY ──
with tab_lib:
    col_s, col_c, col_sort = st.columns([2, 1, 1])
    with col_s:
        search = st.text_input("🔍 ค้นหา:", placeholder="ชื่อ, tag, หรือเนื้อหา...")
    with col_c:
        cat_filter = st.selectbox("หมวด:", ["ทั้งหมด"] + sorted(categories))
    with col_sort:
        sort_by = st.selectbox("เรียงตาม:", ["ล่าสุด", "ใช้มากสุด", "⭐ Rating สูงสุด", "ชื่อ A-Z"])

    filtered = [p for p in prompts
                if (not search or search.lower() in p["title"].lower()
                    or search.lower() in p["prompt"].lower()
                    or any(search.lower() in t.lower() for t in p.get("tags",[])))
                and (cat_filter == "ทั้งหมด" or p["category"] == cat_filter)]

    # Sort
    if sort_by == "ใช้มากสุด":
        filtered = sorted(filtered, key=lambda x: x.get("uses",0), reverse=True)
    elif sort_by == "⭐ Rating สูงสุด":
        filtered = sorted(filtered, key=lambda x: x.get("rating",0), reverse=True)
    elif sort_by == "ชื่อ A-Z":
        filtered = sorted(filtered, key=lambda x: x["title"])

    st.markdown(f"<div style='font-size:13px;color:#64748b;margin-bottom:12px'>แสดง {len(filtered)} prompt</div>", unsafe_allow_html=True)

    for p in filtered:
        tags_html  = "".join(f"<span class='prompt-tag'>{t}</span>" for t in p.get("tags", []))
        rating_val = p.get("rating", 0)
        stars_html = "".join("⭐" if i < rating_val else "☆" for i in range(5))

        with st.expander(f"{'⭐'*rating_val if rating_val else ''}  **{p['title']}**  ·  {p['category']}  ·  ใช้แล้ว {p.get('uses',0)} ครั้ง"):
            st.markdown(f"""<div class="prompt-card">
  <div class="prompt-title">{p['title']}</div>
  <span class="cat-badge">{p['category']}</span>{tags_html}
  <div style='margin:6px 0;font-size:16px;letter-spacing:2px' title='Rating {rating_val}/5'>{stars_html}</div>
  <div class="prompt-body">{p['prompt']}</div>
</div>""", unsafe_allow_html=True)

            # ── RATING ──
            st.markdown("<div style='font-size:11px;color:#64748b;margin-bottom:4px'>⭐ ให้คะแนน Prompt นี้:</div>", unsafe_allow_html=True)
            rating_cols = st.columns(5)
            for star in range(1, 6):
                with rating_cols[star - 1]:
                    is_filled = star <= rating_val
                    if st.button(
                        "⭐" if is_filled else "☆",
                        key=f"star_{p['id']}_{star}",
                        use_container_width=True,
                        help=f"{star} ดาว"
                    ):
                        for item in st.session_state.prompts:
                            if item["id"] == p["id"]:
                                # toggle: ถ้ากดดาวเดิม → ล้าง rating
                                item["rating"] = star if star != rating_val else 0
                        save_prompts(st.session_state.prompts)
                        st.rerun()

            # ── EDIT / COPY / SAVE / DEL ──
            new_prompt_text = st.text_area("แก้ไข Prompt:", value=p["prompt"], height=150, key=f"edit_{p['id']}")
            col_copy, col_save, col_del = st.columns(3)

            with col_copy:
                if st.button("📋 Copy & ใช้งาน", key=f"copy_{p['id']}", use_container_width=True):
                    for item in st.session_state.prompts:
                        if item["id"] == p["id"]:
                            item["uses"] = item.get("uses", 0) + 1
                    save_prompts(st.session_state.prompts)
                    st.code(p["prompt"], language=None)
                    st.success("✅ คัดลอกจากช่องด้านบนได้เลยครับ (+1 use)")

            with col_save:
                if st.button("💾 บันทึกการแก้ไข", key=f"save_{p['id']}", use_container_width=True):
                    for item in st.session_state.prompts:
                        if item["id"] == p["id"]:
                            item["prompt"] = new_prompt_text
                    save_prompts(st.session_state.prompts)
                    st.success("✅ บันทึกแล้ว!")
                    st.rerun()

            with col_del:
                if st.button("🗑️ ลบ", key=f"del_{p['id']}", use_container_width=True):
                    st.session_state.prompts = [item for item in st.session_state.prompts if item["id"] != p["id"]]
                    save_prompts(st.session_state.prompts)
                    st.warning("ลบแล้ว")
                    st.rerun()

# ── TAB: ADD NEW ──
with tab_add:
    st.markdown("### ➕ เพิ่ม Prompt ใหม่")
    col_l, col_r = st.columns(2)
    with col_l:
        new_title    = st.text_input("ชื่อ Prompt *", placeholder="เช่น LINE Broadcast — Flash Sale")
        new_category = st.text_input("หมวดหมู่ *", placeholder="เช่น CRM, Ads, Video, SEO, Sales")
        new_tags_raw = st.text_input("Tags (คั่นด้วย ,)", placeholder="เช่น LINE OA, Broadcast, Promo")
        new_rating   = st.slider("Rating เริ่มต้น:", 0, 5, 0, key="new_rating_slider")
        st.markdown(f"<div style='font-size:18px;letter-spacing:2px'>{'⭐'*new_rating}{'☆'*(5-new_rating)}</div>", unsafe_allow_html=True)
    with col_r:
        new_prompt_body = st.text_area("Prompt Text *", height=200,
            placeholder="พิมพ์ Prompt ที่ใช้งานได้เลย...\nใส่ [placeholder] สำหรับส่วนที่ต้องแก้ก่อนใช้")

    if st.button("✅ บันทึก Prompt ใหม่", type="primary", use_container_width=True):
        if new_title and new_prompt_body and new_category:
            new_id = f"u{datetime.now().strftime('%Y%m%d%H%M%S')}"
            new_tags = [t.strip() for t in new_tags_raw.split(",") if t.strip()]
            st.session_state.prompts.append({
                "id": new_id, "title": new_title, "category": new_category,
                "tags": new_tags, "prompt": new_prompt_body,
                "created": datetime.now().strftime("%Y-%m-%d"),
                "uses": 0, "rating": new_rating,
            })
            save_prompts(st.session_state.prompts)
            st.success(f"✅ เพิ่ม '{new_title}' แล้วครับ!")
            st.rerun()
        else:
            st.error("กรุณากรอก ชื่อ, หมวดหมู่ และ Prompt Text")

# ── TAB: IMPORT / EXPORT ──
with tab_impexp:
    st.markdown("### 📤 Export คลัง Prompt")
    st.markdown("<div style='font-size:12px;color:#64748b;margin-bottom:12px'>Export ทั้งคลัง Prompt เพื่อ backup หรือแชร์ให้ทีม</div>", unsafe_allow_html=True)

    exp_col1, exp_col2, exp_col3 = st.columns(3)

    with exp_col1:
        json_bytes = export_prompts_json()
        st.download_button(
            "⬇️ Export JSON",
            data=json_bytes,
            file_name=f"aqualine_prompts_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True,
            help="Export เป็น JSON สำหรับ import กลับ"
        )
        st.caption("สำหรับ backup & import กลับ")

    with exp_col2:
        txt_bytes = export_prompts_txt()
        st.download_button(
            "⬇️ Export TXT",
            data=txt_bytes,
            file_name=f"aqualine_prompts_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
            use_container_width=True,
            help="Export เป็น plain text อ่านง่าย"
        )
        st.caption("สำหรับอ่านหรือแชร์")

    with exp_col3:
        zip_bytes = export_prompts_zip()
        st.download_button(
            "⬇️ Export ZIP",
            data=zip_bytes,
            file_name=f"aqualine_prompts_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
            mime="application/zip",
            use_container_width=True,
            help="Export แต่ละ Prompt แยกเป็นไฟล์ใน ZIP"
        )
        st.caption("แต่ละ Prompt แยกไฟล์")

    st.markdown("---")
    st.markdown("### 📥 Import Prompt จากไฟล์")
    st.markdown("<div style='font-size:12px;color:#64748b;margin-bottom:12px'>รองรับเฉพาะ JSON ที่ Export จาก Aqualine Prompt Library เท่านั้น</div>", unsafe_allow_html=True)

    imp_file = st.file_uploader(
        "เลือกไฟล์ JSON ที่ต้องการ Import:",
        type=["json"],
        key="import_json_uploader",
        label_visibility="collapsed"
    )

    if imp_file:
        st.markdown(f"<div style='font-size:12px;color:#38bdf8;font-family:IBM Plex Mono,monospace'>📄 {imp_file.name} ({imp_file.size/1024:.1f} KB)</div>", unsafe_allow_html=True)
        imp_col1, imp_col2 = st.columns(2)
        with imp_col1:
            # Preview
            try:
                raw_preview = json.loads(imp_file.read().decode("utf-8"))
                imp_file.seek(0)
                incoming = raw_preview.get("prompts", raw_preview) if isinstance(raw_preview, dict) else raw_preview
                st.markdown(f"<div style='font-size:12px;color:#34d399'>✅ อ่านไฟล์ได้ — พบ {len(incoming) if isinstance(incoming,list) else '?'} prompt</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"❌ ไฟล์ JSON ไม่ถูกต้อง: {e}")
        with imp_col2:
            if st.button("📥 Import เพิ่มเข้าคลัง", type="primary", use_container_width=True, key="do_import"):
                imp_file.seek(0)
                added, err = import_prompts_from_json(imp_file.read())
                if err:
                    st.error(f"❌ {err}")
                else:
                    st.success(f"✅ Import สำเร็จ! เพิ่ม {added} prompt เข้าคลังแล้ว")
                    st.rerun()

    st.markdown("---")
    st.markdown("### ⚙️ จัดการคลัง")
    danger_col1, danger_col2 = st.columns(2)
    with danger_col1:
        if st.button("🔄 Reset เป็น Default Prompts", use_container_width=True):
            st.session_state.prompts = list(DEFAULT_PROMPTS)
            save_prompts(st.session_state.prompts)
            st.success("Reset แล้ว!")
            st.rerun()
    with danger_col2:
        if st.button("🗑️ ลบ Prompt ทั้งหมด", use_container_width=True):
            st.session_state.prompts = []
            save_prompts(st.session_state.prompts)
            st.warning("ลบทั้งหมดแล้ว!")
            st.rerun()
