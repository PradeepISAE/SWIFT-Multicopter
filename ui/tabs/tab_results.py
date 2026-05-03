"""
Results tab — convergence plot, mass breakdown bar chart, resizing targets, CSV download.
"""

import streamlit as st
import numpy as np
import pandas as pd
import io
import plotly.graph_objects as go


def _cell_count(v: float) -> str:
    cells = {7.4: "2", 11.1: "3", 14.8: "4", 22.2: "6"}
    for volt, s in cells.items():
        if abs(v - volt) < 0.1:
            return s
    return "?"


def _no_results():
    st.markdown("""
<div style="background:#ffffff;border:1px dashed #e5e7eb;border-radius:12px;
            padding:56px;text-align:center;margin-top:32px;">
    <div style="font-size:2.8rem;margin-bottom:14px;color:#d97706;">⬡</div>
    <div style="color:#1a1a1a;font-size:1.05rem;font-weight:600;">
        No sizing results yet
    </div>
    <div style="color:#6b7280;font-size:0.85rem;margin-top:8px;">
        Complete tabs 01–06 and click <b style="color:#d97706;">▶ Run Sizing</b>
        in the Battery tab to generate results.
    </div>
</div>
""", unsafe_allow_html=True)


def render():
    st.markdown('<div class="section-tag">Sizing Results</div>', unsafe_allow_html=True)
    st.markdown("## 07 · Results")

    r = st.session_state.get("results", None)
    if r is None:
        _no_results()
        return

    uav_name = st.session_state.get("uav_name", "SWIFT UAV")
    n_motors = st.session_state.n_motors
    V_batt   = st.session_state.V_batt

    # ── Convergence badge ────────────────────────────────────────────────────
    if r["converged"]:
        st.markdown(
            f'<span class="converged-badge">✓ Converged &nbsp;·&nbsp; {r["n_iterations"]} iterations'
            f' &nbsp;·&nbsp; |ΔMTOW| &lt; 0.1 g</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="warn-badge">⚠ Not converged — max iterations reached. '
            'Check MF_pay and MF_str values.</span>',
            unsafe_allow_html=True,
        )

    st.markdown(f"**Design:** {uav_name} &nbsp;|&nbsp; {n_motors}× motors &nbsp;|&nbsp; "
                f"{V_batt:.1f} V ({_cell_count(V_batt)}S LiPo) &nbsp;|&nbsp; "
                f"PL = {r['PL']:.4g} g/W")

    st.markdown("---")

    # ────────────────────────────────────────────────────────────────────────
    # ROW 1: Convergence plot  +  Mass bar chart
    # ────────────────────────────────────────────────────────────────────────
    col_conv, col_bar = st.columns([1, 1], gap="large")

    with col_conv:
        st.markdown("### A · Convergence History")
        hist  = r["history"]
        iters = list(range(len(hist)))

        fig_conv = go.Figure()
        fig_conv.add_trace(go.Scatter(
            x=iters, y=hist,
            mode="lines+markers",
            line=dict(color="#d97706", width=2.5),
            marker=dict(size=7, color="#d97706", symbol="circle",
                        line=dict(color="#ffffff", width=1.5)),
            fill="tozeroy",
            fillcolor="rgba(217,119,6,0.06)",
            hovertemplate="Iteration %{x}<br>MTOW = %{y:.4g} kg<extra></extra>",
        ))
        fig_conv.add_hline(
            y=r["M_TO"],
            line_dash="dash", line_color="#6b7280",
            annotation_text=f"Converged: {r['M_TO']:.4g} kg",
            annotation_font_color="#6b7280",
        )
        fig_conv.update_layout(
            paper_bgcolor="#ffffff", plot_bgcolor="#f9fafb",
            font=dict(color="#374151", size=11),
            xaxis=dict(title="Iteration", gridcolor="#e5e7eb", dtick=1,
                       title_font_color="#6b7280"),
            yaxis=dict(title="MTOW [kg]", gridcolor="#e5e7eb",
                       title_font_color="#6b7280"),
            height=320,
            margin=dict(l=10, r=10, t=10, b=10),
            showlegend=False,
        )
        st.plotly_chart(fig_conv, use_container_width=True)

    with col_bar:
        st.markdown("### B · Mass Breakdown")
        labels = ["Payload", "Structure", "Avionics", "Propulsion", "Battery"]
        values = [r["m_pay"], r["m_struct"], r["m_avi"], r["M_prop"], r["M_batt"]]
        M_TO   = r["M_TO"]
        colors = ["#d97706", "#6b7280", "#3b82f6", "#10b981", "#8b5cf6"]

        fig_bar = go.Figure(go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker_color=colors,
            text=[f"{v*1000:.4g} g  ({v/M_TO*100:.1f}%)" for v in values],
            textposition="outside",
            textfont=dict(size=10, color="#374151"),
            hovertemplate="%{y}: %{x:.4g} kg<extra></extra>",
        ))
        fig_bar.add_vline(
            x=M_TO, line_dash="dot", line_color="#d97706",
            annotation_text=f"MTOW = {M_TO:.4g} kg",
            annotation_font_color="#d97706",
        )
        fig_bar.update_layout(
            paper_bgcolor="#ffffff", plot_bgcolor="#f9fafb",
            font=dict(color="#374151", size=11),
            xaxis=dict(title="Mass [kg]", gridcolor="#e5e7eb",
                       title_font_color="#6b7280"),
            yaxis=dict(gridcolor="#e5e7eb"),
            height=320,
            margin=dict(l=10, r=140, t=10, b=10),
            showlegend=False,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # ────────────────────────────────────────────────────────────────────────
    # ROW 2: Mass budget table
    # ────────────────────────────────────────────────────────────────────────
    st.markdown("### Mass Budget")
    budget_rows = [
        ("Payload",     r["m_pay"],    r["m_pay"]    / M_TO * 100),
        ("Structure",   r["m_struct"], r["m_struct"] / M_TO * 100),
        ("Avionics",    r["m_avi"],    r["m_avi"]    / M_TO * 100),
        ("Propulsion",  r["M_prop"],   r["M_prop"]   / M_TO * 100),
        ("Battery",     r["M_batt"],   r["M_batt"]   / M_TO * 100),
    ]
    rows_html = ""
    for name, mass_kg, pct in budget_rows:
        bar_w = int(pct / 2.5)
        rows_html += (
            f'<tr>'
            f'<td style="padding:6px 12px;color:#1a1a1a;">{name}</td>'
            f'<td style="padding:6px 12px;color:#1a1a1a;text-align:right;">{mass_kg*1000:.4g}</td>'
            f'<td style="padding:6px 12px;color:#1a1a1a;text-align:right;">{mass_kg:.4g}</td>'
            f'<td style="padding:6px 12px;color:#6b7280;text-align:right;">{pct:.1f} %</td>'
            f'<td style="padding:6px 12px;">'
            f'<div style="background:#d97706;height:8px;width:{bar_w*8}px;border-radius:4px;"></div>'
            f'</td>'
            f'</tr>'
        )
    rows_html += (
        f'<tr style="border-top:2px solid #e5e7eb;">'
        f'<td style="padding:7px 12px;color:#d97706;font-weight:700;">MTOW (converged)</td>'
        f'<td style="padding:7px 12px;color:#d97706;font-weight:700;text-align:right;">{M_TO*1000:.4g}</td>'
        f'<td style="padding:7px 12px;color:#d97706;font-weight:700;text-align:right;">{M_TO:.4g}</td>'
        f'<td style="padding:7px 12px;color:#d97706;text-align:right;">100.0 %</td>'
        f'<td></td>'
        f'</tr>'
    )
    st.markdown(f"""
<div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;">
<table style="width:100%;border-collapse:collapse;font-size:0.85rem;">
<tr style="background:#f9fafb;">
  <th style="color:#d97706;padding:8px 12px;text-align:left;border-bottom:1px solid #e5e7eb;">Component</th>
  <th style="color:#d97706;padding:8px 12px;text-align:right;border-bottom:1px solid #e5e7eb;">Mass [g]</th>
  <th style="color:#d97706;padding:8px 12px;text-align:right;border-bottom:1px solid #e5e7eb;">Mass [kg]</th>
  <th style="color:#d97706;padding:8px 12px;text-align:right;border-bottom:1px solid #e5e7eb;">Fraction</th>
  <th style="color:#d97706;padding:8px 12px;border-bottom:1px solid #e5e7eb;">Bar</th>
</tr>
{rows_html}
</table>
</div>
""", unsafe_allow_html=True)

    # ────────────────────────────────────────────────────────────────────────
    # ROW 3: Resizing Phase Targets
    # ────────────────────────────────────────────────────────────────────────
    st.markdown("")
    st.markdown('<div class="section-tag" style="margin-top:8px;">Phase 2 — Resizing Targets</div>', unsafe_allow_html=True)
    st.markdown("### C · Target Specifications for Hardware Selection")
    st.caption(
        "Use these values when selecting real motors, ESCs, and batteries in the Resizing Phase."
    )

    targets = [
        ("Converged MTOW",
         f"{M_TO:.4g} kg  ({M_TO*1000:.4g} g)",
         "Final converged maximum take-off mass"),
        ("P_motor_target",
         f"{r['P_motor_W']:.4g} W",
         "Required power per motor at hover (from PL model)"),
        ("T_motor_target at hover",
         f"{r['T_motor_g']:.4g} g",
         "Required hover thrust per motor = MTOW / n_motors × 1000"),
        ("T_at_50 pct throttle",
         f"{r['T_at_50pct_g']:.4g} g",
         "Motor thrust at 50 % of max throttle = T_motor / 2"),
        ("Battery energy",
         f"{r['E_req_Wh']:.4g} Wh",
         "Total energy required for the mission"),
        ("Battery capacity (raw)",
         f"{r['C_mAh']:.4g} mAh",
         "Exact capacity from energy model: C = E_req × 1000 / V_batt"),
        ("Battery capacity (+15 % buffer)",
         f"{r['C_mAh_target']:.4g} mAh",
         "With 15 % safety buffer — use this for hardware selection"),
        ("Power loading used",
         f"{r['PL']:.4g} g/W",
         "Design power loading for this sizing run"),
        ("Operating voltage",
         f"{V_batt:.1f} V  ({_cell_count(V_batt)}S LiPo)",
         "Nominal battery pack voltage"),
        ("Total electrical power",
         f"{r['P_total_W']:.4g} W",
         "Propulsion + avionics + payload power at hover"),
    ]

    tgt_html = ""
    for name, value, note in targets:
        tgt_html += (
            f'<tr>'
            f'<td style="padding:7px 14px;color:#b45309;font-family:monospace;font-size:0.82rem;">{name}</td>'
            f'<td style="padding:7px 14px;color:#d97706;font-weight:700;font-size:0.90rem;">{value}</td>'
            f'<td style="padding:7px 14px;color:#6b7280;font-size:0.79rem;">{note}</td>'
            f'</tr>'
        )

    st.markdown(f"""
<div style="background:#ffffff;border:1px solid #e5e7eb;border-top:2px solid #d97706;
            border-radius:10px;overflow:hidden;">
<table style="width:100%;border-collapse:collapse;">
<tr style="background:#fffbeb;">
  <th style="color:#d97706;padding:9px 14px;text-align:left;font-size:0.70rem;
             letter-spacing:0.10em;text-transform:uppercase;border-bottom:1px solid #e5e7eb;">Parameter</th>
  <th style="color:#d97706;padding:9px 14px;text-align:left;font-size:0.70rem;
             letter-spacing:0.10em;text-transform:uppercase;border-bottom:1px solid #e5e7eb;">Value</th>
  <th style="color:#d97706;padding:9px 14px;text-align:left;font-size:0.70rem;
             letter-spacing:0.10em;text-transform:uppercase;border-bottom:1px solid #e5e7eb;">Notes</th>
</tr>
{tgt_html}
</table>
</div>
""", unsafe_allow_html=True)

    # ────────────────────────────────────────────────────────────────────────
    # ROW 4: PL sweep chart (if available)
    # ────────────────────────────────────────────────────────────────────────
    sweep = st.session_state.get("sweep_results", None)
    if sweep:
        st.markdown("### MTOW vs Power Loading  (PL sweep)")
        pl_arr  = [s["PL"] for s in sweep]
        mto_arr = [s["M_TO"] for s in sweep]
        bat_arr = [s["M_batt"] for s in sweep]
        pro_arr = [s["M_prop"] for s in sweep]

        fig_sw = go.Figure()
        fig_sw.add_trace(go.Scatter(
            x=pl_arr, y=mto_arr,
            mode="lines+markers",
            line=dict(color="#d97706", width=2.5),
            marker=dict(size=9, color="#d97706"),
            name="MTOW",
            hovertemplate="PL=%{x:.1f} g/W<br>MTOW=%{y:.4g} kg<extra></extra>",
        ))
        fig_sw.add_trace(go.Scatter(
            x=pl_arr, y=bat_arr,
            mode="lines+markers",
            line=dict(color="#6b7280", width=1.5, dash="dash"),
            marker=dict(size=7, color="#6b7280"),
            name="M_batt",
            hovertemplate="PL=%{x:.1f} g/W<br>M_batt=%{y:.4g} kg<extra></extra>",
        ))
        fig_sw.add_trace(go.Scatter(
            x=pl_arr, y=pro_arr,
            mode="lines+markers",
            line=dict(color="#3b82f6", width=1.5, dash="dot"),
            marker=dict(size=7, color="#3b82f6"),
            name="M_prop",
            hovertemplate="PL=%{x:.1f} g/W<br>M_prop=%{y:.4g} kg<extra></extra>",
        ))
        fig_sw.add_vline(
            x=r["PL"], line_dash="dash", line_color="#16a34a",
            annotation_text=f"Design: {r['PL']:.1f} g/W",
            annotation_font_color="#16a34a",
        )
        fig_sw.update_layout(
            paper_bgcolor="#ffffff", plot_bgcolor="#f9fafb",
            font=dict(color="#374151", size=11),
            xaxis=dict(title="Power loading PL [g/W]", gridcolor="#e5e7eb",
                       title_font_color="#6b7280"),
            yaxis=dict(title="Mass [kg]", gridcolor="#e5e7eb",
                       title_font_color="#6b7280"),
            legend=dict(bgcolor="#ffffff", bordercolor="#e5e7eb", borderwidth=1),
            height=340,
            margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig_sw, use_container_width=True)

        sweep_df = pd.DataFrame({
            "PL [g/W]":          [f"{s['PL']:.1f}" for s in sweep],
            "MTOW [kg]":         [f"{s['M_TO']:.4g}" for s in sweep],
            "M_batt [g]":        [f"{s['M_batt']*1000:.4g}" for s in sweep],
            "M_prop [g]":        [f"{s['M_prop']*1000:.4g}" for s in sweep],
            "P_motor [W]":       [f"{s['P_motor_W']:.4g}" for s in sweep],
            "E_req [Wh]":        [f"{s['E_req_Wh']:.4g}" for s in sweep],
            "C_batt+15% [mAh]":  [f"{s['C_mAh_target']:.4g}" for s in sweep],
            "Converged":         ["✓" if s["converged"] else "✗" for s in sweep],
        })
        st.dataframe(sweep_df, use_container_width=True, hide_index=True)

    # ────────────────────────────────────────────────────────────────────────
    # ROW 5: Download CSV
    # ────────────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### D · Download Results")

    ss = st.session_state
    csv_rows = {
        "UAV Name":                   [uav_name],
        "MTOW [kg]":                  [f"{M_TO:.6f}"],
        "MTOW [g]":                   [f"{M_TO*1000:.4f}"],
        "Converged":                  ["Yes" if r["converged"] else "No"],
        "Iterations":                 [str(r["n_iterations"])],
        # Mass breakdown
        "m_pay [g]":                  [f"{r['m_pay']*1000:.4f}"],
        "m_struct [g]":               [f"{r['m_struct']*1000:.4f}"],
        "m_avi [g]":                  [f"{r['m_avi']*1000:.4f}"],
        "M_prop [g]":                 [f"{r['M_prop']*1000:.4f}"],
        "M_batt [g]":                 [f"{r['M_batt']*1000:.4f}"],
        # Propulsion / power
        "T_motor_hover [g]":          [f"{r['T_motor_g']:.4f}"],
        "T_at_50pct [g]":             [f"{r['T_at_50pct_g']:.4f}"],
        "P_motor [W]":                [f"{r['P_motor_W']:.4f}"],
        "P_total [W]":                [f"{r['P_total_W']:.4f}"],
        # Battery
        "E_req [Wh]":                 [f"{r['E_req_Wh']:.4f}"],
        "C_mAh (raw)":                [f"{r['C_mAh']:.2f}"],
        "C_mAh (+15%)":               [f"{r['C_mAh_target']:.2f}"],
        # Inputs
        "n_motors":                   [str(ss.n_motors)],
        "t_flight [min]":             [f"{ss.t_flight_min:.1f}"],
        "MF_pay":                     [f"{ss.MF_pay:.4f}"],
        "MF_str":                     [f"{ss.MF_str:.4f}"],
        "MF_avi":                     [f"{ss.MF_avi:.4f}"],
        "M_motor [g]":                [f"{ss.M_motor_g:.2f}"],
        "M_prop_per [g]":             [f"{ss.M_prop_g:.2f}"],
        "V_batt [V]":                 [f"{ss.V_batt:.1f}"],
        "SED [Wh/kg]":                [f"{ss.SED:.1f}"],
        "DoD":                        [f"{ss.DoD:.3f}"],
        "eta_elec":                   [f"{ss.eta_elec:.3f}"],
        "PL [g/W]":                   [f"{r['PL']:.2f}"],
        "P_avi [W]":                  [f"{ss.P_avi:.2f}"],
        "P_pay [W]":                  [f"{ss.P_pay:.2f}"],
    }

    df_out = pd.DataFrame(csv_rows).T.reset_index()
    df_out.columns = ["Parameter", "Value"]

    buf = io.StringIO()
    df_out.to_csv(buf, index=False)
    csv_str = buf.getvalue()

    st.download_button(
        label="⬇  Download Results as CSV",
        data=csv_str,
        file_name=f"swift_sizing_{uav_name.replace(' ', '_')}.csv",
        mime="text/csv",
        help="Download all sizing inputs and results as a CSV file.",
    )

    st.caption(
        f"Results for: **{uav_name}** &nbsp;·&nbsp; MTOW = {M_TO:.4g} kg &nbsp;·&nbsp; "
        f"{r['n_iterations']} iterations"
    )
