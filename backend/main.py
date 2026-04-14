import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.error_handlers import register_error_handlers
from backend.core.response import success_response
from backend.db_service import init_db
from backend.routers.ocr_router import router as ocr_router
from backend.routers.receipt_router import router as receipt_router
from backend.routers.stats_router import router as stats_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

app = FastAPI()

if os.getenv("SKIP_DB_INIT", "").strip().lower() not in {"1", "true", "yes", "on"}:
    init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)


@app.get("/test")
def test():
    return success_response(data={"status": "ok"})


app.include_router(receipt_router)
app.include_router(stats_router)
app.include_router(ocr_router)
