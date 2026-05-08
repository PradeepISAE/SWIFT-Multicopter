"""
2D top-view layout drawing + aerodynamic reference areas — SWIFT Resizing Phase.

S_top   = projected top area  (drag reference for climb/hover)
S_front = projected frontal area (drag reference for cruise)
"""
import io
import numpy as np
import matplotlib.pyplot as plt

CONFIG_ANGLES = {
    "Quad X":  [45, 135, 225, 315],
    "Quad +":  [0, 90, 180, 270],
    "Hex":     [0, 60, 120, 180, 240, 300],
    "Octo":    [0, 45, 90, 135, 180, 225, 270, 315],
}

_SPIN = ["CW", "CCW", "CW", "CCW", "CW", "CCW", "CW", "CCW"]


def compute_reference_areas(L_arm_m: float, D_prop_m: float,
                             n_motors: int, config_name: str,
                             body_diameter_m: float,
                             d_out_m: float) -> tuple:
    """Compute aerodynamic reference areas.

    S_top:   n × π×(D/2)²  +  n × L_arm × d_out  +  π×(body_d/2)²
    S_front: n × π×(D/2)²×|sin(θ_mean)| + n×L_arm×d_out×|cos(θ_mean)| + π×(body_d/2)²
    Returns (S_top [m²], S_front [m²]).
    """
    angles_deg = CONFIG_ANGLES.get(config_name, CONFIG_ANGLES["Quad X"])[:n_motors]
    angles_rad = [np.deg2rad(a) for a in angles_deg]
    theta_mean = float(np.mean(np.abs(angles_rad)))

    A_prop_disc  = np.pi * (D_prop_m / 2.0) ** 2
    A_arm_stripe = L_arm_m * d_out_m
    A_body       = np.pi * (body_diameter_m / 2.0) ** 2

    S_top   = n_motors * A_prop_disc + n_motors * A_arm_stripe + A_body
    S_front = (n_motors * A_prop_disc * abs(np.sin(theta_mean))
               + n_motors * A_arm_stripe * abs(np.cos(theta_mean))
               + A_body)
    return S_top, S_front


def draw_top_view(L_arm_m: float, D_prop_m: float, n_motors: int,
                  config_name: str, clearance_ok: bool = True,
                  c_margin_m: float = 0.010,
                  body_diameter_m: float = 0.08) -> plt.Figure:
    """Generate top-view matplotlib Figure."""
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
        mxs.append(mx)
        mys.append(my)

        ax.plot([0, mx], [0, my], color="#374151", lw=2.5,
                solid_capstyle="round", zorder=2)

        circ = plt.Circle((mx, my), D_prop_m / 2.0,
                           facecolor=prop_color + "18",
                           edgecolor=prop_color, lw=1.8, zorder=3)
        ax.add_patch(circ)

        # CW/CCW arc indicator
        arc_r  = D_prop_m / 2.0 * 0.65
        arrow_color = "#374151"
        if spin == "CW":
            arc = plt.matplotlib.patches.Arc(
                (mx, my), 2*arc_r, 2*arc_r, angle=0,
                theta1=30, theta2=330, color=arrow_color, lw=1.2, zorder=4)
        else:
            arc = plt.matplotlib.patches.Arc(
                (mx, my), 2*arc_r, 2*arc_r, angle=0,
                theta1=210, theta2=150, color=arrow_color, lw=1.2, zorder=4)
        ax.add_patch(arc)

        dot = plt.Circle((mx, my), max(L_arm_m * 0.025, 0.003),
                          color="#d97706", zorder=5)
        ax.add_patch(dot)

        off = L_arm_m * 0.22
        ax.text(mx + off * np.cos(theta), my + off * np.sin(theta),
                spin, fontsize=7, color="#6b7280",
                ha="center", va="center", zorder=6)
        ax.text(mx - off * 0.45 * np.cos(theta),
                my - off * 0.45 * np.sin(theta),
                f"M{i+1}", fontsize=7, color="#374151",
                ha="center", va="center", zorder=6)

    # Central body
    body_r = body_diameter_m / 2.0
    ax.add_patch(plt.Circle((0, 0), body_r, color="#d97706", alpha=0.85, zorder=6))

    # L_arm annotation
    theta0 = angles_rad[0]
    ax.annotate("",
                xy=(mxs[0] * 0.92, mys[0] * 0.92),
                xytext=(body_r * 1.4 * np.cos(theta0), body_r * 1.4 * np.sin(theta0)),
                arrowprops=dict(arrowstyle="<->", color="#d97706", lw=1.5))
    perp = theta0 + np.pi / 2
    lx = L_arm_m / 2 * np.cos(theta0) + L_arm_m * 0.10 * np.cos(perp)
    ly = L_arm_m / 2 * np.sin(theta0) + L_arm_m * 0.10 * np.sin(perp)
    ax.text(lx, ly, f"L = {L_arm_m*1000:.0f} mm", fontsize=9,
            color="#d97706", ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#d97706", alpha=0.9))

    # D_prop label
    ax.annotate("", xy=(mxs[0] + D_prop_m / 2, mys[0]),
                xytext=(mxs[0], mys[0]),
                arrowprops=dict(arrowstyle="->", color=prop_color, lw=1.2))
    ax.text(mxs[0] + D_prop_m / 2 + L_arm_m * 0.05, mys[0],
            f"D = {D_prop_m*1000:.0f} mm", fontsize=8,
            color=prop_color, va="center")

    # Total span annotation
    span = 2 * L_arm_m + D_prop_m
    sy   = -(L_arm_m + D_prop_m / 2) * 1.22
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
    ax.set_title(f"SWIFT — {config_name}  ({n_motors} motors)",
                 fontsize=12, color="#1a1a1a", fontweight="bold", pad=12)

    pad = (L_arm_m + D_prop_m / 2) * 1.45
    ax.set_xlim(-pad, pad)
    ax.set_ylim(-pad * 1.28, pad)
    plt.tight_layout()
    return fig


def fig_to_png_bytes(fig: plt.Figure) -> bytes:
    """Convert matplotlib Figure to PNG bytes."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150,
                bbox_inches="tight", facecolor="white")
    buf.seek(0)
    return buf.read()
