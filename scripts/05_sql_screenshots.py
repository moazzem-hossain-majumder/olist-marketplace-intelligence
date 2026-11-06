"""
Step 6 - Render "terminal" screenshots of key SQL queries and their real output
(images/sql_*.png), so the README can show the SQL work without anyone running it.

Usage:  python scripts/05_sql_screenshots.py
"""
from pathlib import Path
import re
import sqlite3
import textwrap
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "olist.db"
IMG = ROOT / "images"

BG, FG, DIM, KEY, OK = "#282c34", "#dcdfe4", "#7f848e", "#e5c07b", "#98c379"
KEYWORDS = r"\b(SELECT|FROM|WHERE|GROUP BY|ORDER BY|JOIN|LEFT JOIN|ON|AS|CASE|WHEN|THEN|ELSE|END|WITH|SUM|COUNT|AVG|ROUND|HAVING|AND|OVER|PARTITION BY|ROW_NUMBER|DESC|LIMIT)\b"


def render(name: str, title: str, sql: str, max_rows: int = 12) -> None:
    con = sqlite3.connect(DB)
    df = pd.read_sql(sql, con).head(max_rows)
    con.close()
    sql_lines = textwrap.dedent(sql).strip().splitlines()
    table = df.to_string(index=False, max_colwidth=34).splitlines()
    lines = [("$ sqlite3 data/olist.db   -- " + title, DIM), ("", FG)]
    lines += [("sqlite> " + l if i == 0 else "   ...> " + l, KEY if re.search(KEYWORDS, l) else FG)
              for i, l in enumerate(sql_lines)]
    lines += [("", FG)] + [(l, OK if i == 0 else FG) for i, l in enumerate(table)]
    lines += [("", FG), (f"-- {len(df)} rows shown", DIM)]
    width = max(len(l) for l, _ in lines)
    fig = plt.figure(figsize=(max(8, width * 0.083), 0.205 * len(lines) + 0.6))
    fig.patch.set_facecolor(BG)
    for i, (l, c) in enumerate(lines):
        fig.text(0.02, 1 - (i + 1.2) / (len(lines) + 1.6), l, family="DejaVu Sans Mono", fontsize=9.5, color=c, va="top")
    fig.savefig(IMG / f"{name}.png", dpi=150, facecolor=BG)
    plt.close(fig)
    print(f"images/{name}.png")


if __name__ == "__main__":
    render("sql_reconciliation_summary", "Problem 1: reconciliation summary", """
        SELECT check_id, COUNT(*) AS orders_failing,
               ROUND(SUM(COALESCE(amount_at_stake, 0)), 0) AS brl_at_stake
        FROM v_recon_exceptions
        GROUP BY check_id
        ORDER BY brl_at_stake DESC;""")
    render("sql_late_vs_handoff", "Problem 3: seller handoff vs customer lateness", """
        SELECT seller_late_handoff,
               COUNT(*)                            AS orders,
               ROUND(AVG(is_late) * 100, 2)        AS customer_late_pct,
               ROUND(AVG(review_score), 2)         AS avg_review,
               ROUND(AVG(seller_handling_days), 2) AS handling_days,
               ROUND(AVG(carrier_transit_days), 2) AS transit_days
        FROM v_delivered
        GROUP BY seller_late_handoff;""")
    render("sql_stuck_backlog", "Problem 2: stuck-order backlog by bucket", """
        SELECT bucket, COUNT(*) AS orders,
               ROUND(SUM(order_value), 0) AS value_brl,
               ROUND(AVG(age_days), 0)    AS avg_age_days,
               COUNT(DISTINCT seller_id)  AS sellers
        FROM v_stuck_orders
        GROUP BY bucket
        ORDER BY bucket;""")
