"""
Battery tab — energy model inputs, power loading mode, and Run Sizing trigger.
"""

import streamlit as st
import numpy as np
from core.sizing_loop import run_sizing, run_sizing_sweep


def _gather_params() -> dict:
    ss = st.session_state
    return {
        # Mission
        "n_motors":  ss.n_motors,
        "t_flight":  ss.t_flight_min / 60.0,
        "P_avi":     ss.P_avi,
        # Payload
        "m_pay":     ss.m_pay,
        "MF_pay":    ss.MF_pay,
        "P_pay":     ss.P_pay,
        # Structures
        "MF_str":    ss.MF_str,
        # Avionics
        "MF_avi":    ss.MF_avi,
        # Propulsion
        "M_motor_g": ss.M_motor_g,
        "M_prop_g":  ss.M_prop_g,
        "V_batt":    ss.V_batt,
        # Battery
        "SED":       ss.SED,
        "DoD":       ss.DoD,
        "eta_elec":  ss.eta_elec,
        "PL":        ss.PL,
    }


def render():
    st.markdown('<div class="section-tag">Battery Energy Model</div>', unsafe_allow_html=True)
    st.markdown("## 06 · Battery")

    st.markdown("**Governing equations**")
    st.latex(
        r"T_{motor} = \frac{\text{MTOW}}{n_{motors}} \quad \text{[kg]}"
    )
    st.latex(
        r"P_{motor} = \frac{T_{motor} \times 1000}{PL} \quad \text{[W]}"
    )
    st.latex(
        r"E_{req} = \left(n_{motors} \cdot P_{motor} + P_{avi} + P_{pay}\right) \times t_{flight} \quad \text{[Wh]}"
    )
    st.latex(
        r"M_{batt} = \frac{E_{req}}{SED \times DoD \times \eta_{elec}} \quad \text{[kg]}"
    )

    st.markdown("""
<div class="info-box">
<b>SED</b> is the specific energy density of the battery cell chemistry.
<b>DoD</b> is the depth of discharge (fraction of capacity actually used — limits battery stress).
<b>η_elec</b> captures combined ESC, wiring, and connector losses.
<b>PL</b> (power loading) relates thrust to power: higher PL → lighter system, less thrust margin.
</div>
""", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown("**Battery parameters**")

        SED = st.number_input(
            "Specific energy SED [Wh/kg]",
            min_value=50.0, max_value=500.0,
            value=float(st.session_state.SED),
            step=5.0, format="%.0f",
            help="Li-Po: 130–220 Wh/kg  |  Li-Ion: 180–260 Wh/kg  |  Solid-state: 300+ Wh/kg",
            key="_num_SED",
        )
        st.session_state.SED = SED

        DoD = st.slider(
            "Depth of Discharge DoD [—]",
            min_value=0.50, max_value=0.99,
            value=float(st.session_state.DoD),
            step=0.01, format="%.2f",
            help="0.80–0.90 recommended for Li-Po cycle life.",
            key="_sl_DoD",
        )
        st.session_state.DoD = DoD

        eta_elec = st.slider(
            "Electrical efficiency η_elec [—]",
            min_value=0.60, max_value=0.99,
            value=float(st.session_state.eta_elec),
            step=0.01, format="%.2f",
            help="Combined ESC + motor + wiring efficiency. Typical: 0.82–0.90.",
            key="_sl_eta_elec",
        )
        st.session_state.eta_elec = eta_elec

    with col2:
        st.markdown("**Power loading**")

        PL_mode = st.radio(
            "Power loading mode",
            options=["Single Value", "Sweep (5 – 8 g/W)"],
            index=0 if st.session_state.PL_mode == "Single Value" else 1,
            help=(
                "Single Value: size for one PL point. "
                "Sweep: compute MTOW vs PL chart over 5–8 g/W, step 0.5 g/W."
            ),
            key="_radio_PL_mode",
        )
        st.session_state.PL_mode = PL_mode

        if PL_mode == "Single Value":
            PL = st.number_input(
                "Power loading PL [g/W]",
                min_value=1.0, max_value=20.0,
                value=float(st.session_state.PL),
                step=0.5, format="%.1f",
                help="Higher PL → lighter system, lower thrust margin. Typical: 5–8 g/W for endurance.",
                key="_num_PL",
            )
            st.session_state.PL = PL
        else:
            st.info("Sweep: PL stepped from **5.0 to 8.0 g/W** in steps of 0.5 g/W.")
            PL = st.session_state.PL

        st.markdown("""
<div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:10px;padding:12px 16px;margin-top:8px;">
<div style="font-size:0.70rem;font-weight:700;color:#d97706;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px;">
  PL Reference Values
</div>
<table style="width:100%;font-size:0.81rem;border-collapse:collapse;">
<tr><td style="padding:3px 8px;color:#1a1a1a;">3–4 g/W</td><td style="padding:3px 8px;color:#6b7280;">Racing / high-agility</td></tr>
<tr><td style="padding:3px 8px;color:#1a1a1a;">5–6 g/W</td><td style="padding:3px 8px;color:#6b7280;">Photography / inspection</td></tr>
<tr><td style="padding:3px 8px;color:#1a1a1a;">6–8 g/W</td><td style="padding:3px 8px;color:#6b7280;">Endurance / delivery</td></tr>
<tr><td style="padding:3px 8px;color:#1a1a1a;">&gt; 8 g/W</td><td style="padding:3px 8px;color:#6b7280;">Ultra-endurance</td></tr>
</table>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")

    # ── RUN SIZING BUTTON ────────────────────────────────────────────────────
    btn_col, status_col = st.columns([1, 3], gap="medium")
    with btn_col:
        run_clicked = st.button(
            "▶  Run Sizing",
            help="Execute fixed-point mass convergence with current inputs.",
            use_container_width=True,
        )

    if run_clicked:
        params = _gather_params()
        with st.spinner("Running convergence loop…"):
            results = run_sizing(params)
            st.session_state.results = results

            # Bridge to Resizing Phase
            st.session_state.sizing_done            = True
            st.session_state.mtow_converged         = results["M_TO"]
            st.session_state.m_struct_sizing        = results["m_struct"]
            st.session_state.m_avi_sizing           = results["m_avi"]
            st.session_state.m_prop_sizing          = results["M_prop"]
            st.session_state.m_batt_sizing          = results["M_batt"]
            st.session_state.pl_sizing              = results["PL"]
            st.session_state.p_motor_target         = results["P_motor_W"]
            st.session_state.t_motor_target         = results["T_motor_g"]
            st.session_state.t_motor_50pct_target   = results["T_at_50pct_g"]
            st.session_state.c_battery_target       = results["C_mAh_target"]
            st.session_state.e_battery_target       = results["E_req_Wh"]
            st.session_state.p_total_target         = results["P_total_W"]

            if PL_mode == "Sweep (5 – 8 g/W)":
                pl_vals = np.arange(5.0, 8.5, 0.5).tolist()
                sweep = run_sizing_sweep(params, pl_vals)
                st.session_state.sweep_results = sweep
            else:
                st.session_state.sweep_results = None

    with status_col:
        if st.session_state.results is not None:
            r = st.session_state.results
            if r["converged"]:
                st.markdown(
                    f'<span class="converged-badge">✓ Converged in {r["n_iterations"]} iterations'
                    f'  ·  MTOW = {r["M_TO"]:.4g} kg</span>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<span class="warn-badge">⚠ Not converged after 50 iterations'
                    f'  ·  MTOW = {r["M_TO"]:.4g} kg</span>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<span style="color:#6b7280;font-size:0.85rem;">No results yet — click ▶ Run Sizing</span>',
                unsafe_allow_html=True,
            )

    # ── Quick preview ────────────────────────────────────────────────────────
    if st.session_state.results is not None:
        r = st.session_state.results
        st.markdown("**Quick preview** — see Results tab for full breakdown")
        c1, c2, c3, c4, c5 = st.columns(5, gap="small")
        c1.metric("MTOW", f"{r['M_TO']:.4g} kg")
        c2.metric("M_batt", f"{r['M_batt'] * 1000:.4g} g")
        c3.metric("P_total", f"{r['P_total_W']:.4g} W")
        c4.metric("E_req", f"{r['E_req_Wh']:.4g} Wh")
        c5.metric("Iterations", str(r["n_iterations"]))

    # ── PL Sweep chart ───────────────────────────────────────────────────────
    if st.session_state.sweep_results is not None:
        import plotly.graph_objects as go

        sweep   = st.session_state.sweep_results
        pl_arr  = [s["PL"] for s in sweep]
        mto_arr = [s["M_TO"] for s in sweep]
        bat_arr = [s["M_batt"] for s in sweep]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=pl_arr, y=mto_arr,
            mode="lines+markers",
            line=dict(color="#d97706", width=2.5),
            marker=dict(size=8, color="#d97706"),
            name="MTOW [kg]",
            hovertemplate="PL=%{x:.1f} g/W<br>MTOW=%{y:.4g} kg<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=pl_arr, y=bat_arr,
            mode="lines+markers",
            line=dict(color="#6b7280", width=1.5, dash="dash"),
            marker=dict(size=6, color="#6b7280"),
            name="M_batt [kg]",
            hovertemplate="PL=%{x:.1f} g/W<br>M_batt=%{y:.4g} kg<extra></extra>",
        ))
        fig.update_layout(
            paper_bgcolor="#ffffff", plot_bgcolor="#f9fafb",
            font=dict(color="#374151", size=11),
            xaxis=dict(title="Power loading PL [g/W]", gridcolor="#e5e7eb",
                       title_font_color="#6b7280"),
            yaxis=dict(title="Mass [kg]", gridcolor="#e5e7eb",
                       title_font_color="#6b7280"),
            legend=dict(bgcolor="#ffffff", bordercolor="#e5e7eb", borderwidth=1),
            height=300,
            margin=dict(l=10, r=10, t=10, b=10),
            title=dict(text="MTOW vs Power Loading (sweep)", font_color="#6b7280", font_size=12),
        )
        st.plotly_chart(fig, use_container_width=True)
