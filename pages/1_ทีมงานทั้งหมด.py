import streamlit as st
import base64, os, json
from datetime import datetime

st.set_page_config(page_title="Team Roster — AQUALINE", layout="wide")

ANALYTICS_FILE = "analytics_data.json"
PERSONA_FILE   = "agent_personas.json"

# ─── Load analytics for "last used" badges ───
def load_analytics():
    if os.path.exists(ANALYTICS_FILE):
        try:
            with open(ANALYTICS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {"sessions": [], "agent_usage": {}}

def load_personas():
    if os.path.exists(PERSONA_FILE):
        try:
            with open(PERSONA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {}

def save_personas(p):
    with open(PERSONA_FILE, "w", encoding="utf-8") as f:
        json.dump(p, f, ensure_ascii=False, indent=2)

analytics = load_analytics()
personas  = load_personas()
agent_usage = analytics.get("agent_usage", {})

# ─── Find recently active agents (last 3 sessions) ───
recent_agents = set()
for s in analytics.get("sessions", [])[-3:]:
    for a in s.get("agents_used", []):
        recent_agents.add(a)

# ─── CSS ───
st.markdown("""
<style>
.stApp{background:linear-gradient(135deg,#0b0f19 0%,#1a1a2e 100%);color:#e2e8f0}
[data-testid="stSidebar"]{background:rgba(15,23,42,.8);border-right:1px solid #1e293b}

.agent-card{background:rgba(15,23,42,.9);border-radius:16px;padding:16px;
  text-align:center;border:1px solid #1e293b;transition:all .25s;cursor:pointer;position:relative}
.agent-card:hover{border-color:#8b5cf6;box-shadow:0 0 20px rgba(139,92,246,.3);transform:translateY(-4px)}
.agent-avatar{font-size:52px;margin-bottom:8px;line-height:1;min-height:80px;display:flex;align-items:center;justify-content:center}
.agent-name{font-size:13px;font-weight:700;color:#e2e8f0;margin-bottom:4px}
.agent-role{font-size:11px;color:#64748b;margin-bottom:8px;line-height:1.4;min-height:28px}
.badge-legendary{background:linear-gradient(90deg,#f59e0b,#ef4444);color:#fff;font-size:9px;font-weight:700;padding:2px 8px;border-radius:20px;letter-spacing:.5px}
.badge-epic{background:linear-gradient(90deg,#8b5cf6,#6366f1);color:#fff;font-size:9px;font-weight:700;padding:2px 8px;border-radius:20px;letter-spacing:.5px}
.badge-rare{background:linear-gradient(90deg,#3b82f6,#06b6d4);color:#fff;font-size:9px;font-weight:700;padding:2px 8px;border-radius:20px;letter-spacing:.5px}
.stat-row{display:flex;justify-content:center;gap:10px;margin-top:8px;font-size:11px;color:#64748b}
.stat-item{display:flex;flex-direction:column;align-items:center;gap:2px}
.stat-val{font-size:13px;font-weight:700;color:#e2e8f0}
.header-box{background:linear-gradient(90deg,rgba(83,74,183,.2),rgba(219,39,119,.1));
  border:1px solid #534AB7;border-radius:12px;padding:16px 24px;margin-bottom:24px}
.active-dot{position:absolute;top:10px;right:10px;width:8px;height:8px;border-radius:50%;
  background:#34d399;box-shadow:0 0 6px #34d399;animation:pulse-g 2s infinite}
@keyframes pulse-g{0%,100%{opacity:1}50%{opacity:.4}}
.usage-bar{background:#1e293b;border-radius:4px;height:4px;width:100%;margin-top:6px}
.usage-fill{height:4px;border-radius:4px;background:linear-gradient(90deg,#8b5cf6,#3b82f6)}
.modal-overlay{background:rgba(0,0,0,.85);border-radius:16px;padding:24px;
  border:1px solid #334155;margin-top:12px}
.quick-btn{display:inline-block;background:linear-gradient(90deg,#3b82f6,#8b5cf6);
  color:#fff;border:none;border-radius:8px;padding:8px 16px;font-size:12px;
  font-weight:700;cursor:pointer;margin-top:10px;text-decoration:none}
.export-btn{background:rgba(52,211,153,.15);border:1px solid #34d39933;color:#34d399;
  border-radius:8px;padding:6px 14px;font-size:12px;cursor:pointer}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-box">
  <span style='font-size:28px;font-weight:900;color:#fff'>🎯 AQUALINE STUDIO SPECIAL TEAM</span>
  <span style='font-size:13px;color:#a78bfa;margin-left:16px'>25 Agents · V9.0 ULTRA</span>
</div>
""", unsafe_allow_html=True)

def get_agent_avatar(aid: str, icon: str, size: int = 80) -> str:
    path = os.path.join("agents", f"{aid}.png")
    if os.path.exists(path):
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return f'<img src="data:image/png;base64,{b64}" width="{size}" height="{size}" style="border-radius:8px;object-fit:cover;image-rendering:pixelated"/>'
    return f'<span style="font-size:52px;line-height:1">{icon}</span>'

AGENTS = {
    "A1":  {"name":"นักกลยุทธ์การตลาด",   "icon":"👨‍💼","p":"วางแผนภาพรวม กลยุทธ์ Positioning และจุดขายหลัก","rarity":"LEGENDARY","parallel":False,
            "skills":["Marketing Strategy","Brand Positioning","Campaign Planning"],"model":"Gemini 2.5 Flash"},
    "A2":  {"name":"ผู้จัดการโครงการ",      "icon":"📋",  "p":"คุมเป้าหมาย ไทม์ไลน์ และทรัพยากรทีมงาน","rarity":"EPIC","parallel":False,
            "skills":["Project Management","Timeline Planning","Resource Allocation"],"model":"Gemini 2.5 Flash"},
    "A3":  {"name":"นักเขียนคำโฆษณา",       "icon":"✍️",  "p":"สร้าง Content, Caption, Hook และ Copy โซเชียล","rarity":"EPIC","parallel":True,
            "skills":["Copywriting","Content Creation","Social Media"],"model":"Gemini 2.5 Flash"},
    "A4":  {"name":"กราฟิกดีไซเนอร์",       "icon":"🎨",  "p":"ออกแบบ Visual, Brand Identity และ Layout","rarity":"EPIC","parallel":True,
            "skills":["Graphic Design","Brand Identity","Visual Direction"],"model":"Gemini 2.5 Flash"},
    "A5":  {"name":"3D Visualizer",          "icon":"🏗️",  "p":"เรนเดอร์ภาพสินค้า 3D และ Architectural Viz","rarity":"EPIC","parallel":True,
            "skills":["3D Rendering","Product Visualization","Blender/3ds Max"],"model":"Gemini 2.5 Flash"},
    "A6":  {"name":"ผู้เชี่ยวชาญวิดีโอ",     "icon":"🎬",  "p":"สคริปต์ มุมกล้อง Storyboard และ Production","rarity":"EPIC","parallel":True,
            "skills":["Video Script","Storyboard","Film Direction"],"model":"Gemini 2.5 Flash"},
    "A7":  {"name":"นักยิงแอด Facebook",     "icon":"📈",  "p":"วางแผน Campaign, Audience, Budget และ KPI Ads","rarity":"LEGENDARY","parallel":False,
            "skills":["Facebook Ads","Campaign Planning","Audience Targeting","ROAS Optimization"],"model":"Gemini 2.5 Flash"},
    "A8":  {"name":"ผู้เชี่ยวชาญ SEO",       "icon":"🌐",  "p":"ปรับแต่งเนื้อหา Keyword และ On-Page SEO","rarity":"EPIC","parallel":True,
            "skills":["SEO","Keyword Research","On-Page Optimization"],"model":"Gemini 2.5 Flash"},
    "A9":  {"name":"ฝ่ายบริการลูกค้า",       "icon":"💬",  "p":"วางแนวทาง FAQ, Script ตอบคำถาม และ CRM","rarity":"RARE","parallel":True,
            "skills":["Customer Service","FAQ","CRM"],"model":"Gemini 2.5 Flash"},
    "A10": {"name":"นักวิเคราะห์ข้อมูล",     "icon":"📊",  "p":"วิเคราะห์สถิติ ความคุ้มค่า และ Data Insight","rarity":"EPIC","parallel":True,
            "skills":["Data Analysis","Statistics","Business Intelligence"],"model":"Gemini 2.5 Flash"},
    "A11": {"name":"ครีเอทีฟไดเรกเตอร์",     "icon":"💡",  "p":"คิด Big Idea, Concept และควบคุมทิศทางงานสร้างสรรค์","rarity":"LEGENDARY","parallel":False,
            "skills":["Creative Direction","Big Idea","Brand Concept"],"model":"Gemini 2.5 Flash"},
    "A12": {"name":"คนเขียนสตอรี่บอร์ด",     "icon":"🎞️",  "p":"วางลำดับภาพ เล่าเรื่อง และ Visual Narrative","rarity":"RARE","parallel":True,
            "skills":["Storyboard","Visual Storytelling","Film Pre-production"],"model":"Gemini 2.5 Flash"},
    "A13": {"name":"อาร์ตไดเรกเตอร์",        "icon":"✨",  "p":"ควบคุมคุณภาพ Visual, Style Guide และ QA งาน","rarity":"EPIC","parallel":True,
            "skills":["Art Direction","Quality Control","Style Guide"],"model":"Gemini 2.5 Flash"},
    "A14": {"name":"ผู้เชี่ยวชาญ AI Prompt", "icon":"🤖",  "p":"ปรับจูน Prompt Engineering สำหรับ AI Tools","rarity":"EPIC","parallel":True,
            "skills":["Prompt Engineering","AI Tools","Midjourney","Stable Diffusion"],"model":"Gemini 2.5 Flash"},
    "A15": {"name":"นักวางระบบอัตโนมัติ",    "icon":"⚙️",  "p":"เชื่อมระบบ Automation, Zapier และ Workflow","rarity":"RARE","parallel":True,
            "skills":["Automation","Zapier","Make.com","API Integration"],"model":"Gemini 2.5 Flash"},
    "A16": {"name":"นักออกแบบบูธ",           "icon":"🎪",  "p":"วางผัง Exhibition, Event Space และ Signage","rarity":"RARE","parallel":True,
            "skills":["Booth Design","Exhibition Planning","Signage"],"model":"Gemini 2.5 Flash"},
    "A17": {"name":"นักวิจัยตลาด",           "icon":"🔍",  "p":"เจาะลึกข้อมูลคู่แข่ง Trend และ Market Intelligence","rarity":"EPIC","parallel":False,
            "skills":["Market Research","Competitor Analysis","Trend Forecasting"],"model":"Gemini 2.5 Flash + Search"},
    "A18": {"name":"ฝ่ายตรวจสเปกสินค้า",     "icon":"✅",  "p":"ตรวจสอบความถูกต้องทางเทคนิค Spec และ QC","rarity":"RARE","parallel":True,
            "skills":["Product Spec","Technical QC","Documentation"],"model":"Gemini 2.5 Flash"},
    "A19": {"name":"นักขายมือโปร",           "icon":"💰",  "p":"สร้าง Sales Script, Pitch Deck และปิดการขาย","rarity":"EPIC","parallel":True,
            "skills":["Sales Script","Pitch Deck","Closing Techniques"],"model":"Gemini 2.5 Flash"},
    "A20": {"name":"ที่ปรึกษากฎหมาย",        "icon":"⚖️",  "p":"ตรวจสอบข้อบังคับ ลิขสิทธิ์ และ Legal Compliance","rarity":"EPIC","parallel":False,
            "skills":["Legal Review","Copyright","Advertising Law"],"model":"Gemini 2.5 Flash"},
    "A21": {"name":"นักเขียนบทความ",         "icon":"📝",  "p":"เขียนบทความยาว Long-form Content และเนื้อหาเชิงลึก","rarity":"RARE","parallel":True,
            "skills":["Long-form Writing","Blog","Thought Leadership"],"model":"Gemini 2.5 Flash"},
    "A22": {"name":"นักวางราคา/Pricing",      "icon":"🧮",  "p":"วิเคราะห์ราคา ตั้ง Promo Bundle และ Pricing Strategy","rarity":"EPIC","parallel":True,
            "skills":["Pricing Strategy","Bundle Offer","Promo Design"],"model":"Gemini 2.5 Flash"},
    "A23": {"name":"ผู้เชี่ยวชาญ LINE OA",   "icon":"📱",  "p":"วางแผน LINE OA, CRM, Broadcast และ Chatbot","rarity":"EPIC","parallel":True,
            "skills":["LINE OA","CRM","Broadcast","Chatbot"],"model":"Gemini 2.5 Flash"},
    "A24": {"name":"TikTok & Reels",          "icon":"🎵",  "p":"Hook, Trend, Script TikTok/Reels และ Viral Content","rarity":"EPIC","parallel":True,
            "skills":["TikTok","Reels","Viral Content","Hook Writing"],"model":"Gemini 2.5 Flash"},
    "A25": {"name":"นักจิตวิทยาการตลาด",     "icon":"🧠",  "p":"Psychology Marketing, Trigger การซื้อ และ Persuasion","rarity":"LEGENDARY","parallel":False,
            "skills":["Consumer Psychology","Persuasion","Behavioral Marketing"],"model":"Gemini 2.5 Flash"},
}

RARITY_ORDER = {"LEGENDARY": 0, "EPIC": 1, "RARE": 2}
max_usage = max(agent_usage.values(), default=1)

# ─── Filter bar ───
col_f1, col_f2, col_f3, col_f4 = st.columns([2, 1, 1, 1])
with col_f1:
    search = st.text_input("🔍 ค้นหา Agent:", placeholder="ชื่อ ทักษะ หรือความสามารถ...")
with col_f2:
    rarity_filter = st.selectbox("✨ Rarity:", ["ทั้งหมด", "LEGENDARY", "EPIC", "RARE"])
with col_f3:
    mode_filter = st.selectbox("⚡ Mode:", ["ทั้งหมด", "Sequential", "Parallel"])
with col_f4:
    sort_by = st.selectbox("🔢 เรียงโดย:", ["Rarity", "Usage มากสุด", "ชื่อ A-Z"])

filtered = {}
for aid, info in AGENTS.items():
    if search and search.lower() not in info["name"].lower() and search.lower() not in info["p"].lower() \
       and not any(search.lower() in s.lower() for s in info.get("skills",[])):
        continue
    if rarity_filter != "ทั้งหมด" and info["rarity"] != rarity_filter:
        continue
    if mode_filter == "Sequential" and info["parallel"]:
        continue
    if mode_filter == "Parallel" and not info["parallel"]:
        continue
    filtered[aid] = info

if sort_by == "Usage มากสุด":
    sorted_agents = sorted(filtered.items(), key=lambda x: agent_usage.get(x[0], 0), reverse=True)
elif sort_by == "ชื่อ A-Z":
    sorted_agents = sorted(filtered.items(), key=lambda x: x[1]["name"])
else:
    sorted_agents = sorted(filtered.items(), key=lambda x: RARITY_ORDER.get(x[1]["rarity"], 99))

st.markdown(f"<div style='font-size:13px;color:#64748b;margin-bottom:16px'>แสดง {len(sorted_agents)} / 25 Agent</div>", unsafe_allow_html=True)

# ─── Session state for modal ───
if "selected_agent" not in st.session_state:
    st.session_state.selected_agent = None

# ─── Grid 5 cols ───
cols_per_row = 5
rows = [sorted_agents[i:i+cols_per_row] for i in range(0, len(sorted_agents), cols_per_row)]
for row in rows:
    cols = st.columns(cols_per_row)
    for col, (aid, info) in zip(cols, row):
        with col:
            badge_class = f"badge-{info['rarity'].lower()}"
            mode_icon   = "⚡" if info["parallel"] else "🔄"
            mode_label  = "Parallel" if info["parallel"] else "Sequential"
            usage_count = agent_usage.get(aid, 0)
            usage_pct   = int(usage_count / max_usage * 100) if max_usage else 0
            is_active   = aid in recent_agents
            active_dot  = '<span class="active-dot"></span>' if is_active else ""

            st.markdown(f"""
<div class="agent-card" onclick="void(0)">
  {active_dot}
  <div class="agent-avatar">{get_agent_avatar(aid, info['icon'], 80)}</div>
  <div class="agent-name">{info['name']}</div>
  <div class="agent-role">{info['p']}</div>
  <span class="{badge_class}">{info['rarity']}</span>
  <div class="stat-row">
    <div class="stat-item"><span class="stat-val">{mode_icon}</span><span>{mode_label}</span></div>
    <div class="stat-item"><span class="stat-val">{usage_count}</span><span>ครั้ง</span></div>
    <div class="stat-item"><span class="stat-val">{aid}</span><span>ID</span></div>
  </div>
  <div class="usage-bar"><div class="usage-fill" style="width:{usage_pct}%"></div></div>
</div>
""", unsafe_allow_html=True)
            if st.button(f"ดูรายละเอียด", key=f"btn_{aid}", use_container_width=True):
                st.session_state.selected_agent = aid if st.session_state.selected_agent != aid else None
                st.rerun()

# ─── Agent Detail Modal ───
if st.session_state.selected_agent:
    aid  = st.session_state.selected_agent
    info = AGENTS.get(aid, {})
    if info:
        persona_key = f"persona_{aid}"
        current_persona = personas.get(aid, "")
        st.markdown("---")
        st.markdown(f"""
<div class="modal-overlay">
  <div style='display:flex;align-items:center;gap:16px;margin-bottom:16px'>
    <div style='font-size:64px'>{get_agent_avatar(aid, info['icon'], 64)}</div>
    <div>
      <div style='font-size:22px;font-weight:900;color:#e2e8f0'>{info['name']}</div>
      <div style='font-size:13px;color:#64748b;margin-top:4px'>{info['p']}</div>
      <div style='margin-top:8px'>
        <span class="badge-{info['rarity'].lower()}">{info['rarity']}</span>
        <span style='font-size:12px;color:#64748b;margin-left:8px'>ID: {aid}</span>
        <span style='font-size:12px;color:#64748b;margin-left:8px'>Model: {info.get('model','Gemini 2.5 Flash')}</span>
      </div>
    </div>
  </div>
  <div style='margin-bottom:12px'>
    <div style='font-size:12px;color:#64748b;margin-bottom:6px'>🛠️ ทักษะความสามารถ:</div>
    {''.join(f"<span style='background:rgba(139,92,246,.2);border:1px solid #8b5cf644;border-radius:12px;padding:3px 10px;font-size:11px;color:#c4b5fd;margin:3px;display:inline-block'>{s}</span>" for s in info.get('skills',[]))}
  </div>
  <div style='display:flex;gap:16px;font-size:12px;color:#64748b'>
    <span>⚡ Mode: {'Parallel' if info['parallel'] else 'Sequential'}</span>
    <span>📊 ถูกเรียกใช้: {agent_usage.get(aid, 0)} ครั้ง</span>
    <span>{'🟢 Active ล่าสุด' if aid in recent_agents else '⚪ ไม่ได้ใช้ล่าสุด'}</span>
  </div>
</div>
""", unsafe_allow_html=True)

        col_m1, col_m2, col_m3 = st.columns([2, 1, 1])
        with col_m1:
            st.markdown("**✏️ แก้ไข Custom Persona / System Prompt:**")
            new_persona = st.text_area(
                "Custom Persona:",
                value=current_persona,
                placeholder=f"Default: {info['p']}\n\nพิมพ์ system prompt ที่ต้องการให้ Agent นี้ใช้แทนค่า default...",
                height=120,
                label_visibility="collapsed",
                key=f"persona_ta_{aid}"
            )
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                if st.button("💾 บันทึก Persona", key=f"save_persona_{aid}", use_container_width=True, type="primary"):
                    personas[aid] = new_persona
                    save_personas(personas)
                    st.success("✅ บันทึก Persona แล้ว!")
            with col_s2:
                if st.button("🔄 Reset Default", key=f"reset_persona_{aid}", use_container_width=True):
                    personas.pop(aid, None)
                    save_personas(personas)
                    st.info("รีเซ็ตเป็นค่า default แล้ว")
                    st.rerun()

        with col_m2:
            st.markdown("**🚀 Quick Actions:**")
            if st.button(f"💬 คุยกับ {info['name']}", key=f"chat_{aid}", use_container_width=True):
                st.switch_page("pages/2_คุยกับ_AI_Agent.py")
            if st.button("📊 ดูสถิติ Agent", key=f"stat_{aid}", use_container_width=True):
                st.switch_page("pages/4_สถิติการใช้งาน.py")

        with col_m3:
            st.markdown("**📋 Info:**")
            st.markdown(f"""
<div style='background:rgba(15,23,42,.8);border:1px solid #1e293b;border-radius:8px;padding:12px;font-size:12px'>
  <div style='color:#64748b'>Mode</div>
  <div style='color:#e2e8f0;font-weight:700'>{"⚡ Parallel" if info['parallel'] else "🔄 Sequential"}</div>
  <div style='color:#64748b;margin-top:8px'>Model</div>
  <div style='color:#38bdf8;font-weight:700'>{info.get('model','Gemini')}</div>
  <div style='color:#64748b;margin-top:8px'>Agent ID</div>
  <div style='color:#a78bfa;font-weight:700'>{aid}</div>
</div>
""", unsafe_allow_html=True)

        if st.button("✖️ ปิด", key="close_modal", use_container_width=False):
            st.session_state.selected_agent = None
            st.rerun()

st.markdown("---")

# ─── Export Section ───
with st.expander("📤 Export ข้อมูลทีม", expanded=False):
    col_e1, col_e2, col_e3 = st.columns(3)
    with col_e1:
        # Export CSV
        csv_lines = ["ID,ชื่อ,บทบาท,Rarity,Mode,ครั้งที่ใช้"]
        for aid, info in AGENTS.items():
            mode = "Parallel" if info["parallel"] else "Sequential"
            usage = agent_usage.get(aid, 0)
            csv_lines.append(f"{aid},{info['name']},{info['p']},{info['rarity']},{mode},{usage}")
        csv_data = "\n".join(csv_lines)
        st.download_button(
            "📥 Export CSV",
            data=csv_data.encode("utf-8-sig"),
            file_name="aqualine_agents.csv",
            mime="text/csv",
            use_container_width=True
        )
    with col_e2:
        # Export JSON
        export_json = json.dumps(
            {aid: {**info, "usage": agent_usage.get(aid, 0)} for aid, info in AGENTS.items()},
            ensure_ascii=False, indent=2
        )
        st.download_button(
            "📥 Export JSON",
            data=export_json.encode("utf-8"),
            file_name="aqualine_agents.json",
            mime="application/json",
            use_container_width=True
        )
    with col_e3:
        # Export Markdown report
        md_lines = ["# AQUALINE STUDIO SPECIAL TEAM\n", f"อัปเดต: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"]
        for rarity in ["LEGENDARY", "EPIC", "RARE"]:
            md_lines.append(f"## {rarity}\n")
            for aid, info in AGENTS.items():
                if info["rarity"] == rarity:
                    usage = agent_usage.get(aid, 0)
                    md_lines.append(f"- **{info['name']}** ({aid}) — {info['p']} | ใช้ {usage} ครั้ง\n")
        st.download_button(
            "📥 Export Markdown",
            data="".join(md_lines).encode("utf-8"),
            file_name="aqualine_team.md",
            mime="text/markdown",
            use_container_width=True
        )

# ─── Summary ───
s1, s2, s3, s4 = st.columns(4)
counts = {"LEGENDARY": 0, "EPIC": 0, "RARE": 0, "Parallel": 0}
for a in AGENTS.values():
    counts[a["rarity"]] += 1
    if a["parallel"]: counts["Parallel"] += 1

for col, label, val, color in [
    (s1, "🤖 ทั้งหมด",    "25",                   "#e2e8f0"),
    (s2, "⭐ LEGENDARY", str(counts["LEGENDARY"]), "#f59e0b"),
    (s3, "💜 EPIC",      str(counts["EPIC"]),      "#8b5cf6"),
    (s4, "💙 RARE",      str(counts["RARE"]),      "#3b82f6"),
]:
    col.markdown(f"""
<div style='background:rgba(15,23,42,.8);border:1px solid #1e293b;border-radius:10px;padding:14px;text-align:center'>
  <div style='font-size:24px;font-weight:700;color:{color}'>{val}</div>
  <div style='font-size:12px;color:#64748b'>{label}</div>
</div>
""", unsafe_allow_html=True)