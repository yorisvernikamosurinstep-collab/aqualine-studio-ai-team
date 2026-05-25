import streamlit as st
import requests, json, base64, os, re, time, io, zipfile, textwrap
from datetime import datetime

st.set_page_config(
    page_title="Content Factory — AQUALINE",
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
*, *::before, *::after { box-sizing: border-box; }
.stApp { background:#070b12; color:#cbd5e1; font-family:'IBM Plex Sans Thai',sans-serif; }
[data-testid="stSidebar"]{ background:#0d1117 !important; border-right:1px solid #1e293b !important; }

.factory-banner{
  background:linear-gradient(90deg,#0d1117 0%,#0f172a 40%,#0d1117 100%);
  border-bottom:1px solid #1e293b; padding:18px 32px;
  display:flex; align-items:center; gap:20px; margin-bottom:24px;
  position:relative; overflow:hidden;
}
.factory-banner::after{
  content:''; position:absolute; inset:0;
  background:repeating-linear-gradient(90deg,transparent,transparent 60px,rgba(56,189,248,.03) 60px,rgba(56,189,248,.03) 61px);
  pointer-events:none;
}
.banner-title{ font-family:'IBM Plex Mono',monospace; font-size:22px; font-weight:700; color:#f1f5f9; letter-spacing:-.5px; }
.banner-sub  { font-size:12px; color:#475569; margin-top:3px; font-family:'IBM Plex Mono',monospace; }

.badge{ font-family:'IBM Plex Mono',monospace; font-size:10px; font-weight:600; padding:4px 12px; border-radius:4px; letter-spacing:.5px; text-transform:uppercase; }
.badge-blue { background:rgba(56,189,248,.1);  color:#38bdf8; border:1px solid rgba(56,189,248,.25); }
.badge-green{ background:rgba(52,211,153,.1);  color:#34d399; border:1px solid rgba(52,211,153,.25); }
.badge-amber{ background:rgba(251,191,36,.1);  color:#fbbf24; border:1px solid rgba(251,191,36,.25); }
.badge-pink { background:rgba(236,72,153,.1);  color:#f472b6; border:1px solid rgba(236,72,153,.25); }
.badge-red  { background:rgba(248,113,113,.1); color:#f87171; border:1px solid rgba(248,113,113,.25); }

.sb{ background:rgba(15,23,42,.8); border:1px solid #1e293b; border-radius:12px; margin-bottom:14px; overflow:hidden; }
.sh{ background:rgba(0,0,0,.3); border-bottom:1px solid #1e293b; padding:11px 18px;
     display:flex; align-items:center; gap:10px;
     font-family:'IBM Plex Mono',monospace; font-size:11px; font-weight:600; color:#64748b; letter-spacing:1px; text-transform:uppercase; }
.sbody{ padding:14px 18px; }

.node-pill{ display:inline-flex; align-items:center; gap:5px; font-family:'IBM Plex Mono',monospace; font-size:10px; font-weight:600; padding:3px 10px; border-radius:4px; letter-spacing:.3px; }
.pill-idle   { background:#0f172a; color:#334155; border:1px solid #1e293b; }
.pill-running{ background:rgba(251,191,36,.1); color:#fbbf24; border:1px solid rgba(251,191,36,.3); }
.pill-done   { background:rgba(52,211,153,.1); color:#34d399; border:1px solid rgba(52,211,153,.3); }
.pill-skip   { background:rgba(99,102,241,.1); color:#818cf8; border:1px solid rgba(99,102,241,.3); }
.pill-error  { background:rgba(248,113,113,.1);color:#f87171; border:1px solid rgba(248,113,113,.3); }

.out-box{ background:rgba(0,0,0,.5); border:1px solid #1e293b; border-radius:8px; padding:14px; font-size:12px; color:#94a3b8; line-height:1.8; white-space:pre-wrap; max-height:260px; overflow-y:auto; }
.out-box-ok { border-color:rgba(52,211,153,.3); }
.out-box-err{ border-color:rgba(248,113,113,.3); color:#f87171; }

.log-terminal{ background:#020409; border:1px solid #0f172a; border-radius:8px; padding:12px; max-height:180px; overflow-y:auto; font-family:'IBM Plex Mono',monospace; font-size:11px; line-height:1.7; }
.lt-info{ color:#38bdf8; } .lt-ok{ color:#34d399; } .lt-warn{ color:#fbbf24; } .lt-err{ color:#f87171; } .lt-dim{ color:#334155; }

.pipe-row{ display:flex; align-items:center; gap:0; padding:10px 0; overflow-x:auto; scrollbar-width:none; }
.pipe-row::-webkit-scrollbar{ display:none; }
.pipe-step{ display:flex; flex-direction:column; align-items:center; gap:5px; min-width:80px; }
.pipe-icon{ width:40px; height:40px; border-radius:10px; border:1px solid #1e293b; background:rgba(15,23,42,.9); display:flex; align-items:center; justify-content:center; font-size:16px; transition:all .3s; }
.pipe-icon.active{ border-color:#38bdf8; box-shadow:0 0 12px rgba(56,189,248,.3); }
.pipe-icon.done  { border-color:#34d399; box-shadow:0 0 10px rgba(52,211,153,.2); background:rgba(52,211,153,.05); }
.pipe-icon.error { border-color:#f87171; }
.pipe-icon.skip  { opacity:.3; }
.pipe-label{ font-size:9px; color:#475569; font-family:'IBM Plex Mono',monospace; text-align:center; }
.pipe-arrow{ color:#1e293b; font-size:12px; padding:0 3px; margin-bottom:16px; flex-shrink:0; }

.export-card{ background:linear-gradient(135deg,rgba(15,23,42,.95),rgba(7,11,18,.95)); border:1px solid rgba(52,211,153,.25); border-radius:14px; padding:20px 24px; text-align:center; }
.export-title{ font-family:'IBM Plex Mono',monospace; font-size:16px; font-weight:700; color:#34d399; margin-bottom:6px; }
.export-sub{ font-size:12px; color:#475569; margin-bottom:14px; }

.storyboard-scene{ background:rgba(15,23,42,.9); border:1px solid #1e293b; border-radius:10px; padding:14px; margin-bottom:10px; }
.scene-num{ font-family:'IBM Plex Mono',monospace; font-size:10px; color:#38bdf8; font-weight:700; margin-bottom:6px; }
.scene-row{ display:flex; gap:10px; align-items:flex-start; font-size:12px; color:#94a3b8; margin-bottom:4px; }
.scene-label{ color:#475569; font-family:'IBM Plex Mono',monospace; font-size:10px; min-width:70px; }

.divider{ height:1px; background:#1e293b; margin:14px 0; }
.stButton>button{ font-family:'IBM Plex Mono',monospace !important; font-size:12px !important; font-weight:600 !important; letter-spacing:.3px !important; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════
DEFAULTS = {
    "cf_images_b64":      [],    # list of (filename, b64, mime)
    "cf_status":          {},
    "cf_outputs":         {},
    "cf_logs":            [],
    "cf_running":         False,
    "cf_saved_workflows": [],    # ← Save Workflow: list of saved workflow configs
    "cf_active_template": None, # ← Template: template ที่เลือกอยู่
    "cf_gen_images":      [],    # list of (prompt_label, bytes)
    "cf_strategy":        "",
    "cf_ad_copy":         "",    # ← ใหม่: Ad Copy สำเร็จรูป
    "cf_storyboard":      "",    # ← ใหม่: Storyboard
    "cf_video_script":    "",
    "cf_voice_script":    "",
    "cf_tts_audios":      [],
    "cf_caption":         "",
    "cf_email_line":      "",    # ← ใหม่: Email/LINE Broadcast
    "cf_hashtag_bank":    "",    # ← ใหม่: Hashtag Bank
    "cf_zip_name":        "aqualine_content_pack",
    "cf_include_tts":     True,
    "cf_include_video":   True,
    "cf_include_caption": True,
    "cf_include_storyboard": True,   # ← ใหม่
    "cf_include_adcopy":  True,      # ← ใหม่
    "cf_include_email":   True,      # ← ใหม่
    "cf_ab_test":         "",        # ← A/B Test Hook & CTA
    "cf_calendar":        "",        # ← Content Calendar 30 วัน
    "cf_review_script":   "",        # ← Review / UGC Script
    "cf_repurpose":       "",        # ← Repurpose Pack
    "cf_include_ab":      True,
    "cf_include_calendar":True,
    "cf_include_review":  True,
    "cf_include_repurpose":True,
    "cf_include_banner":  True,       # ← Banner Gen
    "cf_banners":         [],         # list of (label, bytes)
    "cf_banner_headline": "",
    "cf_banner_cta":      "สั่งซื้อเลย!",
    "cf_banner_bgcolor":  "#1a1a2e",
    "cf_banner_txtcolor": "#ffffff",
    "cf_banner_count":    3,
    "cf_vid_format":      "TikTok / Reels 30 วิ",
    "cf_tone":            "🔥 กระตุ้นซื้อ",
    "cf_img_style":       "Photorealistic · Product Studio",
    "cf_img_count":       3,
    "cf_language":        "ภาษาไทย",   # ← ใหม่: ภาษา output
    "cf_web_data":        "",           # ← ข้อมูลดิบจากเว็บที่ user วาง
    "cf_web_analysis":    "",           # ← ผลวิเคราะห์ข้อมูลเว็บ
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════
def log(msg, level="info"):
    st.session_state.cf_logs.append({"ts": datetime.now().strftime("%H:%M:%S"), "msg": msg, "level": level})

def set_status(node, status): st.session_state.cf_status[node] = status
def set_output(node, content): st.session_state.cf_outputs[node] = content

def pill_html(node_id):
    s = st.session_state.cf_status.get(node_id, "idle")
    icons  = {"idle":"●","running":"◎","done":"✓","error":"✗","skip":"○"}
    labels = {"idle":"IDLE","running":"RUNNING","done":"DONE","error":"ERROR","skip":"SKIP"}
    return f"<span class='node-pill pill-{s}'>{icons[s]} {labels[s]}</span>"

def pipe_cls(nid):
    return {"idle":"","running":"active","done":"done","error":"error","skip":"skip"}.get(
        st.session_state.cf_status.get(nid,"idle"), "")

@st.cache_data(ttl=300)
def best_model(api_key):
    try:
        r = requests.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}", timeout=8)
        if r.status_code == 200:
            avail = [m["name"] for m in r.json().get("models",[]) if "generateContent" in m.get("supportedGenerationMethods",[])]
            for p in ["models/gemini-2.5-flash-preview-05-20","models/gemini-2.5-flash","models/gemini-1.5-flash-latest","models/gemini-1.5-flash"]:
                if p in avail: return p
            return avail[0] if avail else "models/gemini-1.5-flash"
    except: pass
    return "models/gemini-1.5-flash"

def call_gemini(prompt, images_b64=None, max_tokens=8192):
    model = best_model(API_KEY)
    url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={API_KEY}"
    parts = [{"text": prompt}]
    if images_b64:
        for b64, mime in images_b64[:8]:
            parts.append({"inlineData": {"mimeType": mime, "data": b64}})
    
    try:
        r = requests.post(url, json={"contents": [{"parts": parts}], "generationConfig": {"temperature": 0.7, "maxOutputTokens": max_tokens}}, timeout=150)
        if r.status_code == 200:
            return r.json()["candidates"][0]["content"]["parts"][0].get("text", "")
        return f"❌ API Error {r.status_code}"
    except Exception as e:
        return f"❌ Connection Error"

@st.cache_data(ttl=600)
def list_imagen_models(api_key):
    """
    ดึง model ที่ account นี้รองรับจริงจาก ListModels API
    แยกเป็น 2 ประเภท:
      - imagen_predict : ใช้ :predict endpoint (Imagen 3/4)
      - gemini_image   : ใช้ :generateContent endpoint (Gemini image gen)
    """
    try:
        # ListModels มี pagination — ดึงทุก page
        all_models = []
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}&pageSize=100"
        while url:
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                break
            data = r.json()
            all_models.extend(data.get("models", []))
            next_token = data.get("nextPageToken", "")
            if next_token:
                url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}&pageSize=100&pageToken={next_token}"
            else:
                url = None

        imagen_predict = []
        gemini_image   = []
        for m in all_models:
            name    = m.get("name", "").replace("models/", "")
            methods = m.get("supportedGenerationMethods", [])
            if "imagen" in name.lower() and "predict" in methods:
                imagen_predict.append(name)
            # Gemini image-gen models (generateContent + มีคำว่า image/banana ใน name)
            if "generateContent" in methods and any(
                kw in name.lower() for kw in ["image", "banana"]
            ):
                gemini_image.append(name)

        return {"imagen": imagen_predict, "gemini_image": gemini_image}
    except Exception:
        return {"imagen": [], "gemini_image": []}


def gen_imagen(prompt):
    """
    Generate image via Google AI API.

    Priority:
      1. Imagen 4 Fast  (เร็ว ถูก)         → :predict
      2. Imagen 4       (quality ดี)         → :predict
      3. Imagen 4 Ultra (สูงสุด)             → :predict
      4. Gemini image models                  → :generateContent
    Fallback: PIL gradient placeholder (ไม่ error ไม่หยุด pipeline)
    """
    models_map = list_imagen_models(API_KEY)
    imagen_models  = models_map.get("imagen", [])
    gemini_images  = models_map.get("gemini_image", [])

    # ถ้า ListModels ดึงไม่ได้ ใช้ค่า hard-coded จาก account นี้
    if not imagen_models:
        imagen_models = [
            "imagen-4.0-fast-generate-001",
            "imagen-4.0-generate-001",
            "imagen-4.0-ultra-generate-001",
        ]

    # เรียง: fast → standard → ultra → อื่นๆ
    def sort_key(m):
        if "fast"  in m: return 0
        if "ultra" in m: return 2
        return 1
    imagen_models = sorted(imagen_models, key=sort_key)

    last_err = ""

    # ── ลอง Imagen (:predict) ──
    for mid in imagen_models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{mid}:predict?key={API_KEY}"
        payload = {
            "instances": [{"prompt": prompt}],
            "parameters": {
                "sampleCount": 1,
                "aspectRatio": "1:1",
                "safetyFilterLevel": "block_few",
                "personGeneration": "allow_adult",
            }
        }
        try:
            r = requests.post(url, json=payload, timeout=90)
            if r.status_code == 200:
                preds = r.json().get("predictions", [])
                if preds:
                    b64 = preds[0].get("bytesBase64Encoded", "")
                    if b64:
                        return base64.b64decode(b64), None
                last_err = f"{mid}: predictions empty"
            elif r.status_code == 429:
                time.sleep(15)
                r2 = requests.post(url, json=payload, timeout=90)
                if r2.status_code == 200:
                    preds = r2.json().get("predictions", [])
                    if preds:
                        b64 = preds[0].get("bytesBase64Encoded", "")
                        if b64:
                            return base64.b64decode(b64), None
                last_err = f"{mid}: rate limited 429"
                continue
            elif r.status_code == 404:
                last_err = f"{mid}: 404"
                continue
            else:
                try:
                    msg = r.json().get("error", {}).get("message", "")[:200]
                except Exception:
                    msg = r.text[:200]
                last_err = f"{mid} HTTP {r.status_code}: {msg}"
                # ถ้า 400/403 ไม่ลอง model ต่อไป (permission / billing issue)
                if r.status_code in (400, 403):
                    return None, last_err
                continue
        except requests.exceptions.Timeout:
            last_err = f"{mid}: timeout 90s"
            continue
        except Exception as e:
            last_err = str(e)[:120]
            continue

    # ── Fallback: Gemini image-gen models (:generateContent) ──
    # เรียง: gemini-2.5-flash-image ก่อน จากนั้น 3.1 flash image แล้ว pro image
    def gemini_sort(m):
        if "2.5" in m: return 0
        if "3.1" in m and "flash" in m: return 1
        if "3.1" in m: return 2
        if "3" in m and "flash" in m: return 3
        return 4

    gemini_images_sorted = sorted(gemini_images, key=gemini_sort)
    # เพิ่ม hard-coded fallback เผื่อ ListModels ไม่ครบ
    for hm in ["gemini-2.5-flash-image", "gemini-3.1-flash-image-preview", "gemini-3-pro-image-preview"]:
        if hm not in gemini_images_sorted:
            gemini_images_sorted.append(hm)

    for gmodel in gemini_images_sorted:
        try:
            gurl = f"https://generativelanguage.googleapis.com/v1beta/models/{gmodel}:generateContent?key={API_KEY}"
            gpayload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseModalities": ["IMAGE", "TEXT"]}
            }
            gr = requests.post(gurl, json=gpayload, timeout=90)
            if gr.status_code == 200:
                cands = gr.json().get("candidates", [])
                if cands:
                    for part in cands[0].get("content", {}).get("parts", []):
                        if "inlineData" in part:
                            b64 = part["inlineData"].get("data", "")
                            if b64:
                                return base64.b64decode(b64), None
            last_err = f"{gmodel}: HTTP {gr.status_code}"
        except Exception as e:
            last_err = f"{gmodel}: {str(e)[:80]}"
            continue

    return None, last_err

def tts_gtts(text, lang="th"):
    try:
        from gtts import gTTS
        buf = io.BytesIO()
        gTTS(text=text[:4000], lang=lang, slow=False).write_to_fp(buf)
        buf.seek(0)
        return buf.read()
    except Exception as e:
        log(f"TTS error: {e}", "warn")
        return None

def render_log_box(container, n=22):
    lines = st.session_state.cf_logs[-n:]
    html  = "".join(f"<div class='lt-{e['level']}'>[{e['ts']}] {e['msg']}</div>" for e in lines)
    container.markdown(f"<div class='log-terminal'>{html}</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# TOP BANNER
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<div class="factory-banner">
  <div style='font-size:32px'>🏭</div>
  <div>
    <div class="banner-title">CONTENT FACTORY  <span style='color:#334155;font-weight:400'>v3.0</span></div>
    <div class="banner-sub">โยนรูป + กรอกข้อมูล → AI สร้างทุกอย่าง → Download ZIP</div>
  </div>
  <div style='margin-left:auto;display:flex;gap:8px;flex-wrap:wrap;align-items:center'>
    <span class="badge badge-blue">GEMINI POWERED</span>
    <span class="badge badge-green">MULTI-IMAGE</span>
    <span class="badge badge-amber">TTS AUDIO</span>
    <span class="badge badge-pink">STORYBOARD</span>
    <span class="badge badge-red">A/B TEST</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# PIPELINE STATUS BAR
# ══════════════════════════════════════════════════════════════════
PIPELINE = [
    ("input","🖼️","Input"),
    ("strategy","🧠","Strategy"),
    ("genimg","🎨","Gen Image"),
    ("storyboard","🎞️","Storyboard"),
    ("vidscript","🎬","Video Script"),
    ("voicescript","🎤","Voice Script"),
    ("tts","🔊","TTS Audio"),
    ("adcopy","📣","Ad Copy"),
    ("caption","📝","Caption"),
    ("email","📧","Email/LINE"),
    ("hashtag","#️⃣","Hashtags"),
    ("abtest","🧪","A/B Test"),
    ("calendar","📅","Calendar"),
    ("review","⭐","Review"),
    ("repurpose","🔄","Repurpose"),
    ("banner","🖼️","Banner"),
    ("export","📦","ZIP"),
]
pipe_html = "<div class='pipe-row'>"
for i,(nid,icon,label) in enumerate(PIPELINE):
    c = pipe_cls(nid)
    pipe_html += f"<div class='pipe-step'><div class='pipe-icon {c}'>{icon}</div><div class='pipe-label'>{label}</div></div>"
    if i < len(PIPELINE)-1: pipe_html += "<div class='pipe-arrow'>›</div>"
pipe_html += "</div>"
st.markdown(f"<div class='sb'><div class='sh'>⚡ PIPELINE STATUS</div><div class='sbody' style='padding:8px 18px'>{pipe_html}</div></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# LAYOUT
# ══════════════════════════════════════════════════════════════════
col_left, col_right = st.columns([1, 1.45], gap="large")

# ══════════════════ LEFT PANEL ══════════════════
with col_left:

    # NODE 01 — IMAGE INPUT
    st.markdown(f"<div class='sb'><div class='sh'>🖼️ NODE 01 · IMAGE INPUT <span style='margin-left:auto'>{pill_html('input')}</span></div><div class='sbody'>", unsafe_allow_html=True)

    uploaded_files = st.file_uploader(
        "อัปโหลดรูปภาพสินค้า (ไม่จำกัดจำนวน — ยิ่งมากยิ่งดี)",
        type=["jpg","jpeg","png","webp"],
        accept_multiple_files=True,
        key="img_uploader", label_visibility="collapsed"
    )
    if uploaded_files:
        new_list = []
        for f in uploaded_files:
            raw  = f.read()
            new_list.append((f.name, base64.b64encode(raw).decode(), f.type or "image/jpeg"))
        st.session_state.cf_images_b64 = new_list
        set_status("input", "done")
        gcols = st.columns(min(len(uploaded_files), 4))
        for i, f in enumerate(uploaded_files[:8]):
            f.seek(0)
            with gcols[i % 4]: st.image(f.read(), use_container_width=True)
        if len(uploaded_files) > 8: st.caption(f"+ อีก {len(uploaded_files)-8} ไฟล์")
        st.success(f"✅ {len(uploaded_files)} ไฟล์พร้อม")
    elif st.session_state.cf_images_b64:
        st.info(f"📁 มีภาพอยู่แล้ว {len(st.session_state.cf_images_b64)} ไฟล์")

    st.markdown("</div></div>", unsafe_allow_html=True)

    # PRODUCT BRIEF
    st.markdown("<div class='sb'><div class='sh'>📋 PRODUCT BRIEF</div><div class='sbody'>", unsafe_allow_html=True)
    product_name = st.text_input("ชื่อสินค้า *", placeholder="เช่น รางน้ำ Prestige Series สแตนเลส 304", key="pname")
    product_desc = st.text_area("รายละเอียด / จุดเด่น *", height=90,
        placeholder="เช่น: สแตนเลส 304 กันสนิม · ดีไซน์ Minimalist · ติดตั้งง่าย 30 นาที · รับประกัน 10 ปี · รางวัล iF Design Award",
        key="pdesc")
    c1,c2 = st.columns(2)
    with c1: price  = st.text_input("ราคา", placeholder="฿3,990", key="pprice")
    with c2: promo  = st.text_input("โปรโมชัน", placeholder="ลด 20% + ฟรีติดตั้ง", key="ppromo")
    target  = st.text_input("กลุ่มเป้าหมาย", placeholder="เจ้าของบ้านรีโนเวท อายุ 30-45", key="ptarget")
    brand   = st.text_input("แบรนด์ / เว็บไซต์ (ถ้ามี)", placeholder="AQUALINE · aqualine.co.th", key="pbrand")

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    st.markdown("<div class='sh' style='border-radius:6px;margin-bottom:8px'>🌐 ข้อมูลเพิ่มเติมจากเว็บ (ไม่บังคับ)</div>", unsafe_allow_html=True)
    web_data = st.text_area(
        "วางข้อมูลดิบจากเว็บไซต์ / รีวิว / spec sheet / คู่แข่ง ได้เลย",
        height=110,
        placeholder="เช่น: วาง spec จากเว็บ, รีวิวจากลูกค้า, ข้อมูลคู่แข่ง, คำถามที่คนถามบ่อย, ราคาจาก Shopee...\nAI จะวิเคราะห์และนำไปเป็นไอเดียในการ Gen ภาพและเขียน Script ให้ตรงจุดยิ่งขึ้น",
        key="cf_web_data"
    )
    wa_col1, wa_col2 = st.columns([2, 1])
    with wa_col1:
        analyze_btn = st.button("🔍 วิเคราะห์ข้อมูลเว็บ → สรุปไอเดียภาพ", use_container_width=True, key="analyze_web")
    with wa_col2:
        if st.session_state.cf_web_analysis:
            if st.button("✕ ล้างผลวิเคราะห์", use_container_width=True, key="clear_analysis"):
                st.session_state.cf_web_analysis = ""
                st.rerun()

    if analyze_btn:
        if not web_data.strip():
            st.warning("⚠️ กรุณาวางข้อมูลจากเว็บก่อนครับ")
        else:
            with st.spinner("🔍 AI กำลังวิเคราะห์..."):
                pname_for_analysis = st.session_state.get("pname", "") or "สินค้า"
                analysis_result = call_gemini(f"""วิเคราะห์ข้อมูลต่อไปนี้ที่ copy มาจากเว็บ แล้วสรุปออกมาเป็นไอเดียสำหรับสร้าง content ขายสินค้า: {pname_for_analysis}

ข้อมูลดิบจากเว็บ:
\"\"\"
{web_data[:6000]}
\"\"\"

สรุปออกมาเป็น 5 หัวข้อนี้เท่านั้น:

🎯 จุดเด่นที่ขุดได้จากข้อมูล (bullet 5-8 ข้อ — เฉพาะที่ไม่ชัดเจนจากชื่อสินค้า):

🖼️ ไอเดีย Gen ภาพ (5 ไอเดีย — ระบุ: มุม, องค์ประกอบ, อารมณ์ภาพ):

🎬 Angle การขายที่ได้จากข้อมูลนี้ (3 angle — ต่างจากการขายทั่วไป):

💬 Pain point ลูกค้าที่พบในข้อมูล (bullet 3-5 ข้อ):

⚠️ ข้อควรระวัง / สิ่งที่ควรหลีกเลี่ยงในการโฆษณา (ถ้ามี):

ตอบกระชับ ตรงประเด็น ใช้งานได้จริง ภาษาไทย""")
                st.session_state.cf_web_analysis = analysis_result

    if st.session_state.cf_web_analysis:
        st.markdown(f'<div class="out-box out-box-ok" style="max-height:220px">{st.session_state.cf_web_analysis}</div>', unsafe_allow_html=True)
        st.caption("✅ AI วิเคราะห์แล้ว — ข้อมูลนี้จะถูกส่งไปช่วยทุก Node ใน pipeline อัตโนมัติ")

    st.markdown("</div></div>", unsafe_allow_html=True)

    # OUTPUT CONFIG
    st.markdown("<div class='sb'><div class='sh'>⚙️ OUTPUT CONFIG</div><div class='sbody'>", unsafe_allow_html=True)
    ca, cb = st.columns(2)
    with ca:
        img_style = st.selectbox("สไตล์ภาพ:", [
            "Photorealistic · Product Studio",
            "3D Render · CGI Premium",
            "Cinematic · Dark Dramatic",
            "Minimalist · Clean White BG",
            "Lifestyle · In-Context Shot",
            "Luxury · Gold & Dark",
        ], key="cf_img_style")
        img_count = st.slider("จำนวนภาพที่จะ Gen:", 1, 6, 3, key="cf_img_count")
    with cb:
        vid_format = st.selectbox("รูปแบบวิดีโอ:", [
            "TikTok / Reels 30 วิ",
            "TikTok / Reels 60 วิ",
            "YouTube Short 60 วิ",
            "Product Demo 2 นาที",
            "Flash Sale Ad 15 วิ",
        ], key="cf_vid_format")
        tone = st.selectbox("Tone:", [
            "🔥 กระตุ้นซื้อ",
            "💼 Professional",
            "😊 Friendly & Warm",
            "✨ Luxury / Premium",
            "🎯 Educational",
        ], key="cf_tone")

    output_lang = st.selectbox("ภาษา Output:", ["ภาษาไทย","English","ภาษาไทย + English"], key="cf_language")

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    st.markdown("**เปิด/ปิด Nodes:**")
    r1c1,r1c2,r1c3 = st.columns(3)
    r2c1,r2c2,r2c3 = st.columns(3)
    with r1c1: inc_video      = st.toggle("🎬 Video Script",  value=True,  key="cf_include_video")
    with r1c2: inc_storyboard = st.toggle("🎞️ Storyboard",   value=True,  key="cf_include_storyboard")
    with r1c3: inc_tts        = st.toggle("🔊 TTS Audio",     value=True,  key="cf_include_tts")
    with r2c1: inc_adcopy     = st.toggle("📣 Ad Copy",       value=True,  key="cf_include_adcopy")
    with r2c2: inc_caption    = st.toggle("📝 Caption",       value=True,  key="cf_include_caption")
    with r2c3: inc_email      = st.toggle("📧 Email/LINE",    value=True,  key="cf_include_email")
    r3c1,r3c2,r3c3,r3c4 = st.columns(4)
    with r3c1: inc_ab         = st.toggle("🧪 A/B Test",      value=True,  key="cf_include_ab")
    with r3c2: inc_calendar   = st.toggle("📅 Calendar",      value=True,  key="cf_include_calendar")
    with r3c3: inc_review     = st.toggle("⭐ Review Script", value=True,  key="cf_include_review")
    with r3c4: inc_repurpose  = st.toggle("🔄 Repurpose",     value=True,  key="cf_include_repurpose")
    r4c1, r4c2 = st.columns(2)
    with r4c1: inc_banner = st.toggle("🖼️ Banner โฆษณา",   value=True,  key="cf_include_banner")

    if st.session_state.get("cf_include_banner", True):
        st.markdown("<div class='sh' style='border-radius:6px;margin:8px 0 4px;font-size:10px'>🖼️ ตั้งค่าแบนเนอร์</div>", unsafe_allow_html=True)
        bn1, bn2 = st.columns(2)
        with bn1:
            st.text_input("Headline บนแบนเนอร์", placeholder="เช่น ซื้อ 1 แถม 1 วันนี้!", key="cf_banner_headline")
            st.color_picker("สีพื้นหลัง", value="#1a1a2e", key="cf_banner_bgcolor")
        with bn2:
            st.text_input("ข้อความ CTA", value="สั่งซื้อเลย!", key="cf_banner_cta")
            st.color_picker("สีข้อความ", value="#ffffff", key="cf_banner_txtcolor")
        st.slider("จำนวนแบนเนอร์ที่ gen", 1, 6, 3, key="cf_banner_count")

    zip_name = st.text_input("ชื่อโฟลเดอร์ ZIP:", value=st.session_state.cf_zip_name, key="cf_zip_name")

    # ══ SAVE WORKFLOW ══
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    st.markdown("<div class='sh' style='border-radius:6px;margin-bottom:10px'>💾 SAVE / LOAD WORKFLOW</div>", unsafe_allow_html=True)

    # ── Pre-built Templates ──
    TEMPLATES = {
        "🔥 Flash Sale Campaign": {
            "tone": "🔥 กระตุ้นซื้อ", "vid_format": "Flash Sale Ad 15 วิ",
            "img_style": "Photorealistic · Product Studio", "img_count": 3,
            "language": "ภาษาไทย",
            "toggles": {"video": True, "storyboard": True, "tts": True, "adcopy": True,
                        "caption": True, "email": True, "ab": True, "calendar": False,
                        "review": False, "repurpose": False, "banner": True},
        },
        "✨ Luxury Brand Launch": {
            "tone": "✨ Luxury / Premium", "vid_format": "Product Demo 2 นาที",
            "img_style": "Luxury · Gold & Dark", "img_count": 4,
            "language": "ภาษาไทย + English",
            "toggles": {"video": True, "storyboard": True, "tts": True, "adcopy": True,
                        "caption": True, "email": True, "ab": True, "calendar": True,
                        "review": True, "repurpose": True, "banner": True},
        },
        "🎯 TikTok Viral": {
            "tone": "🔥 กระตุ้นซื้อ", "vid_format": "TikTok / Reels 30 วิ",
            "img_style": "Lifestyle · In-Context Shot", "img_count": 3,
            "language": "ภาษาไทย",
            "toggles": {"video": True, "storyboard": True, "tts": True, "adcopy": True,
                        "caption": True, "email": False, "ab": True, "calendar": True,
                        "review": False, "repurpose": True, "banner": False},
        },
        "📧 Email Marketing": {
            "tone": "💼 Professional", "vid_format": "Product Demo 2 นาที",
            "img_style": "Minimalist · Clean White BG", "img_count": 2,
            "language": "ภาษาไทย",
            "toggles": {"video": False, "storyboard": False, "tts": False, "adcopy": True,
                        "caption": True, "email": True, "ab": True, "calendar": True,
                        "review": True, "repurpose": False, "banner": False},
        },
        "🛒 Shopee/Lazada Listing": {
            "tone": "😊 Friendly & Warm", "vid_format": "TikTok / Reels 30 วิ",
            "img_style": "Photorealistic · Product Studio", "img_count": 4,
            "language": "ภาษาไทย",
            "toggles": {"video": False, "storyboard": False, "tts": False, "adcopy": True,
                        "caption": True, "email": False, "ab": False, "calendar": False,
                        "review": True, "repurpose": True, "banner": True},
        },
    }

    tmpl_names = ["-- เลือก Template --"] + list(TEMPLATES.keys())
    sel_tmpl = st.selectbox("📋 Template สำเร็จรูป:", tmpl_names, key="tmpl_selector")
    if sel_tmpl and sel_tmpl != "-- เลือก Template --":
        if st.button(f"⚡ ใช้ Template: {sel_tmpl}", use_container_width=True, key="apply_tmpl"):
            t = TEMPLATES[sel_tmpl]
            st.session_state.cf_tone       = t["tone"]
            st.session_state.cf_vid_format = t["vid_format"]
            st.session_state.cf_img_style  = t["img_style"]
            st.session_state.cf_img_count  = t["img_count"]
            st.session_state.cf_language   = t["language"]
            tgl = t["toggles"]
            st.session_state.cf_include_video      = tgl["video"]
            st.session_state.cf_include_storyboard = tgl["storyboard"]
            st.session_state.cf_include_tts        = tgl["tts"]
            st.session_state.cf_include_adcopy     = tgl["adcopy"]
            st.session_state.cf_include_caption    = tgl["caption"]
            st.session_state.cf_include_email      = tgl["email"]
            st.session_state.cf_include_ab         = tgl["ab"]
            st.session_state.cf_include_calendar   = tgl["calendar"]
            st.session_state.cf_include_review     = tgl["review"]
            st.session_state.cf_include_repurpose  = tgl["repurpose"]
            st.session_state.cf_include_banner     = tgl["banner"]
            st.session_state.cf_active_template    = sel_tmpl
            st.success(f"✅ โหลด Template '{sel_tmpl}' แล้ว — ตั้งค่าทุกอย่างพร้อม!")
            st.rerun()

    st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)

    # ── Save current workflow ──
    wf_save_col, wf_name_col = st.columns([2, 3])
    with wf_name_col:
        wf_name_input = st.text_input("ชื่อ Workflow:", placeholder="เช่น Campaign Q3 2025",
                                       key="wf_name_input", label_visibility="collapsed")
    with wf_save_col:
        if st.button("💾 Save Workflow นี้", use_container_width=True, key="save_wf_btn"):
            if wf_name_input.strip():
                saved_wf = {
                    "name":        wf_name_input.strip(),
                    "saved_at":    datetime.now().strftime("%d/%m %H:%M"),
                    "tone":        st.session_state.cf_tone,
                    "vid_format":  st.session_state.cf_vid_format,
                    "img_style":   st.session_state.cf_img_style,
                    "img_count":   st.session_state.cf_img_count,
                    "language":    st.session_state.cf_language,
                    "zip_name":    st.session_state.cf_zip_name,
                    "banner_headline": st.session_state.get("cf_banner_headline",""),
                    "banner_cta":      st.session_state.get("cf_banner_cta","สั่งซื้อเลย!"),
                    "banner_bgcolor":  st.session_state.get("cf_banner_bgcolor","#1a1a2e"),
                    "banner_txtcolor": st.session_state.get("cf_banner_txtcolor","#ffffff"),
                    "banner_count":    st.session_state.get("cf_banner_count",3),
                    "toggles": {
                        "video":      st.session_state.cf_include_video,
                        "storyboard": st.session_state.cf_include_storyboard,
                        "tts":        st.session_state.cf_include_tts,
                        "adcopy":     st.session_state.cf_include_adcopy,
                        "caption":    st.session_state.cf_include_caption,
                        "email":      st.session_state.cf_include_email,
                        "ab":         st.session_state.cf_include_ab,
                        "calendar":   st.session_state.cf_include_calendar,
                        "review":     st.session_state.cf_include_review,
                        "repurpose":  st.session_state.cf_include_repurpose,
                        "banner":     st.session_state.get("cf_include_banner", True),
                    }
                }
                # อัพเดทถ้าชื่อซ้ำ
                existing = [i for i, w in enumerate(st.session_state.cf_saved_workflows)
                            if w["name"] == saved_wf["name"]]
                if existing:
                    st.session_state.cf_saved_workflows[existing[0]] = saved_wf
                    st.success(f"✅ อัพเดท Workflow '{saved_wf['name']}' แล้ว")
                else:
                    st.session_state.cf_saved_workflows.append(saved_wf)
                    st.success(f"✅ บันทึก Workflow '{saved_wf['name']}' แล้ว")
                st.rerun()
            else:
                st.warning("⚠️ กรุณาใส่ชื่อ Workflow ก่อนครับ")

    # ── Saved Workflows List ──
    if st.session_state.cf_saved_workflows:
        st.markdown("<div style='font-size:10px;color:#475569;font-family:IBM Plex Mono,monospace;margin:6px 0 4px'>📂 Workflows ที่บันทึกไว้:</div>", unsafe_allow_html=True)
        for wi, wf in enumerate(st.session_state.cf_saved_workflows):
            wf_col1, wf_col2, wf_col3 = st.columns([4, 2, 1])
            with wf_col1:
                st.markdown(f"<div style='font-size:11px;color:#94a3b8;font-family:IBM Plex Mono,monospace;padding:4px 0'>"
                            f"📁 <b style='color:#e2e8f0'>{wf['name']}</b> "
                            f"<span style='color:#334155'>· {wf['saved_at']}</span></div>",
                            unsafe_allow_html=True)
            with wf_col2:
                if st.button("📂 Load", key=f"load_wf_{wi}", use_container_width=True):
                    st.session_state.cf_tone        = wf.get("tone", st.session_state.cf_tone)
                    st.session_state.cf_vid_format  = wf.get("vid_format", st.session_state.cf_vid_format)
                    st.session_state.cf_img_style   = wf.get("img_style", st.session_state.cf_img_style)
                    st.session_state.cf_img_count   = wf.get("img_count", st.session_state.cf_img_count)
                    st.session_state.cf_language    = wf.get("language", st.session_state.cf_language)
                    st.session_state.cf_zip_name    = wf.get("zip_name", st.session_state.cf_zip_name)
                    st.session_state.cf_banner_headline = wf.get("banner_headline", "")
                    st.session_state.cf_banner_cta      = wf.get("banner_cta", "สั่งซื้อเลย!")
                    st.session_state.cf_banner_bgcolor   = wf.get("banner_bgcolor", "#1a1a2e")
                    st.session_state.cf_banner_txtcolor  = wf.get("banner_txtcolor", "#ffffff")
                    st.session_state.cf_banner_count     = wf.get("banner_count", 3)
                    tgl = wf.get("toggles", {})
                    st.session_state.cf_include_video      = tgl.get("video", True)
                    st.session_state.cf_include_storyboard = tgl.get("storyboard", True)
                    st.session_state.cf_include_tts        = tgl.get("tts", True)
                    st.session_state.cf_include_adcopy     = tgl.get("adcopy", True)
                    st.session_state.cf_include_caption    = tgl.get("caption", True)
                    st.session_state.cf_include_email      = tgl.get("email", True)
                    st.session_state.cf_include_ab         = tgl.get("ab", True)
                    st.session_state.cf_include_calendar   = tgl.get("calendar", True)
                    st.session_state.cf_include_review     = tgl.get("review", True)
                    st.session_state.cf_include_repurpose  = tgl.get("repurpose", True)
                    st.session_state.cf_include_banner     = tgl.get("banner", True)
                    st.success(f"✅ โหลด Workflow '{wf['name']}' แล้ว!")
                    st.rerun()
            with wf_col3:
                if st.button("🗑️", key=f"del_wf_{wi}", help="ลบ Workflow นี้"):
                    st.session_state.cf_saved_workflows.pop(wi)
                    st.rerun()

    st.markdown("</div></div>", unsafe_allow_html=True)

    # RUN / RESET
    rc1, rc2 = st.columns([3,1])
    with rc1:
        run_btn = st.button("🏭  RUN CONTENT FACTORY", type="primary",
                             use_container_width=True, disabled=st.session_state.cf_running, key="run_factory")
    with rc2:
        if st.button("↺ Reset", use_container_width=True, key="reset_factory"):
            for k in ["cf_status","cf_outputs","cf_logs","cf_gen_images","cf_strategy",
                      "cf_ad_copy","cf_storyboard","cf_video_script","cf_voice_script",
                      "cf_tts_audios","cf_caption","cf_email_line","cf_hashtag_bank",
                      "cf_ab_test","cf_calendar","cf_review_script","cf_repurpose"]:
                st.session_state[k] = DEFAULTS[k]
            st.session_state.cf_running = False
            st.rerun()

# ══════════════════ RIGHT PANEL ══════════════════
with col_right:

    log_container = st.empty()
    render_log_box(log_container)

    # ── LIVE PREVIEW PANEL (แสดงเมื่อยังไม่มี output) ──
    has_any_output = any([
        st.session_state.cf_gen_images,
        st.session_state.cf_strategy,
        st.session_state.cf_storyboard,
        st.session_state.cf_video_script,
        st.session_state.cf_ad_copy,
        st.session_state.cf_caption,
    ])

    if not has_any_output and not st.session_state.cf_running:

        # ── UPLOADED IMAGE PREVIEW ──
        if st.session_state.cf_images_b64:
            st.markdown(f"<div class='sb'><div class='sh'>🖼️ PREVIEW · ภาพที่อัปโหลด ({len(st.session_state.cf_images_b64)} ไฟล์)</div><div class='sbody'>", unsafe_allow_html=True)
            preview_imgs = st.session_state.cf_images_b64[:6]
            cols_prev = st.columns(min(len(preview_imgs), 3))
            for idx, (fname, b64, mime) in enumerate(preview_imgs):
                with cols_prev[idx % 3]:
                    img_bytes = base64.b64decode(b64)
                    st.image(img_bytes, caption=fname[:18], use_container_width=True)
            if len(st.session_state.cf_images_b64) > 6:
                st.caption(f"+ อีก {len(st.session_state.cf_images_b64)-6} ไฟล์")
            st.markdown("</div></div>", unsafe_allow_html=True)
        else:
            st.markdown("""
<div class='sb'>
  <div class='sh'>🖼️ PREVIEW · ภาพสินค้า</div>
  <div class='sbody' style='text-align:center;padding:40px 18px'>
    <div style='font-size:48px;margin-bottom:12px'>📷</div>
    <div style='font-family:"IBM Plex Mono",monospace;font-size:12px;color:#334155'>ยังไม่มีภาพ — อัปโหลดจากฝั่งซ้ายก่อนครับ</div>
  </div>
</div>
""", unsafe_allow_html=True)

        # ── PRODUCT BRIEF SUMMARY ──
        pname_live = st.session_state.get("pname", "")
        pdesc_live = st.session_state.get("pdesc", "")
        pprice_live = st.session_state.get("pprice", "")
        ptarget_live = st.session_state.get("ptarget", "")
        pbrand_live = st.session_state.get("pbrand", "")
        ppromo_live = st.session_state.get("ppromo", "")

        if pname_live or pdesc_live:
            rows_html = ""
            if pname_live:   rows_html += f"<div class='scene-row'><span class='scene-label'>สินค้า</span><span>{pname_live}</span></div>"
            if pdesc_live:   rows_html += f"<div class='scene-row'><span class='scene-label'>จุดเด่น</span><span>{pdesc_live[:120]}{'...' if len(pdesc_live)>120 else ''}</span></div>"
            if pprice_live:  rows_html += f"<div class='scene-row'><span class='scene-label'>ราคา</span><span>{pprice_live}</span></div>"
            if ppromo_live:  rows_html += f"<div class='scene-row'><span class='scene-label'>โปรโมชัน</span><span>{ppromo_live}</span></div>"
            if ptarget_live: rows_html += f"<div class='scene-row'><span class='scene-label'>กลุ่มเป้าหมาย</span><span>{ptarget_live}</span></div>"
            if pbrand_live:  rows_html += f"<div class='scene-row'><span class='scene-label'>แบรนด์</span><span>{pbrand_live}</span></div>"
            st.markdown(f"<div class='sb'><div class='sh'>📋 BRIEF SUMMARY</div><div class='sbody'>{rows_html}</div></div>", unsafe_allow_html=True)

        # ── PIPELINE PLANNER ──
        inc_v   = st.session_state.get("cf_include_video", True)
        inc_s   = st.session_state.get("cf_include_storyboard", True)
        inc_t   = st.session_state.get("cf_include_tts", True)
        inc_a   = st.session_state.get("cf_include_adcopy", True)
        inc_c   = st.session_state.get("cf_include_caption", True)
        inc_e   = st.session_state.get("cf_include_email", True)
        inc_ab2 = st.session_state.get("cf_include_ab", True)
        inc_cal = st.session_state.get("cf_include_calendar", True)
        inc_rv  = st.session_state.get("cf_include_review", True)
        inc_rp  = st.session_state.get("cf_include_repurpose", True)
        ic      = st.session_state.get("cf_img_count", 3)

        plan_nodes = [
            ("🧠", "Marketing Strategy", True, "เสมอ"),
            ("🎨", f"Gen Images ({ic} ภาพ)", True, "Imagen API"),
            ("🎞️", "Storyboard", inc_s, ""),
            ("🎬", "Video Script", inc_v, ""),
            ("🎤", "Voice Script", inc_v, ""),
            ("🔊", "TTS Audio", inc_t, "gTTS"),
            ("📣", "Ad Copy", inc_a, ""),
            ("📝", "Caption + Hashtag", inc_c, ""),
            ("📧", "Email / LINE", inc_e, ""),
            ("#️⃣", "Hashtag Bank", True, ""),
            ("🧪", "A/B Test", inc_ab2, ""),
            ("📅", "Calendar 30 วัน", inc_cal, ""),
            ("⭐", "Review Script", inc_rv, ""),
            ("🔄", "Repurpose Pack", inc_rp, ""),
        ]
        active_nodes = [n for n in plan_nodes if n[2]]
        rows = ""
        for icon, label, active, note in plan_nodes:
            if active:
                badge = f"<span style='margin-left:auto;font-size:9px;color:#34d399;font-family:IBM Plex Mono,monospace'>{'· '+note if note else '✓'}</span>"
                rows += f"<div style='display:flex;align-items:center;gap:8px;padding:5px 0;border-bottom:1px solid #0f172a'><span>{icon}</span><span style='font-size:12px;color:#94a3b8'>{label}</span>{badge}</div>"
            else:
                rows += f"<div style='display:flex;align-items:center;gap:8px;padding:5px 0;border-bottom:1px solid #0f172a;opacity:.3'><span>{icon}</span><span style='font-size:12px;color:#475569;text-decoration:line-through'>{label}</span><span style='margin-left:auto;font-size:9px;color:#334155;font-family:IBM Plex Mono,monospace'>ปิดอยู่</span></div>"

        n_active = len(active_nodes)
        est_min  = max(2, n_active * 2)
        st.markdown(f"""
<div class='sb'>
  <div class='sh'>🗺️ PIPELINE PLANNER · {n_active} nodes · ~{est_min} นาที</div>
  <div class='sbody' style='padding:10px 18px'>{rows}
    <div style='margin-top:12px;background:rgba(56,189,248,.05);border:1px solid rgba(56,189,248,.15);border-radius:8px;padding:10px;font-family:IBM Plex Mono,monospace;font-size:10px;color:#38bdf8;text-align:center'>
      📦 OUTPUT: {n_active + 1} ไฟล์ + {ic} ภาพ + ZIP พร้อม Download
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

        # ── TIPS ──
        st.markdown("""
<div class='sb'>
  <div class='sh'>💡 TIPS</div>
  <div class='sbody' style='font-size:11px;color:#475569;line-height:1.9'>
    <div>🖼️ <b style='color:#64748b'>ยิ่งใส่ภาพมาก ยิ่งได้ผลลัพธ์ดี</b> — ใส่ 3-8 ภาพ มุมต่างกัน</div>
    <div>🌐 <b style='color:#64748b'>วาง spec จากเว็บ</b> ใน "ข้อมูลจากเว็บ" แล้วกด วิเคราะห์ ก่อน Run</div>
    <div>🎛️ <b style='color:#64748b'>ปิด node ที่ไม่ใช้</b> เพื่อให้ pipeline เร็วขึ้น</div>
    <div>📝 <b style='color:#64748b'>แก้ไขผลลัพธ์ได้</b> — ทุก text area แก้ได้ก่อน export ZIP</div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── OUTPUT TABS (แสดงเมื่อมีผลลัพธ์อย่างน้อย 1 อย่าง) ──
    if has_any_output:
        tab_imgs, tab_scripts, tab_social, tab_advanced, tab_banner = st.tabs([
            "🎨 ภาพ & กลยุทธ์",
            "🎬 Scripts & Audio",
            "📱 Social & Copy",
            "📊 Advanced",
            "🖼️ Banner โฆษณา"
        ])

        with tab_imgs:
            # GEN IMAGES
            if st.session_state.cf_gen_images:
                st.markdown(f"<div class='sb'><div class='sh'>🎨 GENERATED IMAGES ({len(st.session_state.cf_gen_images)} ภาพ) <span style='margin-left:auto'>{pill_html('genimg')}</span></div><div class='sbody'>", unsafe_allow_html=True)
                gcols = st.columns(min(len(st.session_state.cf_gen_images), 3))
                for idx, (plabel, img_bytes) in enumerate(st.session_state.cf_gen_images):
                    with gcols[idx % 3]:
                        st.image(img_bytes, caption=plabel[:30], use_container_width=True)
                        st.download_button(f"⬇️ ภาพ {idx+1}", data=img_bytes,
                            file_name=f"gen_{idx+1:02d}.png", mime="image/png",
                            use_container_width=True, key=f"dl_img_{idx}")
                st.markdown("</div></div>", unsafe_allow_html=True)
            # STRATEGY
            if st.session_state.cf_strategy:
                st.markdown(f"<div class='sb'><div class='sh'>🧠 MARKETING STRATEGY <span style='margin-left:auto'>{pill_html('strategy')}</span></div><div class='sbody'>", unsafe_allow_html=True)
                st.markdown(f'<div class="out-box out-box-ok">{st.session_state.cf_strategy}</div>', unsafe_allow_html=True)
                st.download_button("⬇️ Export Strategy", data=st.session_state.cf_strategy,
                    file_name="marketing_strategy.txt", mime="text/plain", use_container_width=True, key="dl_strategy")
                st.markdown("</div></div>", unsafe_allow_html=True)
            # STORYBOARD
            if st.session_state.cf_storyboard:
                st.markdown(f"<div class='sb'><div class='sh'>🎞️ STORYBOARD <span style='margin-left:auto'>{pill_html('storyboard')}</span></div><div class='sbody'>", unsafe_allow_html=True)
                edited_sb = st.text_area("", value=st.session_state.cf_storyboard, height=200,
                                          key="edit_storyboard", label_visibility="collapsed")
                st.session_state.cf_storyboard = edited_sb
                st.download_button("⬇️ Export Storyboard", data=edited_sb,
                    file_name="storyboard.txt", mime="text/plain", use_container_width=True, key="dl_sb")
                st.markdown("</div></div>", unsafe_allow_html=True)

        with tab_scripts:
            # VIDEO SCRIPT
            if st.session_state.cf_video_script:
                st.markdown(f"<div class='sb'><div class='sh'>🎬 VIDEO SCRIPT <span style='margin-left:auto'>{pill_html('vidscript')}</span></div><div class='sbody'>", unsafe_allow_html=True)
                edited_vid = st.text_area("", value=st.session_state.cf_video_script, height=220,
                                           key="edit_vidscript", label_visibility="collapsed")
                st.session_state.cf_video_script = edited_vid
                st.download_button("⬇️ Export Video Script", data=edited_vid,
                    file_name="video_script.txt", mime="text/plain", use_container_width=True, key="dl_vid")
                st.markdown("</div></div>", unsafe_allow_html=True)
            # VOICE SCRIPT
            if st.session_state.cf_voice_script:
                st.markdown(f"<div class='sb'><div class='sh'>🎤 VOICE SCRIPT <span style='margin-left:auto'>{pill_html('voicescript')}</span></div><div class='sbody'>", unsafe_allow_html=True)
                edited_voice = st.text_area("", value=st.session_state.cf_voice_script, height=200,
                                             key="edit_voice", label_visibility="collapsed")
                st.session_state.cf_voice_script = edited_voice
                st.download_button("⬇️ Export Voice Script", data=edited_voice,
                    file_name="voice_script.txt", mime="text/plain", use_container_width=True, key="dl_voice")
                st.markdown("</div></div>", unsafe_allow_html=True)
            # TTS AUDIO
            if st.session_state.cf_tts_audios:
                st.markdown(f"<div class='sb'><div class='sh'>🔊 TTS AUDIO ({len(st.session_state.cf_tts_audios)} ไฟล์) <span style='margin-left:auto'>{pill_html('tts')}</span></div><div class='sbody'>", unsafe_allow_html=True)
                for label, audio_bytes in st.session_state.cf_tts_audios:
                    st.markdown(f"**{label}**")
                    st.audio(audio_bytes, format="audio/mp3")
                    st.download_button(f"⬇️ {label}.mp3", data=audio_bytes,
                        file_name=f"{label.replace(' ','_')}.mp3", mime="audio/mp3",
                        use_container_width=True, key=f"dl_tts_{label}")
                st.markdown("</div></div>", unsafe_allow_html=True)

        with tab_social:
            # AD COPY
            if st.session_state.cf_ad_copy:
                st.markdown(f"<div class='sb'><div class='sh'>📣 AD COPY <span style='margin-left:auto'>{pill_html('adcopy')}</span></div><div class='sbody'>", unsafe_allow_html=True)
                edited_ad = st.text_area("", value=st.session_state.cf_ad_copy, height=200,
                                          key="edit_adcopy", label_visibility="collapsed")
                st.session_state.cf_ad_copy = edited_ad
                st.download_button("⬇️ Export Ad Copy", data=edited_ad,
                    file_name="ad_copy.txt", mime="text/plain", use_container_width=True, key="dl_ad")
                st.markdown("</div></div>", unsafe_allow_html=True)
            # CAPTION
            if st.session_state.cf_caption:
                st.markdown(f"<div class='sb'><div class='sh'>📝 CAPTION + HASHTAG <span style='margin-left:auto'>{pill_html('caption')}</span></div><div class='sbody'>", unsafe_allow_html=True)
                edited_cap = st.text_area("", value=st.session_state.cf_caption, height=180,
                                           key="edit_caption", label_visibility="collapsed")
                st.session_state.cf_caption = edited_cap
                st.download_button("⬇️ Export Caption", data=edited_cap,
                    file_name="caption.txt", mime="text/plain", use_container_width=True, key="dl_cap")
                st.markdown("</div></div>", unsafe_allow_html=True)
            # EMAIL / LINE
            if st.session_state.cf_email_line:
                st.markdown(f"<div class='sb'><div class='sh'>📧 EMAIL / LINE BROADCAST <span style='margin-left:auto'>{pill_html('email')}</span></div><div class='sbody'>", unsafe_allow_html=True)
                edited_email = st.text_area("", value=st.session_state.cf_email_line, height=180,
                                             key="edit_email", label_visibility="collapsed")
                st.session_state.cf_email_line = edited_email
                st.download_button("⬇️ Export Email/LINE", data=edited_email,
                    file_name="email_line_broadcast.txt", mime="text/plain", use_container_width=True, key="dl_email")
                st.markdown("</div></div>", unsafe_allow_html=True)
            # HASHTAG BANK
            if st.session_state.cf_hashtag_bank:
                st.markdown(f"<div class='sb'><div class='sh'>#️⃣ HASHTAG BANK <span style='margin-left:auto'>{pill_html('hashtag')}</span></div><div class='sbody'>", unsafe_allow_html=True)
                st.markdown(f'<div class="out-box out-box-ok">{st.session_state.cf_hashtag_bank}</div>', unsafe_allow_html=True)
                st.download_button("⬇️ Export Hashtag Bank", data=st.session_state.cf_hashtag_bank,
                    file_name="hashtag_bank.txt", mime="text/plain", use_container_width=True, key="dl_hash")
                st.markdown("</div></div>", unsafe_allow_html=True)

        with tab_advanced:
            # A/B TEST
            if st.session_state.cf_ab_test:
                st.markdown(f"<div class='sb'><div class='sh'>🧪 A/B TEST COPY <span style='margin-left:auto'>{pill_html('abtest')}</span></div><div class='sbody'>", unsafe_allow_html=True)
                edited_ab = st.text_area("", value=st.session_state.cf_ab_test, height=220,
                                          key="edit_abtest", label_visibility="collapsed")
                st.session_state.cf_ab_test = edited_ab
                st.download_button("⬇️ Export A/B Test", data=edited_ab,
                    file_name="ab_test.txt", mime="text/plain", use_container_width=True, key="dl_ab")
                st.markdown("</div></div>", unsafe_allow_html=True)
            # CONTENT CALENDAR
            if st.session_state.cf_calendar:
                st.markdown(f"<div class='sb'><div class='sh'>📅 CONTENT CALENDAR 30 วัน <span style='margin-left:auto'>{pill_html('calendar')}</span></div><div class='sbody'>", unsafe_allow_html=True)
                edited_cal = st.text_area("", value=st.session_state.cf_calendar, height=240,
                                           key="edit_calendar", label_visibility="collapsed")
                st.session_state.cf_calendar = edited_cal
                st.download_button("⬇️ Export Calendar", data=edited_cal,
                    file_name="content_calendar_30d.txt", mime="text/plain", use_container_width=True, key="dl_cal")
                st.markdown("</div></div>", unsafe_allow_html=True)
            # REVIEW SCRIPT
            if st.session_state.cf_review_script:
                st.markdown(f"<div class='sb'><div class='sh'>⭐ REVIEW / UGC SCRIPT <span style='margin-left:auto'>{pill_html('review')}</span></div><div class='sbody'>", unsafe_allow_html=True)
                edited_rv = st.text_area("", value=st.session_state.cf_review_script, height=200,
                                          key="edit_review", label_visibility="collapsed")
                st.session_state.cf_review_script = edited_rv
                st.download_button("⬇️ Export Review Script", data=edited_rv,
                    file_name="review_ugc_script.txt", mime="text/plain", use_container_width=True, key="dl_rv")
                st.markdown("</div></div>", unsafe_allow_html=True)
            # REPURPOSE PACK
            if st.session_state.cf_repurpose:
                st.markdown(f"<div class='sb'><div class='sh'>🔄 REPURPOSE PACK <span style='margin-left:auto'>{pill_html('repurpose')}</span></div><div class='sbody'>", unsafe_allow_html=True)
                edited_rp = st.text_area("", value=st.session_state.cf_repurpose, height=200,
                                          key="edit_repurpose", label_visibility="collapsed")
                st.session_state.cf_repurpose = edited_rp
                st.download_button("⬇️ Export Repurpose Pack", data=edited_rp,
                    file_name="repurpose_pack.txt", mime="text/plain", use_container_width=True, key="dl_rp")
                st.markdown("</div></div>", unsafe_allow_html=True)

        with tab_banner:
            if st.session_state.cf_banners:
                st.markdown(
                    f"<div class='sb'><div class='sh'>🖼️ BANNER โฆษณา"
                    f" · {len(st.session_state.cf_banners)} ชิ้น"
                    f" <span style='margin-left:auto'>{pill_html('banner')}</span>"
                    f"</div><div class='sbody'>",
                    unsafe_allow_html=True
                )
                st.caption("ภาพแบนเนอร์พร้อม Headline + CTA — download แล้วยิงแอดได้เลย")
                gcols = st.columns(min(len(st.session_state.cf_banners), 3))
                for idx, (blabel, bimg) in enumerate(st.session_state.cf_banners):
                    with gcols[idx % 3]:
                        st.image(bimg, caption=blabel.replace("_", " "), use_container_width=True)
                        st.download_button(
                            f"⬇️ {blabel[:18]}.png", data=bimg,
                            file_name=f"banner_{idx+1:02d}_{blabel}.png",
                            mime="image/png", use_container_width=True,
                            key=f"dl_banner_{idx}"
                        )
                st.markdown("</div></div>", unsafe_allow_html=True)
            else:
                st.info("🖼️ Banner จะปรากฏที่นี่หลัง Run — เปิด Toggle 'Banner โฆษณา' ก่อนกด Run")
    if st.session_state.cf_outputs.get("export") == "ready":
        folder   = (st.session_state.cf_zip_name or "aqualine_content_pack").strip()
        ts_str   = datetime.now().strftime("%Y%m%d_%H%M%S")

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for idx, (plabel, img_bytes) in enumerate(st.session_state.cf_gen_images):
                zf.writestr(f"{folder}/images/gen_{idx+1:02d}_{plabel[:20].replace(' ','_')}.png", img_bytes)
            for idx, (blabel, bimg) in enumerate(st.session_state.cf_banners):
                zf.writestr(f"{folder}/banners/banner_{idx+1:02d}_{blabel}.png", bimg)
            for label, audio_bytes in st.session_state.cf_tts_audios:
                zf.writestr(f"{folder}/audio/{label.replace(' ','_')}.mp3", audio_bytes)
            texts = [
                ("marketing_strategy.txt",    st.session_state.cf_strategy),
                ("storyboard.txt",            st.session_state.cf_storyboard),
                ("video_script.txt",          st.session_state.cf_video_script),
                ("voice_script.txt",          st.session_state.cf_voice_script),
                ("ad_copy.txt",               st.session_state.cf_ad_copy),
                ("caption.txt",               st.session_state.cf_caption),
                ("email_line_broadcast.txt",  st.session_state.cf_email_line),
                ("hashtag_bank.txt",          st.session_state.cf_hashtag_bank),
                ("ab_test.txt",               st.session_state.cf_ab_test),
                ("content_calendar_30d.txt",  st.session_state.cf_calendar),
                ("review_ugc_script.txt",     st.session_state.cf_review_script),
                ("repurpose_pack.txt",        st.session_state.cf_repurpose),
            ]
            for fname, content in texts:
                if content:
                    zf.writestr(f"{folder}/{fname}", content.encode("utf-8"))
            readme = f"""AQUALINE CONTENT FACTORY — CONTENT PACK
สินค้า : {product_name or '-'}
แบรนด์ : {brand or '-'}
สร้างเมื่อ : {datetime.now().strftime('%d/%m/%Y %H:%M')}
{'='*50}

โฟลเดอร์นี้ประกอบด้วย:
  images/                  ภาพที่ Gen แล้ว ({len(st.session_state.cf_gen_images)} ไฟล์)
  banners/                 แบนเนอร์โฆษณา ({len(st.session_state.cf_banners)} ชิ้น · Facebook/TikTok/Shopee/IG/LINE)
  audio/                   ไฟล์เสียง TTS ({len(st.session_state.cf_tts_audios)} ไฟล์)
  marketing_strategy.txt   กลยุทธ์การตลาด + Persona + Key Messages
  storyboard.txt           Storyboard scene-by-scene
  video_script.txt         Video Script ครบทุก scene
  voice_script.txt         Voice Script สำหรับพากย์
  ad_copy.txt              Ad Copy สำเร็จรูป (Facebook/TikTok/Google)
  caption.txt              Caption + Hashtag ทุกแพลตฟอร์ม
  email_line_broadcast.txt Email + LINE Broadcast ลูกค้าเก่า
  hashtag_bank.txt         Hashtag Bank 50+ อัน แยกหมวด
  ab_test.txt              A/B Test Hook & CTA 2 versions
  content_calendar_30d.txt แผนโพสต์รายวัน 30 วัน
  review_ugc_script.txt    สคริปต์รีวิว / UGC สำหรับลูกค้า
  repurpose_pack.txt       แปลง content ข้ามแพลตฟอร์มทุกช่อง
"""
            zf.writestr(f"{folder}/README.txt", readme.encode("utf-8"))

        buf.seek(0)
        zip_bytes = buf.read()
        n_img  = len(st.session_state.cf_gen_images)
        n_aud  = len(st.session_state.cf_tts_audios)
        n_txt  = sum(1 for _, c in texts if c)

        st.markdown(f"""
<div class="export-card">
  <div class="export-title">📦 CONTENT PACK READY</div>
  <div class="export-sub">{n_img} ภาพ · {len(st.session_state.cf_banners)} banner · {n_aud} ไฟล์เสียง · {n_txt} documents · พร้อม README</div>
</div>
""", unsafe_allow_html=True)
        st.download_button(
            f"📦  DOWNLOAD  {folder}.zip",
            data=zip_bytes,
            file_name=f"{folder}_{ts_str}.zip",
            mime="application/zip",
            use_container_width=True,
            type="primary", key="dl_zip"
        )

# ══════════════════════════════════════════════════════════════════
# WORKFLOW ENGINE
# ══════════════════════════════════════════════════════════════════
if run_btn:
    if not st.session_state.cf_images_b64:
        st.error("❌ กรุณาอัปโหลดรูปภาพก่อนครับ"); st.stop()
    if not product_name or not product_desc:
        st.error("❌ กรุณากรอกชื่อสินค้าและรายละเอียดก่อนครับ"); st.stop()

    # reset outputs
    st.session_state.update({
        "cf_running":True,"cf_logs":[],"cf_status":{},"cf_outputs":{},
        "cf_gen_images":[],"cf_strategy":"","cf_ad_copy":"","cf_storyboard":"",
        "cf_video_script":"","cf_voice_script":"","cf_tts_audios":[],
        "cf_caption":"","cf_email_line":"","cf_hashtag_bank":"",
        "cf_ab_test":"","cf_calendar":"","cf_review_script":"","cf_repurpose":"",
        "cf_banners":[],
    })

    prog          = st.progress(0, text="🏭 เริ่ม Content Factory...")
    images_for_api = [(b64, mime) for (_, b64, mime) in st.session_state.cf_images_b64]

    # read toggle states (must be read after session_state reset above only resets outputs, not toggles)
    inc_video      = st.session_state.cf_include_video
    inc_storyboard = st.session_state.cf_include_storyboard
    inc_tts        = st.session_state.cf_include_tts
    inc_adcopy     = st.session_state.cf_include_adcopy
    inc_caption    = st.session_state.cf_include_caption
    inc_email      = st.session_state.cf_include_email
    inc_ab         = st.session_state.cf_include_ab
    inc_calendar   = st.session_state.cf_include_calendar
    inc_review     = st.session_state.cf_include_review
    inc_repurpose  = st.session_state.cf_include_repurpose
    inc_banner     = st.session_state.get("cf_include_banner", True)

    STYLE_MAP = {
        "Photorealistic · Product Studio": "photorealistic product photography, studio lighting, sharp focus, 4K ultra",
        "3D Render · CGI Premium":         "3D render CGI quality, ray-traced lighting, ultra detailed",
        "Cinematic · Dark Dramatic":        "cinematic photography, dramatic dark background, moody lighting, premium",
        "Minimalist · Clean White BG":      "minimalist clean white background, professional commercial product photo",
        "Lifestyle · In-Context Shot":      "lifestyle photography, product in real environment, natural lighting",
        "Luxury · Gold & Dark":             "luxury brand photography, dark background, gold accents, elegant premium",
    }
    style_suffix = STYLE_MAP.get(st.session_state.cf_img_style, "photorealistic, 4K")
    lang_note    = f"ตอบเป็น{st.session_state.cf_language}"

    # ── ข้อมูลจากเว็บ (ถ้ามี) ──
    web_analysis = st.session_state.get("cf_web_analysis", "").strip()
    web_ctx = f"\n\n📊 ข้อมูลเพิ่มเติมจากการวิเคราะห์เว็บ (ใช้เป็น insight เพิ่มเติม):\n{web_analysis}" if web_analysis else ""

    # ── STEP 1: INPUT CHECK ──
    prog.progress(4); set_status("input","done")
    log(f"✓ รับภาพ {len(images_for_api)} ไฟล์","ok")
    log(f"✓ สินค้า: {product_name}","ok")
    if web_analysis:
        log("✓ มีข้อมูลจากเว็บ — จะใช้เป็น context เพิ่มเติมทุก Node","ok")
    render_log_box(log_container)

    # ── STEP 2: MARKETING STRATEGY ──
    prog.progress(8, text="NODE 02 · วิเคราะห์กลยุทธ์...")
    set_status("strategy","running"); log("กำลังวิเคราะห์กลยุทธ์การตลาด...","info")
    render_log_box(log_container)

    r = call_gemini(f"""วิเคราะห์ภาพสินค้าและข้อมูลต่อไปนี้ แล้วสร้างกลยุทธ์การตลาดแบบครอบคลุม:

สินค้า: {product_name}
รายละเอียด/จุดเด่น: {product_desc}
ราคา: {price or '-'} | โปรโมชัน: {promo or '-'}
กลุ่มเป้าหมาย: {target or '-'}
แบรนด์: {brand or '-'}
Tone: {tone}{web_ctx}

สร้างครอบคลุม:
1. 🎯 POSITIONING — จุดยืน + USP ที่แข็งแกร่ง
2. 👥 TARGET PERSONA — 2 persona (ชื่อ, อายุ, ปัญหา, trigger ซื้อ, งบ)
3. 💬 KEY MESSAGES — 5 ข้อความหลัก
4. 📱 CONTENT PLAN — แผนคอนเทนต์ TikTok / IG / FB รายสัปดาห์
5. 🔑 SEO KEYWORDS — 10 คำ (ไทย+อังกฤษ)
6. ⚡ HOOK IDEAS — 5 Hook วิดีโอ พร้อมเหตุผล
7. 💰 PRICING PSYCHOLOGY — จิตวิทยาราคาให้รู้สึกคุ้ม
8. 🏆 COMPETITOR GAP — จุดที่คู่แข่งยังทำไม่ได้ เราทำได้

{lang_note} ละเอียด ใช้งานได้จริง""", images_for_api[:4])

    if r.startswith("❌"):
        set_status("strategy","error"); log(r,"err")
    else:
        st.session_state.cf_strategy = r
        set_status("strategy","done"); log("✓ Strategy เสร็จแล้ว","ok")
    render_log_box(log_container)

    # ── STEP 3: GEN IMAGE ──
    prog.progress(18, text="NODE 03 · Gen ภาพ...")
    set_status("genimg","running"); log("สร้าง image prompt...","info")
    render_log_box(log_container)

    # แสดง model ที่ account นี้รองรับจริง (diagnostic)
    _avail_img = list_imagen_models(API_KEY)
    if _avail_img:
        log(f"✓ Imagen models พร้อม: {', '.join(_avail_img)}", "ok")
    else:
        log("⚠️ ไม่พบ Imagen model — ตรวจสอบ console.cloud.google.com → Enable Vertex AI API", "warn")
    render_log_box(log_container)

    prompts_raw = call_gemini(f"""You are a world-class AI image prompt engineer specializing in product advertising photography.

Analyze the product images provided carefully, then create {img_count} ULTRA-DETAILED image generation prompts in English.

Product: {product_name}
Key features: {product_desc}
Price: {price or 'N/A'} | Promo: {promo or 'N/A'}
Target: {target or 'general consumers'}
Visual style: {style_suffix}{web_ctx}

PROMPT STRUCTURE (use ALL components for each prompt):

[SHOT TYPE] + [PRODUCT DESCRIPTION] + [BACKGROUND SCENE] + [LIGHTING SETUP] + [COMPOSITION & LAYOUT] + [TEXT/TYPOGRAPHY ELEMENTS] + [COLOR PALETTE] + [MOOD & ATMOSPHERE] + [TECHNICAL SPECS]

SHOT TYPES to use (one per prompt, vary them):
1. Hero Shot — product centered, dramatic lighting, premium feel
2. Lifestyle In-Use — real person using product in context
3. Feature Callout — close-up with annotation arrows/labels highlighting key features
4. Before/After Split — problem vs solution side by side
5. Flat Lay / Knolling — product + accessories on clean surface top-down
6. Social Proof — product with 5-star rating, review snippet, usage numbers

DETAILED PROMPT RULES:
- Background: describe EXACTLY (e.g. "seamless gradient background transitioning from deep navy #1a1a2e to midnight blue, subtle bokeh light orbs")
- Lighting: describe rig (e.g. "3-point studio lighting: key light at 45° right, soft fill left, rim light behind creating product separation")
- Composition: describe layout zones (e.g. "product occupies lower-left 60% of frame, upper-right reserved for text overlay")
- Text elements IN the image: include Thai product name in large bold font, key benefit in smaller text, price badge if relevant — but write them as DESIGN ELEMENTS in the prompt
- Camera: specify lens (e.g. "shot on 85mm f/1.8, shallow depth of field, product tack sharp")
- Quality tags: "8K ultra-detailed, commercial advertising photography, magazine quality, no watermark"

IMPORTANT:
- Make each prompt completely different angle/concept
- Include specific hex colors that match {bg_color if bg_color else '#1a1a2e'} brand palette
- Each prompt must be 150-250 words long
- NO markdown, return ONLY a valid JSON array: ["prompt1","prompt2",...]

Return ONLY the JSON array, no explanation.""", images_for_api[:4], max_tokens=4096)

    image_prompts = []
    try:
        cleaned = re.sub(r"```json|```","", prompts_raw).strip()
        # หา JSON array ใน response
        match = re.search(r'\[.*\]', cleaned, re.DOTALL)
        if match:
            cleaned = match.group(0)
        image_prompts = json.loads(cleaned)
        if not isinstance(image_prompts, list):
            image_prompts = [image_prompts]
        image_prompts = [str(p) for p in image_prompts if p]
    except Exception:
        # Fallback prompts แบบละเอียด
        image_prompts = [
            (f"Hero shot product advertising photograph of {product_name}, "
             f"{style_suffix}, product centered on seamless dark gradient background "
             f"transitioning from deep navy to midnight blue, 3-point studio lighting "
             f"with key light at 45 degrees right creating dramatic shadows, product "
             f"occupies center 70% of frame with breathing room around edges, "
             f"subtle light reflections on product surface, product name '{product_name}' "
             f"in bold white typography upper-left corner, key benefit text smaller below, "
             f"shot on 85mm f/1.8 lens tack sharp, 8K ultra-detailed commercial "
             f"advertising photography, magazine quality, vibrant saturated colors"),
            (f"Lifestyle in-context photograph showing {product_name} being used by "
             f"a real person in natural environment, {style_suffix}, warm natural "
             f"lighting with soft window light from left, shallow depth of field "
             f"85mm portrait lens, subject and product both sharp foreground blurred "
             f"background, authentic candid expression showing satisfaction, "
             f"product prominently visible with features highlighted, "
             f"lifestyle photography editorial style, 8K commercial quality"),
            (f"Feature callout flat lay photograph of {product_name} on clean "
             f"premium surface, {style_suffix}, top-down 90-degree overhead shot, "
             f"product surrounded by complementary lifestyle accessories, "
             f"soft diffused studio lighting no harsh shadows, clean white or "
             f"light gray background with subtle texture, minimalist composition "
             f"with generous negative space, annotation lines pointing to key "
             f"product features with clean sans-serif labels, "
             f"8K product photography commercial quality"),
        ][:img_count]

    image_prompts = image_prompts[:img_count]

    # log prompt แต่ละอันให้เห็นว่าละเอียดแค่ไหน
    for pi, pp in enumerate(image_prompts):
        log(f"📝 Prompt {pi+1} ({len(pp)} chars): {pp[:80]}...", "dim")
    log(f"✓ สร้าง {len(image_prompts)} ultra-detailed prompt","ok")
    render_log_box(log_container)

    gen_ok = 0
    for idx, iprompt in enumerate(image_prompts):
        log(f"Gen ภาพ {idx+1}/{len(image_prompts)}...","info")
        render_log_box(log_container)
        if idx > 0:
            time.sleep(6)  # Imagen rate limit ~3 req/min
        img_bytes, err = gen_imagen(iprompt)
        short_label    = f"view_{idx+1}"
        if img_bytes:
            st.session_state.cf_gen_images.append((short_label, img_bytes))
            gen_ok += 1
            log(f"✓ ภาพ {idx+1} OK ({len(img_bytes)//1024} KB)","ok")
        else:
            log(f"⚠️ ภาพ {idx+1}: {err}","warn")
            _, b64_orig, mime_orig = st.session_state.cf_images_b64[idx % len(st.session_state.cf_images_b64)]
            st.session_state.cf_gen_images.append((short_label, base64.b64decode(b64_orig)))
        render_log_box(log_container)

    set_status("genimg","done" if gen_ok > 0 else "error")
    log(f"✓ รวม {len(st.session_state.cf_gen_images)} ภาพ","ok")
    prog.progress(35)
    render_log_box(log_container)

    # ── STEP 4: STORYBOARD ──
    if inc_storyboard:
        prog.progress(40, text="NODE 04 · สร้าง Storyboard...")
        set_status("storyboard","running"); log("กำลังสร้าง Storyboard...","info")
        render_log_box(log_container)

        r = call_gemini(f"""สร้าง Storyboard สำหรับวิดีโอโฆษณา {product_name} Format: {vid_format}

สร้างแบบมืออาชีพ:

[SCENE 01 — 0:00-0:03 — HOOK]
📐 ขนาดภาพ: 9:16 vertical
🎬 Camera: (มุมกล้อง + การเคลื่อนที่)
🖼️ Visual: (บรรยายภาพที่ต้องถ่าย/สร้าง ละเอียดมาก)
🎨 Color mood: (โทนสี)
📝 Text overlay: (ข้อความบนหน้าจอ + ตำแหน่ง + ขนาด font)
🎤 VO line: (ประโยคที่พูด)
🎵 Sound: (เสียง/เพลง)
⏱️ Duration: X วินาที

(ทำทุก scene จนครบ)

จุดเด่น: {product_desc}
ราคา: {price or '-'} | โปรโมชัน: {promo or '-'}{web_ctx}
{lang_note}""", images_for_api[:4])

        if not r.startswith("❌"):
            st.session_state.cf_storyboard = r
            set_status("storyboard","done"); log("✓ Storyboard เสร็จแล้ว","ok")
        else:
            set_status("storyboard","error"); log(r,"err")
        render_log_box(log_container)
    else:
        set_status("storyboard","skip"); log("○ ข้าม Storyboard","dim")

    # ── STEP 5: VIDEO SCRIPT ──
    if inc_video:
        prog.progress(50, text="NODE 05 · เขียน Video Script...")
        set_status("vidscript","running"); log("กำลังเขียน Video Script...","info")
        render_log_box(log_container)

        r = call_gemini(f"""เขียน Video Script ครบ 100% สำหรับ {vid_format}

สินค้า: {product_name} | Tone: {tone}
จุดเด่น: {product_desc}
ราคา: {price or '-'} | โปรโมชัน: {promo or '-'}
กลุ่มเป้าหมาย: {target or '-'}{web_ctx}

Format:
════ VIDEO SCRIPT · {product_name} ════
Format: {vid_format}

[Scene N — 0:00-0:XX]
🎬 Visual   : ...
🎤 Voiceover: "..."
📝 On screen: ...
🎵 Music    : ...

(ทุก scene จนครบ)

🚀 HOOK (3 วิแรก): ...
📣 CTA ปิดท้าย: ...
🎵 เพลงแนะนำ: ...

{lang_note}""", images_for_api[:4])

        if not r.startswith("❌"):
            st.session_state.cf_video_script = r
            set_status("vidscript","done"); log("✓ Video Script เสร็จแล้ว","ok")
        else:
            set_status("vidscript","error"); log(r,"err")
        render_log_box(log_container)
    else:
        set_status("vidscript","skip"); log("○ ข้าม Video Script","dim")

    prog.progress(60)

    # ── STEP 6: VOICE SCRIPT ──
    prog.progress(63, text="NODE 06 · เขียน Voice Script...")
    set_status("voicescript","running"); log("กำลังเขียน Voice Script...","info")
    render_log_box(log_container)

    r = call_gemini(f"""เขียน Voice Script (Voiceover) สำหรับ {vid_format} สินค้า {product_name}

จุดเด่น: {product_desc} | ราคา: {price or '-'} | Tone: {tone}{web_ctx}

Format:
════ VOICE SCRIPT ════

[Scene 1 — 0:00-0:03 — Tone: ตื่นเต้น/เร็ว]
"ข้อความที่พูด..."

(ทุก scene)

════ FULL READ-THROUGH ════
(ข้อความทั้งหมดรวมกัน อ่านต่อเนื่องได้ทันที)

{lang_note} เขียนให้ฟังเป็นธรรมชาติ ไม่มีวงเล็บ""", images_for_api[:2])

    if not r.startswith("❌"):
        st.session_state.cf_voice_script = r
        set_status("voicescript","done"); log("✓ Voice Script เสร็จแล้ว","ok")
    else:
        set_status("voicescript","error"); log(r,"err")
    render_log_box(log_container)
    prog.progress(68)

    # ── STEP 7: TTS ──
    if inc_tts and st.session_state.cf_voice_script:
        prog.progress(72, text="NODE 07 · สร้างไฟล์เสียง TTS...")
        set_status("tts","running"); log("กำลังสร้างไฟล์เสียง...","info")
        render_log_box(log_container)

        vtext     = st.session_state.cf_voice_script
        full_read = vtext
        if "FULL READ-THROUGH" in vtext:
            try:
                full_read = re.sub(r"[═=]+","", vtext.split("FULL READ-THROUGH")[1]).strip()
            except: pass

        full_audio = tts_gtts(full_read)
        if full_audio:
            st.session_state.cf_tts_audios.append(("00_full_voiceover", full_audio))
            log("✓ Full voiceover เสร็จแล้ว","ok")

        scenes = re.findall(r'\[Scene\s*\d+[^\]]*\]\s*["""]([^"""]+)["""]', vtext, re.DOTALL)
        for i, sc in enumerate(scenes[:6]):
            log(f"TTS scene {i+1}...","info"); render_log_box(log_container)
            a = tts_gtts(sc.strip())
            if a: st.session_state.cf_tts_audios.append((f"scene_{i+1:02d}", a))
            render_log_box(log_container)

        if st.session_state.cf_tts_audios:
            set_status("tts","done"); log(f"✓ รวม {len(st.session_state.cf_tts_audios)} ไฟล์เสียง","ok")
        else:
            set_status("tts","error"); log("⚠️ TTS ล้มเหลว — pip install gtts","warn")
        render_log_box(log_container)
    else:
        set_status("tts","skip"); log("○ ข้าม TTS","dim")

    prog.progress(78)

    # ── STEP 8: AD COPY ──
    if inc_adcopy:
        prog.progress(80, text="NODE 08 · สร้าง Ad Copy...")
        set_status("adcopy","running"); log("กำลังสร้าง Ad Copy...","info")
        render_log_box(log_container)

        r = call_gemini(f"""สร้าง Ad Copy สำเร็จรูป ใช้งานได้ทันทีสำหรับ:

สินค้า: {product_name}
จุดเด่น: {product_desc}
ราคา: {price or '-'} | โปรโมชัน: {promo or '-'}
Tone: {tone}{web_ctx}

สร้างครบทุกรูปแบบ:

📘 FACEBOOK AD COPY (3 variations):
· Variation A — Awareness: Headline + Primary text + CTA
· Variation B — Consideration: Pain point angle
· Variation C — Conversion: Urgency + offer

🎵 TIKTOK AD SCRIPT (hook + body + CTA ≤60 คำ) — 2 variations

🔍 GOOGLE AD (Headline 1-3 + Description 1-2) — 2 sets

📱 LINE OA PUSH MESSAGE (≤500 chars) — 2 variations

{lang_note} ทุก copy ใช้งานได้ copy-paste ทันที""", images_for_api[:2])

        if not r.startswith("❌"):
            st.session_state.cf_ad_copy = r
            set_status("adcopy","done"); log("✓ Ad Copy เสร็จแล้ว","ok")
        else:
            set_status("adcopy","error"); log(r,"err")
        render_log_box(log_container)
    else:
        set_status("adcopy","skip"); log("○ ข้าม Ad Copy","dim")

    # ── STEP 9: CAPTION ──
    if inc_caption:
        prog.progress(84, text="NODE 09 · สร้าง Caption...")
        set_status("caption","running"); log("กำลังสร้าง Caption...","info")
        render_log_box(log_container)

        r = call_gemini(f"""สร้าง Caption + Hashtag ครบทุกแพลตฟอร์ม

สินค้า: {product_name} | จุดเด่น: {product_desc}
ราคา: {price or '-'} | โปรโมชัน: {promo or '-'}
Tone: {tone}

📘 FACEBOOK (Headline + 3 ย่อหน้า + CTA + Hashtag 5-8)
📷 INSTAGRAM (Lifestyle hook + body + CTA + Hashtag 12-15)
🎵 TIKTOK (Punchy + Hashtag trending 5-8)
🛒 SHOPEE (ชื่อ SEO 120 ตัว + Bullet 5 ข้อ + Tags 5)
🐦 X/TWITTER (≤280 chars + Hashtag 2-3)

{lang_note} copy-paste ได้ทันที""", images_for_api[:2])

        if not r.startswith("❌"):
            st.session_state.cf_caption = r
            set_status("caption","done"); log("✓ Caption เสร็จแล้ว","ok")
        else:
            set_status("caption","error"); log(r,"err")
        render_log_box(log_container)
    else:
        set_status("caption","skip"); log("○ ข้าม Caption","dim")

    # ── STEP 10: EMAIL / LINE BROADCAST ──
    if inc_email:
        prog.progress(88, text="NODE 10 · สร้าง Email/LINE Broadcast...")
        set_status("email","running"); log("กำลังสร้าง Email/LINE...","info")
        render_log_box(log_container)

        r = call_gemini(f"""สร้าง Email Marketing + LINE Broadcast สำหรับสินค้า {product_name}

จุดเด่น: {product_desc} | ราคา: {price or '-'} | โปรโมชัน: {promo or '-'}
กลุ่มเป้าหมาย: {target or '-'} | Tone: {tone}

📧 EMAIL — NEW LAUNCH:
Subject: (เปิดอ่านแน่ ≤50 ตัวอักษร)
Preview text: ...
Body: (Greeting → Problem → Solution → CTA → PS)

📧 EMAIL — FOLLOW-UP (ยังไม่ซื้อหลัง 3 วัน):
Subject: ...
Body: ...

📱 LINE BROADCAST — ANNOUNCEMENT (≤300 chars + emoji):
...

📱 LINE BROADCAST — FLASH SALE REMINDER:
...

{lang_note}""", images_for_api[:2])

        if not r.startswith("❌"):
            st.session_state.cf_email_line = r
            set_status("email","done"); log("✓ Email/LINE เสร็จแล้ว","ok")
        else:
            set_status("email","error"); log(r,"err")
        render_log_box(log_container)
    else:
        set_status("email","skip"); log("○ ข้าม Email/LINE","dim")

    # ── STEP 11: HASHTAG BANK ──
    prog.progress(93, text="NODE 11 · สร้าง Hashtag Bank...")
    set_status("hashtag","running"); log("กำลังสร้าง Hashtag Bank...","info")
    render_log_box(log_container)

    r = call_gemini(f"""สร้าง Hashtag Bank ครบสำหรับ {product_name} ({product_desc[:80]})

แบ่งเป็น:
🔥 VIRAL (ยอดนิยม >1M) — 10 อัน
🎯 NICHE (เฉพาะกลุ่ม 100K-1M) — 15 อัน
🏷️ BRAND (แบรนด์+สินค้า) — 10 อัน
📍 LOCAL THAI (ไทย) — 10 อัน
🛒 COMMERCE (ซื้อขาย) — 10 อัน
📐 BY PLATFORM:
  · TikTok set (8 อัน)
  · Instagram set (15 อัน)
  · Facebook set (5 อัน)

รวม 50+ hashtag ที่ใช้งานได้จริงปี 2025
{lang_note}""", None)

    if not r.startswith("❌"):
        st.session_state.cf_hashtag_bank = r
        set_status("hashtag","done"); log("✓ Hashtag Bank เสร็จแล้ว","ok")
    else:
        set_status("hashtag","error"); log(r,"err")
    render_log_box(log_container)

    # ── STEP 12: A/B TEST ──
    if inc_ab:
        prog.progress(94, text="NODE 12 · สร้าง A/B Test...")
        set_status("abtest","running"); log("กำลังสร้าง A/B Test Copy...","info")
        render_log_box(log_container)

        r = call_gemini(f"""สร้าง A/B Test สำหรับ {product_name} เพื่อทดสอบว่า Hook และ CTA แบบไหนได้ผลดีกว่า

จุดเด่น: {product_desc} | ราคา: {price or '-'} | Tone: {tone}

สร้าง 2 version ที่ต่างกันสุด ๆ:

🅰️ VERSION A — EMOTION-BASED:
· Hook (3 วิ): ...
· Body (10 วิ): ...
· CTA: ...
· เหตุผลที่ใช้ได้ผล: ...

🅱️ VERSION B — LOGIC-BASED:
· Hook (3 วิ): ...
· Body (10 วิ): ...
· CTA: ...
· เหตุผลที่ใช้ได้ผล: ...

📊 วิธีทดสอบ A/B แนะนำ:
· Budget split: ...
· Metric หลักที่ดู: ...
· ระยะเวลาทดสอบ: ...
· เกณฑ์ตัดสิน Winner: ...

{lang_note}""", images_for_api[:2])

        if not r.startswith("❌"):
            st.session_state.cf_ab_test = r
            set_status("abtest","done"); log("✓ A/B Test เสร็จแล้ว","ok")
        else:
            set_status("abtest","error"); log(r,"err")
        render_log_box(log_container)
    else:
        set_status("abtest","skip"); log("○ ข้าม A/B Test","dim")

    # ── STEP 13: CONTENT CALENDAR ──
    if inc_calendar:
        prog.progress(95, text="NODE 13 · สร้าง Content Calendar...")
        set_status("calendar","running"); log("กำลังสร้าง Content Calendar 30 วัน...","info")
        render_log_box(log_container)

        r = call_gemini(f"""สร้างแผนโพสต์ Content Calendar 30 วัน สำหรับ {product_name}

จุดเด่น: {product_desc} | Tone: {tone} | กลุ่มเป้าหมาย: {target or '-'}

แบ่งเป็น 4 สัปดาห์ · แต่ละวันระบุ:
📅 วันที่ | 📱 แพลตฟอร์ม | 🎯 Content Type | 📝 หัวข้อ | ⏰ เวลาโพสต์

สัปดาห์ 1 — AWARENESS (สร้างการรับรู้)
วันที่ 1: TikTok | Hook Video | [หัวข้อ] | 18:00
วันที่ 2: IG | Product Close-up | [หัวข้อ] | 09:00
... (ครบ 7 วัน)

สัปดาห์ 2 — CONSIDERATION (เปรียบเทียบ/ให้ข้อมูล)
...

สัปดาห์ 3 — CONVERSION (กระตุ้นซื้อ)
...

สัปดาห์ 4 — RETENTION (รักษาลูกค้า/รีวิว)
...

📌 Content Mix แนะนำ:
· วิดีโอ: X%
· ภาพ: X%
· Story/Reel: X%
· Live: X%

{lang_note} ใช้งานได้จริง copy-paste""", None)

        if not r.startswith("❌"):
            st.session_state.cf_calendar = r
            set_status("calendar","done"); log("✓ Content Calendar เสร็จแล้ว","ok")
        else:
            set_status("calendar","error"); log(r,"err")
        render_log_box(log_container)
    else:
        set_status("calendar","skip"); log("○ ข้าม Calendar","dim")

    # ── STEP 14: REVIEW / UGC SCRIPT ──
    if inc_review:
        prog.progress(96, text="NODE 14 · สร้าง Review Script...")
        set_status("review","running"); log("กำลังสร้าง Review/UGC Script...","info")
        render_log_box(log_container)

        r = call_gemini(f"""สร้างสคริปต์รีวิวสินค้า {product_name} สำหรับ UGC และลูกค้าจริง

จุดเด่น: {product_desc} | Tone: {tone}

🎬 SHORT REVIEW (TikTok/Reels ≤30 วิ):
Opening: "..."
Problem: "..."
Discovery: "..."
Result: "..."
CTA: "..."

🎬 LONG REVIEW (YouTube 2-3 นาที) — Outline:
00:00 — Intro + Hook
00:15 — ปัญหาก่อนใช้
00:45 — แกะกล่อง/Unbox
01:15 — วิธีใช้งาน
01:45 — ผลลัพธ์จริง
02:15 — เปรียบเทียบคู่แข่ง
02:45 — สรุป + ราคา + ลิงก์

💬 CUSTOMER TESTIMONIAL TEMPLATES (3 แบบ):
แบบที่ 1 — ปัญหาแก้ได้: "..."
แบบที่ 2 — ผลลัพธ์ตัวเลข: "..."
แบบที่ 3 — เปรียบเทียบ before/after: "..."

📝 REVIEW REQUEST MESSAGE (ส่งลูกค้าหลังซื้อ 7 วัน):
LINE: "..."
Email subject: "..."

{lang_note}""", images_for_api[:2])

        if not r.startswith("❌"):
            st.session_state.cf_review_script = r
            set_status("review","done"); log("✓ Review Script เสร็จแล้ว","ok")
        else:
            set_status("review","error"); log(r,"err")
        render_log_box(log_container)
    else:
        set_status("review","skip"); log("○ ข้าม Review Script","dim")

    # ── STEP 15: REPURPOSE PACK ──
    if inc_repurpose:
        prog.progress(98, text="NODE 15 · สร้าง Repurpose Pack...")
        set_status("repurpose","running"); log("กำลังสร้าง Repurpose Pack...","info")
        render_log_box(log_container)

        r = call_gemini(f"""สร้าง Repurpose Pack สำหรับ {product_name} — แปลง 1 content ให้ใช้ได้ทุกแพลตฟอร์ม

จุดเด่น: {product_desc} | Tone: {tone}

เริ่มจาก Video Script หลัก แล้วแปลงเป็น:

🎵 TIKTOK VERSION (punchy, ≤60 วิ):
Hook: "..." | Script: "..."

📷 INSTAGRAM REEL CAPTION:
...

📘 FACEBOOK POST (story format, 3 ย่อหน้า):
...

🐦 X/TWITTER THREAD (5 tweets):
Tweet 1: ...
Tweet 2: ...
...

📰 BLOG POST OUTLINE (SEO):
Title: ...
H1: ... | H2: ... | H3: ...
Meta description: ...

🎙️ PODCAST TALKING POINTS (5 ข้อ):
...

📧 NEWSLETTER SNIPPET (100 คำ):
...

🛒 MARKETPLACE DESCRIPTION (Shopee/Lazada):
ชื่อสินค้า SEO: ...
คำอธิบาย: ...
จุดเด่น (bullet): ...

{lang_note} ใช้งานได้ทันที copy-paste""", images_for_api[:2])

        if not r.startswith("❌"):
            st.session_state.cf_repurpose = r
            set_status("repurpose","done"); log("✓ Repurpose Pack เสร็จแล้ว","ok")
        else:
            set_status("repurpose","error"); log(r,"err")
        render_log_box(log_container)
    else:
        set_status("repurpose","skip"); log("○ ข้าม Repurpose Pack","dim")

    # ── STEP BANNER: สร้างแบนเนอร์จากรูปสินค้าจริง (PIL) ──
    if inc_banner:
        prog.progress(99, text="NODE · สร้างแบนเนอร์โฆษณา...")
        set_status("banner","running"); log("กำลังสร้างแบนเนอร์โฆษณา (PIL จากรูปสินค้าจริง)...","info")
        render_log_box(log_container)

        headline     = st.session_state.get("cf_banner_headline","").strip() or product_name
        cta_text     = st.session_state.get("cf_banner_cta","สั่งซื้อเลย!")
        bg_color     = st.session_state.get("cf_banner_bgcolor","#1a1a2e")
        txt_color    = st.session_state.get("cf_banner_txtcolor","#ffffff")
        banner_count = int(st.session_state.get("cf_banner_count", 3))

        # (label, W, H, layout)
        # layout: "landscape" | "portrait" | "square" | "leaderboard"
        BANNER_SPECS = [
            ("Facebook_AD_1200x628",       1200, 628,  "landscape"),
            ("TikTok_Story_1080x1920",     1080, 1920, "portrait"),
            ("Shopee_Banner_1200x628",     1200, 628,  "landscape"),
            ("Instagram_Square_1080x1080", 1080, 1080, "square"),
            ("LINE_OA_1040x585",           1040, 585,  "landscape"),
            ("Google_Display_728x90",       728,  90,  "leaderboard"),
        ]

        try:
            from PIL import Image as PImage, ImageDraw, ImageFont, ImageFilter, ImageEnhance
            import io as _io
            PIL_OK = True
        except ImportError:
            PIL_OK = False
            log("⚠️ ไม่มี Pillow (pip install Pillow)", "warn")

        def hex2rgb(h):
            h = h.lstrip("#")
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

        def load_font(size):
            """โหลด font ที่ render Thai ได้ หรือ fallback default"""
            for fp in [
                "/usr/share/fonts/truetype/thai/THSarabunNew Bold.ttf",
                "/usr/share/fonts/truetype/thai/THSarabunNew.ttf",
                "/usr/share/fonts/truetype/noto/NotoSansThai-Bold.ttf",
                "/usr/share/fonts/truetype/noto/NotoSansThai-Regular.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            ]:
                try:
                    return ImageFont.truetype(fp, size)
                except Exception:
                    continue
            return ImageFont.load_default()

        def draw_text_shadow(draw, pos, text, font, fill, shadow_offset=2):
            """วาด text พร้อม drop shadow"""
            sx, sy = pos
            draw.text((sx+shadow_offset, sy+shadow_offset), text, font=font, fill=(0,0,0,160))
            draw.text(pos, text, font=font, fill=fill)

        def wrap_text(text, font, max_width, draw):
            """ตัดบรรทัด text ให้พอดีกับ max_width"""
            words = text.split()
            lines, cur = [], ""
            for w in words:
                test = (cur + " " + w).strip()
                try:
                    tw = draw.textbbox((0,0), test, font=font)[2]
                except Exception:
                    tw = len(test) * (font.size if hasattr(font,'size') else 12)
                if tw <= max_width:
                    cur = test
                else:
                    if cur: lines.append(cur)
                    cur = w
            if cur: lines.append(cur)
            return lines if lines else [text]

        def make_banner_pil(product_photo_bytes, W, H, layout,
                            headline_text, cta, bg_hex, txt_hex, price_text=""):
            """
            สร้าง banner จากรูปสินค้าจริง
            - landscape/square: รูปซ้าย, text ขวา หรือ text overlay ล่าง
            - portrait (TikTok): รูปบน, text ล่าง gradient
            - leaderboard (728x90): รูปซ้าย, text เรียง inline
            """
            bg_rgb  = hex2rgb(bg_hex)
            txt_rgb = hex2rgb(txt_hex)
            acc_rgb = (220, 50, 50)   # accent แดง (CTA button)

            # ── สร้าง canvas ──
            canvas = PImage.new("RGB", (W, H), bg_rgb)
            draw   = ImageDraw.Draw(canvas)

            # ── โหลดรูปสินค้า ──
            prod_img = PImage.open(_io.BytesIO(product_photo_bytes)).convert("RGBA")

            if layout == "leaderboard":
                # 728×90 — รูปซ้าย 80px, text กลาง, CTA ขวา
                ph = H - 8
                pw = ph
                prod_img_r = prod_img.copy()
                prod_img_r.thumbnail((pw, ph), PImage.LANCZOS)
                px = 4; py = (H - prod_img_r.height) // 2
                canvas.paste(prod_img_r, (px, py), prod_img_r)

                f_hl  = load_font(max(11, H//6))
                f_cta = load_font(max(10, H//7))
                text_x = pw + 12
                try:
                    tw = draw.textbbox((0,0), headline_text[:35], font=f_hl)[3]
                except Exception:
                    tw = H//2
                draw_text_shadow(draw, (text_x, (H-tw)//2 - 2),
                                 headline_text[:35], f_hl, (*txt_rgb, 255))
                # CTA
                try:    cw = draw.textbbox((0,0), cta[:15], font=f_cta)[2]
                except: cw = 80
                cx2 = W - cw - 16; cy2 = (H - H//4)//2
                pad2 = 4
                draw.rounded_rectangle([cx2-pad2, cy2-pad2, cx2+cw+pad2, cy2+H//4+pad2],
                                        radius=4, fill=acc_rgb)
                draw.text((cx2, cy2), cta[:15], font=f_cta, fill=(255,255,255))

            elif layout == "portrait":
                # TikTok 1080×1920 — รูปบน 65%, gradient ล่าง 35%
                prod_area_h = int(H * 0.65)
                prod_img_r  = prod_img.copy()
                prod_img_r.thumbnail((W, prod_area_h), PImage.LANCZOS)
                px = (W - prod_img_r.width) // 2
                py = (prod_area_h - prod_img_r.height) // 2
                canvas.paste(prod_img_r, (px, py), prod_img_r)

                # gradient overlay ล่าง
                grad = PImage.new("RGBA", (W, H - prod_area_h + 60), (0,0,0,0))
                for gy in range(grad.height):
                    alpha = int(220 * gy / grad.height)
                    grad_draw = ImageDraw.Draw(grad)
                    grad_draw.line([(0,gy),(W,gy)], fill=(*bg_rgb, alpha))
                canvas.paste(grad.convert("RGB"), (0, prod_area_h - 60),
                             grad.split()[3] if grad.mode == "RGBA" else None)

                # text zone
                tz_y = prod_area_h + 20
                f_hl  = load_font(max(52, W//18))
                f_sub = load_font(max(36, W//28))
                f_cta = load_font(max(40, W//24))

                lines = wrap_text(headline_text, f_hl, W - 80, draw)
                cy3 = tz_y
                for line in lines[:3]:
                    draw_text_shadow(draw, (40, cy3), line, f_hl, (*txt_rgb, 255), shadow_offset=3)
                    try:    lh = draw.textbbox((0,0), line, font=f_hl)[3] + 8
                    except: lh = f_hl.size + 8 if hasattr(f_hl,'size') else 60
                    cy3 += lh

                if price_text:
                    draw_text_shadow(draw, (40, cy3 + 10), price_text, f_sub, (255,220,50,255))
                    cy3 += 70

                # CTA button
                try:    cw3 = draw.textbbox((0,0), cta[:20], font=f_cta)[2]
                except: cw3 = 300
                btn_x = (W - cw3 - 80) // 2; btn_y = cy3 + 30
                draw.rounded_rectangle([btn_x, btn_y, btn_x+cw3+80, btn_y+80],
                                        radius=40, fill=acc_rgb)
                draw.text((btn_x+40, btn_y+18), cta[:20], font=f_cta, fill=(255,255,255))

            else:
                # landscape / square
                # รูปสินค้าด้านขวา 45% ของ canvas
                prod_zone_w = int(W * 0.45)
                prod_img_r  = prod_img.copy()
                prod_img_r.thumbnail((prod_zone_w - 20, H - 20), PImage.LANCZOS)
                px4 = W - prod_zone_w + (prod_zone_w - prod_img_r.width) // 2
                py4 = (H - prod_img_r.height) // 2
                canvas.paste(prod_img_r, (px4, py4), prod_img_r)

                # vertical divider แสงสี accent
                div_x = W - prod_zone_w - 2
                for di in range(4):
                    draw.line([(div_x+di, 0),(div_x+di, H)],
                              fill=(*acc_rgb, 180 - di*40))

                # text zone ซ้าย
                text_zone_w = W - prod_zone_w - 40
                pad_left    = 40

                if layout == "square":
                    f_hl  = load_font(max(48, W//20))
                    f_sub = load_font(max(30, W//32))
                    f_cta = load_font(max(34, W//28))
                else:
                    f_hl  = load_font(max(42, W//24))
                    f_sub = load_font(max(26, W//40))
                    f_cta = load_font(max(28, W//36))

                # headline (wrap)
                lines5 = wrap_text(headline_text, f_hl, text_zone_w, draw)
                cy5 = int(H * 0.18)
                for line in lines5[:3]:
                    draw_text_shadow(draw, (pad_left, cy5), line, f_hl, (*txt_rgb, 255))
                    try:    lh5 = draw.textbbox((0,0), line, font=f_hl)[3] + 6
                    except: lh5 = 50
                    cy5 += lh5

                # ราคา (ถ้ามี)
                if price_text:
                    cy5 += 10
                    draw_text_shadow(draw, (pad_left, cy5), price_text, f_sub,
                                     (255, 220, 50, 255))
                    cy5 += 50

                # CTA button
                try:    cw5 = draw.textbbox((0,0), cta[:20], font=f_cta)[2]
                except: cw5 = 160
                btn_y5 = cy5 + 20
                btn_pad = max(14, W//60)
                draw.rounded_rectangle(
                    [pad_left, btn_y5, pad_left+cw5+btn_pad*2,
                     btn_y5 + max(36, H//8)],
                    radius=max(8, H//20), fill=acc_rgb
                )
                draw.text((pad_left+btn_pad, btn_y5 + max(6,H//18)),
                          cta[:20], font=f_cta, fill=(255,255,255))

            # ── ขอบ accent ──
            bd = 3
            draw.rectangle([0,0,W-1,H-1], outline=(*acc_rgb,), width=bd)

            buf_out = _io.BytesIO()
            canvas.save(buf_out, format="PNG", optimize=True)
            return buf_out.getvalue()

        if not PIL_OK:
            log("❌ ไม่มี Pillow — ข้าม Banner","err")
            set_status("banner","error")
        else:
            banner_ok   = 0
            price_label = f"฿{price}" if price else ""
            specs_to_run = BANNER_SPECS[:banner_count]

            for idx, (blabel, BW, BH, blayout) in enumerate(specs_to_run):
                log(f"สร้าง banner {idx+1}/{len(specs_to_run)}: {blabel} ({BW}×{BH})...", "info")
                render_log_box(log_container)
                try:
                    # เลือกรูปสินค้าหมุนเวียน
                    _, b64src, _ = st.session_state.cf_images_b64[
                        idx % len(st.session_state.cf_images_b64)
                    ]
                    prod_bytes = base64.b64decode(b64src)

                    banner_bytes = make_banner_pil(
                        prod_bytes, BW, BH, blayout,
                        headline, cta_text, bg_color, txt_color, price_label
                    )
                    st.session_state.cf_banners.append((blabel, banner_bytes))
                    banner_ok += 1
                    log(f"✓ banner {idx+1} ({blabel}) OK", "ok")
                except Exception as e:
                    log(f"⚠️ banner {idx+1} error: {e}", "warn")
                render_log_box(log_container)

            set_status("banner", "done" if banner_ok > 0 else "error")
            log(f"✓ Banner เสร็จ {banner_ok} ชิ้น (ใช้รูปสินค้าจริง)" if banner_ok > 0
                else "⚠️ Gen banner ไม่สำเร็จ",
                "ok" if banner_ok > 0 else "err")
            render_log_box(log_container)
    else:
        set_status("banner","skip"); log("○ ข้าม Banner Gen","dim")
    prog.progress(100, text="✅ เสร็จสมบูรณ์!")
    set_status("export","done"); set_output("export","ready")
    log("🎉 Content Factory v3.0 เสร็จสมบูรณ์! Download ZIP ได้เลยครับ","ok")
    render_log_box(log_container)

    st.session_state.cf_running = False
    st.rerun()