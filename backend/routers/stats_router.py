from fastapi import APIRouter

from backend.core.exceptions import DatabaseException
from backend.core.response import success_response
from backend.services.stats_service import get_statistics_service

router = APIRouter(tags=["statistics"])


@router.get("/statistics")
def statistics():
    try:
        data = get_statistics_service()
        return success_response(data=data)
    except DatabaseException:
        raise
