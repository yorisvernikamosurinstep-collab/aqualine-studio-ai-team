"""
product_knowledge.py — ฐานความรู้สินค้า (Knowledge Hub) แยกตามสินค้า/แบรนด์
======================================================================
แต่ละ "สินค้า" มีคลังความรู้ของตัวเอง (ไฟล์ PDF/Word/โน้ตที่อัปโหลด หรือในอนาคต
จะซิงค์มาจากโฟลเดอร์ Google Drive จริง — ดู drive_folder_url/drive_folder_id)
ความรู้นี้คือ "สมองรวม" ที่ส่งให้ AI agent ทุกแผนกใช้อ้างอิงตอนประชุม/ทำงาน
ตามวิสัยทัศน์ของผู้ใช้ (NotebookLM-style shared knowledge ต่อสินค้า)

บันทึกถาวรลงไฟล์ product_knowledge.json (อยู่ข้าง ๆ ไฟล์นี้) และใช้ร่วมกันทุกหน้าในแอป
"""

import hashlib
import json
import os
import uuid
from datetime import datetime

KB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "product_knowledge.json")

# โครงสร้าง product แต่ละตัวที่เก็บใน data["products"]:
# {
#   "id": "uuid สั้น",
#   "name": "เช่น รางน้ำฝน VG",
#   "drive_folder_url": "",   # ลิงก์โฟลเดอร์ Google Drive (เตรียมไว้สำหรับขั้นเชื่อม Drive จริง)
#   "drive_folder_id": "",    # Drive folder id หลังเชื่อม OAuth จริง (อนาคต)
#   "notes": "",              # โน้ต/บริฟสินค้าที่พิมพ์เพิ่มเองได้ทันที
#   "files": [
#       {"filename": "...", "text": "...", "source": "upload" | "drive", "added_at": "iso datetime"}
#   ],
#   "created_at": "iso datetime",
# }


def _empty_data() -> dict:
    return {"products": []}


def load_kb() -> dict:
    """โหลดฐานความรู้ทั้งหมดจากไฟล์ — คืน dict เปล่าตามโครงสร้างถ้ายังไม่มีไฟล์/ไฟล์เสีย"""
    if os.path.exists(KB_FILE):
        try:
            with open(KB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict) or "products" not in data:
                return _empty_data()
            return data
        except Exception:
            return _empty_data()
    return _empty_data()


def save_kb(data: dict) -> None:
    with open(KB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_products() -> list:
    """คืน list ของสินค้าทั้งหมด เรียงตามวันที่สร้าง (เก่า→ใหม่)"""
    return load_kb()["products"]


def get_product(product_id: str) -> dict | None:
    for p in get_products():
        if p["id"] == product_id:
            return p
    return None


def add_product(name: str, notes: str = "") -> dict:
    """สร้างสินค้าใหม่ในฐานความรู้ — คืน dict ของสินค้าที่สร้าง"""
    data = load_kb()
    new_p = {
        "id": uuid.uuid4().hex[:10],
        "name": name.strip(),
        "drive_folder_url": "",
        "drive_folder_id": "",
        "notes": notes.strip(),
        "files": [],
        "created_at": datetime.now().isoformat(timespec="seconds"),
    }
    data["products"].append(new_p)
    save_kb(data)
    return new_p


def delete_product(product_id: str) -> None:
    data = load_kb()
    data["products"] = [p for p in data["products"] if p["id"] != product_id]
    save_kb(data)


def update_product(product_id: str, **fields) -> None:
    """แก้ field ใดก็ได้ของสินค้า เช่น update_product(pid, name="...", notes="...", drive_folder_url="...")"""
    data = load_kb()
    for p in data["products"]:
        if p["id"] == product_id:
            p.update(fields)
            break
    save_kb(data)


def _content_hash(text: str) -> str:
    """แฮชเนื้อหาไฟล์ (ตัดช่องว่าง/ขึ้นบรรทัดส่วนเกินออกก่อน) ใช้เทียบไฟล์ซ้ำแบบไม่สนใจรูปแบบเล็กน้อยที่ต่างกัน"""
    normalized = " ".join((text or "").split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def add_file_to_product(product_id: str, filename: str, text: str, source: str = "upload",
                         dedup: bool = True) -> dict:
    """เพิ่มไฟล์เข้าฐานความรู้สินค้า
    ถ้า dedup=True (ค่าเริ่มต้น — Item 5: memory consolidation) จะข้ามการเพิ่มถ้ามีไฟล์ที่เนื้อหา
    เหมือนกันอยู่แล้วในสินค้านี้ (เทียบจาก content hash ไม่สนใจชื่อไฟล์) — กันฐานความรู้บวมจากการบันทึก
    ซ้ำซ้อน เช่น Pipeline ที่รันหัวข้อใกล้เคียงกันหลายรอบ
    คืน {"added": bool, "skipped_duplicate_of": str|None} ให้ฝั่งเรียกใช้เช็คผลได้"""
    data = load_kb()
    new_hash = _content_hash(text)
    result = {"added": False, "skipped_duplicate_of": None}
    for p in data["products"]:
        if p["id"] != product_id:
            continue
        if dedup:
            dup = next((f for f in p.get("files", []) if f.get("content_hash") == new_hash), None)
            if dup:
                result["skipped_duplicate_of"] = dup["filename"]
                return result
        p.setdefault("files", []).append({
            "filename": filename,
            "text": text,
            "source": source,
            "added_at": datetime.now().isoformat(timespec="seconds"),
            "content_hash": new_hash,
        })
        result["added"] = True
        break
    if result["added"]:
        save_kb(data)
    return result


def consolidate_product_knowledge(product_id: str, max_auto_files: int = 20) -> dict:
    """รูทีนรวบรวม/ทำความสะอาดฐานความรู้ของสินค้านี้ (Item 5 — memory consolidation):
    1) ลบไฟล์ที่เนื้อหาซ้ำกันเป๊ะ (เทียบ content hash) เก็บไว้แค่ฉบับล่าสุดของแต่ละชุดที่ซ้ำกัน
    2) backfill content_hash ให้ไฟล์เก่าที่เพิ่มไว้ก่อนมีระบบ dedup (ยังไม่มีฟิลด์นี้)
    3) ถ้าไฟล์ source="pipeline" (บันทึกอัตโนมัติจาก Pipeline) มีเกิน max_auto_files ไฟล์
       จะตัดไฟล์ pipeline ที่เก่าที่สุดทิ้ง เหลือไว้แค่ล่าสุด max_auto_files ไฟล์
       (ไฟล์ source="upload"/"drive" ที่ผู้ใช้ตั้งใจเพิ่ม/ซิงค์เองจะไม่ถูกแตะต้องเลย)
    คืน {"removed_duplicates": int, "removed_old_auto": int, "remaining_files": int}"""
    data = load_kb()
    summary = {"removed_duplicates": 0, "removed_old_auto": 0, "remaining_files": 0}
    for p in data["products"]:
        if p["id"] != product_id:
            continue
        files = p.get("files", [])
        for f in files:
            if not f.get("content_hash"):
                f["content_hash"] = _content_hash(f.get("text", ""))

        files.sort(key=lambda f: f.get("added_at", ""))  # เก่า -> ใหม่
        seen_at = {}
        deduped = []
        for f in files:
            h = f["content_hash"]
            if h in seen_at:
                summary["removed_duplicates"] += 1
                deduped[seen_at[h]] = f  # เจอซ้ำ -> แทนที่ด้วยฉบับล่าสุด (เก็บฉบับใหม่สุดของแต่ละ hash ไว้)
            else:
                seen_at[h] = len(deduped)
                deduped.append(f)
        files = deduped

        auto_files = sorted((f for f in files if f.get("source") == "pipeline"),
                             key=lambda f: f.get("added_at", ""))
        if len(auto_files) > max_auto_files:
            n_to_drop = len(auto_files) - max_auto_files
            drop_ids = {id(f) for f in auto_files[:n_to_drop]}
            files = [f for f in files if id(f) not in drop_ids]
            summary["removed_old_auto"] = n_to_drop

        p["files"] = files
        summary["remaining_files"] = len(files)
        break

    save_kb(data)
    return summary


def delete_file_from_product(product_id: str, filename: str) -> None:
    data = load_kb()
    for p in data["products"]:
        if p["id"] == product_id:
            p["files"] = [f for f in p.get("files", []) if f["filename"] != filename]
            break
    save_kb(data)


def replace_drive_files(product_id: str, drive_files: list) -> None:
    """แทนที่ไฟล์ source="drive" ทั้งหมดของสินค้านี้ด้วยรายการที่ซิงค์มาใหม่
    (ไฟล์ source="upload" ที่แนบเองไม่ถูกแตะต้อง) — เรียกทุกครั้งที่กด "ซิงค์จาก Drive"
    drive_files: [{"filename": "...", "text": "..."}, ...]"""
    data = load_kb()
    now = datetime.now().isoformat(timespec="seconds")
    for p in data["products"]:
        if p["id"] == product_id:
            kept = [f for f in p.get("files", []) if f.get("source") != "drive"]
            new_drive = [
                {"filename": f["filename"], "text": f["text"], "source": "drive", "added_at": now}
                for f in drive_files
            ]
            p["files"] = kept + new_drive
            p["drive_last_synced"] = now
            break
    save_kb(data)


def get_product_knowledge_text(product_id: str) -> str:
    """รวมความรู้ทั้งหมดของสินค้าตัวนี้ (โน้ต + ทุกไฟล์) เป็น string เดียว สำหรับส่งเข้า prompt ของ agent"""
    p = get_product(product_id)
    if not p:
        return ""
    parts = []
    if p.get("notes"):
        parts.append(f"--- โน้ต/บริฟสินค้า: {p['name']} ---\n{p['notes']}")
    for f in p.get("files", []):
        parts.append(f"--- {f['filename']} (สินค้า: {p['name']}) ---\n{f['text']}")
    return "\n\n".join(parts)


def get_combined_knowledge_text(product_ids: list | None = None) -> str:
    """รวมความรู้จากหลายสินค้า (หรือทั้งหมดถ้าไม่ระบุ product_ids) เป็น string เดียว
    — ใช้เป็น "สมองรวม" ส่งให้ทุกแผนก/ทุก agent อ้างอิงตอนประชุม"""
    products = get_products()
    if product_ids is not None:
        products = [p for p in products if p["id"] in product_ids]
    texts = [get_product_knowledge_text(p["id"]) for p in products]
    return "\n\n".join(t for t in texts if t)


def get_product_names() -> dict:
    """{id: name} — สะดวกสำหรับทำ dropdown/multiselect เลือกสินค้า"""
    return {p["id"]: p["name"] for p in get_products()}


def total_chars(product_id: str) -> int:
    """จำนวนตัวอักษรความรู้ทั้งหมดของสินค้านี้ (โน้ต + ทุกไฟล์) — ใช้โชว์สถานะ/ขนาดคลังความรู้"""
    p = get_product(product_id)
    if not p:
        return 0
    return len(p.get("notes", "")) + sum(len(f.get("text", "")) for f in p.get("files", []))
