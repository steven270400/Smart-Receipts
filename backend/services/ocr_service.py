import logging
import os
import shutil
import time
import uuid
from datetime import datetime

from backend import db_service
from backend.core.exceptions import DatabaseException, LLMException, OCRException
from backend.extract_service import extract_receipt_info_with_meta
from backend.ocr_service import recognize_text

logger = logging.getLogger("smartreceipts.ocr")
UPLOAD_DIR = "uploads"


if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)


def build_safe_upload_path(original_filename: str) -> tuple[str, str]:
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
    transaction_time = info.get("transaction_time")

    if amount is None or not transaction_time:
        return False, "missing_amount_or_transaction_time"

    try:
        float(amount)
        datetime.strptime(str(transaction_time), "%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError):
        return False, "invalid_amount_or_transaction_time"

    return True, "ok"


def process_ocr_upload(upload_file) -> dict:
    try:
        file_path, saved_filename = build_safe_upload_path(upload_file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    except Exception as exc:
        raise OCRException("save upload file failed") from exc

    try:
        ocr_start = time.time()
        texts = recognize_text(file_path)
        ocr_elapsed_ms = int((time.time() - ocr_start) * 1000)
    except Exception as exc:
        raise OCRException("ocr recognize failed") from exc

    try:
        info, llm_meta = extract_receipt_info_with_meta(texts)
    except Exception as exc:
        raise LLMException("llm extraction failed") from exc

    if info.get("date") and not info.get("transaction_time"):
        info["transaction_time"] = f"{info['date']} 00:00:00"
    info.pop("date", None)

    should_save, save_reason = validate_receipt_info(info)
    llm_fallback = bool(llm_meta.get("error"))
    llm_enabled = bool(llm_meta.get("llm_enabled"))
    match_status = llm_meta.get("match_status")
    match_failure_reason = llm_meta.get("match_failure_reason")
    selected_amount_id = llm_meta.get("selected_amount_id")
    final_amount = info.get("amount")

    if should_save:
        try:
            db_service.save_receipt(
                {
                    **info,
                    "source_type": "ocr",
                    "file_name": saved_filename,
                    "raw_text": texts,
                    "extracted_json": {**info, "llm_meta": llm_meta},
                }
            )
        except Exception as exc:
            raise DatabaseException("save ocr receipt failed") from exc

    logger.info(
        "ocr_log elapsed_ms=%s llm_enabled=%s llm_fallback=%s",
        ocr_elapsed_ms,
        llm_enabled,
        llm_fallback,
    )
    if llm_enabled:
        if match_status == "matched":
            logger.info(
                "llm_match=matched amount_id=%s final_amount=%s",
                selected_amount_id,
                final_amount,
            )
        else:
            logger.info(
                "llm_match=failed_fallback_auto reason=%s amount_id=%s final_amount=%s action=转至自动匹配",
                match_failure_reason or "unknown",
                selected_amount_id,
                final_amount,
            )

    return {
        "filename": upload_file.filename,
        "saved_filename": saved_filename,
        "ocr_result": texts,
        "extracted_info": info,
        "saved": should_save,
        "save_reason": save_reason,
        "ocr_meta": {
            "ocr_elapsed_ms": ocr_elapsed_ms,
            "llm_enabled": llm_enabled,
            "llm_fallback": llm_fallback,
        },
    }
