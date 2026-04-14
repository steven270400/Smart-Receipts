from datetime import datetime

from backend import db_service
from backend.core.exceptions import DatabaseException, NotFoundException, ParamException
from backend.schemas.receipt import ReceiptCreateSchema, ReceiptQuerySchema, ReceiptUpdateSchema


def _normalize_receipt_row(row: dict | None) -> dict | None:
    if row is None:
        return None
    normalized = dict(row)
    normalized.pop("date", None)
    return normalized


def _normalize_payload(payload: dict) -> dict:
    normalized = dict(payload)
    category_id = normalized.get("category_id")
    payment_method_id = normalized.get("payment_method_id")

    if category_id is None and normalized.get("category"):
        category_id = db_service.get_category_id_by_name(normalized.get("category"))
    if payment_method_id is None and normalized.get("payment_method"):
        payment_method_id = db_service.get_payment_method_id_by_name(normalized.get("payment_method"))

    if category_id is None:
        raise ParamException("分类不存在")
    if payment_method_id is None:
        raise ParamException("支付方式不存在")

    normalized["category_id"] = int(category_id)
    normalized["payment_method_id"] = int(payment_method_id)
    return normalized


def list_receipts_service(query: ReceiptQuerySchema) -> dict:
    try:
        result = db_service.list_receipts(
            page=query.page,
            size=query.size,
            merchant=query.merchant,
            keyword=query.keyword,
            category_id=query.category_id,
            payment_method_id=query.payment_method_id,
            start_time=query.start_time,
            end_time=query.end_time,
        )
    except ValueError as exc:
        raise ParamException(str(exc)) from exc
    except Exception as exc:
        raise DatabaseException("query receipts failed") from exc

    rows = [_normalize_receipt_row(item) for item in (result.get("data") or [])]
    return {
        "list": rows,
        "pagination": result.get("pagination") or {"page": query.page, "size": query.size, "total": 0},
    }


def create_receipt_service(payload: ReceiptCreateSchema) -> dict:
    normalized_payload = _normalize_payload(payload.model_dump())
    try:
        record = db_service.create_manual_receipt(normalized_payload)
    except ValueError as exc:
        raise ParamException(str(exc)) from exc
    except Exception as exc:
        raise DatabaseException("create receipt failed") from exc

    return _normalize_receipt_row(record)


def update_receipt_service(receipt_id: int, payload: ReceiptUpdateSchema) -> dict:
    normalized_payload = _normalize_payload(payload.model_dump())
    try:
        record = db_service.update_receipt_by_id(receipt_id, normalized_payload)
    except LookupError as exc:
        raise NotFoundException(str(exc)) from exc
    except RuntimeError as exc:
        raise ParamException(str(exc)) from exc
    except ValueError as exc:
        raise ParamException(str(exc)) from exc
    except Exception as exc:
        raise DatabaseException("update receipt failed") from exc

    return _normalize_receipt_row(record)


def delete_receipt_service(receipt_id: int) -> None:
    try:
        db_service.soft_delete_receipt(receipt_id)
    except LookupError as exc:
        raise NotFoundException(str(exc)) from exc
    except RuntimeError as exc:
        raise ParamException(str(exc)) from exc
    except Exception as exc:
        raise DatabaseException("delete receipt failed") from exc


def build_operation_log(operation_type: str, record_id: int | None = None) -> dict:
    return {
        "operation_type": operation_type,
        "record_id": record_id,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
