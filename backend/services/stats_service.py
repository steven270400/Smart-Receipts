from backend import db_service
from backend.core.exceptions import DatabaseException


def get_statistics_service() -> dict:
    try:
        return db_service.get_statistics()
    except Exception as exc:
        raise DatabaseException("query statistics failed") from exc
