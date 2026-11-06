"""
One command to rebuild the whole project from raw data:

    python run_all.py              # full pipeline
    python run_all.py --skip-download

1. download raw CSVs        scripts/01_download_data.py
2. build SQLite database    scripts/02_build_database.py
3. run all SQL             scripts/03_run_sql.py          -> data/processed/*.csv
4. execute notebooks       notebooks/0*.ipynb             -> images/*.png, more CSVs
5. build Excel workbook    scripts/04_build_excel.py      -> excel/*.xlsx
6. SQL screenshots         scripts/05_sql_screenshots.py  -> images/sql_*.png
7. Excel screenshots       scripts/06_excel_screenshots.py (optional, needs LibreOffice)
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = sys.executable


def run(cmd, cwd=ROOT):
    print("\n>>", " ".join(str(c) for c in cmd), flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)


def main() -> None:
    if "--skip-download" not in sys.argv:
        run([PY, "scripts/01_download_data.py"])
    run([PY, "scripts/02_build_database.py"])
    run([PY, "scripts/03_run_sql.py"])
    for nb in sorted((ROOT / "notebooks").glob("0*.ipynb")):
        run([PY, "-m", "jupyter", "nbconvert", "--to", "notebook", "--execute", "--inplace",
             "--ExecutePreprocessor.timeout=1200", nb.name], cwd=ROOT / "notebooks")
    run([PY, "scripts/04_build_excel.py"])
    run([PY, "scripts/05_sql_screenshots.py"])
    if shutil.which("soffice") and shutil.which("pdftoppm"):
        run([PY, "scripts/06_excel_screenshots.py"])
    else:
        print("\n(LibreOffice/poppler not found - skipping Excel screenshots)")
    print("\nDone. Open excel/Olist_Ops_Command_Center.xlsx and the notebooks in /notebooks.")


if __name__ == "__main__":
    main()
