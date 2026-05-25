import streamlit as st
import json
import os
import base64
from datetime import datetime

st.set_page_config(page_title="Project Vault — AQUALINE", layout="wide")

VAULT_FILE = "project_vault.json"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=IBM+Plex+Sans+Thai:wght@300;400;600;700&display=swap');
*,*::before,*::after{box-sizing:border-box;}
.stApp{background:linear-gradient(135deg,#0b0f19 0%,#1a1a2e 100%);color:#e2e8f0;font-family:'IBM Plex Sans Thai',sans-serif;}
[data-testid="stSidebar"]{background:rgba(15,23,42,.8);border-right:1px solid #1e293b;}
.header-box{background:linear-gradient(90deg,rgba(245,158,11,.15),rgba(251,146,60,.1));
  border:1px solid #f59e0b44;border-radius:12px;padding:16px 24px;margin-bottom:24px;}
.stat-box{background:rgba(15,23,42,.8);border:1px solid #1e293b;border-radius:10px;padding:14px;text-align:center;}
.stat-num{font-size:28px;font-weight:900;color:#fbbf24;}
.stat-lbl{font-size:12px;color:#64748b;}

/* tag/label styles */
.tag-pill{display:inline-flex;align-items:center;gap:4px;padding:2px 10px;border-radius:20px;
  font-size:11px;font-weight:600;margin:2px;font-family:'IBM Plex Mono',monospace;cursor:default;}
.tag-red   {background:rgba(239,68,68,.15);  border:1px solid rgba(239,68,68,.35);  color:#f87171;}
.tag-amber {background:rgba(251,191,36,.15); border:1px solid rgba(251,191,36,.35); color:#fbbf24;}
.tag-green {background:rgba(52,211,153,.15); border:1px solid rgba(52,211,153,.35); color:#34d399;}
.tag-blue  {background:rgba(56,189,248,.15); border:1px solid rgba(56,189,248,.35); color:#38bdf8;}
.tag-purple{background:rgba(167,139,250,.15);border:1px solid rgba(167,139,250,.35);color:#a78bfa;}
.tag-pink  {background:rgba(244,114,182,.15);border:1px solid rgba(244,114,182,.35);color:#f472b6;}
.tag-gray  {background:rgba(100,116,139,.15);border:1px solid rgba(100,116,139,.35);color:#94a3b8;}

/* file attach card */
.file-card{display:flex;align-items:center;gap:10px;background:rgba(15,23,42,.9);border:1px solid #1e293b;
  border-radius:8px;padding:8px 12px;margin:4px 0;}
.file-icon{font-size:20px;flex-shrink:0;}
.file-meta{font-size:11px;color:#64748b;font-family:'IBM Plex Mono',monospace;}
.file-name{font-size:12px;color:#e2e8f0;font-weight:600;}

.stButton>button{font-family:'IBM Plex Mono',monospace!important;font-size:12px!important;font-weight:600!important;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="header-box">
  <span style='font-size:28px;font-weight:900;color:#fff'>🗄️ PROJECT VAULT</span>
  <span style='font-size:13px;color:#fbbf24;margin-left:16px'>จัดการแฟ้มงานทั้งหมด</span>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# TAG SYSTEM
# ══════════════════════════════════════════════════════════════════
PRESET_TAGS = {
    "🔴 เร่งด่วน":    "red",
    "🟡 กำลังทำ":     "amber",
    "🟢 เสร็จแล้ว":   "green",
    "🔵 รอข้อมูล":    "blue",
    "🟣 สำคัญ":       "purple",
    "🩷 Campaign":    "pink",
    "⚪ Backlog":     "gray",
}

def tag_html(tag_text: str) -> str:
    color = PRESET_TAGS.get(tag_text, "gray")
    return f"<span class='tag-pill tag-{color}'>{tag_text}</span>"

# ══════════════════════════════════════════════════════════════════
# FILE HELPERS
# ══════════════════════════════════════════════════════════════════
FILE_ICONS = {
    "image": "🖼️", "pdf": "📄", "video": "🎬", "audio": "🎵",
    "word": "📝", "excel": "📊", "zip": "🗜️", "text": "📃", "other": "📎",
}

def get_file_icon(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext in ("jpg","jpeg","png","webp","gif","heic"): return FILE_ICONS["image"]
    if ext == "pdf":                                    return FILE_ICONS["pdf"]
    if ext in ("mp4","mov","avi","webm"):               return FILE_ICONS["video"]
    if ext in ("mp3","wav","ogg","aac","m4a"):          return FILE_ICONS["audio"]
    if ext in ("doc","docx"):                           return FILE_ICONS["word"]
    if ext in ("xls","xlsx","csv"):                     return FILE_ICONS["excel"]
    if ext in ("zip","rar","7z"):                       return FILE_ICONS["zip"]
    if ext in ("txt","md","json","py","js","ts"):       return FILE_ICONS["text"]
    return FILE_ICONS["other"]

def format_filesize(nbytes: int) -> str:
    if nbytes < 1024:       return f"{nbytes} B"
    if nbytes < 1024**2:    return f"{nbytes/1024:.1f} KB"
    return f"{nbytes/1024**2:.1f} MB"

# ══════════════════════════════════════════════════════════════════
# VAULT LOAD / SAVE
# ══════════════════════════════════════════════════════════════════
def load_vault():
    if os.path.exists(VAULT_FILE):
        try:
            with open(VAULT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for k in data:
                    if "knowledge" not in data[k]: data[k]["knowledge"] = ""
                    if "history"   not in data[k]: data[k]["history"]   = []
                    if "tags"      not in data[k]: data[k]["tags"]      = []   # ← ใหม่
                    if "files"     not in data[k]: data[k]["files"]     = []   # ← ใหม่
                return data
        except: pass
    return {"Default Project": {"url": "", "brief": "", "knowledge": "", "history": [], "tags": [], "files": []}}

def save_vault(v):
    with open(VAULT_FILE, "w", encoding="utf-8") as f:
        json.dump(v, f, ensure_ascii=False, indent=4)

vault = load_vault()

# ── Stats ──
total_projects  = len(vault)
total_history   = sum(len(v.get("history", [])) for v in vault.values())
total_knowledge = sum(len(v.get("knowledge", "")) for v in vault.values())
total_files     = sum(len(v.get("files", [])) for v in vault.values())

c1, c2, c3, c4 = st.columns(4)
for col, num, lbl in [
    (c1, str(total_projects),          "Project ทั้งหมด"),
    (c2, str(total_history),           "Session History รวม"),
    (c3, f"{total_knowledge//1000}K",  "Knowledge ที่บันทึก"),
    (c4, str(total_files),             "ไฟล์แนบรวม"),
]:
    col.markdown(f"""<div class="stat-box">
  <div class="stat-num">{num}</div>
  <div class="stat-lbl">{lbl}</div>
</div>""", unsafe_allow_html=True)

st.markdown("---")

# ── Create new project ──
with st.expander("➕ สร้าง Project ใหม่", expanded=False):
    new_name = st.text_input("ชื่อ Project ใหม่:", placeholder="เช่น Campaign-Jun-2569")
    new_init_tags = st.multiselect("Label เริ่มต้น (ไม่บังคับ):", list(PRESET_TAGS.keys()), key="new_proj_tags")
    if st.button("✅ สร้าง", type="primary"):
        if new_name and new_name not in vault:
            vault[new_name] = {"url": "", "brief": "", "knowledge": "", "history": [], "tags": list(new_init_tags), "files": []}
            save_vault(vault)
            st.success(f"✅ สร้าง '{new_name}' แล้ว!")
            st.rerun()
        elif new_name in vault:
            st.error("มีชื่อนี้อยู่แล้วครับ")

st.markdown("---")

# ── Search & Tag Filter ──
col_search, col_tag_filter = st.columns([3, 2])
with col_search:
    search = st.text_input("🔍 ค้นหา Project:", placeholder="พิมพ์ชื่อ...")
with col_tag_filter:
    tag_filter = st.multiselect("🏷️ กรองด้วย Label:", list(PRESET_TAGS.keys()), key="tag_filter_main")

# ══════════════════════════════════════════════════════════════════
# PROJECT LIST
# ══════════════════════════════════════════════════════════════════
for pname, pdata in vault.items():
    if search and search.lower() not in pname.lower():
        continue
    if tag_filter and not any(t in pdata.get("tags", []) for t in tag_filter):
        continue

    history     = pdata.get("history", [])
    brief       = pdata.get("brief", "")
    url         = pdata.get("url", "")
    knowledge   = pdata.get("knowledge", "")
    tags        = pdata.get("tags", [])
    files       = pdata.get("files", [])
    last_session = history[-1]["timestamp"] if history else "—"

    tags_display = "".join(tag_html(t) for t in tags) if tags else ""
    file_count_badge = f"<span style='font-size:10px;color:#38bdf8;font-family:IBM Plex Mono,monospace;margin-left:8px'>📎 {len(files)} ไฟล์</span>" if files else ""

    with st.expander(f"📁 {pname}  ·  {len(history)} session  ·  last: {last_session}"):
        # tag preview row
        if tags_display or file_count_badge:
            st.markdown(f"<div style='margin-bottom:8px'>{tags_display}{file_count_badge}</div>", unsafe_allow_html=True)

        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 Brief & URL", "🏷️ Tags & Labels", "📎 ไฟล์แนบ", "📚 Knowledge", "🕐 History"])

        # ── TAB 1: Brief & URL ──
        with tab1:
            new_url = st.text_input("URL:", value=url, key=f"url_{pname}")
            new_brief = st.text_area("Brief:", value=brief, height=180, key=f"brief_{pname}")
            col_save, col_del = st.columns([2, 1])
            with col_save:
                if st.button("💾 บันทึก", key=f"save_{pname}", use_container_width=True, type="primary"):
                    vault[pname]["url"]   = new_url
                    vault[pname]["brief"] = new_brief
                    save_vault(vault)
                    st.success("✅ บันทึกแล้ว!")
            with col_del:
                if pname != "Default Project":
                    if st.button("🗑️ ลบ Project", key=f"del_{pname}", use_container_width=True):
                        del vault[pname]
                        save_vault(vault)
                        st.warning(f"ลบ '{pname}' แล้ว")
                        st.rerun()

        # ── TAB 2: TAGS & LABELS ──
        with tab2:
            st.markdown("<div style='font-size:12px;color:#64748b;margin-bottom:8px'>เลือก Label ที่ต้องการติด (เลือกได้หลายอัน):</div>", unsafe_allow_html=True)

            # preset tags as toggle buttons
            current_tags = list(vault[pname].get("tags", []))
            changed = False
            cols_tags = st.columns(4)
            for ti, (tname, tcolor) in enumerate(PRESET_TAGS.items()):
                with cols_tags[ti % 4]:
                    is_on = tname in current_tags
                    btn_style = f"background:rgba({'239,68,68' if tcolor=='red' else '251,191,36' if tcolor=='amber' else '52,211,153' if tcolor=='green' else '56,189,248' if tcolor=='blue' else '167,139,250' if tcolor=='purple' else '244,114,182' if tcolor=='pink' else '100,116,139'},.2);border:1px solid rgba({'239,68,68' if tcolor=='red' else '251,191,36' if tcolor=='amber' else '52,211,153' if tcolor=='green' else '56,189,248' if tcolor=='blue' else '167,139,250' if tcolor=='purple' else '244,114,182' if tcolor=='pink' else '100,116,139'},.4);border-radius:8px;padding:6px;text-align:center;font-size:11px;cursor:pointer;"
                    checked = st.checkbox(tname, value=is_on, key=f"tag_{pname}_{tname}")
                    if checked and tname not in current_tags:
                        current_tags.append(tname); changed = True
                    elif not checked and tname in current_tags:
                        current_tags.remove(tname); changed = True

            # Custom tag
            st.markdown("<div style='margin-top:12px;font-size:12px;color:#64748b'>หรือเพิ่ม Label เอง:</div>", unsafe_allow_html=True)
            custom_col1, custom_col2 = st.columns([3, 1])
            with custom_col1:
                custom_tag = st.text_input("", placeholder="เช่น Q3, ลูกค้า VIP, ส่ง 1 มิ.ย.", key=f"custom_tag_{pname}", label_visibility="collapsed")
            with custom_col2:
                if st.button("➕ เพิ่ม", key=f"add_custom_tag_{pname}", use_container_width=True):
                    if custom_tag.strip() and custom_tag.strip() not in current_tags:
                        current_tags.append(custom_tag.strip())
                        vault[pname]["tags"] = current_tags
                        save_vault(vault)
                        st.success(f"เพิ่ม '{custom_tag}' แล้ว!")
                        st.rerun()

            if changed:
                vault[pname]["tags"] = current_tags
                save_vault(vault)

            # Preview
            if current_tags:
                st.markdown("<div style='margin-top:8px;font-size:11px;color:#475569'>Label ที่ติดอยู่:</div>", unsafe_allow_html=True)
                preview_html = "".join(tag_html(t) for t in current_tags)
                rm_cols = st.columns(min(len(current_tags), 4))
                for ti, t in enumerate(current_tags):
                    with rm_cols[ti % 4]:
                        if st.button(f"✕ {t}", key=f"rm_tag_{pname}_{ti}", use_container_width=True):
                            vault[pname]["tags"].remove(t)
                            save_vault(vault)
                            st.rerun()

        # ── TAB 3: FILE ATTACH ──
        with tab3:
            st.markdown("<div style='font-size:12px;color:#64748b;margin-bottom:10px'>แนบไฟล์เข้า Project นี้ (รูป, PDF, Word, Excel, เสียง, วีดีโอ, ไฟล์อื่นๆ)</div>", unsafe_allow_html=True)

            # Upload area
            uploaded = st.file_uploader(
                "เลือกไฟล์ที่ต้องการแนบ",
                accept_multiple_files=True,
                key=f"file_upload_{pname}",
                type=["jpg","jpeg","png","webp","gif","pdf","doc","docx","xls","xlsx",
                      "csv","txt","md","mp3","mp4","mov","zip","json","py"],
                label_visibility="collapsed"
            )

            if uploaded:
                added = 0
                existing_names = [f["name"] for f in vault[pname].get("files", [])]
                for uf in uploaded:
                    if uf.name in existing_names:
                        continue
                    raw    = uf.read()
                    b64    = base64.b64encode(raw).decode()
                    mime   = uf.type or "application/octet-stream"
                    fentry = {
                        "name":     uf.name,
                        "mime":     mime,
                        "size":     uf.size,
                        "data":     b64,
                        "added_at": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "note":     "",
                    }
                    vault[pname]["files"].append(fentry)
                    added += 1
                if added:
                    save_vault(vault)
                    st.success(f"✅ เพิ่มไฟล์ {added} ไฟล์แล้ว!")
                    st.rerun()

            # List files
            current_files = vault[pname].get("files", [])
            if not current_files:
                st.info("ยังไม่มีไฟล์แนบ — อัปโหลดจากช่องด้านบน")
            else:
                st.markdown(f"<div style='font-size:12px;color:#38bdf8;font-family:IBM Plex Mono,monospace;margin-bottom:8px'>📎 {len(current_files)} ไฟล์</div>", unsafe_allow_html=True)
                for fi, fdata in enumerate(current_files):
                    fname  = fdata.get("name", "")
                    fsize  = fdata.get("size", 0)
                    fmime  = fdata.get("mime", "")
                    fadded = fdata.get("added_at", "")
                    fnote  = fdata.get("note", "")
                    ficon  = get_file_icon(fname)
                    fraw   = base64.b64decode(fdata.get("data", "")) if fdata.get("data") else b""

                    fc1, fc2, fc3 = st.columns([5, 2, 1])
                    with fc1:
                        st.markdown(f"""<div class='file-card'>
  <span class='file-icon'>{ficon}</span>
  <div>
    <div class='file-name'>{fname}</div>
    <div class='file-meta'>{format_filesize(fsize)} · {fadded}</div>
    {f"<div style='font-size:11px;color:#64748b;margin-top:2px'>📝 {fnote}</div>" if fnote else ""}
  </div>
</div>""", unsafe_allow_html=True)
                    with fc2:
                        if fraw:
                            # Preview รูปภาพ
                            if fmime.startswith("image/"):
                                st.image(fraw, use_container_width=True)
                            st.download_button(
                                f"⬇️ ดาวน์โหลด",
                                data=fraw,
                                file_name=fname,
                                mime=fmime,
                                use_container_width=True,
                                key=f"dl_file_{pname}_{fi}"
                            )
                    with fc3:
                        if st.button("🗑️", key=f"del_file_{pname}_{fi}", help="ลบไฟล์นี้"):
                            vault[pname]["files"].pop(fi)
                            save_vault(vault)
                            st.rerun()

                    # Note editor
                    new_note = st.text_input(f"บันทึกหมายเหตุ:", value=fnote,
                                              placeholder="เพิ่มหมายเหตุสำหรับไฟล์นี้...",
                                              key=f"note_{pname}_{fi}",
                                              label_visibility="collapsed")
                    if new_note != fnote:
                        vault[pname]["files"][fi]["note"] = new_note
                        save_vault(vault)

                    st.markdown("<hr style='border-color:#1e293b;margin:6px 0'>", unsafe_allow_html=True)

                # ── ล้างทุกไฟล์ ──
                if st.button(f"🗑️ ลบไฟล์ทั้งหมดของ {pname}", key=f"del_all_files_{pname}"):
                    vault[pname]["files"] = []
                    save_vault(vault)
                    st.warning("ลบไฟล์ทั้งหมดแล้ว")
                    st.rerun()

        # ── TAB 4: Knowledge ──
        with tab4:
            if knowledge:
                st.markdown(f"**ขนาด:** {len(knowledge):,} chars")
                st.text_area("Knowledge:", value=knowledge, height=200, key=f"know_{pname}")
                if st.button("🗑️ ลบ Knowledge นี้", key=f"delknow_{pname}"):
                    vault[pname]["knowledge"] = ""
                    save_vault(vault)
                    st.success("ลบแล้ว!")
                    st.rerun()
            else:
                st.info("ยังไม่มี Knowledge — อัปโหลดไฟล์ในหน้าหลักเพื่อบันทึก")

        # ── TAB 5: History ──
        with tab5:
            if not history:
                st.info("ยังไม่มีประวัติ Session")
            else:
                for i, entry in enumerate(reversed(history)):
                    ts      = entry.get("timestamp", "")
                    n_agents= entry.get("agents", 0)
                    brief_s = entry.get("brief", "")[:100]
                    st.markdown(f"""<div style='background:rgba(15,23,42,.8);border:1px solid #1e293b;border-radius:8px;
  padding:10px 14px;margin-bottom:6px'>
  <span style='color:#fbbf24;font-weight:700'>{ts}</span>
  <span style='color:#64748b;font-size:12px;margin-left:8px'>{n_agents} Agents</span>
  <div style='font-size:12px;color:#94a3b8;margin-top:4px'>{brief_s}...</div>
</div>""", unsafe_allow_html=True)
                if st.button(f"🗑️ ล้างประวัติ Session ทั้งหมดของ {pname}", key=f"clrhist_{pname}"):
                    vault[pname]["history"] = []
                    save_vault(vault)
                    st.success("ล้างแล้ว!")
                    st.rerun()
