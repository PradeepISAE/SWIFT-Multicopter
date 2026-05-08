"""
Resizing Phase — Optimisation (R9).
SLSQP: minimise MTOW over [k_arm, t_wall_m] with 4 constraints.
Profile-aware: circular, square, or flat_plate arm cross-section.
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from resizing.optimisation import run_optimisation
from resizing.structure_resizing import (
    MATERIALS, compute_F_max, solve_arm, arm_mass_one, prop_clearance,
    compute_stress_mpa,
)
from resizing.convergence_resizing import run_resizing


# ── Profile helpers ───────────────────────────────────────────────────────────

_PROF_LABELS = {
    "circular":  "Circular Hollow Tube",
    "square":    "Square Hollow Tube",
    "flat_plate": "Flat Plate",
}

def _to_profile(stored: str) -> str:
    """Normalise any stored value → lowercase profile key."""
    m = {
        "circular": "circular", "Circular Hollow Tube": "circular",
        "square": "square",     "Square Hollow Tube": "square",
        "flat_plate": "flat_plate", "Flat Plate": "flat_plate",
    }
    return m.get(stored, "circular")

def _to_cs_type(stored: str) -> str:
    """Normalise → display label for run_resizing / solve_arm."""
    p = _to_profile(stored)
    return _PROF_LABELS.get(p, "Circular Hollow Tube")


# ── Parameter builders ────────────────────────────────────────────────────────

def _build_opt_base_params(ss) -> dict:
    """Mission / battery / fixed-mass parameters for the objective."""
    return {
        "mtow_estimate": float(ss.get("resizing_MTOW_converged",
                                       ss.get("mtow_converged", 0.500))),
        "m_pay":         float(ss.get("m_pay",  0.030)),
        "m_avi":         float(ss.get("resizing_M_avi",  0.030)),
        "m_prop":        float(ss.get("resizing_M_prop", 0.020)),
        "pl_gW":         float(ss.get("resizing_PL_50pct_gW", 4.0)),
        "P_avi_W":       float(ss.get("resizing_P_avi",  1.3)),
        "P_pay_W":       float(ss.get("P_pay",           1.0)),
        "segments":      ss.get("resizing_mission_segments", {
            "takeoff": {"active": True,  "duration_min": 0.5,  "a_TO_ms2": 19.62},
            "climb":   {"active": False, "duration_min": 2.0},
            "cruise":  {"active": False, "duration_min": 5.0},
            "hover":   {"active": True,  "duration_min": 20.0},
            "land":    {"active": True,  "duration_min": 0.5,  "k_land": 0.5},
        }),
        "E_cruise_Wh":   float(ss.get("resizing_E_cruise_Wh", 0.0)),
        "SED_whkg":      float(ss.get("resizing_SED",      150.0)),
        "DoD":           float(ss.get("resizing_DoD",      0.85)),
        "eta_elec":      float(ss.get("resizing_eta_elec", 0.85)),
        "V_batt":        float(ss.get("resizing_V_batt",   11.1)),
        "k_arm":         float(ss.get("resizing_k_arm",    1.2)),
        # kept for run_resizing backward compat (constraint status section)
        "m_pay_rz":      float(ss.get("m_pay",  0.030)),
        "MF_pay":        float(ss.get("MF_pay", 0.20)),
        "M_avi_fixed":   float(ss.get("resizing_M_avi",  0.030)),
        "M_prop_fixed":  float(ss.get("resizing_M_prop", 0.020)),
        "n_motors":      int(ss.get("n_motors", 4)),
        "PL_50pct_gW":   float(ss.get("resizing_PL_50pct_gW", 4.0)),
        "P_avi_W_rz":    float(ss.get("resizing_P_avi",  1.3)),
        "P_pay_W_rz":    float(ss.get("P_pay",           1.0)),
        "altitude_m":    float(ss.get("resizing_altitude_m", 0.0)),
    }


def _build_struct_params(ss) -> dict:
    """Geometry / material / constraint parameters for the arm model."""
    mat = ss.get("resizing_material", "CF tube/rod")
    if mat == "Custom":
        rho_mat      = float(ss.get("resizing_rho_custom", 1600.0))
        sigma_allow  = float(ss.get("resizing_sigma_custom", 600.0))
    else:
        m = MATERIALS.get(mat, MATERIALS["CF tube/rod"])
        rho_mat      = float(m["rho"])
        sigma_allow  = float(m["sigma_allow_MPa"])

    return {
        "profile":          _to_profile(ss.get("resizing_cross_section", "Circular Hollow Tube")),
        "t_wall_m":         float(ss.get("resizing_t_wall_mm", 1.0)) / 1000.0,
        "b_plate_m":        float(ss.get("resizing_b_plate_m", 0.012)),
        "rho_mat":          rho_mat,
        "sigma_allow_mpa":  sigma_allow,
        "fos":              float(ss.get("resizing_FoS", 1.5)),
        "n_motors":         int(ss.get("n_motors", 4)),
        "d_prop_m":         float(ss.get("resizing_D_prop_m", 0.127)),
        "altitude_m":       float(ss.get("resizing_altitude_m", 0.0)),
        "t_motor_100pct_g": float(ss.get("resizing_T_100pct_g", 0.0)),
        "a_to_ms2":         float(ss.get("resizing_a_TO_ms2", 19.62)),
        "m_struct_sizing":  float(ss.get("resizing_M_struct_sizing",
                                          ss.get("m_struct_sizing", 0.050))),
        "c_margin_m":       float(ss.get("resizing_c_margin_m", 0.010)),
        "tw_required":      float(ss.get("opt_TW_req", 2.0)),
    }


# ── Render ────────────────────────────────────────────────────────────────────

def render():
    st.markdown('<div class="section-tag">Resizing Phase · Optimisation</div>',
                unsafe_allow_html=True)
    st.markdown("## R9 · SLSQP Optimisation")

    st.markdown("""
<div class="info-box">
<b>Minimise MTOW</b> by tuning arm geometry <b>x = [k_arm, t_wall_m]</b> subject to:<br>
① FoS_actual − FoS_req ≥ 0 &nbsp;(structural factor of safety)<br>
② d_between − D_prop − margin ≥ 0 &nbsp;(propeller clearance)<br>
③ T_100pct × n / (MTOW × g) − TW_req ≥ 0 &nbsp;(thrust-to-weight)<br>
④ M_struct_sizing − M_arms ≥ 0 &nbsp;(positive body mass)<br>
<i>Profile-aware: arm geometry uses the cross-section selected in R4 · Structure.</i>
</div>
""", unsafe_allow_html=True)

    with st.expander("Equations & References — SLSQP Formulation"):
        st.markdown("**Objective**")
        st.latex(r"\min_{k_{arm},\,t_{wall}}\; MTOW(k_{arm},\, t_{wall})")
        st.markdown("**Constraint g1 — Structural factor of safety (stress-based)**")
        st.latex(r"g_1 = \frac{\sigma_{allow}}{\sigma_{root}(k_{arm},\,t_{wall})} - FoS_{req} \geq 0")
        st.markdown("**Constraint g2 — Propeller tip clearance**")
        st.latex(r"g_2 = d_{between} - D_{prop} - c_{margin} \geq 0, \quad d_{between} = 2L_{arm}\sin\!\left(\frac{\pi}{n}\right)")
        st.markdown("**Constraint g3 — Thrust-to-weight (total thrust / total weight)**")
        st.latex(r"g_3 = \frac{T_{100\%} \cdot n_{motors}}{MTOW \cdot g} - TW_{req} \geq 0")
        st.markdown("**Constraint g4 — Positive body mass**")
        st.latex(r"g_4 = M_{struct,sizing} - M_{arms}(k_{arm},\,t_{wall}) \geq 0")
        st.caption(
            "Solver: SciPy SLSQP (Kraft 1988). "
            "References: Pollet (2024) PhD Thesis §3.8; "
            "Tyan et al. (2017) §4; "
            "Nocedal & Wright (2006) Numerical Optimization §18"
        )

    ss = st.session_state

    # ── Cross-section profile info ────────────────────────────────────────────
    _profile = _to_profile(ss.get("resizing_cross_section", "Circular Hollow Tube"))
    _prof_label = _PROF_LABELS.get(_profile, "Circular Hollow Tube")
    st.info(f"Cross-section profile (from R4): **{_prof_label}**  —  change in R4 · Structure.")

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
            t_wall_lo = st.number_input("t_wall min [mm]", 0.2, 1.5,
                                        float(ss.get("opt_tw_lo", 0.3)), 0.1,
                                        format="%.1f", key="_opt_twlo")
            t_wall_hi = st.number_input("t_wall max [mm]", 0.5, 4.0,
                                        float(ss.get("opt_tw_hi", 3.0)), 0.1,
                                        format="%.1f", key="_opt_twhi")
            t_wall_0  = st.number_input("t_wall init [mm]", t_wall_lo, t_wall_hi,
                                        float(ss.get("resizing_t_wall_mm", 1.0)), 0.1,
                                        format="%.1f", key="_opt_tw0")

        ss.opt_k_lo  = k_arm_lo;  ss.opt_k_hi  = k_arm_hi
        ss.opt_tw_lo = t_wall_lo; ss.opt_tw_hi = t_wall_hi

    with col_const:
        st.markdown("**Constraint parameters**")
        TW_required = st.number_input(
            "Required T/W ratio (constraint g3)", 1.0, 5.0,
            float(ss.get("opt_TW_req", 2.0)), 0.1, format="%.1f", key="_opt_tw_req")
        ss.opt_TW_req = TW_required

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

    # ── Run optimisation ──────────────────────────────────────────────────────
    st.markdown("---")
    if st.button("▶ Run Optimisation", use_container_width=False):
        opt_base    = _build_opt_base_params(ss)
        struct_p    = _build_struct_params(ss)
        struct_p["c_margin_m"]  = c_margin_m
        struct_p["tw_required"] = TW_required
        struct_p["t_motor_100pct_g"] = T_100pct_g

        x0     = [k_arm_0, t_wall_0 / 1000.0]
        bounds = [(k_arm_lo, k_arm_hi), (t_wall_lo / 1000.0, t_wall_hi / 1000.0)]

        with st.spinner("Running SLSQP optimisation…"):
            try:
                res, history, phys_dims = run_optimisation(
                    opt_base, struct_p, x0, bounds,
                )
                ss.resizing_opt_k_arm      = float(res.x[0])
                ss.resizing_opt_t_wall_mm  = phys_dims["t_wall_mm"]
                ss.resizing_opt_d_out_mm   = phys_dims["d_out_mm"]
                ss.resizing_opt_d_in_mm    = phys_dims["d_in_mm"]
                ss.resizing_opt_L_arm_mm   = phys_dims["L_arm_mm"]
                ss.resizing_opt_FoS_actual = phys_dims["FoS_actual"]
                ss.resizing_opt_MTOW       = float(res.fun)
                ss.resizing_opt_M_arms     = phys_dims["M_arms_g"]
                ss.resizing_opt_M_batt     = phys_dims["M_batt_g"]
                ss.resizing_std_cf_od_mm   = phys_dims["std_cf_od_mm"]
                ss.resizing_std_cf_wall_mm = phys_dims["std_cf_wall_mm"]
                ss.resizing_opt_history    = history
                ss._opt_result = {
                    "success":   res.success,
                    "message":   res.message,
                    "fun":       float(res.fun),
                    "x":         res.x.tolist(),
                    "nit":       int(res.nit),
                    "phys_dims": phys_dims,
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

    k_opt, t_wall_opt_m = opt["x"]
    phys = opt.get("phys_dims", {})
    t_wall_opt_mm = phys.get("t_wall_mm", t_wall_opt_m * 1000.0)
    d_out_opt_mm  = phys.get("d_out_mm",  0.0)
    d_in_opt_mm   = phys.get("d_in_mm",   0.0)
    k_ratio_opt   = phys.get("k_ratio",   0.0)
    L_arm_opt_mm  = phys.get("L_arm_mm",  k_opt * float(ss.get("resizing_D_prop_m", 0.127)) / 2.0 * 1000.0)
    std_cf_od     = phys.get("std_cf_od_mm",   0.0)
    std_cf_wall   = phys.get("std_cf_wall_mm", 0.0)
    D_prop_m      = float(ss.get("resizing_D_prop_m", 0.127))
    prof_opt      = phys.get("profile", _profile)
    prof_label    = _PROF_LABELS.get(prof_opt, "Circular Hollow Tube")
    sigma_opt_mpa = phys.get("sigma_mpa", 0.0)

    # Profile-specific dimension labels
    if prof_opt == "circular":
        dim_line = (f"d_out* = <b>{d_out_opt_mm:.2f} mm</b> &nbsp;·&nbsp; "
                    f"d_in* = <b>{d_in_opt_mm:.2f} mm</b>")
        kr_line  = f"k_ratio (derived) = {k_ratio_opt:.3f}"
    elif prof_opt == "square":
        dim_line = (f"b_out* = <b>{d_out_opt_mm:.2f} mm</b> &nbsp;·&nbsp; "
                    f"b_in* = <b>{d_in_opt_mm:.2f} mm</b>")
        kr_line  = f"k_ratio (derived) = {k_ratio_opt:.3f}"
    else:
        dim_line = f"h* = <b>{d_out_opt_mm:.2f} mm</b> &nbsp;(flat-plate height, b = {phys.get('b_plate_mm', float(ss.get('resizing_b_plate_m', 0.012)) * 1000):.1f} mm)"
        kr_line  = ""

    st.markdown(f"""
<div style="background:#ffffff;border:1px solid #e5e7eb;border-top:2px solid #d97706;
            border-radius:10px;padding:16px 20px;margin-top:12px;">
  <b style="color:#d97706;">Optimal design variables</b>
  &nbsp;<span style="font-size:0.78rem;color:#6b7280;">({prof_label})</span><br><br>
  k_arm* = <b>{k_opt:.3f}</b> &nbsp;→&nbsp; L_arm* = <b>{L_arm_opt_mm:.2f} mm</b><br>
  t_wall* = <b>{t_wall_opt_mm:.2f} mm</b> &nbsp;→&nbsp; {dim_line}<br>
  {(kr_line + " &nbsp;·&nbsp; ") if kr_line else ""}FoS_actual = {phys.get("FoS_actual", 0.0):.3f}
  &nbsp;·&nbsp; σ_root = {sigma_opt_mpa:.2f} MPa<br>
  MTOW* = <b style="color:#d97706;">{opt["fun"]:.4g} kg  ({opt["fun"]*1000:.1f} g)</b>
</div>
""", unsafe_allow_html=True)

    # CF tube recommendation (circular / square only)
    if std_cf_od > 0 and prof_opt in ("circular", "square"):
        st.markdown(f"""
<div style="background:#f0fdf4;border:1px solid #86efac;border-radius:8px;
            padding:10px 14px;margin-top:8px;font-size:0.83rem;">
  <b>Standard CF tube recommendation:</b> OD = {std_cf_od:.1f} mm &nbsp;·&nbsp;
  wall = {std_cf_wall:.1f} mm
  &nbsp;(smallest catalogue size ≥ {d_out_opt_mm:.2f} mm)
</div>
""", unsafe_allow_html=True)

    # Altitude correction notice
    _opt_alt = float(ss.get("resizing_altitude_m", 0.0))
    _opt_k   = float(ss.get("resizing_k_alt", 1.0))
    if _opt_alt > 0:
        st.info(
            f"Results account for **altitude correction at {_opt_alt:.0f} m** "
            f"(power factor = {_opt_k:.4f}, +{(_opt_k-1)*100:.1f}% vs sea level). "
            f"Change altitude in R1 · Mission."
        )

    # Savings vs current resizing design
    rz = ss.get("resizing_results")
    if rz is not None:
        delta_g = (rz["M_TO"] - opt["fun"]) * 1000.0
        color = "#16a34a" if delta_g > 0 else "#dc2626"
        st.markdown(
            f'<span style="color:{color};font-weight:600;font-size:0.87rem;">'
            f'Mass saving vs current design: {"+" if delta_g >= 0 else ""}{delta_g:.1f} g</span>',
            unsafe_allow_html=True,
        )

    # ── T/W breakdown table ───────────────────────────────────────────────────
    n_motors = int(ss.get("n_motors", 4))
    MTOW_opt = opt["fun"]
    if T_100pct_g > 0 and MTOW_opt > 0:
        TW_actual = T_100pct_N * n_motors / (MTOW_opt * 9.81)
        st.markdown("### T/W Breakdown at Optimum")
        tw_rows = [
            ("T per motor",   f"{T_100pct_g:.1f} g",              f"{T_100pct_N:.3f} N"),
            ("n motors",      str(n_motors),                       ""),
            ("Total thrust",  f"{T_100pct_g*n_motors:.1f} g",     f"{T_100pct_N*n_motors:.3f} N"),
            ("MTOW*",         f"{MTOW_opt*1000:.1f} g",           f"{MTOW_opt:.4g} kg"),
            ("T/W actual",    f"{TW_actual:.3f}",                  f"(req ≥ {TW_required:.1f})"),
        ]
        tw_rows_html = "".join(
            f'<tr><td style="padding:6px 12px;color:#374151;font-size:0.83rem;">{n}</td>'
            f'<td style="padding:6px 12px;color:#d97706;font-weight:600;font-size:0.83rem;">{v}</td>'
            f'<td style="padding:6px 12px;color:#6b7280;font-size:0.79rem;">{u}</td></tr>'
            for n, v, u in tw_rows
        )
        tw_badge = "converged-badge" if TW_actual >= TW_required else "warn-badge"
        st.markdown(f"""
<div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:10px;
            overflow:hidden;margin-bottom:16px;">
<table style="width:100%;border-collapse:collapse;">
<tr style="background:#fffbeb;">
  <th style="color:#d97706;padding:8px 12px;text-align:left;font-size:0.70rem;
             letter-spacing:0.10em;text-transform:uppercase;border-bottom:1px solid #e5e7eb;">Parameter</th>
  <th style="color:#d97706;padding:8px 12px;text-align:left;font-size:0.70rem;
             letter-spacing:0.10em;text-transform:uppercase;border-bottom:1px solid #e5e7eb;">Value</th>
  <th style="color:#d97706;padding:8px 12px;text-align:left;font-size:0.70rem;
             letter-spacing:0.10em;text-transform:uppercase;border-bottom:1px solid #e5e7eb;">Notes</th>
</tr>
{tw_rows_html}
</table>
</div>
<span class="{tw_badge}">{"✓" if TW_actual >= TW_required else "✗"} T/W = {TW_actual:.3f} (req ≥ {TW_required:.1f})</span>
""", unsafe_allow_html=True)

    # ── Cross-section comparison expander ─────────────────────────────────────
    with st.expander("Cross-section profile — governing equations"):
        st.markdown(f"**Active profile: {prof_label}**")
        if prof_opt == "circular":
            st.latex(r"\sigma_{root} = \frac{32\,M_{root}}{\pi\,d_{out}^3\,(1-k^4)}, "
                     r"\quad k = \frac{d_{out} - 2\,t_{wall}}{d_{out}}")
            st.latex(r"A_{cs} = \frac{\pi}{4}\,(d_{out}^2 - d_{in}^2)")
        elif prof_opt == "square":
            st.latex(r"\sigma_{root} = \frac{6\,M_{root}}{b_{out}^3\,(1-k^4)}, "
                     r"\quad k = \frac{b_{out} - 2\,t_{wall}}{b_{out}}")
            st.latex(r"A_{cs} = b_{out}^2 - b_{in}^2")
        else:
            st.latex(r"\sigma_{root} = \frac{6\,M_{root}}{b\,h^2}")
            st.latex(r"A_{cs} = b \times h")
        st.caption(
            "FoS_actual = σ_allow / σ_root. "
            "Constraint g1 requires FoS_actual ≥ FoS_req."
        )

    # ── Step-by-step solution expander ────────────────────────────────────────
    with st.expander("Step-by-step solution at optimum"):
        st.markdown("**1. Arm geometry**")
        st.latex(rf"L_{{arm}}^* = k_{{arm}}^* \cdot \frac{{D_{{prop}}}}{{2}} = "
                 rf"{k_opt:.3f} \times \frac{{{D_prop_m*1000:.1f}\,\text{{mm}}}}{{2}} "
                 rf"= {L_arm_opt_mm:.2f}\,\text{{mm}}")
        st.markdown("**2. Wall thickness → outer dimension (stress-based inverse solve)**")
        if prof_opt in ("circular", "square"):
            dim_sym = "d_{out}" if prof_opt == "circular" else "b_{out}"
            st.latex(rf"t_{{wall}}^* = {t_wall_opt_mm:.2f}\,\text{{mm}} \;\Rightarrow\; "
                     rf"{dim_sym}^* = {d_out_opt_mm:.2f}\,\text{{mm}}, \quad "
                     rf"k_{{ratio}} = \frac{{{dim_sym} - 2t_{{wall}}}}{{{dim_sym}}} = {k_ratio_opt:.3f}")
        else:
            st.latex(rf"t_{{wall}}^* = {t_wall_opt_mm:.2f}\,\text{{mm}} \;\Rightarrow\; "
                     rf"h^* = {d_out_opt_mm:.2f}\,\text{{mm}}")
        st.markdown("**3. Bending stress at root**")
        st.latex(rf"\sigma_{{root}}^* = {sigma_opt_mpa:.2f}\,\text{{MPa}}, \quad "
                 rf"FoS_{{actual}} = {phys.get('FoS_actual', 0.0):.3f}")
        st.markdown("**4. Structural arms mass**")
        st.latex(rf"M_{{arms}}^* = n \cdot \rho \cdot A_{{cs}} \cdot L_{{arm}} = "
                 rf"{phys.get('M_arms_g', 0.0):.2f}\,\text{{g}}")
        st.markdown("**5. Battery mass at optimum**")
        st.latex(rf"M_{{batt}}^* \approx {phys.get('M_batt_g', 0.0):.2f}\,\text{{g}}")
        st.markdown("**6. Converged MTOW**")
        st.latex(rf"MTOW^* = {opt['fun']*1000:.1f}\,\text{{g}}")

    # ── Convergence plot & history table ──────────────────────────────────────
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

        df_disp = df_hist.copy()
        for col in ["k_arm", "t_wall_mm", "MTOW"]:
            if col in df_disp.columns:
                df_disp[col] = df_disp[col].map(
                    "{:.4f}".format if col == "MTOW" else "{:.3f}".format)
        st.dataframe(df_disp, use_container_width=True, hide_index=True)

    # ── Constraint status at optimum ──────────────────────────────────────────
    st.markdown("### Constraint Status at Optimum")

    struct_p_chk = _build_struct_params(ss)
    struct_p_chk["c_margin_m"]  = c_margin_m
    struct_p_chk["tw_required"] = TW_required
    struct_p_chk["t_motor_100pct_g"] = T_100pct_g
    opt_base_chk = _build_opt_base_params(ss)

    try:
        from resizing.optimisation import (
            _g1_stress, _g2_clearance, _g3_tw, _g4_body_mass,
            _arm_dims,
        )
        x_opt = [k_opt, t_wall_opt_m]

        g1 = _g1_stress(x_opt, struct_p_chk, opt_base_chk)
        g2 = _g2_clearance(x_opt, struct_p_chk)
        g3 = _g3_tw(x_opt, struct_p_chk, opt_base_chk)
        g4 = _g4_body_mass(x_opt, struct_p_chk, opt_base_chk)

        _, _, L_arm_chk, _, _ = _arm_dims(k_opt, t_wall_opt_m, opt_base_chk, struct_p_chk)
        d_between_chk, _ = prop_clearance(L_arm_chk, D_prop_m, n_motors, c_margin_m)

        if T_100pct_N > 0:
            MTOW_chk = T_100pct_N * n_motors / ((g3 + TW_required) * 9.81)
            TW_actual_chk = T_100pct_N * n_motors / (MTOW_chk * 9.81) if MTOW_chk > 0 else 0.0
        else:
            TW_actual_chk = 0.0

        constraints_chk = [
            ("g1  σ FoS",     g1,        "FoS_actual − FoS_req"),
            ("g2  Clearance", g2 * 1000, "d_between − D_prop − margin [mm]"),
            ("g3  T/W",       g3,        "TW_actual − TW_required"),
            ("g4  Body mass", g4 * 1000, "M_struct_sizing − M_arms [g]"),
        ]
        for name, val, desc in constraints_chk:
            ok    = val >= -1e-6
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

    # ── MDO note ─────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("""
<div class="info-box">
<b>Mode 2 check:</b> After optimisation, verify that g1–g4 ≥ 0 above. If any constraint is
violated (shown in red), tighten bounds or adjust the initial guess and re-run.<br><br>
For a full MDO loop, iterate: Optimisation → Results (re-run) → Aerodynamics → repeat
until MTOW and E_cruise are self-consistent.
</div>
""", unsafe_allow_html=True)
