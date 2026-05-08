"""
Resizing Phase — Optimisation (R9).
SLSQP: minimise MTOW over [k_arm, k_ratio] with 4 constraints.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from resizing.optimisation import run_optimisation
from resizing.structure_resizing import MATERIALS


def _gather_base_params(ss):
    mat = ss.get("resizing_material", "CF tube/rod")
    if mat == "Custom":
        rho         = ss.get("resizing_rho_custom", 1600.0)
        sigma_allow = ss.get("resizing_sigma_custom", 600.0) * 1e6
    else:
        m = MATERIALS.get(mat, MATERIALS["CF tube/rod"])
        rho         = m["rho"]
        sigma_allow = m["sigma_allow_MPa"] * 1e6

    return {
        "m_pay":          ss.get("m_pay",  0.030),
        "MF_pay":         ss.get("MF_pay", 0.20),
        "M_avi_fixed":    ss.get("resizing_M_avi",    0.030),
        "M_prop_fixed":   ss.get("resizing_M_prop",   0.020),
        "n_motors":       int(ss.get("n_motors", 4)),
        "PL_50pct_gW":    ss.get("resizing_PL_50pct_gW", 4.0),
        "P_avi_W":        ss.get("resizing_P_avi",    1.3),
        "P_pay_W":        ss.get("P_pay",             1.0),
        "segments":       ss.get("resizing_mission_segments", {
            "takeoff": {"active": True,  "duration_min": 0.5,  "a_TO_ms2": 19.62},
            "climb":   {"active": False, "duration_min": 2.0},
            "cruise":  {"active": False, "duration_min": 0.0},
            "hover":   {"active": True,  "duration_min": 20.0},
            "land":    {"active": True,  "duration_min": 0.5,  "k_land": 0.5},
        }),
        "E_cruise_Wh":    ss.get("resizing_E_cruise_Wh", 0.0),
        "SED":            ss.get("resizing_SED",      150.0),
        "DoD":            ss.get("resizing_DoD",      0.85),
        "eta_elec":       ss.get("resizing_eta_elec", 0.85),
        "V_batt":         ss.get("resizing_V_batt",   11.1),
        "a_TO_ms2":       ss.get("resizing_a_TO_ms2", 19.62),
        "D_prop_m":       ss.get("resizing_D_prop_m", 0.127),
        "cs_type":        ss.get("resizing_cross_section", "Circular Hollow Tube"),
        "b_plate_m":      ss.get("resizing_b_plate_m", 0.012),
        "rho":            rho,
        "sigma_allow_Pa": sigma_allow,
        "FoS":            ss.get("resizing_FoS", 1.5),
        "M_struct_sizing_kg": ss.get("resizing_M_struct_sizing",
                                ss.get("m_struct_sizing", 0.05)),
        # These are pass-through keys used by optimisation constraint builders
        "k_arm":   ss.get("resizing_k_arm",   1.2),
        "k_ratio": ss.get("resizing_k_ratio",  0.7),
    }


def render():
    st.markdown('<div class="section-tag">Resizing Phase · Optimisation</div>',
                unsafe_allow_html=True)
    st.markdown("## R9 · SLSQP Optimisation")

    st.markdown("""
<div class="info-box">
<b>Minimise MTOW</b> by tuning arm geometry <b>x = [k_arm, k_ratio]</b> subject to:<br>
① σ_allow/FoS − σ_root ≥ 0 &nbsp;(structural FoS)<br>
② d_between − D_prop − margin ≥ 0 &nbsp;(propeller clearance)<br>
③ T_100pct × n − TW_req × MTOW × g ≥ 0 &nbsp;(thrust-to-weight)<br>
④ M_struct_sizing − M_arms ≥ 0 &nbsp;(positive body mass)
</div>
""", unsafe_allow_html=True)

    ss = st.session_state

    # ── Problem configuration ─────────────────────────────────────────────────
    col_dv, col_const = st.columns([1, 1], gap="large")

    with col_dv:
        st.markdown("**Design variable bounds**")
        col_a, col_b = st.columns(2)
        with col_a:
            k_arm_lo = st.number_input("k_arm  min", 0.8, 3.0,
                                       float(ss.get("opt_k_lo", 1.0)), 0.1,
                                       format="%.2f", key="_opt_klo")
            k_arm_hi = st.number_input("k_arm  max", 1.0, 6.0,
                                       float(ss.get("opt_k_hi", 3.0)), 0.1,
                                       format="%.2f", key="_opt_khi")
            k_arm_0  = st.number_input("k_arm  init", k_arm_lo, k_arm_hi,
                                       float(ss.get("resizing_k_arm", 1.2)), 0.05,
                                       format="%.2f", key="_opt_k0")
        with col_b:
            k_rat_lo = st.number_input("k_ratio min", 0.10, 0.80,
                                       float(ss.get("opt_kr_lo", 0.30)), 0.05,
                                       format="%.2f", key="_opt_krlo")
            k_rat_hi = st.number_input("k_ratio max", 0.30, 0.95,
                                       float(ss.get("opt_kr_hi", 0.90)), 0.05,
                                       format="%.2f", key="_opt_krhi")
            k_rat_0  = st.number_input("k_ratio init", k_rat_lo, k_rat_hi,
                                       float(ss.get("resizing_k_ratio", 0.7)), 0.05,
                                       format="%.2f", key="_opt_kr0")

        ss.opt_k_lo  = k_arm_lo; ss.opt_k_hi  = k_arm_hi
        ss.opt_kr_lo = k_rat_lo; ss.opt_kr_hi = k_rat_hi

    with col_const:
        st.markdown("**Constraint parameters**")
        TW_required = st.number_input(
            "Required T/W ratio (constraint g3)", 1.0, 5.0,
            float(ss.get("opt_TW_req", 2.0)), 0.1, format="%.1f", key="_opt_tw")
        c_margin_m = st.number_input(
            "Clearance margin [mm] (constraint g2)", 0.0, 50.0,
            float(ss.get("resizing_c_margin_m", 0.010) * 1000),
            step=1.0, format="%.0f", key="_opt_cm",
        ) / 1000.0

        T_100pct_g = float(ss.get("resizing_T_100pct_g", 0.0))
        T_100pct_N = T_100pct_g * 9.81 / 1000.0
        st.metric("T_100pct / motor",
                  f"{T_100pct_g:.0f} g  ({T_100pct_N:.2f} N)",
                  help="From R3 · Propulsion, selected motor T_100pct.")
        if T_100pct_g <= 0:
            st.warning("Set motor T_100pct in R3 · Propulsion for constraint g3.")

        ss.opt_TW_req = TW_required

    # ── Run optimisation ──────────────────────────────────────────────────────
    st.markdown("---")
    if st.button("Run Optimisation", use_container_width=False):
        base_params = _gather_base_params(ss)
        x0     = [k_arm_0, k_rat_0]
        bounds = [(k_arm_lo, k_arm_hi), (k_rat_lo, k_rat_hi)]

        with st.spinner("Running SLSQP optimisation…"):
            try:
                res, history = run_optimisation(
                    base_params, T_100pct_N, TW_required, c_margin_m,
                    x0, bounds,
                )
                ss.resizing_opt_k_arm    = float(res.x[0])
                ss.resizing_opt_k_ratio  = float(res.x[1])
                ss.resizing_opt_MTOW     = float(res.fun)
                ss.resizing_opt_history  = history
                ss._opt_result = {
                    "success":  res.success,
                    "message":  res.message,
                    "fun":      float(res.fun),
                    "x":        res.x.tolist(),
                    "nit":      int(res.nit),
                }
            except Exception as exc:
                st.error(f"Optimisation failed: {exc}")

    # ── Results ───────────────────────────────────────────────────────────────
    opt = ss.get("_opt_result")
    if opt is None:
        st.info("Click ▶ Run Optimisation to find the minimum-MTOW arm geometry.")
        return

    badge = "converged-badge" if opt["success"] else "warn-badge"
    sym   = "✓" if opt["success"] else "✗"
    st.markdown(
        f'<span class="{badge}">{sym} {opt["message"]} &nbsp;·&nbsp;'
        f' {opt["nit"]} iterations &nbsp;·&nbsp;'
        f' MTOW* = {opt["fun"]:.4g} kg  ({opt["fun"]*1000:.1f} g)</span>',
        unsafe_allow_html=True,
    )

    k_opt, kr_opt = opt["x"]
    D_prop_m = float(ss.get("resizing_D_prop_m", 0.127))
    L_opt = k_opt * D_prop_m / 2.0

    st.markdown(f"""
<div style="background:#ffffff;border:1px solid #e5e7eb;border-top:2px solid #d97706;
            border-radius:10px;padding:16px 20px;margin-top:12px;">
  <b style="color:#d97706;">Optimal design variables</b><br><br>
  k_arm* = <b>{k_opt:.3f}</b> &nbsp;→&nbsp; L_arm* = <b>{L_opt*1000:.2f} mm</b><br>
  k_ratio* = <b>{kr_opt:.3f}</b><br>
  MTOW* = <b style="color:#d97706;">{opt["fun"]:.4g} kg  ({opt["fun"]*1000:.1f} g)</b>
</div>
""", unsafe_allow_html=True)

    # Savings vs initial
    rz = ss.get("resizing_results")
    if rz is not None:
        delta_g = (rz["M_TO"] - opt["fun"]) * 1000.0
        color = "#16a34a" if delta_g > 0 else "#dc2626"
        st.markdown(
            f'<span style="color:{color};font-weight:600;font-size:0.87rem;">'
            f'Mass saving vs current design: {"+" if delta_g >= 0 else ""}{delta_g:.1f} g</span>',
            unsafe_allow_html=True,
        )

    # Convergence plot
    history = ss.get("resizing_opt_history", [])
    if history:
        st.markdown("### Optimisation Convergence")
        df_hist = pd.DataFrame(history)

        fig_h = go.Figure()
        fig_h.add_trace(go.Scatter(
            x=df_hist["iter"], y=df_hist["MTOW"],
            mode="lines+markers",
            line=dict(color="#d97706", width=2),
            marker=dict(size=6, color="#d97706"),
            hovertemplate="Iter %{x}: MTOW = %{y:.4g} kg<extra></extra>",
        ))
        fig_h.update_layout(
            paper_bgcolor="#ffffff", plot_bgcolor="#f9fafb",
            font=dict(color="#374151", size=11),
            xaxis=dict(title="Iteration", gridcolor="#e5e7eb", title_font_color="#6b7280"),
            yaxis=dict(title="MTOW [kg]", gridcolor="#e5e7eb", title_font_color="#6b7280"),
            height=280, margin=dict(l=10, r=10, t=10, b=10), showlegend=False,
        )
        st.plotly_chart(fig_h, use_container_width=True)

        # History table
        df_disp = df_hist.copy()
        for col in ["k_arm", "k_ratio", "MTOW"]:
            if col in df_disp.columns:
                df_disp[col] = df_disp[col].map(
                    "{:.4f}".format if col == "MTOW" else "{:.3f}".format)
        st.dataframe(df_disp, use_container_width=True, hide_index=True)

    # ── Constraint status at optimum ──────────────────────────────────────────
    st.markdown("### Constraint Status at Optimum")
    from resizing.structure_resizing import (
        compute_F_max, solve_arm, arm_mass_one, prop_clearance,
    )
    from resizing.convergence_resizing import run_resizing

    bp = _gather_base_params(ss)
    bp["k_arm"]   = k_opt
    bp["k_ratio"] = kr_opt

    try:
        rz_opt = run_resizing(bp)
        MTOW_opt = rz_opt["M_TO"]
        n = int(ss.get("n_motors", 4))

        L_arm = k_opt * D_prop_m / 2.0
        F_max = compute_F_max(MTOW_opt, bp["a_TO_ms2"], n)
        M_root = F_max * L_arm
        dims = solve_arm(bp["cs_type"], M_root, bp["sigma_allow_Pa"], bp["FoS"],
                         kr_opt, bp["b_plate_m"])
        m_one = arm_mass_one(bp["rho"], dims["A_m2"], L_arm)
        M_arms = n * m_one
        d_between, _ = prop_clearance(L_arm, D_prop_m, n, c_margin_m)
        TW_actual = T_100pct_N * n / (MTOW_opt * 9.81) if MTOW_opt > 0 else 0.0

        g1 = dims.get("FoS_actual", 0.0) - bp["FoS"]
        g2 = d_between - D_prop_m - c_margin_m
        g3 = TW_actual - TW_required
        g4 = bp["M_struct_sizing_kg"] - M_arms

        constraints = [
            ("g1  σ FoS", g1, "FoS_actual − FoS_req"),
            ("g2  Clearance", g2 * 1000, "d_between − D_prop − margin [mm]"),
            ("g3  T/W", g3, "TW_actual − TW_required"),
            ("g4  Body mass", g4 * 1000, "M_struct_sizing − M_arms [g]"),
        ]

        for name, val, desc in constraints:
            ok = val >= -1e-6
            badge = "converged-badge" if ok else "warn-badge"
            sym   = "✓" if ok else "✗"
            val_str = f"{val:.4f}" if abs(val) < 100 else f"{val:.2f}"
            st.markdown(
                f'<span class="{badge}" style="margin-bottom:6px;">'
                f'{sym} {name} = {val_str} &nbsp;({desc})</span>',
                unsafe_allow_html=True,
            )
    except Exception as exc:
        st.warning(f"Constraint evaluation skipped: {exc}")

    # ── Mode 2 / MDO note ─────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("""
<div class="info-box">
<b>Mode 2 check:</b> After optimisation, verify that the optimised k_arm and k_ratio
satisfy all physical constraints above (g1–g4 ≥ 0). If any constraint is violated
(shown in red), tighten bounds or adjust the initial guess and re-run.<br><br>
For a full MDO loop, iterate: Optimisation → Results (re-run) → Aerodynamics → repeat
until MTOW and E_cruise are self-consistent.
</div>
""", unsafe_allow_html=True)
