import streamlit as st
import requests
import json
import base64
import re
import html as html_lib
import time
import hashlib
from datetime import datetime

st.set_page_config(
    page_title="KONEX — AQUALINE Brand Intelligence",
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
  padding:20px 28px;display:flex;align-items:center;gap:16px;position:relative;overflow:hidden;margin-bottom:20px;}
.page-header::after{content:'';position:absolute;inset:0;
  background:repeating-linear-gradient(90deg,transparent,transparent 80px,rgba(56,189,248,.03) 80px,rgba(56,189,248,.03) 81px);pointer-events:none;}
.page-title{font-family:'IBM Plex Mono',monospace;font-size:22px;font-weight:700;color:#f1f5f9;letter-spacing:2px;}
.page-sub{font-size:11px;color:#475569;font-family:'IBM Plex Mono',monospace;margin-top:3px;}
.konex-badge{display:inline-block;padding:2px 10px;border-radius:20px;font-family:'IBM Plex Mono',monospace;
  font-size:10px;font-weight:700;letter-spacing:1px;background:linear-gradient(90deg,#38bdf8,#818cf8);color:#070b12;margin-left:10px;}
.section-title{font-family:'IBM Plex Mono',monospace;font-size:11px;font-weight:700;color:#475569;
  letter-spacing:2px;text-transform:uppercase;margin:16px 0 10px;padding-bottom:5px;border-bottom:1px solid #1e293b;}
.source-pill{display:inline-flex;align-items:center;gap:5px;background:rgba(15,23,42,.8);
  border:1px solid #1e293b;border-radius:20px;padding:4px 12px;font-size:11px;
  font-family:'IBM Plex Mono',monospace;color:#64748b;margin:2px;}
.source-pill.active{border-color:#38bdf8;color:#38bdf8;background:rgba(56,189,248,.06);}
.product-card{background:rgba(15,23,42,.9);border:1px solid #1e293b;border-radius:14px;
  padding:18px 20px;margin-bottom:10px;transition:border-color .2s,box-shadow .2s;}
.product-card:hover{border-color:#38bdf8;box-shadow:0 0 24px rgba(56,189,248,.07);}
.product-name{font-family:'IBM Plex Mono',monospace;font-size:14px;font-weight:700;color:#f1f5f9;}
.product-model{font-size:11px;color:#38bdf8;font-family:'IBM Plex Mono',monospace;margin-bottom:8px;}
.product-price{font-family:'IBM Plex Mono',monospace;font-size:18px;font-weight:700;color:#34d399;}
.tag{display:inline-block;padding:2px 8px;border-radius:10px;font-size:10px;font-family:'IBM Plex Mono',monospace;border:1px solid;margin:2px;}
.tag-blue{color:#38bdf8;border-color:#38bdf820;background:rgba(56,189,248,.06);}
.tag-green{color:#34d399;border-color:#34d39920;background:rgba(52,211,153,.06);}
.tag-amber{color:#fbbf24;border-color:#fbbf2420;background:rgba(251,191,36,.06);}
.chat-wrap{background:rgba(7,11,18,.95);border:1px solid #1e293b;border-radius:14px;overflow:hidden;margin-top:8px;}
.chat-msg-user{display:flex;justify-content:flex-end;padding:8px 16px;}
.chat-msg-user .bubble{background:linear-gradient(135deg,#1d4ed8,#3b82f6);color:#fff;
  border-radius:18px 18px 4px 18px;padding:10px 16px;font-size:13px;max-width:78%;line-height:1.7;}
.chat-msg-agent{display:flex;justify-content:flex-start;gap:10px;padding:8px 16px;align-items:flex-start;}
.chat-msg-agent .bubble{background:rgba(15,23,42,.9);border:1px solid #1e293b;color:#cbd5e1;
  border-radius:18px 18px 18px 4px;padding:10px 16px;font-size:13px;max-width:78%;line-height:1.7;white-space:pre-wrap;}
.agent-icon-chip{width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#0f2a44,#1e3a5f);
  border:1px solid #38bdf840;display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0;}
.msg-time{font-family:'IBM Plex Mono',monospace;font-size:10px;color:#334155;margin-top:3px;text-align:right;}
.memory-badge{background:rgba(52,211,153,.08);border:1px solid rgba(52,211,153,.25);border-radius:8px;
  padding:8px 14px;font-size:11px;color:#34d399;font-family:'IBM Plex Mono',monospace;display:flex;align-items:center;gap:6px;}
.blog-card{background:rgba(15,23,42,.8);border:1px solid #1e293b;border-radius:12px;padding:18px 20px;margin-bottom:10px;}
.blog-title{font-size:15px;font-weight:700;color:#f1f5f9;margin-bottom:4px;}
.blog-meta{font-family:'IBM Plex Mono',monospace;font-size:10px;color:#334155;margin-bottom:10px;}
.blog-preview{font-size:12px;color:#64748b;line-height:1.7;}
.vs-them{background:rgba(248,113,113,.04);border:1px solid rgba(248,113,113,.15);border-radius:10px;padding:12px;margin-bottom:4px;}
.vs-us{background:rgba(52,211,153,.04);border:1px solid rgba(52,211,153,.15);border-radius:10px;padding:12px;}
.stButton > button{border-radius:8px!important;font-family:'IBM Plex Sans Thai',sans-serif!important;font-size:12px!important;}
.cite-block{margin-top:10px;padding-top:8px;border-top:1px solid #1e293b;}
.cite-label{font-family:'IBM Plex Mono',monospace;font-size:9px;color:#334155;letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;}
.cite-chip{display:inline-flex;align-items:center;gap:4px;background:rgba(56,189,248,.07);
  border:1px solid rgba(56,189,248,.25);border-radius:6px;padding:3px 9px;font-size:10px;
  font-family:'IBM Plex Mono',monospace;color:#38bdf8;margin:2px;cursor:default;}
.cite-chip.pdf{background:rgba(167,139,250,.07);border-color:rgba(167,139,250,.25);color:#a78bfa;}
.cite-chip.manual{background:rgba(52,211,153,.07);border-color:rgba(52,211,153,.25);color:#34d399;}
.cite-chip.web{background:rgba(56,189,248,.07);border-color:rgba(56,189,248,.25);color:#38bdf8;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# AQUALINE WEBSITE DATA
# ══════════════════════════════════════════════════════════════════
AQUALINE_WEB = {
    "url": "https://www.aqualine.co.th",
    "name": "Aqualine Protarget Co., Ltd.",
    "desc": "ผลิตและจัดจำหน่ายหลังคาซีมรูฟ รางน้ำฝน ถังเก็บน้ำ และถังบำบัดน้ำเสีย คุณภาพระดับยุโรป",
    "warranty_note": "การรับประกันแตกต่างตามรุ่นและสเปก — ดูข้อมูลจากหน้าสินค้าจริงเสมอ (ห้ามเดาหรือแต่งตัวเลขขึ้นมาเอง)",
    "origin": "นำเข้าจากสวีเดน (Lindab) — เฉพาะรางน้ำฝน",
    "categories": [
        "หลังคาอาควาไลน์ สมาร์ทซีม (SMART SEAM INSULATED 600, BIG SEAM INSULATED 700, TRIPLE SEAM INSULATED 660, FREEFORM, SANDWICH PANEL)",
        "รางน้ำฝนอาควาไลน์ ลินแดบ (Lindab) — นำเข้าจากสวีเดน",
        "ถังไฟเบอร์กลาส (เก็บน้ำ, บำบัดน้ำเสีย, ดักไขมัน)",
        "ถังโพลีเอทิลีน (เก็บน้ำ, บำบัดน้ำเสีย, ดักไขมัน)",
    ],
    "product_urls": {
        "TRIPLE SEAM INSULATED 660": "https://www.aqualine.co.th/aqualine-roof-triple-seam-insulated-660",
        "SMART SEAM INSULATED 600":  "https://www.aqualine.co.th/aqualine-roof-smart-seam-insulated-600",
        "BIG SEAM INSULATED 700":    "https://www.aqualine.co.th/aqualine-roof-big-seam-insulated-700",
        "SMART SEAM 600":            "https://www.aqualine.co.th/aqualine-roof-smart-seam-600",
        "SMART SEAM FREEFORM":       "https://www.aqualine.co.th/aqualine-roof-smart-seam-freeform",
        "SANDWICH PANEL":            "https://www.aqualine.co.th/aqualine-wall-sandwich-panel",
        "รางน้ำฝน Lindab":           "https://www.aqualine.co.th/raingutter",
    },
    "blog_url": "https://www.aqualine.co.th/blog",
}

# ══════════════════════════════════════════════════════════════════
# THAI STOPWORDS
# ══════════════════════════════════════════════════════════════════
THAI_STOPWORDS = {
    "และ","ของ","ที่","มี","การ","ใน","จาก","ให้","ได้","ว่า","จะ","เป็น",
    "นี้","นั้น","แต่","หรือ","เพื่อ","กับ","โดย","ถ้า","ซึ่ง","ทำ","กัน",
    "อยู่","ยัง","แล้ว","ทั้ง","ด้วย","ต้อง","เมื่อ","อีก","เพราะ","แม้",
    "ไม่","ก็","มา","ไป","ใช้","รับ","บน","ลง","ขึ้น","สำหรับ","เพียง",
}

# ══════════════════════════════════════════════════════════════════
# PERSISTENT STORE — ไม่หายแม้ Streamlit rerun หรือ session reset
# ══════════════════════════════════════════════════════════════════
@st.cache_resource
def get_persistent_store():
    return {
        "kx_products": [],
        "kx_brand": {
            "name": "AQUALINE Protarget",
            "desc": AQUALINE_WEB["desc"],
            "tone": "มืออาชีพ / Professional",
            "target": "เจ้าของบ้าน, ผู้รับเหมา, สถาปนิก, นักพัฒนาอสังหาฯ",
            "strength": "คุณภาพระดับยุโรป, ระบบซีมรูฟ Click Lock ซ่อนสกรู, ฉนวน PU/PIR ในตัว, รางน้ำฝน Lindab นำเข้าสวีเดน",
            "website": AQUALINE_WEB["url"],
        },
        "kx_competitors": [],
        "kx_pdf_texts":   [],
        "kx_chat":        [],
        "kx_blogs":       [],
    }

# Bootstrap session_state จาก persistent store
_store = get_persistent_store()
for _k, _v in _store.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

def _sync_to_store():
    s = get_persistent_store()
    for k in ["kx_products","kx_brand","kx_competitors","kx_pdf_texts","kx_chat","kx_blogs"]:
        s[k] = st.session_state[k]

# ══════════════════════════════════════════════════════════════════
# CONSTANTS
# ══════════════════════════════════════════════════════════════════
MAX_PDF_TEXT_CHARS = 10_000
MAX_CONTEXT_CHARS  = 90_000
MAX_HISTORY_MSGS   = 10
MAX_HISTORY_CHARS  = 600
CATS  = ["หลังคา","รางน้ำฝน","ถังไฟเบอร์กลาส","ถังโพลีเอทิลีน","อุปกรณ์ติดตั้ง","อื่นๆ"]
TGTS  = ["บ้านพักอาศัย","คอนโด","โรงแรม","โรงงาน","อาคารพาณิชย์","โครงการ"]
TONES = ["มืออาชีพ / Professional","เป็นกันเอง / Friendly","พรีเมียม / Luxury","เทคนิค / Technical"]

def pid():
    return f"p_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

# ══════════════════════════════════════════════════════════════════
# MODEL SELECTOR — cache 5 นาที
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
            for p in ["models/gemini-2.5-flash-preview-05-20","models/gemini-2.5-flash",
                      "models/gemini-1.5-flash-latest","models/gemini-1.5-flash"]:
                if p in avail:
                    return p
    except Exception as e:
        st.warning(f"⚠️ ตรวจสอบ model ไม่ได้: {e}")
    return "models/gemini-1.5-flash"

# ══════════════════════════════════════════════════════════════════
# CORE API CALLER — retry + error handling ครบ
# ══════════════════════════════════════════════════════════════════
def _call_gemini_api(payload: dict, timeout: int = 90, max_retries: int = 3) -> str:
    model = get_model(API_KEY)
    url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={API_KEY}"
    for attempt in range(max_retries):
        try:
            resp = requests.post(url, json=payload, timeout=timeout)
            if resp.status_code == 200:
                return resp.json()["candidates"][0]["content"]["parts"][0].get("text","").strip()
            elif resp.status_code == 429:
                wait = 2 ** (attempt + 1)
                st.warning(f"⏳ Rate limit — รอ {wait}s...")
                time.sleep(wait)
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

# ══════════════════════════════════════════════════════════════════
# CONTEXT CACHE — rebuild เฉพาะเมื่อข้อมูลเปลี่ยน
# ══════════════════════════════════════════════════════════════════
def _context_hash() -> str:
    s = get_persistent_store()
    raw = (
        json.dumps(s["kx_brand"], ensure_ascii=False, sort_keys=True) +
        json.dumps([p.get("id","") for p in s["kx_products"]]) +
        json.dumps([p.get("name","") for p in s["kx_pdf_texts"]]) +
        json.dumps([c.get("id","") for c in s["kx_competitors"]])
    )
    return hashlib.md5(raw.encode()).hexdigest()[:12]

@st.cache_data(ttl=120, show_spinner=False)
def _build_context(context_hash: str) -> str:
    """Cached — rebuild เฉพาะเมื่อ hash เปลี่ยน"""
    _s = get_persistent_store()
    brand       = _s["kx_brand"]
    products    = _s["kx_products"]
    competitors = _s["kx_competitors"]
    pdfs        = _s["kx_pdf_texts"]

    lines = [
        "# KONEX — ฐานความรู้ AQUALINE\n",
        "## ⚠️ กฎสำคัญ:",
        "- ห้ามแต่งหรือเดาตัวเลขรับประกัน สเปก หรือราคา",
        "- ถ้าไม่มีในข้อมูลด้านล่าง ให้บอกว่า 'ดูจากหน้าสินค้าจริง'",
        "- ใช้ข้อมูลจากหน้าสินค้า URL ใน Memory ก่อนเสมอ",
        "",
        f"## แบรนด์: {brand.get('name','')}",
        f"- เว็บไซต์: {brand.get('website', AQUALINE_WEB['url'])}",
        f"- คำอธิบาย: {brand.get('desc','')}",
        f"- จุดแข็ง: {brand.get('strength','')}",
        f"- กลุ่มลูกค้า: {brand.get('target','')}",
        f"- Tone: {brand.get('tone','')}",
        "",
        "## ข้อมูล aqualine.co.th",
        f"- สินค้าหลัก: {', '.join(AQUALINE_WEB['categories'])}",
        f"- หมายเหตุรับประกัน: {AQUALINE_WEB['warranty_note']}",
        f"- แหล่งผลิต: {AQUALINE_WEB['origin']}",
        "\n## URL สินค้า:",
    ]
    for pname, purl in AQUALINE_WEB["product_urls"].items():
        lines.append(f"  - {pname}: {purl}")

    if pdfs:
        lines.append("\n## ข้อมูลจาก PDF/Catalog/เว็บ (ใช้ก่อนเสมอ)")
        for pdf in pdfs:
            src = f" [จาก {pdf.get('source_url', pdf['name'])}]" if pdf.get('source_url') else f" [PDF: {pdf['name']}]"
            lines.append(f"\n### 📄 {pdf['name']}{src}")
            lines.append(pdf['text'][:MAX_PDF_TEXT_CHARS])

    if products:
        lines.append(f"\n## สินค้าที่เพิ่มเอง ({len(products)} รายการ)")
        for i, p in enumerate(products, 1):
            lines.append(f"\n{i}. **{p['name']}** (รุ่น: {p.get('model','-')})")
            lines.append(f"   ราคา: {p.get('price','ไม่ระบุ')} | โปรโมชัน: {p.get('promo','ไม่มี')}")
            lines.append(f"   สเปก: {p.get('spec','')}")
            lines.append(f"   USP: {p.get('usp','')}")
            if p.get('extra'): lines.append(f"   เพิ่มเติม: {p['extra']}")

    if competitors:
        lines.append("\n## คู่แข่ง")
        for c in competitors:
            lines.append(f"- **{c['name']}**: {c.get('desc','')} | เราดีกว่า: {c.get('diff','')}")

    if brand.get("avoid"):
        lines.append(f"\n## ข้อห้าม: {brand['avoid']}")

    lines += [
        "\n---\n## หน้าที่ KONEX:",
        "1. ตอบโดยอ้างอิงแหล่งที่มาทุกครั้ง",
        "2. เขียน Content ใช้ข้อมูลจริง ห้ามแต่ง",
        "3. เขียน Wix Blog SEO ภาษาไทย",
        "4. ตอบในฐานะ Expert ของ Aqualine",
        "5. เปรียบเทียบสินค้ากับคู่แข่งอย่างมืออาชีพ",
        "ตอบภาษาไทย กระชับ ชัดเจน อ้างแหล่งที่มาทุกครั้ง",
    ]
    ctx = "\n".join(lines)
    if len(ctx) > MAX_CONTEXT_CHARS:
        ctx = ctx[:MAX_CONTEXT_CHARS] + "\n...[ตัดเพื่อประหยัด token]"
        st.session_state["kx_ctx_truncated"] = True
    else:
        st.session_state["kx_ctx_truncated"] = False
    return ctx

def build_full_context() -> str:
    return _build_context(_context_hash())

# ══════════════════════════════════════════════════════════════════
# PDF EXTRACTION
# ══════════════════════════════════════════════════════════════════
def extract_pdf_with_gemini(pdf_b64: str, filename: str) -> str:
    prompt = f"""อ่านและสกัดข้อมูลจาก PDF "{filename}" อย่างละเอียด

สกัดให้ครบ 100% (ห้ามแต่ง ถ้าไม่มีให้บอก 'ไม่ระบุ'):
1. ชื่อสินค้าและรุ่นเต็ม
2. จุดเด่น/USP (Triple Seam, Click Lock, Hidden Screw, ฉนวน PU/PIR ฯลฯ)
3. สเปกทางเทคนิค (ความหนา, ขนาด, เคลือบ AZ ฯลฯ)
4. การรับประกัน (ตัวเลขปีแน่นอน แยกประเภท)
5. สีที่มี (ชื่อและรหัส)
6. ราคา (ถ้ามี)
7. กลุ่มลูกค้า / การใช้งาน
8. ข้อมูลสำคัญอื่นๆ

จัด Markdown ภาษาไทย พร้อมหัวข้อชัดเจน"""
    return _call_gemini_api(
        payload={
            "contents": [{"parts": [
                {"inline_data": {"mime_type": "application/pdf", "data": pdf_b64}},
                {"text": prompt}
            ]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 4096},
        },
        timeout=120,
    )

# ══════════════════════════════════════════════════════════════════
# WEB FETCH — ใช้ 2 วิธีพร้อมกัน (HTML + Google Search Grounding)
# ══════════════════════════════════════════════════════════════════
def fetch_product_page_with_gemini(url: str) -> str:
    # วิธีที่ 1: requests.get → วิเคราะห์ HTML structure / meta / SSR
    raw_html = ""
    try:
        r = requests.get(url, timeout=20, headers={
            "User-Agent": "Mozilla/5.0 (compatible; Googlebot/2.1)",
            "Accept-Language": "th,en;q=0.9",
        })
        raw_html = r.text[:30000]
    except Exception as e:
        raw_html = f"(HTML ไม่ได้: {e})"

    result_html = _call_gemini_api(
        payload={
            "contents": [{"parts": [{"text": f"""HTML จาก {url}:
```html
{raw_html}
```
สกัดข้อมูลสินค้า: ชื่อ, USP, สเปก, รับประกัน (ตัวเลขจริง), สี, ฉนวน, ระบบติดตั้ง
ตอบ Markdown ภาษาไทย ใช้ข้อมูลจาก HTML เท่านั้น"""}]}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 4096},
        },
        timeout=90,
    )

    # วิธีที่ 2: Google Search Grounding — แก้ปัญหา Wix JS-rendered
    slug = url.rstrip("/").split("/")[-1]
    result_search = _call_gemini_api(
        payload={
            "contents": [{"parts": [{"text": f"""ค้นหาข้อมูลสินค้า Aqualine: {slug}
จาก {url}

สกัด: ชื่อรุ่น, USP ทุกข้อ, สเปก, รับประกัน (ปีแน่นอน), สี
ตอบ Markdown ภาษาไทย"""}]}],
            "tools": [{"google_search": {}}],
            "generationConfig": {"temperature": 0.1, "maxOutputTokens": 4096},
        },
        timeout=60,
    )

    if result_search.startswith("⚠️"):
        return result_html
    if result_html.startswith("⚠️"):
        return result_search
    return f"## ข้อมูลจาก HTML\n{result_html}\n\n## ข้อมูลจาก Google Search\n{result_search}"

def fetch_and_cache_product_url(url: str, label: str = "") -> str:
    cache_name = f"🌐 {label or url.split('/')[-1]}"
    already = next((p for p in st.session_state.kx_pdf_texts if p["name"] == cache_name), None)
    if already:
        return already["text"]
    text = fetch_product_page_with_gemini(url)
    if not text.startswith("⚠️"):
        st.session_state.kx_pdf_texts.append({
            "name": cache_name,
            "text": text[:MAX_PDF_TEXT_CHARS],
            "uploaded_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "size_kb": round(len(text) / 1024, 1),
            "source_url": url,
        })
        _sync_to_store()
    return text

# ══════════════════════════════════════════════════════════════════
# CITATION ENGINE — cached + stopword-filtered
# ══════════════════════════════════════════════════════════════════
@st.cache_data(ttl=60, show_spinner=False)
def _build_chunks(context_hash: str) -> list:
    _s = get_persistent_store()
    chunks = []
    web_text = (
        "หลังคา SMART SEAM BIG SEAM TRIPLE SEAM FREEFORM SANDWICH PANEL "
        "รางน้ำฝน Lindab สวีเดน ถังไฟเบอร์กลาส ถังโพลีเอทิลีน เก็บน้ำ บำบัดน้ำเสีย "
        f"{AQUALINE_WEB['warranty_note']} {AQUALINE_WEB['origin']} {AQUALINE_WEB['desc']}"
    )
    chunks.append({"source_id":"web","source_type":"web","label":"aqualine.co.th",
                   "url":AQUALINE_WEB["url"],"text":web_text.lower()})
    for pdf in _s["kx_pdf_texts"]:
        for para in [p.strip() for p in pdf["text"].split("\n") if len(p.strip()) > 30][:50]:
            chunks.append({"source_id":f"pdf_{pdf['name']}","source_type":"pdf",
                           "label":pdf["name"],"url":None,"text":para.lower()})
    for p in _s["kx_products"]:
        chunks.append({
            "source_id": f"manual_{p['id']}","source_type":"manual",
            "label": p["name"],"url":None,
            "text": f"{p['name']} {p.get('model','')} {p.get('spec','')} {p.get('usp','')}".lower(),
        })
    return chunks

def find_citations(response_text: str) -> list:
    chunks = _build_chunks(_context_hash())
    resp_lower = response_text.lower()
    tokens = set(re.findall(r'[ก-๙a-z0-9]{4,}', resp_lower)) - THAI_STOPWORDS
    if not tokens:
        return []
    scored = {}
    for chunk in chunks:
        chunk_tokens = set(re.findall(r'[ก-๙a-z0-9]{4,}', chunk["text"])) - THAI_STOPWORDS
        overlap = len(tokens & chunk_tokens)
        if overlap < 2:
            continue
        sid = chunk["source_id"]
        if sid not in scored or overlap > scored[sid]["score"]:
            scored[sid] = {**chunk, "score": overlap}
    top = sorted(scored.values(), key=lambda x: -x["score"])[:4]
    seen, result = set(), []
    for c in top:
        if c["label"] not in seen:
            seen.add(c["label"])
            result.append(c)
    return result

def render_citations(citations: list) -> str:
    if not citations:
        return ""
    icons = {"web":"🌐","pdf":"📄","manual":"📦"}
    chips = ""
    for c in citations:
        icon = icons.get(c["source_type"],"📎")
        label = html_lib.escape(c["label"])
        css_cls = c["source_type"]
        if c.get("url"):
            chips += f'<a href="{c["url"]}" target="_blank" style="text-decoration:none"><span class="cite-chip {css_cls}">{icon} {label}</span></a>'
        else:
            chips += f'<span class="cite-chip {css_cls}">{icon} {label}</span>'
    return f'<div class="cite-block"><div class="cite-label">📎 อ้างอิง</div>{chips}</div>'

# ══════════════════════════════════════════════════════════════════
# KONEX CALL — แยก temperature ตาม task type
# ══════════════════════════════════════════════════════════════════
TEMP_MAP = {"factual": 0.2, "creative": 0.72, "analysis": 0.4}

def detect_task_type(prompt: str) -> str:
    p = prompt.lower()
    if any(k in p for k in ["caption","บล็อก","blog","script","tiktok","facebook","เขียน","โปรโมท"]):
        return "creative"
    if any(k in p for k in ["สเปก","spec","รับประกัน","warranty","ราคา","price","ขนาด","ความหนา"]):
        return "factual"
    return "analysis"

def call_konex(user_msg: str, max_tokens: int = 3000, task_type: str = "analysis") -> str:
    temperature = TEMP_MAP.get(task_type, 0.4)
    ctx = build_full_context()
    hist = ""
    for m in st.session_state.kx_chat[-MAX_HISTORY_MSGS:]:
        role = "คุณ" if m["role"] == "user" else "KONEX"
        limit = MAX_HISTORY_CHARS if m["role"] == "user" else MAX_HISTORY_CHARS // 2
        hist += f"{role}: {m['content'][:limit]}\n"
    full_prompt = f"{ctx}\n\n## ประวัติสนทนา\n{hist}\n## คำถามใหม่\n{user_msg}"
    return _call_gemini_api(
        payload={
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
        },
        timeout=90,
    )

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
    st.page_link("ai_team.py",                       label="🤖 AI Special Team")
    st.page_link("pages/8_Workflow_Builder.py",       label="🏭 Content Factory")
    st.page_link("pages/9_Live_Chat.py",              label="💬 Live Chat")
    st.page_link("pages/10_Dashboard.py",             label="📊 Dashboard")
    st.page_link("pages/11_Budget_Cost_Manager.py",   label="💰 Budget & Cost")
    st.page_link("pages/12_Report_Generator.py",      label="📄 Report Generator")
    st.page_link("pages/13_Agent_Persona_Editor.py",  label="🧬 Agent Persona Editor")
    st.page_link("pages/14_Settings_Config.py",       label="⚙️ Settings & Config")
    st.page_link("pages/15_KONEX.py",                 label="🧠 KONEX")
    st.markdown("---")

    n_pdf  = len(st.session_state.kx_pdf_texts)
    n_prod = len(st.session_state.kx_products)
    n_comp = len(st.session_state.kx_competitors)
    n_blog = len(st.session_state.kx_blogs)

    def _dot(v): return "✅" if v else "○"
    def _col(v): return "#34d399" if v else "#334155"

    st.markdown(f"""
    <div style='padding:10px;background:rgba(15,23,42,.8);border:1px solid #1e293b;border-radius:8px;
      font-size:11px;font-family:IBM Plex Mono,monospace'>
      <div style='color:#38bdf8;margin-bottom:8px;font-weight:700'>🧠 KONEX MEMORY</div>
      <div style='color:#34d399;margin-bottom:3px'>✅ เว็บ aqualine.co.th</div>
      <div style='color:{_col(n_pdf)};margin-bottom:3px'>{_dot(n_pdf)} PDF {n_pdf} ไฟล์</div>
      <div style='color:{_col(n_prod)};margin-bottom:3px'>{_dot(n_prod)} สินค้า {n_prod} รายการ</div>
      <div style='color:{_col(n_comp)};margin-bottom:3px'>{_dot(n_comp)} คู่แข่ง {n_comp} ราย</div>
      <div style='color:{_col(n_blog)}'>{_dot(n_blog)} Blog {n_blog} บทความ</div>
    </div>""", unsafe_allow_html=True)

    if st.session_state.get("kx_ctx_truncated"):
        st.warning("⚠️ Context ใหญ่เกิน — PDF บางส่วนถูกตัด ลองลบไฟล์ที่ไม่ใช้")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    if st.button("🗑️ ล้างแชท", use_container_width=True, key="clr_chat_sb"):
        st.session_state.kx_chat = []
        _sync_to_store()
        st.rerun()
    if st.button("💣 ล้างทั้งหมด", use_container_width=True, key="clr_all_sb"):
        for k in ["kx_products","kx_competitors","kx_pdf_texts","kx_chat","kx_blogs"]:
            st.session_state[k] = []
        _sync_to_store()
        st.rerun()

# ══════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<div class="page-header">
  <div style='font-size:38px'>🧠</div>
  <div>
    <div class="page-title">KONEX <span class="konex-badge">BRAND INTELLIGENCE</span></div>
    <div class="page-sub">อ่าน PDF · จำเว็บ aqualine.co.th · เขียนบล็อก Wix · ตอบลูกค้า · Battle Card</div>
  </div>
</div>
""", unsafe_allow_html=True)

src = """<div style='display:flex;flex-wrap:wrap;gap:4px;margin-bottom:16px;align-items:center'>
<span style='font-family:IBM Plex Mono,monospace;font-size:10px;color:#334155;margin-right:4px'>SOURCES:</span>
<span class='source-pill active'>🌐 aqualine.co.th</span>"""
for pdf in st.session_state.kx_pdf_texts:
    src += f"<span class='source-pill active'>📄 {html_lib.escape(pdf['name'][:22])}</span>"
if st.session_state.kx_products:
    src += f"<span class='source-pill active'>📦 Manual {len(st.session_state.kx_products)} items</span>"
src += "</div>"
st.markdown(src, unsafe_allow_html=True)

if st.session_state.kx_products or st.session_state.kx_pdf_texts:
    st.markdown(f"""
    <div class="memory-badge" style='margin-bottom:12px'>
      <span>🟢</span>
      <span>KONEX ACTIVE — สินค้า {len(st.session_state.kx_products)} รายการ · PDF {len(st.session_state.kx_pdf_texts)} ไฟล์ · คู่แข่ง {len(st.session_state.kx_competitors)} ราย</span>
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════
tab_chat, tab_pdf, tab_blog, tab_products, tab_battle, tab_web, tab_brand, tab_export = st.tabs([
    "💬 KONEX Chat","📄 อัป PDF/Catalog","✍️ เขียนบล็อก (Wix)",
    "📦 สินค้า","⚔️ Battle Card","🌐 Web Agent","🏷️ แบรนด์","📥 Export"
])

# ══════════════════════════════════════════════════════════════════
# TAB 1 — CHAT
# ══════════════════════════════════════════════════════════════════
with tab_chat:
    st.markdown("<div class='section-title'>🎯 เลือก Product</div>", unsafe_allow_html=True)
    web_cats = ["หลังคา Smart Seam","หลังคา Big Seam","หลังคา Triple Seam",
                "หลังคา Freeform","หลังคา Sandwich Panel","รางน้ำฝน Lindab","ถังไฟเบอร์กลาส","ถังโพลีเอทิลีน"]
    all_products = (["🌐 (สินค้าทั้งหมด)"] + web_cats
                    + [p["name"] for p in st.session_state.kx_products]
                    + [f"📄 {p['name']}" for p in st.session_state.kx_pdf_texts])

    sel_col, info_col = st.columns([2, 3])
    with sel_col:
        selected_product = st.selectbox("สินค้า", all_products, key="qa_product_sel", label_visibility="collapsed")
    with info_col:
        if selected_product == "🌐 (สินค้าทั้งหมด)":
            st.markdown("<div style='font-size:11px;color:#475569;padding-top:8px'>Quick Actions ใช้ข้อมูลทุกสินค้า</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='font-size:11px;color:#38bdf8;padding-top:8px'>→ โฟกัสที่ <b>{html_lib.escape(selected_product)}</b></div>", unsafe_allow_html=True)

    prod_target = "" if selected_product == "🌐 (สินค้าทั้งหมด)" else f"สินค้า: {selected_product} — "

    st.markdown("<div class='section-title'>⚡ Quick Actions</div>", unsafe_allow_html=True)
    qa_cols = st.columns(5)
    quick_actions = [
        ("📝 Caption FB",    f"{prod_target}เขียน Caption Facebook โปรโมทให้น่าสนใจ ใช้จุดขายจริงจาก KONEX Memory",  "creative"),
        ("🎵 Script TikTok", f"{prod_target}เขียน Script TikTok 30 วินาที Hook แรกดึงดูด ใช้ข้อมูลจริง",              "creative"),
        ("💬 ตอบลูกค้า",    f"{prod_target}ลูกค้าถามว่า 'ทำไมต้องซื้อ Aqualine?' ตอบแบบ Expert",                      "analysis"),
        ("📊 เปรียบเทียบ",  f"{prod_target}ตารางเปรียบเทียบกับคู่แข่ง คุณภาพ ราคา รับประกัน ใช้ข้อมูลจริง",          "analysis"),
        ("✍️ บล็อกด่วน",   f"{prod_target}บทความบล็อก 300 คำ Wix SEO ใช้ข้อมูลจริงจาก KONEX Memory",                 "creative"),
    ]
    for col, (label, prompt, task_t) in zip(qa_cols, quick_actions):
        with col:
            if st.button(label, use_container_width=True, key=f"qa_{label}"):
                st.session_state.kx_chat.append({"role":"user","content":prompt,"time":datetime.now().strftime("%H:%M")})
                with st.spinner("🧠 KONEX กำลังค้นหา..."):
                    reply = call_konex(prompt, task_type=task_t)
                st.session_state.kx_chat.append({"role":"agent","content":reply,"time":datetime.now().strftime("%H:%M")})
                _sync_to_store()
                st.rerun()

    st.markdown("<div class='section-title'>💬 บทสนทนา</div>", unsafe_allow_html=True)
    if st.session_state.kx_chat:
        chat_html = ""
        for m in st.session_state.kx_chat:
            safe = html_lib.escape(m["content"]).replace("\n","<br>")
            t = html_lib.escape(m.get("time",""))
            if m["role"] == "user":
                chat_html += f'<div class="chat-msg-user"><div><div class="bubble">{safe}</div><div class="msg-time">{t}</div></div></div>'
            else:
                cite_html = render_citations(find_citations(m["content"]))
                chat_html += (f'<div class="chat-msg-agent"><div class="agent-icon-chip">🧠</div>'
                              f'<div><div style="font-family:IBM Plex Mono,monospace;font-size:9px;color:#38bdf8;margin-bottom:3px">KONEX · Brand Intelligence</div>'
                              f'<div class="bubble">{safe}{cite_html}</div>'
                              f'<div class="msg-time">{t}</div></div></div>')
        st.markdown(f'<div class="chat-wrap" style="max-height:500px;overflow-y:auto;padding:12px 0">{chat_html}</div>', unsafe_allow_html=True)
    else:
        st.markdown("""<div style='text-align:center;padding:40px;border:1px dashed #1e293b;border-radius:12px;
          color:#334155;font-family:IBM Plex Mono,monospace;font-size:12px'>
          <div style='font-size:36px;margin-bottom:8px'>🧠</div>
          KONEX พร้อมแล้ว — ลอง Quick Actions หรือพิมพ์คำถาม
        </div>""", unsafe_allow_html=True)

    ci, cs = st.columns([5, 1])
    with ci:
        inp = st.text_input("พิมพ์คำถาม...", key="kx_inp", label_visibility="collapsed",
            placeholder="เช่น เขียน Caption ถังเก็บน้ำ / อธิบายความแตกต่างหลังคาแต่ละรุ่น / สร้าง SEO Blog")
    with cs:
        send = st.button("🚀 ส่ง", use_container_width=True, type="primary", key="kx_send")
    if send and inp.strip():
        msg = inp.strip()
        st.session_state.kx_chat.append({"role":"user","content":msg,"time":datetime.now().strftime("%H:%M")})
        with st.spinner("🧠 KONEX กำลังค้นหา..."):
            reply = call_konex(msg, task_type=detect_task_type(msg))
        st.session_state.kx_chat.append({"role":"agent","content":reply,"time":datetime.now().strftime("%H:%M")})
        _sync_to_store()
        st.rerun()

# ══════════════════════════════════════════════════════════════════
# TAB 2 — PDF UPLOAD
# ══════════════════════════════════════════════════════════════════
with tab_pdf:
    st.markdown("""
    <div style='background:rgba(56,189,248,.06);border:1px solid rgba(56,189,248,.2);border-radius:10px;padding:14px 18px;margin-bottom:16px'>
      <div style='font-family:IBM Plex Mono,monospace;font-size:12px;font-weight:700;color:#38bdf8;margin-bottom:4px'>
        📄 อัป PDF แล้ว KONEX อ่านเองเลย
      </div>
      <div style='font-size:12px;color:#64748b'>Catalog · Brochure · Price List · Spec Sheet — Gemini 2.5 Flash อ่านโดยตรง</div>
    </div>""", unsafe_allow_html=True)

    uploaded_pdfs = st.file_uploader("อัป PDF", type=["pdf"],
        accept_multiple_files=True, key="pdf_uploader", label_visibility="collapsed")
    if uploaded_pdfs:
        for upf in uploaded_pdfs:
            if not any(p["name"] == upf.name for p in st.session_state.kx_pdf_texts):
                with st.spinner(f"📖 อ่าน '{upf.name}'..."):
                    b64 = base64.b64encode(upf.read()).decode("utf-8")
                    extracted = extract_pdf_with_gemini(b64, upf.name)
                    st.session_state.kx_pdf_texts.append({
                        "name": upf.name,
                        "text": extracted[:MAX_PDF_TEXT_CHARS],
                        "uploaded_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "size_kb": round(len(b64) * 0.75 / 1024, 1),
                    })
                    _sync_to_store()
                st.rerun()

    if st.session_state.kx_pdf_texts:
        st.markdown(f"<div class='section-title'>📚 PDF ในความจำ ({len(st.session_state.kx_pdf_texts)} ไฟล์)</div>", unsafe_allow_html=True)
        for i, pdf in enumerate(st.session_state.kx_pdf_texts):
            cp, cask, cdel = st.columns([4, 1, 1])
            with cp:
                preview = html_lib.escape(pdf['text'][:200]) + ('...' if len(pdf['text']) > 200 else '')
                st.markdown(f"""
                <div class="product-card">
                  <div style='display:flex;justify-content:space-between;align-items:center'>
                    <div>
                      <div class="product-name">📄 {html_lib.escape(pdf['name'])}</div>
                      <div style='font-size:10px;color:#334155;font-family:IBM Plex Mono,monospace;margin-top:2px'>
                        {pdf.get('uploaded_at','')} · {pdf.get('size_kb',0)} KB
                      </div>
                    </div>
                    <span class='tag tag-green'>✅ อ่านแล้ว</span>
                  </div>
                  <div style='margin-top:8px;font-size:11px;color:#475569;background:rgba(30,41,59,.4);
                    padding:8px;border-radius:6px;border-left:2px solid #38bdf8'>{preview}</div>
                </div>""", unsafe_allow_html=True)
            with cask:
                if st.button("💬 ถาม", key=f"ask_pdf_{i}", use_container_width=True):
                    q = f"สรุปข้อมูลสำคัญจาก PDF '{pdf['name']}' แนะนำว่าจะเขียน Content อะไรได้บ้าง"
                    st.session_state.kx_chat.append({"role":"user","content":q,"time":datetime.now().strftime("%H:%M")})
                    with st.spinner("🧠 วิเคราะห์..."):
                        r = call_konex(q, task_type="analysis")
                    st.session_state.kx_chat.append({"role":"agent","content":r,"time":datetime.now().strftime("%H:%M")})
                    _sync_to_store()
                    st.rerun()
            with cdel:
                if st.button("🗑️", key=f"del_pdf_{i}", use_container_width=True):
                    st.session_state.kx_pdf_texts.pop(i)
                    _sync_to_store()
                    st.rerun()
            with st.expander(f"📖 ดูข้อมูลเต็ม — {pdf['name']}"):
                st.markdown(pdf["text"])
    else:
        st.markdown("""
        <div style='border:2px dashed #1e293b;border-radius:12px;padding:40px;text-align:center'>
          <div style='font-size:40px;margin-bottom:8px'>📄</div>
          <div style='font-family:IBM Plex Mono,monospace;font-size:13px;color:#475569'>ลาก PDF มาวางหรือคลิกเลือกไฟล์</div>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# TAB 3 — BLOG WRITER
# ══════════════════════════════════════════════════════════════════
with tab_blog:
    st.markdown("""
    <div style='background:rgba(167,139,250,.06);border:1px solid rgba(167,139,250,.2);border-radius:10px;padding:14px 18px;margin-bottom:16px'>
      <div style='font-family:IBM Plex Mono,monospace;font-size:12px;font-weight:700;color:#a78bfa;margin-bottom:4px'>
        ✍️ เขียนบล็อก Wix SEO — ใช้ข้อมูลจริงจาก KONEX Memory
      </div>
    </div>""", unsafe_allow_html=True)

    col_form, col_out = st.columns([1, 1.1])
    with col_form:
        blog_type  = st.selectbox("ประเภทบทความ", [
            "📚 บทความให้ความรู้ (How-to / Guide)",
            "🏆 เปรียบเทียบสินค้า (Comparison)",
            "💡 แก้ปัญหาลูกค้า (Problem-Solution)",
            "📣 โปรโมทสินค้า (Product Highlight)",
            "🌟 Case Study / ผลงาน",
            "🔍 SEO Long-tail Keyword Article",
        ], key="blog_type_sel")
        blog_topic = st.text_input("หัวข้อบทความ", placeholder="เช่น วิธีเลือกรางน้ำฝน", key="blog_topic_inp")
        blog_kw    = st.text_input("Keywords SEO", placeholder="เช่น รางน้ำฝน, ถังเก็บน้ำ", key="blog_kw_inp")
        blog_len   = st.select_slider("ความยาว",
            options=["สั้น (300 คำ)","กลาง (600 คำ)","ยาว (1,000 คำ)","ยาวมาก (1,500+ คำ)"],
            value="กลาง (600 คำ)", key="blog_len_sl")
        blog_tone  = st.selectbox("Tone", [
            "มืออาชีพ แต่อ่านง่าย","เป็นกันเอง เข้าถึงง่าย",
            "เชิงวิชาการ เชิงลึก","กระตุ้นการตัดสินใจซื้อ",
        ], key="blog_tone_sel")
        include_opts = st.multiselect("รวมใน Output", [
            "Meta Title (SEO)","Meta Description","Suggested Tags",
            "Internal Links","Call-to-Action","รูปแบบ Wix Blog HTML",
        ], default=["Meta Title (SEO)","Meta Description","Call-to-Action"], key="blog_incl_ms")

        st.markdown("<div class='section-title'>🔗 URL สินค้า</div>", unsafe_allow_html=True)
        blog_product_url = st.text_input("URL หน้าสินค้า", key="blog_prod_url",
            placeholder="https://www.aqualine.co.th/...", label_visibility="collapsed")
        pc1, pc2, pc3, pc4 = st.columns(4)
        _preset_map = {
            "pre_ts": "https://www.aqualine.co.th/aqualine-roof-triple-seam-insulated-660",
            "pre_ss": "https://www.aqualine.co.th/aqualine-roof-smart-seam-insulated-600",
            "pre_bs": "https://www.aqualine.co.th/aqualine-roof-big-seam-insulated-700",
            "pre_rn": "https://www.aqualine.co.th/raingutter",
        }
        for _col, (_key, _label) in zip(
            [pc1, pc2, pc3, pc4],
            [("pre_ts","Triple Seam"),("pre_ss","Smart Seam"),("pre_bs","Big Seam"),("pre_rn","รางน้ำฝน")]
        ):
            with _col:
                if st.button(_label, key=_key, use_container_width=True):
                    st.session_state["_blog_prod_url_preset"] = _preset_map[_key]
                    st.rerun()

        # ใช้ค่า preset ถ้ามี แล้วล้างทิ้ง
        if st.session_state.get("_blog_prod_url_preset"):
            blog_product_url = st.session_state.pop("_blog_prod_url_preset")
        # blog_product_url ที่ใช้ด้านล่างจะเป็นค่าจาก text_input หรือ preset
        gen_blog = st.button("✍️ เขียนบทความ", use_container_width=True, type="primary", key="gen_blog_btn")

    with col_out:
        st.markdown("<div class='section-title'>📄 บทความ</div>", unsafe_allow_html=True)
        if gen_blog:
            if blog_topic.strip():
                product_data_note = ""
                fetched_url = blog_product_url.strip() if blog_product_url else st.session_state.get("blog_prod_url","").strip()
                if not fetched_url:
                    tl = blog_topic.lower()
                    for pname, purl in AQUALINE_WEB["product_urls"].items():
                        if any(k in tl for k in pname.lower().split()):
                            fetched_url = purl
                            break

                if fetched_url:
                    slug = fetched_url.split("/")[-1]
                    already_cached = any(p.get("source_url") == fetched_url for p in st.session_state.kx_pdf_texts)
                    if not already_cached:
                        with st.spinner(f"🌐 ดึงข้อมูลจาก {fetched_url}..."):
                            ft = fetch_and_cache_product_url(fetched_url, slug)
                        if not ft.startswith("⚠️"):
                            st.success("✅ ดึงข้อมูลสินค้าแล้ว")
                            product_data_note = f"\n\n**ข้อมูลจาก {fetched_url}:**\n{ft[:4000]}"
                        else:
                            st.warning("⚠️ ดึง URL ไม่ได้ ใช้ข้อมูลจาก Memory")
                    else:
                        cached = next((p for p in st.session_state.kx_pdf_texts if p.get("source_url") == fetched_url), None)
                        if cached:
                            product_data_note = f"\n\n**ข้อมูล cache จาก {fetched_url}:**\n{cached['text'][:4000]}"
                            st.info(f"📦 ใช้ข้อมูล cache")

                prompt = f"""เขียนบทความ Wix Blog สำหรับ AQUALINE (aqualine.co.th/blog)

ประเภท: {blog_type}
หัวข้อ: {blog_topic}
Keywords: {blog_kw}
ความยาว: {blog_len}
Tone: {blog_tone}
รวม: {', '.join(include_opts)}

กฎเหล็ก:
1. ใช้ข้อมูลจริงเท่านั้น ห้ามแต่งสเปคหรือรับประกัน
2. อ้างอิง [จาก {fetched_url or 'aqualine.co.th'}] ทุกครั้ง
3. SEO keyword "{blog_kw}" ใน heading, body, meta
{product_data_note}"""

                with st.spinner("✍️ เขียนบทความ..."):
                    result = call_konex(prompt, max_tokens=4096, task_type="creative")
                st.session_state.kx_blogs.append({
                    "id": pid(), "title": blog_topic, "type": blog_type,
                    "content": result, "keywords": blog_kw,
                    "source_url": fetched_url,
                    "created": datetime.now().strftime("%d/%m/%Y %H:%M"),
                })
                _sync_to_store()
                st.download_button("📥 Download (.txt)", data=result,
                    file_name=f"blog_{blog_topic[:20].replace(' ','_')}_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain", use_container_width=True, key="dl_blog_btn")
                safe_r = html_lib.escape(result).replace("\n","<br>")
                cite_html = render_citations(find_citations(result))
                src_badge = html_lib.escape(f"🌐 {fetched_url.split('/')[-1]}" if fetched_url else "💾 Memory")
                st.markdown(f"""
                <div style='background:rgba(15,23,42,.9);border:1px solid rgba(167,139,250,.25);border-radius:12px;
                  padding:20px;max-height:480px;overflow-y:auto;font-size:12px;color:#cbd5e1;line-height:1.8'>
                  <div style='font-family:IBM Plex Mono,monospace;font-size:10px;color:#a78bfa;margin-bottom:10px;
                    display:flex;justify-content:space-between'>
                    <span>✍️ {html_lib.escape(blog_topic)}</span>
                    <span style='color:#34d399;border:1px solid rgba(52,211,153,.25);padding:2px 8px;border-radius:6px'>{src_badge}</span>
                  </div>
                  {safe_r}{cite_html}
                </div>""", unsafe_allow_html=True)
            else:
                st.warning("⚠️ กรุณาใส่หัวข้อบทความก่อน")
        else:
            if st.session_state.kx_blogs:
                for i, b in enumerate(reversed(st.session_state.kx_blogs)):
                    ri = len(st.session_state.kx_blogs) - 1 - i
                    cb, cbd = st.columns([4, 1])
                    with cb:
                        st.markdown(f"""
                        <div class="blog-card">
                          <div class="blog-title">{html_lib.escape(b['title'])}</div>
                          <div class="blog-meta">{html_lib.escape(b.get('type',''))} · {b.get('created','')} · {html_lib.escape(b.get('keywords',''))}</div>
                          <div class="blog-preview">{html_lib.escape(b['content'][:150])}...</div>
                        </div>""", unsafe_allow_html=True)
                    with cbd:
                        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                        st.download_button("📥", data=b["content"],
                            file_name=f"blog_{ri}.txt", mime="text/plain",
                            key=f"dl_b_{ri}", use_container_width=True)
                        if st.button("🗑️", key=f"del_b_{ri}", use_container_width=True):
                            st.session_state.kx_blogs.pop(ri)
                            _sync_to_store()
                            st.rerun()
            else:
                st.markdown("""<div style='text-align:center;padding:40px;border:1px dashed #1e293b;border-radius:10px;
                  color:#334155;font-family:IBM Plex Mono,monospace;font-size:12px'>
                  กรอกหัวข้อด้านซ้าย แล้วกด "เขียนบทความ"</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# TAB 4 — PRODUCTS
# ══════════════════════════════════════════════════════════════════
with tab_products:
    st.markdown("<div class='section-title'>➕ เพิ่มสินค้า</div>", unsafe_allow_html=True)
    with st.form("add_prod_form", clear_on_submit=True):
        rc1, rc2, rc3 = st.columns(3)
        with rc1: fn = st.text_input("ชื่อสินค้า *")
        with rc2: fm = st.text_input("รหัส / รุ่น")
        with rc3: fc = st.selectbox("หมวดหมู่", CATS)
        rp1, rp2 = st.columns(2)
        with rp1: fp = st.text_input("ราคาปกติ")
        with rp2: fpr = st.text_input("โปรโมชัน")
        fsp = st.text_area("สเปก", height=70)
        fu  = st.text_area("USP / จุดขาย *", height=70)
        rg1, rg2 = st.columns(2)
        with rg1: ftg = st.multiselect("กลุ่มลูกค้า", TGTS, default=["บ้านพักอาศัย"])
        with rg2: fex = st.text_input("ข้อมูลเพิ่มเติม")
        if st.form_submit_button("💾 บันทึก", use_container_width=True, type="primary"):
            if fn and fu:
                st.session_state.kx_products.append({
                    "id": pid(), "name": fn, "model": fm, "category": fc,
                    "price": fp, "promo": fpr, "spec": fsp, "usp": fu,
                    "target": ", ".join(ftg), "extra": fex,
                    "created": datetime.now().strftime("%d/%m/%Y %H:%M"),
                })
                _sync_to_store()
                st.success(f"✅ เพิ่ม '{fn}'")
                st.rerun()
            else:
                st.warning("⚠️ กรุณากรอก ชื่อสินค้า และ USP")

    if st.session_state.kx_products:
        st.markdown(f"<div class='section-title'>📦 สินค้า ({len(st.session_state.kx_products)} รายการ)</div>", unsafe_allow_html=True)
        srch = st.text_input("🔍 ค้นหา", key="srch_prod", label_visibility="collapsed", placeholder="ค้นหา...")
        for i, p in enumerate(st.session_state.kx_products):
            if srch and srch.lower() not in f"{p['name']} {p.get('model','')}".lower():
                continue
            cc, cd = st.columns([5, 1])
            with cc:
                promo_html = f"<div style='margin-top:4px'><span class='tag tag-amber'>🏷️ {html_lib.escape(p['promo'])}</span></div>" if p.get('promo') else ""
                st.markdown(f"""
                <div class="product-card">
                  <div style='display:flex;justify-content:space-between'>
                    <div>
                      <div class="product-name">{html_lib.escape(p['name'])}</div>
                      <div class="product-model">{html_lib.escape(p.get('model',''))} · {html_lib.escape(p.get('category',''))}</div>
                    </div>
                    <div class="product-price">{html_lib.escape(p.get('price','—'))}</div>
                  </div>
                  <div style='font-size:12px;color:#64748b;margin-top:6px'>{html_lib.escape(p.get('usp','')[:100])}</div>
                  {promo_html}
                </div>""", unsafe_allow_html=True)
            with cd:
                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                if st.button("💬 AI", key=f"ask_p_{i}", use_container_width=True):
                    q = f"เขียน Caption โปรโมท {p['name']} ให้น่าสนใจ ใช้จุดขายจริง"
                    st.session_state.kx_chat.append({"role":"user","content":q,"time":datetime.now().strftime("%H:%M")})
                    with st.spinner("🧠 กำลังเขียน..."):
                        reply = call_konex(q, task_type="creative")
                    st.session_state.kx_chat.append({"role":"agent","content":reply,"time":datetime.now().strftime("%H:%M")})
                    _sync_to_store()
                    st.rerun()
                if st.button("🗑️", key=f"del_kx_p_{i}", use_container_width=True):
                    st.session_state.kx_products.pop(i)
                    _sync_to_store()
                    st.rerun()

# ══════════════════════════════════════════════════════════════════
# TAB 5 — BATTLE CARD
# ══════════════════════════════════════════════════════════════════
with tab_battle:
    st.markdown("""
    <div style='background:rgba(248,113,113,.06);border:1px solid rgba(248,113,113,.2);border-radius:10px;padding:14px 18px;margin-bottom:16px'>
      <div style='font-family:IBM Plex Mono,monospace;font-size:12px;font-weight:700;color:#f87171;margin-bottom:4px'>
        ⚔️ Competitor Battle Card
      </div>
      <div style='font-size:12px;color:#64748b'>ใส่ชื่อคู่แข่ง → AI สร้าง "ทำไมต้องเลือก Aqualine"</div>
    </div>""", unsafe_allow_html=True)

    bc1, bc2 = st.columns([1, 1])
    with bc1:
        st.markdown("<div class='section-title'>➕ เพิ่มคู่แข่ง</div>", unsafe_allow_html=True)
        with st.form("add_comp_form", clear_on_submit=True):
            cn   = st.text_input("ชื่อคู่แข่ง *", placeholder="เช่น SCG, Monier")
            cd_i = st.text_input("จุดแข็งคู่แข่ง")
            cw   = st.text_input("จุดอ่อนคู่แข่ง")
            cdf  = st.text_area("เราดีกว่าตรงไหน *", height=80)
            if st.form_submit_button("➕ เพิ่ม", use_container_width=True):
                if cn and cdf:
                    st.session_state.kx_competitors.append({"id":pid(),"name":cn,"desc":cd_i,"weak":cw,"diff":cdf})
                    _sync_to_store()
                    st.success(f"✅ เพิ่ม {cn}")
                    st.rerun()

        st.markdown("<div class='section-title'>🤖 AI สร้าง Battle Card</div>", unsafe_allow_html=True)
        comp_name = st.text_input("ชื่อคู่แข่ง", placeholder="เช่น Grando, SCG", key="battle_inp")
        if st.button("⚔️ สร้าง Battle Card", use_container_width=True, type="primary", key="gen_battle_btn"):
            if comp_name.strip():
                q = f"""Battle Card: AQUALINE vs {comp_name}
1. จุดแข็ง {comp_name} ที่ลูกค้าอาจถาม
2. วิธีตอบโต้ — เน้น Aqualine
3. คำถาม Sales ควรถามเพื่อ highlight Aqualine
4. สรุป Why Aqualine wins
ใช้ข้อมูลจาก KONEX Memory"""
                with st.spinner(f"⚔️ สร้าง Battle Card..."):
                    result = call_konex(q, max_tokens=2048, task_type="analysis")
                st.session_state.kx_chat.append({"role":"user","content":q,"time":datetime.now().strftime("%H:%M")})
                st.session_state.kx_chat.append({"role":"agent","content":result,"time":datetime.now().strftime("%H:%M")})
                _sync_to_store()
                safe_r = html_lib.escape(result).replace("\n","<br>")
                st.markdown(f"""
                <div style='background:rgba(15,23,42,.9);border:1px solid rgba(248,113,113,.25);
                  border-radius:12px;padding:18px;margin-top:8px;font-size:12px;color:#cbd5e1;line-height:1.8'>
                  <div style='font-family:IBM Plex Mono,monospace;font-size:10px;color:#f87171;margin-bottom:8px'>
                    ⚔️ BATTLE CARD: Aqualine vs {html_lib.escape(comp_name)}</div>
                  {safe_r}
                </div>""", unsafe_allow_html=True)
            else:
                st.warning("⚠️ ใส่ชื่อคู่แข่งก่อน")

    with bc2:
        st.markdown("<div class='section-title'>📋 คู่แข่งในความจำ</div>", unsafe_allow_html=True)
        if st.session_state.kx_competitors:
            for i, c in enumerate(st.session_state.kx_competitors):
                cv, cdel = st.columns([5, 1])
                with cv:
                    st.markdown(f"""
                    <div style='border:1px solid #1e293b;border-radius:12px;padding:14px;margin-bottom:8px'>
                      <div style='font-family:IBM Plex Mono,monospace;font-size:13px;font-weight:700;color:#f87171;margin-bottom:8px'>⚔️ {html_lib.escape(c['name'])}</div>
                      <div class="vs-them">
                        <div style='font-size:10px;color:#f87171;margin-bottom:3px'>พวกเขา</div>
                        <div style='font-size:11px;color:#94a3b8'>💪 {html_lib.escape(c.get('desc','—'))}</div>
                        <div style='font-size:11px;color:#94a3b8'>😮 {html_lib.escape(c.get('weak','—'))}</div>
                      </div>
                      <div class="vs-us">
                        <div style='font-size:10px;color:#34d399;margin-bottom:3px'>เรา (Aqualine)</div>
                        <div style='font-size:11px;color:#34d399'>✅ {html_lib.escape(c.get('diff',''))}</div>
                      </div>
                    </div>""", unsafe_allow_html=True)
                with cdel:
                    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
                    if st.button("🗑️", key=f"del_kx_c_{i}", use_container_width=True):
                        st.session_state.kx_competitors.pop(i)
                        _sync_to_store()
                        st.rerun()

# ══════════════════════════════════════════════════════════════════
# TAB 6 — WEB AGENT
# ══════════════════════════════════════════════════════════════════
with tab_web:
    st.markdown("""
    <div style='background:rgba(52,211,153,.06);border:1px solid rgba(52,211,153,.2);border-radius:10px;padding:14px 18px;margin-bottom:16px'>
      <div style='font-family:IBM Plex Mono,monospace;font-size:12px;font-weight:700;color:#34d399;margin-bottom:4px'>
        🌐 Web Agent — HTML + Google Search Grounding
      </div>
      <div style='font-size:12px;color:#64748b'>แก้ปัญหา Wix JS-rendered — ข้อมูลสินค้าแม่นยำขึ้น</div>
    </div>""", unsafe_allow_html=True)

    wc1, wc2 = st.columns([1.2, 0.8])
    with wc1:
        st.markdown("<div class='section-title'>🔗 URL</div>", unsafe_allow_html=True)
        preset_urls = {
            "🏠 หน้าหลัก":          "https://www.aqualine.co.th",
            "📝 บล็อก":              "https://www.aqualine.co.th/blog",
            "🌧️ รางน้ำฝน Lindab":   "https://www.aqualine.co.th/raingutter",
            "🏗️ Triple Seam 660":   "https://www.aqualine.co.th/aqualine-roof-triple-seam-insulated-660",
            "🏗️ Smart Seam 600":    "https://www.aqualine.co.th/aqualine-roof-smart-seam-insulated-600",
            "🏗️ Big Seam 700":      "https://www.aqualine.co.th/aqualine-roof-big-seam-insulated-700",
            "📥 Brochure Download": "https://www.aqualine.co.th/download-brochure-aqualine-products",
        }
        sel_preset = st.selectbox("Preset", list(preset_urls.keys()), key="web_preset")
        manual_url = st.text_input("หรือใส่ URL เอง", placeholder="https://...", key="manual_url_inp")
        target_url = manual_url.strip() if manual_url.strip() else preset_urls[sel_preset]
        st.markdown(f"<div style='font-size:11px;color:#38bdf8;font-family:IBM Plex Mono,monospace;margin-bottom:8px'>→ {html_lib.escape(target_url)}</div>", unsafe_allow_html=True)
        save_to_mem = st.checkbox("💾 บันทึกเข้า Memory", value=True, key="web_save_mem")
        web_q = st.text_area("ถาม KONEX", placeholder="สรุปจุดเด่น / ดึงสเปกและรับประกัน / เขียน Caption",
            height=80, key="web_q_inp")
        fetch_btn = st.button("🌐 ดึงข้อมูลและถาม", use_container_width=True, type="primary", key="fetch_web_btn")

    with wc2:
        st.markdown("<div class='section-title'>📊 ผลลัพธ์</div>", unsafe_allow_html=True)
        if fetch_btn:
            with st.spinner(f"🌐 กำลังอ่าน {target_url}..."):
                page_text = fetch_product_page_with_gemini(target_url)
            if page_text.startswith("⚠️"):
                st.error(page_text)
            else:
                if save_to_mem:
                    cache_label = f"🌐 {target_url.split('/')[-1] or 'aqualine.co.th'}"
                    if not any(p.get("source_url") == target_url for p in st.session_state.kx_pdf_texts):
                        st.session_state.kx_pdf_texts.append({
                            "name": cache_label,
                            "text": page_text[:MAX_PDF_TEXT_CHARS],
                            "uploaded_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "size_kb": round(len(page_text) / 1024, 1),
                            "source_url": target_url,
                        })
                        _sync_to_store()
                        st.success("✅ บันทึกเข้า Memory")
                uq = web_q.strip() if web_q.strip() else "สรุปจุดเด่นและข้อมูลสำคัญ แนะนำว่าจะเขียน Content อะไรได้"
                q = f"ข้อมูลจาก {target_url}:\n{page_text[:4000]}\n---\n{uq}\nอ้างอิง [หน้าสินค้า {target_url}]"
                reply = call_konex(q, max_tokens=2048, task_type="analysis")
                st.session_state.kx_chat.append({"role":"user","content":f"ดึงข้อมูลจาก: {target_url}\n{web_q}","time":datetime.now().strftime("%H:%M")})
                st.session_state.kx_chat.append({"role":"agent","content":reply,"time":datetime.now().strftime("%H:%M")})
                _sync_to_store()
                safe_r = html_lib.escape(reply).replace("\n","<br>")
                st.markdown(f"""
                <div style='background:rgba(15,23,42,.9);border:1px solid rgba(52,211,153,.25);
                  border-radius:10px;padding:16px;font-size:12px;color:#cbd5e1;line-height:1.8;max-height:380px;overflow-y:auto'>
                  <div style='font-family:IBM Plex Mono,monospace;font-size:9px;color:#34d399;margin-bottom:8px'>
                    🌐 {html_lib.escape(target_url)}</div>
                  {safe_r}
                </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# TAB 7 — BRAND
# ══════════════════════════════════════════════════════════════════
with tab_brand:
    st.markdown("<div class='section-title'>🏷️ ข้อมูลแบรนด์</div>", unsafe_allow_html=True)
    brand = st.session_state.kx_brand
    with st.form("brand_kx_form"):
        bb1, bb2 = st.columns(2)
        with bb1:
            bn  = st.text_input("ชื่อแบรนด์", value=brand.get("name","AQUALINE Protarget"))
            bt  = st.selectbox("Tone & Voice", TONES,
                index=TONES.index(brand.get("tone",TONES[0])) if brand.get("tone") in TONES else 0)
            bw  = st.text_input("เว็บไซต์", value=brand.get("website", AQUALINE_WEB["url"]))
        with bb2:
            btg = st.text_input("กลุ่มลูกค้าหลัก", value=brand.get("target",""))
            bs  = st.text_input("จุดแข็งหลัก", value=brand.get("strength",""))
        bd  = st.text_area("คำอธิบายแบรนด์", value=brand.get("desc",""), height=90)
        bex = st.text_area("ห้ามพูดถึง", value=brand.get("avoid",""), height=60)
        if st.form_submit_button("💾 บันทึก", use_container_width=True, type="primary"):
            st.session_state.kx_brand = {"name":bn,"tone":bt,"target":btg,"strength":bs,"desc":bd,"website":bw,"avoid":bex}
            _sync_to_store()
            st.success("✅ บันทึกแบรนด์แล้ว")
            st.rerun()

    with st.expander("👁️ Preview Context"):
        b = st.session_state.kx_brand
        st.markdown(f"""
        <div style='background:rgba(15,23,42,.9);border:1px solid #1e293b;border-radius:8px;padding:14px;
          font-size:12px;color:#94a3b8;line-height:1.8;font-family:IBM Plex Mono,monospace'>
          <b style='color:#38bdf8'>แบรนด์:</b> {html_lib.escape(b.get('name',''))} · <b style='color:#38bdf8'>Tone:</b> {html_lib.escape(b.get('tone',''))}<br>
          <b style='color:#38bdf8'>กลุ่มลูกค้า:</b> {html_lib.escape(b.get('target',''))}<br>
          <b style='color:#38bdf8'>จุดแข็ง:</b> {html_lib.escape(b.get('strength',''))}
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# TAB 8 — EXPORT / IMPORT
# ══════════════════════════════════════════════════════════════════
with tab_export:
    st.markdown("<div class='section-title'>💾 Export / Import KONEX Memory</div>", unsafe_allow_html=True)
    full_mem = {
        "exported_at":  datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "brand":        st.session_state.kx_brand,
        "products":     st.session_state.kx_products,
        "competitors":  st.session_state.kx_competitors,
        "pdf_texts":    st.session_state.kx_pdf_texts,
        "blogs":        [{"title":b["title"],"created":b["created"]} for b in st.session_state.kx_blogs],
    }
    ec1, ec2 = st.columns(2)
    with ec1:
        st.markdown("""
        <div style='background:rgba(15,23,42,.8);border:1px solid #1e293b;border-radius:10px;padding:16px;margin-bottom:12px'>
          <div style='font-family:IBM Plex Mono,monospace;font-size:12px;font-weight:700;color:#e2e8f0;margin-bottom:4px'>📥 Export ความจำ</div>
          <div style='font-size:11px;color:#475569'>สินค้า · แบรนด์ · PDF · คู่แข่ง</div>
        </div>""", unsafe_allow_html=True)
        st.download_button("💾 Download JSON",
            data=json.dumps(full_mem, ensure_ascii=False, indent=2),
            file_name=f"konex_memory_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json", use_container_width=True, key="exp_konex")
        st.download_button("📝 Download Context Text",
            data=build_full_context(),
            file_name=f"konex_context_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain", use_container_width=True, key="exp_konex_txt")

    with ec2:
        st.markdown("""
        <div style='background:rgba(15,23,42,.8);border:1px solid #1e293b;border-radius:10px;padding:16px;margin-bottom:12px'>
          <div style='font-family:IBM Plex Mono,monospace;font-size:12px;font-weight:700;color:#e2e8f0;margin-bottom:4px'>📤 Import ความจำ</div>
          <div style='font-size:11px;color:#475569'>โหลดข้อมูลที่ export ไว้กลับเข้าระบบ</div>
        </div>""", unsafe_allow_html=True)
        imp = st.file_uploader("เลือกไฟล์ JSON", type=["json"], key="imp_konex")
        if imp:
            try:
                d = json.loads(imp.read().decode("utf-8"))
                n_p = len(d.get("products", []))
                n_c = len(d.get("competitors", []))
                st.markdown(f"""<div style='font-size:11px;color:#fbbf24;font-family:IBM Plex Mono,monospace;margin-bottom:8px'>
                  ⚠️ Import: สินค้า {n_p} รายการ · คู่แข่ง {n_c} ราย
                  {" · แบรนด์" if d.get("brand") else ""}
                  {" · PDF " + str(len(d.get("pdf_texts",[]))) + " ไฟล์" if d.get("pdf_texts") else ""}
                </div>""", unsafe_allow_html=True)
                if st.button("✅ Import เลย", use_container_width=True, type="primary", key="do_import"):
                    if d.get("brand"):       st.session_state.kx_brand       = d["brand"]
                    if d.get("products"):    st.session_state.kx_products    = d["products"]
                    if d.get("competitors"): st.session_state.kx_competitors = d["competitors"]
                    if d.get("pdf_texts"):   st.session_state.kx_pdf_texts   = d["pdf_texts"]
                    _sync_to_store()
                    st.success("✅ Import สำเร็จ!")
                    st.rerun()
            except json.JSONDecodeError as e:
                st.error(f"❌ JSON ไม่ถูกต้อง: {e}")
            except UnicodeDecodeError:
                st.error("❌ Encoding ผิด — ใช้ UTF-8")
            except Exception as e:
                st.error(f"❌ Import ผิดพลาด: {str(e)[:80]}")

    st.markdown("<div class='section-title'>👁️ Raw Context Preview</div>", unsafe_allow_html=True)
    with st.expander("ดู Context"):
        ctx_preview = build_full_context()
        st.markdown(f"**ขนาด:** {len(ctx_preview):,} chars (~{len(ctx_preview)//4:,} tokens)")
        st.code(ctx_preview, language="markdown")