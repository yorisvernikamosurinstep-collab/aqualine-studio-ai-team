@echo off
cd /d "C:\Users\User\Desktop\Aqualine_A"

:: ==========================================
:: 1. สำหรับโปรไฟล์ Aqualine Graphic (Profile 5)
:: ==========================================
:: --- หน้าจัดการโฆษณา (Link เดิมของคุณ) ---
start chrome.exe --profile-directory="Profile 5" "https://adsmanager.facebook.com/adsmanager/manage/campaigns?act=629802197497218&..."

:: --- เพิ่มหน้าเว็บอื่นใน Profile 5 (ก๊อปปี้บรรทัดล่างนี้ไปใช้ได้เลย) ---
start chrome.exe --profile-directory="Profile 5" "https://manage.wix.com/dashboard/86803e10-71a5-405c-9b1a-deefcbb22ad4/home"


:: ==========================================
:: 2. สำหรับโปรไฟล์หลัก (Default)
:: ==========================================
:: --- สั่งรันระบบ AI เบื้องหลัง ---
start /b python -m streamlit run ai_team.py --server.headless true

:: --- รอระบบเตรียมตัว 5 วินาที ---
timeout /t 5 /nobreak > nul

:: --- เปิดหน้าจอ AI Studio (localhost) ---
start chrome.exe --profile-directory="Default" "http://localhost:8501"

:: --- เพิ่มหน้าเว็บอื่นใน Profile Default (เช่น Gmail หรือ Google) ---
start chrome.exe --profile-directory="Default" "https://nikamo638.pythonanywhere.com/"
start chrome.exe --profile-directory="Default" "https://www.aqualine.co.th"
start chrome.exe --profile-directory="Default" "https://gemini.google.com/u/1/app?hl=th&pageId=none"

start "" "C:\Program Files\Python314\pythonw.exe" "Z:\ek_listener.py"

exit