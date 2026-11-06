"""
Generate an animated demo GIF showing the sheets of the Excel Ops Command Center.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
IMG_DIR = ROOT / "images"
OUT_PATH = IMG_DIR / "excel_command_center_demo.gif"

SLIDES = [
    ("excel_dashboard.png", "Sheet 1/5: Operations Dashboard (KPI Tiles & Interactive Month Filter)"),
    ("excel_backlog_worklist.png", "Sheet 2/5: Backlog Worklist (1,729 Triage Orders with Status Dropdowns)"),
    ("excel_capacity_model.png", "Sheet 3/5: Capacity Model (Dynamic Headcount & 10-Day Clearing Schedule)"),
    ("excel_seller_risk.png", "Sheet 4/5: Seller Risk Matrix (Empirical Bayes Scoring & AM Allocation)"),
    ("excel_whatif.png", "Sheet 5/5: Delivery SLA What-If Model (Handoff Reduction Impact)"),
]

TARGET_W = 1200
TARGET_H = 750
NAV_H = 45


def make_frame(img_name: str, caption: str) -> Image.Image:
    src_path = IMG_DIR / img_name
    src = Image.open(src_path).convert("RGB")

    # Available space for screenshot
    avail_w = TARGET_W - 40
    avail_h = TARGET_H - NAV_H - 40

    # Scale to fit while preserving aspect ratio
    scale = min(avail_w / src.width, avail_h / src.height)
    new_w = int(src.width * scale)
    new_h = int(src.height * scale)
    resized_src = src.resize((new_w, new_h), Image.Resampling.LANCZOS)

    # Create canvas
    canvas = Image.new("RGB", (TARGET_W, TARGET_H), color=(248, 249, 250))
    draw = ImageDraw.Draw(canvas)

    # Top navigation header
    draw.rectangle([(0, 0), (TARGET_W, NAV_H)], fill=(55, 86, 35))  # Header green
    # Title / caption
    draw.text((20, 14), f"Olist Operations Command Center  |  {caption}", fill=(255, 255, 255))

    # Center image
    offset_x = 20 + (avail_w - new_w) // 2
    offset_y = NAV_H + 20 + (avail_h - new_h) // 2

    # Draw subtle border / shadow around image
    draw.rectangle(
        [(offset_x - 1, offset_y - 1), (offset_x + new_w + 1, offset_y + new_h + 1)],
        outline=(210, 215, 220),
        width=1,
    )
    canvas.paste(resized_src, (offset_x, offset_y))

    return canvas


def main():
    frames = []
    for img_name, caption in SLIDES:
        frame = make_frame(img_name, caption)
        frames.append(frame)

    # Save animated GIF (2.6 seconds per frame, loop forever)
    frames[0].save(
        OUT_PATH,
        save_all=True,
        append_images=frames[1:],
        duration=2600,
        loop=0,
        optimize=True,
    )
    print(f"Generated {OUT_PATH} successfully! Size: {OUT_PATH.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()

