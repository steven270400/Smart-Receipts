# System Design

## Layering
- `backend/routers`: API route definitions and request orchestration
- `backend/services`: business services (receipt/statistics/ocr)
- `backend/db_service.py`: database access and SQL
- `backend/schemas`: Pydantic request models and validation
- `backend/core`: exception system, error handlers, response contract
- `backend/utils`: shared time parsing/formatting utilities

## Frontend Structure
- `frontend/src/views`: page-level views (`Dashboard`, `ReceiptManage`, `OcrConsole`)
- `frontend/src/components`: reusable UI modules
- `frontend/src/api`: API encapsulation with unified response handling
- `frontend/src/utils/date.js`: frontend date format/parse helpers

## OCR/LLM Data Flow
1. Frontend uploads file to `/ocr`.
2. Backend stores file in `uploads/` with safe filename.
3. OCR engine returns text lines.
4. Extract service generates baseline fields and optional LLM-enhanced selection.
5. Backend normalizes to `transaction_time` and validates key fields.
6. If valid, receipt and source metadata are persisted.
7. API returns unified payload `{ code, message, data }`.

## Logging
- Operation log: create/update/delete returns `operation_type`, `record_id`, `time`.
- OCR/LLM log: records OCR latency, LLM enabled flag, fallback flag.
- API error log: records path, error message, timestamp.
