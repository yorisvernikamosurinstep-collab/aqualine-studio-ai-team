# -*- coding: utf-8 -*-
"""
🔭 ANDROMEDA — Pre-Meeting Ad Auditor (Omni Scanner)
จำลองวิธีคิดของ Meta Andromeda Engine + GEM + Lattice
วิเคราะห์ Ads ก่อนยิงจริง ด้วย Gemini Vision + Claude Vision
"""

import streamlit as st
import requests
import base64
import json
import os
import re
import time
from datetime import datetime
from io import BytesIO

import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ui_settings import inject_global_font_css

st.set_page_config(
    page_title="Andromeda — Ad Auditor · AQUALINE",
    layout="wide",
    initial_sidebar_state="expanded",
    page_icon="🔭"
)

from auth_guard import require_auth
require_auth()
st.session_state["_active_page"] = __file__
st.markdown(inject_global_font_css(), unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# PROJECT VAULT HELPERS
# ══════════════════════════════════════════════════════════════════
VAULT_FILE = "project_vault.json"

def load_vault():
    if os.path.exists(VAULT_FILE):
        try:
            with open(VAULT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for k in data:
                    if "knowledge" not in data[k]: data[k]["knowledge"] = ""
                    if "history" not in data[k]: data[k]["history"] = []
                    if "memory" not in data[k]: data[k]["memory"] = ""
                    if "pinned_facts" not in data[k]: data[k]["pinned_facts"] = []
                    if "memory_updated_at" not in data[k]: data[k]["memory_updated_at"] = ""
                    if "ad_performance" not in data[k]: data[k]["ad_performance"] = []
                return data
        except: pass
    return {"Default Project": {"url": "", "brief": "", "knowledge": "", "history": [],
                                 "memory": "", "pinned_facts": [], "memory_updated_at": "",
                                 "ad_performance": []}}

def save_vault(vault_data):
    with open(VAULT_FILE, "w", encoding="utf-8") as f:
        json.dump(vault_data, f, ensure_ascii=False, indent=4)

if "vault" not in st.session_state:
    st.session_state.vault = load_vault()
if "current_project" not in st.session_state:
    st.session_state.current_project = list(st.session_state.vault.keys())[0]

# ══════════════════════════════════════════════════════════════════
# API KEYS
# ══════════════════════════════════════════════════════════════════
GEMINI_KEY      = st.secrets.get("GOOGLE_API_KEY", "")
ANTHROPIC_KEY   = st.secrets.get("ANTHROPIC_API_KEY", "")
ANDROMEDA_ENGINE = st.secrets.get("ANDROMEDA_ENGINE", "gemini")  # gemini | claude | both

# ══════════════════════════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=IBM+Plex+Sans+Thai:wght@300;400;600;700&display=swap');
*,*::before,*::after{box-sizing:border-box;}
.stApp{background:#040710;color:#cbd5e1;font-family:'IBM Plex Sans Thai',sans-serif;}
[data-testid="stSidebar"]{background:#080d16!important;border-right:1px solid #1e293b!important;}

/* ── Header ── */
.andro-header{
  background:linear-gradient(135deg,#040710 0%,#0a0e1a 40%,#0d1020 100%);
  border-bottom:1px solid rgba(56,189,248,.2);
  padding:24px 32px; margin-bottom:28px;
  position:relative; overflow:hidden;
}
.andro-header::before{
  content:''; position:absolute; inset:0;
  background:radial-gradient(ellipse 60% 80% at 50% -20%, rgba(56,189,248,.08) 0%, transparent 70%);
  pointer-events:none;
}
.andro-header::after{
  content:''; position:absolute; inset:0;
  background:repeating-linear-gradient(90deg,transparent,transparent 100px,rgba(56,189,248,.02) 100px,rgba(56,189,248,.02) 101px);
  pointer-events:none;
}
.andro-title{font-family:'IBM Plex Mono',monospace;font-size:28px;font-weight:700;color:#f1f5f9;
  letter-spacing:3px;text-shadow:0 0 30px rgba(56,189,248,.3);}
.andro-subtitle{font-family:'IBM Plex Mono',monospace;font-size:11px;color:#38bdf8;
  letter-spacing:2px;margin-top:4px;text-transform:uppercase;}
.andro-badge{display:inline-block;padding:3px 12px;border-radius:3px;font-family:'IBM Plex Mono',monospace;
  font-size:9px;font-weight:700;letter-spacing:2px;background:rgba(56,189,248,.15);
  border:1px solid rgba(56,189,248,.4);color:#38bdf8;margin-left:12px;vertical-align:middle;}
.meta-badge{background:rgba(99,102,241,.15);border-color:rgba(99,102,241,.4);color:#818cf8;}

/* ── Mode Tabs ── */
.mode-grid{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:24px;}
.mode-card{background:rgba(15,23,42,.8);border:1px solid #1e293b;border-radius:10px;
  padding:14px 10px;text-align:center;cursor:pointer;transition:all .25s;position:relative;}
.mode-card:hover{border-color:#38bdf8;background:rgba(56,189,248,.05);}
.mode-card.active{border-color:#38bdf8;background:rgba(56,189,248,.1);
  box-shadow:0 0 20px rgba(56,189,248,.15);}
.mode-icon{font-size:24px;margin-bottom:6px;}
.mode-name{font-family:'IBM Plex Mono',monospace;font-size:10px;font-weight:700;color:#94a3b8;
  letter-spacing:.5px;text-transform:uppercase;line-height:1.4;}
.mode-card.active .mode-name{color:#38bdf8;}

/* ── Score Meters ── */
.score-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:16px 0;}
.score-card{background:rgba(7,11,18,.95);border:1px solid #1e293b;border-radius:10px;padding:16px;text-align:center;}
.score-label{font-family:'IBM Plex Mono',monospace;font-size:9px;color:#475569;
  letter-spacing:2px;text-transform:uppercase;margin-bottom:8px;}
.score-num{font-family:'IBM Plex Mono',monospace;font-size:36px;font-weight:700;line-height:1;}
.score-bar{height:4px;border-radius:2px;background:#1e293b;margin-top:8px;overflow:hidden;}
.score-fill{height:100%;border-radius:2px;transition:width 1s ease;}
.score-high{color:#34d399;} .score-fill-high{background:linear-gradient(90deg,#34d399,#6ee7b7);}
.score-mid {color:#fbbf24;} .score-fill-mid {background:linear-gradient(90deg,#f59e0b,#fbbf24);}
.score-low {color:#f87171;} .score-fill-low {background:linear-gradient(90deg,#ef4444,#f87171);}

/* ── Entity ID Badge ── */
.entity-safe{background:rgba(52,211,153,.1);border:1px solid rgba(52,211,153,.3);
  color:#34d399;border-radius:6px;padding:8px 14px;font-family:'IBM Plex Mono',monospace;font-size:11px;}
.entity-warn{background:rgba(251,191,36,.1);border:1px solid rgba(251,191,36,.3);
  color:#fbbf24;border-radius:6px;padding:8px 14px;font-family:'IBM Plex Mono',monospace;font-size:11px;}
.entity-danger{background:rgba(248,113,113,.1);border:1px solid rgba(248,113,113,.3);
  color:#f87171;border-radius:6px;padding:8px 14px;font-family:'IBM Plex Mono',monospace;font-size:11px;}

/* ── Result Blocks ── */
.result-block{background:rgba(7,11,18,.9);border:1px solid rgba(56,189,248,.15);
  border-radius:12px;padding:20px;margin:12px 0;position:relative;}
.result-block::before{content:'';position:absolute;top:0;left:0;right:0;height:1px;
  background:linear-gradient(90deg,transparent,rgba(56,189,248,.4),transparent);}
.result-engine{font-family:'IBM Plex Mono',monospace;font-size:9px;letter-spacing:2px;
  color:#38bdf8;text-transform:uppercase;margin-bottom:10px;}
.result-content{font-size:13px;line-height:1.85;color:#cbd5e1;white-space:pre-wrap;}

/* ── Input Zones ── */
.upload-zone{border:2px dashed #1e293b;border-radius:12px;padding:30px;
  text-align:center;background:rgba(15,23,42,.5);transition:border-color .2s;}
.upload-zone:hover{border-color:#38bdf8;}

/* ── Verdict Bar ── */
.verdict-bar{display:flex;align-items:center;gap:16px;padding:16px 20px;
  border-radius:10px;margin:16px 0;}
.verdict-pass{background:rgba(52,211,153,.08);border:1px solid rgba(52,211,153,.3);}
.verdict-warn{background:rgba(251,191,36,.08);border:1px solid rgba(251,191,36,.3);}
.verdict-fail{background:rgba(248,113,113,.08);border:1px solid rgba(248,113,113,.3);}
.verdict-icon{font-size:28px;}
.verdict-text{font-family:'IBM Plex Mono',monospace;font-size:14px;font-weight:700;}
.verdict-sub{font-size:12px;color:#64748b;margin-top:2px;}

/* ── Pipeline Visual ── */
.pipeline{display:flex;align-items:center;gap:0;padding:16px;overflow-x:auto;margin-bottom:16px;}
.pipe-node{display:flex;flex-direction:column;align-items:center;gap:6px;min-width:90px;}
.pipe-node-icon{width:42px;height:42px;border-radius:10px;display:flex;align-items:center;
  justify-content:center;font-size:18px;border:1px solid #1e293b;background:rgba(15,23,42,.9);
  transition:all .3s;}
.pipe-node-icon.active{border-color:#38bdf8;box-shadow:0 0 16px rgba(56,189,248,.4);
  background:rgba(56,189,248,.08);}
.pipe-node-icon.done{border-color:#34d399;background:rgba(52,211,153,.08);}
.pipe-node-label{font-family:'IBM Plex Mono',monospace;font-size:9px;color:#475569;
  text-align:center;text-transform:uppercase;letter-spacing:.3px;}
.pipe-arrow{color:#1e293b;font-size:16px;padding:0 4px;flex-shrink:0;margin-bottom:20px;}

/* ── Misc ── */
.divider{height:1px;background:linear-gradient(90deg,transparent,#1e293b,transparent);margin:20px 0;}
.section-title{font-family:'IBM Plex Mono',monospace;font-size:11px;font-weight:700;
  color:#475569;letter-spacing:2px;text-transform:uppercase;margin:20px 0 12px;
  padding-bottom:6px;border-bottom:1px solid #1e293b;}
.tip-box{background:rgba(99,102,241,.07);border:1px solid rgba(99,102,241,.2);
  border-radius:8px;padding:12px 16px;font-size:12px;color:#94a3b8;margin:10px 0;}
.tip-box b{color:#818cf8;}

.stButton>button{font-family:'IBM Plex Mono',monospace!important;font-size:12px!important;
  font-weight:600!important;letter-spacing:.5px!important;}
div.stButton>button:first-child{
  background:linear-gradient(90deg,#0ea5e9,#6366f1)!important;color:#fff!important;
  border:none!important;box-shadow:0 4px 20px rgba(14,165,233,.3)!important;}
div.stButton>button:first-child:hover{
  transform:translateY(-1px)!important;box-shadow:0 6px 28px rgba(14,165,233,.5)!important;}
/* ── Mobile Previewer ── */
.mobile-preview-box {
  background: #18191a;
  border: 1px solid #3a3b3c;
  border-radius: 12px;
  max-width: 400px;
  margin: 16px auto;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  color: #e4e6eb;
  overflow: hidden;
  text-align: left;
}
.mp-header {
  display: flex;
  align-items: center;
  padding: 12px;
  gap: 10px;
}
.mp-avatar {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: #242526;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 18px;
  color: #38bdf8;
  border: 1px solid #38bdf840;
}
.mp-header-text {
  display: flex;
  flex-direction: column;
}
.mp-author {
  font-weight: 600;
  font-size: 14px;
  color: #e4e6eb;
}
.mp-sub {
  font-size: 11px;
  color: #b0b3b8;
  display: flex;
  align-items: center;
  gap: 4px;
}
.mp-body {
  padding: 0 12px 10px;
  font-size: 13px;
  line-height: 1.5;
  color: #e4e6eb;
  white-space: pre-wrap;
}
.mp-image {
  width: 100%;
  aspect-ratio: 1.91/1;
  background: #242526;
  object-fit: cover;
}
.mp-footer {
  background: #242526;
  padding: 10px 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid #393a3b;
}
.mp-footer-text {
  display: flex;
  flex-direction: column;
  flex: 1;
  padding-right: 8px;
}
.mp-site {
  font-size: 11px;
  color: #b0b3b8;
  text-transform: uppercase;
  letter-spacing: .5px;
}
.mp-headline {
  font-weight: 600;
  font-size: 14px;
  color: #e4e6eb;
  margin-top: 2px;
}
.mp-cta-btn {
  background: #3a3b3c;
  color: #e4e6eb;
  padding: 6px 12px;
  border-radius: 6px;
  font-weight: 600;
  font-size: 12px;
  border: none;
  white-space: nowrap;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════
_AD_DEFAULTS = {
    "andro_mode":           0,
    "andro_results":        {},
    "andro_running":        False,
    "andro_images_b64":     [],   # list of (filename, b64, mime)
    "andro_copy_headline":  "",
    "andro_copy_body":      "",
    "andro_copy_cta":       "",
    "andro_comp_images":    [],
    "andro_ab_a":           [],
    "andro_ab_b":           [],
    "andro_engine_choice":  ANDROMEDA_ENGINE,
    "andro_history":        [],
}
for k, v in _AD_DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════
# HELPER — API CALLS
# ══════════════════════════════════════════════════════════════════
@st.cache_data(ttl=300)
def _best_gemini_model(key):
    try:
        r = requests.get(
            f"https://generativelanguage.googleapis.com/v1beta/models?key={key}",
            timeout=10)
        if r.status_code == 200:
            avail = [m["name"] for m in r.json().get("models", [])
                     if "generateContent" in m.get("supportedGenerationMethods", [])]
            for p in [
                "models/gemini-2.5-flash-preview-05-20",
                "models/gemini-2.5-flash",
                "models/gemini-2.0-flash",
                "models/gemini-1.5-flash-latest",
            ]:
                if p in avail:
                    return p
            return avail[0] if avail else "models/gemini-2.0-flash"
    except:
        pass
    return "models/gemini-2.0-flash"


def call_gemini_vision(prompt: str, images_b64: list, max_tokens: int = 16384) -> str:
    """images_b64: list of (filename, b64_str, mime_type)"""
    if not GEMINI_KEY:
        return "❌ ไม่พบ GOOGLE_API_KEY ใน secrets.toml"
    model = _best_gemini_model(GEMINI_KEY)
    url = f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={GEMINI_KEY}"
    parts = [{"text": prompt}]
    for _, b64, mime in images_b64[:10]:
        parts.append({"inlineData": {"mimeType": mime, "data": b64}})
    payload = {
        "contents": [{"parts": parts}],
        "generationConfig": {"temperature": 0.6, "maxOutputTokens": max_tokens}
    }
    try:
        r = requests.post(url, json=payload, timeout=180)
        if r.status_code == 200:
            return r.json()["candidates"][0]["content"]["parts"][0].get("text", "")
        return f"❌ Gemini Error {r.status_code}: {r.text[:300]}"
    except Exception as e:
        return f"❌ Connection Error: {str(e)[:150]}"


def call_claude_vision(prompt: str, images_b64: list, max_tokens: int = 4096) -> str:
    """images_b64: list of (filename, b64_str, mime_type)"""
    if not ANTHROPIC_KEY:
        return "❌ ไม่พบ ANTHROPIC_API_KEY ใน secrets.toml"
    content = []
    for _, b64, mime in images_b64[:5]:
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": mime, "data": b64}
        })
    content.append({"type": "text", "text": prompt})
    payload = {
        "model": "claude-haiku-4-5",
        "max_tokens": max_tokens,
        "messages": [{"role": "user", "content": content}]
    }
    headers = {
        "x-api-key": ANTHROPIC_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    try:
        r = requests.post("https://api.anthropic.com/v1/messages",
                          headers=headers, json=payload, timeout=120)
        if r.status_code == 200:
            return r.json()["content"][0]["text"]
        return f"❌ Claude Error {r.status_code}: {r.text[:300]}"
    except Exception as e:
        return f"❌ Connection Error: {str(e)[:150]}"


def call_engine(prompt: str, images_b64: list = None, engine: str = None, max_tokens: int = 8192) -> str:
    """Smart router — เลือก engine ตาม setting"""
    eng = engine or st.session_state.andro_engine_choice
    imgs = images_b64 or []
    if eng == "claude":
        return call_claude_vision(prompt, imgs, max_tokens)
    elif eng == "both":
        g = call_gemini_vision(prompt, imgs, max_tokens)
        c = call_claude_vision(prompt, imgs, min(max_tokens, 4096))
        return f"**🔵 Gemini Analysis:**\n{g}\n\n{'─'*60}\n\n**🟣 Claude Analysis:**\n{c}"
    else:  # gemini
        return call_gemini_vision(prompt, imgs, max_tokens)


def image_to_b64(uploaded_file) -> tuple:
    """Convert Streamlit UploadedFile → (name, b64_str, mime)"""
    b = uploaded_file.read()
    b64 = base64.b64encode(b).decode()
    mime = uploaded_file.type or "image/jpeg"
    return (uploaded_file.name, b64, mime)


def score_color_class(s: int) -> str:
    if s >= 70: return "high"
    if s >= 45: return "mid"
    return "low"


def score_bar_html(label: str, score: int) -> str:
    cls = score_color_class(score)
    return f"""
<div class="score-card">
  <div class="score-label">{label}</div>
  <div class="score-num score-{cls}">{score}</div>
  <div class="score-bar"><div class="score-fill score-fill-{cls}" style="width:{score}%"></div></div>
</div>"""


def save_to_history(mode_name: str, summary: str):
    st.session_state.andro_history.append({
        "ts": datetime.now().strftime("%d/%m %H:%M"),
        "mode": mode_name,
        "summary": summary[:200]
    })
    st.session_state.andro_history = st.session_state.andro_history[-50:]


def render_facebook_preview(headline, body, cta, image_b64=None, mime=None):
    img_tag = ""
    if image_b64:
        img_tag = f'<img class="mp-image" src="data:{mime};base64,{image_b64}">'
    else:
        img_tag = '<div class="mp-image" style="background:linear-gradient(135deg,#0d1117,#1f2937);display:flex;align-items:center;justify-content:center;color:#475569;font-size:12px;font-family:monospace;height:210px;">[ MOCKUP AD IMAGE ]</div>'
        
    html = f"""
    <div class="mobile-preview-box">
      <div class="mp-header">
        <div class="mp-avatar">A</div>
        <div class="mp-header-text">
          <div class="mp-author">AQUALINE</div>
          <div class="mp-sub">Sponsored · 🌐</div>
        </div>
      </div>
      <div class="mp-body">{body or 'เนื้อหาโฆษณา (Body Copy)...'}</div>
      {img_tag}
      <div class="mp-footer">
        <div class="mp-footer-text">
          <div class="mp-site">AQUALINE.CO.TH</div>
          <div class="mp-headline">{headline or 'หัวข้อโฆษณา (Headline)...'}</div>
        </div>
        <button class="mp-cta-btn">{cta or 'ส่งข้อความ'}</button>
      </div>
    </div>
    """
    return html

def retrieve_relevant_memories(query_text: str, memory_text: str, top_n: int = 7) -> str:
    if not memory_text.strip() or not query_text.strip():
        return memory_text
    bullets = []
    for line in memory_text.split("\n"):
        line_s = line.strip()
        if line_s.startswith(("•", "-", "*")) or (line_s and line_s[0].isdigit() and "." in line_s[:3]):
            bullets.append(line_s)
    if not bullets:
        return memory_text
    keywords = [w.lower() for w in re.findall(r"\w+", query_text) if len(w) > 2]
    if not keywords:
        return "\n".join(bullets[:top_n])
    scored_bullets = []
    for bullet in bullets:
        score = 0
        bullet_lower = bullet.lower()
        for kw in keywords:
            if kw in bullet_lower:
                score += 1.5
        scored_bullets.append((score, bullet))
    scored_bullets.sort(key=lambda x: x[0], reverse=True)
    relevant = [b for s, b in scored_bullets if s > 0]
    if not relevant:
        relevant = bullets[:top_n]
    else:
        relevant = relevant[:top_n]
    return "\n".join(relevant)

def get_project_context_for_prompt(query_text: str = "") -> str:
    if "vault" not in st.session_state or st.session_state.current_project not in st.session_state.vault:
        return ""
    p_data = st.session_state.vault[st.session_state.current_project]
    parts = []
    memory = p_data.get("memory", "").strip()
    pinned = [f.strip() for f in p_data.get("pinned_facts", []) if f.strip()]
    perf_list = p_data.get("ad_performance", [])

    if pinned:
        parts.append("📌 ข้อเท็จจริงสำคัญของแบรนด์:\n" + "\n".join(f"• {f}" for f in pinned))
    if memory:
        filtered = retrieve_relevant_memories(query_text, memory)
        parts.append(f"🧠 ข้อมูลโปรเจกต์ที่เกี่ยวข้อง:\n{filtered}")
    if perf_list:
        perf_lines = []
        for p in perf_list[-8:]:
            perf_lines.append(f"• [ยิงจริง {p.get('date')}] CTR: {p.get('ctr')}% | CPM: {p.get('cpm')}B | Conv: {p.get('conversions')} ({p.get('notes', '')})")
        parts.append("📈 สถิติผลงานโฆษณาจริงที่เคยยิงแล้ว (Closed-Loop Data):\n" + "\n".join(perf_lines))
        
    if not parts:
        return ""
    return "\n\n[PROJECT CONTEXT & PAST PERFORMANCE LEARNINGS]\n" + "\n\n".join(parts) + "\n[/PROJECT CONTEXT]\n\n"

# ══════════════════════════════════════════════════════════════════
# META AI SYSTEM PROMPTS — จำลองการคิดของ Meta Andromeda Engine
# ══════════════════════════════════════════════════════════════════
def _base_meta_context(query_text: str = "") -> str:
    proj_ctx = get_project_context_for_prompt(query_text)
    return f"""คุณคือ Andromeda — AI ที่จำลองการทำงานของ Meta Andromeda Engine + GEM + Lattice
{proj_ctx}
ระบบของ Meta ประเมิน Ads ใน 3 มิติหลัก:
1. Quality Ranking (0-100): คุณภาพ creative โดยรวม — production quality, ความน่าเชื่อถือ, post-click experience
2. Engagement Rate Ranking (0-100): โอกาสที่คนจะ click/share/react — hook strength, emotional trigger, scroll-stop power
3. Conversion Rate Ranking (0-100): โอกาสที่คนจะ convert — urgency, CTA clarity, offer value, social proof

นอกจากนี้ Meta ใช้ Entity ID ตรวจว่า creative คล้ายกันเกินไปหรือไม่ (ถ้าคล้าย → ได้ "ตั๋ว" ประมูลเดียวกัน → ลด reach)

ตอบเป็นภาษาไทย ใช้ emoji ประกอบ ให้คะแนนชัดเจน และให้คำแนะนำที่ปฏิบัติได้จริงเสมอ
"""

def make_dynamic_prompt(base_prompt: str, query_text: str) -> str:
    load_time_context = _base_meta_context("")
    dynamic_context = _base_meta_context(query_text)
    if load_time_context in base_prompt:
        return base_prompt.replace(load_time_context, dynamic_context)
    return dynamic_context + base_prompt

PROMPT_MODE1_IMAGE = _base_meta_context() + """
โหมด: Creative Audit — วิเคราะห์ภาพ Ad ที่ได้รับ

วิเคราะห์ภาพ Ad ที่แนบมานี้ในฐานะ Meta Andromeda Engine ตามโครงสร้างต่อไปนี้:

═══ ANDROMEDA SCAN REPORT ═══

**📊 คะแนน 3 มิติ (Meta Framework):**
- Quality Ranking: [0-100] — อธิบายเหตุผล
- Engagement Rate Ranking: [0-100] — อธิบายเหตุผล  
- Conversion Rate Ranking: [0-100] — อธิบายเหตุผล

**🧬 Entity ID Risk Assessment:**
ประเมินว่า creative นี้มีความเสี่ยงที่ Meta จะจัดเป็น Entity เดียวกับ Ad อื่นๆ ในระดับไหน
(ต่ำ / กลาง / สูง) + เหตุผล

**🪝 Hook Analysis (3 วินาทีแรก):**
- จุดที่ดึงดูดสายตาก่อน
- ความแข็งแกร่งของ Hook (1-10)
- สิ่งที่ควรปรับปรุง

**⚠️ Policy Risk Check:**
ตรวจสอบว่ามีเนื้อหาที่อาจผิด Meta Ads Policy หรือไม่

**✅ สิ่งที่ดีอยู่แล้ว:**
[bullet points]

**🔧 Action Items ก่อนยิง:**
เรียงลำดับจากสำคัญที่สุด

**🎯 Overall Andromeda Score: [0-100]**
[สรุปว่า Ad นี้พร้อมยิงหรือไม่ และทำไม]
"""

PROMPT_MODE2_COPY = _base_meta_context() + """
โหมด: Copy Analyzer — วิเคราะห์ข้อความโฆษณา

วิเคราะห์ Ad Copy ที่ให้มาตามโครงสร้าง Meta GEM Framework:

**📝 Copy ที่ได้รับ:**
{copy_text}

═══ COPY AUDIT REPORT ═══

**🪝 Hook Strength Analysis:**
- บรรทัดแรก/ประโยคแรกแข็งแกร่งแค่ไหน (1-10)
- เหตุผล + เปรียบเทียบกับ benchmark ของ Meta

**📊 คะแนน Copy ใน 3 มิติ:**
- Quality Score: [0-100]
- Engagement Score: [0-100]
- Conversion Score: [0-100]

**🚫 Forbidden Word / Policy Check:**
ตรวจหาคำหรือข้อความที่อาจถูก Meta reject

**💡 ปัญหาที่พบ:**
[bullet points]

**✍️ Copy ที่ปรับปรุงแล้ว (3 เวอร์ชัน):**

Version A — Hook เน้นปัญหา:
> [Headline]
> [Body]
> [CTA]

Version B — Hook เน้นประโยชน์:
> [Headline]
> [Body]
> [CTA]

Version C — Hook เน้น Social Proof:
> [Headline]
> [Body]
> [CTA]

**🎯 คำแนะนำสุดท้าย:**
"""

PROMPT_MODE3_FULL = _base_meta_context() + """
โหมด: Full Ad Simulator — จำลองการประเมินของ Meta แบบเต็ม (ภาพ + ข้อความ)

วิเคราะห์ Ad ทั้งใบ ทั้งภาพและข้อความ ในฐานะที่คุณคือ Meta Ads Delivery System:

**Ad Copy ที่แนบ:**
{copy_text}

═══ FULL AD SIMULATION REPORT ═══

**🔭 Andromeda Retrieval Score:**
โอกาสที่ Ad นี้จะถูก Andromeda เลือกเข้าสู่ขั้นตอน Ranking: [%]

**📊 Final Composite Scores:**
- Quality Ranking: [0-100] / เปรียบเทียบ: Average / Above Average / Top 10%
- Engagement Rate Ranking: [0-100] / เปรียบเทียบ: ...
- Conversion Rate Ranking: [0-100] / เปรียบเทียบ: ...

**🧬 Creative-Copy Synergy:**
ภาพและข้อความ "ไปด้วยกัน" ดีแค่ไหน และส่งเสริมกันหรือขัดกัน

**📈 Predicted Performance Range:**
- CTR Estimate: [X.X% - X.X%]
- CPM Estimate: [XXX - XXXB บาท]
- Engagement Rate: [X.X% - X.X%]
(อ้างอิงจาก benchmark อุตสาหกรรมวัสดุก่อสร้างไทย)

**🚀 Placement Recommendation:**
แนะนำ Placement ที่เหมาะที่สุดกับ Ad นี้ (Feed / Reels / Story / Audience Network)

**📋 Pre-Flight Checklist:**
☐ [สิ่งที่ต้องตรวจก่อนยิง]
☐ ...

**🏆 VERDICT:** [READY TO LAUNCH ✅ / NEEDS REVISION ⚠️ / DO NOT LAUNCH ❌]
เหตุผล + Action Items ด่วน (ถ้ามี)
"""

PROMPT_MODE4_COMPETITOR = _base_meta_context() + """
โหมด: Competitor Ad Spy — วิเคราะห์โฆษณาคู่แข่ง

วิเคราะห์โฆษณาของคู่แข่งที่แนบมา และสร้าง Counter-Strategy สำหรับ AQUALINE:

═══ COMPETITOR INTELLIGENCE REPORT ═══

**🔍 Creative Breakdown:**
วิเคราะห์ว่าทำไม Ad นี้ถึงได้ผล (หรือไม่ได้ผล)

**📊 ประเมิน Andromeda Score ของคู่แข่ง:**
- Quality: [0-100]
- Engagement: [0-100]
- Conversion: [0-100]

**💡 What Makes It Work:**
สิ่งที่คู่แข่งทำได้ดี (เรียนรู้ได้)

**⚔️ Weakness ที่ AQUALINE เอาเปรียบได้:**
จุดอ่อนของ Ad คู่แข่งที่ AQUALINE สามารถโจมตีได้

**🎯 Counter-Strategy สำหรับ AQUALINE:**

Creative Direction ที่แนะนำ:
> [อธิบาย Concept ที่ชนะคู่แข่งได้]

Hook ที่แนะนำ:
> [Headline ที่จะทำให้ AQUALINE โดดเด่นกว่า]

USP ที่ควรเน้น:
> [จุดขายที่คู่แข่งไม่มี]

**📈 Estimated Advantage:**
ถ้า AQUALINE ทำตาม Counter-Strategy นี้ จะได้เปรียบคู่แข่งในด้านไหนบ้าง
"""

PROMPT_MODE5_AB = _base_meta_context() + """
โหมด: A/B Pre-Check — ทำนายผลก่อนทดสอบจริง

วิเคราะห์ Ad A (ภาพแรก) vs Ad B (ภาพที่สอง) และทำนายผลก่อนยิงจริง:

═══ A/B PRE-CHECK REPORT ═══

**📊 Ad A — Andromeda Scores:**
- Quality: [0-100]
- Engagement: [0-100]
- Conversion: [0-100]
- Overall: [0-100]

**📊 Ad B — Andromeda Scores:**
- Quality: [0-100]
- Engagement: [0-100]
- Conversion: [0-100]
- Overall: [0-100]

**🏆 Predicted Winner: Ad [A/B]**
เหตุผล 3-5 ข้อที่ชัดเจน

**🧬 Entity ID Check:**
A และ B ต่างกันพอให้ Meta มอง Entity ID ต่างกันหรือไม่?
ถ้าไม่ต่าง → คำแนะนำในการปรับให้ต่างพอ

**⚡ จุดแข็งของแต่ละตัว:**
Ad A ชนะในด้าน: ...
Ad B ชนะในด้าน: ...

**💎 Ad C — Recommended Variant (ดีกว่าทั้ง A และ B):**
Creative Direction:
> [อธิบาย Concept ที่รวมจุดแข็งของทั้งคู่]

Copy ที่แนะนำ:
> Headline: [...]
> Body: [...]
> CTA: [...]

**📋 Testing Recommendation:**
วิธี A/B Test ที่ถูกต้องตาม Meta best practices 2025
"""

# ══════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<div class="andro-header">
  <div>
    <div class="andro-title">
      🔭 ANDROMEDA
      <span class="andro-badge">PRE-MEETING AUDITOR</span>
      <span class="andro-badge meta-badge">META AI ENGINE</span>
    </div>
    <div class="andro-subtitle">Omni Scanner · Ad Intelligence · Powered by Gemini Vision + Claude Vision</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# SIDEBAR — Engine Selector + History
# ══════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 🔭 Andromeda Control")
    st.markdown("---")

    # Project Selector
    st.markdown('<div class="section-title">📂 เลือกแฟ้มงาน (Project)</div>', unsafe_allow_html=True)
    proj_list = list(st.session_state.vault.keys())
    selected_p = st.selectbox(
        "เลือกแฟ้มงาน:",
        proj_list,
        index=proj_list.index(st.session_state.current_project) if st.session_state.current_project in proj_list else 0,
        key="andro_proj_selector"
    )
    st.session_state.current_project = selected_p

    # Engine selector
    st.markdown('<div class="section-title">AI Engine</div>', unsafe_allow_html=True)
    engine_options = []
    if GEMINI_KEY:   engine_options.append("gemini")
    if ANTHROPIC_KEY: engine_options.append("claude")
    if GEMINI_KEY and ANTHROPIC_KEY: engine_options.append("both")
    if not engine_options: engine_options = ["gemini"]

    engine_labels = {"gemini": "🔵 Gemini Vision", "claude": "🟣 Claude Vision", "both": "⚡ Both (Dual Analysis)"}
    chosen = st.selectbox(
        "เลือก Engine:",
        engine_options,
        index=engine_options.index(st.session_state.andro_engine_choice)
              if st.session_state.andro_engine_choice in engine_options else 0,
        format_func=lambda x: engine_labels.get(x, x)
    )
    st.session_state.andro_engine_choice = chosen

    # 📈 CLOSED-LOOP PERFORMANCE LEARNER FORM
    st.markdown('<div class="section-title">📈 Performance Feedback Loop</div>', unsafe_allow_html=True)
    with st.expander("📝 บันทึกผลลัพธ์ยิงจริง"):
        fb_date = st.date_input("วันที่ลงโฆษณา:", key="fb_date")
        fb_ctr = st.number_input("CTR (%) ที่ได้จริง:", min_value=0.0, max_value=100.0, step=0.1, key="fb_ctr")
        fb_cpm = st.number_input("CPM (บาท):", min_value=0.0, step=1.0, key="fb_cpm")
        fb_conv = st.number_input("Conversions (ครั้ง):", min_value=0, step=1, key="fb_conv")
        fb_notes = st.text_input("โน้ตย่อยการเรียนรู้:", placeholder="เช่น รูปบ้านไม้ปังกว่า", key="fb_notes")
        
        if st.button("💾 บันทึกความรู้เข้า AI", use_container_width=True, key="save_feedback_btn"):
            p_data = st.session_state.vault[st.session_state.current_project]
            if "ad_performance" not in p_data:
                p_data["ad_performance"] = []
            
            p_data["ad_performance"].append({
                "date": fb_date.strftime("%d/%m/%Y"),
                "ctr": fb_ctr,
                "cpm": fb_cpm,
                "conversions": fb_conv,
                "notes": fb_notes
            })
            save_vault(st.session_state.vault)
            st.success("✅ บันทึกประวัติและผลลัพธ์โฆษณาเรียบร้อยแล้ว!")
            st.rerun()

    # API status
    st.markdown('<div class="section-title">API Status</div>', unsafe_allow_html=True)
    st.markdown(f"{'🟢' if GEMINI_KEY else '🔴'} Gemini: {'Connected' if GEMINI_KEY else 'No Key'}")
    st.markdown(f"{'🟢' if ANTHROPIC_KEY else '🔴'} Claude: {'Connected' if ANTHROPIC_KEY else 'No Key'}")

    if not GEMINI_KEY and not ANTHROPIC_KEY:
        st.error("⚠️ ไม่พบ API Key ใดเลย\nไปตั้งค่าที่ Settings หน้า 14")

    st.markdown("---")

    # History
    st.markdown('<div class="section-title">📋 ประวัติการ Scan</div>', unsafe_allow_html=True)
    if st.session_state.andro_history:
        for h in reversed(st.session_state.andro_history[-10:]):
            st.markdown(f"**{h['ts']}** — {h['mode']}\n_{h['summary'][:60]}..._")
            st.markdown("---")
    else:
        st.caption("ยังไม่มีประวัติ")

    if st.button("🗑️ ล้างประวัติ", use_container_width=True):
        st.session_state.andro_history = []
        st.rerun()

# ══════════════════════════════════════════════════════════════════
# MODE SELECTOR
# ══════════════════════════════════════════════════════════════════
MODES = [
    ("🔬", "Creative\nAudit", "วิเคราะห์ภาพ Ad"),
    ("📝", "Copy\nAnalyzer", "วิเคราะห์ข้อความ"),
    ("🎯", "Full Ad\nSimulator", "ภาพ + ข้อความ"),
    ("⚔️", "Competitor\nSpy", "วิเคราะห์คู่แข่ง"),
    ("🧪", "A/B\nPre-Check", "ทำนาย A/B"),
]

st.markdown('<div class="section-title">เลือกโหมดการวิเคราะห์</div>', unsafe_allow_html=True)
mode_cols = st.columns(5)
for i, (icon, name, desc) in enumerate(MODES):
    with mode_cols[i]:
        is_active = st.session_state.andro_mode == i
        active_class = "active" if is_active else ""
        st.markdown(f"""
        <div class="mode-card {active_class}">
          <div class="mode-icon">{icon}</div>
          <div class="mode-name">{name}</div>
        </div>""", unsafe_allow_html=True)
        if st.button(desc, key=f"mode_btn_{i}", use_container_width=True):
            st.session_state.andro_mode = i
            st.rerun()

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# META PIPELINE VISUAL
# ══════════════════════════════════════════════════════════════════
pipeline_steps = [
    ("📥", "INPUT", "Creative/Copy"),
    ("🔭", "ANDROMEDA", "Retrieval Scan"),
    ("💎", "GEM", "Ranking Score"),
    ("🕸️", "LATTICE", "Journey Map"),
    ("📋", "REPORT", "Action Plan"),
]
pipe_html = '<div class="pipeline">'
for i, (icon, label, desc) in enumerate(pipeline_steps):
    cls = "done" if st.session_state.andro_results else ("active" if i == 0 else "")
    pipe_html += f"""
    <div class="pipe-node">
      <div class="pipe-node-icon {cls}">{icon}</div>
      <div class="pipe-node-label">{label}<br><span style="color:#1e293b;font-size:8px">{desc}</span></div>
    </div>"""
    if i < len(pipeline_steps) - 1:
        pipe_html += '<div class="pipe-arrow">→</div>'
pipe_html += '</div>'
st.markdown(pipe_html, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# MODE 0 — Creative Audit (Image Analysis)
# ══════════════════════════════════════════════════════════════════
if st.session_state.andro_mode == 0:
    st.markdown("## 🔬 Creative Audit — วิเคราะห์ภาพ Ad")
    st.markdown("""<div class="tip-box">
    <b>📡 วิธีใช้:</b> อัพโหลดภาพ Ad 1-10 ใบ → Andromeda จะวิเคราะห์ตาม Meta 3-Dimension Framework
    + ตรวจ Entity ID Risk + Hook Strength + Policy Check<br>
    <b>💡 Tip:</b> ถ้าอัพหลายภาพ ระบบจะตรวจด้วยว่าภาพ "คล้ายกันเกินไป" หรือเปล่า (Entity ID Warning)
    </div>""", unsafe_allow_html=True)

    uploaded = st.file_uploader(
        "อัพโหลดภาพ Ad (PNG, JPG, WEBP — สูงสุด 10 ใบ)",
        type=["png", "jpg", "jpeg", "webp"],
        accept_multiple_files=True,
        key="mode0_upload"
    )
    if uploaded:
        st.session_state.andro_images_b64 = [image_to_b64(f) for f in uploaded[:10]]
        cols = st.columns(min(len(uploaded), 5))
        for i, f in enumerate(uploaded[:5]):
            with cols[i]:
                f.seek(0)
                st.image(f, caption=f.name[:20], use_container_width=True)
        if len(uploaded) > 5:
            st.caption(f"... และอีก {len(uploaded)-5} ภาพ")

    extra_context = st.text_area(
        "📝 ข้อมูลเพิ่มเติม (ไม่บังคับ) — เช่น กลุ่มเป้าหมาย, วัตถุประสงค์, งบประมาณ",
        placeholder="เช่น: ยิงหา Lookalike 1% จากลูกค้าเก่า, งบ 300 บาท/วัน, เป้าหมาย Lead Generation",
        height=80, key="mode0_extra"
    )

    if st.button("🔭 START ANDROMEDA SCAN", use_container_width=True, key="mode0_run",
                 disabled=not st.session_state.andro_images_b64):
        with st.spinner("🔭 Andromeda Engine กำลังสแกน..."):
            imgs = st.session_state.andro_images_b64
            prompt = make_dynamic_prompt(PROMPT_MODE1_IMAGE, extra_context)
            if extra_context:
                prompt += f"\n\n**ข้อมูลเพิ่มเติมจากผู้ใช้:** {extra_context}"
            if len(imgs) > 1:
                prompt += f"\n\n**หมายเหตุ:** มีภาพ {len(imgs)} ใบ — วิเคราะห์แต่ละใบ และเปรียบเทียบ Entity ID Risk ระหว่างภาพด้วย"
            result = call_engine(prompt, imgs)
            st.session_state.andro_results["mode0"] = result
            save_to_history("Creative Audit", result[:100])

    if "mode0" in st.session_state.andro_results:
        st.markdown('<div class="section-title">📋 Andromeda Scan Report</div>', unsafe_allow_html=True)
        st.markdown(f"""<div class="result-block">
        <div class="result-engine">🔭 ANDROMEDA · {engine_labels.get(st.session_state.andro_engine_choice, '')} · {datetime.now().strftime("%H:%M:%S")}</div>
        <div class="result-content">{st.session_state.andro_results["mode0"]}</div>
        </div>""", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.download_button("📥 Download Report",
                               st.session_state.andro_results["mode0"],
                               file_name=f"andromeda_creative_audit_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                               use_container_width=True)
        with col2:
            if st.button("🔄 Scan ใหม่", use_container_width=True, key="mode0_reset"):
                del st.session_state.andro_results["mode0"]
                st.rerun()

# ══════════════════════════════════════════════════════════════════
# MODE 1 — Copy Analyzer
# ══════════════════════════════════════════════════════════════════
elif st.session_state.andro_mode == 1:
    st.markdown("## 📝 Copy Analyzer — วิเคราะห์ข้อความโฆษณา")
    st.markdown("""<div class="tip-box">
    <b>📡 วิธีใช้:</b> วาง Headline, Body Copy, และ CTA → Andromeda ตรวจ Hook strength,
    คำต้องห้ามของ Meta, และสร้าง Copy ที่ดีกว่า 3 เวอร์ชัน<br>
    <b>💡 Tip:</b> ยิ่งใส่ข้อมูลครบ ผลวิเคราะห์ยิ่งแม่นยำ
    </div>""", unsafe_allow_html=True)

    col_h, col_b = st.columns([1, 2])
    with col_h:
        headline = st.text_input("📢 Headline:", placeholder="เช่น: หลังคา AQUALINE แข็งแกร่ง 30 ปี",
                                  key="copy_headline")
        cta = st.text_input("🎯 CTA:", placeholder="เช่น: ขอใบเสนอราคาฟรี",
                             key="copy_cta")
        objective = st.selectbox("🎪 Campaign Objective:",
                                  ["Lead Generation", "Traffic", "Awareness", "Conversion", "Engagement"],
                                  key="copy_obj")
    with col_b:
        body = st.text_area("✍️ Body Copy:", height=120,
                             placeholder="เช่น: ปัญหาหลังคารั่วทำให้คุณเครียดทุกหน้าฝน? AQUALINE มีคำตอบ...",
                             key="copy_body")

    target_audience = st.text_input("👥 กลุ่มเป้าหมาย (ไม่บังคับ):",
                                     placeholder="เช่น: เจ้าของบ้าน อายุ 30-50 ปี ภาคกลาง",
                                     key="copy_audience")

    copy_compiled = f"Headline: {headline}\n\nBody Copy:\n{body}\n\nCTA: {cta}"
    if target_audience:
        copy_compiled += f"\n\nกลุ่มเป้าหมาย: {target_audience}"
    if objective:
        copy_compiled += f"\nวัตถุประสงค์: {objective}"

    if st.button("🔭 ANALYZE COPY", use_container_width=True, key="mode1_run",
                 disabled=not headline and not body):
        with st.spinner("📝 วิเคราะห์ Ad Copy..."):
            prompt = make_dynamic_prompt(PROMPT_MODE2_COPY.replace("{copy_text}", copy_compiled), copy_compiled)
            result = call_engine(prompt, [], max_tokens=8192)
            st.session_state.andro_results["mode1"] = result
            save_to_history("Copy Analyzer", result[:100])

    if "mode1" in st.session_state.andro_results:
        col_rep, col_mock = st.columns([1.2, 0.8])
        with col_rep:
            st.markdown('<div class="section-title">📋 Copy Audit Report</div>', unsafe_allow_html=True)
            st.markdown(f"""<div class="result-block">
            <div class="result-engine">📝 COPY ANALYZER · {engine_labels.get(st.session_state.andro_engine_choice, '')} · {datetime.now().strftime("%H:%M:%S")}</div>
            <div class="result-content">{st.session_state.andro_results["mode1"]}</div>
            </div>""", unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                st.download_button("📥 Download Report",
                                   st.session_state.andro_results["mode1"],
                                   file_name=f"andromeda_copy_audit_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                                   use_container_width=True)
            with col2:
                if st.button("🔄 วิเคราะห์ใหม่", use_container_width=True, key="mode1_reset"):
                    del st.session_state.andro_results["mode1"]
                    st.rerun()
                    
        with col_mock:
            st.markdown('<div class="section-title">📱 Live Facebook Ad Mockup</div>', unsafe_allow_html=True)
            mock_headline = st.text_input("Preview Headline:", value=headline, key="m1_prev_h")
            mock_body = st.text_area("Preview Body Copy:", value=body, height=120, key="m1_prev_b")
            mock_cta = st.text_input("Preview CTA:", value=cta or "ส่งข้อความ", key="m1_prev_c")
            st.markdown(render_facebook_preview(mock_headline, mock_body, mock_cta), unsafe_allow_html=True)
            
            if st.button("🏭 ส่งข้อมูลนี้ไปหน้า Content Factory", use_container_width=True, key="m1_send_cf"):
                st.session_state.pname = st.session_state.current_project
                st.session_state.pdesc = mock_body
                st.session_state.cf_web_data = f"Headline: {mock_headline}\nBody: {mock_body}\nCTA: {mock_cta}\n\n[Andromeda Copy Analyzer Feedback]:\n{st.session_state.andro_results['mode1']}"
                st.success("✅ ส่งข้อมูลบรีฟโฆษณาไปที่ Content Factory เรียบร้อยแล้ว!")
                st.page_link("pages/5_Workflow_Builder.py", label="👉 คลิกที่นี่เพื่อไปหน้า Content Factory (Workflow Builder)", icon="🏭")

# ══════════════════════════════════════════════════════════════════
# MODE 2 — Full Ad Simulator
# ══════════════════════════════════════════════════════════════════
elif st.session_state.andro_mode == 2:
    st.markdown("## 🎯 Full Ad Simulator — จำลองการประเมินของ Meta แบบเต็ม")
    st.markdown("""<div class="tip-box">
    <b>📡 วิธีใช้:</b> อัพโหลดภาพ + วาง Copy → Andromeda จำลองว่า Meta จะให้คะแนน Ad นี้เท่าไหร่
    พร้อม Predicted CTR/CPM และ Pre-Flight Checklist ก่อนยิงจริง
    </div>""", unsafe_allow_html=True)

    col_img, col_txt = st.columns([1, 1])
    with col_img:
        st.markdown("**📸 อัพโหลดภาพ Ad:**")
        sim_imgs = st.file_uploader("ภาพ Ad (สูงสุด 5 ใบ)",
                                     type=["png","jpg","jpeg","webp"],
                                     accept_multiple_files=True, key="mode2_imgs")
        if sim_imgs:
            st.image(sim_imgs[0], caption=sim_imgs[0].name[:20], use_container_width=True)

    with col_txt:
        st.markdown("**✍️ Ad Copy:**")
        sim_headline = st.text_input("Headline:", key="sim_headline",
                                      placeholder="หัวเรื่องโฆษณา")
        sim_body = st.text_area("Body Copy:", height=100, key="sim_body",
                                 placeholder="เนื้อหาโฆษณา")
        sim_cta = st.text_input("CTA:", key="sim_cta", placeholder="Call-to-Action")
        sim_placement = st.multiselect("Placement ที่จะยิง:",
                                        ["Facebook Feed", "Instagram Feed", "Facebook/Instagram Reels",
                                         "Story", "Audience Network"],
                                        default=["Facebook Feed"],
                                        key="sim_placement")
        sim_budget = st.number_input("งบต่อวัน (บาท):", min_value=0, value=300, step=50, key="sim_budget")

    sim_copy = f"Headline: {sim_headline}\nBody: {sim_body}\nCTA: {sim_cta}"
    sim_copy += f"\nPlacement: {', '.join(sim_placement)}"
    sim_copy += f"\nงบต่อวัน: {sim_budget} บาท"

    if st.button("🚀 RUN FULL SIMULATION", use_container_width=True, key="mode2_run"):
        if not sim_headline and not sim_body:
            st.warning("กรุณาใส่ Copy ก่อน")
        else:
            with st.spinner("🎯 กำลัง simulate Meta Ad Delivery System..."):
                imgs_b64 = [image_to_b64(f) for f in (sim_imgs or [])[:5]]
                prompt = make_dynamic_prompt(PROMPT_MODE3_FULL.replace("{copy_text}", sim_copy), sim_copy)
                result = call_engine(prompt, imgs_b64, max_tokens=12288)
                st.session_state.andro_results["mode2"] = result
                save_to_history("Full Ad Simulator", result[:100])

    if "mode2" in st.session_state.andro_results:
        col_rep, col_mock = st.columns([1.2, 0.8])
        with col_rep:
            st.markdown('<div class="section-title">📋 Full Simulation Report</div>', unsafe_allow_html=True)
            st.markdown(f"""<div class="result-block">
            <div class="result-engine">🎯 FULL SIMULATOR · {engine_labels.get(st.session_state.andro_engine_choice, '')} · {datetime.now().strftime("%H:%M:%S")}</div>
            <div class="result-content">{st.session_state.andro_results["mode2"]}</div>
            </div>""", unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                st.download_button("📥 Download Report",
                                   st.session_state.andro_results["mode2"],
                                   file_name=f"andromeda_simulation_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                                   use_container_width=True)
            with col2:
                if st.button("🔄 Simulate ใหม่", use_container_width=True, key="mode2_reset"):
                    del st.session_state.andro_results["mode2"]
                    st.rerun()
                    
        with col_mock:
            st.markdown('<div class="section-title">📱 Live Facebook Ad Mockup</div>', unsafe_allow_html=True)
            img_b64, img_mime = None, None
            if sim_imgs:
                try:
                    sim_imgs[0].seek(0)
                    img_b64 = base64.b64encode(sim_imgs[0].read()).decode()
                    img_mime = sim_imgs[0].type or "image/jpeg"
                except:
                    pass
            st.markdown(render_facebook_preview(sim_headline, sim_body, sim_cta, img_b64, img_mime), unsafe_allow_html=True)
            
            if st.button("🏭 ส่งโฆษณานี้ไปที่ Content Factory", use_container_width=True, key="m2_send_cf"):
                st.session_state.pname = st.session_state.current_project
                st.session_state.pdesc = sim_body
                st.session_state.cf_web_data = f"Headline: {sim_headline}\nBody: {sim_body}\nCTA: {sim_cta}\n\n[Andromeda Ad Simulator Feedback]:\n{st.session_state.andro_results['mode2']}"
                st.success("✅ ส่งข้อมูลบรีฟโฆษณาไปที่ Content Factory เรียบร้อยแล้ว!")
                st.page_link("pages/5_Workflow_Builder.py", label="👉 คลิกที่นี่เพื่อไปหน้า Content Factory (Workflow Builder)", icon="🏭")

# ══════════════════════════════════════════════════════════════════
# MODE 3 — Competitor Spy
# ══════════════════════════════════════════════════════════════════
elif st.session_state.andro_mode == 3:
    st.markdown("## ⚔️ Competitor Spy — วิเคราะห์โฆษณาคู่แข่ง")
    st.markdown("""<div class="tip-box">
    <b>📡 วิธีใช้:</b> อัพโหลด Screenshot ของ Ad คู่แข่ง → Andromeda วิเคราะห์ว่าทำไมมันได้ผล
    และสร้าง Counter-Strategy สำหรับ AQUALINE<br>
    <b>💡 Tip:</b> Screenshot จาก Meta Ads Library ได้เลย (facebook.com/ads/library)
    </div>""", unsafe_allow_html=True)

    comp_imgs = st.file_uploader(
        "📸 อัพโหลด Ad คู่แข่ง (สูงสุด 5 ใบ)",
        type=["png","jpg","jpeg","webp"],
        accept_multiple_files=True,
        key="mode3_comp"
    )
    if comp_imgs:
        cols = st.columns(min(len(comp_imgs), 4))
        for i, f in enumerate(comp_imgs[:4]):
            with cols[i]:
                f.seek(0)
                st.image(f, caption=f"Ad {i+1}", use_container_width=True)

    comp_name = st.text_input("ชื่อคู่แข่ง (ไม่บังคับ):", placeholder="เช่น: SCG, Winn, Diamond",
                               key="comp_name")
    comp_context = st.text_area("ข้อมูลเพิ่มเติม:", height=60,
                                 placeholder="เช่น: Ad นี้ run มา 3 เดือน, วิ่งใน Feed Facebook, น่าจะยิงหาเจ้าของบ้าน",
                                 key="comp_ctx")

    if st.button("🕵️ ANALYZE COMPETITOR", use_container_width=True, key="mode3_run",
                 disabled=not comp_imgs):
        with st.spinner("⚔️ กำลังวิเคราะห์ข่าวกรอง Ads คู่แข่ง..."):
            imgs_b64 = [image_to_b64(f) for f in comp_imgs[:5]]
            prompt = make_dynamic_prompt(PROMPT_MODE4_COMPETITOR, comp_context)
            if comp_name:
                prompt += f"\n\n**ชื่อคู่แข่ง:** {comp_name}"
            if comp_context:
                prompt += f"\n**ข้อมูลเพิ่มเติม:** {comp_context}"
            result = call_engine(prompt, imgs_b64, max_tokens=10240)
            st.session_state.andro_results["mode3"] = result
            save_to_history("Competitor Spy", result[:100])

    if "mode3" in st.session_state.andro_results:
        st.markdown('<div class="section-title">📋 Competitor Intelligence Report</div>', unsafe_allow_html=True)
        st.markdown(f"""<div class="result-block">
        <div class="result-engine">⚔️ COMPETITOR SPY · {engine_labels.get(st.session_state.andro_engine_choice, '')} · {datetime.now().strftime("%H:%M:%S")}</div>
        <div class="result-content">{st.session_state.andro_results["mode3"]}</div>
        </div>""", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.download_button("📥 Download Intel Report",
                               st.session_state.andro_results["mode3"],
                               file_name=f"andromeda_competitor_spy_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                               use_container_width=True)
        with col2:
            if st.button("🔄 Spy ใหม่", use_container_width=True, key="mode3_reset"):
                del st.session_state.andro_results["mode3"]
                st.rerun()

# ══════════════════════════════════════════════════════════════════
# MODE 4 — A/B Pre-Check
# ══════════════════════════════════════════════════════════════════
elif st.session_state.andro_mode == 4:
    st.markdown("## 🧪 A/B Pre-Check — ทำนายผลก่อนทดสอบจริง")
    st.markdown("""<div class="tip-box">
    <b>📡 วิธีใช้:</b> อัพโหลด Ad A และ Ad B → Andromeda ทำนายว่าตัวไหนชนะและทำไม
    + ตรวจ Entity ID Risk + แนะนำ Variant C ที่ดีกว่าทั้งคู่<br>
    <b>💡 Tip:</b> A/B ที่ดีควรต่างกัน "conceptually" ไม่ใช่แค่เปลี่ยนสีปุ่ม
    </div>""", unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("### 🅰️ Ad A")
        ab_imgs_a = st.file_uploader("อัพโหลด Ad A (สูงสุด 3 ใบ)",
                                      type=["png","jpg","jpeg","webp"],
                                      accept_multiple_files=True, key="ab_a")
        if ab_imgs_a:
            ab_imgs_a[0].seek(0)
            st.image(ab_imgs_a[0], caption="Ad A", use_container_width=True)
        ab_copy_a = st.text_area("Copy ของ Ad A:", height=80, key="ab_copy_a",
                                  placeholder="Headline + Body + CTA ของ Ad A")

    with col_b:
        st.markdown("### 🅱️ Ad B")
        ab_imgs_b = st.file_uploader("อัพโหลด Ad B (สูงสุด 3 ใบ)",
                                      type=["png","jpg","jpeg","webp"],
                                      accept_multiple_files=True, key="ab_b")
        if ab_imgs_b:
            ab_imgs_b[0].seek(0)
            st.image(ab_imgs_b[0], caption="Ad B", use_container_width=True)
        ab_copy_b = st.text_area("Copy ของ Ad B:", height=80, key="ab_copy_b",
                                  placeholder="Headline + Body + CTA ของ Ad B")

    ab_objective = st.selectbox("วัตถุประสงค์ Campaign:",
                                 ["Lead Generation", "Traffic", "Conversion", "Awareness", "Engagement"],
                                 key="ab_obj")

    can_run = (ab_imgs_a or ab_copy_a) and (ab_imgs_b or ab_copy_b)

    if st.button("🧪 RUN A/B PRE-CHECK", use_container_width=True, key="mode4_run",
                 disabled=not can_run):
        with st.spinner("🧪 Andromeda กำลังประเมิน A vs B..."):
            all_imgs = [image_to_b64(f) for f in (ab_imgs_a or [])[:3]]
            all_imgs += [image_to_b64(f) for f in (ab_imgs_b or [])[:3]]

            prompt = make_dynamic_prompt(PROMPT_MODE5_AB, f"A/B Test: {ab_copy_a} vs {ab_copy_b}")
            if ab_copy_a or ab_copy_b:
                prompt += f"\n\n**Ad A Copy:**\n{ab_copy_a}\n\n**Ad B Copy:**\n{ab_copy_b}"
            prompt += f"\n\n**วัตถุประสงค์:** {ab_objective}"
            if len(all_imgs) < 2:
                prompt += "\n\n(ไม่มีภาพแนบ — วิเคราะห์จาก Copy เท่านั้น)"

            result = call_engine(prompt, all_imgs, max_tokens=10240)
            st.session_state.andro_results["mode4"] = result
            save_to_history("A/B Pre-Check", result[:100])

    if "mode4" in st.session_state.andro_results:
        st.markdown('<div class="section-title">📋 A/B Pre-Check Report</div>', unsafe_allow_html=True)
        st.markdown(f"""<div class="result-block">
        <div class="result-engine">🧪 A/B PRE-CHECK · {engine_labels.get(st.session_state.andro_engine_choice, '')} · {datetime.now().strftime("%H:%M:%S")}</div>
        <div class="result-content">{st.session_state.andro_results["mode4"]}</div>
        </div>""", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.download_button("📥 Download A/B Report",
                               st.session_state.andro_results["mode4"],
                               file_name=f"andromeda_ab_precheck_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                               use_container_width=True)
        with col2:
            if st.button("🔄 ทดสอบใหม่", use_container_width=True, key="mode4_reset"):
                del st.session_state.andro_results["mode4"]
                st.rerun()

# ══════════════════════════════════════════════════════════════════
# FOOTER
# ══════════════════════════════════════════════════════════════════
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.markdown("""
<div style="text-align:center;font-family:'IBM Plex Mono',monospace;font-size:10px;color:#1e293b;padding:8px;">
ANDROMEDA OMNI SCANNER · Inspired by Meta Andromeda Engine + GEM + Lattice ·
Powered by Google Gemini Vision & Anthropic Claude Vision · AQUALINE AI SYSTEM
</div>
""", unsafe_allow_html=True)
