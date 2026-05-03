"""
Resizing Phase — Overview tab.
Displays sizing-phase targets as a reference card and confirms the bridge.
"""
import streamlit as st


def _no_sizing():
    st.markdown("""
<div style="background:#ffffff;border:1px dashed #e5e7eb;border-radius:12px;
            padding:56px;text-align:center;margin-top:32px;">
    <div style="font-size:2.8rem;margin-bottom:14px;color:#d97706;">⬡</div>
    <div style="color:#1a1a1a;font-size:1.05rem;font-weight:600;">
        Sizing Phase not yet complete
    </div>
    <div style="color:#6b7280;font-size:0.85rem;margin-top:8px;">
        Complete the <b>Sizing Phase</b> (tabs 01–06) and click
        <b style="color:#d97706;">▶ Run Sizing</b> in the Battery tab first.
    </div>
</div>
""", unsafe_allow_html=True)


def render():
    st.markdown('<div class="section-tag">Resizing Phase · Overview</div>',
                unsafe_allow_html=True)
    st.markdown("## R0 · Sizing Targets")

    if not st.session_state.get("sizing_done", False):
        _no_sizing()
        return

    ss = st.session_state

    st.markdown("""
<div class="info-box">
These are the <b>target specifications</b> produced by the Sizing Phase fixed-point loop.
Use them to select real motors, ESCs, and batteries in the tabs below.
The Resizing Phase will re-converge MTOW using the actual hardware masses you choose.
</div>
""", unsafe_allow_html=True)

    # ── Targets card ─────────────────────────────────────────────────────────
    rows = [
        ("MTOW (converged)",           f"{ss.mtow_converged:.4g} kg",
         f"{ss.mtow_converged*1000:.4g} g"),
        ("Structural mass (sizing)",   f"{ss.m_struct_sizing:.4g} kg",
         f"{ss.m_struct_sizing*1000:.4g} g"),
        ("Avionics mass (sizing)",     f"{ss.get('m_avi_sizing', 0.0):.4g} kg",
         f"{ss.get('m_avi_sizing', 0.0)*1000:.4g} g"),
        ("Propulsion mass (sizing)",   f"{ss.get('m_prop_sizing', 0.0):.4g} kg",
         f"{ss.get('m_prop_sizing', 0.0)*1000:.4g} g"),
        ("Battery mass (sizing)",      f"{ss.m_batt_sizing:.4g} kg",
         f"{ss.m_batt_sizing*1000:.4g} g"),
        ("T_motor at hover",           f"{ss.t_motor_target:.4g} g",   "per motor"),
        ("T_motor at 50 % throttle",   f"{ss.get('t_motor_50pct_target', ss.t_motor_target/2):.4g} g",
         "per motor"),
        ("P_motor target",             f"{ss.p_motor_target:.4g} W",   "per motor at hover"),
        ("P_total (prop+avi+pay)",      f"{ss.get('p_total_target', 0.0):.4g} W", ""),
        ("Battery energy",             f"{ss.e_battery_target:.4g} Wh", ""),
        ("Battery capacity (+15 %)",   f"{ss.c_battery_target:.4g} mAh",
         "use this for hardware selection"),
        ("Power loading (design)",     f"{ss.pl_sizing:.4g} g/W",      ""),
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
    st.markdown("### Resizing Workflow")
    steps = [
        ("R1 · Structure",    "Set arm geometry (k_arm, cross-section, material). Verify stress FoS and prop clearance."),
        ("R2 · Avionics",     "Select real avionics components. Total mass and power replace the MF_avi fraction."),
        ("R3 · Propulsion",   "Choose motor, propeller, and ESC from datasheets. Check feasibility against T_motor target."),
        ("R4 · Battery",      "Match a real battery to the capacity target. Extract SED for the convergence loop."),
        ("R5 · Mission",      "Set actual flight time, DoD, η, and configuration. Preview the 2D top-view layout."),
        ("R6 · Results",      "Run the fixed-point resizing loop with real hardware masses. Compare against sizing."),
        ("R7 · Optimisation", "Optionally run SLSQP to minimise MTOW over arm geometry within stress/clearance constraints."),
    ]
    for label, desc in steps:
        st.markdown(f"""
<div style="display:flex;align-items:flex-start;gap:12px;margin-bottom:10px;">
  <div style="background:#fef3c7;border:1px solid #fde68a;border-radius:6px;
              padding:4px 10px;font-size:0.72rem;font-weight:700;color:#b45309;
              white-space:nowrap;flex-shrink:0;">{label}</div>
  <div style="color:#374151;font-size:0.85rem;padding-top:4px;">{desc}</div>
</div>""", unsafe_allow_html=True)
