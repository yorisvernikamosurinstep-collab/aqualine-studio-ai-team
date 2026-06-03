import streamlit as st
import streamlit.components.v1 as components
import requests, json, base64, os, re
from datetime import datetime

try:
    import pdfplumber
    from docx import Document
except ImportError:
    pass

st.set_page_config(page_title="Virtual Office & Team Chat", layout="wide")

# ══════════════════════════════════════════════════════════════════
# ดึง API KEY จาก secrets
# ══════════════════════════════════════════════════════════════════
if "GOOGLE_API_KEY" in st.secrets:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("🔑 ไม่พบ GOOGLE_API_KEY ใน secrets.toml")
    st.stop()

# ══════════════════════════════════════════════════════════════════
# 🧬 PERSONA LOADER — sync กับ Agent Persona Editor (หน้า 13)
# ══════════════════════════════════════════════════════════════════
PERSONA_FILE = "agent_personas.json"

def load_custom_personas() -> dict:
    """โหลด custom system prompts จาก agent_personas.json"""
    if os.path.exists(PERSONA_FILE):
        try:
            with open(PERSONA_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
            out = {}
            for k, v in raw.items():
                if k == "__full__":
                    continue
                if isinstance(v, str):
                    out[k] = v
                elif isinstance(v, dict):
                    out[k] = v.get("system_prompt", "")
            return out
        except:
            pass
    return {}

# Reload ทุกครั้งที่หน้า render เพื่อรับ persona ใหม่จากหน้า 13 ทันที
_custom_personas = load_custom_personas()

# ══════════════════════════════════════════════════════════════════
# 🎯 THE REAL TWO-WAY SYNC (ระบบซิงค์ที่รื้อและแก้ไขใหม่ 100%)
# ══════════════════════════════════════════════════════════════════
# สร้างตัวแปรเริ่มต้นสำหรับช่องเลือก
if "widget_chat_multiselect" not in st.session_state:
    st.session_state.widget_chat_multiselect = []

# ฟังก์ชันนี้จะทำงานเมื่อ JS ส่งรายชื่อตัวละครในวงกลมมาให้
def sync_js_to_py():
    val = st.session_state.js_sync_val
    if val:
        try:
            # 🎯 จุดสำคัญที่แก้ปัญหา: เอาค่าที่ JS ส่งมา ยัดใส่กล่อง Choose Options โดยตรง!
            st.session_state.widget_chat_multiselect = json.loads(val)
        except: 
            pass

# กล่องรับข้อมูลลับ (เดี๋ยว JS จะมาจับซ่อนให้เองแบบเนียนๆ ไม่ให้หลุดขึ้นจอ)
st.text_input("JS_SYNC_INPUT", key="js_sync_val", on_change=sync_js_to_py, label_visibility="collapsed")


# ══════════════════════════════════════════════════════════════════
# DATA: ข้อมูล Agent (ครบ 25 ตัว)
# ══════════════════════════════════════════════════════════════════
AGENTS = {
    "A1":  {"name":"นักกลยุทธ์การตลาด", "icon":"👨‍💼", "p":"วางแผนภาพรวม กลยุทธ์ Positioning และจุดขายหลัก", "rarity":"LEGENDARY", "zone":"center"},
    "A2":  {"name":"ผู้จัดการโครงการ", "icon":"📋", "p":"คุมเป้าหมาย ไทม์ไลน์ และทรัพยากรทีมงาน", "rarity":"EPIC", "zone":"center"},
    "A10": {"name":"นักวิเคราะห์ข้อมูล", "icon":"📊", "p":"วิเคราะห์สถิติ ความคุ้มค่า และ Data Insight", "rarity":"EPIC", "zone":"center"},
    "A17": {"name":"นักวิจัยตลาด", "icon":"🔍", "p":"เจาะลึกข้อมูลคู่แข่ง Trend และ Market Intelligence", "rarity":"EPIC", "zone":"center"},
    "A19": {"name":"นักขายมือโปร", "icon":"💰", "p":"สร้าง Sales Script, Pitch Deck และปิดการขาย", "rarity":"EPIC", "zone":"center"},
    "A25": {"name":"นักจิตวิทยาการตลาด", "icon":"🧠", "p":"Psychology Marketing, Trigger การซื้อ และ Persuasion", "rarity":"LEGENDARY", "zone":"center"},
    "A3":  {"name":"นักเขียนคำโฆษณา", "icon":"✍️", "p":"สร้าง Content, Caption, Hook และ Copy โซเชียล", "rarity":"EPIC", "zone":"top_left"},
    "A7":  {"name":"นักยิงแอด Facebook", "icon":"📈", "p":"วางแผน Campaign, Audience, Budget และ KPI Ads", "rarity":"LEGENDARY", "zone":"top_left"},
    "A8":  {"name":"ผู้เชี่ยวชาญ SEO", "icon":"🌐", "p":"ปรับแต่งเนื้อหา Keyword และ On-Page SEO", "rarity":"EPIC", "zone":"top_left"},
    "A21": {"name":"นักเขียนบทความ", "icon":"📝", "p":"เขียนบทความยาว Long-form Content และเนื้อหาเชิงลึก", "rarity":"RARE", "zone":"top_left"},
    "A23": {"name":"ผู้เชี่ยวชาญ LINE OA", "icon":"📱", "p":"วางแผน LINE OA, CRM, Broadcast และ Chatbot", "rarity":"EPIC", "zone":"top_left"},
    "A9":  {"name":"ฝ่ายบริการลูกค้า", "icon":"💬", "p":"วางแนวทาง FAQ, Script ตอบคำถาม และ CRM", "rarity":"RARE", "zone":"top_right"},
    "A15": {"name":"นักวางระบบอัตโนมัติ", "icon":"⚙️", "p":"เชื่อมระบบ Automation, Zapier และ Workflow", "rarity":"RARE", "zone":"top_right"},
    "A22": {"name":"นักวางราคา/Pricing", "icon":"🧮", "p":"วิเคราะห์ราคา ตั้ง Promo Bundle และ Pricing Strategy", "rarity":"EPIC", "zone":"top_right"},
    "A4":  {"name":"กราฟิกดีไซเนอร์", "icon":"🎨", "p":"ออกแบบ Visual, Brand Identity และ Layout", "rarity":"EPIC", "zone":"bottom_left"},
    "A5":  {"name":"3D Visualizer", "icon":"🏗️", "p":"เรนเดอร์ภาพสินค้า 3D และ Architectural Viz", "rarity":"EPIC", "zone":"bottom_left"},
    "A13": {"name":"อาร์ตไดเรกเตอร์", "icon":"✨", "p":"ควบคุมคุณภาพ Visual, Style Guide และ QA งาน", "rarity":"EPIC", "zone":"bottom_left"},
    "A14": {"name":"ผู้เชี่ยวชาญ AI Prompt", "icon":"🤖", "p":"ปรับจูน Prompt Engineering สำหรับ AI Tools", "rarity":"EPIC", "zone":"bottom_left"},
    "A16": {"name":"นักออกแบบบูธ", "icon":"🎪", "p":"วางผัง Exhibition, Event Space และ Signage", "rarity":"RARE", "zone":"bottom_left"},
    "A20": {"name":"ที่ปรึกษากฎหมาย", "icon":"⚖️", "p":"ตรวจสอบข้อบังคับ ลิขสิทธิ์ และ Legal Compliance", "rarity":"EPIC", "zone":"bottom_left"},
    "A6":  {"name":"ผู้เชี่ยวชาญวิดีโอ", "icon":"🎬", "p":"สคริปต์ มุมกล้อง Storyboard และ Production", "rarity":"EPIC", "zone":"bottom_right"},
    "A11": {"name":"ครีเอทีฟไดเรกเตอร์", "icon":"💡", "p":"คิด Big Idea, Concept และควบคุมทิศทางงานสร้างสรรค์", "rarity":"LEGENDARY", "zone":"bottom_right"},
    "A12": {"name":"คนเขียนสตอรี่บอร์ด", "icon":"🎞️", "p":"วางลำดับภาพ เล่าเรื่อง และ Visual Narrative", "rarity":"RARE", "zone":"bottom_right"},
    "A18": {"name":"ฝ่ายตรวจสเปกสินค้า", "icon":"✅", "p":"ตรวจสอบความถูกต้องทางเทคนิค Spec และ QC", "rarity":"RARE", "zone":"bottom_right"},
    "A24": {"name":"TikTok & Reels", "icon":"🎵", "p":"Hook, Trend, Script TikTok/Reels และ Viral Content", "rarity":"EPIC", "zone":"bottom_right"},
}

def agent_b64(aid: str) -> str:
    path = os.path.join("agents", f"{aid}.png")
    if os.path.exists(path):
        with open(path, "rb") as f:
            return "data:image/png;base64," + base64.b64encode(f.read()).decode()
    return ""

def get_bg_b64() -> str:
    path = os.path.join("assets", "office_bg.jpg")
    if os.path.exists(path):
        with open(path, "rb") as f:
            ext = path.split('.')[-1]
            mime = "image/jpeg" if ext.lower() in ["jpg", "jpeg"] else "image/png"
            return f"data:{mime};base64," + base64.b64encode(f.read()).decode()
    return ""

agents_json_parts = []
for aid, info in AGENTS.items():
    b64 = agent_b64(aid)
    agents_json_parts.append(
        f'{{"id":"{aid}","name":"{info["name"]}","role":"{info["p"]}","rarity":"{info["rarity"]}",'
        f'"icon":"{info["icon"]}","img":"{b64}","zone":"{info["zone"]}"}}'
    )
agents_json = "[" + ",".join(agents_json_parts) + "]"
bg_base64 = get_bg_b64()

# ดึงสถานะปัจจุบันของช่องแชท ส่งให้เอนจินเกม 3D ทราบ
py_selected_json = json.dumps(st.session_state.widget_chat_multiselect)

# ══════════════════════════════════════════════════════════════════
# AI LOGIC
# ══════════════════════════════════════════════════════════════════
@st.cache_data(ttl=300)
def get_best_model(api_key): return "models/gemini-2.5-flash"

def process_file(file) -> dict:
    fname, ftype = file.name.lower(), file.type or ""
    if ftype.startswith("image/") or fname.endswith((".jpg",".jpeg",".png",".webp")):
        return {"type":"image","name":file.name,"content":base64.b64encode(file.read()).decode(),"mime":ftype or "image/jpeg"}
    if ftype.startswith("video/") or fname.endswith((".mp4",".mov")):
        data = file.read()
        if len(data) <= 20 * 1024 * 1024:
            return {"type":"video","name":file.name,"content":base64.b64encode(data).decode(),"mime":ftype or "video/mp4"}
        return {"type":"toolarge","name":file.name,"content":"[ไฟล์ใหญ่เกิน 20MB]"}
    if ftype == "application/pdf" or fname.endswith(".pdf"):
        try:
            with pdfplumber.open(file) as pdf:
                text = "\n".join([p.extract_text() or "" for p in pdf.pages])
            return {"type":"text_file","name":file.name,"content":text[:15000],"mime":"pdf"}
        except: return {"type":"text_file","name":file.name,"content":f"[อ่าน PDF ไม่ได้]"}
    if ftype.startswith("text/") or fname.endswith((".txt",".csv",".md",".py",".html")):
        return {"type":"text_file","name":file.name,"content":file.read().decode("utf-8", errors="replace")[:15000],"mime":ftype}
    return {"type":"text_file","name":file.name,"content":f"[ไฟล์ {file.name}]"}

def build_parts(processed_files, user_msg):
    parts, extra_text = [], ""
    for f in processed_files:
        if f["type"] in ["image", "video", "audio"]: parts.append({"inlineData":{"mimeType":f["mime"],"data":f["content"]}})
        else: extra_text += f"\n\n--- ไฟล์: {f['name']} ---\n{f['content']}"
    parts.append({"text": user_msg + (f"\n\n[ข้อมูลจากไฟล์แนบ]{extra_text}" if extra_text else "")})
    return parts

def call_team_agent_stream(agent_id, team_history, user_msg, processed_files=None):
    info, model = AGENTS[agent_id], get_best_model(API_KEY)
    context_str = "ประวัติการสนทนาในห้องแชทล่าสุด:\n" + "".join([f"{'Boss (คุณ)' if m['role']=='user' else f'[{m.get('agent','')}] {AGENTS.get(m.get('agent',''),{}).get('name','')}'}: {m['text']}\n" for m in team_history[-6:]]) if team_history else ""
    # 🧬 ใช้ Custom Persona จากหน้า 13 ถ้ามี ไม่งั้นใช้ default
    _personas = load_custom_personas()
    custom_p = _personas.get(agent_id, "").strip()
    system = custom_p if custom_p else f"คุณคือ {info['name']} ({info['p']}) ของทีม AQUALINE STUDIO\nตอบในมุมมองและหน้าที่ของคุณเท่านั้น! เป็นภาษาไทย กระชับ ตรงประเด็น"
    url = f"https://generativelanguage.googleapis.com/v1beta/{model}:streamGenerateContent?alt=sse&key={API_KEY}"
    try:
        with requests.post(url, json={"system_instruction":{"parts":[{"text":system}]}, "contents":[{"role":"user","parts":build_parts(processed_files or [], f"{context_str}\n\nคำสั่งล่าสุดจาก Boss: {user_msg}")}], "generationConfig":{"temperature":0.8,"maxOutputTokens":4096}}, stream=True, timeout=180) as resp:
            if resp.status_code != 200: yield f"❌ Error {resp.status_code}"; return
            for line in resp.iter_lines():
                if line and line.decode("utf-8").startswith("data: "):
                    try:
                        chunk = json.loads(line.decode("utf-8")[6:])["candidates"][0]["content"]["parts"][0].get("text","")
                        if chunk: yield chunk
                    except: pass
    except Exception as e: yield f"❌ Error: {str(e)[:100]}"


# ══════════════════════════════════════════════════════════════════
# UI & LAYOUT: ซ้าย (Office) | ขวา (Team Chat)
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
.stApp { background: linear-gradient(135deg, #0b0f19 0%, #1a1a2e 100%); color: #e2e8f0; }
.chat-container { background: rgba(15,23,42,0.6); border-radius: 12px; border: 1px solid #334155; padding: 12px; }
.user-msg { background: rgba(59,130,246,0.15); border: 1px solid #3b82f644; border-radius: 12px 12px 4px 12px; padding: 10px; margin-bottom: 12px; text-align: right; }
.ai-msg { background: rgba(30,41,59,0.8); border: 1px solid #475569; border-radius: 12px 12px 12px 4px; padding: 10px; margin-bottom: 12px; }
.ai-name { font-weight: bold; color: #a78bfa; font-size: 13px; margin-bottom: 4px; }
</style>
""", unsafe_allow_html=True)

col_office, col_chat = st.columns([7.5, 2.5], gap="small")

with col_office:
    OFFICE_HTML = f"""<!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
    *{{margin:0;padding:0;box-sizing:border-box;}}
    body{{background:#0d0d1a;font-family:'Courier New',monospace; overflow: hidden;}}
    #ctrl{{display:flex;gap:8px;padding:8px 12px;background:#13102a;border-bottom:2px solid #534AB7;flex-wrap:wrap;align-items:center;}}
    #ctrl span{{color:#a78bfa;font-size:11px;font-weight:bold;margin-right:4px;}}
    .cb{{padding:5px 14px;border-radius:4px;border:2px solid;font-family:'Courier New',monospace;font-size:11px;font-weight:bold;cursor:pointer;transition:all .15s;user-select:none;background:#0d0d1a;}}
    .bw{{border-color:#34d399;color:#34d399;}}
    .bk{{border-color:#60a5fa;color:#60a5fa;}}
    .bm{{border-color:#f472b6;color:#f472b6;}}
    .cb:hover{{opacity:.7;transform:scale(1.05);}}
    .cb.active{{background:rgba(59,130,246,0.2);}}
    #mlbl{{margin-left:auto;padding:4px 12px;border-radius:4px;font-size:11px;font-weight:bold;color:#fff;background:#534AB7;border:1px solid #7c6fdb;}}

    #sc {{ position: relative; width: 100%; height: 800px; background: #0d0d1a; overflow: hidden; }}
    #world {{ position: absolute; transform-origin: top left; }}
    #bg-canvas {{ position: absolute; top:0; left:0; }}
    #al {{ position: absolute; top:0; left:0; width: 100%; height: 100%; }}
    
    .asp{{position:absolute;width:60px;height:80px;image-rendering:pixelated;cursor:grab;z-index:10;}}
    .asp:active {{ cursor:grabbing; }}
    .asp img{{width:100%;height:100%;object-fit:contain;image-rendering:pixelated; pointer-events: none;}}
    .albl{{position:absolute;bottom:-15px;left:50%;transform:translateX(-50%);font-size:11px;white-space:nowrap;color:#ffe066;pointer-events:none;text-shadow:1px 1px 0 #000,-1px -1px 0 #000; font-weight:bold;}}
    .ash{{position:absolute;bottom:0;left:50%;transform:translateX(-50%);width:40px;height:8px;background:rgba(0,0,0,.5);border-radius:50%; filter:blur(1px); pointer-events: none;}}
    
    #tip{{position:absolute;background:rgba(10,8,28,.97);border:2px solid #534AB7;border-radius:6px;padding:8px 12px;font-size:11px;color:#e2e8f0;pointer-events:none;z-index:200;display:none;max-width:200px;}}
    .tn{{color:#ffe066;font-weight:bold;font-size:12px;margin-bottom:2px;}}
    .tr{{color:#a78bfa;font-size:10px;margin-bottom:4px;}}
    .bL{{background:linear-gradient(90deg,#f59e0b,#ef4444);color:#fff;font-size:9px;font-weight:bold;padding:1px 6px;border-radius:3px;}}
    .bE{{background:linear-gradient(90deg,#8b5cf6,#6366f1);color:#fff;font-size:9px;font-weight:bold;padding:1px 6px;border-radius:3px;}}
    .bR{{background:linear-gradient(90deg,#3b82f6,#06b6d4);color:#fff;font-size:9px;font-weight:bold;padding:1px 6px;border-radius:3px;}}
    </style>
    </head>
    <body>
    <div id="ctrl">
      <span>🏢 OFFICE ACTIVITY:</span>
      <button class="cb bw" id="btn-work" onclick="setMode('work')">💼 ทำงานที่โต๊ะ</button>
      <button class="cb bk active" id="btn-walk" onclick="setMode('walk')">🚶 เดินเล่นอิสระ</button>
      <button class="cb bm" id="btn-meet" onclick="setMode('meet')">📋 ประชุมทีม</button>
      <div id="mlbl">💡 ลากตัวละครลงฐานวงกลม เพื่อดึงตัวเข้าแชท!</div>
    </div>
    <div id="sc">
      <div id="world">
        <canvas id="bg-canvas"></canvas>
        <div id="al"></div>
      </div>
      <div id="tip"></div>
    </div>

    <script>
    const AGENTS = {agents_json};
    const PYTHON_SELECTED = {py_selected_json};
    
    const sc     = document.getElementById('sc');
    const world  = document.getElementById('world');
    const canvas = document.getElementById('bg-canvas');
    const ctx    = canvas.getContext('2d');
    const al     = document.getElementById('al');
    const tip    = document.getElementById('tip');
    const mlbl   = document.getElementById('mlbl');

    let WORLD_W = 1600;
    let WORLD_H = 900;
    
    // 🎯 ความจำชั่วคราว ให้ตัวละครไม่ลืมพิกัดเก่าเวลาถูกรีโหลดจาก Streamlit
    let savedState = {{}};
    try {{
        const data = sessionStorage.getItem('aqualine_agent_positions');
        if (data) savedState = JSON.parse(data);
    }} catch(e) {{}}

    function savePositions() {{
        let stateToSave = {{}};
        states.forEach(s => {{
            stateToSave[s.ag.id] = {{ x: s.x, y: s.y, inCircle: s.inCircle, mode: s.mode }};
        }});
        try {{ sessionStorage.setItem('aqualine_agent_positions', JSON.stringify(stateToSave)); }} catch(e) {{}}
    }}
    setInterval(savePositions, 500);

    const bgImg = new Image();
    bgImg.onload = function() {{
      WORLD_W = bgImg.naturalWidth || 1600;
      WORLD_H = bgImg.naturalHeight || 900;
      world.style.width = WORLD_W + 'px';
      world.style.height = WORLD_H + 'px';
      canvas.width = WORLD_W;
      canvas.height = WORLD_H;
      ctx.drawImage(bgImg, 0, 0, WORLD_W, WORLD_H);
      resize();
      
      initAgents();
      requestAnimationFrame(animate);
    }};
    bgImg.src = '{bg_base64}';

    function resize() {{
      const containerW = sc.offsetWidth; 
      const containerH = 800; 
      sc.style.height = containerH + 'px';
      const scale = Math.min(containerW / WORLD_W, containerH / WORLD_H);
      world.style.transform = `scale(${{scale}})`;
      const offsetX = (containerW - (WORLD_W * scale)) / 2;
      const offsetY = (containerH - (WORLD_H * scale)) / 2;
      world.style.left = offsetX + 'px';
      world.style.top = offsetY + 'px';
    }}
    window.addEventListener('resize', resize);

    // 🎯 ฟังก์ชันซ่อน Input ลับของ Python 
    // โดยใช้ JS วิ่งไปหาแล้วจัดการใส่ Display None ให้กล่องหลักของมัน (แก้ปัญหาโค้ดโผล่ 100%)
    function hidePythonElements() {{
      try {{
        const parentDoc = window.parent.document;
        const input = parentDoc.querySelector('input[aria-label="JS_SYNC_INPUT"]');
        if (input) {{
            const container = input.closest('div[data-testid="stElementContainer"]');
            if (container) {{
                container.style.position = 'fixed';
                container.style.top = '-10000px';
                container.style.opacity = '0';
                container.style.pointerEvents = 'none';
            }}
        }}
      }} catch(e) {{}}
    }}
    setInterval(hidePythonElements, 200);

    const ZONES = {{
      'center':       {{ rxMin: 0.38, rxMax: 0.62, ryMin: 0.25, ryMax: 0.50 }},
      'top_left':     {{ rxMin: 0.08, rxMax: 0.35, ryMin: 0.22, ryMax: 0.50 }},
      'top_right':    {{ rxMin: 0.65, rxMax: 0.92, ryMin: 0.25, ryMax: 0.50 }},
      'bottom_left':  {{ rxMin: 0.08, rxMax: 0.40, ryMin: 0.55, ryMax: 0.88 }},
      'bottom_right': {{ rxMin: 0.60, rxMax: 0.92, ryMin: 0.55, ryMax: 0.88 }}
    }};

    const PORTAL_CX = 0.50; 
    const PORTAL_CY = 0.865;

    function randPos(zone, isPortal=false) {{
      if(isPortal) {{
        const cx = WORLD_W * PORTAL_CX;
        const cy = WORLD_H * PORTAL_CY;
        const angle = Math.random() * Math.PI * 2;
        const r = Math.sqrt(Math.random());
        return {{ x: cx + Math.cos(angle) * 110 * r, y: cy + Math.sin(angle) * 35 * r }};
      }}
      const b = ZONES[zone] || ZONES['center'];
      return {{ x: (b.rxMin + Math.random() * (b.rxMax - b.rxMin)) * WORLD_W, y: (b.ryMin + Math.random() * (b.ryMax - b.ryMin)) * WORLD_H }};
    }}

    const DESK_POSITIONS = {{
      'center':       [ {{rx:0.42, ry:0.35}}, {{rx:0.58, ry:0.35}}, {{rx:0.50, ry:0.48}}, {{rx:0.50, ry:0.25}}, {{rx:0.40, ry:0.48}}, {{rx:0.60, ry:0.48}} ],
      'top_left':     [ {{rx:0.20, ry:0.45}}, {{rx:0.30, ry:0.50}}, {{rx:0.10, ry:0.38}}, {{rx:0.25, ry:0.35}}, {{rx:0.15, ry:0.28}} ],
      'top_right':    [ {{rx:0.70, ry:0.50}}, {{rx:0.80, ry:0.43}}, {{rx:0.90, ry:0.35}} ],
      'bottom_left':  [ {{rx:0.28, ry:0.85}}, {{rx:0.18, ry:0.80}}, {{rx:0.38, ry:0.75}}, {{rx:0.20, ry:0.60}}, {{rx:0.30, ry:0.65}}, {{rx:0.10, ry:0.65}} ],
      'bottom_right': [ {{rx:0.65, ry:0.85}}, {{rx:0.75, ry:0.80}}, {{rx:0.65, ry:0.65}}, {{rx:0.85, ry:0.60}}, {{rx:0.90, ry:0.75}} ]
    }};

    const deskCounter = {{ 'center':0, 'top_left':0, 'top_right':0, 'bottom_left':0, 'bottom_right':0 }};
    function getDeskPos(zone) {{
      const desks = DESK_POSITIONS[zone];
      if (desks && deskCounter[zone] < desks.length) {{
        let pos = desks[deskCounter[zone]]; deskCounter[zone]++; 
        return {{ x: pos.x !== undefined ? pos.x : (pos.rx * WORLD_W), y: pos.y !== undefined ? pos.y : (pos.ry * WORLD_H) }};
      }}
      return randPos(zone);
    }}

    const states=[];
    let isDragging = false;
    let dragSt = null;
    let dragOffsetX = 0;
    let dragOffsetY = 0;

    function initAgents() {{
        AGENTS.forEach((ag, i) => {{
          const wrap = document.createElement('div'); wrap.className = 'asp'; wrap.dataset.id = ag.id;
          if (ag.img) {{ const im = document.createElement('img'); im.src = ag.img; wrap.appendChild(im); }}
          const sh = document.createElement('div'); sh.className = 'ash';
          const lb = document.createElement('div'); lb.className = 'albl'; lb.textContent = ag.id;
          wrap.appendChild(sh); wrap.appendChild(lb); al.appendChild(wrap);

          const inCircle = PYTHON_SELECTED.includes(ag.id);
          const oldState = savedState[ag.id];
          
          // 🎯 จุดเริ่มต้น: ดึงจากความจำเสมอ ถ้าไม่มีความจำให้เช็กว่าต้องเริ่มในวงกลมหรือสุ่มปกติ
          let startX = oldState ? oldState.x : (inCircle ? randPos('', true).x : getDeskPos(ag.zone).x);
          let startY = oldState ? oldState.y : (inCircle ? randPos('', true).y : getDeskPos(ag.zone).y);

          const st = {{ 
            el: wrap, ag: ag, 
            x: startX, y: startY, 
            deskX: getDeskPos(ag.zone).x, deskY: getDeskPos(ag.zone).y,
            tx: startX, ty: startY, vx: 0, vy: 0, dir: 1, 
            mode: 'walk', 
            stateTimer: Math.random()*120 + 60,
            inCircle: inCircle
          }};
          
          // 🎯 ให้ "เดิน" ไปหาเป้าหมายอย่างสมูท (แก้ปัญหาการวาร์ปถาวร)
          if (inCircle) {{
              if (oldState && !oldState.inCircle) {{
                  const wp = randPos('', true);
                  st.tx = wp.x; st.ty = wp.y;
              }} else if (!oldState) {{
                  const wp = randPos('', true);
                  st.tx = wp.x; st.ty = wp.y;
              }} else {{
                  const wp = randPos('', true);
                  st.tx = wp.x; st.ty = wp.y;
              }}
              st.mode = 'walk';
          }} else {{
              if (oldState && oldState.inCircle) {{
                  // ออกจากแชท: เดินกลับโต๊ะ
                  st.tx = st.deskX; st.ty = st.deskY;
                  st.mode = 'walk';
              }} else {{
                  // เดินเล่นอิสระ
                  const wp = randPos(ag.zone);
                  st.tx = wp.x; st.ty = wp.y;
              }}
          }}

          states.push(st);

          wrap.addEventListener('mouseenter', e => {{
            if(isDragging) return;
            tip.style.display='block';
            const bc = ag.rarity==='LEGENDARY' ? 'bL' : ag.rarity==='EPIC' ? 'bE' : 'bR';
            tip.innerHTML = `<div class="tn">${{ag.icon}} ${{ag.name}}</div><div class="tr">${{ag.role}}</div><span class="${{bc}}">${{ag.rarity}}</span><div style="margin-top:4px;color:#64748b;font-size:9px">Zone: ${{ag.zone.toUpperCase().replace('_',' ')}}</div>`;
          }});
          wrap.addEventListener('mouseleave', () => tip.style.display='none');
          wrap.addEventListener('mousemove', e => {{
            if(isDragging) return;
            const r = document.body.getBoundingClientRect();
            let tx = e.clientX + 14, ty = e.clientY - 70;
            if (tx + 210 > r.width) tx = tx - 220;
            tip.style.left = tx + 'px'; tip.style.top = ty + 'px';
          }});

          wrap.addEventListener('mousedown', e => {{
            e.preventDefault();
            isDragging = true;
            dragSt = st;
            tip.style.display='none';
            const rect = world.getBoundingClientRect();
            const scale = rect.width / WORLD_W;
            const mouseX = (e.clientX - rect.left) / scale;
            const mouseY = (e.clientY - rect.top) / scale;
            dragOffsetX = dragSt.x - mouseX;
            dragOffsetY = dragSt.y - mouseY;
            dragSt.mode = 'drag';
            dragSt.el.style.zIndex = 99999;
          }});
        }});
    }}

    window.addEventListener('mousemove', e => {{
      if(!isDragging || !dragSt) return;
      const rect = world.getBoundingClientRect();
      const scale = rect.width / WORLD_W;
      const mouseX = (e.clientX - rect.left) / scale;
      const mouseY = (e.clientY - rect.top) / scale;
      dragSt.x = mouseX + dragOffsetX;
      dragSt.y = mouseY + dragOffsetY;
      dragSt.el.style.left = (dragSt.x - 30) + 'px'; 
      dragSt.el.style.top = (dragSt.y - 80) + 'px';
    }});

    window.addEventListener('mouseup', e => {{
      if(!isDragging || !dragSt) return;
      isDragging = false;
      const cx = WORLD_W * PORTAL_CX;
      const cy = WORLD_H * PORTAL_CY; 
      const dx = dragSt.x - cx;
      const dy = dragSt.y - cy;
      const inPortal = ((dx*dx)/(160*160) + (dy*dy)/(55*55)) <= 1;
      
      let changed = false;
      if(inPortal) {{
        if(!dragSt.inCircle) {{ dragSt.inCircle = true; changed = true; }}
        dragSt.mode = 'walk';
        const wp = randPos('', true);
        dragSt.tx = wp.x; dragSt.ty = wp.y;
      }} else {{
        if(dragSt.inCircle) {{ dragSt.inCircle = false; changed = true; }}
        dragSt.mode = 'walk';
        const wp = randPos(dragSt.ag.zone); 
        dragSt.tx = wp.x; dragSt.ty = wp.y;
      }}
      
      if (changed) {{
          savePositions(); // จำพิกัดให้แม่น ก่อนที่จะสั่งรีเฟรชหน้าต่าง
          notifyPython();
      }}
      dragSt = null;
    }});

    // 🎯 ท่อส่งข้อมูลฉบับแก้ปัญหา 100%: จำลองการกดพิมพ์แล้ว Blur เพื่อหลอก Streamlit ให้รับข้อมูล
    function notifyPython() {{
      let selected = states.filter(s => s.inCircle).map(s => s.ag.id);
      try {{
        const parentDoc = window.parent.document;
        const input = parentDoc.querySelector('input[aria-label="JS_SYNC_INPUT"]');
        
        if (input) {{
            // เช็กก่อนว่าค่าเปลี่ยนจริงมั้ย จะได้ไม่ทำงานซ้ำซ้อน
            if(input.value === JSON.stringify(selected)) return;
            
            input.focus(); // โฟกัสกล่องเหมือนคนเอาเมาส์ไปคลิก
            let nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
            nativeSetter.call(input, JSON.stringify(selected));
            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
            
            // สั่งให้กด Enter 
            input.dispatchEvent(new KeyboardEvent('keydown', {{ key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }}));
            input.dispatchEvent(new KeyboardEvent('keyup', {{ key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true }}));
            
            input.blur(); // ยกเลิกการโฟกัส เพื่อให้ Streamlit ส่งข้อมูลไปหลังบ้าน!
        }}
      }} catch (e) {{ console.log("Sync Error:", e); }}
    }}

    let gMode = 'walk'; 
    const mLbls = {{work:'💼 ทำงานที่โต๊ะ', walk:'🚶 เดินเล่นอิสระ', meet:'📋 ประชุมทีม'}};
    
    function setMode(m) {{
      gMode = m; mlbl.textContent = mLbls[m];
      document.getElementById('btn-work').className = 'cb bw' + (m==='work'?' active':'');
      document.getElementById('btn-walk').className = 'cb bk' + (m==='walk'?' active':'');
      document.getElementById('btn-meet').className = 'cb bm' + (m==='meet'?' active':'');

      states.forEach((s) => {{
        if(s.mode === 'drag') return;
        if(s.inCircle) {{
            s.mode = 'walk'; 
            const wp = randPos('', true); 
            s.tx = wp.x; s.ty = wp.y; 
            s.stateTimer = Math.random() * 120 + 60;
            return;
        }}

        if (m === 'work') {{ s.mode = 'work'; s.tx = s.deskX; s.ty = s.deskY; s.stateTimer = Math.random() * 80 + 40; }}
        else if (m === 'walk') {{ s.mode = 'walk'; const wp = randPos(s.ag.zone); s.tx = wp.x; s.ty = wp.y; s.stateTimer = Math.random() * 120 + 60; }}
        else if (m === 'meet') {{ s.mode = 'meet'; const b = ZONES[s.ag.zone]; const centerX = (b.rxMin + (b.rxMax - b.rxMin)/2) * WORLD_W; const centerY = (b.ryMin + (b.ryMax - b.ryMin)/2) * WORLD_H; const angle = Math.random() * Math.PI * 2; const radius = WORLD_W * 0.025; s.tx = centerX + Math.cos(angle) * radius; s.ty = centerY + Math.sin(angle) * radius; s.stateTimer = 9999; }}
      }});
    }}

    let tick = 0;
    function animate() {{
      tick++;
      states.forEach(s => {{
        if(s.mode === 'drag') return;

        s.stateTimer--;
        if (s.mode === 'walk' && s.stateTimer <= 0) {{ 
            const wp = s.inCircle ? randPos('', true) : randPos(s.ag.zone); 
            s.tx = wp.x; s.ty = wp.y; 
            s.stateTimer = Math.random() * 150 + 60; 
        }}
        
        const dx = s.tx - s.x, dy = s.ty - s.y; const dist = Math.sqrt(dx*dx + dy*dy);
        const spd = (s.mode === 'walk') ? WORLD_W*0.001 : WORLD_W*0.0015; 
        if (dist > 2) {{ s.vx = (dx/dist) * spd; s.vy = (dy/dist) * spd; s.dir = s.vx < 0 ? -1 : 1; s.x += s.vx; s.y += s.vy; }} else {{ s.vx = 0; s.vy = 0; }}
        const isMoving = Math.abs(s.vx) > 0 || Math.abs(s.vy) > 0;
        let bounce = 0; if (isMoving) bounce = Math.abs(Math.sin(tick * 0.35)) * 2.5;
        
        s.el.style.left = (s.x - 30) + 'px'; 
        s.el.style.top = (s.y - 80 - bounce) + 'px';
        s.el.style.transform = `scaleX(${{s.dir}})`; s.el.style.zIndex = Math.round(s.y); 
      }});
      requestAnimationFrame(animate);
    }}
    </script>
    </body>
    </html>"""
    components.html(OFFICE_HTML, height=830, scrolling=False)

# ══════════════════════════════════════════════════════════════════
# SIDE PANEL: Team Chat (25% ขวา)
# ══════════════════════════════════════════════════════════════════
with col_chat:
    st.markdown("""
    <div style='background:linear-gradient(90deg, #1e1b4b, #0f172a); padding: 12px; border-radius: 8px; border-bottom: 2px solid #6366f1; margin-bottom: 12px;'>
      <div style='font-size: 16px; font-weight: 800; color: #fff;'>💬 Team Chat (#hq-general)</div>
    </div>
    """, unsafe_allow_html=True)

    # 🎯 หากคุณโยริเลือกชื่อจากกล่องแชทโดยตรง ตัวละครจะค่อยๆ "เดิน" มารวมตัวกันที่วงกลม
    def on_chat_box_change():
        pass # ปล่อยให้ Streamlit อัปเดต st.session_state.widget_chat_multiselect ไปเลย

    selected_agents = st.multiselect(
        "เรียกตัว AI เข้าร่วมแชท (3-5 คน):",
        options=list(AGENTS.keys()),
        default=st.session_state.widget_chat_multiselect,
        format_func=lambda aid: f"{AGENTS[aid]['icon']} {AGENTS[aid]['name']}",
        max_selections=5,
        key="widget_chat_multiselect",
        on_change=on_chat_box_change
    )

    uploaded_files = st.file_uploader(
        "แนบไฟล์ (เอกสาร, รูปภาพ, โค้ด)", 
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

    if "team_chat_history" not in st.session_state:
        st.session_state.team_chat_history = []

    chat_box = st.container(height=520)
    with chat_box:
        if not st.session_state.team_chat_history:
            st.markdown("<div style='text-align:center; color:#64748b; margin-top:50px;'>เริ่มพิมพ์สั่งงาน หรือลากทีมงานลงมาที่วงกลมได้เลยครับ!</div>", unsafe_allow_html=True)
            
        for msg in st.session_state.team_chat_history:
            if msg["role"] == "user":
                if msg.get("files"):
                    files_html = "".join([f"<span style='background:#1e293b; padding:2px 6px; border-radius:4px; font-size:11px; margin-right:4px;'>📎 {f}</span>" for f in msg["files"]])
                    st.markdown(f"<div style='text-align:right; margin-bottom:4px;'>{files_html}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='user-msg'>👤 <b>You (Boss):</b><br>{msg['text']}</div>", unsafe_allow_html=True)
            else:
                aid = msg["agent"]
                icon = AGENTS[aid]["icon"]
                name = AGENTS[aid]["name"]
                st.markdown(f"<div class='ai-msg'><div class='ai-name'>{icon} {name}</div>{msg['text']}</div>", unsafe_allow_html=True)

    prompt = st.chat_input("พิมพ์คำสั่งงานให้ทีม...")

    if prompt:
        if not selected_agents:
            st.error("กรุณาเลือก Agent เข้าห้องแชทอย่างน้อย 1 คนครับ")
        else:
            processed_files = []
            file_names = []
            if uploaded_files:
                for f in uploaded_files:
                    processed_files.append(process_file(f))
                    file_names.append(f.name)
            
            st.session_state.team_chat_history.append({"role": "user", "text": prompt, "files": file_names})
            with chat_box:
                st.markdown(f"<div class='user-msg'>👤 <b>You (Boss):</b><br>{prompt}</div>", unsafe_allow_html=True)
            
            for aid in selected_agents:
                with chat_box:
                    icon = AGENTS[aid]["icon"]
                    name = AGENTS[aid]["name"]
                    placeholder = st.empty()
                    
                    full_response = ""
                    for chunk in call_team_agent_stream(aid, st.session_state.team_chat_history, prompt, processed_files):
                        full_response += chunk
                        placeholder.markdown(f"<div class='ai-msg'><div class='ai-name'>{icon} {name}</div>{full_response}▌</div>", unsafe_allow_html=True)
                    
                    placeholder.markdown(f"<div class='ai-msg'><div class='ai-name'>{icon} {name}</div>{full_response}</div>", unsafe_allow_html=True)
                
                st.session_state.team_chat_history.append({"role": "ai", "agent": aid, "text": full_response})
            
            st.rerun()