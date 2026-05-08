"""
Resizing Phase — Overview (R0).
Displays sizing-phase targets, ANAFI USA verification case loader, workflow guide.
"""
import streamlit as st


# ── ANAFI USA verification case (Pollet 2024, Tables 3.8 / 3.9) ─────────────
_ANAFI_SEGMENTS = {
    "takeoff": {"active": True,  "duration_min": 0.5,  "a_TO_ms2": 24.525},
    "climb":   {"active": False, "duration_min": 1.0},
    "cruise":  {"active": False, "duration_min": 5.0},
    "hover":   {"active": True,  "duration_min": 25.0},
    "land":    {"active": True,  "duration_min": 0.5,  "k_land": 0.5},
}

_ANAFI_MOTOR = {
    "Motor": "Parrot Bebop 2 (ANAFI proxy)",
    "Mass_g": 10.0, "T_50pct_g": 117.0, "P_50pct_W": 25.4,
    "T_100pct_g": 210.0, "P_100pct_W": 56.0,
    "PL_50pct_gW": 117.0 / 25.4, "PL_100pct_gW": 210.0 / 56.0,
    "Selected": True,
}
_ANAFI_PROP = {
    "Propeller": "Parrot 6.6in", "Diameter_in": 6.6,
    "Diameter_m": 0.1676, "Mass_g": 3.0, "Selected": True,
}
_ANAFI_BATTERY = {
    "Label": "ANAFI 3S 2700mAh", "Capacity_mAh": 2700,
    "Cells": 3, "V_cell_V": 3.8, "Mass_g": 195.0,
}
_ANAFI_AVI = [
    {"Component": "Autopilot / FC",      "Enabled": True,  "Mass_g": 8.0,  "Power_W": 0.5},
    {"Component": "GPS / Compass",       "Enabled": True,  "Mass_g": 6.0,  "Power_W": 0.3},
    {"Component": "Telemetry",           "Enabled": True,  "Mass_g": 5.0,  "Power_W": 0.2},
    {"Component": "RC Receiver",         "Enabled": True,  "Mass_g": 2.5,  "Power_W": 0.1},
    {"Component": "Power Module",        "Enabled": True,  "Mass_g": 6.0,  "Power_W": 0.2},
    {"Component": "Camera (payload)",    "Enabled": False, "Mass_g": 0.0,  "Power_W": 0.0},
    {"Component": "Custom 1",            "Enabled": False, "Mass_g": 0.0,  "Power_W": 0.0},
]


def _load_anafi(ss):
    """Populate session state with ANAFI USA verification case."""
    # Mission / payload (override sizing bridge values for standalone testing)
    ss.m_pay   = 0.250
    ss.MF_pay  = 0.50
    ss.P_pay   = 15.0
    ss.n_motors = 4

    # Segments
    ss.resizing_mission_segments = {k: dict(v) for k, v in _ANAFI_SEGMENTS.items()}
    ss.resizing_cruise_active    = False
    ss.resizing_a_TO_ms2         = 24.525
    ss.resizing_k_land           = 0.5

    # Avionics
    ss.resizing_avi_architecture = "AIO Stack"
    ss.resizing_avi_components   = [dict(r) for r in _ANAFI_AVI]
    ss.resizing_M_avi = 27.5 / 1000.0
    ss.resizing_P_avi = 1.3

    # Propulsion
    ss.resizing_motors       = [dict(_ANAFI_MOTOR)]
    ss.resizing_props        = [dict(_ANAFI_PROP)]
    ss.resizing_escs         = []
    ss.resizing_motor_selected = dict(_ANAFI_MOTOR)
    ss.resizing_prop_selected  = dict(_ANAFI_PROP)
    ss.resizing_M_prop         = 4 * (10.0 + 3.0) / 1000.0
    ss.resizing_PL_50pct_gW    = 117.0 / 25.4
    ss.resizing_T_100pct_g     = 210.0

    # Structure
    ss.resizing_cross_section = "Circular Hollow Tube"
    ss.resizing_material      = "CF tube/rod"
    ss.resizing_k_arm         = 1.2
    ss.resizing_k_ratio       = 0.7
    ss.resizing_b_plate_m     = 0.012
    ss.resizing_FoS           = 1.5
    ss.resizing_c_margin_m    = 0.005
    ss.resizing_D_prop_m      = 0.1676
    ss.resizing_body_diameter = 0.08
    ss.resizing_M_body        = 0.030
    ss.resizing_M_struct_sizing = ss.get("m_struct_sizing", 0.050)

    # Battery
    ss.resizing_batteries       = [dict(_ANAFI_BATTERY)]
    ss.resizing_selected_batt_idx = 0
    ss.resizing_battery_selected  = dict(_ANAFI_BATTERY)
    ss.resizing_SED     = 195.0 * 3 * 3.8 / 195.0  # ≈ 205 Wh/kg from datasheet
    ss.resizing_V_batt  = 3 * 3.8
    ss.resizing_DoD     = 0.80
    ss.resizing_eta_elec = 0.95

    # Config
    ss.resizing_config = "Quad X"


def _no_sizing():
    st.markdown("""
<div style="background:#ffffff;border:1px dashed #e5e7eb;border-radius:12px;
            padding:56px;text-align:center;margin-top:32px;">
    <div style="font-size:2.8rem;margin-bottom:14px;color:#d97706;">⬡</div>
    <div style="color:#1a1a1a;font-size:1.05rem;font-weight:600;">
        Sizing Phase not yet complete
    </div>
    <div style="color:#6b7280;font-size:0.85rem;margin-top:8px;">
        Complete the <b>Sizing Phase</b> (tabs 01–07) and click
        <b style="color:#d97706;">▶ Run Sizing</b> in the Battery tab first,
        or use <b>Load ANAFI USA Case</b> below for a standalone verification.
    </div>
</div>
""", unsafe_allow_html=True)


def render():
    st.markdown('<div class="section-tag">Resizing Phase · Overview</div>',
                unsafe_allow_html=True)
    st.markdown("## R0 · Overview & Sizing Targets")

    ss = st.session_state

    # ── ANAFI verification case ───────────────────────────────────────────────
    st.markdown("### ANAFI USA Verification Case")
    st.markdown("""
<div class="info-box">
<b>Pollet (2024) Tables 3.8 / 3.9</b> — loads all inputs for the Parrot ANAFI USA
(n=4 motors, m_pay=250 g, 25 min hover, no cruise). Expected result: MTOW ≈ 500 g,
E_batt ≈ 40 Wh, P_motor ≈ 46 W. Click <b>Load</b> then go to R7 · Results and click
<b>▶ Run Resizing</b>.
</div>
""", unsafe_allow_html=True)

    col_btn, col_hint = st.columns([1, 3], gap="medium")
    with col_btn:
        if st.button("Load ANAFI USA Case", use_container_width=True,
                     help="Populate all resizing tabs with ANAFI USA verification data."):
            _load_anafi(ss)
            st.success("ANAFI USA case loaded — proceed to R7 · Results to run.")

    with col_hint:
        st.markdown("""
<div style="font-size:0.82rem;color:#6b7280;padding-top:8px;">
  n=4 · m_pay=250 g · MF_pay=0.50 · Hover 25 min · CF arm · k_arm=1.2 · k_ratio=0.7<br>
  Motor: T_50=117 g / P_50=25.4 W (PL≈4.6 g/W) · Battery: 3S 2700 mAh 195 g
</div>
""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Sizing phase targets ──────────────────────────────────────────────────
    st.markdown("### Sizing Phase Targets")
    if not ss.get("sizing_done", False):
        _no_sizing()
    else:
        st.markdown("""
<div class="info-box">
These targets come from the Sizing Phase fixed-point loop.
Use them to select real hardware in R1–R5; then R7 re-converges MTOW.
</div>
""", unsafe_allow_html=True)

        rows = [
            ("MTOW (converged)",          f"{ss.mtow_converged:.4g} kg",
             f"{ss.mtow_converged*1000:.4g} g"),
            ("Structural mass",           f"{ss.m_struct_sizing:.4g} kg",
             f"{ss.m_struct_sizing*1000:.4g} g"),
            ("Avionics mass",             f"{ss.get('m_avi_sizing', 0.0):.4g} kg",
             f"{ss.get('m_avi_sizing', 0.0)*1000:.4g} g"),
            ("Propulsion mass",           f"{ss.get('m_prop_sizing', 0.0):.4g} kg",
             f"{ss.get('m_prop_sizing', 0.0)*1000:.4g} g"),
            ("Battery mass",              f"{ss.m_batt_sizing:.4g} kg",
             f"{ss.m_batt_sizing*1000:.4g} g"),
            ("T_motor at hover",          f"{ss.t_motor_target:.4g} g",  "per motor"),
            ("T_motor at 50% throttle",   f"{ss.get('t_motor_50pct_target', ss.t_motor_target/2):.4g} g",
             "per motor"),
            ("P_motor target",            f"{ss.p_motor_target:.4g} W",  "per motor"),
            ("P_total",                   f"{ss.get('p_total_target', 0.0):.4g} W", ""),
            ("Battery energy",            f"{ss.e_battery_target:.4g} Wh", ""),
            ("Battery capacity (+15%)",   f"{ss.c_battery_target:.4g} mAh",
             "use for hardware selection"),
            ("Power loading (design)",    f"{ss.pl_sizing:.4g} g/W",  ""),
        ]

        rows_html = ""
        for name, val, note in rows:
            rows_html += (
                f'<tr>'
                f'<td style="padding:7px 14px;color:#b45309;font-family:monospace;font-size:0.82rem;">{name}</td>'
                f'<td style="padding:7px 14px;color:#d97706;font-weight:700;font-size:0.90rem;">{val}</td>'
                f'<td style="padding:7px 14px;color:#6b7280;font-size:0.79rem;">{note}</td>'
                f'</tr>'
            )

        st.markdown(f"""
<div style="background:#ffffff;border:1px solid #e5e7eb;border-top:2px solid #d97706;
            border-radius:10px;overflow:hidden;margin-bottom:20px;">
<table style="width:100%;border-collapse:collapse;">
<tr style="background:#fffbeb;">
  <th style="color:#d97706;padding:9px 14px;text-align:left;font-size:0.70rem;
             letter-spacing:0.10em;text-transform:uppercase;border-bottom:1px solid #e5e7eb;">Parameter</th>
  <th style="color:#d97706;padding:9px 14px;text-align:left;font-size:0.70rem;
             letter-spacing:0.10em;text-transform:uppercase;border-bottom:1px solid #e5e7eb;">Value</th>
  <th style="color:#d97706;padding:9px 14px;text-align:left;font-size:0.70rem;
             letter-spacing:0.10em;text-transform:uppercase;border-bottom:1px solid #e5e7eb;">Notes</th>
</tr>
{rows_html}
</table>
</div>
""", unsafe_allow_html=True)

    # ── Workflow guide ────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Resizing Workflow")
    steps = [
        ("R1 · Mission",     "Define flight segments (Takeoff / Climb / Cruise / Hover / Land) and durations."),
        ("R2 · Avionics",    "Select FC+ESC architecture. Component-level mass/power replaces the MF_avi fraction."),
        ("R3 · Propulsion",  "Choose motor, propeller, ESC from datasheets. Auto-computes PL_50pct and PL_100pct."),
        ("R4 · Structure",   "Material and cross-section chosen; arm dimensions are SOLVED from the stress constraint."),
        ("R5 · Battery",     "Match a real battery to capacity target. SED is extracted for the convergence loop."),
        ("R6 · Layout 2D",   "View 2D top-view drawing. Reference areas S_top / S_front used for aerodynamics."),
        ("R7 · Aerodynamics","(Only with cruise segment) Compute drag, lift, cruise power and energy."),
        ("R8 · Results",     "Run fixed-point resizing loop with real hardware. Compare against sizing phase."),
        ("R9 · Optimisation","SLSQP: minimise MTOW over [k_arm, k_ratio] within structural and T/W constraints."),
    ]
    for label, desc in steps:
        st.markdown(f"""
<div style="display:flex;align-items:flex-start;gap:12px;margin-bottom:10px;">
  <div style="background:#fef3c7;border:1px solid #fde68a;border-radius:6px;
              padding:4px 10px;font-size:0.72rem;font-weight:700;color:#b45309;
              white-space:nowrap;flex-shrink:0;">{label}</div>
  <div style="color:#374151;font-size:0.85rem;padding-top:4px;">{desc}</div>
</div>""", unsafe_allow_html=True)
