from fastapi import APIRouter, Depends
from pydantic import ValidationError

from backend.core.exceptions import DatabaseException, NotFoundException, ParamException
from backend.core.response import success_response
from backend.schemas.receipt import ReceiptCreateSchema, ReceiptQuerySchema, ReceiptUpdateSchema
from backend.services.receipt_service import (
    build_operation_log,
    create_receipt_service,
    delete_receipt_service,
    list_receipts_service,
    update_receipt_service,
)

router = APIRouter(prefix="/receipts", tags=["receipts"])


def parse_query(
    page: int = 1,
    size: int = 10,
    merchant: str | None = None,
    keyword: str | None = None,
    category_id: int | None = None,
    payment_method_id: int | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
) -> ReceiptQuerySchema:
    try:
        return ReceiptQuerySchema(
            page=page,
            size=size,
            merchant=merchant,
            keyword=keyword,
            category_id=category_id,
            payment_method_id=payment_method_id,
            start_time=start_time,
            end_time=end_time,
        )
    except ValidationError as exc:
        raise ParamException(str(exc)) from exc


@router.get("")
def list_receipts(query: ReceiptQuerySchema = Depends(parse_query)):
    try:
        data = list_receipts_service(query)
        return success_response(data=data)
    except ParamException:
        raise
    except Exception as exc:
        raise DatabaseException("list receipts failed") from exc


@router.post("")
def create_receipt(payload: ReceiptCreateSchema):
    try:
        data = create_receipt_service(payload)
        return success_response(data={"record": data, "operation_log": build_operation_log("create", data.get("id"))})
    except (ParamException, DatabaseException, NotFoundException):
        raise


@router.put("/{receipt_id}")
def update_receipt(receipt_id: int, payload: ReceiptUpdateSchema):
    try:
        data = update_receipt_service(receipt_id, payload)
        return success_response(data={"record": data, "operation_log": build_operation_log("update", receipt_id)})
    except (ParamException, DatabaseException, NotFoundException):
        raise


@router.delete("/{receipt_id}")
def delete_receipt(receipt_id: int):
    try:
        delete_receipt_service(receipt_id)
        return success_response(data={"operation_log": build_operation_log("delete", receipt_id)})
    except (ParamException, DatabaseException, NotFoundException):
        raise
