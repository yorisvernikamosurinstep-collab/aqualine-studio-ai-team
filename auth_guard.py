"""
auth_guard.py — กันคนเข้าหน้าใดหน้าหนึ่งของแอปตรง ๆ ผ่าน URL โดยไม่ผ่านด่านล็อกอินที่หน้าแรก
(รูบิค 3 คลิก + รหัสผ่าน ใน ai_team.py) เพราะ Streamlit multipage แต่ละหน้ารันสคริปต์แยกกัน
ถ้าผู้ใช้เปิดลิงก์ตรงของหน้าย่อย (เช่น .../Live_Chat) โดยไม่เคยผ่านหน้าแรกในเซสชันนี้มาก่อน
จะไม่มีค่า st.session_state.authenticated เลย ฟังก์ชันนี้จึงเช็กแล้วเด้งกลับไปหน้าแรกให้

วิธีใช้: import แล้วเรียก require_auth() ทันทีหลัง st.set_page_config() ของทุกหน้าใน pages/
"""

import streamlit as st


def require_auth():
    """ถ้ายัง authenticated=False (ยังไม่ผ่านด่านรูบิค+รหัสผ่านที่หน้าแรก) ให้หยุดแสดงหน้านี้
    และเสนอปุ่มกลับไปเข้าสู่ระบบที่หน้าแรกแทน — ไม่กระทบ session ที่ authenticated แล้ว"""
    if st.session_state.get("authenticated"):
        return

    st.markdown(
        """
        <style>
          #MainMenu, header, footer {visibility: hidden;}
          section[data-testid="stSidebar"] {display: none;}
          [data-testid="stAppViewContainer"] {background: #000 !important;}
        </style>
        <div style='text-align:center;margin-top:18vh;'>
          <p style='color:#fff;font-size:22px;letter-spacing:1px;'>🔐 กรุณาเข้าสู่ระบบก่อนใช้งานหน้านี้</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    _c1, _c2, _c3 = st.columns([1, 1, 1])
    with _c2:
        if st.button("⬅️ ไปหน้าแรกเพื่อเข้าสู่ระบบ", use_container_width=True):
            st.switch_page("ai_team.py")
    st.stop()
