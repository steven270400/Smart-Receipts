from fastapi import APIRouter

from backend.core.exceptions import DatabaseException, NotFoundException, ParamException
from backend.core.response import success_response
from backend.schemas.system import NamePayloadSchema
from backend.services.system_service import (
    create_category_service,
    create_payment_method_service,
    delete_category_service,
    delete_payment_method_service,
    list_categories_service,
    list_payment_methods_service,
    rename_category_service,
    rename_payment_method_service,
)

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/categories")
def list_categories():
    try:
        data = list_categories_service()
        return success_response(data=data)
    except (ParamException, DatabaseException, NotFoundException):
        raise


@router.post("/categories")
def create_category(payload: NamePayloadSchema):
    try:
        data = create_category_service(payload.name)
        return success_response(data=data)
    except (ParamException, DatabaseException, NotFoundException):
        raise


@router.delete("/categories/{category_id}")
def delete_category(category_id: int):
    try:
        delete_category_service(category_id)
        return success_response(data={"id": category_id})
    except (ParamException, DatabaseException, NotFoundException):
        raise


@router.put("/categories/{category_id}")
def rename_category(category_id: int, payload: NamePayloadSchema):
    try:
        data = rename_category_service(category_id, payload.name)
        return success_response(data=data)
    except (ParamException, DatabaseException, NotFoundException):
        raise


@router.get("/payment-methods")
def list_payment_methods():
    try:
        data = list_payment_methods_service()
        return success_response(data=data)
    except (ParamException, DatabaseException, NotFoundException):
        raise


@router.post("/payment-methods")
def create_payment_method(payload: NamePayloadSchema):
    try:
        data = create_payment_method_service(payload.name)
        return success_response(data=data)
    except (ParamException, DatabaseException, NotFoundException):
        raise


@router.put("/payment-methods/{payment_method_id}")
def rename_payment_method(payment_method_id: int, payload: NamePayloadSchema):
    try:
        data = rename_payment_method_service(payment_method_id, payload.name)
        return success_response(data=data)
    except (ParamException, DatabaseException, NotFoundException):
        raise


@router.delete("/payment-methods/{payment_method_id}")
def delete_payment_method(payment_method_id: int):
    try:
        delete_payment_method_service(payment_method_id)
        return success_response(data={"id": payment_method_id})
    except (ParamException, DatabaseException, NotFoundException):
        raise
