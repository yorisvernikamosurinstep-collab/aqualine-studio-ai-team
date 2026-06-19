# -*- coding: utf-8 -*-
"""
eval_runner.py — ชุดทดสอบ regression สำหรับ Smart Filter (Item 1) และ SOP/Persona (Item 2)
================================================================================
ใช้ตรวจสอบว่าการแก้ไข agent_default_personas.py (AGENT_META, AGENT_DEFAULT_PERSONAS, DEPARTMENT_SOP)
หรือ meeting_engine.py (select_relevant_agents, build_agent_prompt) ไม่ทำให้พฤติกรรมเดิมพัง
ก่อน commit การเปลี่ยนแปลง persona/SOP ใด ๆ ควรรันสคริปต์นี้แล้วอ่านผลด้วยตา (manual review)
— ผลลัพธ์เป็นแค่ "สัญญาณเตือน" ไม่ใช่คำตัดสินสุดท้าย เพราะการกรองด้วยคำคีย์เวิร์ดมีขอบเขตจำกัด

วิธีรัน:
    python eval_runner.py

ไม่เรียก Gemini API จริง (ไม่ต้องมี API key, ไม่มีค่าใช้จ่าย) — ทดสอบเฉพาะตรรกะ
การกรอง agent (deterministic) และการประกอบ prompt (string building) เท่านั้น
ไม่ import streamlit — รันได้ตรง ๆ นอก Streamlit app
"""

import sys

from agent_default_personas import (
    AGENT_IDS,
    AGENT_META,
    DEPARTMENTS,
    get_department_id,
    get_department_ids,
    get_department_sop,
)
from meeting_engine import (
    select_relevant_agents,
    build_agent_prompt,
    estimate_tokens_th,
)

PASS = "✅ PASS"
FAIL = "❌ FAIL"
INFO = "ℹ️  INFO"

_results = []  # [(label, ok_or_none, detail), ...]  ok=None แปลว่าแค่โชว์ผลให้ดู ไม่ assert


def _record(label, ok, detail=""):
    _results.append((label, ok, detail))
    tag = PASS if ok is True else (FAIL if ok is False else INFO)
    print(f"{tag} | {label}")
    if detail:
        print(f"        {detail}")


# ════════════════════════════════════════════════════════════════════
# 1) EVAL SET — หัวข้อประชุมตัวอย่าง + แผนกที่ "ควรจะ" ถูกกรองเข้ามา
#    (เลือกคำที่ตรงกับ p / dept name / dept desc ของแต่ละแผนกใน agent_default_personas.py
#     ตรงตามตรรกะจริงของ select_relevant_agents() — ดู meeting_engine.py บรรทัด ~181-200)
# ════════════════════════════════════════════════════════════════════
RELEVANCE_CASES = [
    {
        "topic": "แผนโปรโมชันหน้าฝนปีนี้ ซื้อโฆษณา Facebook พร้อมตั้งราคา Bundle",
        "expect_depts": ["D4"],
        "note": "คำว่า โฆษณา/ราคา/Bundle ควรดึงฝ่ายมีเดียและงบโฆษณา (D4) เข้ามา",
    },
    {
        "topic": "ไอเดียแคมเปญ TikTok ใหม่ พร้อมสตอรี่บอร์ดและกราฟิกสินค้า",
        "expect_depts": ["D2"],
        "note": "คำว่า TikTok/สตอรี่บอร์ด/กราฟิก ควรดึงฝ่ายครีเอทีฟ (D2) เข้ามา",
    },
    {
        "topic": "ตรวจสอบสเปกสินค้าและข้อกฎหมายลิขสิทธิ์ก่อนเปิดตัว",
        "expect_depts": ["D6"],
        "note": "คำว่า สเปก/กฎหมาย/ลิขสิทธิ์ ควรดึงฝ่ายกำกับมาตรฐานและเทคนิค (D6) เข้ามา",
    },
    {
        "topic": "วิจัยคู่แข่งและราคาตลาดล่าสุดแบบ Real-time",
        "expect_depts": ["D5"],
        "note": "คำว่า วิจัย/คู่แข่ง/Real-time ควรดึงฝ่ายข่าวกรองตลาดและคู่แข่ง (D5) เข้ามา",
    },
    {
        "topic": "ประชุมทีมประจำสัปดาห์",
        "expect_depts": None,  # หัวข้อกว้าง/กำกวม ไม่ฟันธงว่าควรได้แผนกไหน — ดูผลด้วยตาเท่านั้น
        "note": "หัวข้อกว้าง/กำกวม ใช้ดู fallback behavior (ไม่ตั้งใจให้ assert pass/fail)",
    },
]


def run_relevance_evals():
    print("\n" + "=" * 70)
    print("🎯 EVAL 1/2 — select_relevant_agents() (Smart Filter, Item 1)")
    print("=" * 70)
    full_count = len(AGENT_IDS)
    for case in RELEVANCE_CASES:
        topic = case["topic"]
        filtered = select_relevant_agents(AGENT_IDS, topic, min_keep=3)
        filtered_depts = sorted({get_department_id(a) for a in filtered if get_department_id(a)})
        reduction_pct = round(100 * (1 - len(filtered) / full_count), 1)
        detail = (
            f'หัวข้อ: "{topic}"\n'
            f"        เหลือ {len(filtered)}/{full_count} agent ({reduction_pct}% ลดลง) — แผนกที่ติด: {filtered_depts}\n"
            f"        agent: {filtered}"
        )
        if case["expect_depts"] is None:
            _record(f"[กำกวม] {case['note']}", None, detail)
        else:
            ok = all(d in filtered_depts for d in case["expect_depts"])
            _record(case["note"], ok, detail)

    # Sanity: หัวข้อว่าง ต้องคืน agent ครบทุกตัวเสมอ (ไม่กรองอะไรเลยตอนไม่มีหัวข้อ)
    empty_result = select_relevant_agents(AGENT_IDS, "", min_keep=3)
    _record(
        "หัวข้อว่าง ต้องคืน agent ครบทุกตัว (ไม่กรองอะไรเลย)",
        len(empty_result) == full_count,
        f"ได้ {len(empty_result)}/{full_count} ตัว",
    )

    # Sanity: หัวข้อที่ไม่ match อะไรเลย ต้อง fallback กลับเป็น list เดิมทั้งหมด (กันกรองพลาดจนทีมขาดมุมมอง)
    tiny_topic = "zzzqqqxxxnonexistentkeyword"
    fallback_result = select_relevant_agents(AGENT_IDS, tiny_topic, min_keep=3)
    _record(
        "หัวข้อที่ไม่ match อะไรเลย ต้อง fallback คืน agent ครบทุกตัว",
        len(fallback_result) == full_count,
        f"ได้ {len(fallback_result)}/{full_count} ตัว",
    )


# ════════════════════════════════════════════════════════════════════
# 2) EVAL — build_agent_prompt() ต้องฉีด role_desc + SOP (Item 2) ของแผนกต้นสังกัดเสมอ
#    เลือก agent ตัวแทน 1 ตัวต่อแผนก (ตัวแรกในรายชื่อของแต่ละแผนก ตาม DEPARTMENTS)
# ════════════════════════════════════════════════════════════════════
def run_prompt_evals():
    print("\n" + "=" * 70)
    print("📝 EVAL 2/2 — build_agent_prompt() (SOP injection, Item 2)")
    print("=" * 70)
    sample_topic = "ทดสอบระบบ eval_runner.py"
    for did in get_department_ids():
        dept = DEPARTMENTS[did]
        agents_in_dept = dept.get("agents", [])
        if not agents_in_dept:
            _record(f"แผนก {did} ({dept['name']}) ไม่มี agent ให้ทดสอบ", False)
            continue
        aid = agents_in_dept[0]
        sop = get_department_sop(did)
        try:
            prompt = build_agent_prompt(aid, sample_topic, "", "", round_no=1)
        except Exception as e:
            _record(f"build_agent_prompt() พังตอนสร้าง prompt ของ {aid} ({did})", False, f"Exception: {e}")
            continue

        checks = {
            "มีชื่อ agent อยู่ใน prompt": (AGENT_META.get(aid, {}).get("name", "") in prompt),
            "มีหัวข้อประชุมอยู่ใน prompt": (sample_topic in prompt),
            "มี SOP ของแผนกอยู่ใน prompt (ถ้าแผนกนี้นิยาม SOP ไว้)": (sop in prompt if sop else True),
        }
        all_ok = all(checks.values())
        tok_est = estimate_tokens_th(prompt)
        detail_lines = [f"{'✓' if v else '✗'} {k}" for k, v in checks.items()]
        detail = (
            f"agent ตัวแทน: {aid} ({AGENT_META.get(aid, {}).get('name','')}) แผนก {did}\n        "
            + "\n        ".join(detail_lines)
            + f"\n        ความยาว prompt: {len(prompt)} chars (~{tok_est} tokens ประมาณ)"
        )
        _record(f"แผนก {did} ({dept['name']}) — prompt ครบโครงสร้าง", all_ok, detail)


def print_summary():
    print("\n" + "=" * 70)
    print("📊 สรุปผล")
    print("=" * 70)
    n_pass = sum(1 for _, ok, _ in _results if ok is True)
    n_fail = sum(1 for _, ok, _ in _results if ok is False)
    n_info = sum(1 for _, ok, _ in _results if ok is None)
    print(f"ผ่าน: {n_pass}  |  ไม่ผ่าน: {n_fail}  |  ข้อมูลให้ดูเฉย ๆ (ไม่ assert): {n_info}")
    if n_fail:
        print("\n⚠️  มีรายการไม่ผ่าน — ตรวจสอบการแก้ไข agent_default_personas.py / meeting_engine.py ล่าสุด")
    else:
        print("\n✅ ทุกรายการที่ assert ผ่านหมด (รายการ INFO ให้อ่านด้วยตาเพิ่มเติมข้างบน)")
    return n_fail


if __name__ == "__main__":
    run_relevance_evals()
    run_prompt_evals()
    _n_fail = print_summary()
    sys.exit(1 if _n_fail else 0)
