"""
Resizing Phase — Structure (R4).
Arm dimensions are SOLVED from the bending stress constraint (inverse problem).
"""
import streamlit as st
import numpy as np
from resizing.structure_resizing import (
    MATERIALS, compute_F_max, solve_arm, arm_mass_one, prop_clearance,
)


def _get_mat_props(ss):
    mat = ss.get("resizing_material", "CF tube/rod")
    if mat == "Custom":
        return ss.get("resizing_rho_custom", 1600.0), ss.get("resizing_sigma_custom", 600.0) * 1e6
    m = MATERIALS.get(mat, MATERIALS["CF tube/rod"])
    return m["rho"], m["sigma_allow_MPa"] * 1e6


def _compute_and_store(ss):
    """Solve arm dimensions for current session state and persist results."""
    rho, sigma_allow_Pa = _get_mat_props(ss)
    cs_type   = ss.get("resizing_cross_section", "Circular Hollow Tube")
    k_arm     = float(ss.get("resizing_k_arm",    1.2))
    k_ratio   = float(ss.get("resizing_k_ratio",  0.7))
    b_plate_m = float(ss.get("resizing_b_plate_m", 0.012))
    D_prop_m  = float(ss.get("resizing_D_prop_m",  0.127))
    FoS       = float(ss.get("resizing_FoS",        1.5))
    n_motors  = int(ss.get("n_motors", 4))
    c_margin  = float(ss.get("resizing_c_margin_m", 0.010))
    a_TO      = float(ss.get("resizing_a_TO_ms2",   19.62))
    M_sz      = float(ss.get("resizing_M_struct_sizing",
                              ss.get("m_struct_sizing", 0.05)))

    # Use MTOW estimate: converged if available, else from sizing, else guess
    MTOW_est = float(ss.get("resizing_MTOW_converged",
                     ss.get("mtow_converged", 0.5)))
    if MTOW_est <= 0:
        MTOW_est = 0.5

    L_arm  = k_arm * D_prop_m / 2.0
    F_max  = compute_F_max(MTOW_est, a_TO, n_motors)
    M_root = F_max * L_arm

    try:
        dims = solve_arm(cs_type, M_root, sigma_allow_Pa, FoS, k_ratio, b_plate_m)
    except Exception:
        dims = {"A_m2": 0.0, "FoS_actual": 0.0, "sigma_root_Pa": 0.0, "passed": False}

    A      = dims.get("A_m2", 0.0)
    m_one  = arm_mass_one(rho, A, L_arm)
    M_arms = n_motors * m_one
    M_body = max(0.0, M_sz - M_arms)
    M_struct = M_arms + M_body

    d_between, clear_ok = prop_clearance(L_arm, D_prop_m, n_motors, c_margin)

    # Persist to session state for use by convergence loop
    ss.resizing_L_arm         = L_arm
    ss.resizing_d_out         = dims.get("d_out_m", dims.get("b_out_m", dims.get("h_m", 0.0)))
    ss.resizing_M_arms        = M_arms
    ss.resizing_M_body_calc   = M_body
    ss.resizing_M_struct      = M_struct
    ss.resizing_FoS_actual    = dims.get("FoS_actual", 0.0)
    ss.resizing_sigma_root_MPa = dims.get("sigma_root_Pa", 0.0) / 1e6
    ss.resizing_stress_ok     = dims.get("passed", False)
    ss.resizing_clearance_ok  = clear_ok
    ss.resizing_d_between_m   = d_between
    ss.resizing_struct_dims   = dims

    return {
        "L_arm": L_arm, "F_max": F_max, "M_root": M_root,
        "dims": dims, "A": A,
        "m_one_g": m_one * 1000.0,
        "M_arms_g": M_arms * 1000.0,
        "M_body_g": M_body * 1000.0,
        "M_struct_g": M_struct * 1000.0,
        "FoS_actual": dims.get("FoS_actual", 0.0),
        "sigma_root_MPa": dims.get("sigma_root_Pa", 0.0) / 1e6,
        "stress_ok": dims.get("passed", False),
        "d_between": d_between,
        "clear_ok": clear_ok,
        "rho": rho,
        "sigma_allow_MPa": sigma_allow_Pa / 1e6,
    }


def render():
    st.markdown('<div class="section-tag">Resizing Phase · Structure</div>',
                unsafe_allow_html=True)
    st.markdown("## R4 · Arm Structural Sizing")

    st.markdown("""
<div class="eq-box">
Arm dimensions are <b>solved</b> from the bending stress constraint (inverse problem).<br>
Cantilever tip load: F_max = MTOW × g × (1 + a_TO/g) / n_motors<br>
Root moment: M_root = F_max × L_arm &nbsp;·&nbsp; L_arm = k_arm × D_prop / 2
</div>
""", unsafe_allow_html=True)

    ss = st.session_state

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown("**Cross-section type**")
        cs_opts = ["Circular Hollow Tube", "Square Hollow Tube", "Flat Plate"]
        cs_type = st.selectbox(
            "Cross-section",
            cs_opts,
            index=cs_opts.index(ss.get("resizing_cross_section", "Circular Hollow Tube")),
            key="_rz_cs",
        )
        ss.resizing_cross_section = cs_type

        if cs_type in ("Circular Hollow Tube", "Square Hollow Tube"):
            ss.resizing_k_ratio = st.slider(
                "Inner/outer ratio k_ratio  (d_in/d_out or b_in/b_out)",
                0.30, 0.90,
                float(ss.get("resizing_k_ratio", 0.7)),
                step=0.05, format="%.2f",
                help="0.7 is typical for CF tubes. Higher → thinner wall → lighter but weaker.",
                key="_rz_kr",
            )
        else:
            ss.resizing_b_plate_m = st.number_input(
                "Plate width b [mm]", 5.0, 80.0,
                float(ss.get("resizing_b_plate_m", 0.012) * 1000),
                step=1.0, format="%.1f", key="_rz_bp",
            ) / 1000.0

        st.markdown("**Material**")
        mat_keys = list(MATERIALS.keys())
        mat = st.selectbox(
            "Material", mat_keys,
            index=mat_keys.index(ss.get("resizing_material", "CF tube/rod")),
            key="_rz_mat",
        )
        ss.resizing_material = mat

        if mat == "Custom":
            ss.resizing_rho_custom = st.number_input(
                "Density ρ [kg/m³]", 100.0, 20000.0,
                float(ss.get("resizing_rho_custom", 1600.0)), step=10.0, key="_rz_rho")
            ss.resizing_sigma_custom = st.number_input(
                "Allowable stress σ [MPa]", 1.0, 2000.0,
                float(ss.get("resizing_sigma_custom", 600.0)), step=5.0, key="_rz_sig")
        else:
            m = MATERIALS[mat]
            st.caption(f"ρ = {m['rho']:.0f} kg/m³  ·  σ_allow = {m['sigma_allow_MPa']:.0f} MPa")

    with col_right:
        st.markdown("**Geometry & safety**")

        ss.resizing_D_prop_m = st.number_input(
            "Propeller diameter D [m]", 0.05, 1.0,
            float(ss.get("resizing_D_prop_m", 0.127)), step=0.005, format="%.4f",
            help="Set automatically when a propeller is selected in R3.",
            key="_rz_Dp",
        )
        ss.resizing_k_arm = st.slider(
            "Arm length factor k_arm  (L_arm = k × D/2)",
            1.0, 4.0, float(ss.get("resizing_k_arm", 1.2)),
            step=0.05, format="%.2f",
            help="k=1.2 → compact; k=2.0 → comfortable clearance.",
            key="_rz_karm",
        )
        ss.resizing_FoS = st.number_input(
            "Required factor of safety FoS", 1.0, 5.0,
            float(ss.get("resizing_FoS", 1.5)), step=0.1, format="%.1f",
            key="_rz_fos",
        )
        ss.resizing_c_margin_m = st.number_input(
            "Prop clearance margin [mm]", 0.0, 50.0,
            float(ss.get("resizing_c_margin_m", 0.010) * 1000),
            step=1.0, format="%.0f", key="_rz_cm",
        ) / 1000.0
        ss.resizing_M_struct_sizing = st.number_input(
            "Structural mass from sizing [g]", 0.0, 2000.0,
            float(ss.get("resizing_M_struct_sizing",
                          ss.get("m_struct_sizing", 50.0)) * 1000),
            step=1.0, format="%.1f",
            help="M_body = max(0, M_struct_sizing − M_arms). Bridges from Sizing Phase.",
            key="_rz_msz",
        ) / 1000.0

    st.markdown("---")

    # ── Live computation ──────────────────────────────────────────────────────
    res = _compute_and_store(ss)
    dims = res["dims"]

    c1, c2, c3, c4 = st.columns(4, gap="small")
    c1.metric("L_arm",    f"{res['L_arm']*1000:.1f} mm")
    c2.metric("m_arm",    f"{res['m_one_g']:.2f} g")
    c3.metric("M_struct", f"{res['M_struct_g']:.2f} g")
    c4.metric("M_body",   f"{res['M_body_g']:.2f} g")

    if res["M_body_g"] < 0.1:
        st.markdown(
            '<span class="warn-badge">⚠ M_body ≈ 0 — arms alone exceed M_struct_sizing. '
            'Increase M_struct_sizing or reduce k_arm.</span>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    col_str, col_clr = st.columns([1, 1], gap="large")

    with col_str:
        st.markdown("### Solved Arm Dimensions")

        cs_type = ss.resizing_cross_section
        if cs_type == "Circular Hollow Tube":
            d_out_mm = dims.get("d_out_m", 0.0) * 1000.0
            d_in_mm  = dims.get("d_in_m",  0.0) * 1000.0
            t_mm     = dims.get("t_wall_m", 0.0) * 1000.0
            st.latex(
                r"d_{out} = \left(\frac{32\,M_{root}\,FoS}{\pi\,\sigma_{allow}"
                r"\,(1-k^4)}\right)^{1/3}"
            )
            st.markdown(f"""
<div style="background:#fffbeb;border:1px solid #fde68a;border-radius:8px;
            padding:12px 16px;font-size:0.87rem;margin-top:8px;">
  d_out = <b style="color:#d97706;">{d_out_mm:.3f} mm</b><br>
  d_in  = {d_in_mm:.3f} mm &nbsp;·&nbsp; t_wall = {t_mm:.3f} mm<br>
  k_ratio = {ss.resizing_k_ratio:.2f} &nbsp;·&nbsp; A = {dims.get("A_m2",0)*1e6:.3f} mm²
</div>
""", unsafe_allow_html=True)

        elif cs_type == "Square Hollow Tube":
            b_out_mm = dims.get("b_out_m", 0.0) * 1000.0
            b_in_mm  = dims.get("b_in_m",  0.0) * 1000.0
            t_mm     = dims.get("t_wall_m", 0.0) * 1000.0
            st.latex(
                r"b_{out} = \left(\frac{6\,M_{root}\,FoS}{\sigma_{allow}"
                r"\,(1-k^4)}\right)^{1/3}"
            )
            st.markdown(f"""
<div style="background:#fffbeb;border:1px solid #fde68a;border-radius:8px;
            padding:12px 16px;font-size:0.87rem;margin-top:8px;">
  b_out = <b style="color:#d97706;">{b_out_mm:.3f} mm</b><br>
  b_in  = {b_in_mm:.3f} mm &nbsp;·&nbsp; t_wall = {t_mm:.3f} mm<br>
  k_ratio = {ss.resizing_k_ratio:.2f} &nbsp;·&nbsp; A = {dims.get("A_m2",0)*1e6:.3f} mm²
</div>
""", unsafe_allow_html=True)

        else:
            h_mm = dims.get("h_m", 0.0) * 1000.0
            b_mm = dims.get("b_m", 0.0) * 1000.0
            st.latex(r"h = \sqrt{\frac{6\,M_{root}\,FoS}{\sigma_{allow}\,b}}")
            st.markdown(f"""
<div style="background:#fffbeb;border:1px solid #fde68a;border-radius:8px;
            padding:12px 16px;font-size:0.87rem;margin-top:8px;">
  h = <b style="color:#d97706;">{h_mm:.3f} mm</b><br>
  b = {b_mm:.1f} mm &nbsp;·&nbsp; A = {dims.get("A_m2",0)*1e6:.3f} mm²
</div>
""", unsafe_allow_html=True)

        # Stress check badge
        ok    = res["stress_ok"]
        badge = "converged-badge" if ok else "warn-badge"
        sym   = "✓" if ok else "✗"
        st.markdown(
            f'<span class="{badge}">{sym} FoS_actual = {res["FoS_actual"]:.3f} '
            f'(req ≥ {ss.resizing_FoS:.1f})  ·  '
            f'σ_root = {res["sigma_root_MPa"]:.3f} MPa</span>',
            unsafe_allow_html=True,
        )

    with col_clr:
        st.markdown("### Propeller Clearance")
        st.latex(r"d_{between} = 2\,L_{arm}\,\sin\!\left(\frac{\pi}{n}\right)")
        clr_ok = res["clear_ok"]
        cbadge = "converged-badge" if clr_ok else "warn-badge"
        csym   = "✓" if clr_ok else "✗"
        D_prop_mm = ss.resizing_D_prop_m * 1000.0
        c_margin_mm = ss.resizing_c_margin_m * 1000.0
        st.markdown(
            f'<span class="{cbadge}">{csym} d_between = {res["d_between"]*1000:.1f} mm '
            f'(need > {D_prop_mm + c_margin_mm:.1f} mm)</span>',
            unsafe_allow_html=True,
        )
        st.markdown(f"""
<div style="background:#ffffff;border:1px solid #e5e7eb;
            border-left:3px solid {"#16a34a" if clr_ok else "#dc2626"};
            border-radius:0 8px 8px 0;padding:10px 14px;margin-top:10px;font-size:0.83rem;">
  F_max = {res["F_max"]:.3f} N &nbsp;·&nbsp;
  M_root = {res["M_root"]*1000:.2f} N·mm<br>
  d_between = {res["d_between"]*1000:.1f} mm<br>
  D_prop + margin = {D_prop_mm + c_margin_mm:.1f} mm
</div>
""", unsafe_allow_html=True)

    # Material reference table
    with st.expander("Material reference"):
        import pandas as pd
        df = pd.DataFrame([
            {"Material": k, "ρ [kg/m³]": v["rho"],
             "σ_allow [MPa]": v["sigma_allow_MPa"]}
            for k, v in MATERIALS.items() if v["rho"] is not None
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)
