"""
Resizing Phase — Results (R8).
Fixed-point resizing loop with real hardware. Six result sections.
"""
import io
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from resizing.convergence_resizing import run_resizing
from resizing.structure_resizing import MATERIALS


def _gather_params(ss):
    mat = ss.get("resizing_material", "CF tube/rod")
    if mat == "Custom":
        rho          = ss.get("resizing_rho_custom", 1600.0)
        sigma_allow  = ss.get("resizing_sigma_custom", 600.0) * 1e6
    else:
        m = MATERIALS.get(mat, MATERIALS["CF tube/rod"])
        rho         = m["rho"]
        sigma_allow = m["sigma_allow_MPa"] * 1e6

    return {
        "m_pay":             ss.get("m_pay",  0.030),
        "MF_pay":            ss.get("MF_pay", 0.20),
        "M_avi_fixed":       ss.get("resizing_M_avi",    0.030),
        "M_prop_fixed":      ss.get("resizing_M_prop",   0.020),
        "n_motors":          int(ss.get("n_motors", 4)),
        "PL_50pct_gW":       ss.get("resizing_PL_50pct_gW", 4.0),
        "P_avi_W":           ss.get("resizing_P_avi",    1.3),
        "P_pay_W":           ss.get("P_pay",             1.0),
        "segments":          ss.get("resizing_mission_segments", {
            "takeoff": {"active": True,  "duration_min": 0.5,  "a_TO_ms2": 19.62},
            "climb":   {"active": False, "duration_min": 2.0},
            "cruise":  {"active": False, "duration_min": 5.0},
            "hover":   {"active": True,  "duration_min": 20.0},
            "land":    {"active": True,  "duration_min": 0.5,  "k_land": 0.5},
        }),
        "E_cruise_Wh":       ss.get("resizing_E_cruise_Wh", 0.0),
        "SED":               ss.get("resizing_SED",      150.0),
        "DoD":               ss.get("resizing_DoD",      0.85),
        "eta_elec":          ss.get("resizing_eta_elec", 0.85),
        "V_batt":            ss.get("resizing_V_batt",   11.1),
        "a_TO_ms2":          ss.get("resizing_a_TO_ms2", 19.62),
        "k_arm":             ss.get("resizing_k_arm",    1.2),
        "D_prop_m":          ss.get("resizing_D_prop_m", 0.127),
        "cs_type":           ss.get("resizing_cross_section", "Circular Hollow Tube"),
        "k_ratio":           ss.get("resizing_k_ratio",  0.7),
        "b_plate_m":         ss.get("resizing_b_plate_m", 0.012),
        "rho":               rho,
        "sigma_allow_Pa":    sigma_allow,
        "FoS":               ss.get("resizing_FoS",      1.5),
        "M_struct_sizing_kg": ss.get("resizing_M_struct_sizing",
                               ss.get("m_struct_sizing", 0.05)),
    }


def render():
    st.markdown('<div class="section-tag">Resizing Phase · Results</div>',
                unsafe_allow_html=True)
    st.markdown("## R8 · Resizing Results")

    ss = st.session_state

    # ── Run button ────────────────────────────────────────────────────────────
    btn_col, status_col = st.columns([1, 3], gap="medium")
    with btn_col:
        run_clicked = st.button(
            "Run Resizing",
            help="Run fixed-point mass convergence with real hardware.",
            use_container_width=True,
        )

    if run_clicked:
        params = _gather_params(ss)
        with st.spinner("Running resizing convergence…"):
            try:
                rz = run_resizing(params)
                ss.resizing_results = rz
                ss.resizing_done    = True
                ss.resizing_MTOW_converged = rz["M_TO"]
            except Exception as exc:
                st.error(f"Convergence failed: {exc}")

    with status_col:
        rz = ss.get("resizing_results")
        if rz is not None:
            if rz["converged"]:
                st.markdown(
                    f'<span class="converged-badge">✓ Converged in {rz["n_iterations"]} iterations'
                    f'  ·  MTOW = {rz["M_TO"]:.4g} kg  ({rz["M_TO"]*1000:.1f} g)</span>',
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

    rz = ss.get("resizing_results")
    if rz is None:
        st.markdown("""
<div style="background:#ffffff;border:1px dashed #e5e7eb;border-radius:12px;
            padding:48px;text-align:center;margin-top:24px;">
  <div style="font-size:2.4rem;color:#d97706;margin-bottom:12px;">⬡</div>
  <div style="color:#1a1a1a;font-size:1.0rem;font-weight:600;">Set R1–R6 first</div>
  <div style="color:#6b7280;font-size:0.83rem;margin-top:6px;">
    Define mission, avionics, propulsion, structure, battery, and layout,
    then click <b style="color:#d97706;">▶ Run Resizing</b>.
  </div>
</div>
""", unsafe_allow_html=True)
        return

    st.markdown("---")

    # ── A: Quick metrics ──────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5, gap="small")
    c1.metric("MTOW",       f"{rz['M_TO']:.4g} kg")
    c2.metric("M_batt",     f"{rz['M_batt']*1000:.1f} g")
    c3.metric("E_total",    f"{rz['E_total_Wh']:.3f} Wh")
    c4.metric("C_target",   f"{rz['C_target_mAh']:.0f} mAh")
    c5.metric("P_motors",   f"{rz['P_motors_W']:.2f} W")

    st.markdown("---")

    # ── B: Convergence + mass breakdown ───────────────────────────────────────
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
            hovertemplate="Iter %{x}<br>MTOW = %{y:.4g} kg<extra></extra>",
        ))
        fig_c.add_hline(y=rz["M_TO"], line_dash="dash", line_color="#6b7280",
                        annotation_text=f"MTOW* = {rz['M_TO']:.4g} kg",
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
        values = [
            rz.get("m_pay",    0.0),
            rz.get("m_struct", 0.0),
            rz.get("m_avi",    0.0),
            rz.get("M_prop",   0.0),
            rz.get("M_batt",   0.0),
        ]
        M_TO   = rz["M_TO"]
        colors = ["#d97706", "#6b7280", "#3b82f6", "#10b981", "#8b5cf6"]

        fig_b = go.Figure(go.Bar(
            x=values, y=labels, orientation="h",
            marker_color=colors,
            text=[f"{v*1000:.1f} g  ({v/M_TO*100:.1f}%)" if M_TO > 0 else ""
                  for v in values],
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
            height=300, margin=dict(l=10, r=160, t=10, b=10), showlegend=False,
        )
        st.plotly_chart(fig_b, use_container_width=True)

    # ── C: Segment energy breakdown ───────────────────────────────────────────
    E_segs = rz.get("E_segments", {})
    if E_segs:
        st.markdown("### C · Segment Energy")
        _SEG_COLORS = {"takeoff": "#d97706", "climb": "#3b82f6", "cruise": "#10b981",
                       "hover": "#6b7280", "land": "#8b5cf6"}
        _SEG_LABELS = {"takeoff": "Takeoff", "climb": "Climb", "cruise": "Cruise",
                       "hover": "Hover", "land": "Land"}
        E_total = rz.get("E_total_Wh", 1.0)
        names = [_SEG_LABELS.get(k, k) for k, v in E_segs.items() if v > 0]
        vals  = [v for v in E_segs.values() if v > 0]
        clrs  = [_SEG_COLORS.get(k, "#6b7280") for k, v in E_segs.items() if v > 0]
        if vals:
            fig_e = go.Figure(go.Pie(
                labels=names, values=vals,
                marker_colors=clrs,
                textinfo="label+percent",
                textfont=dict(size=11),
                hovertemplate="%{label}: %{value:.3f} Wh (%{percent})<extra></extra>",
            ))
            fig_e.update_layout(
                paper_bgcolor="#ffffff",
                font=dict(color="#374151", size=11),
                height=260,
                margin=dict(l=10, r=10, t=10, b=10),
                showlegend=True,
                legend=dict(bgcolor="#ffffff", bordercolor="#e5e7eb", borderwidth=1),
            )
            st.plotly_chart(fig_e, use_container_width=True)

    # ── D: Sizing vs Resizing comparison ──────────────────────────────────────
    if ss.get("sizing_done", False) and ss.get("results"):
        sz = ss.results
        st.markdown("### D · Sizing vs Resizing")

        comp_rows = [
            ("MTOW [kg]",       sz.get("M_TO", 0),         rz["M_TO"]),
            ("M_struct [g]",    sz.get("m_struct", 0)*1000, rz.get("m_struct", 0)*1000),
            ("M_avi [g]",       sz.get("m_avi", 0)*1000,    rz.get("m_avi", 0)*1000),
            ("M_prop [g]",      sz.get("M_prop", 0)*1000,   rz.get("M_prop", 0)*1000),
            ("M_batt [g]",      sz.get("M_batt", 0)*1000,   rz.get("M_batt", 0)*1000),
            ("P_motor [W]",     sz.get("P_motor_W", 0),     rz.get("P_motor_W", 0)),
            ("E_total [Wh]",    sz.get("E_req_Wh", 0),      rz.get("E_total_Wh", 0)),
            ("C_target [mAh]",  sz.get("C_mAh_target", 0),  rz.get("C_target_mAh", 0)),
        ]

        rows_html = ""
        for name, sz_val, rz_val in comp_rows:
            delta = rz_val - sz_val
            sign  = "+" if delta >= 0 else ""
            color = "#dc2626" if delta > 1e-9 else "#16a34a"
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

    # ── E: Structural + battery summary ───────────────────────────────────────
    col_s, col_b2 = st.columns([1, 1], gap="large")

    with col_s:
        st.markdown("### E · Structural Summary")
        struct_dims = rz.get("struct_dims", {})
        stress_ok   = struct_dims.get("passed",    None)
        FoS_act     = struct_dims.get("FoS_actual", 0.0)
        sigma_MPa   = struct_dims.get("sigma_root_Pa", 0.0) / 1e6
        d_out_mm    = struct_dims.get("d_out_m", struct_dims.get("b_out_m",
                      struct_dims.get("h_m", 0.0))) * 1000.0
        L_arm_mm    = rz.get("L_arm_m", 0.0) * 1000.0

        if stress_ok is not None:
            badge = "converged-badge" if stress_ok else "warn-badge"
            st.markdown(
                f'<span class="{badge}">{"✓" if stress_ok else "✗"} '
                f'FoS = {FoS_act:.3f}  ·  σ = {sigma_MPa:.3f} MPa</span>',
                unsafe_allow_html=True,
            )
        st.markdown(f"""
<div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:10px;
            padding:12px 16px;margin-top:8px;font-size:0.83rem;">
  L_arm = {L_arm_mm:.1f} mm &nbsp;·&nbsp; dim = {d_out_mm:.2f} mm<br>
  M_arms = {rz.get("M_arms",0)*1000:.2f} g &nbsp;·&nbsp;
  M_body = {rz.get("M_body",0)*1000:.2f} g<br>
  M_struct = {rz.get("m_struct",0)*1000:.2f} g
</div>
""", unsafe_allow_html=True)

    with col_b2:
        st.markdown("### F · Battery Card")
        batt_idx = ss.get("resizing_selected_batt_idx", -1)
        if batt_idx >= 0 and batt_idx < len(ss.get("resizing_batteries", [])):
            b = ss.resizing_batteries[batt_idx]
            SED   = ss.get("resizing_SED",    150.0)
            V_b   = ss.get("resizing_V_batt", 11.1)
            st.markdown(f"""
<div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:10px;
            padding:14px 18px;font-size:0.84rem;">
  <b style="color:#d97706;">{b.get("Label","—")}</b><br>
  {b.get("Capacity_mAh",0)} mAh &nbsp;·&nbsp;
  {b.get("Cells",3)}S ({V_b:.1f} V) &nbsp;·&nbsp;
  {b.get("Mass_g",0):.1f} g<br>
  SED = <b>{SED:.1f} Wh/kg</b> &nbsp;·&nbsp;
  M_batt (loop) = <b>{rz.get("M_batt",0)*1000:.1f} g</b>
</div>
""", unsafe_allow_html=True)
        else:
            st.caption("No battery selected — set in R5.")

    # ── G: Download ───────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### G · Download Results")

    p   = _gather_params(ss)
    uav = ss.get("uav_name", "SWIFT UAV")
    csv_rows = {
        "UAV Name":               [uav],
        "MTOW_resizing [kg]":     [f"{rz['M_TO']:.6f}"],
        "Converged":              ["Yes" if rz["converged"] else "No"],
        "Iterations":             [str(rz["n_iterations"])],
        "m_struct [g]":           [f"{rz.get('m_struct',0)*1000:.4f}"],
        "M_arms [g]":             [f"{rz.get('M_arms',0)*1000:.4f}"],
        "M_body [g]":             [f"{rz.get('M_body',0)*1000:.4f}"],
        "m_avi [g]":              [f"{rz.get('m_avi',0)*1000:.4f}"],
        "M_prop [g]":             [f"{rz.get('M_prop',0)*1000:.4f}"],
        "M_batt [g]":             [f"{rz.get('M_batt',0)*1000:.4f}"],
        "T_motor [g]":            [f"{rz.get('T_motor_g',0):.4f}"],
        "P_motor [W]":            [f"{rz.get('P_motor_W',0):.4f}"],
        "P_motors_total [W]":     [f"{rz.get('P_motors_W',0):.4f}"],
        "E_total [Wh]":           [f"{rz.get('E_total_Wh',0):.4f}"],
        "C_req [mAh]":            [f"{rz.get('C_req_mAh',0):.2f}"],
        "C_target +15% [mAh]":    [f"{rz.get('C_target_mAh',0):.2f}"],
        "L_arm [mm]":             [f"{rz.get('L_arm_m',0)*1000:.2f}"],
        "D_prop [mm]":            [f"{p['D_prop_m']*1000:.2f}"],
        "k_arm":                  [f"{p['k_arm']:.3f}"],
        "k_ratio":                [f"{p['k_ratio']:.3f}"],
        "SED [Wh/kg]":            [f"{p['SED']:.1f}"],
        "DoD":                    [f"{p['DoD']:.3f}"],
        "eta_elec":               [f"{p['eta_elec']:.3f}"],
        "V_batt [V]":             [f"{p['V_batt']:.2f}"],
        "FoS_required":           [f"{p['FoS']:.2f}"],
        "n_motors":               [str(p["n_motors"])],
        "cs_type":                [p["cs_type"]],
        "material":               [ss.get("resizing_material","CF tube/rod")],
        "config":                 [ss.get("resizing_config","Quad X")],
    }

    df_out = pd.DataFrame(csv_rows).T.reset_index()
    df_out.columns = ["Parameter", "Value"]

    buf = io.StringIO()
    df_out.to_csv(buf, index=False)

    st.download_button(
        label="Download Resizing Results (CSV)",
        data=buf.getvalue(),
        file_name=f"swift_resizing_{uav.replace(' ', '_')}.csv",
        mime="text/csv",
    )
