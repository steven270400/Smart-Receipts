import json
import os
from contextlib import contextmanager
from datetime import datetime

import pymysql
from pymysql.cursors import DictCursor
from pymysql.err import OperationalError

DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "1234")
DB_NAME = os.getenv("DB_NAME", "smartreceipts")

DEFAULT_CATEGORY = "其他"
DEFAULT_PAYMENT_METHOD = "其他"

DEFAULT_CATEGORIES = ["餐饮", "交通", "生活缴费", "购物", "其他"]
DEFAULT_PAYMENT_METHODS = ["支付宝", "微信", "余额", "银行卡", "现金", "其他"]


@contextmanager
def get_server_connection():
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        charset="utf8mb4",
        autocommit=True,
        cursorclass=DictCursor,
    )
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def get_connection():
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
        autocommit=False,
        cursorclass=DictCursor,
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_server_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS categories (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    name VARCHAR(100) NOT NULL UNIQUE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS payment_methods (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    name VARCHAR(100) NOT NULL UNIQUE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS receipts (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    merchant VARCHAR(255) NOT NULL,
                    amount DECIMAL(12,2) NOT NULL,
                    transaction_time DATETIME NOT NULL,
                    category_id BIGINT NOT NULL,
                    payment_method_id BIGINT NOT NULL,
                    notes TEXT NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    is_deleted TINYINT(1) NOT NULL DEFAULT 0,
                    CONSTRAINT fk_receipts_category FOREIGN KEY (category_id) REFERENCES categories(id),
                    CONSTRAINT fk_receipts_payment_method FOREIGN KEY (payment_method_id) REFERENCES payment_methods(id)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS receipt_sources (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    receipt_id BIGINT NOT NULL UNIQUE,
                    source_type ENUM('manual', 'ocr') NOT NULL,
                    file_name VARCHAR(255) NULL,
                    raw_text LONGTEXT NULL,
                    extracted_json JSON NULL,
                    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_sources_receipt FOREIGN KEY (receipt_id) REFERENCES receipts(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
            try:
                cursor.execute(
                    "CREATE INDEX idx_receipts_tci ON receipts(transaction_time, category_id, is_deleted)"
                )
            except OperationalError as exc:
                if exc.args and exc.args[0] != 1061:
                    raise

            try:
                cursor.execute("CREATE INDEX idx_receipts_merchant ON receipts(merchant)")
            except OperationalError as exc:
                if exc.args and exc.args[0] != 1061:
                    raise

    _seed_dimensions()


def _seed_dimensions():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            for name in DEFAULT_CATEGORIES:
                cursor.execute(
                    "INSERT IGNORE INTO categories (name) VALUES (%s)",
                    (name,),
                )
            for name in DEFAULT_PAYMENT_METHODS:
                cursor.execute(
                    "INSERT IGNORE INTO payment_methods (name) VALUES (%s)",
                    (name,),
                )


def _normalize_transaction_time(data: dict) -> datetime:
    value = data.get("transaction_time")
    if isinstance(value, datetime):
        return value

    if isinstance(value, str):
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                parsed = datetime.strptime(value, fmt)
                if fmt == "%Y-%m-%d":
                    return datetime(parsed.year, parsed.month, parsed.day, 0, 0, 0)
                return parsed
            except ValueError:
                continue

    return datetime.now()


def _get_or_create_category_id(cursor, name: str) -> int:
    final_name = (name or DEFAULT_CATEGORY).strip() or DEFAULT_CATEGORY
    cursor.execute("INSERT IGNORE INTO categories (name) VALUES (%s)", (final_name,))
    cursor.execute("SELECT id FROM categories WHERE name = %s", (final_name,))
    return cursor.fetchone()["id"]


def _get_or_create_payment_method_id(cursor, name: str) -> int:
    final_name = (name or DEFAULT_PAYMENT_METHOD).strip() or DEFAULT_PAYMENT_METHOD
    cursor.execute("INSERT IGNORE INTO payment_methods (name) VALUES (%s)", (final_name,))
    cursor.execute("SELECT id FROM payment_methods WHERE name = %s", (final_name,))
    return cursor.fetchone()["id"]


def save_receipt(data):
    merchant = (data.get("merchant") or "").strip() or "未知商家"
    amount = float(data.get("amount", 0))
    transaction_time = _normalize_transaction_time(data)
    notes = data.get("notes")

    source_type = data.get("source_type", "ocr")
    if source_type not in {"manual", "ocr"}:
        source_type = "manual"

    with get_connection() as conn:
        with conn.cursor() as cursor:
            category_id = _get_or_create_category_id(cursor, data.get("category"))
            payment_method_id = _get_or_create_payment_method_id(cursor, data.get("payment_method"))

            cursor.execute(
                """
                INSERT INTO receipts (
                    merchant, amount, transaction_time, category_id, payment_method_id, notes
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (merchant, amount, transaction_time, category_id, payment_method_id, notes),
            )
            receipt_id = cursor.lastrowid

            raw_text = data.get("raw_text")
            if isinstance(raw_text, list):
                raw_text = "\n".join(str(item) for item in raw_text)

            extracted_json = data.get("extracted_json")
            if isinstance(extracted_json, (dict, list)):
                extracted_json = json.dumps(extracted_json, ensure_ascii=False)

            cursor.execute(
                """
                INSERT INTO receipt_sources (
                    receipt_id, source_type, file_name, raw_text, extracted_json
                ) VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    receipt_id,
                    source_type,
                    data.get("file_name"),
                    raw_text,
                    extracted_json,
                ),
            )


def get_receipts():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    r.id,
                    r.merchant,
                    CAST(r.amount AS DOUBLE) AS amount,
                    c.name AS category,
                    DATE_FORMAT(r.transaction_time, '%Y-%m-%d %H:%i:%s') AS transaction_time,
                    pm.name AS payment_method,
                    r.notes,
                    rs.source_type,
                    DATE_FORMAT(r.created_at, '%Y-%m-%d %H:%i:%s') AS created_at,
                    DATE_FORMAT(r.updated_at, '%Y-%m-%d %H:%i:%s') AS updated_at
                FROM receipts r
                INNER JOIN categories c ON c.id = r.category_id
                INNER JOIN payment_methods pm ON pm.id = r.payment_method_id
                LEFT JOIN receipt_sources rs ON rs.receipt_id = r.id
                WHERE r.is_deleted = 0
                ORDER BY r.id DESC
                """
            )
            return cursor.fetchall()


def get_statistics():
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    COALESCE(SUM(amount), 0) AS total_amount,
                    COUNT(*) AS total_records
                FROM receipts
                WHERE is_deleted = 0
                """
            )
            totals = cursor.fetchone()

            cursor.execute(
                """
                SELECT c.name AS category, COALESCE(SUM(r.amount), 0) AS amount
                FROM receipts r
                INNER JOIN categories c ON c.id = r.category_id
                WHERE r.is_deleted = 0
                GROUP BY c.name
                ORDER BY c.name
                """
            )
            category_rows = cursor.fetchall()

            cursor.execute(
                """
                SELECT
                    DATE_FORMAT(transaction_time, '%Y-%m') AS month,
                    COALESCE(SUM(amount), 0) AS amount
                FROM receipts
                WHERE is_deleted = 0
                GROUP BY DATE_FORMAT(transaction_time, '%Y-%m')
                ORDER BY month
                """
            )
            monthly_rows = cursor.fetchall()

            cursor.execute(
                """
                SELECT
                    r.id,
                    r.merchant,
                    CAST(r.amount AS DOUBLE) AS amount,
                    c.name AS category,
                    DATE_FORMAT(r.transaction_time, '%Y-%m-%d %H:%i:%s') AS transaction_time
                FROM receipts r
                INNER JOIN categories c ON c.id = r.category_id
                WHERE r.is_deleted = 0
                ORDER BY r.amount DESC, r.id DESC
                LIMIT 1
                """
            )
            max_expense = cursor.fetchone()

    category_stats = {}
    for row in category_rows:
        category_stats[row["category"] or DEFAULT_CATEGORY] = float(row["amount"] or 0)

    return {
        "total_amount": float(totals["total_amount"] or 0),
        "total_records": int(totals["total_records"] or 0),
        "category_stats": category_stats,
        "monthly_trend": [
            {"month": row["month"], "amount": float(row["amount"] or 0)} for row in monthly_rows
        ],
        "max_expense": max_expense,
    }

def _parse_transaction_time(value):
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        text = value.strip()
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                parsed = datetime.strptime(text, fmt)
                if fmt == "%Y-%m-%d":
                    return datetime(parsed.year, parsed.month, parsed.day, 0, 0, 0)
                return parsed
            except ValueError:
                continue
    raise ValueError("时间格式错误，支持 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS")


def get_category_id_by_name(name):
    if not name:
        return None
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM categories WHERE name=%s LIMIT 1", (name,))
            row = cursor.fetchone()
            return row["id"] if row else None


def get_payment_method_id_by_name(name):
    if not name:
        return None
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM payment_methods WHERE name=%s LIMIT 1", (name,))
            row = cursor.fetchone()
            return row["id"] if row else None


def _exists_category(cursor, category_id: int) -> bool:
    cursor.execute("SELECT 1 FROM categories WHERE id=%s LIMIT 1", (category_id,))
    return cursor.fetchone() is not None


def _exists_payment_method(cursor, payment_method_id: int) -> bool:
    cursor.execute("SELECT 1 FROM payment_methods WHERE id=%s LIMIT 1", (payment_method_id,))
    return cursor.fetchone() is not None


def list_receipts(
    page: int = 1,
    size: int = 1000,
    merchant: str | None = None,
    keyword: str | None = None,
    category_id: int | None = None,
    payment_method_id: int | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
):
    page = max(1, int(page or 1))
    size = max(1, min(1000, int(size or 1000)))
    offset = (page - 1) * size

    where = ["r.is_deleted = 0"]
    params = []

    if merchant:
        where.append("r.merchant LIKE %s")
        params.append(f"%{merchant.strip()}%")
    if keyword:
        kw = keyword.strip()
        if kw:
            like_kw = f"%{kw}%"
            or_parts = ["r.merchant LIKE %s", "c.name LIKE %s", "pm.name LIKE %s"]
            or_params = [like_kw, like_kw, like_kw]
            try:
                day = datetime.strptime(kw, "%Y-%m-%d").date()
            except ValueError:
                day = None
            if day:
                # Match the whole day. This is robust even when the DB doesn't store microseconds.
                or_parts.append("DATE(r.transaction_time) = %s")
                or_params.append(day.strftime("%Y-%m-%d"))
            where.append("(" + " OR ".join(or_parts) + ")")
            params.extend(or_params)
    if category_id is not None:
        where.append("r.category_id = %s")
        params.append(int(category_id))
    if payment_method_id is not None:
        where.append("r.payment_method_id = %s")
        params.append(int(payment_method_id))
    if start_time:
        where.append("r.transaction_time >= %s")
        params.append(_parse_transaction_time(start_time))
    if end_time:
        where.append("r.transaction_time <= %s")
        params.append(_parse_transaction_time(end_time))

    where_sql = " AND ".join(where)
    from_join_sql = """
        FROM receipts r
        INNER JOIN categories c ON c.id = r.category_id
        INNER JOIN payment_methods pm ON pm.id = r.payment_method_id
    """

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"SELECT COUNT(*) AS total {from_join_sql} WHERE {where_sql}",
                params,
            )
            total = int(cursor.fetchone()["total"])

            data_sql = f"""
                SELECT
                    r.id,
                    r.merchant,
                    CAST(r.amount AS DOUBLE) AS amount,
                    DATE_FORMAT(r.transaction_time, '%%Y-%%m-%%d %%H:%%i:%%s') AS transaction_time,
                    r.category_id,
                    c.name AS category,
                    r.payment_method_id,
                    pm.name AS payment_method,
                    r.notes,
                    DATE_FORMAT(r.created_at, '%%Y-%%m-%%d %%H:%%i:%%s') AS created_at,
                    DATE_FORMAT(r.updated_at, '%%Y-%%m-%%d %%H:%%i:%%s') AS updated_at
                {from_join_sql}
                WHERE {where_sql}
                ORDER BY r.transaction_time DESC, r.id DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(data_sql, params + [size, offset])
            rows = cursor.fetchall()

    return {
        "data": rows,
        "pagination": {
            "page": page,
            "size": size,
            "total": total,
        },
    }


def get_receipt_by_id(receipt_id: int, include_deleted: bool = False):
    where_deleted = "" if include_deleted else "AND r.is_deleted = 0"
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT
                    r.id,
                    r.merchant,
                    CAST(r.amount AS DOUBLE) AS amount,
                    DATE_FORMAT(r.transaction_time, '%%Y-%%m-%%d %%H:%%i:%%s') AS transaction_time,
                    r.category_id,
                    c.name AS category,
                    r.payment_method_id,
                    pm.name AS payment_method,
                    r.notes,
                    DATE_FORMAT(r.created_at, '%%Y-%%m-%%d %%H:%%i:%%s') AS created_at,
                    DATE_FORMAT(r.updated_at, '%%Y-%%m-%%d %%H:%%i:%%s') AS updated_at,
                    r.is_deleted
                FROM receipts r
                INNER JOIN categories c ON c.id = r.category_id
                INNER JOIN payment_methods pm ON pm.id = r.payment_method_id
                WHERE r.id = %s {where_deleted}
                LIMIT 1
                """,
                (int(receipt_id),),
            )
            return cursor.fetchone()


def create_manual_receipt(payload: dict):
    merchant = (payload.get("merchant") or "").strip()
    if not merchant:
        raise ValueError("商家名称不能为空")

    try:
        amount = float(payload.get("amount"))
    except (TypeError, ValueError):
        raise ValueError("金额格式错误")

    transaction_input = payload.get("transaction_time")
    transaction_time = _parse_transaction_time(transaction_input)

    category_id = payload.get("category_id")
    payment_method_id = payload.get("payment_method_id")
    notes = payload.get("notes")

    with get_connection() as conn:
        with conn.cursor() as cursor:
            if not _exists_category(cursor, int(category_id)):
                raise ValueError("分类不存在")
            if not _exists_payment_method(cursor, int(payment_method_id)):
                raise ValueError("支付方式不存在")

            cursor.execute(
                """
                INSERT INTO receipts (
                    merchant, amount, transaction_time, category_id, payment_method_id, notes
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (merchant, amount, transaction_time, int(category_id), int(payment_method_id), notes),
            )
            receipt_id = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO receipt_sources (
                    receipt_id, source_type, file_name, raw_text, extracted_json
                ) VALUES (%s, 'manual', NULL, NULL, NULL)
                """,
                (receipt_id,),
            )

    return get_receipt_by_id(receipt_id)


def update_receipt_by_id(receipt_id: int, payload: dict):
    current = get_receipt_by_id(receipt_id, include_deleted=True)
    if not current:
        raise LookupError("账单不存在")
    if int(current["is_deleted"]) == 1:
        raise RuntimeError("账单已删除")

    merchant = (payload.get("merchant") or "").strip()
    if not merchant:
        raise ValueError("商家名称不能为空")

    try:
        amount = float(payload.get("amount"))
    except (TypeError, ValueError):
        raise ValueError("金额格式错误")

    transaction_input = payload.get("transaction_time")
    transaction_time = _parse_transaction_time(transaction_input)

    category_id = payload.get("category_id")
    payment_method_id = payload.get("payment_method_id")
    notes = payload.get("notes")

    with get_connection() as conn:
        with conn.cursor() as cursor:
            if not _exists_category(cursor, int(category_id)):
                raise ValueError("分类不存在")
            if not _exists_payment_method(cursor, int(payment_method_id)):
                raise ValueError("支付方式不存在")

            cursor.execute(
                """
                UPDATE receipts
                SET
                    merchant=%s,
                    amount=%s,
                    transaction_time=%s,
                    category_id=%s,
                    payment_method_id=%s,
                    notes=%s,
                    updated_at=NOW()
                WHERE id=%s AND is_deleted=0
                """,
                (
                    merchant,
                    amount,
                    transaction_time,
                    int(category_id),
                    int(payment_method_id),
                    notes,
                    int(receipt_id),
                ),
            )

    return get_receipt_by_id(receipt_id)


def soft_delete_receipt(receipt_id: int):
    current = get_receipt_by_id(receipt_id, include_deleted=True)
    if not current:
        raise LookupError("账单不存在")
    if int(current["is_deleted"]) == 1:
        raise RuntimeError("账单已删除")

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE receipts
                SET is_deleted=1, updated_at=NOW()
                WHERE id=%s AND is_deleted=0
                """,
                (int(receipt_id),),
            )

