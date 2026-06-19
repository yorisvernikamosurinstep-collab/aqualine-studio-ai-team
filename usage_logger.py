# -*- coding: utf-8 -*-
"""
usage_logger.py — สะพานบันทึกค่าใช้จ่าย AI จริงเข้า budget_data.json
======================================================================
หน้า "Budget & Cost Manager" (pages/11_Budget_Cost_Manager.py) เดิมรับค่าใช้จ่ายจาก
การกรอกมือ (manual entry) เท่านั้น โมดูลนี้เพิ่มทางที่สอง: บันทึกอัตโนมัติทุกครั้งที่มี
การเรียก Gemini จริงจาก meeting_engine.py (หน้า "งานบริษัทอาควาไลน์") และ ai_team.py (หน้าแรก)

ใช้ schema ของ "expense" แบบเดียวกับที่หน้า Budget อ่านอยู่แล้วทุกตัวอักษร
(category/amount/desc/session/date) เพื่อให้สองทางผสมรวมกันในตารางเดียวได้ทันที
โดยไม่ต้องแก้ไขหน้า Budget & Cost Manager เลย

ไม่ import streamlit — เรียกได้ปลอดภัยจากทั้ง meeting_engine.py (worker thread) และ ai_team.py
"""

import json
import os
from datetime import datetime

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
BUDGET_DATA_FILE = os.path.join(_THIS_DIR, "budget_data.json")

_DEFAULT = {"expenses": [], "budget_limit": 5000.0, "alert_pct": 80}


def _load() -> dict:
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
    return dict(_DEFAULT)


def _save(data: dict) -> None:
    try:
        with open(BUDGET_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def log_usage(amount_thb: float, desc: str = "", session: str = "", category: str = "Gemini Flash") -> None:
    """บันทึกค่าใช้จ่ายจริง 1 รายการ — เรียกใช้หลังเรียก Gemini จริงแต่ละครั้ง/แต่ละรอบ"""
    try:
        amt = float(amount_thb)
    except (TypeError, ValueError):
        return
    if amt <= 0:
        return
    data = _load()
    data["expenses"].append({
        "category": category,
        "amount": round(amt, 4),
        "desc": desc,
        "session": session,
        "date": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "auto": True,  # ทำเครื่องหมายว่าระบบบันทึกอัตโนมัติ (แยกจากที่กรอกมือ)
    })
    _save(data)


def log_meeting_batch(entries: list, session: str = "", category: str = "Gemini Flash") -> None:
    """บันทึกหลายรายการพร้อมกัน (เช่น ผลลัพธ์ 1 รอบประชุมที่มีหลาย agent ตอบพร้อมกัน)
    entries: [{"amount_thb": float, "desc": str}, ...] — ข้าม entry ที่ amount_thb <= 0"""
    if not entries:
        return
    data = _load()
    now = datetime.now().strftime("%d/%m/%Y %H:%M")
    changed = False
    for e in entries:
        try:
            amt = float(e.get("amount_thb", 0))
        except (TypeError, ValueError):
            continue
        if amt <= 0:
            continue
        data["expenses"].append({
            "category": category,
            "amount": round(amt, 4),
            "desc": e.get("desc", ""),
            "session": session,
            "date": now,
            "auto": True,
        })
        changed = True
    if changed:
        _save(data)
