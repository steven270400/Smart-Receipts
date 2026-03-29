from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import time
import uuid
from datetime import datetime

from backend.ocr_service import recognize_text
from backend.extract_service import extract_receipt_info
from backend.db_service import init_db, save_receipt, get_receipts, get_statistics

app = FastAPI()
init_db()

UPLOAD_DIR = "uploads"

if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)


def build_safe_upload_path(original_filename: str) -> tuple[str, str]:
    # Never trust client-provided filename for storage path.
    base_name = os.path.basename(original_filename or "")
    _, ext = os.path.splitext(base_name)
    ext = ext.lower()

    if not ext or len(ext) > 10 or not ext.replace(".", "", 1).isalnum():
        ext = ".bin"

    saved_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_DIR, saved_filename)
    return file_path, saved_filename


def validate_receipt_info(info: dict) -> tuple[bool, str]:
    amount = info.get("amount")
    date_value = info.get("date")

    if amount is None or not date_value:
        return False, "missing_amount_or_date"

    try:
        float(amount)
        datetime.strptime(str(date_value), "%Y-%m-%d")
    except (TypeError, ValueError):
        return False, "invalid_amount_or_date"

    return True, "ok"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/test")
def test():
    return {"message": "ok"}

@app.get("/receipts")
def list_receipts():
    data = get_receipts()

    return {
        "data": data
    }

@app.get("/statistics")
def statistic():
    stats = get_statistics()
    return {
        "data": stats
    }


@app.post("/ocr")
async def ocr_image(file: UploadFile = File(...)):

    file_path, saved_filename = build_safe_upload_path(file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    start = time.time()
    texts = recognize_text(file_path)
    end = time.time()

    print("OCR elapsed:", end - start)

    info = extract_receipt_info(texts)
    should_save, save_reason = validate_receipt_info(info)

    if should_save:
        save_receipt(info)

    return {
        "filename": file.filename,
        "saved_filename": saved_filename,
        "ocr_result": texts,
        "extracted_info": info,
        "saved": should_save,
        "save_reason": save_reason
    }
