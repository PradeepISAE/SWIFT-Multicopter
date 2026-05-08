"""
Resizing Phase — Mission Segments (R1).
Five segments: Takeoff (always), Climb (optional), Cruise (optional → enables Aero tab),
Hover (always), Land (always).
"""
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


_SEG_COLORS = {
    "takeoff": "#d97706",
    "climb":   "#3b82f6",
    "cruise":  "#10b981",
    "hover":   "#6b7280",
    "land":    "#8b5cf6",
}

_SEG_LABELS = {
    "takeoff": "Takeoff",
    "climb":   "Climb",
    "cruise":  "Cruise",
    "hover":   "Hover",
    "land":    "Land",
}


def _default_segments():
    return {
        "takeoff": {"active": True,  "duration_min": 0.5,  "a_TO_ms2": 19.62},
        "climb":   {"active": False, "duration_min": 2.0},
        "cruise":  {"active": False, "duration_min": 5.0},
        "hover":   {"active": True,  "duration_min": 20.0},
        "land":    {"active": True,  "duration_min": 0.5,  "k_land": 0.5},
    }


def _eq_ref():
    with st.expander("Equations & References"):
        st.markdown("**Throttle factors**")
        st.latex(r"k_{TO} = 1 + \frac{a_{TO}}{g}")
        st.latex(r"k_{land} \in (0,\,1] \quad \text{(partial throttle during descent)}")
        st.markdown("**Segment power**")
        st.latex(r"P_{hover} = \frac{MTOW \cdot g \cdot 1000}{PL_{50\%}} \quad \text{[W, all motors]}")
        st.latex(r"P_{TO} = k_{TO} \cdot P_{hover}, \qquad P_{land} = k_{land} \cdot P_{hover}")
        st.markdown("**Segment energy**")
        st.latex(r"E_k = P_k \cdot \frac{t_k}{60} \quad \text{[Wh]}, \quad t_k \text{ in minutes}")
        st.latex(r"E_{total} = \sum_k E_k + E_{cruise} \quad \text{[Wh]}")
        st.caption(
            "References: Pollet (2024) PhD Thesis §3.6; "
            "Tyan et al. (2017) 'Improving Reliability of UAV Preliminary Sizing' §3.2"
        )


def _mission_profile_chart(segs: dict) -> plt.Figure:
    """Draw altitude vs time mission profile."""
    fig, ax = plt.subplots(figsize=(8, 3), dpi=110)
    ax.set_facecolor("#f9fafb")
    fig.patch.set_facecolor("#ffffff")

    t_cursor = 0.0
    h_cursor = 0.0
    MAX_H = 50.0  # representative altitude [m]

    def seg_height(name):
        if name == "takeoff":
            return 10.0
        if name == "climb":
            return MAX_H
        if name == "cruise":
            return MAX_H
        if name == "hover":
            return MAX_H * 0.3 if not segs.get("climb", {}).get("active", False) else MAX_H
        return 0.0

    order = ["takeoff", "climb", "cruise", "hover", "land"]
    xs, ys = [0.0], [0.0]

    for name in order:
        seg = segs.get(name, {})
        if not seg.get("active", False):
            continue
        dur = seg.get("duration_min", 0.5)
        h_end = seg_height(name) if name != "land" else 0.0
        # For land: descend from current height
        if name == "land":
            h_end = 0.0
        # Transition point
        xs.append(t_cursor)
        ys.append(h_cursor)
        t_cursor += dur
        h_cursor = h_end
        xs.append(t_cursor)
        ys.append(h_cursor)

    ax.fill_between(xs, ys, alpha=0.12, color="#d97706")
    ax.plot(xs, ys, color="#d97706", lw=2.0)

    t_cursor = 0.0
    h_cursor = 0.0
    for name in order:
        seg = segs.get(name, {})
        if not seg.get("active", False):
            continue
        dur = seg.get("duration_min", 0.5)
        h_start = h_cursor
        h_end = seg_height(name) if name != "land" else 0.0
        t_mid = t_cursor + dur / 2.0
        h_mid = (h_start + h_end) / 2.0
        ax.text(t_mid, max(h_mid + MAX_H * 0.06, MAX_H * 0.05),
                f"{_SEG_LABELS[name]}\n{dur:.1f} min",
                ha="center", va="bottom", fontsize=7, color=_SEG_COLORS[name],
                fontweight="bold")
        t_cursor += dur
        h_cursor = h_end

    total_min = sum(
        segs.get(n, {}).get("duration_min", 0.0)
        for n in order if segs.get(n, {}).get("active", False)
    )
    ax.set_xlim(-0.3, total_min + 0.3)
    ax.set_ylim(-3, MAX_H * 1.35)
    ax.set_xlabel("Time [min]", color="#6b7280", fontsize=9)
    ax.set_ylabel("Altitude [m]", color="#6b7280", fontsize=9)
    ax.set_title("Mission Profile", fontsize=10, color="#1a1a1a", fontweight="bold")
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)
    for spine in ("left", "bottom"):
        ax.spines[spine].set_color("#e5e7eb")
    ax.tick_params(colors="#6b7280", labelsize=8)
    ax.grid(axis="y", color="#e5e7eb", lw=0.7, linestyle="--")
    plt.tight_layout()
    return fig


def render():
    st.markdown('<div class="section-tag">Resizing Phase · Mission</div>',
                unsafe_allow_html=True)
    st.markdown("## R1 · Mission Segments")

    ss = st.session_state

    if "resizing_mission_segments" not in ss:
        ss.resizing_mission_segments = _default_segments()

    segs = ss.resizing_mission_segments

    st.markdown("""
<div class="info-box">
Define each flight segment. <b>Cruise</b> activates the <b>Aerodynamics tab</b> for drag / power
computation. Takeoff, Hover, and Land are always active.
</div>
""", unsafe_allow_html=True)

    _eq_ref()

    col_inputs, col_chart = st.columns([1, 1], gap="large")

    with col_inputs:
        # ── Takeoff ───────────────────────────────────────────────────────────
        st.markdown("**Takeoff** (always active)")
        to = segs["takeoff"]
        to["duration_min"] = st.number_input(
            "Takeoff duration [min]", 0.1, 5.0, float(to.get("duration_min", 0.5)),
            step=0.1, format="%.1f", key="_rz_to_dur",
        )
        to["a_TO_ms2"] = st.number_input(
            "Takeoff acceleration a_TO [m/s²]", 1.0, 50.0,
            float(to.get("a_TO_ms2", 19.62)), step=0.5, format="%.2f",
            help="a_TO = 2g ≈ 19.62 m/s² ; a_TO = 2.5g ≈ 24.525 m/s²",
            key="_rz_to_ato",
        )
        ss.resizing_a_TO_ms2 = to["a_TO_ms2"]
        st.caption(f"Throttle factor k_TO = 1 + a_TO/g = {1 + to['a_TO_ms2']/9.81:.3f}")

        st.markdown("---")

        # ── Climb ─────────────────────────────────────────────────────────────
        cl = segs["climb"]
        cl["active"] = st.checkbox("Enable Climb segment", value=bool(cl.get("active", False)),
                                   key="_rz_cl_en")
        if cl["active"]:
            cl["duration_min"] = st.number_input(
                "Climb duration [min]", 0.1, 30.0, float(cl.get("duration_min", 2.0)),
                step=0.5, format="%.1f", key="_rz_cl_dur",
            )
            ss.resizing_V_climb = st.number_input(
                "Climb speed V_climb [m/s]", 0.5, 20.0,
                float(ss.get("resizing_V_climb", 3.0)), step=0.5, format="%.1f",
                key="_rz_cl_v",
            )

        st.markdown("---")

        # ── Cruise ────────────────────────────────────────────────────────────
        cr = segs["cruise"]
        cr["active"] = st.checkbox("Enable Cruise segment (activates Aerodynamics tab)",
                                   value=bool(cr.get("active", False)), key="_rz_cr_en")
        ss.resizing_cruise_active = cr["active"]
        if cr["active"]:
            cr["duration_min"] = st.number_input(
                "Cruise duration [min]", 0.1, 120.0,
                max(0.1, float(cr.get("duration_min", 5.0))),
                step=0.5, format="%.1f", key="_rz_cr_dur",
            )
            ss.resizing_V_cruise = st.number_input(
                "Cruise speed V_cruise [m/s]", 1.0, 40.0,
                float(ss.get("resizing_V_cruise", 10.0)), step=0.5, format="%.1f",
                key="_rz_cr_v",
            )
            st.info("Set drag coefficients and compute cruise energy in R7 · Aerodynamics.")

        st.markdown("---")

        # ── Hover ─────────────────────────────────────────────────────────────
        st.markdown("**Hover** (always active)")
        hv = segs["hover"]
        hv["duration_min"] = st.number_input(
            "Hover duration [min]", 1.0, 240.0, float(hv.get("duration_min", 20.0)),
            step=1.0, format="%.1f", key="_rz_hv_dur",
        )

        st.markdown("---")

        # ── Land ──────────────────────────────────────────────────────────────
        st.markdown("**Land** (always active)")
        ld = segs["land"]
        ld["duration_min"] = st.number_input(
            "Landing duration [min]", 0.1, 5.0, float(ld.get("duration_min", 0.5)),
            step=0.1, format="%.1f", key="_rz_ld_dur",
        )
        ld["k_land"] = st.slider(
            "Landing throttle factor k_land", 0.2, 1.0,
            float(ld.get("k_land", 0.5)), step=0.05, format="%.2f",
            help="k_land < 1 → motors at partial throttle during descent (autorotation assist).",
            key="_rz_ld_k",
        )
        ss.resizing_k_land = ld["k_land"]

    # Persist
    ss.resizing_mission_segments = segs

    with col_chart:
        st.markdown("**Mission Profile**")
        fig = _mission_profile_chart(segs)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

        # Summary table
        total_min = sum(
            segs.get(n, {}).get("duration_min", 0.0)
            for n in ["takeoff", "climb", "cruise", "hover", "land"]
            if segs.get(n, {}).get("active", False)
        )
        active_names = [
            _SEG_LABELS[n] for n in ["takeoff", "climb", "cruise", "hover", "land"]
            if segs.get(n, {}).get("active", False)
        ]
        st.markdown(f"""
<div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:8px;
            padding:12px 14px;margin-top:8px;font-size:0.84rem;">
  <b>Active segments:</b> {" → ".join(active_names)}<br>
  <b>Total flight time:</b> {total_min:.1f} min
  {' &nbsp;·&nbsp; <b style="color:#10b981;">Cruise active</b>' if segs.get("cruise", {}).get("active") else ""}
</div>
""", unsafe_allow_html=True)

        # Additional parameters
        st.markdown("---")
        st.markdown("**Electrical parameters**")
        ss.resizing_DoD = st.slider(
            "Depth of Discharge DoD", 0.50, 0.99,
            float(ss.get("resizing_DoD", ss.get("DoD", 0.85))),
            step=0.01, format="%.2f", key="_rz_dod",
        )
        ss.resizing_eta_elec = st.slider(
            "Electrical efficiency η", 0.60, 0.99,
            float(ss.get("resizing_eta_elec", ss.get("eta_elec", 0.85))),
            step=0.01, format="%.2f", key="_rz_eta",
        )
        ss.resizing_config = st.selectbox(
            "Multirotor configuration",
            ["Quad X", "Quad +", "Hex", "Octo"],
            index=["Quad X", "Quad +", "Hex", "Octo"].index(
                ss.get("resizing_config", "Quad X")),
            key="_rz_cfg",
        )

    # ── Operating altitude ────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### Operating Altitude (ISA)")

    st.latex(
        r"\rho_{alt} = 1.225 \times \left(1 - 2.2558 \times 10^{-5} \cdot h"
        r"\right)^{4.2559} \quad [\text{kg/m}^3]"
    )

    col_alt, col_alt_out = st.columns(2)

    with col_alt:
        altitude_m = st.number_input(
            "Operating altitude h [m]",
            min_value=0,
            max_value=11000,
            value=int(ss.get("resizing_altitude_m", 0)),
            step=50,
            help=(
                "Altitude at which the UAV operates. "
                "Higher altitude = lower air density = more power needed "
                "for the same thrust. Sea level = 0 m."
            ),
            key="r_altitude_m",
        )
        ss["resizing_altitude_m"] = float(altitude_m)

    with col_alt_out:
        from resizing.mission_resizing import isa_density, altitude_power_correction
        rho_alt = isa_density(altitude_m)
        k_alt   = altitude_power_correction(altitude_m)
        ss["resizing_rho_alt"] = rho_alt
        ss["resizing_k_alt"]   = k_alt
        st.metric(
            "Air density ρ",
            f"{rho_alt:.4f} kg/m³",
            delta=f"{((rho_alt/1.225)-1)*100:.1f}% vs SL",
            delta_color="inverse",
            help="ISA density at operating altitude",
        )
        st.metric(
            "Power correction factor",
            f"{k_alt:.4f}",
            delta=f"+{(k_alt-1)*100:.1f}% more power vs SL",
            delta_color="inverse",
            help="P_alt = P_SL × this factor",
        )

    with st.expander("Altitude correction reference table", expanded=False):
        import pandas as pd
        altitudes = [0, 500, 1000, 1500, 2000, 2500, 3000, 4000, 5000]
        table_data = []
        for h in altitudes:
            rho = isa_density(h)
            k   = altitude_power_correction(h)
            table_data.append({
                "Altitude [m]":               h,
                "ρ [kg/m³]":                  round(rho, 4),
                "ρ/ρ_SL [-]":                 round(rho / 1.225, 4),
                "Power factor √(ρ_SL/ρ) [-]": round(k, 4),
                "Extra power [%]":             round((k - 1) * 100, 1),
            })
        st.dataframe(pd.DataFrame(table_data), use_container_width=True,
                     hide_index=True)

    st.caption(
        "Source: ICAO Standard Atmosphere (ISA). "
        "Power correction from actuator disc momentum theory — "
        "Pollet (2024), §3.3.2."
    )
