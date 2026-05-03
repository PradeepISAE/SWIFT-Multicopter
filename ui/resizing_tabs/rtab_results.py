"""
Resizing Phase — Results tab.
Runs the fixed-point resizing loop; comparison against sizing phase.
"""
import io
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from resizing.convergence_resizing import run_resizing


def _gather_params():
    ss = st.session_state
    return {
        "m_pay":          ss.m_pay,
        "MF_pay":         ss.MF_pay,
        "M_struct_fixed": ss.get("rz_M_struct_fixed", ss.get("m_struct_sizing", 0.05)),
        "M_avi_fixed":    ss.get("rz_M_avi_fixed",    ss.get("m_avi_sizing",    0.03)),
        "M_prop_fixed":   ss.get("rz_M_prop_fixed",   ss.get("m_prop_sizing",   0.02)),
        "n_motors":       int(ss.n_motors),
        "PL":             ss.get("rz_PL",             ss.PL),
        "P_avi":          ss.get("rz_P_avi_W",        ss.P_avi),
        "P_pay":          ss.P_pay,
        "t_flight":       ss.get("rz_t_flight_min",   ss.t_flight_min) / 60.0,
        "SED":            ss.get("rz_SED",            ss.SED),
        "DoD":            ss.get("rz_DoD",            ss.DoD),
        "eta_elec":       ss.get("rz_eta_elec",       ss.eta_elec),
        "V_batt":         ss.get("rz_V_batt",         ss.V_batt),
    }


def _no_sizing():
    st.markdown("""
<div style="background:#ffffff;border:1px dashed #e5e7eb;border-radius:12px;
            padding:48px;text-align:center;margin-top:24px;">
    <div style="font-size:2.4rem;color:#d97706;margin-bottom:12px;">⬡</div>
    <div style="color:#1a1a1a;font-size:1.0rem;font-weight:600;">Complete R1–R5 first</div>
    <div style="color:#6b7280;font-size:0.83rem;margin-top:6px;">
        Set structure, avionics, propulsion, battery, and mission tabs, then click
        <b style="color:#d97706;">▶ Run Resizing</b>.
    </div>
</div>
""", unsafe_allow_html=True)


def render():
    st.markdown('<div class="section-tag">Resizing Phase · Results</div>',
                unsafe_allow_html=True)
    st.markdown("## R6 · Resizing Results")

    ss = st.session_state

    # ── Run button ────────────────────────────────────────────────────────────
    btn_col, status_col = st.columns([1, 3], gap="medium")
    with btn_col:
        run_clicked = st.button(
            "▶  Run Resizing",
            help="Execute fixed-point mass convergence with real hardware masses.",
            use_container_width=True,
        )

    if run_clicked:
        params = _gather_params()
        with st.spinner("Running resizing convergence…"):
            rz = run_resizing(params)
            ss.rz_results = rz

    with status_col:
        rz = ss.get("rz_results")
        if rz is not None:
            if rz["converged"]:
                st.markdown(
                    f'<span class="converged-badge">✓ Converged in {rz["n_iterations"]} iterations'
                    f'  ·  MTOW = {rz["M_TO"]:.4g} kg</span>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<span class="warn-badge">⚠ Not converged after 50 iterations'
                    f'  ·  MTOW = {rz["M_TO"]:.4g} kg</span>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<span style="color:#6b7280;font-size:0.85rem;">'
                'No results yet — click ▶ Run Resizing</span>',
                unsafe_allow_html=True,
            )

    rz = ss.get("rz_results")
    if rz is None:
        _no_sizing()
        return

    st.markdown("---")

    # ── Quick metrics ─────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5, gap="small")
    c1.metric("MTOW",     f"{rz['M_TO']:.4g} kg")
    c2.metric("M_batt",   f"{rz['M_batt']*1000:.4g} g")
    c3.metric("P_total",  f"{rz['P_total_W']:.4g} W")
    c4.metric("E_req",    f"{rz['E_req_Wh']:.4g} Wh")
    c5.metric("C_mAh+15%",f"{rz['C_mAh_target']:.0f} mAh")

    st.markdown("---")

    # ── ROW 1: convergence + mass bar ─────────────────────────────────────────
    col_conv, col_bar = st.columns([1, 1], gap="large")

    with col_conv:
        st.markdown("### A · Convergence History")
        hist  = rz["history"]
        iters = list(range(len(hist)))

        fig_c = go.Figure()
        fig_c.add_trace(go.Scatter(
            x=iters, y=hist,
            mode="lines+markers",
            line=dict(color="#d97706", width=2.5),
            marker=dict(size=7, color="#d97706",
                        line=dict(color="#ffffff", width=1.5)),
            fill="tozeroy", fillcolor="rgba(217,119,6,0.06)",
            hovertemplate="Iteration %{x}<br>MTOW = %{y:.4g} kg<extra></extra>",
        ))
        fig_c.add_hline(y=rz["M_TO"], line_dash="dash", line_color="#6b7280",
                        annotation_text=f"Converged: {rz['M_TO']:.4g} kg",
                        annotation_font_color="#6b7280")
        fig_c.update_layout(
            paper_bgcolor="#ffffff", plot_bgcolor="#f9fafb",
            font=dict(color="#374151", size=11),
            xaxis=dict(title="Iteration", gridcolor="#e5e7eb", dtick=1,
                       title_font_color="#6b7280"),
            yaxis=dict(title="MTOW [kg]", gridcolor="#e5e7eb",
                       title_font_color="#6b7280"),
            height=300, margin=dict(l=10, r=10, t=10, b=10), showlegend=False,
        )
        st.plotly_chart(fig_c, use_container_width=True)

    with col_bar:
        st.markdown("### B · Mass Breakdown")
        labels = ["Payload", "Structure", "Avionics", "Propulsion", "Battery"]
        values = [rz["m_pay"], rz["m_struct"], rz["m_avi"], rz["M_prop"], rz["M_batt"]]
        M_TO   = rz["M_TO"]
        colors = ["#d97706", "#6b7280", "#3b82f6", "#10b981", "#8b5cf6"]

        fig_b = go.Figure(go.Bar(
            x=values, y=labels, orientation="h",
            marker_color=colors,
            text=[f"{v*1000:.4g} g  ({v/M_TO*100:.1f}%)" for v in values],
            textposition="outside",
            textfont=dict(size=10, color="#374151"),
            hovertemplate="%{y}: %{x:.4g} kg<extra></extra>",
        ))
        fig_b.add_vline(x=M_TO, line_dash="dot", line_color="#d97706",
                        annotation_text=f"MTOW = {M_TO:.4g} kg",
                        annotation_font_color="#d97706")
        fig_b.update_layout(
            paper_bgcolor="#ffffff", plot_bgcolor="#f9fafb",
            font=dict(color="#374151", size=11),
            xaxis=dict(title="Mass [kg]", gridcolor="#e5e7eb",
                       title_font_color="#6b7280"),
            yaxis=dict(gridcolor="#e5e7eb"),
            height=300, margin=dict(l=10, r=140, t=10, b=10), showlegend=False,
        )
        st.plotly_chart(fig_b, use_container_width=True)

    # ── ROW 2: Comparison Sizing vs Resizing ──────────────────────────────────
    if ss.get("sizing_done", False):
        st.markdown("### C · Sizing vs Resizing Comparison")
        sz = ss.results  # sizing results

        comp_rows = [
            ("MTOW [kg]",      sz["M_TO"],       rz["M_TO"]),
            ("M_struct [g]",   sz["m_struct"]*1000, rz["m_struct"]*1000),
            ("M_avi [g]",      sz["m_avi"]*1000,    rz["m_avi"]*1000),
            ("M_prop [g]",     sz["M_prop"]*1000,   rz["M_prop"]*1000),
            ("M_batt [g]",     sz["M_batt"]*1000,   rz["M_batt"]*1000),
            ("P_motor [W]",    sz["P_motor_W"],     rz["P_motor_W"]),
            ("E_req [Wh]",     sz["E_req_Wh"],      rz["E_req_Wh"]),
            ("C_mAh +15%",     sz["C_mAh_target"],  rz["C_mAh_target"]),
        ]

        rows_html = ""
        for name, sz_val, rz_val in comp_rows:
            delta  = rz_val - sz_val
            sign   = "+" if delta >= 0 else ""
            color  = "#dc2626" if delta > 1e-9 else "#16a34a"
            rows_html += (
                f'<tr>'
                f'<td style="padding:7px 14px;color:#374151;font-size:0.83rem;">{name}</td>'
                f'<td style="padding:7px 14px;color:#6b7280;text-align:right;">{sz_val:.4g}</td>'
                f'<td style="padding:7px 14px;color:#d97706;font-weight:700;text-align:right;">{rz_val:.4g}</td>'
                f'<td style="padding:7px 14px;text-align:right;font-weight:600;'
                f'color:{color};">{sign}{delta:.4g}</td>'
                f'</tr>'
            )

        st.markdown(f"""
<div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;">
<table style="width:100%;border-collapse:collapse;font-size:0.85rem;">
<tr style="background:#f9fafb;">
  <th style="color:#d97706;padding:8px 14px;text-align:left;border-bottom:1px solid #e5e7eb;">Parameter</th>
  <th style="color:#6b7280;padding:8px 14px;text-align:right;border-bottom:1px solid #e5e7eb;">Sizing</th>
  <th style="color:#d97706;padding:8px 14px;text-align:right;border-bottom:1px solid #e5e7eb;">Resizing</th>
  <th style="color:#374151;padding:8px 14px;text-align:right;border-bottom:1px solid #e5e7eb;">Δ</th>
</tr>
{rows_html}
</table>
</div>
""", unsafe_allow_html=True)

    # ── ROW 3: Stress + battery summary ──────────────────────────────────────
    st.markdown("")
    col_s, col_b2 = st.columns([1, 1], gap="large")

    with col_s:
        st.markdown("### D · Structural Summary")
        stress_ok = ss.get("rz_stress_ok",   None)
        clear_ok  = ss.get("rz_clearance_ok",None)
        fos       = ss.get("rz_FoS_actual",  0.0)
        sig       = ss.get("rz_sigma_MPa",   0.0)
        d_bet     = ss.get("rz_d_between_m", 0.0)

        if stress_ok is not None:
            b1 = "converged-badge" if stress_ok else "warn-badge"
            b2 = "converged-badge" if clear_ok  else "warn-badge"
            st.markdown(
                f'<span class="{b1}">{"✓" if stress_ok else "✗"} '
                f'FoS = {fos:.3f}  ·  σ = {sig:.3f} MPa</span>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<span class="{b2}" style="margin-top:6px;display:inline-flex;">{"✓" if clear_ok else "✗"} '
                f'Clearance = {d_bet*1000:.1f} mm</span>',
                unsafe_allow_html=True,
            )
        else:
            st.info("Set arm geometry in R1 · Structure.")

    with col_b2:
        st.markdown("### E · Battery Card")
        SED   = ss.get("rz_SED",    ss.SED)
        V_b   = ss.get("rz_V_batt", ss.V_batt)
        batt_idx = ss.get("rz_selected_batt", -1)
        if batt_idx >= 0 and batt_idx < len(ss.get("rz_batteries", [])):
            b = ss.rz_batteries[batt_idx]
            st.markdown(f"""
<div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:10px;
            padding:14px 18px;font-size:0.84rem;">
  <b style="color:#d97706;">{b.get("Label","—")}</b><br>
  {b.get("Capacity_mAh",0)} mAh &nbsp;·&nbsp;
  {b.get("Cells",3)}S ({V_b:.1f} V) &nbsp;·&nbsp;
  {b.get("Mass_g",0):.1f} g<br>
  SED = <b>{SED:.1f} Wh/kg</b>
</div>
""", unsafe_allow_html=True)
        else:
            st.caption("No battery selected — set in R4.")

    # ── Download ──────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### F · Download Resizing Results")

    p  = _gather_params()
    uav = ss.get("uav_name", "SWIFT UAV")
    csv_rows = {
        "UAV Name":            [uav],
        "MTOW_resizing [kg]":  [f"{rz['M_TO']:.6f}"],
        "Converged":           ["Yes" if rz["converged"] else "No"],
        "Iterations":          [str(rz["n_iterations"])],
        "m_struct [g]":        [f"{rz['m_struct']*1000:.4f}"],
        "m_avi [g]":           [f"{rz['m_avi']*1000:.4f}"],
        "M_prop [g]":          [f"{rz['M_prop']*1000:.4f}"],
        "M_batt [g]":          [f"{rz['M_batt']*1000:.4f}"],
        "T_motor [g]":         [f"{rz['T_motor_g']:.4f}"],
        "P_motor [W]":         [f"{rz['P_motor_W']:.4f}"],
        "P_total [W]":         [f"{rz['P_total_W']:.4f}"],
        "E_req [Wh]":          [f"{rz['E_req_Wh']:.4f}"],
        "C_mAh (raw)":         [f"{rz['C_mAh']:.2f}"],
        "C_mAh (+15%)":        [f"{rz['C_mAh_target']:.2f}"],
        "SED [Wh/kg]":         [f"{p['SED']:.1f}"],
        "V_batt [V]":          [f"{p['V_batt']:.2f}"],
        "t_flight [min]":      [f"{p['t_flight']*60:.1f}"],
        "PL [g/W]":            [f"{p['PL']:.2f}"],
        "n_motors":            [str(p["n_motors"])],
        "FoS_actual":          [f"{ss.get('rz_FoS_actual', 0):.3f}"],
        "stress_ok":           ["Yes" if ss.get("rz_stress_ok") else "No"],
        "clearance_ok":        ["Yes" if ss.get("rz_clearance_ok") else "No"],
        "L_arm [mm]":          [f"{ss.get('rz_L_arm_m',0)*1000:.2f}"],
        "D_prop [mm]":         [f"{ss.get('rz_D_prop_m',0)*1000:.2f}"],
        "config":              [ss.get("rz_config", "Quad X")],
    }

    df_out = pd.DataFrame(csv_rows).T.reset_index()
    df_out.columns = ["Parameter", "Value"]

    buf = io.StringIO()
    df_out.to_csv(buf, index=False)

    st.download_button(
        label="⬇  Download Resizing Results as CSV",
        data=buf.getvalue(),
        file_name=f"swift_resizing_{uav.replace(' ', '_')}.csv",
        mime="text/csv",
    )
