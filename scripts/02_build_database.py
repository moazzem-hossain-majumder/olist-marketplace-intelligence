"""
Step 2 - Load the raw CSVs into a local SQLite database (data/olist.db).

* Tables keep the raw column names, so every SQL file in /sql can be read
  against the original Kaggle data dictionary.
* Geolocation has ~1M rows with many duplicates per zip prefix, so we also
  build a de-duplicated `geo_zip` table (mean lat/lng per zip prefix).
* Indexes are added on the join keys used across the analyses.

Usage:  python scripts/02_build_database.py
"""
from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DB = ROOT / "data" / "olist.db"

TABLES = {
    "customers": "olist_customers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}

# zip prefixes are codes, not numbers: keep leading zeros
STR_COLS = {
    "customer_zip_code_prefix": str,
    "seller_zip_code_prefix": str,
    "geolocation_zip_code_prefix": str,
}

INDEXES = [
    "CREATE INDEX IF NOT EXISTS ix_orders_id ON orders(order_id)",
    "CREATE INDEX IF NOT EXISTS ix_orders_cust ON orders(customer_id)",
    "CREATE INDEX IF NOT EXISTS ix_items_order ON order_items(order_id)",
    "CREATE INDEX IF NOT EXISTS ix_items_seller ON order_items(seller_id)",
    "CREATE INDEX IF NOT EXISTS ix_items_product ON order_items(product_id)",
    "CREATE INDEX IF NOT EXISTS ix_pay_order ON payments(order_id)",
    "CREATE INDEX IF NOT EXISTS ix_rev_order ON reviews(order_id)",
    "CREATE INDEX IF NOT EXISTS ix_cust_id ON customers(customer_id)",
    "CREATE INDEX IF NOT EXISTS ix_seller_id ON sellers(seller_id)",
    "CREATE INDEX IF NOT EXISTS ix_prod_id ON products(product_id)",
    "CREATE INDEX IF NOT EXISTS ix_geo_zip ON geo_zip(zip_prefix)",
]


def main() -> None:
    if DB.exists():
        DB.unlink()
    con = sqlite3.connect(DB)
    for table, file in TABLES.items():
        df = pd.read_csv(RAW / file, dtype=STR_COLS, encoding="utf-8-sig")
        for c in df.columns:
            if c.endswith("zip_code_prefix"):
                df[c] = df[c].str.zfill(5)
        df.to_sql(table, con, index=False)
        print(f"{table:<22} {len(df):>9,} rows")

    geo = pd.read_sql("SELECT * FROM geolocation", con)
    geo_zip = (
        geo.groupby("geolocation_zip_code_prefix", as_index=False)
        .agg(lat=("geolocation_lat", "mean"), lng=("geolocation_lng", "mean"))
        .rename(columns={"geolocation_zip_code_prefix": "zip_prefix"})
    )
    geo_zip.to_sql("geo_zip", con, index=False)
    print(f"{'geo_zip (dedup)':<22} {len(geo_zip):>9,} rows")

    for stmt in INDEXES:
        con.execute(stmt)
    con.commit()
    con.close()
    print(f"Database written to {DB}")


if __name__ == "__main__":
    main()
