import streamlit as st
import json
import os
import pandas as pd
from collections import Counter
from datetime import datetime, timedelta, date

st.set_page_config(page_title="Analytics — AQUALINE", layout="wide")

ANALYTICS_FILE = "analytics_data.json"

# ── Agent name / icon map ──
AGENT_NAMES = {
    "A1":"นักกลยุทธ์การตลาด", "A2":"ผู้จัดการโครงการ",   "A3":"นักเขียนคำโฆษณา",
    "A4":"กราฟิกดีไซเนอร์",   "A5":"3D Visualizer",       "A6":"ผู้เชี่ยวชาญวิดีโอ",
    "A7":"นักยิงแอด Facebook", "A8":"ผู้เชี่ยวชาญ SEO",    "A9":"ฝ่ายบริการลูกค้า",
    "A10":"นักวิเคราะห์ข้อมูล","A11":"ครีเอทีฟไดเรกเตอร์","A12":"คนเขียนสตอรี่บอร์ด",
    "A13":"อาร์ตไดเรกเตอร์",  "A14":"AI Prompt Expert",   "A15":"นักวางระบบอัตโนมัติ",
    "A16":"นักออกแบบบูธ",     "A17":"นักวิจัยตลาด",      "A18":"ฝ่ายตรวจสเปก",
    "A19":"นักขายมือโปร",     "A20":"ที่ปรึกษากฎหมาย",   "A21":"นักเขียนบทความ",
    "A22":"Pricing Expert",   "A23":"LINE OA Expert",     "A24":"TikTok & Reels",
    "A25":"นักจิตวิทยาการตลาด",
}
AGENT_ICONS = {
    "A1":"👨‍💼","A2":"📋","A3":"✍️","A4":"🎨","A5":"🏗️","A6":"🎬","A7":"📈",
    "A8":"🌐","A9":"💬","A10":"📊","A11":"💡","A12":"🎞️","A13":"✨","A14":"🤖",
    "A15":"⚙️","A16":"🎪","A17":"🔍","A18":"✅","A19":"💰","A20":"⚖️","A21":"📝",
    "A22":"🧮","A23":"📱","A24":"🎵","A25":"🧠",
}

st.markdown("""
<style>
.stApp{background:linear-gradient(135deg,#0b0f19 0%,#1a1a2e 100%);color:#e2e8f0}
[data-testid="stSidebar"]{background:rgba(15,23,42,.8);border-right:1px solid #1e293b}
.kpi-card{background:rgba(15,23,42,.9);border:1px solid #1e293b;border-radius:12px;
  padding:16px;text-align:center;margin-bottom:8px}
.kpi-num{font-size:32px;font-weight:900}
.kpi-lbl{font-size:12px;color:#64748b;margin-top:4px}
.kpi-delta{font-size:11px;margin-top:4px}
.rank-row{background:rgba(15,23,42,.8);border:1px solid #1e293b;border-radius:8px;
  padding:10px 14px;margin-bottom:6px;display:flex;align-items:center;gap:12px}
.rank-bar-bg{background:#1e293b;border-radius:4px;height:8px;flex:1}
.header-box{background:linear-gradient(90deg,rgba(16,185,129,.1),rgba(6,182,212,.1));
  border:1px solid #10b98144;border-radius:12px;padding:16px 24px;margin-bottom:24px}
.filter-bar{background:rgba(30,41,59,.6);border:1px solid #334155;border-radius:10px;
  padding:14px 18px;margin-bottom:20px}
.section-card{background:rgba(15,23,42,.9);border:1px solid #1e293b;border-radius:12px;
  padding:18px;margin-bottom:16px}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-box">
  <span style='font-size:28px;font-weight:900;color:#fff'>📈 ANALYTICS DASHBOARD</span>
  <span style='font-size:13px;color:#34d399;margin-left:16px'>สถิติการใช้งาน AQUALINE STUDIO</span>
</div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════
# LOAD DATA
# ════════════════════════════════════════════
def load_analytics():
    if os.path.exists(ANALYTICS_FILE):
        try:
            with open(ANALYTICS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"sessions": [], "agent_usage": {}, "project_count": {}, "weekly": {}}

a        = load_analytics()
sessions = a.get("sessions", [])

# ── Demo data ถ้ายังไม่มีข้อมูลจริง ──
DEMO_MODE = not sessions
if DEMO_MODE:
    import random, math
    random.seed(42)
    agents_pool = ["A1","A3","A7","A9","A11","A3","A7","A1","A17","A25","A14","A4"]
    projects_pool = ["AQUALINE Campaign Q2","Prestige Series Launch","งาน Thailand Pavilion",
                     "Social Media June","SEO Blog Content","TikTok Q3"]
    now = datetime.now()
    for i in range(90):
        days_ago = random.randint(0, 59)
        hour     = random.randint(7, 21)
        ts       = (now - timedelta(days=days_ago)).replace(
                       hour=hour, minute=random.randint(0,59), second=0)
        used_agents = random.sample(agents_pool, k=random.randint(1,4))
        tokens  = random.randint(800, 8000)
        sessions.append({
            "timestamp":   ts.isoformat(),
            "project":     random.choice(projects_pool),
            "agents_used": used_agents,
            "tokens":      tokens,
            "cost_usd":    tokens * 0.000002,
        })
    # rebuild agent_usage & project_count from demo sessions
    for s in sessions:
        for ag in s.get("agents_used", []):
            a["agent_usage"][ag] = a["agent_usage"].get(ag, 0) + 1
        proj = s.get("project","")
        a["project_count"][proj] = a["project_count"].get(proj, 0) + 1
    st.info("📌 แสดงข้อมูลตัวอย่าง — เริ่มใช้งาน AI Team จริงเพื่อดูสถิติของคุณ")

if not sessions:
    st.markdown("""
<div style='text-align:center;padding:80px;color:#334155'>
  <div style='font-size:56px;margin-bottom:16px'>📊</div>
  <div style='font-size:18px;font-weight:700;color:#475569'>ยังไม่มีข้อมูล</div>
  <div style='font-size:14px;margin-top:8px'>กลับไปหน้าหลักแล้วรัน AI Team ก่อนครับ</div>
</div>
""", unsafe_allow_html=True)
    st.stop()

# ── Build DataFrame ──
rows = []
for s in sessions:
    try:
        dt = datetime.fromisoformat(s.get("timestamp",""))
    except:
        dt = datetime.now()
    rows.append({
        "datetime":    dt,
        "date":        dt.date(),
        "week":        dt.strftime("%Y-W%V"),
        "hour":        dt.hour,
        "dow":         dt.weekday(),
        "project":     s.get("project","Unknown"),
        "agents_used": s.get("agents_used",[]),
        "tokens":      s.get("tokens",0),
        "cost_usd":    s.get("cost_usd",0),
    })
df_all = pd.DataFrame(rows)
df_all["date"] = pd.to_datetime(df_all["date"])

# ════════════════════════════════════════════
# DATE FILTER BAR
# ════════════════════════════════════════════
st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
fc1, fc2, fc3, fc4, fc5 = st.columns([1.6, 1.6, 1.6, 1.4, 1])

with fc1:
    min_d = df_all["date"].min().date()
    max_d = df_all["date"].max().date()
    # clamp default value ให้อยู่ระหว่าง min_d และ max_d เสมอ
    _default_from = max(min_d, min(max_d, max_d - timedelta(days=29)))
    date_from = st.date_input("📅 ตั้งแต่", value=_default_from,
                               min_value=min_d, max_value=max_d, key="df")
with fc2:
    _default_to = max_d
    date_to = st.date_input("ถึงวันที่", value=_default_to,
                             min_value=min_d, max_value=max_d, key="dt")
with fc3:
    all_projects = ["ทั้งหมด"] + sorted(df_all["project"].unique().tolist())
    proj_filter  = st.selectbox("📁 Project", all_projects)
with fc4:
    preset = st.selectbox("⚡ Preset ด่วน", ["Custom","7 วันล่าสุด","30 วันล่าสุด","เดือนนี้","ทั้งหมด"])
with fc5:
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    show_cost = st.toggle("💰 แสดง Cost", value=True)

st.markdown('</div>', unsafe_allow_html=True)

# Apply preset
today = date.today()
if preset == "7 วันล่าสุด":
    date_from, date_to = today - timedelta(days=6), today
elif preset == "30 วันล่าสุด":
    date_from, date_to = today - timedelta(days=29), today
elif preset == "เดือนนี้":
    date_from, date_to = today.replace(day=1), today
elif preset == "ทั้งหมด":
    date_from, date_to = min_d, max_d

# Filter
mask = (df_all["date"].dt.date >= date_from) & (df_all["date"].dt.date <= date_to)
if proj_filter != "ทั้งหมด":
    mask = mask & (df_all["project"] == proj_filter)
df = df_all[mask].copy()

# Previous period for delta
period_len = (date_to - date_from).days + 1
prev_from  = date_from - timedelta(days=period_len)
prev_to    = date_from - timedelta(days=1)
prev_mask  = (df_all["date"].dt.date >= prev_from) & (df_all["date"].dt.date <= prev_to)
df_prev    = df_all[prev_mask]

# ════════════════════════════════════════════
# KPI CARDS
# ════════════════════════════════════════════
def delta_tag(curr, prev):
    if prev == 0: return ""
    pct = round((curr - prev) / prev * 100)
    c   = "#4ade80" if pct >= 0 else "#f87171"
    sym = "▲" if pct >= 0 else "▼"
    return f"<div class='kpi-delta' style='color:{c}'>{sym} {abs(pct)}% vs ช่วงก่อน</div>"

total_sessions = len(df)
total_tokens   = int(df["tokens"].sum())
total_cost     = df["cost_usd"].sum()
avg_tokens     = int(df["tokens"].mean()) if not df.empty else 0
unique_agents  = len(set(ag for lst in df["agents_used"] for ag in lst)) if not df.empty else 0

prev_sessions  = len(df_prev)
prev_tokens    = int(df_prev["tokens"].sum())
prev_cost      = df_prev["cost_usd"].sum()

k1, k2, k3, k4, k5 = st.columns(5)
cards = [
    (k1, str(total_sessions),        "Sessions",            "#38bdf8", delta_tag(total_sessions, prev_sessions)),
    (k2, f"{total_tokens:,}",         "Tokens สะสม",         "#a78bfa", delta_tag(total_tokens, prev_tokens)),
    (k3, f"${total_cost:.3f}",        "Cost รวม (USD)",       "#34d399", delta_tag(total_cost, prev_cost)),
    (k4, f"{avg_tokens:,}",           "Avg Tokens/Session",  "#f59e0b", ""),
    (k5, str(unique_agents),          "Agent ที่ใช้",         "#ec4899", ""),
]
if not show_cost:
    cards[2] = (k3, "🔒", "Cost (ซ่อน)", "#334155", "")

for col, num, lbl, color, delta in cards:
    col.markdown(f"""
<div class="kpi-card">
  <div class="kpi-num" style='color:{color}'>{num}</div>
  <div class="kpi-lbl">{lbl}</div>
  {delta}
</div>""", unsafe_allow_html=True)

st.markdown("---")

# ════════════════════════════════════════════
# ROW 1: Sessions รายวัน + Agent Ranking
# ════════════════════════════════════════════
chart1, chart2 = st.columns([3, 2])

with chart1:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("**📈 Sessions รายวัน**")
    if not df.empty:
        daily = df.groupby(df["date"].dt.date).agg(
            Sessions=("tokens","count"),
            Tokens=("tokens","sum")
        ).reset_index()
        daily.columns = ["วันที่","Sessions","Tokens"]
        daily["วันที่"] = pd.to_datetime(daily["วันที่"])
        full_range = pd.date_range(start=date_from, end=date_to, freq="D")
        daily = (daily.set_index("วันที่")
                      .reindex(full_range, fill_value=0)
                      .reset_index()
                      .rename(columns={"index":"วันที่"}))
        # Chart toggle
        chart_metric = st.radio("แสดง:", ["Sessions","Tokens"], horizontal=True, key="daily_metric")
        st.line_chart(daily.set_index("วันที่")[chart_metric],
                      height=220, use_container_width=True)
    else:
        st.info("ไม่มีข้อมูลในช่วงที่เลือก")
    st.markdown('</div>', unsafe_allow_html=True)

with chart2:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("**🏆 Agent ที่ใช้บ่อยสุด**")
    agent_usage = a.get("agent_usage", {})

    # Re-count from filtered df
    filtered_agent_counts: dict = {}
    for lst in df["agents_used"]:
        for ag in lst:
            filtered_agent_counts[ag] = filtered_agent_counts.get(ag, 0) + 1

    if filtered_agent_counts:
        top_agents = sorted(filtered_agent_counts.items(), key=lambda x: x[1], reverse=True)[:8]
        max_count  = top_agents[0][1] if top_agents else 1
        for rank, (aid, count) in enumerate(top_agents, 1):
            name  = AGENT_NAMES.get(aid, aid)
            icon  = AGENT_ICONS.get(aid, "🤖")
            pct   = count / max_count * 100
            medal = ["🥇","🥈","🥉"][rank-1] if rank <= 3 else f"#{rank}"
            bar_c = ["#f59e0b","#94a3b8","#b45309"][rank-1] if rank <= 3 else "#3b82f6"
            st.markdown(f"""
<div class="rank-row">
  <span style='font-size:15px;width:26px'>{medal}</span>
  <span style='font-size:17px'>{icon}</span>
  <div style='flex:1;min-width:0'>
    <div style='font-size:11px;font-weight:700;color:#e2e8f0;
      white-space:nowrap;overflow:hidden;text-overflow:ellipsis'>{name}</div>
    <div class="rank-bar-bg">
      <div style='background:{bar_c};height:8px;border-radius:4px;width:{pct:.0f}%'></div>
    </div>
  </div>
  <span style='font-size:13px;font-weight:700;color:{bar_c};min-width:30px;text-align:right'>{count}</span>
</div>""", unsafe_allow_html=True)
    else:
        st.info("ไม่มีข้อมูล Agent")
    st.markdown('</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════
# ROW 2: วันในสัปดาห์ + ชั่วโมง heatmap
# ════════════════════════════════════════════
chart3, chart4 = st.columns([2, 3])

with chart3:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("**📅 วันในสัปดาห์**")
    if not df.empty:
        day_names = ["จ.","อ.","พ.","พฤ.","ศ.","ส.","อา."]
        dow_df = df.groupby("dow").size().reset_index()
        dow_df.columns = ["dow","Sessions"]
        full_dow = pd.DataFrame({"dow": range(7), "วัน": day_names})
        dow_df = full_dow.merge(dow_df, on="dow", how="left").fillna(0)
        dow_df["Sessions"] = dow_df["Sessions"].astype(int)
        st.bar_chart(dow_df.set_index("วัน")["Sessions"],
                     height=210, use_container_width=True)
    else:
        st.info("ไม่มีข้อมูล")
    st.markdown('</div>', unsafe_allow_html=True)

with chart4:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("**⏰ ชั่วโมงที่ใช้งาน**")
    if not df.empty:
        hour_df = df.groupby("hour").size().reset_index()
        hour_df.columns = ["Hour","Sessions"]
        all_hours = pd.DataFrame({"Hour": range(24)})
        hour_df = all_hours.merge(hour_df, on="Hour", how="left").fillna(0)
        hour_df["Sessions"] = hour_df["Sessions"].astype(int)
        hour_df["label"]    = hour_df["Hour"].map(lambda h: f"{h:02d}:00")
        st.bar_chart(hour_df.set_index("label")["Sessions"],
                     height=210, use_container_width=True)
    else:
        st.info("ไม่มีข้อมูล")
    st.markdown('</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════
# ROW 3: Trend รายสัปดาห์ + Top Projects
# ════════════════════════════════════════════
chart5, chart6 = st.columns([3, 2])

with chart5:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("**📊 Trend รายสัปดาห์**")
    if not df.empty:
        weekly_df = df.groupby("week").size().reset_index()
        weekly_df.columns = ["สัปดาห์","Sessions"]
        weekly_df = weekly_df.sort_values("สัปดาห์").tail(12)
        # shorten label to just week number
        weekly_df["สัปดาห์"] = weekly_df["สัปดาห์"].str[-4:]
        st.bar_chart(weekly_df.set_index("สัปดาห์")["Sessions"],
                     height=210, use_container_width=True)
    else:
        st.info("ไม่มีข้อมูล")
    st.markdown('</div>', unsafe_allow_html=True)

with chart6:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("**📁 Project ที่ใช้งานบ่อย**")
    if not df.empty:
        proj_df = df.groupby("project").size().reset_index()
        proj_df.columns = ["Project","Sessions"]
        proj_df = proj_df.sort_values("Sessions", ascending=False).head(6)
        max_pc  = proj_df["Sessions"].max()
        for _, row in proj_df.iterrows():
            pct   = row["Sessions"] / max_pc * 100
            pname = str(row["Project"])[:28] + ("…" if len(str(row["Project"])) > 28 else "")
            st.markdown(f"""
<div class="rank-row">
  <span style='font-size:18px'>📁</span>
  <div style='flex:1;min-width:0'>
    <div style='font-size:11px;font-weight:700;color:#e2e8f0;
      white-space:nowrap;overflow:hidden;text-overflow:ellipsis'>{pname}</div>
    <div class="rank-bar-bg">
      <div style='background:#6366f1;height:8px;border-radius:4px;width:{pct:.0f}%'></div>
    </div>
  </div>
  <span style='font-size:12px;font-weight:700;color:#818cf8;min-width:42px;text-align:right'>
    {int(row["Sessions"])}
  </span>
</div>""", unsafe_allow_html=True)
    else:
        st.info("ไม่มีข้อมูล")
    st.markdown('</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════
# RECENT SESSIONS TIMELINE
# ════════════════════════════════════════════
st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown("**🕐 Session ล่าสุด**")

src1, src2 = st.columns([3,1])
with src1:
    search_q = st.text_input("🔍 ค้นหา project", placeholder="พิมพ์ชื่อ project...",
                              label_visibility="collapsed")
with src2:
    show_n = st.selectbox("แสดง", [5, 10, 20, 50], label_visibility="collapsed")

display_df = df.copy().sort_values("datetime", ascending=False)
if search_q:
    display_df = display_df[display_df["project"].str.contains(search_q, case=False, na=False)]
display_df = display_df.head(show_n)

for _, s in display_df.iterrows():
    try:
        dt_label = s["datetime"].strftime("%d %b %Y · %H:%M")
    except:
        dt_label = str(s["datetime"])[:16]
    agents_used = s.get("agents_used", [])
    agent_str   = " · ".join(
        f"{AGENT_ICONS.get(ag,'🤖')} {AGENT_NAMES.get(ag,ag)}" for ag in agents_used[:4]
    )
    if len(agents_used) > 4:
        agent_str += f" +{len(agents_used)-4}"
    cost_html = (f"<span style='color:#a78bfa'>{int(s['tokens']):,} tokens"
                 + (f" · ${s['cost_usd']:.4f}" if show_cost else "")
                 + "</span>")
    st.markdown(f"""
<div style='background:rgba(15,23,42,.8);border:1px solid #1e293b;border-radius:10px;
  padding:12px 16px;margin-bottom:8px;display:flex;align-items:center;gap:16px'>
  <div style='font-size:24px'>📁</div>
  <div style='flex:1'>
    <div style='font-size:13px;font-weight:700;color:#e2e8f0'>{s['project']}</div>
    <div style='font-size:11px;color:#64748b;margin-top:2px'>{agent_str or "—"}</div>
  </div>
  <div style='text-align:right;font-size:12px;color:#64748b'>
    <div>{dt_label}</div>
    {cost_html}
  </div>
</div>""", unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════
# EXPORT
# ════════════════════════════════════════════
st.markdown("---")
ex1, ex2 = st.columns(2)
with ex1:
    export_df = df[["datetime","project","tokens","cost_usd"]].copy()
    export_df["datetime"] = export_df["datetime"].astype(str)
    export_df["agents"]   = df["agents_used"].apply(lambda x: ", ".join(x))
    csv_data = export_df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button("⬇️ Export CSV", data=csv_data,
                       file_name=f"analytics_{date_from}_{date_to}.csv",
                       mime="text/csv", use_container_width=True)
with ex2:
    summary = {
        "ช่วงเวลา": f"{date_from} ถึง {date_to}",
        "Sessions": total_sessions,
        "Tokens": total_tokens,
        "Cost_USD": round(total_cost, 5),
        "Avg_Tokens": avg_tokens,
        "Agent_ที่ใช้": unique_agents,
    }
    st.download_button("⬇️ Export Summary JSON",
                       data=json.dumps(summary, ensure_ascii=False, indent=2),
                       file_name=f"summary_{date_from}_{date_to}.json",
                       mime="application/json", use_container_width=True)
