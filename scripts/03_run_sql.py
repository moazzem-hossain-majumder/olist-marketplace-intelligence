"""
Step 3 - Run every SQL file in /sql against data/olist.db.

Each file is split into blocks marked with `-- name: <block_name>`.
* Blocks that create views (DDL) are executed.
* Blocks that are a SELECT / WITH query are executed and exported to
  data/processed/<block_name>.csv, so the Python notebooks and the Excel
  dashboard read exactly what SQL produced.

Usage:  python scripts/03_run_sql.py
"""
from pathlib import Path
import re
import sqlite3
import time
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "olist.db"
SQL_DIR = ROOT / "sql"
OUT = ROOT / "data" / "processed"

BLOCK = re.compile(r"^--\s*name:\s*(\w+)\s*$", re.MULTILINE)


def strip_comments(sql: str) -> str:
    return "\n".join(l for l in sql.splitlines() if not l.strip().startswith("--")).strip()


def blocks(text: str):
    parts = BLOCK.split(text)
    # parts = [preamble, name1, body1, name2, body2, ...]
    for i in range(1, len(parts), 2):
        yield parts[i], parts[i + 1]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB)
    for f in sorted(SQL_DIR.glob("*.sql")):
        print(f"\n=== {f.name}")
        for name, body in blocks(f.read_text(encoding="utf-8")):
            code = strip_comments(body)
            t0 = time.time()
            if re.match(r"^(SELECT|WITH)\b", code, re.IGNORECASE):
                df = pd.read_sql(code.rstrip(";"), con)
                df.to_csv(OUT / f"{name}.csv", index=False)
                print(f"  [query] {name:<36} {len(df):>7,} rows  {time.time()-t0:5.1f}s")
            else:
                con.executescript(code)
                print(f"  [ddl  ] {name:<36}            {time.time()-t0:5.1f}s")
    con.close()


if __name__ == "__main__":
    main()
