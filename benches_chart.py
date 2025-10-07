# benches_chart.py
from __future__ import annotations
from typing import Iterable
from io import BytesIO
import matplotlib
matplotlib.use("Agg")  # <- headless backend (no Tk)
import matplotlib.pyplot as plt

def make_strat_image(rows: Iterable[dict], title: str = "Intervals") -> bytes:
    """
    rows: iterable of dict-like with keys: bench, group, phase_tag, display_order, color
    Returns: PNG bytes for embedding in Flet Image (src_base64).
    """
    rows = list(rows)

    fig = plt.figure(figsize=(4.2, 5.5), dpi=110)
    ax = fig.add_axes([0.25, 0.08, 0.6, 0.84])

    if not rows:
        ax.text(0.5, 0.5, "No intervals found", ha="center", va="center")
        ax.axis("off")
    else:
        # Sort top->bottom
        rows.sort(key=lambda r: r.get("display_order", 0))
        n = len(rows)
        for i, r in enumerate(rows):
            y_top = n - i
            y_bottom = n - (i + 1)
            color = r.get("color", "#999999")
            ax.fill_between([0, 1], [y_bottom, y_bottom], [y_top, y_top],
                            color=color, alpha=0.9, edgecolor="black", linewidth=0.8)
            ax.text(0.5, (y_top + y_bottom) / 2,
                    r.get("bench", ""), ha="center", va="center",
                    fontsize=9, wrap=True, color="white")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, n)
        ax.set_xticks([]); ax.set_yticks([])
        for s in ("top","right","bottom","left"):
            ax.spines[s].set_visible(False)

    ax.set_title(title, fontsize=12)

    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()
