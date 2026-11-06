"""
Step 7 (optional) - Render PNG screenshots of the Excel workbook for the README.
Needs LibreOffice (`soffice`) and poppler (`pdftoppm`) on PATH.

Usage:  python scripts/06_excel_screenshots.py
"""
from pathlib import Path
import subprocess
import tempfile
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
XLSX = ROOT / "excel" / "Olist_Ops_Command_Center.xlsx"
IMG = ROOT / "images"
# PDF page number -> screenshot name (page order = sheet order)
PAGES = {2: "excel_dashboard", 4: "excel_recon_checks", 5: "excel_backlog_worklist",
         6: "excel_seller_risk", 7: "excel_capacity_model", 8: "excel_whatif"}


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", str(tmp), str(XLSX)],
                       check=True, capture_output=True, timeout=300)
        subprocess.run(["pdftoppm", "-r", "160", "-png", str(tmp / (XLSX.stem + ".pdf")), str(tmp / "pg")], check=True)
        for page, name in PAGES.items():
            src = next(tmp.glob(f"pg-*{page}.png"))
            im = Image.open(src).convert("RGB")
            bbox = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
            im = im.crop((max(bbox[0] - 30, 0), max(bbox[1] - 30, 0),
                          min(bbox[2] + 30, im.width), min(bbox[3] + 30, im.height)))
            im.save(IMG / f"{name}.png", optimize=True)
            print(f"images/{name}.png")


if __name__ == "__main__":
    main()
