"""
2D top-view configuration drawing for SWIFT using matplotlib.
"""
import io
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

CONFIG_ANGLES = {
    "Quad X": [45, 135, 225, 315],
    "Quad +": [0, 90, 180, 270],
    "Hex":    [0, 60, 120, 180, 240, 300],
    "Octo":   [0, 45, 90, 135, 180, 225, 270, 315],
}

_SPIN = ["CW", "CCW", "CW", "CCW", "CW", "CCW", "CW", "CCW"]


def draw_top_view(L_arm_m: float, D_prop_m: float, n_motors: int,
                  config_name: str, clearance_ok: bool = True,
                  c_margin_m: float = 0.010) -> plt.Figure:
    """Generate and return a matplotlib Figure of the top-view layout."""
    angles_deg = CONFIG_ANGLES.get(config_name, CONFIG_ANGLES["Quad X"])[:n_motors]
    spins      = _SPIN[:n_motors]
    angles_rad = [np.deg2rad(a) for a in angles_deg]

    fig, ax = plt.subplots(figsize=(7, 7), dpi=120)
    ax.set_facecolor("#f9fafb")
    fig.patch.set_facecolor("#ffffff")

    prop_color = "#16a34a" if clearance_ok else "#dc2626"

    mxs, mys = [], []
    for i, (theta, spin) in enumerate(zip(angles_rad, spins)):
        mx = L_arm_m * np.cos(theta)
        my = L_arm_m * np.sin(theta)
        mxs.append(mx); mys.append(my)

        # Arm
        ax.plot([0, mx], [0, my], color="#374151", lw=2.5,
                solid_capstyle="round", zorder=2)

        # Propeller disc
        circ = plt.Circle((mx, my), D_prop_m / 2.0,
                           facecolor=prop_color + "18",
                           edgecolor=prop_color, lw=1.8, zorder=3)
        ax.add_patch(circ)

        # Motor dot
        dot = plt.Circle((mx, my), L_arm_m * 0.028,
                          color="#d97706", zorder=5)
        ax.add_patch(dot)

        # Spin label
        off = L_arm_m * 0.20
        ax.text(mx + off * np.cos(theta), my + off * np.sin(theta),
                spin, fontsize=8, color="#6b7280", ha="center",
                va="center", zorder=6)

        # Motor number
        ax.text(mx - off * 0.5 * np.cos(theta),
                my - off * 0.5 * np.sin(theta),
                f"M{i+1}", fontsize=7, color="#374151",
                ha="center", va="center", zorder=6)

    # Centre body
    body_r = min(L_arm_m * 0.10, 0.035)
    ax.add_patch(plt.Circle((0, 0), body_r, color="#d97706", zorder=6))

    # L_arm annotation on first arm
    theta0 = angles_rad[0]
    ax.annotate(
        "", xy=(mxs[0] * 0.94, mys[0] * 0.94),
        xytext=(body_r * 1.5 * np.cos(theta0), body_r * 1.5 * np.sin(theta0)),
        arrowprops=dict(arrowstyle="<->", color="#d97706", lw=1.5),
    )
    perp = theta0 + np.pi / 2
    lx = L_arm_m / 2 * np.cos(theta0) + L_arm_m * 0.09 * np.cos(perp)
    ly = L_arm_m / 2 * np.sin(theta0) + L_arm_m * 0.09 * np.sin(perp)
    ax.text(lx, ly, f"L = {L_arm_m*1000:.0f} mm", fontsize=9,
            color="#d97706", ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.25", fc="white",
                      ec="#d97706", alpha=0.85))

    # D_prop label on first propeller
    ax.annotate("", xy=(mxs[0] + D_prop_m / 2, mys[0]),
                xytext=(mxs[0], mys[0]),
                arrowprops=dict(arrowstyle="->", color=prop_color, lw=1.2))
    ax.text(mxs[0] + D_prop_m / 2 + L_arm_m * 0.05, mys[0],
            f"D = {D_prop_m*1000:.0f} mm",
            fontsize=8, color=prop_color, va="center")

    # Total span
    span = 2 * L_arm_m + D_prop_m
    sy   = -(L_arm_m + D_prop_m / 2) * 1.20
    ax.annotate("", xy=(span / 2, sy), xytext=(-span / 2, sy),
                arrowprops=dict(arrowstyle="<->", color="#374151", lw=1.5))
    ax.text(0, sy - L_arm_m * 0.07, f"Span = {span*1000:.0f} mm",
            ha="center", fontsize=10, color="#374151",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#e5e7eb"))

    ax.set_aspect("equal")
    ax.grid(False)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color("#e5e7eb")
    ax.tick_params(colors="#6b7280", labelsize=8)
    ax.set_xlabel("x [m]", color="#6b7280", fontsize=9)
    ax.set_ylabel("y [m]", color="#6b7280", fontsize=9)
    ax.set_title(f"SWIFT — {config_name} Top View",
                 fontsize=12, color="#1a1a1a", fontweight="bold", pad=12)

    pad = (L_arm_m + D_prop_m / 2) * 1.40
    ax.set_xlim(-pad, pad)
    ax.set_ylim(-pad * 1.25, pad)
    plt.tight_layout()
    return fig


def fig_to_png_bytes(fig: plt.Figure) -> bytes:
    """Convert a matplotlib Figure to PNG bytes for download."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150,
                bbox_inches="tight", facecolor="white")
    buf.seek(0)
    return buf.read()
