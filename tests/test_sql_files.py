"""
Tests for SQL query file integrity and syntax.
"""
from pathlib import Path
import sqlite3
import pytest

ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT / "sql"

EXPECTED_SQL_FILES = [
    "00_views.sql",
    "01_reconciliation.sql",
    "02_stuck_orders.sql",
    "03_delivery_kpis.sql",
    "04_seller_scorecard.sql",
    "05_customers_revenue.sql",
]


def test_sql_files_exist():
    """Verify all expected SQL files exist and are non-empty."""
    for filename in EXPECTED_SQL_FILES:
        file_path = SQL_DIR / filename
        assert file_path.exists(), f"Missing SQL file: {filename}"
        assert file_path.stat().st_size > 0, f"SQL file is empty: {filename}"


def test_sql_views_compilation():
    """
    Verify 00_views.sql compiles cleanly in SQLite against mock table schemas.
    """
    con = sqlite3.connect(":memory:")
    cur = con.cursor()

    # Create mock schema for base tables required by 00_views.sql
    cur.executescript("""
        CREATE TABLE orders (
            order_id TEXT PRIMARY KEY,
            customer_id TEXT,
            order_status TEXT,
            order_purchase_timestamp TEXT,
            order_approved_at TEXT,
            order_delivered_carrier_date TEXT,
            order_delivered_customer_date TEXT,
            order_estimated_delivery_date TEXT
        );
        CREATE TABLE order_items (
            order_id TEXT,
            order_item_id INTEGER,
            product_id TEXT,
            seller_id TEXT,
            shipping_limit_date TEXT,
            price REAL,
            freight_value REAL
        );
        CREATE TABLE payments (
            order_id TEXT,
            payment_sequential INTEGER,
            payment_type TEXT,
            payment_installments INTEGER,
            payment_value REAL
        );
        CREATE TABLE reviews (
            review_id TEXT,
            order_id TEXT,
            review_score INTEGER,
            review_comment_title TEXT,
            review_comment_message TEXT,
            review_creation_date TEXT,
            review_answer_timestamp TEXT
        );
        CREATE TABLE customers (
            customer_id TEXT,
            customer_unique_id TEXT,
            customer_zip_code_prefix TEXT,
            customer_city TEXT,
            customer_state TEXT
        );
        CREATE TABLE sellers (
            seller_id TEXT,
            seller_zip_code_prefix TEXT,
            seller_city TEXT,
            seller_state TEXT
        );
        CREATE TABLE products (
            product_id TEXT,
            product_category_name TEXT,
            product_weight_g REAL
        );
        CREATE TABLE category_translation (
            product_category_name TEXT,
            product_category_name_english TEXT
        );
    """)

    # Execute 00_views.sql
    views_sql = (SQL_DIR / "00_views.sql").read_text(encoding="utf-8")
    cur.executescript(views_sql)

    # Verify key views were created and can be queried
    views_to_test = [
        "v_params",
        "v_order_value",
        "v_order_payment",
        "v_primary_seller",
        "v_order_review",
        "v_delivered",
    ]
    for view_name in views_to_test:
        cur.execute(f"SELECT * FROM {view_name} LIMIT 0;")
        assert cur.description is not None, f"View {view_name} query failed."

    con.close()
