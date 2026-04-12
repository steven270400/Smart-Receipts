from datetime import datetime
import os
import shutil
import time
import uuid

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from backend.db_service import (
    create_manual_receipt,
    get_category_id_by_name,
    get_payment_method_id_by_name,
    get_statistics,
    init_db,
    list_receipts,
    save_receipt,
    soft_delete_receipt,
    update_receipt_by_id,
)
from backend.extract_service import extract_receipt_info_with_meta
from backend.ocr_service import recognize_text

app = FastAPI()
if os.getenv("SKIP_DB_INIT", "").strip().lower() not in {"1", "true", "yes", "on"}:
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
def receipts(
    page: int = Query(1, ge=1),
    size: int = Query(1000, ge=1, le=1000),
    merchant: str | None = None,
    category_id: int | None = None,
    payment_method_id: int | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
):
    try:
        return list_receipts(
            page=page,
            size=size,
            merchant=merchant,
            category_id=category_id,
            payment_method_id=payment_method_id,
            start_time=start_time,
            end_time=end_time,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/receipts")
def create_receipt(payload: dict):
    category_id = payload.get("category_id")
    payment_method_id = payload.get("payment_method_id")

    if category_id is None and payload.get("category"):
        category_id = get_category_id_by_name(payload.get("category"))
    if payment_method_id is None and payload.get("payment_method"):
        payment_method_id = get_payment_method_id_by_name(payload.get("payment_method"))

    normalized = {
        "merchant": payload.get("merchant"),
        "amount": payload.get("amount"),
        "transaction_time": payload.get("transaction_time") or payload.get("date"),
        "category_id": category_id,
        "payment_method_id": payment_method_id,
        "notes": payload.get("notes"),
    }

    try:
        record = create_manual_receipt(normalized)
        return {"data": record}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.put("/receipts/{receipt_id}")
def update_receipt(receipt_id: int, payload: dict):
    category_id = payload.get("category_id")
    payment_method_id = payload.get("payment_method_id")

    if category_id is None and payload.get("category"):
        category_id = get_category_id_by_name(payload.get("category"))
    if payment_method_id is None and payload.get("payment_method"):
        payment_method_id = get_payment_method_id_by_name(payload.get("payment_method"))

    normalized = {
        "merchant": payload.get("merchant"),
        "amount": payload.get("amount"),
        "transaction_time": payload.get("transaction_time") or payload.get("date"),
        "category_id": category_id,
        "payment_method_id": payment_method_id,
        "notes": payload.get("notes"),
    }

    try:
        record = update_receipt_by_id(receipt_id, normalized)
        return {"data": record}
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.delete("/receipts/{receipt_id}")
def delete_receipt(receipt_id: int):
    try:
        soft_delete_receipt(receipt_id)
        return {"message": "ok"}
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


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

    info, llm_meta = extract_receipt_info_with_meta(texts)
    should_save, save_reason = validate_receipt_info(info)

    if should_save:
        save_receipt(
            {
                **info,
                "source_type": "ocr",
                "file_name": saved_filename,
                "raw_text": texts,
                "extracted_json": {**info, "llm_meta": llm_meta},
            }
        )

    return {
        "filename": file.filename,
        "saved_filename": saved_filename,
        "ocr_result": texts,
        "extracted_info": info,
        "saved": should_save,
        "save_reason": save_reason,
    }
