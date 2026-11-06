"""
Step 1 - Download the raw Olist Brazilian E-Commerce dataset.

Source: Olist's own public repository (the same data published on Kaggle as
"Brazilian E-Commerce Public Dataset by Olist", licence CC BY-NC-SA 4.0).
https://github.com/olist/work-at-olist-data

Usage:  python scripts/01_download_data.py
"""
from pathlib import Path
import urllib.request

BASE = "https://raw.githubusercontent.com/olist/work-at-olist-data/master/datasets"
FILES = [
    "olist_customers_dataset.csv",
    "olist_geolocation_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
    "product_category_name_translation.csv",
]

RAW = Path(__file__).resolve().parents[1] / "data" / "raw"


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        target = RAW / name
        if target.exists() and target.stat().st_size > 0:
            print(f"[skip] {name} already downloaded")
            continue
        print(f"[get ] {name}")
        urllib.request.urlretrieve(f"{BASE}/{name}", target)
    print(f"Done. Files saved in {RAW}")


if __name__ == "__main__":
    main()
