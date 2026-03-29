import sqlite3
from contextlib import contextmanager

DB_NAME = "receipt.db"


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                merchant TEXT,
                amount REAL,
                category TEXT,
                date TEXT,
                payment_method TEXT
            )
            """
        )
        conn.commit()


def save_receipt(data):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO receipts (merchant, amount, category, date, payment_method)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                data.get("merchant"),
                data.get("amount"),
                data.get("category"),
                data.get("date"),
                data.get("payment_method"),
            ),
        )
        conn.commit()


def get_receipts():
    with get_connection() as conn:
        cursor = conn.execute(
            """
            SELECT id, merchant, amount, category, date, payment_method
            FROM receipts
            ORDER BY id DESC
            """
        )
        rows = cursor.fetchall()

    return [dict(row) for row in rows]


def get_statistics():
    with get_connection() as conn:
        total_amount = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM receipts").fetchone()[0]
        total_records = conn.execute("SELECT COUNT(*) FROM receipts").fetchone()[0]

        cursor = conn.execute(
            """
            SELECT category, COALESCE(SUM(amount), 0) AS amount
            FROM receipts
            GROUP BY category
            ORDER BY category
            """
        )
        rows = cursor.fetchall()

    category_stats = {}
    for row in rows:
        category = row["category"] if row["category"] else "其他"
        category_stats[category] = row["amount"]

    return {
        "total_amount": total_amount,
        "total_records": total_records,
        "category_stats": category_stats,
    }
