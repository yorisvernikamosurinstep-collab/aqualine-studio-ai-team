import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import os
import time
import base64
import mimetypes
import random
from datetime import datetime
import re
from io import BytesIO

st.set_page_config(
    page_title="Live Chat — AQUALINE AI TEAM",
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
.chat-header{background:linear-gradient(90deg,#0d1117,#0f172a,#0d1117);border-bottom:1px solid #1e293b;
  padding:16px 24px;display:flex;align-items:center;gap:16px;position:relative;overflow:hidden;}
.chat-header::after{content:'';position:absolute;inset:0;
  background:repeating-linear-gradient(90deg,transparent,transparent 80px,rgba(56,189,248,.03) 80px,rgba(56,189,248,.03) 81px);
  pointer-events:none;}
.chat-header-title{font-family:'IBM Plex Mono',monospace;font-size:18px;font-weight:700;color:#f1f5f9;}
.chat-header-sub{font-size:11px;color:#475569;font-family:'IBM Plex Mono',monospace;margin-top:2px;}
.online-dot{width:8px;height:8px;border-radius:50%;background:#34d399;box-shadow:0 0 8px #34d399;
  animation:pulse-dot 2s infinite;display:inline-block;margin-right:5px;}
@keyframes pulse-dot{0%,100%{opacity:1}50%{opacity:.4}}

/* attach pills */
.attach-pill{display:inline-flex;align-items:center;gap:6px;background:rgba(15,23,42,.9);
  border:1px solid #1e293b;border-radius:20px;padding:5px 10px;font-size:11px;color:#94a3b8;
  font-family:'IBM Plex Mono',monospace;margin:2px;}
.attach-pill img{width:28px;height:28px;border-radius:4px;object-fit:cover;}
.attach-badge{background:rgba(56,189,248,.12);border:1px solid rgba(56,189,248,.3);border-radius:6px;
  padding:2px 8px;font-size:10px;color:#38bdf8;}

/* agent card */
.agent-card{display:flex;align-items:center;gap:10px;padding:8px 12px;border-radius:10px;
  background:rgba(15,23,42,.6);border:1px solid #1e293b;margin-bottom:6px;cursor:pointer;transition:all .2s;}
.agent-card:hover{border-color:#38bdf8;}
.agent-card.selected{border-color:rgba(56,189,248,.5);background:rgba(56,189,248,.05);}
.agent-card-name{font-size:12px;font-weight:600;color:#e2e8f0;}
.agent-card-role{font-size:10px;color:#475569;margin-top:1px;}
.agent-card-img{width:36px;height:36px;border-radius:50%;object-fit:cover;border:1px solid #1e293b;background:#0f172a;flex-shrink:0;}

/* search bar */
.search-wrap{background:rgba(15,23,42,.8);border:1px solid #1e293b;border-radius:8px;
  display:flex;align-items:center;gap:8px;padding:6px 12px;margin-bottom:8px;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# AGENTS
# ══════════════════════════════════════════════════════════════════
AGENTS = {
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
AGENTS_FOLDER = "agents"

# ══════════════════════════════════════════════════════════════════
# FILE SUPPORT
# ══════════════════════════════════════════════════════════════════
INLINE_TYPES = {
    "image/jpeg":"🖼️","image/png":"🖼️","image/webp":"🖼️","image/gif":"🖼️",
    "image/heic":"🖼️","image/heif":"🖼️",
    "application/pdf":"📄",
    "audio/mpeg":"🎵","audio/mp3":"🎵","audio/wav":"🎵","audio/ogg":"🎵",
    "audio/flac":"🎵","audio/aac":"🎵","audio/x-m4a":"🎵","audio/mp4":"🎵",
}
VIDEO_TYPES = {
    "video/mp4":"🎬","video/quicktime":"🎬","video/x-msvideo":"🎬",
    "video/mpeg":"🎬","video/webm":"🎬","video/3gpp":"🎬",
}
ALL_ACCEPTED_EXTS = [
    "jpg","jpeg","png","webp","gif","heic","heif",
    "pdf","mp3","wav","ogg","flac","aac","m4a",
    "mp4","mov","avi","mpeg","webm","3gp",
    "obj","glb","gltf","fbx",
    # IMPROVE1: เพิ่มไฟล์ text/code/document
    "txt","csv","json","md","docx","xlsx",
    "py","js","ts","html","css","xml","yaml",
]
FILE_SIZE_LIMIT_MB = 50

def get_mime(file) -> str:
    mime = file.type or ""
    if not mime or mime == "application/octet-stream":
        ext = file.name.rsplit(".", 1)[-1].lower()
        guessed, _ = mimetypes.guess_type(f"x.{ext}")
        mime = guessed or "application/octet-stream"
    return mime

def upload_to_gemini_file_api(data: bytes, mime: str, display_name: str):
    try:
        r = requests.post(
            f"https://generativelanguage.googleapis.com/upload/v1beta/files?key={API_KEY}",
            headers={"X-Goog-Upload-Protocol":"multipart","Content-Type":"multipart/related; boundary=bound"},
            data=(b"--bound\r\nContent-Type: application/json; charset=utf-8\r\n\r\n"
                  + json.dumps({"file":{"display_name":display_name}}).encode()
                  + b"\r\n--bound\r\nContent-Type: "+mime.encode()+b"\r\n\r\n"+data+b"\r\n--bound--"),
            timeout=120
        )
        if r.status_code == 200:
            return r.json().get("file",{}).get("uri")
    except Exception:
        pass
    return None

def process_uploaded_file(uploaded) -> dict | None:
    """แปลง UploadedFile → attachment dict"""
    size_mb = uploaded.size / (1024*1024)
    if size_mb > FILE_SIZE_LIMIT_MB:
        st.error(f"❌ {uploaded.name} ใหญ่เกิน ({size_mb:.1f} MB)")
        return None
    mime = get_mime(uploaded)
    try: uploaded.seek(0)  # BUG9: reset pointer ป้องกัน empty read
    except: pass
    raw  = uploaded.read()
    if mime in INLINE_TYPES:
        if mime == "application/pdf":     cat, ico = "PDF","📄"
        elif mime.startswith("audio/"):   cat, ico = "เสียง","🎵"
        else:                              cat, ico = "รูปภาพ","🖼️"
        return {"name":uploaded.name,"mime":mime,"category":cat,"icon":ico,
                "data":base64.b64encode(raw).decode(),"uri":None,
                "size_str":f"{size_mb:.1f} MB"}
    elif mime in VIDEO_TYPES:
        with st.spinner(f"⬆️ กำลังอัปโหลด {uploaded.name}..."):
            uri = upload_to_gemini_file_api(raw, mime, uploaded.name)
        if uri:
            return {"name":uploaded.name,"mime":mime,"category":"วีดีโอ","icon":"🎬",
                    "data":None,"uri":uri,"size_str":f"{size_mb:.1f} MB"}
        st.error(f"❌ อัปโหลด {uploaded.name} ไม่สำเร็จ")
        return None
    # IMPROVE2: text / code / document files — อ่านเป็น text ส่งให้ Gemini
    text_exts = {"txt","csv","json","md","py","js","ts","html","css","xml","yaml","toml"}
    doc_exts  = {"docx","xlsx"}
    ext_lower = uploaded.name.rsplit(".",1)[-1].lower()
    if ext_lower in text_exts or mime.startswith("text/"):
        try:
            text_content = raw.decode("utf-8", errors="replace")[:12000]
        except:
            text_content = "[อ่านไม่ได้]"
        return {"name":uploaded.name,"mime":mime,"category":f"Code/Text","icon":"📃",
                "data":None,"uri":None,"text_content":text_content,"size_str":f"{size_mb:.1f} MB"}
    elif ext_lower == "docx":
        try:
            from docx import Document as _Doc
            doc_text = "\n".join([p.text for p in _Doc(BytesIO(raw)).paragraphs])[:12000]
        except:
            doc_text = "[อ่าน Word ไม่ได้]"
        return {"name":uploaded.name,"mime":mime,"category":"Word","icon":"📝",
                "data":None,"uri":None,"text_content":doc_text,"size_str":f"{size_mb:.1f} MB"}
    else:
        ext = uploaded.name.rsplit(".",1)[-1].upper()
        return {"name":uploaded.name,"mime":mime,"category":f"ไฟล์ ({ext})","icon":"🏗️",
                "data":None,"uri":None,"size_str":f"{size_mb:.1f} MB"}

# ══════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════
def get_agent_img_b64(agent_id: str):
    for ext in ["png","jpg","jpeg","webp"]:
        path = os.path.join(AGENTS_FOLDER, f"{agent_id}.{ext}")
        if os.path.exists(path):
            try:
                with open(path,"rb") as f: return base64.b64encode(f.read()).decode()
            except Exception: pass
    return None

def agent_avatar_html(agent_id: str, size: int = 40) -> str:
    b64  = get_agent_img_b64(agent_id)
    icon = AGENTS.get(agent_id,{}).get("icon","🤖")
    if b64:
        return f"<img class='agent-avatar' src='data:image/png;base64,{b64}' width='{size}' height='{size}' style='border-radius:50%;object-fit:cover;border:2px solid #1e293b;flex-shrink:0'/>"
    return f"<div class='agent-avatar-fallback' style='width:{size}px;height:{size}px;border-radius:50%;border:2px solid #1e293b;background:linear-gradient(135deg,#1e293b,#0f172a);display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0'>{icon}</div>"

@st.cache_data(ttl=300)
def get_best_model(api_key: str) -> str:
    try:
        r = requests.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}",timeout=8)
        if r.status_code == 200:
            avail = [m["name"] for m in r.json().get("models",[]) if "generateContent" in m.get("supportedGenerationMethods",[])]
            for p in ["models/gemini-2.5-flash-preview-05-20","models/gemini-2.5-flash",
                      "models/gemini-1.5-flash-latest","models/gemini-1.5-flash"]:
                if p in avail: return p
    except Exception: pass
    return "models/gemini-1.5-flash"


# ══════════════════════════════════════════════════════════════════
# URL READER — auto-detect และดึงเนื้อหาจาก URL ในข้อความ
# ══════════════════════════════════════════════════════════════════
URL_PATTERN = re.compile(r'https?://[^\s<>]{8,}', re.IGNORECASE)

def extract_urls(text: str) -> list:
    """ดึง URL ทั้งหมดออกจากข้อความ"""
    return URL_PATTERN.findall(text or "")

@st.cache_data(ttl=600, show_spinner=False)
def fetch_url_content(url: str) -> dict:
    """
    ดึงเนื้อหาจาก URL — cache 10 นาที
    Return: {"url", "title", "content", "type", "error"}
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "th,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/json,*/*",
        }
        res = requests.get(url, headers=headers, timeout=12, allow_redirects=True)
        res.raise_for_status()
        ct = res.headers.get("content-type", "")

        # ── JSON ──
        if "json" in ct:
            try:
                data = res.json()
                text = json.dumps(data, ensure_ascii=False, indent=2)[:8000]
                return {"url":url,"title":"JSON","content":text,"type":"json","error":None}
            except:
                pass

        # ── HTML / Text ──
        if "text" in ct or "html" in ct or not ct:
            html = res.text
            # ดึง title
            title_m = re.search(r'<title[^>]*>([^<]+)</title>', html, re.IGNORECASE)
            title = title_m.group(1).strip() if title_m else url

            # strip script/style
            html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL|re.IGNORECASE)
            html = re.sub(r'<style[^>]*>.*?</style>',  '', html, flags=re.DOTALL|re.IGNORECASE)
            html = re.sub(r'<nav[^>]*>.*?</nav>',      '', html, flags=re.DOTALL|re.IGNORECASE)
            html = re.sub(r'<footer[^>]*>.*?</footer>','', html, flags=re.DOTALL|re.IGNORECASE)
            html = re.sub(r'<header[^>]*>.*?</header>','', html, flags=re.DOTALL|re.IGNORECASE)
            # strip tags
            text = re.sub(r'<[^>]+>', ' ', html)
            text = re.sub(r'&nbsp;', ' ', text)
            text = re.sub(r'&amp;',  '&', text)
            text = re.sub(r'&lt;',   '<', text)
            text = re.sub(r'&gt;',   '>', text)
            text = re.sub(r'&quot;', '"', text)
            text = re.sub(r'\s+',   ' ', text).strip()
            return {"url":url,"title":title,"content":text[:10000],"type":"html","error":None}

        # ── ไฟล์อื่น ──
        return {"url":url,"title":url,"content":f"[ไฟล์ประเภท {ct} — ไม่สามารถอ่านเป็นข้อความได้]",
                "type":"binary","error":None}

    except requests.exceptions.Timeout:
        return {"url":url,"title":url,"content":"","type":"error","error":"⏳ Timeout (12s)"}
    except requests.exceptions.ConnectionError:
        return {"url":url,"title":url,"content":"","type":"error","error":"🔌 เชื่อมต่อไม่ได้"}
    except requests.exceptions.HTTPError as e:
        return {"url":url,"title":url,"content":"","type":"error","error":f"HTTP {e.response.status_code}"}
    except Exception as e:
        return {"url":url,"title":url,"content":"","type":"error","error":str(e)[:80]}


def export_chat_md() -> str:
    lines = [f"# AQUALINE AI LIVE CHAT — Export\n_วันที่: {datetime.now().strftime('%Y-%m-%d %H:%M')}_\n---\n"]
    for m in st.session_state.lc_messages:
        ts = m.get("time","")
        if m["role"] == "user":
            atts = m.get("attachments",[])
            att_str = "  ".join(f"[{a['icon']}{a['name']}]" for a in atts) if atts else ""
            lines.append(f"**👤 คุณ** `{ts}`  \n{att_str}  \n{m['content'] or '(แนบไฟล์)'}\n")
        elif m["role"] == "agent":
            lines.append(f"**{m.get('agent_name','Agent')}** `{ts}`  \n{m['content']}\n")
    return "\n".join(lines)

def export_chat_json() -> str:
    """Export chat history as JSON"""
    export_data = {
        "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_messages": len(st.session_state.lc_messages),
        "agents_used": list(set(m.get("agent_name","") for m in st.session_state.lc_messages if m.get("role")=="agent")),
        "messages": [
            {
                "role": m["role"],
                "agent_name": m.get("agent_name",""),
                "content": m.get("content",""),
                "time": m.get("time",""),
                "attachments": [{"name": a.get("name",""), "category": a.get("category","")}
                                for a in m.get("attachments",[])]
            }
            for m in st.session_state.lc_messages
        ]
    }
    return json.dumps(export_data, ensure_ascii=False, indent=2)

# ══════════════════════════════════════════════════════════════════
# CALL AGENT — Harvard MBA + multimodal + multi-attachment
# ══════════════════════════════════════════════════════════════════
def call_agent(agent_id: str, user_msg: str, history: list, model: str,
               attachments: list | None = None,
               url_contents: dict | None = None) -> str:  # URL READER: เพิ่ม param
    agent = AGENTS.get(agent_id,{})
    name  = agent.get("name", agent_id)
    role  = agent.get("role","")

    ctx = ""
    for h in history[-10:]:
        who = "ผู้ใช้" if h["role"]=="user" else h.get("agent_name","Agent")
        ctx += f"{who}: {h['content']}\n"

    recent_agent_msgs = [h for h in history[-6:] if h.get("role")=="agent"]
    greet_rule = ("ห้ามทักทายซ้ำ เพราะทีมทักทายไปแล้ว — เริ่มเนื้อหาได้เลย"
                  if recent_agent_msgs else "ทักทายสั้นๆ ได้ 1 ครั้ง")

    already_said = ""
    for h in (history[-len(recent_agent_msgs):] if recent_agent_msgs else []):
        if h.get("role")=="agent" and h.get("agent_name")!=name:
            already_said += f"- {h.get('agent_name','')}: {h.get('content','')[:120]}\n"
    no_repeat = f"\nAgent อื่นพูดไปแล้ว (ห้ามซ้ำ):\n{already_said}" if already_said else ""

    # สรุปไฟล์แนบ
    file_ctx = ""
    if attachments:
        descs = [f"{a.get('category','file')}: {a.get('name','')}" for a in attachments]
        file_ctx = f"\n[ผู้ใช้แนบไฟล์ {len(attachments)} ไฟล์: {', '.join(descs)}]"
        # IMPROVE3: แนบ text content ของ text/code/docx เข้า prompt
        for att in attachments:
            tc = att.get("text_content","")
            if tc:
                file_ctx += f"\n\n--- เนื้อหาของ {att.get('name','')} ---\n{tc}"
    # URL READER: เพิ่มเนื้อหาจาก URL ที่ดึงมา
    if url_contents:
        for u, data in url_contents.items():
            if data.get("error"):
                file_ctx += f"\n\n--- URL: {u} ---\n[ดึงข้อมูลไม่ได้: {data['error']}]"
            else:
                file_ctx += f"\n\n--- เนื้อหาจาก URL: {u} ---\nชื่อ: {data.get('title',u)}\n{data.get('content','')}\n"

    system_prompt = f"""คุณคือ {name} — สมาชิกของ AQUALINE AI TEAM

## ตัวตนและความเชี่ยวชาญ
คุณคืออาจารย์ MBA จาก Harvard Business School ที่มีความเชี่ยวชาญเฉพาะด้านในฐานะ {name} ({role})
นอกจากนี้คุณยังมีความรู้รอบด้านครอบคลุมทุกสาขาที่ทีมต้องการ:
กลยุทธ์ธุรกิจ, การตลาด, โฆษณา, Copywriting, Graphic Design, 3D Visualization,
Video Production, Facebook Ads, SEO, Customer Service, Data Analytics,
Creative Direction, Storyboarding, AI Prompt Engineering, Automation,
Booth Design, Market Research, Product Spec, Sales Script, Legal Advisory,
Content Writing, Pricing Strategy, LINE OA/CRM, TikTok & Reels, Marketing Psychology

## บุคลิกและวิธีคิด
- คุณคือ "คน" ที่มีความคิด ความรู้สึก และประสบการณ์จริง — ไม่ใช่ Bot ที่ตอบสูตร
- พูดเหมือนที่ปรึกษาระดับสูงกำลังนั่งคุยกับลูกค้าใน Line Group
- คิดลึก วิเคราะห์จริง ไม่ตอบกว้างๆ ผิวเผิน

## วิธีตอบคำถาม
**คำถามง่าย/ทั่วไป:** ตอบตรงๆ กระชับ เป็นธรรมชาติ ไม่ต้องใส่โครงสร้าง
**คำถามกลยุทธ์/ธุรกิจ/การตลาด:** ใช้โครงสร้างนี้

📌 **สรุปประเด็นสำคัญ**
🔍 **วิเคราะห์เชิงกลยุทธ์** (ข้อดี ข้อเสีย ความเสี่ยง โอกาส)
✅ **สิ่งที่ควรทำต่อ** (Action items เรียงลำดับ)
💡 **คำถามที่ควรคิดเพิ่ม (แบบ MBA)** (2-3 ข้อ)

## กฎเด็ดขาด
1. {greet_rule}
2. ตอบทุกคำถามเสมอ — ห้ามบอกว่านอกขอบเขต
3. ตอบให้ครบจบในคำตอบเดียว — ห้ามทิ้งประโยคค้างกลางคัน
4. ถ้าข้อมูลยังไม่พอ ให้ถามเพิ่มก่อนวิเคราะห์ลึก
5. เสริมมุมมองใหม่ที่ต่างจาก Agent อื่น{no_repeat}
6. ภาษาไทย เข้าใจง่าย แต่คิดลึกแบบที่ปรึกษาระดับสูง"""

    user_turn = f"""บริบทล่าสุด:
{ctx}
คำถาม: {user_msg}{file_ctx}

ตอบในฐานะ {name} ให้ครบจบ:"""

    url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={API_KEY}"
    parts: list = [{"text": system_prompt + "\n\n" + user_turn}]

    # แนบไฟล์ทุกไฟล์เข้า parts
    for att in (attachments or []):
        cat  = att.get("category","")
        mime = att.get("mime","")
        data = att.get("data")
        uri  = att.get("uri")
        if cat in ("รูปภาพ","PDF","เสียง") and data:
            parts.append({"inlineData":{"mimeType":mime,"data":data}})  # BUG2 fixed: camelCase
        elif cat == "วีดีโอ" and uri:
            parts.append({"fileData":{"mimeType":mime,"fileUri":uri}})  # BUG3 fixed: camelCase

    try:
        def _call_api(parts_in: list, extra_text: str = "") -> tuple[str, str]:
            """เรียก Gemini API หนึ่งรอบ — คืน (text, finishReason)"""
            p = list(parts_in)
            if extra_text:
                # BUG4 fixed: เปลี่ยน text part แรกเท่านั้น ไม่ลบ media parts
                p = [{"text": extra_text}] + [x for x in parts_in if "inlineData" in x or "fileData" in x]
            resp = requests.post(url, json={
                "contents": [{"parts": p}],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 8192,   # max ของ Gemini Flash
                    "topP": 0.9,
                }
            }, timeout=120)
            if resp.status_code != 200:
                return f"⚠️ API error {resp.status_code}: {resp.text[:120]}", "ERROR"
            cand   = resp.json()["candidates"][0]
            text   = cand["content"]["parts"][0].get("text", "").strip()
            reason = cand.get("finishReason", "STOP")
            return text, reason

        # รอบแรก
        text, reason = _call_api(parts)

        # ถ้าถูกตัดกลาง (MAX_TOKENS) → ต่อคำตอบอัตโนมัติ 1 รอบ
        if reason == "MAX_TOKENS" and text:
            continuation_prompt = (
                system_prompt + "\n\n" + user_turn +
                "\n\n[คำตอบของคุณถูกตัด กรุณาเขียนต่อจากประโยคที่ค้างไว้ โดยเริ่มต้นจุดที่หยุดพอดี]\n"
                f"ต่อจาก: ...{text[-200:]}"
            )
            extra, _ = _call_api(parts, extra_text=continuation_prompt)
            # ตัดส่วนซ้ำออก — หา overlap ระหว่าง tail กับ head ของ extra
            tail = text[-80:]
            if extra.startswith(tail):
                extra = extra[len(tail):]
            text = text + extra

        return text

    except Exception as e:
        return f"⚠️ {str(e)[:80]}"

# ══════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════
if "lc_messages"      not in st.session_state: st.session_state.lc_messages      = []
if "lc_active_agents" not in st.session_state: st.session_state.lc_active_agents = ["A1","A3","A11"]
if "lc_mode"          not in st.session_state: st.session_state.lc_mode          = "ทีมช่วยกันตอบ"
if "lc_max_agents"    not in st.session_state: st.session_state.lc_max_agents    = 3
if "lc_last_sent"     not in st.session_state: st.session_state.lc_last_sent     = ""
if "lc_input_key"     not in st.session_state: st.session_state.lc_input_key     = 0
if "lc_attachments"   not in st.session_state: st.session_state.lc_attachments   = []   # list ของไฟล์แนบ
if "lc_reactions"     not in st.session_state: st.session_state.lc_reactions     = {}   # msg_idx → list emoji
if "lc_search"        not in st.session_state: st.session_state.lc_search        = ""
if "lc_url_contents"  not in st.session_state: st.session_state.lc_url_contents  = {}   # URL READER: url→content cache

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
    st.page_link("ai_team.py",                  label="🤖 AI Special Team")
    st.page_link("pages/8_Workflow_Builder.py", label="🏭 Content Factory")
    st.page_link("pages/9_Live_Chat.py",        label="💬 Live Chat")
    st.markdown("---")

    # Export
    st.markdown("<div style='font-size:10px;color:#475569;font-family:IBM Plex Mono,monospace;letter-spacing:1px;padding:0 4px 6px'>📥 EXPORT แชท</div>", unsafe_allow_html=True)
    col_exp_md, col_exp_json = st.columns(2)
    with col_exp_md:
        md_data = export_chat_md()
        st.download_button(
            "📄 Markdown",
            data=md_data,
            file_name=f"aqualine_chat_{datetime.now().strftime('%Y%m%d_%H%M')}.md",
            mime="text/markdown",
            use_container_width=True,
            key="dl_md_btn",
            disabled=len(st.session_state.lc_messages) == 0
        )
    with col_exp_json:
        json_data = export_chat_json()
        st.download_button(
            "📊 JSON",
            data=json_data,
            file_name=f"aqualine_chat_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            use_container_width=True,
            key="dl_json_btn",
            disabled=len(st.session_state.lc_messages) == 0
        )
    col_clr_hist2 = st.container()
    with col_clr_hist2:
        if st.button("🗑️ ล้างแชท", use_container_width=True, key="clear_hist"):
            st.session_state.lc_messages    = []
            st.session_state.lc_last_sent   = ""
            st.session_state.lc_attachments = []
            st.session_state.lc_reactions   = {}
            st.session_state.lc_input_key  += 1
            st.rerun()

    st.markdown("---")
    st.markdown("<div style='font-size:10px;color:#475569;font-family:IBM Plex Mono,monospace;letter-spacing:1px;padding:0 4px 8px'>👥 เลือก Agent ที่จะร่วมแชท</div>", unsafe_allow_html=True)

    col_all, col_none = st.columns(2)
    with col_all:
        if st.button("เลือกทั้งหมด", use_container_width=True, key="sel_all"):
            st.session_state.lc_active_agents = list(AGENTS.keys())
            # sync checkbox state ด้วย
            for _aid in AGENTS.keys():
                st.session_state[f"chk_{_aid}"] = True
            st.rerun()
    with col_none:
        if st.button("ล้างทั้งหมด", use_container_width=True, key="clr_all"):
            st.session_state.lc_active_agents = []
            # แก้บัค: reset checkbox state ทุกตัวด้วย
            for _aid in AGENTS.keys():
                st.session_state[f"chk_{_aid}"] = False
            st.rerun()

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    for aid, info in AGENTS.items():
        selected = aid in st.session_state.lc_active_agents
        b64      = get_agent_img_b64(aid)
        img_html = (f"<img class='agent-card-img' src='data:image/png;base64,{b64}'/>"
                    if b64 else f"<div style='width:36px;height:36px;border-radius:50%;background:#0f172a;border:1px solid #1e293b;display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0'>{info['icon']}</div>")
        st.markdown(f"""<div class="agent-card {'selected' if selected else ''}" id="card_{aid}">
            {img_html}<div><div class="agent-card-name">{info['name']}</div>
            <div class="agent-card-role">{info['role']}</div></div></div>""", unsafe_allow_html=True)
        checked = st.checkbox("", value=selected, key=f"chk_{aid}", label_visibility="collapsed")
        if checked and aid not in st.session_state.lc_active_agents:
            st.session_state.lc_active_agents.append(aid)
        elif not checked and aid in st.session_state.lc_active_agents:
            st.session_state.lc_active_agents.remove(aid)

    st.markdown("---")
    st.markdown("<div style='font-size:10px;color:#475569;font-family:IBM Plex Mono,monospace;padding:0 4px 6px'>⚙️ การตั้งค่า</div>", unsafe_allow_html=True)
    st.session_state.lc_mode = st.selectbox("โหมดตอบ:", [
        "ทีมช่วยกันตอบ","ตอบทีละคน (Round Robin)","ตอบพร้อมกันทั้งทีม"], key="mode_select")
    st.session_state.lc_max_agents = st.slider("จำนวน Agent ที่ตอบต่อคำถาม:", 1, 8, 3, key="max_agents_slider")

# ══════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════
active   = st.session_state.lc_active_agents
n_active = len(active)

st.markdown(f"""
<div class="chat-header">
  <div style='font-size:32px'>💬</div>
  <div>
    <div class="chat-header-title">AQUALINE AI LIVE CHAT</div>
    <div class="chat-header-sub">
      <span class="online-dot"></span>
      {n_active} Agent ออนไลน์ · พิมพ์แล้วทีมจะร่วมตอบพร้อมกัน
    </div>
  </div>
  <div style='margin-left:auto;display:flex;gap:6px;flex-wrap:wrap'>
    {''.join(f"<div title='{AGENTS[a]['name']}' style='font-size:20px'>{AGENTS[a]['icon']}</div>" for a in active[:10])}
    {'<div style="font-size:12px;color:#475569;align-self:center">+'+str(n_active-10)+'</div>' if n_active>10 else ''}
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# SEARCH BAR
# ══════════════════════════════════════════════════════════════════
search_col, _ = st.columns([3,5])
with search_col:
    st.session_state.lc_search = st.text_input(
        "", placeholder="🔍 ค้นหาในแชท...",
        key="search_input", label_visibility="collapsed",
        value=st.session_state.lc_search
    )
search_q = st.session_state.lc_search.strip().lower()

# ══════════════════════════════════════════════════════════════════
# RENDER CHAT
# ══════════════════════════════════════════════════════════════════
chat_placeholder = st.empty()

REACTION_EMOJIS = ["👍","❤️","🔥","💯","😂","🤔"]

def build_chat_html(search_q: str = "") -> str:
    msgs = st.session_state.lc_messages
    reactions = st.session_state.lc_reactions

    # กรองตาม search
    if search_q:
        filtered = [(i,m) for i,m in enumerate(msgs)
                    if search_q in (m.get("content","") or "").lower()
                    or search_q in (m.get("agent_name","") or "").lower()]
    else:
        filtered = list(enumerate(msgs))

    if not filtered and not search_q:
        inner = """<div style='flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;'>
          <div style='font-size:48px;margin-bottom:12px'>💬</div>
          <div style='font-family:IBM Plex Mono,monospace;font-size:12px;color:#334155'>เริ่มพิมพ์คำถามด้านล่าง</div>
          <div style='font-size:11px;color:#1e293b;margin-top:6px'>ทีม AI จะร่วมกันตอบทันที</div></div>"""
    elif not filtered and search_q:
        inner = f"<div style='text-align:center;padding:40px;color:#334155;font-family:IBM Plex Mono,monospace;font-size:12px'>ไม่พบ \"{search_q}\" ในแชท</div>"
    else:
        inner = ""
        for orig_idx, m in filtered:
            ts  = m.get("time","")
            rxs = reactions.get(orig_idx, [])
            rx_html = ("".join(f"<span style='font-size:14px;margin-right:2px'>{e}</span>" for e in rxs)
                       if rxs else "")

            if m["role"] == "user":
                # URL READER: แสดง URL preview cards
                msg_urls     = m.get("urls", [])
                msg_url_data = m.get("url_contents", {})
                url_html = ""
                for u in msg_urls:
                    udata = msg_url_data.get(u, {})
                    err   = udata.get("error","")
                    title = udata.get("title", u)[:60]
                    body  = udata.get("content","")[:120].replace("\n"," ")
                    if err:
                        url_html += (
                            "<div style='background:rgba(239,68,68,.1);border:1px solid rgba(239,68,68,.3);"
                            "border-radius:6px;padding:6px 10px;margin:3px 0;font-size:11px;"
                            f"color:#f87171;font-family:IBM Plex Mono,monospace'>🔗 {u[:50]} — {err}</div>"
                        )
                    elif body:
                        url_html += (
                            f"<a href='{u}' target='_blank' style='text-decoration:none'>"
                            "<div style='background:rgba(56,189,248,.08);border:1px solid rgba(56,189,248,.25);"
                            "border-radius:8px;padding:8px 12px;margin:4px 0'>"
                            f"<div style='font-size:11px;color:#38bdf8;font-weight:700;"
                            f"font-family:IBM Plex Mono,monospace;margin-bottom:2px'>🔗 {title}</div>"
                            f"<div style='font-size:10px;color:#64748b;line-height:1.4'>{body}...</div>"
                            "</div></a>"
                        )
                # แสดงไฟล์แนบ (หลายไฟล์)
                atts = m.get("attachments", [])
                attach_html = ""
                for att in atts:
                    cat  = att.get("category","")
                    aname= att.get("name","")
                    ico  = att.get("icon","📎")
                    if cat == "รูปภาพ" and att.get("data"):
                        mime = att.get("mime","image/png")
                        attach_html += f"<img src='data:{mime};base64,{att['data']}' style='max-width:200px;max-height:140px;border-radius:8px;margin:3px 0;display:block;'/>"
                    else:
                        attach_html += f"<div style='background:rgba(56,189,248,.1);border:1px solid rgba(56,189,248,.3);border-radius:6px;padding:3px 8px;font-size:11px;color:#38bdf8;margin:2px 0;font-family:IBM Plex Mono,monospace'>{ico} {aname}</div>"
                inner += f"""<div class="msg-user">
                  <div style='max-width:75%'>
                    {url_html}
                    {attach_html}
                    {'<div class="bubble">'+m['content']+'</div>' if m['content'] else ('<div class="bubble" style="font-style:italic;opacity:.6">(แนบไฟล์)</div>' if not attach_html else '')}
                    <div class="msg-time" style='text-align:right'>{ts} {rx_html}</div>
                  </div>
                  <div style='width:36px;height:36px;border-radius:50%;background:linear-gradient(135deg,#1d4ed8,#3b82f6);display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0'>👤</div>
                </div>"""
            elif m["role"] == "system":
                inner += f"<div class='system-msg'>{m['content']}</div>"
            else:
                aid   = m.get("agent_id","A1")
                aname = m.get("agent_name","Agent")
                av    = agent_avatar_html(aid,40)
                # highlight search term
                content = m['content']
                if search_q and search_q in content.lower():
                    content = re.sub(f"({re.escape(search_q)})", r"<mark style='background:#fbbf24;color:#000;border-radius:2px'>\1</mark>", content, flags=re.IGNORECASE)
                inner += f"""<div class="msg-agent">
                  {av}
                  <div>
                    <div class="agent-name-label">{aname}</div>
                    <div class="bubble">{content}</div>
                    <div class="msg-time">{ts} {rx_html}</div>
                  </div>
                </div>"""

    html = f"""<!DOCTYPE html><html><head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=IBM+Plex+Sans+Thai:wght@300;400;600;700&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#070b12;font-family:'IBM Plex Sans Thai',sans-serif;}}
.chat-room{{background:#070b12;padding:16px;height:520px;overflow-y:auto;display:flex;flex-direction:column;gap:12px;scrollbar-width:thin;scrollbar-color:#1e293b transparent;}}
.chat-room::-webkit-scrollbar{{width:4px;}}
.chat-room::-webkit-scrollbar-thumb{{background:#1e293b;border-radius:2px;}}
.msg-user{{display:flex;justify-content:flex-end;gap:10px;align-items:flex-end;}}
.msg-user .bubble{{background:linear-gradient(135deg,#1d4ed8,#3b82f6);color:#fff;border-radius:18px 18px 4px 18px;padding:10px 16px;font-size:13px;line-height:1.7;max-width:100%;box-shadow:0 2px 12px rgba(59,130,246,.3);}}
.msg-agent{{display:flex;justify-content:flex-start;gap:10px;align-items:flex-start;}}
.msg-agent .bubble{{background:rgba(15,23,42,.9);border:1px solid #1e293b;color:#cbd5e1;border-radius:18px 18px 18px 4px;padding:10px 16px;font-size:13px;line-height:1.7;max-width:75%;white-space:pre-wrap;}}
.agent-avatar{{width:40px;height:40px;border-radius:50%;border:2px solid #1e293b;object-fit:cover;flex-shrink:0;}}
.agent-avatar-fallback{{width:40px;height:40px;border-radius:50%;border:2px solid #1e293b;background:linear-gradient(135deg,#1e293b,#0f172a);display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0;}}
.agent-name-label{{font-family:'IBM Plex Mono',monospace;font-size:10px;font-weight:700;color:#38bdf8;margin-bottom:3px;}}
.msg-time{{font-size:10px;color:#334155;font-family:'IBM Plex Mono',monospace;margin-top:3px;}}
.system-msg{{text-align:center;font-family:'IBM Plex Mono',monospace;font-size:10px;color:#334155;padding:4px 0;}}
</style></head><body>
<div class="chat-room" id="chatroom">{inner}</div>
<script>window.onload=function(){{var el=document.getElementById('chatroom');if(el)el.scrollTop=el.scrollHeight;}};</script>
</body></html>"""
    return html

def render_chat():
    html = build_chat_html(search_q)
    chat_placeholder.empty()
    with chat_placeholder.container():
        components.html(html, height=540, scrolling=False)

render_chat()

# ══════════════════════════════════════════════════════════════════
# REACTION BUTTONS (สำหรับข้อความล่าสุดของ agent)
# ══════════════════════════════════════════════════════════════════
msgs = st.session_state.lc_messages
agent_msgs = [(i,m) for i,m in enumerate(msgs) if m.get("role")=="agent"]
if agent_msgs:
    last_idx, last_m = agent_msgs[-1]
    st.markdown(f"<div style='font-size:10px;color:#334155;font-family:IBM Plex Mono,monospace;margin-bottom:2px'>React ให้ {last_m.get('agent_name','Agent')}:</div>", unsafe_allow_html=True)
    rcols = st.columns(len(REACTION_EMOJIS))
    for i, emoji in enumerate(REACTION_EMOJIS):
        with rcols[i]:
            if st.button(emoji, key=f"react_{last_idx}_{emoji}"):  # BUG7 fixed: ไม่ใช้ input_key
                rxs = st.session_state.lc_reactions.get(last_idx, [])
                rxs.append(emoji)
                st.session_state.lc_reactions[last_idx] = rxs
                render_chat()

# ══════════════════════════════════════════════════════════════════
# ATTACHMENT PREVIEW AREA (multi-file pills)
# ══════════════════════════════════════════════════════════════════
atts_pending = st.session_state.lc_attachments
if atts_pending:
    pills_html = ""
    for i, att in enumerate(atts_pending):
        cat  = att.get("category","")
        ico  = att.get("icon","📎")
        nm   = att.get("name","")
        sz   = att.get("size_str","")
        if cat == "รูปภาพ" and att.get("data"):
            mime = att.get("mime","image/png")
            thumb = f"<img src='data:{mime};base64,{att['data']}' style='width:28px;height:28px;border-radius:4px;object-fit:cover'/>"
        else:
            thumb = f"<span style='font-size:18px'>{ico}</span>"
        pills_html += f"<span class='attach-pill'>{thumb} <span class='attach-badge'>{cat}</span> {nm[:20]}{'…' if len(nm)>20 else ''} <span style='color:#475569'>{sz}</span></span>"
    st.markdown(f"<div style='padding:4px 0;display:flex;flex-wrap:wrap;gap:4px'>{pills_html}</div>", unsafe_allow_html=True)

    if st.button("✕ ลบไฟล์ทั้งหมด", key="rm_all_attach"):
        st.session_state.lc_attachments = []
        st.rerun()

# ══════════════════════════════════════════════════════════════════
# INPUT AREA
# ══════════════════════════════════════════════════════════════════
st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

# ── Voice Input CSS & JS (Isolated Iframe) ──

components.html("""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans+Thai:wght@300;400;600&display=swap" rel="stylesheet">
<style>
body { margin: 0; padding: 0; background-color: transparent; font-family: 'IBM Plex Sans Thai', sans-serif; overflow: hidden; }
.voice-btn { background: rgba(15,23,42,.9); border: 1px solid #1e293b; border-radius: 8px; padding: 8px 12px; font-family: 'IBM Plex Mono', monospace; font-size: 12px; color: #94a3b8; cursor: pointer; transition: all .2s; width: 100%; text-align: center; box-sizing: border-box; }
.voice-btn:hover { border-color: #38bdf8; color: #38bdf8; }
.voice-btn.recording { border-color: #f87171; color: #f87171; background: rgba(248,113,113,.1); }
.voice-transcript { background: rgba(56,189,248,.08); border: 1px solid rgba(56,189,248,.2); border-radius: 8px; padding: 8px 12px; font-size: 12px; color: #94a3b8; margin-top: 4px; box-sizing: border-box; word-wrap: break-word; }
</style>
</head>
<body>
<div id="voice_container">
  <button class="voice-btn" id="vbtn">🎙️ กด เพื่อพูด</button>
  <div class="voice-transcript" id="vout" style="display:none;"></div>
</div>

<script>
const btn = document.getElementById('vbtn');
const out = document.getElementById('vout');
let isRec = false;
let rec = null;

btn.addEventListener('click', function() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { out.style.display = 'block'; out.innerText = '⚠️ ไม่รองรับ (โปรดใช้ Chrome)'; return; }
    
    if (isRec) { if(rec) rec.stop(); return; }
    
    rec = new SR();
    rec.lang = 'th-TH';
    rec.interimResults = true;
    
    rec.onstart = function() {
        isRec = true;
        btn.innerText = '🔴 กำลังฟัง... (คลิกหยุด)';
        btn.classList.add('recording');
        out.style.display = 'block';
        out.innerText = '🎙️ กำลังฟัง...';
    };
    rec.onend = function() {
        isRec = false;
        btn.innerText = '🎙️ กด เพื่อพูด';
        btn.classList.remove('recording');
    };
    rec.onresult = function(e) {
        let t = '';
        for (let i = e.resultIndex; i < e.results.length; i++) {
            t += e.results[i][0].transcript;
        }
        out.innerText = '💬 ' + t;
        if (e.results[e.results.length - 1].isFinal) {
            navigator.clipboard.writeText(t).catch(function(){});
            out.innerHTML = '✅ <b>' + t + '</b><br><span style="font-size:10px;color:#38bdf8;">— คัดลอกแล้ว วางในช่องแชท (Ctrl+V)</span>';
        }
    };
    
    try { rec.start(); } catch (err) { out.style.display = 'block'; out.innerText = '⚠️ ขัดข้อง: เปิดไมค์ไม่ได้'; }
});
</script>
</body>
</html>
""", height=120)

col_attach_btn, col_input, col_voice, col_send = st.columns([1, 5, 1.2, 1])

with col_attach_btn:
    attach_click = st.button("📎", use_container_width=True, key="attach_btn",
                              help="แนบรูป วีดีโอ เสียง PDF ไฟล์ 3D — แนบได้หลายไฟล์")
with col_input:
    user_input = st.text_input(
        "", placeholder="พิมพ์คำถาม... หรือ @ชื่อAgent เพื่อ Mention | หรือกด 🎙️ พูด",
        key=f"chat_input_{st.session_state.lc_input_key}",
        label_visibility="collapsed"
    )
with col_voice:
    # Voice shortcut hint
    st.markdown(
        "<div style='font-size:9px;color:#334155;font-family:IBM Plex Mono,monospace;"
        "text-align:center;padding-top:10px;line-height:1.3'>🎙️ Voice<br>↑ ดูด้านบน</div>",
        unsafe_allow_html=True
    )
with col_send:
    send_btn = st.button("📨 ส่ง", use_container_width=True, type="primary", key="send_btn")

# ── File uploader (multi) ──
if attach_click:
    st.session_state["show_uploader"] = not st.session_state.get("show_uploader", False)

if st.session_state.get("show_uploader", False):
    uploaded_files = st.file_uploader(
        "เลือกไฟล์ที่ต้องการแนบ (เลือกได้หลายไฟล์พร้อมกัน)",
        type=ALL_ACCEPTED_EXTS,
        accept_multiple_files=True,          # ← หลายไฟล์
        key=f"uploader_{st.session_state.lc_input_key}",
        help=f"รูปภาพ, PDF, เสียง, วีดีโอ, ไฟล์ 3D — สูงสุด {FILE_SIZE_LIMIT_MB} MB ต่อไฟล์"
    )
    if uploaded_files:
        new_atts = []
        for uf in uploaded_files:
            # ข้ามไฟล์ที่มีชื่อซ้ำกับที่แนบไปแล้ว
            existing_names = [a["name"] for a in st.session_state.lc_attachments]
            if uf.name in existing_names:
                continue
            att = process_uploaded_file(uf)
            if att:
                new_atts.append(att)
        if new_atts:
            st.session_state.lc_attachments.extend(new_atts)
            st.success(f"✅ เพิ่มไฟล์ {len(new_atts)} ไฟล์ (รวม {len(st.session_state.lc_attachments)} ไฟล์)")
            st.session_state["show_uploader"] = False
            st.rerun()

# ── @Mention Agent dropdown ──
mention_aid = None
if "@" in user_input:
    mention_str = user_input.split("@")[-1].lower()
    matched = [(aid, info) for aid, info in AGENTS.items()
               if mention_str in info["name"].lower() and aid in active]
    if matched:
        st.markdown("<div style='font-size:10px;color:#38bdf8;font-family:IBM Plex Mono,monospace;margin-bottom:2px'>📍 Mention Agent:</div>", unsafe_allow_html=True)
        m_cols = st.columns(min(len(matched), 4))
        for ci, (aid, info) in enumerate(matched[:4]):
            with m_cols[ci]:
                if st.button(f"{info['icon']} {info['name']}", key=f"mention_{aid}_{st.session_state.lc_input_key}"):
                    mention_aid = aid

# ── Quick prompts ──
st.markdown("<div style='font-size:11px;color:#334155;margin-bottom:4px;font-family:IBM Plex Mono,monospace'>⚡ คำถามด่วน:</div>", unsafe_allow_html=True)
qcols = st.columns(4)
quick_questions = ["วิเคราะห์จุดขายหลักของสินค้าเรา","แนะนำ Hook สำหรับ TikTok","ควรยิงแอดช่วงเวลาไหน","ช่วยคิด Big Idea แคมเปญ"]
quick_triggered = ""
for i, qq in enumerate(quick_questions):
    with qcols[i]:
        if st.button(qq, use_container_width=True, key=f"qq_{i}"):
            quick_triggered = qq

# ══════════════════════════════════════════════════════════════════
# SEND MESSAGE
# ══════════════════════════════════════════════════════════════════
triggered_msg = ""
if quick_triggered:
    triggered_msg = quick_triggered
elif send_btn and (user_input.strip() or st.session_state.lc_attachments):
    triggered_msg = user_input.strip()
# BUG5 fixed: ลบ auto-trigger จาก text change — ต้องกดปุ่มส่งหรือ Enter เท่านั้น
# (text_input ไม่รองรับ Enter submit → ใช้ send_btn เท่านั้น)

has_attach = len(st.session_state.lc_attachments) > 0
can_send   = bool(triggered_msg) or (send_btn and has_attach and not triggered_msg)

if can_send:
    active_now = st.session_state.lc_active_agents
    if not active_now:
        st.warning("⚠️ กรุณาเลือก Agent อย่างน้อย 1 คนจาก Sidebar ก่อนครับ")
    else:
        attachments = list(st.session_state.lc_attachments)
        st.session_state.lc_last_sent   = triggered_msg
        st.session_state.lc_attachments = []   # clear

        # ── URL READER: auto-detect URL ในข้อความ ──────────────
        detected_urls = extract_urls(triggered_msg)
        url_contents  = {}
        if detected_urls:
            _url_status = st.empty()
            for u in detected_urls[:5]:  # จำกัด 5 URL ต่อข้อความ
                _url_status.markdown(
                    f"<div style='font-size:11px;color:#38bdf8;font-family:IBM Plex Mono,monospace'>"
                    f"🔗 กำลังอ่าน {u[:60]}{'...' if len(u)>60 else ''}...</div>",
                    unsafe_allow_html=True)
                data = fetch_url_content(u)
                url_contents[u] = data
                st.session_state.lc_url_contents[u] = data
            _url_status.empty()
        # ───────────────────────────────────────────────────────

        st.session_state.lc_messages.append({
            "role": "user",
            "content": triggered_msg,
            "attachments": attachments,
            "urls": detected_urls,          # URL READER: บันทึก URL ที่พบ
            "url_contents": url_contents,   # URL READER: เนื้อหาที่ดึงมา
            "time": datetime.now().strftime("%H:%M"),
        })
        render_chat()

        model = get_best_model(API_KEY)
        mode  = st.session_state.lc_mode
        max_a = st.session_state.lc_max_agents

        # ถ้า mention เฉพาะ Agent
        if mention_aid and mention_aid in active_now:
            responders = [mention_aid]
        elif mode == "ตอบพร้อมกันทั้งทีม":
            responders = active_now[:min(max_a, 25)]  # IMPROVE4: cap 25
        elif mode == "ตอบทีละคน (Round Robin)":
            turn = (len([m for m in st.session_state.lc_messages if m["role"]=="user"])-1) % len(active_now)
            responders = [active_now[turn]]
        else:
            n = min(max_a, len(active_now))
            responders = random.sample(active_now, n)

        status_placeholder = st.empty()
        for idx, aid in enumerate(responders):
            aname = AGENTS[aid]["name"]
            status_placeholder.markdown(
                f"<div style='font-size:11px;color:#38bdf8;font-family:IBM Plex Mono,monospace;padding:4px 0'>✍️ {aname} กำลังพิมพ์...</div>",
                unsafe_allow_html=True
            )
            answer = call_agent(aid, triggered_msg, st.session_state.lc_messages, model, attachments, url_contents)  # URL READER
            msg_idx = len(st.session_state.lc_messages)
            st.session_state.lc_messages.append({
                "role": "agent", "agent_id": aid, "agent_name": aname,
                "content": answer, "time": datetime.now().strftime("%H:%M"),
            })
            render_chat()
            if idx < len(responders)-1:
                time.sleep(0.2)

        status_placeholder.empty()
        st.session_state.lc_input_key += 1
        st.rerun()