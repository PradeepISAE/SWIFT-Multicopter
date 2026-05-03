"""
Resizing Phase — Optimisation tab.
SLSQP: minimise MTOW over [k_arm, dim1_mm, dim2_mm] subject to structural,
clearance, and feasibility constraints.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from resizing.optimisation import run_optimisation
from resizing.structure_resizing import MATERIALS


def _gather_base_params():
    """Collect base_params dict expected by run_optimisation."""
    ss = st.session_state
    return {
        "m_pay":           ss.m_pay,
        "MF_pay":          ss.MF_pay,
        "M_struct_fixed":  ss.get("rz_M_struct_fixed", 0.05),
        "M_avi_fixed":     ss.get("rz_M_avi_fixed",    0.03),
        "M_prop_fixed":    ss.get("rz_M_prop_fixed",   0.02),
        "n_motors":        int(ss.n_motors),
        "PL":              ss.get("rz_PL",             ss.PL),
        "P_avi":           ss.get("rz_P_avi_W",        ss.P_avi),
        "P_pay":           ss.P_pay,
        "t_flight":        ss.get("rz_t_flight_min",   ss.t_flight_min) / 60.0,
        "SED":             ss.get("rz_SED",            ss.SED),
        "DoD":             ss.get("rz_DoD",            ss.DoD),
        "eta_elec":        ss.get("rz_eta_elec",       ss.eta_elec),
        "V_batt":          ss.get("rz_V_batt",         ss.V_batt),
        # extra keys required by optimisation
        "M_struct_sizing": ss.get("m_struct_sizing",   0.05),
        "T_50pct_N":       ss.get("t_motor_50pct_target", 0.0) * 9.81 / 1000.0,
    }


def render():
    st.markdown('<div class="section-tag">Resizing Phase · Optimisation</div>',
                unsafe_allow_html=True)
    st.markdown("## R7 · SLSQP Optimisation")

    st.markdown("""
<div class="info-box">
Minimises MTOW by tuning arm geometry <b>[k_arm, dim1, dim2]</b> subject to:<br>
① Structural FoS ≥ FoS_req &nbsp;·&nbsp;
② Prop-to-prop clearance &gt; D_prop + margin &nbsp;·&nbsp;
③ T_50pct × n_motors ≥ MTOW × g × 2
</div>
""", unsafe_allow_html=True)

    ss = st.session_state

    # ── Configuration ─────────────────────────────────────────────────────────
    col_cs, col_mat = st.columns([1, 1], gap="large")

    with col_cs:
        st.markdown("**Cross-section (optimised)**")
        cs_type = st.selectbox(
            "Cross-section", ["Circular tube", "Square tube", "Flat plate"],
            index=["Circular tube", "Square tube", "Flat plate"].index(
                ss.get("rz_cs_type", "Circular tube")),
            key="_opt_cs",
        )

        if cs_type == "Circular tube":
            dim1_label = "Outer diameter d_outer [mm]"
            dim2_label = "Wall thickness t_wall [mm]"
        elif cs_type == "Square tube":
            dim1_label = "Outer side b_outer [mm]"
            dim2_label = "Wall thickness t_wall [mm]"
        else:
            dim1_label = "Width b [mm]"
            dim2_label = "Height h [mm]"

    with col_mat:
        st.markdown("**Material**")
        mat_keys = [k for k in MATERIALS if MATERIALS[k]["rho"] is not None]
        mat = st.selectbox("Material", mat_keys,
                           index=mat_keys.index(ss.get("rz_material", "CF tube"))
                           if ss.get("rz_material", "CF tube") in mat_keys else 0,
                           key="_opt_mat")
        rho         = MATERIALS[mat]["rho"]
        sigma_allow = MATERIALS[mat]["sigma_allow_MPa"]
        st.caption(f"ρ = {rho:.0f} kg/m³  ·  σ_allow = {sigma_allow:.0f} MPa")

    st.markdown("**Design bounds**")

    D_prop_m = ss.get("rz_D_prop_m", 0.127)

    col_k, col_d1, col_d2 = st.columns(3, gap="medium")
    with col_k:
        k_lo = st.number_input("k_arm min", 1.2, 4.0,
                               float(ss.get("opt_k_lo", 1.5)), 0.1, format="%.1f", key="_opt_klo")
        k_hi = st.number_input("k_arm max", 1.5, 8.0,
                               float(ss.get("opt_k_hi", 4.0)), 0.1, format="%.1f", key="_opt_khi")
        k0   = st.number_input("k_arm init", k_lo, k_hi,
                               float(ss.get("opt_k0",  2.5)), 0.1, format="%.1f", key="_opt_k0")
    with col_d1:
        d1_lo = st.number_input(f"{dim1_label} min", 1.0, 40.0,
                                float(ss.get("opt_d1_lo", 6.0)), 0.5, format="%.1f", key="_opt_d1lo")
        d1_hi = st.number_input(f"{dim1_label} max", 2.0, 80.0,
                                float(ss.get("opt_d1_hi", 20.0)), 0.5, format="%.1f", key="_opt_d1hi")
        d1_0  = st.number_input(f"{dim1_label} init", d1_lo, d1_hi,
                                float(ss.get("opt_d1_0", 10.0)), 0.5, format="%.1f", key="_opt_d10")
    with col_d2:
        d2_lo = st.number_input(f"{dim2_label} min", 0.2, 10.0,
                                float(ss.get("opt_d2_lo", 0.5)), 0.1, format="%.1f", key="_opt_d2lo")
        d2_hi = st.number_input(f"{dim2_label} max", 0.5, 20.0,
                                float(ss.get("opt_d2_hi", 3.0)), 0.1, format="%.1f", key="_opt_d2hi")
        d2_0  = st.number_input(f"{dim2_label} init", d2_lo, d2_hi,
                                float(ss.get("opt_d2_0", 1.0)), 0.1, format="%.1f", key="_opt_d20")

    ss.opt_k_lo  = k_lo;  ss.opt_k_hi  = k_hi;  ss.opt_k0  = k0
    ss.opt_d1_lo = d1_lo; ss.opt_d1_hi = d1_hi; ss.opt_d1_0 = d1_0
    ss.opt_d2_lo = d2_lo; ss.opt_d2_hi = d2_hi; ss.opt_d2_0 = d2_0

    FoS_req    = st.number_input("Required FoS", 1.0, 5.0,
                                  float(ss.get("rz_FoS_req", 1.5)), 0.1,
                                  format="%.1f", key="_opt_fos")
    c_margin_m = ss.get("rz_c_margin_mm", 10.0) / 1000.0

    # ── T_max from selected motor ─────────────────────────────────────────────
    motors = ss.get("rz_motors", [])
    mi     = ss.get("rz_active_motor", 0)
    T_max_N = (float(motors[mi].get("T_max_g", 0) or 0) * 9.81 / 1000.0
               if motors and mi < len(motors) else 0.0)

    # ── Run button ────────────────────────────────────────────────────────────
    st.markdown("---")
    if st.button("▶  Run Optimisation", use_container_width=False):
        base_params = _gather_base_params()
        x0     = [k0, d1_0, d2_0]
        bounds = [(k_lo, k_hi), (d1_lo, d1_hi), (d2_lo, d2_hi)]

        with st.spinner("Running SLSQP optimisation…"):
            res, history = run_optimisation(
                base_params, cs_type, rho, sigma_allow,
                T_max_N, D_prop_m,
                x0, bounds, FoS_req, c_margin_m,
            )
        ss.rz_opt_result  = {
            "success":  res.success,
            "message":  res.message,
            "fun":      float(res.fun),
            "x":        res.x.tolist(),
            "nit":      int(res.nit),
        }
        ss.rz_opt_history = history

    # ── Results ───────────────────────────────────────────────────────────────
    opt = ss.get("rz_opt_result")
    if opt is None:
        st.info("Click ▶ Run Optimisation to find the minimum-MTOW arm geometry.")
        return

    badge = "converged-badge" if opt["success"] else "warn-badge"
    sym   = "✓" if opt["success"] else "✗"
    st.markdown(
        f'<span class="{badge}">{sym} {opt["message"]} &nbsp;·&nbsp;'
        f' {opt["nit"]} iterations &nbsp;·&nbsp;'
        f' MTOW* = {opt["fun"]:.4g} kg</span>',
        unsafe_allow_html=True,
    )

    k_opt, d1_opt, d2_opt = opt["x"]
    L_opt = k_opt * D_prop_m / 2.0

    st.markdown(f"""
<div style="background:#ffffff;border:1px solid #e5e7eb;border-top:2px solid #d97706;
            border-radius:10px;padding:16px 20px;margin-top:12px;">
  <b style="color:#d97706;">Optimal geometry</b><br><br>
  k_arm = <b>{k_opt:.3f}</b> &nbsp;→&nbsp; L_arm = <b>{L_opt*1000:.2f} mm</b><br>
  {dim1_label.split("[")[0].strip()} = <b>{d1_opt:.2f} mm</b><br>
  {dim2_label.split("[")[0].strip()} = <b>{d2_opt:.2f} mm</b><br>
  MTOW* = <b style="color:#d97706;">{opt["fun"]:.4g} kg ({opt["fun"]*1000:.4g} g)</b>
</div>
""", unsafe_allow_html=True)

    # Iteration history
    history = ss.get("rz_opt_history", [])
    if history:
        st.markdown("### Optimisation History")
        df_hist = pd.DataFrame(history)

        fig_h = go.Figure()
        fig_h.add_trace(go.Scatter(
            x=df_hist["iter"], y=df_hist["MTOW"],
            mode="lines+markers",
            line=dict(color="#d97706", width=2),
            marker=dict(size=6, color="#d97706"),
            hovertemplate="Iter %{x}: MTOW=%{y:.4g} kg<extra></extra>",
        ))
        fig_h.update_layout(
            paper_bgcolor="#ffffff", plot_bgcolor="#f9fafb",
            font=dict(color="#374151", size=11),
            xaxis=dict(title="Iteration", gridcolor="#e5e7eb",
                       title_font_color="#6b7280"),
            yaxis=dict(title="MTOW [kg]", gridcolor="#e5e7eb",
                       title_font_color="#6b7280"),
            height=280, margin=dict(l=10, r=10, t=10, b=10), showlegend=False,
        )
        st.plotly_chart(fig_h, use_container_width=True)

        df_disp = df_hist.copy()
        df_disp["k_arm"]  = df_disp["k_arm"].map("{:.3f}".format)
        df_disp["dim1"]   = df_disp["dim1"].map("{:.2f}".format)
        df_disp["dim2"]   = df_disp["dim2"].map("{:.2f}".format)
        df_disp["MTOW"]   = df_disp["MTOW"].map("{:.4g}".format)
        df_disp.columns   = ["Iter", "k_arm", dim1_label[:10], dim2_label[:10], "MTOW [kg]"]
        st.dataframe(df_disp, use_container_width=True, hide_index=True)
