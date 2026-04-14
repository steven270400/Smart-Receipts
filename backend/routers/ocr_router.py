from fastapi import APIRouter, File, UploadFile

from backend.core.exceptions import DatabaseException, LLMException, OCRException
from backend.core.response import success_response
from backend.services.ocr_service import process_ocr_upload

router = APIRouter(tags=["ocr"])


@router.post("/ocr")
async def ocr_image(file: UploadFile = File(...)):
    try:
        data = process_ocr_upload(file)
        return success_response(data=data)
    except (OCRException, LLMException, DatabaseException):
        raise
