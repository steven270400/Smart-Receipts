# API Design

## Unified Response
All APIs return:

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

Error responses keep the same structure with non-zero `code` and readable `message`.

## Receipt APIs

### `GET /receipts`
Query params:
- `page` (int >= 1)
- `size` (int 1..1000)
- `merchant` (optional)
- `category_id` (optional int)
- `payment_method_id` (optional int)
- `start_time` (optional, `YYYY-MM-DD` or `YYYY-MM-DD HH:mm:ss`)
- `end_time` (optional, `YYYY-MM-DD` or `YYYY-MM-DD HH:mm:ss`)

`data`:
- `list`: receipt array
- `pagination`: `{ page, size, total }`

### `POST /receipts`
Body fields:
- `merchant` (required)
- `amount` (required, >= 0)
- `transaction_time` (required, `YYYY-MM-DD HH:mm:ss`)
- `category_id` or `category` (required logically)
- `payment_method_id` or `payment_method` (required logically)
- `notes` (optional)

### `PUT /receipts/{receipt_id}`
Same validation as create.

### `DELETE /receipts/{receipt_id}`
Soft delete only.

## Statistics API

### `GET /statistics`
Returns totals and trends based on active records (`is_deleted = 0`) and `transaction_time`.

## OCR API

### `POST /ocr`
Multipart upload with `file`.

`data` includes:
- `ocr_result`
- `extracted_info` (uses `transaction_time`)
- `saved`, `save_reason`
- `ocr_meta`: `ocr_elapsed_ms`, `llm_enabled`, `llm_fallback`
