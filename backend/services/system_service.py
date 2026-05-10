from backend import db_service
from backend.core.exceptions import DatabaseException, NotFoundException, ParamException


def _normalize_dimension_rows(rows: list[dict] | None) -> list[dict]:
    result = []
    for row in rows or []:
        result.append(
            {
                "id": int(row.get("id")),
                "name": row.get("name") or "",
                "receipt_count": int(row.get("receipt_count") or 0),
                "latest_time": row.get("latest_time"),
            }
        )
    return result


def list_categories_service() -> list[dict]:
    try:
        return _normalize_dimension_rows(db_service.list_categories_with_usage())
    except Exception as exc:
        raise DatabaseException("query categories failed") from exc


def create_category_service(name: str) -> dict:
    try:
        return db_service.create_category(name)
    except ValueError as exc:
        raise ParamException(str(exc)) from exc
    except Exception as exc:
        raise DatabaseException("create category failed") from exc


def delete_category_service(category_id: int) -> None:
    try:
        db_service.delete_category_with_migration(category_id)
    except LookupError as exc:
        raise NotFoundException(str(exc)) from exc
    except RuntimeError as exc:
        raise ParamException(str(exc)) from exc
    except Exception as exc:
        raise DatabaseException("delete category failed") from exc


def rename_category_service(category_id: int, name: str) -> dict:
    try:
        return db_service.rename_category(category_id, name)
    except LookupError as exc:
        raise NotFoundException(str(exc)) from exc
    except (RuntimeError, ValueError) as exc:
        raise ParamException(str(exc)) from exc
    except Exception as exc:
        raise DatabaseException("rename category failed") from exc


def list_payment_methods_service() -> list[dict]:
    try:
        return _normalize_dimension_rows(db_service.list_payment_methods_with_usage())
    except Exception as exc:
        raise DatabaseException("query payment methods failed") from exc


def create_payment_method_service(name: str) -> dict:
    try:
        return db_service.create_payment_method(name)
    except ValueError as exc:
        raise ParamException(str(exc)) from exc
    except Exception as exc:
        raise DatabaseException("create payment method failed") from exc


def rename_payment_method_service(payment_method_id: int, name: str) -> dict:
    try:
        return db_service.rename_payment_method(payment_method_id, name)
    except LookupError as exc:
        raise NotFoundException(str(exc)) from exc
    except ValueError as exc:
        raise ParamException(str(exc)) from exc
    except Exception as exc:
        raise DatabaseException("rename payment method failed") from exc


def delete_payment_method_service(payment_method_id: int) -> None:
    try:
        db_service.delete_payment_method_with_migration(payment_method_id)
    except LookupError as exc:
        raise NotFoundException(str(exc)) from exc
    except RuntimeError as exc:
        raise ParamException(str(exc)) from exc
    except Exception as exc:
        raise DatabaseException("delete payment method failed") from exc
