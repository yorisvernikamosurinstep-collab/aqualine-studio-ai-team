# -*- coding: utf-8 -*-
"""
meeting_engine.py — เครื่องยนต์ "ห้องประชุมแผนก" แบบ parallel จริง สำหรับหน้า งานบริษัทอาควาไลน์
======================================================================================
จงใจทำให้เป็นโมดูล "อิสระ" ไม่ import จาก ai_team.py โดยตรง เพราะ ai_team.py มีโค้ดตรวจรหัสผ่าน
(Rubik's-cube lock gate) อยู่บนสุดของไฟล์ที่จะรันทันทีตอน import (เรียก st.stop() ถ้ายังไม่ login)
— ดังนั้นไฟล์นี้ reimplement Gemini helper เอง (รูปแบบเดียวกับที่ ai_team.py ใช้) แบบสแตนด์อโลน

ความรับผิดชอบของไฟล์นี้:
  1) เรียก Gemini API แบบ non-streaming (ปลอดภัยสำหรับใช้ใน ThreadPoolExecutor worker thread)
  2) สร้าง prompt ให้ agent แต่ละตัวพูดในที่ประชุมแบบมีตัวตน + ฐานความรู้สินค้า + กติกา "ห้ามพูดซ้ำ/เห็นด้วยเฉยๆ"
  3) รันหลาย agent "พร้อมกันจริง" ด้วย ThreadPoolExecutor แล้วเรียก callback กลับ main thread ทันทีที่แต่ละตัวเสร็จ
     (ใช้ wiring Knowledge Graph แบบ real-time ได้ เพราะ as_completed() loop ทำงานบน main thread เสมอ)
  4) สรุปผลประชุมเป็น Action Plan / รับข้อโต้แย้งแล้วปรับมติใหม่ (rebuttal/lock-in)
  5) ให้ "เลขานุการ AI" แตกมติที่ล็อกแล้วเป็นงานต่อแผนก พร้อมคำถามที่ต้องถามผู้บริหารก่อนเริ่มงาน
  6) ให้เลขานุการตอบแชท 1:1 กับผู้บริหาร (ศูนย์กลางคำถามจากทุกแผนก)
"""

import concurrent.futures
import json
import re
import time

import requests

from agent_default_personas import (
    AGENT_META,
    DEPARTMENTS,
    get_agent_role_desc,
    get_department_id,
    get_department_info,
    get_department_sop,
)

# ════════════════════════════════════════════════════════════════════
# 🤖 GEMINI HELPERS — เป็นอิสระจาก ai_team.py โดยสิ้นเชิง (ดูหมายเหตุด้านบน)
# ════════════════════════════════════════════════════════════════════
_MODEL_PRIORITY = [
    "models/gemini-2.5-flash-preview-05-20",
    "models/gemini-2.5-flash-preview-04-17",
    "models/gemini-2.5-flash",
    "models/gemini-2.5-pro-preview-05-06",
    "models/gemini-2.5-pro",
    "models/gemini-2.0-flash",
    "models/gemini-2.0-flash-lite",
    "models/gemini-2.0-flash-001",
    "models/gemini-1.5-flash-latest",
    "models/gemini-1.5-pro-latest",
]

_model_cache: dict = {}


def get_best_model(api_key: str) -> str:
    """หาโมเดล Gemini ที่ดีที่สุดที่ใช้ได้กับ key นี้ (cache ไว้ในหน่วยความจำกันยิง API ซ้ำ)"""
    if api_key in _model_cache:
        return _model_cache[api_key]
    try:
        r = requests.get(
            f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}",
            timeout=10,
        )
        if r.status_code == 200:
            avail = [
                m["name"] for m in r.json().get("models", [])
                if "generateContent" in m.get("supportedGenerationMethods", [])
            ]
            for p in _MODEL_PRIORITY:
                if p in avail:
                    _model_cache[api_key] = p
                    return p
            if avail:
                _model_cache[api_key] = avail[0]
                return avail[0]
    except Exception:
        pass
    return "models/gemini-1.5-flash"


def call_gemini(prompt: str, model_name: str, api_key: str, use_search: bool = False,
                 max_output_tokens: int | None = None, timeout: int = 120, max_retries: int = 3) -> str:
    """เรียก Gemini แบบ non-streaming ครั้งเดียวจบ — ปลอดภัยสำหรับเรียกจาก worker thread ของ
    ThreadPoolExecutor (ไม่มีการเรียก st.* ใดๆในนี้)"""
    if max_output_tokens is None:
        n = len(prompt)
        if n < 3000:
            max_output_tokens = 8192
        elif n < 8000:
            max_output_tokens = 16384
        else:
            max_output_tokens = 32768

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.75, "maxOutputTokens": max_output_tokens},
    }
    if use_search:
        payload["tools"] = [{"google_search": {}}]

    url = f"https://generativelanguage.googleapis.com/v1beta/{model_name}:generateContent?key={api_key}"
    for attempt in range(max_retries):
        try:
            resp = requests.post(url, json=payload, timeout=timeout)
            if resp.status_code == 200:
                try:
                    return resp.json()["candidates"][0]["content"]["parts"][0].get("text", "").strip()
                except (KeyError, IndexError):
                    return "⚠️ ไม่พบคำตอบจากโมเดล (อาจถูก safety filter บล็อก)"
            elif resp.status_code == 429:
                time.sleep(2 ** (attempt + 1))
                continue
            else:
                return f"⚠️ API Error {resp.status_code}: {resp.text[:200]}"
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            return "⚠️ API Timeout — กรุณาลองใหม่"
        except requests.exceptions.ConnectionError:
            return "⚠️ เชื่อมต่อ API ไม่ได้ — ตรวจสอบ internet"
        except Exception as e:
            return f"⚠️ Unexpected error: {str(e)[:150]}"
    return "⚠️ เรียก API ไม่สำเร็จหลัง retry หลายครั้ง"


def smart_chunk_knowledge(text: str, max_chars: int = 12000) -> str:
    """ตัดความรู้แบบรักษาขอบเขตพารากราฟ (ไม่ตัดดิบกลางคำ/กลางประโยค) ถ้ายาวเกิน max_chars"""
    if not text:
        return ""
    if len(text) <= max_chars:
        return text
    paras = text.split("\n\n")
    out, total = [], 0
    for p in paras:
        if total + len(p) > max_chars:
            break
        out.append(p)
        total += len(p) + 2
    chunked = "\n\n".join(out)
    return chunked if chunked else text[:max_chars]


def lang_suffix(lang: str = "TH") -> str:
    if lang == "EN":
        return "\n\n(Please respond in English.)"
    return "\n\n(ตอบเป็นภาษาไทยเท่านั้น)"


# ════════════════════════════════════════════════════════════════════
# 💰 COST/TOKEN ESTIMATOR — สูตรเดียวกับ ai_team.py (estimate_tokens/update_token_counter)
# เพื่อให้ตัวเลขจากสองหน้าเทียบกันได้ ใช้คำนวณต้นทุนจริงของ "งานบริษัทอาควาไลน์" ที่เดิมไม่มีการบันทึกเลย
# ════════════════════════════════════════════════════════════════════
_GEMINI_INPUT_USD_PER_M = 0.075
_GEMINI_OUTPUT_USD_PER_M = 0.30


def estimate_tokens_th(text: str) -> int:
    """ประมาณ token count สำหรับ mixed Thai/EN text
    - ภาษาอังกฤษ: ~4 chars/token
    - ภาษาไทย: ~2 chars/token (Thai unicode = 1 char แต่มักเป็น 1-2 tokens)"""
    if not text:
        return 0
    thai_chars = sum(1 for c in text if "฀" <= c <= "๿")
    other_chars = len(text) - thai_chars
    return max(1, (thai_chars // 2) + (other_chars // 4))


def estimate_gemini_cost_thb(prompt_text: str, response_text: str, usd_to_thb: float = 35.0) -> tuple:
    """ประมาณต้นทุนจริง (Gemini 2.5 Flash) จาก token ที่ใช้จริงของการเรียกครั้งนี้
    คืน (tokens_est, cost_usd, cost_thb)"""
    in_tok = estimate_tokens_th(prompt_text)
    out_tok = estimate_tokens_th(response_text)
    cost_usd = (in_tok / 1_000_000 * _GEMINI_INPUT_USD_PER_M) + (out_tok / 1_000_000 * _GEMINI_OUTPUT_USD_PER_M)
    return in_tok + out_tok, cost_usd, cost_usd * usd_to_thb


# ════════════════════════════════════════════════════════════════════
# 🎯 RELEVANCE FILTER — กรอง agent ที่เกี่ยวข้องกับหัวข้อก่อนเปิดดีเบตเต็มวง (progressive disclosure)
# เทียบคำในหัวข้อกับคำอธิบายสั้น ('p')/ชื่อแผนกของแต่ละ agent แบบเร็ว ไม่ต้องยิง API เพิ่ม
# ════════════════════════════════════════════════════════════════════
def select_relevant_agents(agent_ids: list, topic: str, min_keep: int = 3) -> list:
    """กรอง agent ที่ "น่าจะเกี่ยวข้อง" กับหัวข้อนี้จาก agent_ids ที่ผู้ใช้เลือกไว้ทั้งหมด
    ถ้าหัวข้อว่าง หรือกรองแล้วเหลือน้อยกว่า min_keep ตัว จะคืน agent_ids เดิมทั้งหมด
    (กันกรองพลาดจนทีมขาดมุมมอง — ฟิลเตอร์นี้เป็น opt-in ที่ผู้ใช้เลือกเปิดเองเท่านั้น)"""
    if not topic or not topic.strip():
        return list(agent_ids)
    topic_lower = topic.lower()
    topic_words = set(re.findall(r"[a-zA-Zก-๙]{2,}", topic_lower))
    if not topic_words:
        return list(agent_ids)
    relevant = []
    for aid in agent_ids:
        meta = AGENT_META.get(aid, {})
        dept = get_department_info(aid)
        haystack = f"{meta.get('p','')} {dept.get('name','')} {dept.get('desc','')}".lower()
        if any(word in haystack for word in topic_words):
            relevant.append(aid)
    if len(relevant) >= min_keep:
        return relevant
    return list(agent_ids)


# ════════════════════════════════════════════════════════════════════
# 🗣️ MEETING PROMPT — มี "ตัวตน" ของแต่ละ agent + ฐานความรู้ + กติกาเถียงกันจริง (anti-echo)
# ════════════════════════════════════════════════════════════════════
def build_agent_prompt(aid: str, topic: str, knowledge_text: str, meeting_ctx: str, round_no: int,
                        custom_personas: dict | None = None, lang: str = "TH") -> str:
    meta = AGENT_META.get(aid, {})
    name = meta.get("name", aid)
    icon = meta.get("icon", "🤖")
    dept = get_department_info(aid)
    role_desc = get_agent_role_desc(aid, custom_personas, meta.get("p", ""))
    sop = get_department_sop(get_department_id(aid))
    kb = smart_chunk_knowledge(knowledge_text, 12000) if knowledge_text else ""

    parts = [
        f"คุณคือ {icon} {name} ({aid}) สังกัด{dept.get('icon','')} {dept.get('name','แผนกทั่วไป')} ของบริษัท AQUALINE",
        role_desc,
    ]
    if sop:
        parts.append(sop)
    if kb:
        parts.append(f"--- ความรู้สินค้า/บริษัท AQUALINE (ใช้อ้างอิงเสมอ ห้ามมั่วหรือแต่งข้อมูลที่ไม่มีในนี้) ---\n{kb}")
    parts.append(f"--- หัวข้อการประชุมวันนี้ ---\n{topic}")

    if meeting_ctx:
        parts.append(
            "--- บทสนทนาที่เกิดขึ้นแล้วในห้องประชุม (รอบนี้/รอบก่อนหน้า) ---\n"
            f"{smart_chunk_knowledge(meeting_ctx, 9000)}\n\n"
            "⚠️ ข้อกำหนดสำคัญของการประชุมนี้: ห้ามพูดซ้ำหรือเห็นด้วยเฉยๆกับคนที่พูดไปแล้ว "
            "ให้วิเคราะห์จากมุมความเชี่ยวชาญของตัวเองเท่านั้น ถ้าเห็นต่างจากที่มีคนพูดไปแล้วให้ \"แย้งตรงๆ\" "
            "พร้อมเหตุผลที่ชัดเจนว่าทำไมไม่เห็นด้วย ถ้าเห็นด้วยบางส่วนให้ต่อยอด/เพิ่มมุมที่คนอื่นยังไม่พูดถึง "
            "ห้ามตอบแบบกลางๆที่ไม่มีจุดยืน"
        )
    else:
        parts.append(
            "นี่คือความเห็นแรกของคุณในที่ประชุมรอบนี้ — เสนอมุมมองจากความเชี่ยวชาญของคุณอย่างตรงไปตรงมา ชัดเจน มีจุดยืน"
        )

    parts.append(f"(นี่คือรอบที่ {round_no} ของการประชุม)")
    parts.append("ตอบในขอบเขตความเชี่ยวชาญของคุณเท่านั้น กระชับ ตรงประเด็น ไม่เกินประมาณ 200-300 คำ")
    return "\n\n".join(parts) + lang_suffix(lang)


def get_dept_for_result(aid: str) -> str:
    return get_department_id(aid)


def run_meeting_round(agent_ids: list, topic: str, knowledge_text: str, meeting_ctx: str, round_no: int,
                       api_key: str, model_name: str, custom_personas: dict | None = None, lang: str = "TH",
                       max_workers: int = 5, on_agent_done=None) -> list:
    """รันทุก agent ใน agent_ids แบบ "parallel จริง" ผ่าน ThreadPoolExecutor

    on_agent_done(aid, name, icon, dept_id, text, remaining_ids, round_no) ถ้าระบุไว้ จะถูกเรียก "ใน main thread"
    ทันทีที่ agent ตัวนั้นตอบเสร็จ (ปลอดภัยสำหรับเรียก Streamlit เพราะ as_completed() for-loop รันบน main thread
    เสมอ แม้ว่า HTTP call จริงจะวิ่งอยู่ใน worker thread ก็ตาม) — ใช้ wiring Knowledge Graph แบบ real-time ได้

    คืน list ของ dict ตามลำดับที่ "เสร็จก่อน-หลังจริง":
      [{"aid","name","icon","dept_id","round","text","tokens_est","cost_thb"}, ...]
    (tokens_est/cost_thb เป็นค่าประมาณต้นทุนจริงของการเรียก Gemini ครั้งนี้ — ดู estimate_gemini_cost_thb)
    """
    results = []
    remaining = set(agent_ids)

    def _run_one(aid):
        meta = AGENT_META.get(aid, {})
        prompt = build_agent_prompt(aid, topic, knowledge_text, meeting_ctx, round_no, custom_personas, lang)
        text = call_gemini(prompt, model_name, api_key)
        tokens_est, _cost_usd, cost_thb = estimate_gemini_cost_thb(prompt, text)
        return aid, meta.get("name", aid), meta.get("icon", "🤖"), get_dept_for_result(aid), text, tokens_est, cost_thb

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_run_one, aid): aid for aid in agent_ids}
        for future in concurrent.futures.as_completed(futures):
            aid, name, icon, dept_id, text, tokens_est, cost_thb = future.result()
            remaining.discard(aid)
            entry = {
                "aid": aid, "name": name, "icon": icon, "dept_id": dept_id, "round": round_no, "text": text,
                "tokens_est": tokens_est, "cost_thb": cost_thb,
            }
            results.append(entry)
            if on_agent_done:
                on_agent_done(aid, name, icon, dept_id, text, list(remaining), round_no)
    return results


def format_meeting_log(results: list) -> str:
    """results: list ของ entry จาก run_meeting_round (หลายรอบรวมกันได้) -> string เดียว
    สำหรับใช้เป็น meeting_ctx รอบถัดไป หรือส่งเข้า summarize_meeting/secretary_breakdown"""
    lines = []
    for r in results:
        dept = DEPARTMENTS.get(r.get("dept_id", ""), {})
        lines.append(
            f"[รอบ {r.get('round','?')} | {dept.get('icon','')} {dept.get('name','')}] "
            f"{r['icon']} {r['name']} ({r['aid']}): {r['text']}"
        )
    return "\n\n".join(lines)


# ════════════════════════════════════════════════════════════════════
# 📊 SUMMARIZE / REBUTTAL — ประธานที่ประชุม AI สรุปมติ + รับข้อโต้แย้งแล้วปรับใหม่
# ════════════════════════════════════════════════════════════════════
def summarize_meeting(meeting_log: str, topic: str, api_key: str, model_name: str, lang: str = "TH") -> str:
    chunked = smart_chunk_knowledge(meeting_log, 14000)
    prompt = f"""คุณคือประธานที่ประชุม (Chairman) ของทีม AI AQUALINE สรุปผลการประชุมเรื่อง "{topic}" ด้านล่างนี้ให้เป็น Action Plan ที่ชัดเจน อ่านง่าย และนำไปใช้ได้จริง

--- บทสนทนาที่ประชุม (ทุก agent ทุกรอบ) ---
{chunked}

จัดรูปแบบคำตอบเป็นหัวข้อ Markdown ตามนี้เป๊ะๆ:
## 🎯 สรุปประเด็นสำคัญ
## ✅ มติที่ตกลงร่วมกัน
## 📋 Action Items (ระบุแผนกที่รับผิดชอบแต่ละรายการให้ชัดเจน)
## ⚠️ ความเห็นที่ยังขัดแย้ง/ต้องตัดสินใจเพิ่ม
## 📅 ข้อเสนอ Deadline คร่าวๆ"""
    return call_gemini(prompt + lang_suffix(lang), model_name, api_key, max_output_tokens=4096)


def apply_rebuttal(topic: str, meeting_log: str, prior_summary: str, rebuttal_text: str,
                    api_key: str, model_name: str, lang: str = "TH") -> str:
    prompt = f"""คุณคือประธานที่ประชุมของทีม AI AQUALINE หัวข้อ "{topic}"

--- สรุปมติเดิมที่เสนอไปก่อนหน้า ---
{smart_chunk_knowledge(prior_summary, 6000)}

--- ความเห็นแย้ง/ข้อเสนอเพิ่มเติมจากผู้บริหาร (มนุษย์) ---
{rebuttal_text}

ภารกิจ: ปรับปรุงมติให้สอดคล้องกับความเห็นแย้ง/ข้อเสนอเพิ่มเติมข้างต้น อธิบายสั้นๆว่าจุดไหนถูกแก้ไขเพราะอะไร
แล้วสรุปมติฉบับใหม่ (final) ด้วยรูปแบบหัวข้อเดียวกับเดิม:
## 🎯 สรุปประเด็นสำคัญ
## ✅ มติที่ตกลงร่วมกัน (ฉบับปรับปรุง)
## 📋 Action Items (ระบุแผนกที่รับผิดชอบแต่ละรายการให้ชัดเจน)
## 📅 ข้อเสนอ Deadline คร่าวๆ

ปิดท้ายด้วยบรรทัด: ### 🔒 มติฉบับนี้พร้อมส่งต่อให้เลขานุการแจกงาน"""
    return call_gemini(prompt + lang_suffix(lang), model_name, api_key, max_output_tokens=4096)


# ════════════════════════════════════════════════════════════════════
# 👩‍💼 SECRETARY — แตกมติที่ล็อกแล้วเป็นงานต่อแผนก + ตอบแชท 1:1 กับผู้บริหาร
# ════════════════════════════════════════════════════════════════════
def _strip_json_fence(raw: str) -> str:
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    return cleaned


def secretary_breakdown(topic: str, locked_summary: str, api_key: str, model_name: str, lang: str = "TH") -> dict:
    """ให้เลขานุการ AI แตกมติที่ล็อกแล้วเป็น task ต่อแผนก พร้อม deadline และคำถามที่ต้องถามผู้บริหารก่อนเริ่มงาน
    คืน dict: {"tasks": [{"dept_id","title","detail","deadline","clarifying_questions":[...]}], "secretary_note": "..."}"""
    dept_list = "\n".join(f"- {did}: {d['icon']} {d['name']} — {d['desc']}" for did, d in DEPARTMENTS.items())
    prompt = f"""คุณคือ "เลขานุการ AI" ของทีม AQUALINE หน้าที่คือแตกมติที่ประชุมเป็นงานให้แต่ละแผนกไปทำต่อ

--- มติที่ประชุมล็อกแล้ว เรื่อง "{topic}" ---
{smart_chunk_knowledge(locked_summary, 8000)}

--- รายชื่อแผนกที่มีอยู่จริงในระบบ (ใช้ dept_id ตามนี้เท่านั้น) ---
{dept_list}

ภารกิจ: แตกมติข้างต้นเป็นรายการงาน (task) มอบหมายให้แผนกที่เกี่ยวข้อง โดยแต่ละ task ต้องมี field:
- dept_id: ต้องเป็นหนึ่งใน D1-D6 ด้านบนเท่านั้น
- title: ชื่องานสั้นๆ ไม่เกิน 15 คำ
- detail: รายละเอียดงาน 1-2 ประโยค
- deadline: วันที่ประมาณ (เช่น "ภายใน 3 วัน")
- clarifying_questions: list คำถามที่แผนกนี้ "ต้องถามผู้บริหารก่อน" จึงจะเริ่มงานได้ (list ว่าง [] ถ้าไม่มี)

ตอบเป็น JSON ล้วนๆเท่านั้น ห้ามมีข้อความอื่นนอกเหนือ JSON ห้ามใส่ ```json ครอบ ตามรูปแบบนี้:
{{"tasks": [{{"dept_id": "D2", "title": "...", "detail": "...", "deadline": "...", "clarifying_questions": ["...", "..."]}}], "secretary_note": "สรุปสั้นๆจากเลขาถึงผู้บริหาร 1-2 ประโยค"}}"""
    raw = call_gemini(prompt, model_name, api_key, max_output_tokens=4096)
    cleaned = _strip_json_fence(raw)
    try:
        data = json.loads(cleaned)
        if not isinstance(data, dict) or "tasks" not in data:
            return {"tasks": [], "secretary_note": "⚠️ เลขาตอบไม่ตรงรูปแบบที่กำหนด — กรุณาลองใหม่", "_raw": raw}
        valid_depts = set(DEPARTMENTS.keys())
        for t in data["tasks"]:
            if t.get("dept_id") not in valid_depts:
                t["dept_id"] = "D1"
            t.setdefault("clarifying_questions", [])
            t.setdefault("title", "(ไม่มีชื่องาน)")
            t.setdefault("detail", "")
            t.setdefault("deadline", "")
        data.setdefault("secretary_note", "")
        return data
    except Exception:
        return {"tasks": [], "secretary_note": "⚠️ แปลง JSON จากเลขาไม่สำเร็จ — กรุณาลองใหม่", "_raw": raw}


def secretary_chat_reply(user_message: str, chat_history: list, tasks: list,
                          api_key: str, model_name: str, lang: str = "TH") -> str:
    """ตอบกลับในแชท 1:1 เลขา↔ผู้บริหาร โดยมีบริบทงานทั้งหมดที่แจกไปแล้ว — นี่คือ "ศูนย์กลาง" ที่ทุกแผนก
    ส่งคำถามก่อนเริ่มงานมารวมกัน ดังนั้นเลขาต้องรู้สถานะงาน/คำถามที่ค้างอยู่ทั้งหมดเสมอ"""
    hist_text = "\n".join(
        f"{'ผู้บริหาร' if m.get('role') == 'user' else 'เลขา'}: {m.get('text','')}"
        for m in chat_history[-20:]
    )
    tasks_text = "\n".join(
        f"- [{t.get('dept_id')}] {t.get('title')} (เดดไลน์ {t.get('deadline','-')}, สถานะ {t.get('status','assigned')})"
        + (f" — คำถามที่ยังไม่ตอบ: {[q for q in t.get('clarifying_questions',[]) if q not in t.get('answers',{})]}"
           if [q for q in t.get('clarifying_questions', []) if q not in t.get('answers', {})] else "")
        for t in tasks
    )
    prompt = f"""คุณคือ "เลขานุการ AI" ของทีม AQUALINE สื่อสาร 1:1 กับผู้บริหาร พูดสุภาพ กระชับ เป็นมิตร
ทำหน้าที่ประสานงานระหว่างผู้บริหารกับทุกแผนก และเป็นช่องทางเดียวที่รวมคำถามจากทุกแผนกก่อนเริ่มงาน

--- งานทั้งหมดที่แจกไปแล้ว ---
{tasks_text or '(ยังไม่มีงานที่แจก)'}

--- ประวัติแชทล่าสุด ---
{hist_text}

ผู้บริหารพิมพ์ล่าสุด: {user_message}

ตอบกลับในฐานะเลขา ถ้าผู้บริหารกำลังตอบคำถามที่แผนกใดแผนกหนึ่งถามไว้ ให้ยืนยันว่าจะนำคำตอบไปแจ้งแผนกนั้นต่อ
ถ้าผู้บริหารถามสถานะงาน ให้สรุปจากรายการงานด้านบน ตอบสั้นกระชับ ไม่ต้องทวนคำถามผู้บริหารซ้ำ"""
    return call_gemini(prompt + lang_suffix(lang), model_name, api_key, max_output_tokens=1024)
