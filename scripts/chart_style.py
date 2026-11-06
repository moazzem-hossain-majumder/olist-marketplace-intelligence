"""Common matplotlib settings for the charts in /images."""
from pathlib import Path
import matplotlib as mpl
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
IMG = ROOT / "images"

# colours I picked for this project
GREEN = "#3b7d4f"
ORANGE = "#e07a3f"
MUSTARD = "#e3b23c"
PLUM = "#8e5572"
BRICK = "#c44536"
SAGE = "#9bbf8a"
SAND = "#d9c9a8"
GREY = "#8c8c8c"
DARK = "#333333"
GRIDC = "#e5e5e5"


def apply() -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    mpl.rcParams.update({
        "figure.dpi": 110, "savefig.dpi": 150,
        "font.size": 10, "axes.titlesize": 12, "axes.titleweight": "bold",
        "axes.titlepad": 10, "axes.labelcolor": DARK, "text.color": DARK,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.edgecolor": "#bbbbbb", "grid.color": GRIDC,
        "legend.frameon": False, "legend.fontsize": 9,
    })


def save(fig, name: str) -> Path:
    IMG.mkdir(exist_ok=True)
    path = IMG / f"{name}.png"
    fig.savefig(path, bbox_inches="tight", pad_inches=0.2, facecolor="white")
    plt.close(fig)
    return path
