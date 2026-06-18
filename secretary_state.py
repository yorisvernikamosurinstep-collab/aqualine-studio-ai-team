# -*- coding: utf-8 -*-
"""
secretary_state.py — สถานะถาวรของ "เลขานุการ AI": ประวัติแชท 1:1 (เลขา↔ผู้บริหาร) + กระดานงานแต่ละแผนก
======================================================================================
นี่คือ "ศูนย์กลาง" เดียวที่รวมคำถามก่อนเริ่มงานจากทุกแผนกมาไว้ที่เดียว (ตามที่ผู้ใช้กำหนดไว้)
ผู้บริหารคุยกับเลขาคนเดียวในแชทนี้ ไม่ต้องไล่ตอบคำถามแยกทีละแผนก

บันทึกถาวรลงไฟล์ secretary_state.json (อยู่ข้างๆไฟล์นี้) ใช้ร่วมกันทุกหน้าในแอป
"""

import json
import os
from datetime import datetime

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "secretary_state.json")

# โครงสร้าง task แต่ละตัวที่เก็บใน state["tasks"]:
# {
#   "id": 1,                              # auto-increment
#   "dept_id": "D2",                      # อ้างถึง DEPARTMENTS ใน agent_default_personas.py
#   "title": "...", "detail": "...",
#   "deadline": "...",
#   "topic": "หัวข้อการประชุมที่งานนี้มาจาก",
#   "status": "assigned" | "in_progress" | "delivered",
#   "clarifying_questions": ["...", ...],  # คำถามที่แผนกนี้ต้องถามผู้บริหารก่อนเริ่มงาน
#   "answers": {"คำถาม": "คำตอบ"},         # คำตอบที่ผู้บริหารตอบแล้ว (ผ่านแชทเลขา)
#   "created_at": "iso datetime",
# }


def _empty_state() -> dict:
    return {"chat": [], "tasks": [], "_next_id": 1}


def load_state() -> dict:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return _empty_state()
            data.setdefault("chat", [])
            data.setdefault("tasks", [])
            data.setdefault("_next_id", max([t.get("id", 0) for t in data["tasks"]], default=0) + 1)
            return data
        except Exception:
            return _empty_state()
    return _empty_state()


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def add_chat_message(role: str, text: str) -> None:
    """role: 'user' (ผู้บริหาร) | 'secretary' (เลขา AI)"""
    state = load_state()
    state["chat"].append({
        "role": role,
        "text": text,
        "ts": datetime.now().isoformat(timespec="seconds"),
    })
    save_state(state)


def add_tasks(tasks: list, topic: str = "") -> list:
    """tasks: list ของ dict จาก meeting_engine.secretary_breakdown()['tasks']
    คืน list ของ task ที่สร้างจริง (มี id แล้ว)"""
    state = load_state()
    next_id = state.get("_next_id", 1)
    now = datetime.now().isoformat(timespec="seconds")
    created = []
    for t in tasks:
        new_t = {
            "id": next_id,
            "dept_id": t.get("dept_id", "D1"),
            "title": t.get("title", ""),
            "detail": t.get("detail", ""),
            "deadline": t.get("deadline", ""),
            "topic": topic,
            "status": "assigned",
            "clarifying_questions": list(t.get("clarifying_questions", []) or []),
            "answers": {},
            "created_at": now,
        }
        state["tasks"].append(new_t)
        created.append(new_t)
        next_id += 1
    state["_next_id"] = next_id
    save_state(state)
    return created


def update_task_status(task_id: int, status: str) -> None:
    state = load_state()
    for t in state["tasks"]:
        if t["id"] == task_id:
            t["status"] = status
            break
    save_state(state)


def answer_clarifying_question(task_id: int, question: str, answer: str) -> None:
    state = load_state()
    for t in state["tasks"]:
        if t["id"] == task_id:
            t.setdefault("answers", {})[question] = answer
            break
    save_state(state)


def delete_task(task_id: int) -> None:
    state = load_state()
    state["tasks"] = [t for t in state["tasks"] if t["id"] != task_id]
    save_state(state)


def get_tasks_by_department(did: str) -> list:
    return [t for t in load_state()["tasks"] if t.get("dept_id") == did]


def get_all_pending_questions() -> list:
    """คืน list ของ (task, question) ที่ยังไม่มีคำตอบ — ใช้แจ้งในแชทเลขาว่ามีอะไรรอผู้บริหารตอบบ้าง"""
    out = []
    for t in load_state()["tasks"]:
        for q in t.get("clarifying_questions", []):
            if q not in t.get("answers", {}):
                out.append((t, q))
    return out
