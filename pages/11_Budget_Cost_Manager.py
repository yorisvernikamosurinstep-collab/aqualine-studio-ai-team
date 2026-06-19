import streamlit as st
import streamlit.components.v1 as components
import requests
import json
import os
from datetime import datetime
import csv
from io import StringIO

import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ui_settings import inject_global_font_css

st.set_page_config(
    page_title="Budget & Cost Manager — AQUALINE",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🔐 กันเข้าหน้านี้ตรงผ่าน URL โดยไม่ผ่านด่านล็อกอินที่หน้าแรก
from auth_guard import require_auth
require_auth()

# 🧭 PAGE-VISIT MARKER — ใช้โดยหน้า "งานบริษัทอาควาไลน์" เพื่อรู้ว่าผู้ใช้เปิดหน้าใหม่จริง
st.session_state["_active_page"] = __file__

# ฟอนต์/ขนาดตัวอักษรที่ผู้ใช้กำหนดเอง (หน้า Design UX/UI) — ใช้ร่วมกันทุกหน้า
st.markdown(inject_global_font_css(), unsafe_allow_html=True)

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
  padding:20px 28px;display:flex;align-items:center;gap:16px;position:relative;overflow:hidden;margin-bottom:24px;}
.page-header::after{content:'';position:absolute;inset:0;
  background:repeating-linear-gradient(90deg,transparent,transparent 80px,rgba(56,189,248,.03) 80px,rgba(56,189,248,.03) 81px);pointer-events:none;}
.page-title{font-family:'IBM Plex Mono',monospace;font-size:20px;font-weight:700;color:#f1f5f9;}
.page-sub{font-size:11px;color:#475569;font-family:'IBM Plex Mono',monospace;margin-top:3px;}

.section-title{font-family:'IBM Plex Mono',monospace;font-size:13px;font-weight:700;color:#94a3b8;
  letter-spacing:1px;text-transform:uppercase;margin:20px 0 12px;padding-bottom:6px;border-bottom:1px solid #1e293b;}

.budget-stat{background:rgba(15,23,42,.8);border:1px solid #1e293b;border-radius:12px;padding:16px;text-align:center;}
.budget-stat-val{font-family:'IBM Plex Mono',monospace;font-size:28px;font-weight:700;line-height:1;}
.budget-stat-lbl{font-size:11px;color:#475569;margin-top:4px;font-family:'IBM Plex Mono',monospace;}

.expense-row{background:rgba(15,23,42,.6);border:1px solid #1e293b;border-radius:8px;
  padding:10px 14px;margin-bottom:6px;display:flex;align-items:center;gap:12px;}
.expense-cat{font-size:10px;padding:2px 8px;border-radius:10px;border:1px solid;font-family:'IBM Plex Mono',monospace;}
.expense-desc{flex:1;font-size:12px;color:#94a3b8;}
.expense-amt{font-family:'IBM Plex Mono',monospace;font-size:13px;font-weight:700;}
.expense-date{font-size:10px;color:#334155;font-family:'IBM Plex Mono',monospace;}

.alert-box{border-radius:8px;padding:10px 14px;margin-bottom:8px;font-size:12px;font-family:'IBM Plex Mono',monospace;}
.alert-warning{background:rgba(251,191,36,.08);border:1px solid rgba(251,191,36,.3);color:#fbbf24;}
.alert-danger{background:rgba(248,113,113,.08);border:1px solid rgba(248,113,113,.3);color:#f87171;}
.alert-ok{background:rgba(52,211,153,.08);border:1px solid rgba(52,211,153,.3);color:#34d399;}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# PERSISTENCE — budget_data.json (รายจ่าย/งบประมาณ ต้องอยู่ข้าม session ไม่หายตอนปิดเบราว์เซอร์)
# ══════════════════════════════════════════════════════════════════
BUDGET_DATA_FILE = "budget_data.json"

def load_budget_data() -> dict:
    if os.path.exists(BUDGET_DATA_FILE):
        try:
            with open(BUDGET_DATA_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
            return {
                "expenses": d.get("expenses", []),
                "budget_limit": d.get("budget_limit", 5000.0),
                "alert_pct": d.get("alert_pct", 80),
            }
        except Exception:
            pass
    return {"expenses": [], "budget_limit": 5000.0, "alert_pct": 80}

def save_budget_data():
    try:
        with open(BUDGET_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "expenses": st.session_state.bcm_expenses,
                "budget_limit": st.session_state.bcm_budget_limit,
                "alert_pct": st.session_state.bcm_alert_pct,
            }, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ══════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════
if "bcm_data_loaded" not in st.session_state:
    _bcm_persisted = load_budget_data()
    st.session_state.bcm_expenses     = _bcm_persisted["expenses"]
    st.session_state.bcm_budget_limit = _bcm_persisted["budget_limit"]
    st.session_state.bcm_alert_pct    = _bcm_persisted["alert_pct"]
    st.session_state.bcm_data_loaded  = True
if "bcm_expenses"     not in st.session_state: st.session_state.bcm_expenses     = []
if "bcm_budget_limit" not in st.session_state: st.session_state.bcm_budget_limit = 5000.0
if "bcm_alert_pct"    not in st.session_state: st.session_state.bcm_alert_pct    = 80

CATEGORIES = {
    "Gemini Flash":   {"color":"#38bdf8", "icon":"⚡"},
    "Gemini Pro":     {"color":"#818cf8", "icon":"🔮"},
    "Claude Sonnet":  {"color":"#a78bfa", "icon":"🟣"},
    "Claude Opus":    {"color":"#f472b6", "icon":"🔴"},
    "GPT-4o":         {"color":"#34d399", "icon":"🟢"},
    "DALL-E / Image": {"color":"#fb923c", "icon":"🎨"},
    "อื่นๆ":           {"color":"#94a3b8", "icon":"📦"},
}

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
    st.page_link("ai_team.py",                          label="🤖 AI Special Team")
    st.page_link("pages/1_งานบริษัทอาควาไลน์.py",        label="🏢 งานบริษัทอาควาไลน์")
    st.page_link("pages/2_คุยกับ_AI_Agent.py",           label="💬 คุยกับ AI Agent")
    st.page_link("pages/3_Live_Chat.py",                label="💬 Live Chat")
    st.page_link("pages/4_สร้าง_Brief_ด่วน.py",          label="📝 สร้าง Brief ด่วน")
    st.page_link("pages/5_Workflow_Builder.py",         label="🏭 Content Factory")
    st.page_link("pages/6_ประวัติการประชุม.py",          label="🕐 ประวัติการประชุม")
    st.page_link("pages/7_สถิติการใช้งาน.py",            label="📈 สถิติการใช้งาน")
    st.page_link("pages/8_แฟ้มงาน.py",                   label="📁 แฟ้มงาน")
    st.page_link("pages/9_คลัง_Prompt.py",               label="📚 คลัง Prompt")
    st.page_link("pages/10_Dashboard.py",               label="📊 Dashboard")
    st.page_link("pages/11_Budget_Cost_Manager.py",     label="💰 Budget & Cost")
    st.page_link("pages/12_Report_Generator.py",        label="📄 Report Generator")
    st.page_link("pages/13_Agent_Persona_Editor.py",    label="🧬 Agent Persona Editor")
    st.page_link("pages/14_Settings_Config.py",         label="⚙️ Settings & Config")
    st.page_link("pages/15_KONEX.py",                   label="🧠 KONEX")
    st.page_link("pages/16_Design_UX_UI.py",            label="🎨 Design UX/UI")
    st.markdown("---")
    st.markdown("<div style='font-size:10px;color:#475569;font-family:IBM Plex Mono,monospace;padding:0 0 6px'>⚙️ ตั้งค่างบประมาณ</div>", unsafe_allow_html=True)
    _prev_limit = st.session_state.bcm_budget_limit
    _prev_alert = st.session_state.bcm_alert_pct
    st.session_state.bcm_budget_limit = st.number_input(
        "งบประมาณ/เดือน (฿)", min_value=100.0, max_value=100000.0,
        value=st.session_state.bcm_budget_limit, step=100.0, key="budget_limit_input"
    )
    st.session_state.bcm_alert_pct = st.slider(
        "แจ้งเตือนเมื่อใช้ถึง (%)", 50, 95,
        st.session_state.bcm_alert_pct, key="alert_pct_slider"
    )
    if st.session_state.bcm_budget_limit != _prev_limit or st.session_state.bcm_alert_pct != _prev_alert:
        save_budget_data()

# ══════════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════════
st.markdown("""
<div class="page-header">
  <div style='font-size:36px'>💰</div>
  <div>
    <div class="page-title">BUDGET & COST MANAGER</div>
    <div class="page-sub">ติดตามค่าใช้จ่าย AI · Budget Alert · Gemini vs Claude Breakdown</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# COMPUTE STATS
# ══════════════════════════════════════════════════════════════════
expenses = st.session_state.bcm_expenses
limit    = st.session_state.bcm_budget_limit
alert_at = limit * (st.session_state.bcm_alert_pct / 100)
total_spent = sum(e["amount"] for e in expenses)
remaining   = limit - total_spent
used_pct    = (total_spent / limit * 100) if limit > 0 else 0

# ── Category breakdown ──
cat_totals = {}
for e in expenses:
    cat = e.get("category", "อื่นๆ")
    cat_totals[cat] = cat_totals.get(cat, 0) + e["amount"]

# ══════════════════════════════════════════════════════════════════
# ALERT BANNER
# ══════════════════════════════════════════════════════════════════
if used_pct >= 100:
    st.markdown(f"<div class='alert-box alert-danger'>🚨 เกินงบแล้ว! ใช้ไป ฿{total_spent:,.2f} จาก ฿{limit:,.2f} ({used_pct:.1f}%)</div>", unsafe_allow_html=True)
elif used_pct >= st.session_state.bcm_alert_pct:
    st.markdown(f"<div class='alert-box alert-warning'>⚠️ ใกล้ถึงงบแล้ว! ใช้ไป {used_pct:.1f}% · เหลือ ฿{remaining:,.2f}</div>", unsafe_allow_html=True)
elif total_spent > 0:
    st.markdown(f"<div class='alert-box alert-ok'>✅ อยู่ในงบ — ใช้ไป {used_pct:.1f}% · เหลือ ฿{remaining:,.2f}</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# KPI ROW
# ══════════════════════════════════════════════════════════════════
c1, c2, c3, c4 = st.columns(4)
stats = [
    (c1, "ใช้ไปแล้ว", f"฿{total_spent:,.2f}", "#f87171" if used_pct >= 100 else "#fbbf24" if used_pct >= 80 else "#38bdf8"),
    (c2, "งบที่เหลือ", f"฿{max(remaining,0):,.2f}", "#34d399" if remaining > 0 else "#f87171"),
    (c3, "งบ/เดือน", f"฿{limit:,.2f}", "#94a3b8"),
    (c4, "รายการ", str(len(expenses)), "#a78bfa"),
]
for col, lbl, val, color in stats:
    with col:
        st.markdown(f"""
        <div class="budget-stat">
          <div class="budget-stat-val" style='color:{color}'>{val}</div>
          <div class="budget-stat-lbl">{lbl}</div>
        </div>""", unsafe_allow_html=True)

# ── Progress bar ──
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
bar_color = "#f87171" if used_pct >= 100 else "#fbbf24" if used_pct >= 80 else "#38bdf8"
st.markdown(f"""
<div style='background:#1e293b;border-radius:6px;height:10px;overflow:hidden;margin-bottom:4px'>
  <div style='width:{min(used_pct,100):.1f}%;height:10px;background:{bar_color};border-radius:6px;
    transition:width .5s'></div>
</div>
<div style='display:flex;justify-content:space-between;font-family:IBM Plex Mono,monospace;font-size:10px;color:#334155'>
  <span>฿0</span><span>Alert: ฿{alert_at:,.0f} ({st.session_state.bcm_alert_pct}%)</span><span>฿{limit:,.0f}</span>
</div>""", unsafe_allow_html=True)

st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# ADD EXPENSE
# ══════════════════════════════════════════════════════════════════
col_form, col_breakdown = st.columns([1.1, 0.9])

with col_form:
    st.markdown("<div class='section-title'>➕ บันทึกรายจ่าย</div>", unsafe_allow_html=True)
    with st.form("add_expense_form", clear_on_submit=True):
        fc1, fc2 = st.columns(2)
        with fc1:
            cat = st.selectbox("โมเดล / หมวด", list(CATEGORIES.keys()), key="exp_cat")
        with fc2:
            amt = st.number_input("จำนวน (฿)", min_value=0.01, step=1.0, format="%.2f", key="exp_amt")
        desc    = st.text_input("รายละเอียด (ไม่จำเป็น)", key="exp_desc")
        session = st.text_input("Session/งาน (ไม่จำเป็น)", key="exp_session")
        submitted = st.form_submit_button("💾 บันทึก", use_container_width=True, type="primary")
        if submitted and amt > 0:
            st.session_state.bcm_expenses.append({
                "category": cat,
                "amount":   amt,
                "desc":     desc,
                "session":  session,
                "date":     datetime.now().strftime("%d/%m/%Y %H:%M"),
            })
            save_budget_data()
            st.rerun()

    # ── Export CSV ──
    if expenses:
        st.markdown("<div class='section-title'>📥 Export</div>", unsafe_allow_html=True)
        buf = StringIO()
        writer = csv.DictWriter(buf, fieldnames=["date","category","amount","desc","session"])
        writer.writeheader()
        writer.writerows(expenses)
        st.download_button(
            "📥 Download CSV",
            data=buf.getvalue(),
            file_name=f"aqualine_costs_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True,
            key="dl_csv_btn"
        )
        if st.button("🗑️ ล้างข้อมูลทั้งหมด", use_container_width=True, key="clear_all_exp"):
            st.session_state.bcm_expenses = []
            save_budget_data()
            st.rerun()

with col_breakdown:
    st.markdown("<div class='section-title'>📊 Breakdown by Model</div>", unsafe_allow_html=True)
    if cat_totals:
        for cat_name, cat_amt in sorted(cat_totals.items(), key=lambda x: x[1], reverse=True):
            info  = CATEGORIES.get(cat_name, {"color":"#94a3b8","icon":"📦"})
            pct   = (cat_amt / total_spent * 100) if total_spent > 0 else 0
            st.markdown(f"""
            <div style='margin-bottom:10px'>
              <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:3px'>
                <span style='font-size:12px;color:#94a3b8'>{info["icon"]} {cat_name}</span>
                <span style='font-family:IBM Plex Mono,monospace;font-size:12px;color:{info["color"]}'>฿{cat_amt:,.2f} ({pct:.0f}%)</span>
              </div>
              <div style='background:#1e293b;border-radius:3px;height:5px;overflow:hidden'>
                <div style='width:{pct:.1f}%;height:5px;background:{info["color"]};border-radius:3px'></div>
              </div>
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='text-align:center;padding:40px 0;color:#334155;font-family:IBM Plex Mono,monospace;font-size:12px'>
          ยังไม่มีข้อมูล — บันทึกรายจ่ายก่อนครับ
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# EXPENSE TABLE
# ══════════════════════════════════════════════════════════════════
st.markdown("<div class='section-title'>📋 รายการทั้งหมด</div>", unsafe_allow_html=True)

# ── Filter bar ──
col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    filter_cat = st.selectbox("🔍 กรองหมวด:", ["ทั้งหมด"] + list(CATEGORIES.keys()), key="exp_filter_cat")
with col_f2:
    search_desc = st.text_input("🔍 ค้นหา description:", placeholder="พิมพ์คำค้น...", key="exp_search")
with col_f3:
    sort_exp = st.selectbox("🔢 เรียง:", ["ใหม่ก่อน", "เก่าก่อน", "มากสุด", "น้อยสุด"], key="exp_sort")

filtered_expenses = expenses.copy()
if filter_cat != "ทั้งหมด":
    filtered_expenses = [e for e in filtered_expenses if e.get("category") == filter_cat]
if search_desc:
    filtered_expenses = [e for e in filtered_expenses if search_desc.lower() in (e.get("desc","") + e.get("session","")).lower()]
if sort_exp == "ใหม่ก่อน":
    filtered_expenses = list(reversed(filtered_expenses))
elif sort_exp == "มากสุด":
    filtered_expenses = sorted(filtered_expenses, key=lambda x: x["amount"], reverse=True)
elif sort_exp == "น้อยสุด":
    filtered_expenses = sorted(filtered_expenses, key=lambda x: x["amount"])

# ── Export all formats ──
if filtered_expenses:
    col_ex1, col_ex2, col_ex3 = st.columns(3)
    with col_ex1:
        buf2 = StringIO()
        w2 = csv.DictWriter(buf2, fieldnames=["date","category","amount","desc","session"])
        w2.writeheader(); w2.writerows(filtered_expenses)
        st.download_button("📥 Export CSV", data=buf2.getvalue().encode("utf-8-sig"),
            file_name=f"costs_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv",
            use_container_width=True, key="exp_csv2")
    with col_ex2:
        jexp = json.dumps({"exported": datetime.now().isoformat(),
                           "total": sum(e["amount"] for e in filtered_expenses),
                           "expenses": filtered_expenses}, ensure_ascii=False, indent=2)
        st.download_button("📥 Export JSON", data=jexp.encode("utf-8"),
            file_name=f"costs_{datetime.now().strftime('%Y%m%d')}.json", mime="application/json",
            use_container_width=True, key="exp_json")
    with col_ex3:
        md_exp = [f"# AQUALINE Cost Report\nExported: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n",
                  f"**รวม:** ฿{sum(e['amount'] for e in filtered_expenses):,.2f} | **{len(filtered_expenses)} รายการ**\n\n",
                  "| วันที่ | หมวด | จำนวน | รายละเอียด |\n|---|---|---|---|\n"]
        for e in filtered_expenses:
            md_exp.append(f"| {e['date']} | {e['category']} | ฿{e['amount']:,.2f} | {e.get('desc','')} |\n")
        st.download_button("📥 Export Markdown", data="".join(md_exp).encode("utf-8"),
            file_name=f"costs_{datetime.now().strftime('%Y%m%d')}.md", mime="text/markdown",
            use_container_width=True, key="exp_md")

st.markdown(f"<div style='font-size:12px;color:#475569;margin:8px 0'>แสดง {len(filtered_expenses)} / {len(expenses)} รายการ</div>", unsafe_allow_html=True)

if filtered_expenses:
    for i, e in enumerate(filtered_expenses):
        info  = CATEGORIES.get(e["category"], {"color":"#94a3b8","icon":"📦"})
        ri    = expenses.index(e) if e in expenses else i
        col_e, col_del = st.columns([8, 1])
        with col_e:
            st.markdown(f"""
            <div class="expense-row">
              <span class="expense-cat" style='color:{info["color"]};border-color:{info["color"]}40'>
                {info["icon"]} {e["category"]}
              </span>
              <div class="expense-desc">{e.get("desc","") or e.get("session","") or "—"}</div>
              <div class="expense-amt" style='color:{info["color"]}'>฿{e["amount"]:,.2f}</div>
              <div class="expense-date">{e["date"]}</div>
            </div>""", unsafe_allow_html=True)
        with col_del:
            if st.button("✕", key=f"del_exp_{ri}", help="ลบรายการนี้"):
                st.session_state.bcm_expenses.pop(ri)
                save_budget_data()
                st.rerun()
else:
    st.markdown("""
    <div style='text-align:center;padding:40px;color:#334155;font-family:IBM Plex Mono,monospace;font-size:12px;
      border:1px dashed #1e293b;border-radius:10px'>
      ยังไม่มีรายการ — กดบันทึกรายจ่ายด้านบน
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# AI COST ADVISOR
# ══════════════════════════════════════════════════════════════════
st.markdown("<div class='section-title'>🧠 AI Cost Advisor</div>", unsafe_allow_html=True)
if st.button("💡 ให้ AI แนะนำการลดค่าใช้จ่าย", use_container_width=True, type="primary"):
    prompt = f"""
ข้อมูลค่าใช้จ่าย AI ของทีม AQUALINE:
- งบประมาณ/เดือน: ฿{limit:,.2f}
- ใช้ไปแล้ว: ฿{total_spent:,.2f} ({used_pct:.1f}%)
- เหลือ: ฿{remaining:,.2f}
- Breakdown: {json.dumps({k: round(v,2) for k,v in cat_totals.items()}, ensure_ascii=False)}
- จำนวนรายการ: {len(expenses)} รายการ

กรุณาวิเคราะห์ค่าใช้จ่าย แนะนำโมเดลที่คุ้มค่า และวิธีลดต้นทุน AI โดยไม่กระทบประสิทธิภาพ
เปรียบเทียบ Gemini vs Claude อย่างเป็นกลาง ตอบเป็นภาษาไทย กระชับ actionable
"""
    with st.spinner("💡 AI กำลังวิเคราะห์ค่าใช้จ่าย..."):
        try:
            @st.cache_data(ttl=60, show_spinner=False)
            def get_model_b(k):
                r = requests.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={k}", timeout=8)
                if r.status_code == 200:
                    avail = [m["name"] for m in r.json().get("models",[]) if "generateContent" in m.get("supportedGenerationMethods",[])]
                    for p in ["models/gemini-2.5-flash-preview-05-20","models/gemini-2.5-flash","models/gemini-1.5-flash-latest","models/gemini-1.5-flash"]:
                        if p in avail: return p
                return "models/gemini-1.5-flash"
            model = get_model_b(API_KEY)
            resp = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={API_KEY}",
                json={"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"temperature":0.5,"maxOutputTokens":2048}},
                timeout=60
            )
            if resp.status_code == 200:
                result = resp.json()["candidates"][0]["content"]["parts"][0].get("text","")
                st.markdown(f"""
                <div style='background:rgba(15,23,42,.9);border:1px solid rgba(56,189,248,.3);border-radius:12px;padding:20px;margin-top:8px'>
                  <div style='font-family:IBM Plex Mono,monospace;font-size:10px;color:#38bdf8;margin-bottom:10px'>💡 COST ADVISOR REPORT</div>
                  <div style='font-size:13px;color:#cbd5e1;line-height:1.8;white-space:pre-wrap'>{result}</div>
                </div>""", unsafe_allow_html=True)
            else:
                st.error(f"❌ API Error {resp.status_code}")
        except Exception as e:
            st.error(f"⚠️ {str(e)[:100]}")