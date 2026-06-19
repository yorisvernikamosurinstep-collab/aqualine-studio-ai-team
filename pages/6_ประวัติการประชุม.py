import streamlit as st
import json, os, csv
from datetime import datetime
from io import StringIO, BytesIO

import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ui_settings import inject_global_font_css

st.set_page_config(page_title="Sessions Log — AQUALINE", layout="wide")

# 🔐 กันเข้าหน้านี้ตรงผ่าน URL โดยไม่ผ่านด่านล็อกอินที่หน้าแรก
from auth_guard import require_auth
require_auth()

# 🧭 PAGE-VISIT MARKER — ใช้โดยหน้า "งานบริษัทอาควาไลน์" เพื่อรู้ว่าผู้ใช้เปิดหน้าใหม่จริง
st.session_state["_active_page"] = __file__

# ฟอนต์/ขนาดตัวอักษรที่ผู้ใช้กำหนดเอง (หน้า Design UX/UI) — ใช้ร่วมกันทุกหน้า
st.markdown(inject_global_font_css(), unsafe_allow_html=True)

ANALYTICS_FILE = "analytics_data.json"

# อัตราแลกเปลี่ยน USD→THB — ดึงจาก secrets.toml เดียวกับ ai_team.py (single source of truth)
USD_TO_THB = float(st.secrets.get("USD_TO_THB", "35.0"))

st.markdown("""
<style>
.stApp{background:linear-gradient(135deg,#0b0f19 0%,#1a1a2e 100%);color:#e2e8f0}
[data-testid="stSidebar"]{background:rgba(15,23,42,.8);border-right:1px solid #1e293b}
.session-card{background:rgba(15,23,42,.9);border:1px solid #1e293b;border-radius:12px;
  padding:16px;margin-bottom:10px;transition:border-color .2s}
.session-card:hover{border-color:#3b82f6}
.agent-chip{background:rgba(99,102,241,.2);border:1px solid rgba(99,102,241,.4);
  border-radius:20px;padding:2px 10px;font-size:11px;color:#a5b4fc;display:inline-block;margin:2px}
.stat-box{background:rgba(15,23,42,.8);border:1px solid #1e293b;border-radius:10px;padding:14px;text-align:center}
.stat-num{font-size:28px;font-weight:900;color:#38bdf8}
.stat-lbl{font-size:12px;color:#64748b;margin-top:2px}
.header-box{background:linear-gradient(90deg,rgba(56,189,248,.1),rgba(99,102,241,.1));
  border:1px solid #0ea5e944;border-radius:12px;padding:16px 24px;margin-bottom:24px}
.cost-badge{background:rgba(52,211,153,.15);border:1px solid #34d39933;border-radius:6px;
  padding:2px 8px;font-size:11px;color:#34d399;display:inline-block}
.filter-card{background:rgba(15,23,42,.6);border:1px solid #1e293b;border-radius:10px;padding:16px;margin-bottom:16px}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-box">
  <span style='font-size:28px;font-weight:900;color:#fff'>📑 SESSIONS LOG</span>
  <span style='font-size:13px;color:#38bdf8;margin-left:16px'>ประวัติการประชุม AI ทุก Session</span>
</div>
""", unsafe_allow_html=True)

def load_analytics():
    if os.path.exists(ANALYTICS_FILE):
        try:
            with open(ANALYTICS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: pass
    return {"sessions": [], "agent_usage": {}, "project_count": {}, "weekly": {}}

analytics = load_analytics()
sessions  = analytics.get("sessions", [])

# ─── Summary stats ───
total_sessions = len(sessions)
total_tokens   = sum(s.get("tokens", 0)   for s in sessions)
total_cost     = sum(s.get("cost_usd", 0) for s in sessions)
total_cost_thb = total_cost * USD_TO_THB
total_agents   = sum(len(s.get("agents_used", [])) for s in sessions)

c1, c2, c3, c4, c5 = st.columns(5)
for col, num, lbl, color in [
    (c1, str(total_sessions),           "TOTAL SESSIONS",     "#38bdf8"),
    (c2, f"{total_tokens:,}",            "TOTAL TOKENS",       "#a78bfa"),
    (c3, f"${total_cost:.4f}",           "COST USD",           "#34d399"),
    (c4, f"฿{total_cost_thb:.2f}",       "COST THB",           "#fbbf24"),
    (c5, str(total_agents),              "AGENT CALLS",        "#f59e0b"),
]:
    col.markdown(f"""
<div class="stat-box">
  <div class="stat-num" style='color:{color}'>{num}</div>
  <div class="stat-lbl">{lbl}</div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ─── Advanced Filter ───
with st.expander("🔍 ตัวกรองขั้นสูง", expanded=True):
    col_s, col_p, col_sort = st.columns([2, 2, 2])
    with col_s:
        search_proj = st.text_input("ค้นหา Project:", placeholder="ชื่อ project...")
    with col_p:
        # Build agent list for filter
        all_agents_used = set()
        for s in sessions:
            for a in s.get("agents_used", []):
                all_agents_used.add(a)
        agent_filter = st.multiselect("กรอง Agent ที่ใช้:", sorted(all_agents_used))
    with col_sort:
        sort_opt = st.selectbox("เรียงลำดับ:", ["ใหม่ → เก่า", "เก่า → ใหม่", "tokens มากสุด", "cost มากสุด", "จำนวน Agent มากสุด"])

    col_cost_min, col_cost_max, col_tok_min = st.columns(3)
    with col_cost_min:
        cost_min = st.number_input("Cost ขั้นต่ำ ($):", min_value=0.0, value=0.0, step=0.001, format="%.4f")
    with col_cost_max:
        cost_max = st.number_input("Cost สูงสุด ($):", min_value=0.0, value=9999.0, step=0.001, format="%.4f")
    with col_tok_min:
        tok_min = st.number_input("Tokens ขั้นต่ำ:", min_value=0, value=0, step=100)

# ─── Filter & Sort ───
filtered_sessions = []
for s in sessions:
    if search_proj and search_proj.lower() not in s.get("project", "").lower():
        continue
    if agent_filter and not any(a in s.get("agents_used", []) for a in agent_filter):
        continue
    if s.get("cost_usd", 0) < cost_min or s.get("cost_usd", 0) > cost_max:
        continue
    if s.get("tokens", 0) < tok_min:
        continue
    filtered_sessions.append(s)

if sort_opt == "ใหม่ → เก่า":
    filtered_sessions = list(reversed(filtered_sessions))
elif sort_opt == "tokens มากสุด":
    filtered_sessions = sorted(filtered_sessions, key=lambda x: x.get("tokens", 0), reverse=True)
elif sort_opt == "cost มากสุด":
    filtered_sessions = sorted(filtered_sessions, key=lambda x: x.get("cost_usd", 0), reverse=True)
elif sort_opt == "จำนวน Agent มากสุด":
    filtered_sessions = sorted(filtered_sessions, key=lambda x: len(x.get("agents_used", [])), reverse=True)

# ─── Export Buttons ───
col_exp1, col_exp2, col_exp3, _ = st.columns([1, 1, 1, 2])
with col_exp1:
    # CSV Export
    if filtered_sessions:
        buf = StringIO()
        writer = csv.writer(buf)
        writer.writerow(["timestamp","project","tokens","cost_usd","cost_thb","agents_count","agents_used","brief"])
        for s in filtered_sessions:
            writer.writerow([
                s.get("timestamp",""), s.get("project",""), s.get("tokens",0),
                s.get("cost_usd",0), round(s.get("cost_usd",0)*USD_TO_THB,2),
                len(s.get("agents_used",[])), "|".join(s.get("agents_used",[])),
                s.get("brief","")[:200]
            ])
        st.download_button("📥 Export CSV", data=buf.getvalue().encode("utf-8-sig"),
            file_name=f"sessions_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv", use_container_width=True)

with col_exp2:
    if filtered_sessions:
        json_data = json.dumps(filtered_sessions, ensure_ascii=False, indent=2)
        st.download_button("📥 Export JSON", data=json_data.encode("utf-8"),
            file_name=f"sessions_{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json", use_container_width=True)

with col_exp3:
    if filtered_sessions:
        # Markdown report
        md = [f"# Sessions Log — AQUALINE\nExported: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"]
        md.append(f"**Total sessions:** {len(filtered_sessions)} | **Total cost:** ${sum(s.get('cost_usd',0) for s in filtered_sessions):.4f}\n\n")
        for s in filtered_sessions[:50]:  # limit 50
            ts = s.get("timestamp","")[:16]
            md.append(f"## 📁 {s.get('project','?')} — {ts}\n")
            md.append(f"- Tokens: {s.get('tokens',0):,} | Cost: ${s.get('cost_usd',0):.4f}\n")
            md.append(f"- Agents: {', '.join(s.get('agents_used',[]))}\n\n")
        st.download_button("📥 Export MD", data="".join(md).encode("utf-8"),
            file_name=f"sessions_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown", use_container_width=True)

st.markdown(f"<div style='font-size:13px;color:#64748b;margin:12px 0'>แสดง {len(filtered_sessions)} session</div>", unsafe_allow_html=True)

# ─── Session List ───
if not filtered_sessions:
    st.markdown("""
<div style='text-align:center;padding:60px;color:#334155'>
  <div style='font-size:48px;margin-bottom:16px'>📭</div>
  <div style='font-size:16px'>ไม่พบ Session ที่ตรงกับเงื่อนไข</div>
</div>
""", unsafe_allow_html=True)
else:
    for i, s in enumerate(filtered_sessions):
        ts          = s.get("timestamp", "")
        project     = s.get("project", "Unknown Project")
        tokens      = s.get("tokens", 0)
        cost        = s.get("cost_usd", 0)
        cost_thb    = cost * USD_TO_THB
        agents_used = s.get("agents_used", [])
        brief_short = s.get("brief", "")[:120]
        n_agents    = len(agents_used)

        try:
            dt_obj   = datetime.fromisoformat(ts)
            dt_label = dt_obj.strftime("%d %b %Y · %H:%M")
        except:
            dt_label = ts[:16] if ts else "—"

        agent_chips = "".join(f"<span class='agent-chip'>{a}</span>" for a in agents_used[:12])
        if len(agents_used) > 12:
            agent_chips += f"<span class='agent-chip'>+{len(agents_used)-12}</span>"

        with st.expander(f"📁 {project}  ·  {dt_label}  ·  {n_agents} agents  ·  {tokens:,} tokens  ·  ${cost:.4f}"):
            col_info, col_cost_box = st.columns([3, 1])
            with col_info:
                st.markdown(f"""
<div class="session-card">
  <div style='font-size:14px;font-weight:700;color:#e2e8f0;margin-bottom:6px'>📁 {project}</div>
  <div style='font-size:12px;color:#64748b;margin-bottom:8px'>🕐 {dt_label} &nbsp;·&nbsp; 🤖 {n_agents} Agents</div>
  {"<div style='font-size:12px;color:#94a3b8;margin-bottom:8px;font-style:italic'>📝 " + brief_short + "...</div>" if brief_short else ""}
  <div>{agent_chips}</div>
</div>
""", unsafe_allow_html=True)

            with col_cost_box:
                st.markdown(f"""
<div style='background:rgba(15,23,42,.8);border:1px solid #1e293b;border-radius:10px;padding:14px;text-align:center'>
  <div style='font-size:11px;color:#64748b'>Token ที่ใช้</div>
  <div style='font-size:18px;font-weight:700;color:#a78bfa'>{tokens:,}</div>
  <div style='font-size:11px;color:#64748b;margin-top:8px'>ค่าใช้จ่าย</div>
  <div style='font-size:16px;font-weight:700;color:#34d399'>${cost:.4f}</div>
  <div style='font-size:12px;color:#fbbf24'>฿{cost_thb:.2f}</div>
</div>
""", unsafe_allow_html=True)

            if s.get("log"):
                st.markdown("**📄 Meeting Log:**")
                log_text = s["log"]
                st.text_area("", value=log_text, height=300, key=f"log_{i}", label_visibility="collapsed")
                # Download this session log
                st.download_button(
                    f"📥 Download Log นี้",
                    data=log_text.encode("utf-8"),
                    file_name=f"log_{project}_{dt_label[:10]}.txt",
                    mime="text/plain",
                    key=f"dl_log_{i}"
                )

st.markdown("---")

# ─── Clear with confirmation ───
col_clr, col_clr2, _ = st.columns([1, 1, 3])
with col_clr:
    if st.button("🗑️ ล้างประวัติที่กรองแล้ว", use_container_width=True):
        st.session_state["confirm_clear"] = "filtered"
with col_clr2:
    if st.button("🗑️ ล้างทั้งหมด", use_container_width=True):
        st.session_state["confirm_clear"] = "all"

if st.session_state.get("confirm_clear"):
    mode_clr = st.session_state["confirm_clear"]
    st.warning(f"⚠️ ยืนยันการล้าง{'ประวัติที่กรองแล้ว' if mode_clr=='filtered' else 'ประวัติทั้งหมด'}?")
    col_y, col_n = st.columns(2)
    with col_y:
        if st.button("✅ ยืนยัน ล้างเลย", type="primary", use_container_width=True):
            if mode_clr == "all":
                analytics["sessions"] = []
            else:
                filtered_ids = set(id(s) for s in filtered_sessions)
                analytics["sessions"] = [s for s in sessions if id(s) not in filtered_ids]
            with open(ANALYTICS_FILE, "w", encoding="utf-8") as f:
                json.dump(analytics, f, ensure_ascii=False)
            st.success("✅ ล้างแล้ว!")
            del st.session_state["confirm_clear"]
            st.rerun()
    with col_n:
        if st.button("❌ ยกเลิก", use_container_width=True):
            del st.session_state["confirm_clear"]
            st.rerun()