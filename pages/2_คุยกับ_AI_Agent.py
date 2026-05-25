import streamlit as st
import requests, json, base64, os, re, datetime
import pdfplumber
from docx import Document

st.set_page_config(page_title="Chat Agent — AQUALINE", layout="wide")

CONVO_FILE = "conversations.json"

# ── Conversation Save/Load helpers ──
def load_conversations() -> dict:
    if os.path.exists(CONVO_FILE):
        try:
            with open(CONVO_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {}

def save_conversations(data: dict):
    try:
        with open(CONVO_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except: pass

def save_current_chat(aid: str, history: list, label: str = ""):
    convos = load_conversations()
    ts = datetime.datetime.now().strftime("%d/%m/%y %H:%M")
    key = f"{aid}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if not label:
        # auto-label from first user message
        first_msg = history[0].get("user_text","") if history else ""
        label = first_msg[:30] + ("…" if len(first_msg) > 30 else "") or ts
    convos[key] = {
        "agent": aid,
        "label": label,
        "ts": ts,
        "history": history
    }
    # เก็บแค่ 200 บทสนทนาล่าสุด กันไฟล์ใหญ่เกิน
    if len(convos) > 200:
        oldest_keys = sorted(convos.keys())[:len(convos) - 200]
        for k in oldest_keys:
            del convos[k]
    save_conversations(convos)

# ── Agent PNG helper ──
AGENT_IMG_DIR = "agents"  # โฟลเดอร์ที่เก็บ A1.png, A2.png, ...

@st.cache_data
def get_agent_img_b64(agent_id: str) -> str | None:
    """โหลด agents/A1.png → base64 string; คืน None ถ้าไม่พบไฟล์"""
    path = os.path.join(AGENT_IMG_DIR, f"{agent_id}.png")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

def agent_img_html(agent_id: str, size: int = 40, fallback_icon: str = "🤖") -> str:
    """คืน <img> tag ถ้ามีภาพ, คืน emoji span ถ้าไม่มี"""
    b64 = get_agent_img_b64(agent_id)
    if b64:
        return (f"<img src='data:image/png;base64,{b64}' "
                f"style='width:{size}px;height:{size}px;"
                f"object-fit:cover;border-radius:50%;vertical-align:middle'>")
    return f"<span style='font-size:{size}px;line-height:1'>{fallback_icon}</span>"

if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("🔑 ไม่พบ GOOGLE_API_KEY ใน secrets.toml")
    st.stop()

AGENTS = {
    "A1":  {"name":"นักกลยุทธ์การตลาด",   "icon":"👨‍💼","p":"วางแผนภาพรวมและจุดขาย",             "color":"#f59e0b"},
    "A2":  {"name":"ผู้จัดการโครงการ",      "icon":"📋",  "p":"คุมเป้าหมายและเวลา",               "color":"#8b5cf6"},
    "A3":  {"name":"นักเขียนคำโฆษณา",       "icon":"✍️",  "p":"สร้าง Content และ Caption โซเชียล", "color":"#ec4899"},
    "A4":  {"name":"กราฟิกดีไซเนอร์",       "icon":"🎨",  "p":"ออกแบบ Visual",                     "color":"#06b6d4"},
    "A5":  {"name":"3D Visualizer",          "icon":"🏗️",  "p":"เรนเดอร์ภาพสินค้าจริง",            "color":"#10b981"},
    "A6":  {"name":"ผู้เชี่ยวชาญวิดีโอ",     "icon":"🎬",  "p":"สคริปต์และมุมกล้อง",               "color":"#f97316"},
    "A7":  {"name":"นักยิงแอด Facebook",     "icon":"📈",  "p":"วางแผนสื่อโฆษณา",                  "color":"#3b82f6"},
    "A8":  {"name":"ผู้เชี่ยวชาญ SEO",       "icon":"🌐",  "p":"ปรับแต่งเนื้อหาให้ติดอันดับ",       "color":"#84cc16"},
    "A9":  {"name":"ฝ่ายบริการลูกค้า",       "icon":"💬",  "p":"วางแนวทางตอบคำถาม",                "color":"#14b8a6"},
    "A10": {"name":"นักวิเคราะห์ข้อมูล",     "icon":"📊",  "p":"วิเคราะห์สถิติความคุ้มค่า",         "color":"#a78bfa"},
    "A11": {"name":"ครีเอทีฟไดเรกเตอร์",     "icon":"💡",  "p":"คิดไอเดีย Big Idea",                "color":"#fbbf24"},
    "A12": {"name":"คนเขียนสตอรี่บอร์ด",     "icon":"🎞️",  "p":"วางลำดับภาพเล่าเรื่อง",            "color":"#f472b6"},
    "A13": {"name":"อาร์ตไดเรกเตอร์",        "icon":"✨",  "p":"ควบคุมคุณภาพงานดีไซน์",            "color":"#c084fc"},
    "A14": {"name":"ผู้เชี่ยวชาญ AI Prompt", "icon":"🤖",  "p":"ปรับจูนคำสั่งให้ AI",              "color":"#67e8f9"},
    "A15": {"name":"นักวางระบบอัตโนมัติ",    "icon":"⚙️",  "p":"เชื่อมระบบ Automation",            "color":"#6ee7b7"},
    "A16": {"name":"นักออกแบบบูธ",           "icon":"🎪",  "p":"วางผังงานนิทรรศการ",               "color":"#fda4af"},
    "A17": {"name":"นักวิจัยตลาด",           "icon":"🔍",  "p":"เจาะลึกข้อมูลคู่แข่ง Real-time",   "color":"#93c5fd"},
    "A18": {"name":"ฝ่ายตรวจสเปกสินค้า",     "icon":"✅",  "p":"ตรวจสอบความถูกต้องทางเทคนิค",      "color":"#4ade80"},
    "A19": {"name":"นักขายมือโปร",           "icon":"💰",  "p":"สร้างสคริปต์ปิดการขาย",            "color":"#fcd34d"},
    "A20": {"name":"ที่ปรึกษากฎหมาย",        "icon":"⚖️",  "p":"ตรวจสอบข้อบังคับและลิขสิทธิ์",     "color":"#d1d5db"},
    "A21": {"name":"นักเขียนบทความ",         "icon":"📝",  "p":"เขียนบทความยาว เนื้อหาเชิงลึก",    "color":"#e2e8f0"},
    "A22": {"name":"นักวางราคา/Pricing",      "icon":"🧮",  "p":"วิเคราะห์ราคา ตั้ง Promo Bundle",  "color":"#fb923c"},
    "A23": {"name":"ผู้เชี่ยวชาญ LINE OA",   "icon":"📱",  "p":"วางแผน LINE OA, CRM, Broadcast",   "color":"#4ade80"},
    "A24": {"name":"TikTok & Reels",          "icon":"🎵",  "p":"Hook, Trend, Script TikTok/Reels",  "color":"#f9a8d4"},
    "A25": {"name":"นักจิตวิทยาการตลาด",     "icon":"🧠",  "p":"Psychology ลูกค้า trigger การซื้อ", "color":"#c4b5fd"},
}

st.markdown("""
<style>
.stApp{background:linear-gradient(135deg,#0b0f19 0%,#1a1a2e 100%);color:#e2e8f0}
[data-testid="stSidebar"]{background:rgba(15,23,42,.9);border-right:1px solid #1e293b}
.chat-user{background:rgba(59,130,246,.15);border:1px solid #3b82f644;
  border-radius:12px 12px 4px 12px;padding:10px 14px;margin:6px 0;
  font-size:13px;color:#e2e8f0;max-width:82%;margin-left:auto}
.chat-ai{border-radius:12px 12px 12px 4px;padding:10px 14px;margin:6px 0;
  font-size:13px;color:#e2e8f0;max-width:86%;background:rgba(15,23,42,.8)}
.file-badge{display:inline-block;background:rgba(59,130,246,.15);
  border:1px solid #3b82f644;border-radius:6px;padding:3px 10px;
  font-size:11px;color:#93c5fd;margin:2px}
.mode-tab{display:inline-block;padding:6px 14px;border-radius:8px;font-size:12px;
  cursor:pointer;border:1px solid #334155;margin-right:6px;background:rgba(15,23,42,.6)}
.mode-tab.active{background:rgba(59,130,246,.2);border-color:#3b82f6;color:#93c5fd}
.gen-img-box{background:rgba(15,23,42,.8);border:1px solid #8b5cf6;
  border-radius:12px;padding:14px;margin-top:10px}
.url-result{background:rgba(15,23,42,.6);border:1px solid #334155;
  border-radius:8px;padding:10px;font-size:12px;color:#94a3b8;margin-top:6px}
</style>
""", unsafe_allow_html=True)

# ── Session state ──
if "chat_agent"       not in st.session_state: st.session_state.chat_agent       = "A1"
if "chat_history"     not in st.session_state: st.session_state.chat_history     = {}
if "chat_mode"        not in st.session_state: st.session_state.chat_mode        = "chat"
if "gen_result"       not in st.session_state: st.session_state.gen_result       = None
if "multi_agents"     not in st.session_state: st.session_state.multi_agents     = ["A1"]
if "multi_mode"       not in st.session_state: st.session_state.multi_mode       = False
if "multi_history"    not in st.session_state: st.session_state.multi_history    = []
if "saved_convos"     not in st.session_state: st.session_state.saved_convos     = load_conversations()

# ════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════
@st.cache_data(ttl=300)
def get_best_model(api_key):
    try:
        res = requests.get(
            f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}",
            timeout=8)
        if res.status_code == 200:
            avail = [m["name"] for m in res.json().get("models",[])
                     if "generateContent" in m.get("supportedGenerationMethods",[])]
            for p in ["models/gemini-2.5-flash-preview-05-20","models/gemini-2.5-flash",
                      "models/gemini-1.5-flash-latest","models/gemini-1.5-flash"]:
                if p in avail: return p
            return avail[0] if avail else "models/gemini-1.5-flash"
    except: pass
    return "models/gemini-1.5-flash"

@st.cache_data(ttl=300)
def get_imagen_model(api_key):
    try:
        res = requests.get(
            f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}",
            timeout=8)
        if res.status_code == 200:
            avail = [m["name"] for m in res.json().get("models",[])
                     if "generateContent" in m.get("supportedGenerationMethods",[])]
            for p in ["models/imagen-3.0-generate-002",
                      "models/imagen-3.0-generate-001",
                      "models/imagegeneration@006"]:
                if p in avail: return p
    except: pass
    return None

def fetch_url_content(url: str) -> str:
    """ดึงเนื้อหาจาก URL"""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=15)
        res.raise_for_status()
        ct = res.headers.get("content-type","")
        if "text" in ct or "html" in ct or "json" in ct or "xml" in ct:
            text = res.text
            # strip HTML tags แบบง่าย
            text = re.sub(r'<script[^>]*>.*?</script>','',text,flags=re.DOTALL)
            text = re.sub(r'<style[^>]*>.*?</style>','',text,flags=re.DOTALL)
            text = re.sub(r'<[^>]+>','',text)
            text = re.sub(r'\s+',' ',text).strip()
            return text[:10000]
        return f"[ไฟล์ binary ขนาด {len(res.content):,} bytes — ไม่สามารถอ่านเนื้อหาได้]"
    except Exception as e:
        return f"[ดึง URL ไม่ได้: {str(e)[:100]}]"

def process_file(file) -> dict:
    fname = file.name.lower()
    ftype = file.type or ""

    # รูปภาพ
    if ftype.startswith("image/") or fname.endswith((".jpg",".jpeg",".png",".gif",".webp",".bmp")):
        b64 = base64.b64encode(file.read()).decode()
        return {"type":"image","name":file.name,"content":b64,"mime":ftype or "image/jpeg"}

    # วิดีโอ — ส่งเป็น inline data (Gemini 1.5+ รองรับ)
    if ftype.startswith("video/") or fname.endswith((".mp4",".mov",".avi",".mkv",".webm")):
        data = file.read()
        if len(data) <= 20 * 1024 * 1024:  # ≤ 20MB
            b64 = base64.b64encode(data).decode()
            return {"type":"video","name":file.name,"content":b64,
                    "mime": ftype or "video/mp4","size": len(data)}
        return {"type":"video_toolarge","name":file.name,
                "content":f"[วิดีโอ {file.name} ขนาด {len(data)//1024//1024}MB ใหญ่เกิน 20MB]",
                "mime":"","size":len(data)}

    # เสียง
    if ftype.startswith("audio/") or fname.endswith((".mp3",".wav",".m4a",".ogg")):
        b64 = base64.b64encode(file.read()).decode()
        return {"type":"audio","name":file.name,"content":b64,"mime":ftype or "audio/mpeg"}

    # PDF
    if ftype == "application/pdf" or fname.endswith(".pdf"):
        try:
            with pdfplumber.open(file) as pdf:
                text = "\n".join([p.extract_text() or "" for p in pdf.pages])
            return {"type":"text_file","name":file.name,"content":text[:12000],"mime":"pdf"}
        except Exception as e:
            return {"type":"text_file","name":file.name,"content":f"[อ่าน PDF ไม่ได้: {e}]","mime":"pdf"}

    # Word
    if "wordprocessingml" in ftype or fname.endswith(".docx"):
        try:
            doc = Document(file)
            text = "\n".join([p.text for p in doc.paragraphs])
            return {"type":"text_file","name":file.name,"content":text[:12000],"mime":"docx"}
        except Exception as e:
            return {"type":"text_file","name":file.name,"content":f"[อ่าน Word ไม่ได้: {e}]","mime":"docx"}

    # Text / Code / Data
    if (ftype.startswith("text/") or
        fname.endswith((".txt",".csv",".json",".md",".py",".js",".ts",
                        ".html",".css",".xml",".yaml",".toml",".env"))):
        try:
            text = file.read().decode("utf-8", errors="replace")
            return {"type":"text_file","name":file.name,"content":text[:12000],"mime":ftype}
        except Exception as e:
            return {"type":"text_file","name":file.name,"content":f"[อ่านไม่ได้: {e}]","mime":ftype}

    # Excel / PowerPoint — อ่านเป็น text ไม่ได้ แจ้ง user
    if fname.endswith((".xlsx",".xls",".pptx",".ppt")):
        return {"type":"text_file","name":file.name,
                "content":f"[ไฟล์ {file.name} — แนบแล้ว Agent รับทราบชื่อไฟล์และประเภท แต่อ่านเนื้อหาไม่ได้โดยตรง กรุณาก๊อปข้อมูลมาวางแทน]",
                "mime":ftype}

    return {"type":"text_file","name":file.name,
            "content":f"[ไฟล์ {file.name} ประเภท {ftype}]","mime":ftype}

def build_parts(processed_files, url_contents, user_msg):
    parts = []
    extra_text = ""

    for f in processed_files:
        if f["type"] == "image":
            parts.append({"inlineData":{"mimeType":f["mime"],"data":f["content"]}})
        elif f["type"] == "video" :
            parts.append({"inlineData":{"mimeType":f["mime"],"data":f["content"]}})
        elif f["type"] == "audio":
            parts.append({"inlineData":{"mimeType":f["mime"],"data":f["content"]}})
        elif f["type"] == "video_toolarge":
            extra_text += f"\n{f['content']}"
        else:
            extra_text += f"\n\n--- ไฟล์: {f['name']} ---\n{f['content']}"

    for url, content in url_contents.items():
        extra_text += f"\n\n--- เนื้อหาจาก URL: {url} ---\n{content}"

    full_text = user_msg + (f"\n\n[ข้อมูลจากไฟล์/URL]{extra_text}" if extra_text else "")
    parts.append({"text": full_text})
    return parts

def call_agent_stream(agent_id, history, user_msg, processed_files=None, url_contents=None):
    info   = AGENTS[agent_id]
    model  = get_best_model(API_KEY)
    system = (f"คุณคือ {info['name']} ({info['p']}) ผู้เชี่ยวชาญของ AQUALINE STUDIO "
              f"ตอบในมุมมองของคุณ ตอบเป็นภาษาไทย กระชับและได้ใจความ "
              f"ถ้ามีไฟล์หรือ URL แนบให้วิเคราะห์และตอบตามเนื้อหานั้น")
    messages = []
    for h in history[-8:]:
        messages.append({"role":"user",  "parts":[{"text":h.get("user_text","")}]})
        messages.append({"role":"model", "parts":[{"text":h["ai"]}]})

    current_parts = build_parts(
        processed_files or [], url_contents or {}, user_msg)
    messages.append({"role":"user","parts":current_parts})

    url = (f"https://generativelanguage.googleapis.com/v1beta/"
           f"{model}:streamGenerateContent?alt=sse&key={API_KEY}")
    payload = {
        "system_instruction":{"parts":[{"text":system}]},
        "contents": messages,
        "generationConfig":{"temperature":0.8,"maxOutputTokens":8192},
    }
    try:
        with requests.post(url, json=payload, stream=True, timeout=180) as resp:
            if resp.status_code != 200:
                yield f"❌ Error {resp.status_code}: {resp.text[:200]}"
                return
            for line in resp.iter_lines():
                if line:
                    decoded = line.decode("utf-8")
                    if decoded.startswith("data: "):
                        try:
                            d = json.loads(decoded[6:])
                            chunk = d["candidates"][0]["content"]["parts"][0].get("text","")
                            if chunk: yield chunk
                        except: pass
    except Exception as e:
        yield f"❌ {str(e)[:100]}"

def call_multi_agents(agent_ids: list, history: list, user_msg: str, processed_files=None):
    """สร้าง Multi-Agent: ส่งคำถามเดียวกันไปถามหลาย Agent"""
    results = {}
    for aid in agent_ids:
        info   = AGENTS[aid]
        model  = get_best_model(API_KEY)
        system = (f"คุณคือ {info['name']} ({info['p']}) ผู้เชี่ยวชาญของ AQUALINE STUDIO "
                  f"ตอบในมุมมองของคุณ ตอบเป็นภาษาไทย กระชับและได้ใจความ")
        messages = []
        for h in history[-4:]:
            messages.append({"role":"user",  "parts":[{"text":h.get("user_text","")}]})
            messages.append({"role":"model", "parts":[{"text":h.get("ai","")}]})
        current_parts = build_parts(processed_files or [], {}, user_msg)
        messages.append({"role":"user","parts":current_parts})
        url = (f"https://generativelanguage.googleapis.com/v1beta/"
               f"{model}:generateContent?key={API_KEY}")
        payload = {
            "system_instruction":{"parts":[{"text":system}]},
            "contents": messages,
            "generationConfig":{"temperature":0.8,"maxOutputTokens":4096},
        }
        try:
            r = requests.post(url, json=payload, timeout=120)
            if r.status_code == 200:
                text = r.json()["candidates"][0]["content"]["parts"][0].get("text","")
                results[aid] = text
            else:
                results[aid] = f"Error {r.status_code}"
        except Exception as e:
            results[aid] = f"Error: {str(e)[:80]}"
    return results


def generate_image_gemini(prompt: str, api_key: str):
    """
    Gen ภาพด้วย Gemini Imagen API
    Return: (image_bytes, error_str)
    """
    # ลอง Imagen 3 ก่อน
    for model_id in ["imagen-3.0-generate-002",
                     "imagen-3.0-generate-001",
                     "imagegeneration@006"]:
        url = (f"https://generativelanguage.googleapis.com/v1beta/"
               f"models/{model_id}:predict?key={api_key}")
        payload = {
            "instances": [{"prompt": prompt}],
            "parameters": {"sampleCount": 1}
        }
        try:
            res = requests.post(url, json=payload, timeout=60)
            if res.status_code == 200:
                data = res.json()
                b64  = data["predictions"][0].get("bytesBase64Encoded","")
                if b64:
                    return base64.b64decode(b64), None
            elif res.status_code == 404:
                continue
            else:
                return None, f"Error {res.status_code}: {res.text[:200]}"
        except Exception as e:
            return None, str(e)[:100]

    # fallback: ใช้ Gemini Flash generate image
    chat_model = get_best_model(api_key)
    url2 = (f"https://generativelanguage.googleapis.com/v1beta/"
            f"{chat_model}:generateContent?key={api_key}")
    payload2 = {
        "contents":[{"parts":[{"text":
            f"Please describe in extreme visual detail what this image would look like, "
            f"then generate it as an SVG: {prompt}"}]}],
        "generationConfig":{"maxOutputTokens":4096}
    }
    try:
        r = requests.post(url2, json=payload2, timeout=60)
        if r.status_code == 200:
            text = r.json()["candidates"][0]["content"]["parts"][0].get("text","")
            return None, f"⚠️ Imagen ไม่พร้อมใช้งานกับ API key นี้\n\nGemini อธิบายภาพแทน:\n{text[:1000]}"
    except: pass
    return None, "❌ ไม่สามารถ gen ภาพได้ — Imagen API ต้องการ billing account"

# ═══════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════
with st.sidebar:
    # ── Multi-Agent Toggle ──
    st.markdown("### 🤖 โหมด Agent")
    mode_col1, mode_col2 = st.columns(2)
    with mode_col1:
        if st.button("👤 Single", use_container_width=True,
                     type="primary" if not st.session_state.multi_mode else "secondary"):
            st.session_state.multi_mode = False
            st.rerun()
    with mode_col2:
        if st.button("👥 Multi", use_container_width=True,
                     type="primary" if st.session_state.multi_mode else "secondary"):
            st.session_state.multi_mode = True
            st.rerun()

    st.markdown("---")

    if st.session_state.multi_mode:
        st.markdown("**👥 เลือก Agent หลายคน (Multi-Agent)**")
        st.caption("เลือกอย่างน้อย 2 Agent เพื่อตอบพร้อมกัน")
        selected_multi = []
        for aid_m, info_m in AGENTS.items():
            checked = aid_m in st.session_state.multi_agents
            if st.checkbox(f"{info_m['icon']} {info_m['name']}", value=checked, key=f"multi_{aid_m}"):
                selected_multi.append(aid_m)
        st.session_state.multi_agents = selected_multi if selected_multi else ["A1"]
        if len(st.session_state.multi_agents) > 0:
            st.success(f"✅ เลือก {len(st.session_state.multi_agents)} Agent")
        st.markdown("---")
        if st.button("🗑️ ล้าง Multi-Chat", use_container_width=True):
            st.session_state.multi_history = []
            st.rerun()
    else:
        st.markdown("**👤 เลือก Agent**")
        for aid, info in AGENTS.items():
            is_sel     = st.session_state.chat_agent == aid
            hist_count = len(st.session_state.chat_history.get(aid,[]))
            badge      = f" 💬{hist_count}" if hist_count > 0 else ""
            img_tag = agent_img_html(aid, size=28, fallback_icon=info['icon'])
            col1, col2 = st.sidebar.columns([1, 5])
            with col1:
                st.markdown(img_tag, unsafe_allow_html=True)
            with col2:
                if st.button(f"{info['name']}{badge}",
                             key=f"sel_{aid}", use_container_width=True,
                             type="primary" if is_sel else "secondary"):
                    st.session_state.chat_agent = aid
                    st.session_state.gen_result = None
                    st.rerun()
        st.markdown("---")
        # ── Save Conversation ──
        aid_cur = st.session_state.chat_agent
        cur_hist = st.session_state.chat_history.get(aid_cur, [])
        if cur_hist:
            st.markdown("**💾 บันทึกบทสนทนา**")
            save_label = st.text_input("ชื่อบทสนทนา (ไม่บังคับ)", placeholder="เช่น: แผน Campaign มิ.ย.", key="save_label")
            if st.button("💾 Save บทสนทนานี้", use_container_width=True):
                save_current_chat(aid_cur, cur_hist, save_label)
                st.session_state.saved_convos = load_conversations()
                st.success("✅ บันทึกแล้ว!")
        st.markdown("---")
        # ── Load Saved Conversations ──
        saved = load_conversations()
        agent_saved = {k:v for k,v in saved.items() if v.get("agent")==st.session_state.chat_agent}
        if agent_saved:
            st.markdown("**📂 โหลดบทสนทนาเก่า**")
            for k, v in list(agent_saved.items())[-5:]:
                col_a, col_b = st.columns([4,1])
                with col_a:
                    btn_label = f"📄 {v['label'][:22]} 🕐{v['ts']}"
                    if st.button(btn_label, key=f"load_{k}", use_container_width=True):
                        st.session_state.chat_history[st.session_state.chat_agent] = v["history"]
                        st.rerun()
                with col_b:
                    if st.button("🗑️", key=f"del_{k}"):
                        saved.pop(k)
                        save_conversations(saved)
                        st.rerun()
        st.markdown("---")
        if st.button("🗑️ ล้างประวัติ Chat ทั้งหมด", use_container_width=True):
            st.session_state.chat_history = {}
            st.rerun()

# ═══════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════

# ════════════════════════════════════════════
# MULTI-AGENT MODE
# ════════════════════════════════════════════
if st.session_state.multi_mode:
    selected_ids = st.session_state.multi_agents
    agent_names  = " + ".join([AGENTS[a]['icon']+" "+AGENTS[a]['name'] for a in selected_ids[:3]])
    if len(selected_ids) > 3:
        agent_names += f" + {len(selected_ids)-3} คน"
    header_html = (
        "<div style='background:linear-gradient(90deg,rgba(139,92,246,.2),rgba(236,72,153,.1));"
        "border:1px solid #8b5cf644;border-radius:12px;padding:14px 20px;margin-bottom:12px'>"
        "<div style='font-size:18px;font-weight:700;color:#a78bfa'>\U0001f465 Multi-Agent Mode</div>"
        f"<div style='font-size:12px;color:#94a3b8;margin-top:4px'>{agent_names}</div></div>"
    )
    st.markdown(header_html, unsafe_allow_html=True)

    multi_hist = st.session_state.multi_history
    for msg in multi_hist:
        st.markdown(f"<div class='chat-user'>\U0001f464 {msg['user']}</div>", unsafe_allow_html=True)
        for aid_r, response in msg.get('responses', {}).items():
            ag_info  = AGENTS.get(aid_r, {})
            ag_color = ag_info.get('color','#8b5cf6')
            ag_icon  = ag_info.get('icon','\U0001f916')
            ag_name  = ag_info.get('name', aid_r)
            box_html = (
                f"<div class='chat-ai' style='border:1px solid {ag_color}33;margin-bottom:6px'>"
                f"<b style='color:{ag_color}'>{ag_icon} {ag_name}</b>"
                f"<br>{response}</div>"
            )
            st.markdown(box_html, unsafe_allow_html=True)

    # ── Multi mode sub-tabs ──
    st.markdown("---")
    m_cols = st.columns(3)
    with m_cols[0]:
        if st.button("💬 Chat + ไฟล์", key="m_tab_chat", use_container_width=True,
                     type="primary" if st.session_state.chat_mode == "chat" else "secondary"):
            st.session_state.chat_mode = "chat"; st.rerun()
    with m_cols[1]:
        if st.button("🔗 วิเคราะห์ URL", key="m_tab_url", use_container_width=True,
                     type="primary" if st.session_state.chat_mode == "url" else "secondary"):
            st.session_state.chat_mode = "url"; st.rerun()
    with m_cols[2]:
        if st.button("🎨 Gen ภาพ AI", key="m_tab_gen", use_container_width=True,
                     type="primary" if st.session_state.chat_mode == "gen" else "secondary"):
            st.session_state.chat_mode = "gen"; st.rerun()
    st.markdown("---")

    # ── Multi Chat input (เฉพาะ mode chat) ──
    if st.session_state.chat_mode == "chat":
        multi_input = st.chat_input("💬 พิมพ์คำถามส่งถึงทุก Agent...")
        if multi_input:
            with st.spinner(f"กำลังถามทุก Agent ({len(selected_ids)} คน)..."):
                responses = call_multi_agents(selected_ids, multi_hist, multi_input)
            st.session_state.multi_history.append({"user": multi_input, "responses": responses})
            if len(st.session_state.multi_history) % 5 == 0:
                save_current_chat("MULTI", st.session_state.multi_history,
                                  "Multi-Agent: " + multi_input[:25])
            st.rerun()

    # ── URL วิเคราะห์ (Multi mode) ──
    elif st.session_state.chat_mode == "url":
        first_aid = selected_ids[0]
        first_info = AGENTS[first_aid]
        first_color = first_info["color"]
        st.markdown(f"**🔗 ให้ {agent_img_html(first_aid, size=20, fallback_icon=first_info['icon'])} {first_info['name']} + ทีม วิเคราะห์ URL:**", unsafe_allow_html=True)
        urls_input_m = st.text_area("ใส่ URL (บรรทัดละ 1 ลิ้ง):",
            placeholder="https://example.com", height=80, key="m_urls_input")
        url_question_m = st.text_area("คำถามหรือสิ่งที่อยากให้วิเคราะห์:",
            placeholder="เช่น: วิเคราะห์จุดขายของเว็บนี้", height=60, key="m_url_question")
        if st.button("🔗 วิเคราะห์ URL", use_container_width=True, key="m_url_btn"):
            urls_m = [u.strip() for u in urls_input_m.strip().split("\n") if u.strip()]
            if not urls_m:
                st.error("กรุณาใส่ URL ก่อนครับ")
            elif not url_question_m.strip():
                st.error("กรุณาบอกว่าต้องการให้วิเคราะห์อะไรครับ")
            else:
                url_contents_m = {}
                prog = st.progress(0)
                for i, u in enumerate(urls_m[:5]):
                    with st.spinner(f"กำลังดึง {u[:50]}..."):
                        url_contents_m[u] = fetch_url_content(u)
                    prog.progress((i+1)/len(urls_m[:5]))
                prog.empty()
                combined = "\n\n".join([f"URL: {u}\n{c}" for u, c in url_contents_m.items()])
                full_q = f"{url_question_m}\n\n[เนื้อหาจาก URL]\n{combined[:8000]}"
                with st.spinner(f"กำลังถามทุก Agent ({len(selected_ids)} คน)..."):
                    responses = call_multi_agents(selected_ids, multi_hist, full_q)
                st.session_state.multi_history.append({"user": f"[URL] {url_question_m}", "responses": responses})
                st.rerun()

    # ── Gen ภาพ (Multi mode — ใช้ agent แรกเป็น prompt enhancer) ──
    elif st.session_state.chat_mode == "gen":
        first_aid = selected_ids[0]
        first_info = AGENTS[first_aid]
        st.markdown(f"""
        <div class='gen-img-box'>
        <div style='font-size:15px;font-weight:700;color:#a78bfa;margin-bottom:8px'>
        🎨 Gen ภาพ AI — ทีม {len(selected_ids)} Agent ช่วยกันปรับ prompt
        </div></div>""", unsafe_allow_html=True)
        gen_input_m = st.text_area("📝 อธิบายภาพที่ต้องการ:",
            placeholder="เช่น: ภาพโฆษณารางน้ำฝน Aqualine สีเงิน พื้นหลังโมเดิร์น",
            height=100, key="m_gen_input")
        img_style_m = st.selectbox("🖼️ สไตล์ภาพ:", [
            "Photorealistic","Professional Product Photo",
            "3D Render","Illustration","Minimalist","Cinematic","Social Media Ad"
        ], key="m_img_style")
        enhance_m = st.checkbox("✨ ให้ Agent ช่วยปรับ prompt ก่อน gen", value=True, key="m_enhance")
        if st.button("🎨 Gen ภาพเลย!", use_container_width=True, key="m_gen_btn"):
            if not gen_input_m.strip():
                st.error("กรุณาอธิบายภาพที่ต้องการก่อนครับ")
            else:
                final_prompt_m = gen_input_m
                if enhance_m:
                    with st.spinner(f"{first_info['icon']} {first_info['name']} กำลังปรับปรุง prompt..."):
                        ep = (f"คุณคือ {first_info['name']} ปรับ prompt นี้สำหรับ AI image generation "
                              f"สไตล์ {img_style_m} ตอบเป็น prompt ภาษาอังกฤษเท่านั้น:\n{gen_input_m}")
                        model_e = get_best_model(API_KEY)
                        re_ = requests.post(
                            f"https://generativelanguage.googleapis.com/v1beta/{model_e}:generateContent?key={API_KEY}",
                            json={"contents":[{"parts":[{"text":ep}]}],"generationConfig":{"maxOutputTokens":500}},
                            timeout=30)
                        if re_.status_code == 200:
                            final_prompt_m = re_.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                            st.info(f"✨ Prompt ที่ปรับแล้ว:\n`{final_prompt_m}`")
                with st.spinner("🎨 กำลัง gen ภาพ..."):
                    img_bytes_m, err_m = generate_image_gemini(final_prompt_m, API_KEY)
                if img_bytes_m:
                    st.success("✅ Gen ภาพสำเร็จ!")
                    st.image(img_bytes_m, use_container_width=True)
                    st.download_button("⬇️ ดาวน์โหลดภาพ", data=img_bytes_m,
                        file_name="aqualine_multi_gen.png", mime="image/png", use_container_width=True)
                else:
                    st.warning(err_m or "ไม่สามารถ gen ภาพได้")

    st.stop()

aid   = st.session_state.chat_agent
info  = AGENTS[aid]
color = info["color"]

st.markdown(f"""
<div style='background:linear-gradient(90deg,rgba(15,23,42,.9),rgba(30,41,59,.5));
  border:1px solid {color}44;border-radius:12px;padding:14px 20px;
  margin-bottom:12px;display:flex;align-items:center;gap:14px'>
  {agent_img_html(aid, size=56, fallback_icon=info['icon'])}
  <div>
    <div style='font-size:20px;font-weight:700;color:{color}'>{info['name']}</div>
    <div style='font-size:12px;color:#64748b'>{info['p']}</div>
  </div>
  <div style='margin-left:auto;font-size:11px;color:#475569;
    background:rgba(0,0,0,.3);padding:4px 10px;border-radius:20px'>
    {aid}.SYS · SECURE LINK ✅
  </div>
</div>
""", unsafe_allow_html=True)

# ── Mode tabs ──
mode_cols = st.columns(3)
with mode_cols[0]:
    if st.button("💬 Chat + ไฟล์", use_container_width=True,
                 type="primary" if st.session_state.chat_mode=="chat" else "secondary"):
        st.session_state.chat_mode = "chat"; st.rerun()
with mode_cols[1]:
    if st.button("🔗 วิเคราะห์ URL", use_container_width=True,
                 type="primary" if st.session_state.chat_mode=="url" else "secondary"):
        st.session_state.chat_mode = "url"; st.rerun()
with mode_cols[2]:
    if st.button("🎨 Gen ภาพ AI", use_container_width=True,
                 type="primary" if st.session_state.chat_mode=="gen" else "secondary"):
        st.session_state.chat_mode = "gen"; st.rerun()

st.markdown("---")

# ════════════════════════════════════════════
# MODE: GEN ภาพ
# ════════════════════════════════════════════
if st.session_state.chat_mode == "gen":
    st.markdown(f"""
    <div class='gen-img-box'>
    <div style='font-size:15px;font-weight:700;color:#a78bfa;margin-bottom:8px'>
    🎨 Gen ภาพ AI — โดย {agent_img_html(aid, size=24, fallback_icon=info['icon'])} {info['name']}
    </div>
    <div style='font-size:12px;color:#64748b'>
    Agent จะช่วยปรับ prompt ให้เหมาะกับงานของคุณ แล้วส่งให้ Imagen gen ภาพ
    </div>
    </div>
    """, unsafe_allow_html=True)

    gen_input = st.text_area(
        "📝 อธิบายภาพที่ต้องการ (ภาษาไทยหรืออังกฤษ):",
        placeholder="เช่น: ภาพโฆษณารางน้ำฝน Aqualine สีเงิน พื้นหลังโมเดิร์น มีแสงสวยงาม\nหรือ: Product photo of premium rain gutter, silver color, clean background",
        height=100, key="gen_input"
    )
    enhance = st.checkbox("✨ ให้ Agent ช่วยปรับปรุง prompt ให้ดีขึ้นก่อน gen", value=True)
    img_style = st.selectbox("🖼️ สไตล์ภาพ:", [
        "Photorealistic", "Professional Product Photo",
        "3D Render", "Illustration", "Minimalist",
        "Cinematic", "Social Media Ad"
    ])

    if st.button("🎨 Gen ภาพเลย!", use_container_width=True):
        if not gen_input.strip():
            st.error("กรุณาอธิบายภาพที่ต้องการก่อนครับ")
        else:
            final_prompt = gen_input
            if enhance:
                with st.spinner(f"{info['icon']} {info['name']} กำลังปรับปรุง prompt..."):
                    enhance_prompt = (
                        f"คุณคือ {info['name']} ({info['p']})\n"
                        f"ปรับปรุง prompt นี้ให้เหมาะสำหรับ AI image generation "
                        f"สไตล์ {img_style} ให้ละเอียดและได้ภาพสวยที่สุด\n"
                        f"ตอบเป็น prompt ภาษาอังกฤษเท่านั้น ไม่ต้องอธิบาย:\n{gen_input}"
                    )
                    model = get_best_model(API_KEY)
                    url_e = (f"https://generativelanguage.googleapis.com/v1beta/"
                             f"{model}:generateContent?key={API_KEY}")
                    r = requests.post(url_e, json={
                        "contents":[{"parts":[{"text":enhance_prompt}]}],
                        "generationConfig":{"maxOutputTokens":500}
                    }, timeout=30)
                    if r.status_code == 200:
                        final_prompt = r.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                        st.info(f"✨ Prompt ที่ปรับแล้ว:\n`{final_prompt}`")

            with st.spinner("🎨 กำลัง gen ภาพ..."):
                img_bytes, err = generate_image_gemini(final_prompt, API_KEY)

            if img_bytes:
                st.success("✅ Gen ภาพสำเร็จ!")
                st.image(img_bytes, caption=gen_input, use_container_width=True)
                st.download_button(
                    "⬇️ ดาวน์โหลดภาพ", data=img_bytes,
                    file_name="aqualine_gen.png", mime="image/png",
                    use_container_width=True)
                st.session_state.gen_result = img_bytes
            else:
                st.warning(err or "ไม่สามารถ gen ภาพได้")
                st.markdown("""
                <div style='background:rgba(245,158,11,.1);border:1px solid #f59e0b44;
                border-radius:8px;padding:12px;font-size:12px;color:#fcd34d;margin-top:8px'>
                💡 <b>หมายเหตุ:</b> Imagen API ต้องการ Google Cloud billing account<br>
                ทางเลือก: ใช้ prompt ที่ได้ไปใส่ใน Midjourney, DALL-E, หรือ Stable Diffusion แทนครับ
                </div>
                """, unsafe_allow_html=True)

# ════════════════════════════════════════════
# MODE: URL
# ════════════════════════════════════════════
elif st.session_state.chat_mode == "url":
    st.markdown(f"**🔗 ให้ {agent_img_html(aid, size=20, fallback_icon=info['icon'])} {info['name']} วิเคราะห์ URL:**", unsafe_allow_html=True)

    urls_input = st.text_area(
        "ใส่ URL (หลายลิ้งได้ บรรทัดละ 1 ลิ้ง):",
        placeholder="https://example.com\nhttps://facebook.com/...\nhttps://shopee.co.th/...",
        height=80, key="urls_input"
    )
    url_question = st.text_area(
        "คำถามหรือสิ่งที่อยากให้วิเคราะห์:",
        placeholder="เช่น: วิเคราะห์จุดขายของเว็บนี้, สรุปเนื้อหา, เปรียบเทียบกับคู่แข่ง",
        height=60, key="url_question"
    )

    if st.button("🔗 วิเคราะห์ URL", use_container_width=True):
        urls = [u.strip() for u in urls_input.strip().split("\n") if u.strip()]
        if not urls:
            st.error("กรุณาใส่ URL ก่อนครับ")
        elif not url_question.strip():
            st.error("กรุณาบอกว่าต้องการให้วิเคราะห์อะไรครับ")
        else:
            url_contents = {}
            progress = st.progress(0)
            for i, u in enumerate(urls[:5]):  # จำกัด 5 URL
                with st.spinner(f"กำลังดึง {u[:50]}..."):
                    url_contents[u] = fetch_url_content(u)
                progress.progress((i+1)/len(urls[:5]))
            progress.empty()

            # แสดงผลที่ดึงได้
            with st.expander(f"📄 เนื้อหาที่ดึงได้ ({len(url_contents)} URL)", expanded=False):
                for u, c in url_contents.items():
                    st.markdown(f"**{u}**")
                    st.text(c[:500] + "..." if len(c) > 500 else c)
                    st.markdown("---")

            placeholder = st.empty()
            full_response = ""
            history = st.session_state.chat_history.get(aid, [])
            for chunk in call_agent_stream(aid, history, url_question,
                                           url_contents=url_contents):
                full_response += chunk
                placeholder.markdown(
                    f"<div class='chat-ai' style='border:1px solid {color}33'>"
                    f"<b style='color:{color}'>{agent_img_html(aid, size=22, fallback_icon=info['icon'])} {info['name']}</b>"
                    f"<br>{full_response}▌</div>",
                    unsafe_allow_html=True)
            placeholder.empty()

            if aid not in st.session_state.chat_history:
                st.session_state.chat_history[aid] = []
            st.session_state.chat_history[aid].append({
                "user_text": f"[URL Analysis] {url_question}\nURLs: {', '.join(urls)}",
                "files": [f"🔗 {u}" for u in urls],
                "file_previews": [],
                "ai": full_response
            })
            st.rerun()

# ════════════════════════════════════════════
# MODE: CHAT + FILES
# ════════════════════════════════════════════
else:
    history = st.session_state.chat_history.get(aid, [])
    if not history:
        st.markdown(f"""
<div style='text-align:center;padding:30px;color:#334155'>
  <div style='margin-bottom:10px'>{agent_img_html(aid, size=80, fallback_icon=info['icon'])}</div>
  <div style='font-size:14px;color:#64748b'>
  ช่องส่วนตัว 1-on-1 กับ {info['name']}<br>
  รองรับ: 🖼️ รูปภาพ · 🎬 วิดีโอ · 🔊 เสียง · 📄 PDF · 📝 Word · 📊 CSV · 💻 Code
  </div>
</div>
""", unsafe_allow_html=True)

    for msg in history:
        if msg.get("files"):
            badges = "".join([f"<span class='file-badge'>📎 {f}</span>"
                              for f in msg["files"]])
            st.markdown(f"<div style='text-align:right;margin-bottom:2px'>{badges}</div>",
                        unsafe_allow_html=True)
        for fp in msg.get("file_previews",[]):
            if fp["type"] == "image":
                st.image(base64.b64decode(fp["content"]), width=180)
        st.markdown(f"<div class='chat-user'>👤 {msg.get('user_text','')}</div>",
                    unsafe_allow_html=True)
        st.markdown(
            f"<div class='chat-ai' style='border:1px solid {color}33'>"
            f"<b style='color:{color}'>{agent_img_html(aid, size=22, fallback_icon=info['icon'])} {info['name']}</b>"
            f"<br>{msg['ai']}</div>", unsafe_allow_html=True)

    # ── Upload ──
    st.markdown("""<div style='font-size:11px;color:#475569;margin-bottom:4px'>
    📎 รองรับ: รูปภาพ · วิดีโอ (≤20MB) · เสียง · PDF · Word · CSV · TXT · JSON · Code
    </div>""", unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "แนบไฟล์",
        type=["jpg","jpeg","png","gif","webp","bmp",
              "mp4","mov","avi","mkv","webm",
              "mp3","wav","m4a","ogg",
              "pdf","docx",
              "txt","csv","json","md",
              "py","js","ts","html","css","xml","yaml","toml",
              "xlsx","pptx"],
        accept_multiple_files=True,
        key=f"upload_{aid}",
        label_visibility="collapsed"
    )

    if uploaded:
        prev_cols = st.columns(min(len(uploaded), 5))
        for i, f in enumerate(uploaded):
            with prev_cols[i % 5]:
                if f.type.startswith("image/"):
                    st.image(f, caption=f.name, use_container_width=True)
                else:
                    ext = f.name.split(".")[-1].lower()
                    icon_map = {
                        "pdf":"📄","docx":"📝","txt":"📃","csv":"📊","json":"🔧",
                        "py":"🐍","js":"⚡","html":"🌐","mp4":"🎬","mov":"🎬",
                        "mp3":"🎵","wav":"🎵","xlsx":"📊","pptx":"📊","md":"📝"
                    }
                    ficon = icon_map.get(ext, "📎")
                    size_kb = round(f.size/1024, 1)
                    st.markdown(f"""
<div style='background:rgba(15,23,42,.8);border:1px solid #334155;
border-radius:8px;padding:8px;text-align:center;font-size:11px'>
  <div style='font-size:22px'>{ficon}</div>
  <div style='color:#94a3b8;word-break:break-all;margin-top:2px'>{f.name}</div>
  <div style='color:#475569'>{size_kb} KB</div>
</div>""", unsafe_allow_html=True)

    user_input = st.chat_input(f"💬 พิมพ์ข้อความถึง {info['name']}...")

    if user_input:
        processed, file_names, file_previews = [], [], []
        if uploaded:
            for f in uploaded:
                pf = process_file(f)
                processed.append(pf)
                file_names.append(f.name)
                if pf["type"] == "image":
                    file_previews.append({"type":"image","content":pf["content"]})

        placeholder   = st.empty()
        full_response = ""
        for chunk in call_agent_stream(aid, history, user_input,
                                       processed if processed else None):
            full_response += chunk
            placeholder.markdown(
                f"<div class='chat-ai' style='border:1px solid {color}33'>"
                f"<b style='color:{color}'>{agent_img_html(aid, size=22, fallback_icon=info['icon'])} {info['name']}</b>"
                f"<br>{full_response}▌</div>", unsafe_allow_html=True)
        placeholder.empty()

        if aid not in st.session_state.chat_history:
            st.session_state.chat_history[aid] = []
        st.session_state.chat_history[aid].append({
            "user_text":     user_input,
            "files":         file_names,
            "file_previews": file_previews,
            "ai":            full_response
        })
        st.rerun()
