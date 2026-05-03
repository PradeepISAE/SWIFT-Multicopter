"""
Resizing Phase — Structure tab.
Arm cross-section, material, FoS, geometry. Stress + clearance checks.
"""
import streamlit as st
import numpy as np
from resizing.structure_resizing import (
    MATERIALS, section_properties, stress_check, arm_mass_one, prop_clearance,
)


def _dims_from_state(cs_type):
    ss = st.session_state
    if cs_type == "Circular tube":
        return {"d_outer": ss.rz_d_outer_mm / 1000.0,
                "t_wall":  ss.rz_t_wall_mm  / 1000.0}
    if cs_type == "Square tube":
        return {"b_outer": ss.rz_b_outer_mm / 1000.0,
                "t_wall":  ss.rz_t_wall_mm  / 1000.0}
    return {"b": ss.rz_b_plate_mm / 1000.0,
            "h": ss.rz_h_plate_mm / 1000.0}


def _compute_and_store():
    ss = st.session_state
    cs_type = ss.rz_cs_type
    mat     = ss.rz_material

    if mat == "Custom":
        rho           = ss.rz_rho_custom
        sigma_allow   = ss.rz_sigma_custom
    else:
        rho           = MATERIALS[mat]["rho"]
        sigma_allow   = MATERIALS[mat]["sigma_allow_MPa"]

    D_prop_m  = ss.rz_D_prop_mm / 1000.0
    L_arm_m   = ss.rz_k_arm * D_prop_m / 2.0
    dims_m    = _dims_from_state(cs_type)
    FoS_req   = ss.rz_FoS_req
    c_margin  = ss.rz_c_margin_mm / 1000.0
    n_motors  = ss.n_motors

    try:
        I, c, A = section_properties(cs_type, dims_m)
    except Exception:
        I, c, A = 0.0, 0.0, 0.0

    # T_max: use sizing target if available, else 2 × hover thrust
    T_hover_N = ss.get("t_motor_target", 0.0) * 9.81 / 1000.0  # g → N
    T_max_N   = T_hover_N * 2.0  # worst-case = 2 × hover

    sigma_MPa, FoS_actual, stress_ok = stress_check(T_max_N, L_arm_m, I, c,
                                                     sigma_allow, FoS_req)
    d_between, clear_ok = prop_clearance(L_arm_m, D_prop_m, n_motors, c_margin)
    m_one_arm   = arm_mass_one(rho, A, L_arm_m)
    M_arms      = n_motors * m_one_arm
    M_body      = ss.rz_M_body_g / 1000.0
    M_struct    = M_arms + M_body

    ss.rz_L_arm_m          = L_arm_m
    ss.rz_D_prop_m         = D_prop_m
    ss.rz_M_struct_fixed   = M_struct
    ss.rz_stress_ok        = stress_ok
    ss.rz_clearance_ok     = clear_ok
    ss.rz_FoS_actual       = FoS_actual
    ss.rz_sigma_MPa        = sigma_MPa
    ss.rz_d_between_m      = d_between
    ss.rz_T_max_N          = T_max_N
    ss.rz_m_one_arm_g      = m_one_arm * 1000.0

    return {
        "L_arm_m": L_arm_m, "D_prop_m": D_prop_m,
        "I": I, "c": c, "A": A,
        "sigma_MPa": sigma_MPa, "FoS_actual": FoS_actual, "stress_ok": stress_ok,
        "d_between": d_between, "clear_ok": clear_ok,
        "m_one_arm_g": m_one_arm * 1000.0,
        "M_arms_g": M_arms * 1000.0,
        "M_struct_g": M_struct * 1000.0,
        "rho": rho, "sigma_allow": sigma_allow,
    }


def render():
    st.markdown('<div class="section-tag">Resizing Phase · Structure</div>',
                unsafe_allow_html=True)
    st.markdown("## R1 · Arm Structural Sizing")

    st.markdown("""
<div class="eq-box">
Cantilever beam model — tip load = T_max per motor (= 2 × T_hover, worst-case landing).<br>
σ<sub>root</sub> = M<sub>bend</sub> × c / I &nbsp;·&nbsp;
FoS = σ<sub>allow</sub> / σ<sub>root</sub>
</div>
""", unsafe_allow_html=True)

    ss = st.session_state

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown("**Cross-section**")
        cs_type = st.selectbox(
            "Cross-section type",
            ["Circular tube", "Square tube", "Flat plate"],
            index=["Circular tube", "Square tube", "Flat plate"].index(ss.rz_cs_type),
            key="_sel_cs",
        )
        ss.rz_cs_type = cs_type

        if cs_type == "Circular tube":
            ss.rz_d_outer_mm = st.number_input(
                "Outer diameter [mm]", 2.0, 50.0, float(ss.rz_d_outer_mm),
                step=0.5, format="%.1f", key="_num_do")
            ss.rz_t_wall_mm = st.number_input(
                "Wall thickness [mm]", 0.2, 5.0, float(ss.rz_t_wall_mm),
                step=0.1, format="%.1f", key="_num_tw")
        elif cs_type == "Square tube":
            ss.rz_b_outer_mm = st.number_input(
                "Outer side [mm]", 2.0, 50.0, float(ss.rz_b_outer_mm),
                step=0.5, format="%.1f", key="_num_bo")
            ss.rz_t_wall_mm = st.number_input(
                "Wall thickness [mm]", 0.2, 5.0, float(ss.rz_t_wall_mm),
                step=0.1, format="%.1f", key="_num_tw2")
        else:
            ss.rz_b_plate_mm = st.number_input(
                "Width b [mm]", 2.0, 80.0, float(ss.rz_b_plate_mm),
                step=0.5, format="%.1f", key="_num_bp")
            ss.rz_h_plate_mm = st.number_input(
                "Height h [mm]", 0.5, 20.0, float(ss.rz_h_plate_mm),
                step=0.1, format="%.1f", key="_num_hp")

        st.markdown("**Material**")
        mat_keys = list(MATERIALS.keys())
        ss.rz_material = st.selectbox(
            "Material", mat_keys,
            index=mat_keys.index(ss.rz_material),
            key="_sel_mat",
        )
        if ss.rz_material == "Custom":
            ss.rz_rho_custom = st.number_input(
                "Density ρ [kg/m³]", 100.0, 20000.0,
                float(ss.rz_rho_custom), step=10.0, key="_num_rho")
            ss.rz_sigma_custom = st.number_input(
                "Allowable stress σ [MPa]", 1.0, 2000.0,
                float(ss.rz_sigma_custom), step=5.0, key="_num_sig")
        else:
            m = MATERIALS[ss.rz_material]
            st.caption(
                f"ρ = {m['rho']:.0f} kg/m³  ·  σ_allow = {m['sigma_allow_MPa']:.0f} MPa"
            )

    with col_right:
        st.markdown("**Geometry & safety**")
        ss.rz_D_prop_mm = st.number_input(
            "Propeller diameter D [mm]", 50.0, 800.0,
            float(ss.rz_D_prop_mm), step=5.0, format="%.0f", key="_num_Dp")
        ss.rz_k_arm = st.slider(
            "Arm length factor k_arm  (L_arm = k × D/2)",
            1.2, 6.0, float(ss.rz_k_arm), step=0.05, format="%.2f",
            help="k=2 → L_arm = D (tight packing); k=3 → L_arm = 1.5D (comfortable clearance).",
            key="_sl_karm",
        )
        ss.rz_FoS_req = st.number_input(
            "Required factor of safety FoS", 1.0, 5.0,
            float(ss.rz_FoS_req), step=0.1, format="%.1f", key="_num_fos")
        ss.rz_c_margin_mm = st.number_input(
            "Prop clearance margin [mm]", 0.0, 50.0,
            float(ss.rz_c_margin_mm), step=1.0, format="%.0f", key="_num_cm")
        ss.rz_M_body_g = st.number_input(
            "Body / frame mass (excl. arms) [g]", 0.0, 500.0,
            float(ss.rz_M_body_g), step=1.0, format="%.1f",
            help="Central frame, landing gear, screws, etc.", key="_num_body")

    st.markdown("---")

    # ── Live computation ──────────────────────────────────────────────────────
    res = _compute_and_store()

    c1, c2, c3, c4 = st.columns(4, gap="small")
    c1.metric("L_arm",   f"{res['L_arm_m']*1000:.1f} mm")
    c2.metric("m_arm",   f"{res['m_one_arm_g']:.2f} g")
    c3.metric("M_struct",f"{res['M_struct_g']:.2f} g")
    c4.metric("A_cross", f"{res['A']*1e6:.3f} mm²")

    st.markdown("---")

    col_str, col_clr = st.columns([1, 1], gap="large")

    with col_str:
        st.markdown("### Stress Check")
        st.latex(r"\sigma_{root} = \frac{M_{bend} \cdot c}{I} = \frac{T_{max} \cdot L_{arm} \cdot c}{I}")
        ok     = res["stress_ok"]
        color  = "#16a34a" if ok else "#dc2626"
        badge  = "converged-badge" if ok else "warn-badge"
        symbol = "✓" if ok else "✗"

        st.markdown(
            f'<span class="{badge}">{symbol} FoS = {res["FoS_actual"]:.3f} '
            f'(req ≥ {ss.rz_FoS_req:.1f})</span>',
            unsafe_allow_html=True,
        )
        st.markdown(f"""
<div style="background:#ffffff;border:1px solid #e5e7eb;border-left:3px solid {color};
            border-radius:0 8px 8px 0;padding:10px 14px;margin-top:10px;font-size:0.83rem;">
  <b>σ_root</b> = {res['sigma_MPa']:.3f} MPa<br>
  <b>σ_allow</b> = {res['sigma_allow']:.0f} MPa<br>
  <b>T_max</b> = {ss.rz_T_max_N:.3f} N &nbsp;(2 × T_hover)<br>
  <b>I</b> = {res['I']:.4e} m⁴ &nbsp;·&nbsp; <b>c</b> = {res['c']*1000:.3f} mm
</div>
""", unsafe_allow_html=True)

    with col_clr:
        st.markdown("### Propeller Clearance")
        st.latex(r"d_{between} = 2 L_{arm} \sin\!\left(\frac{\pi}{n_{motors}}\right)")
        clr_ok = res["clear_ok"]
        cbadge = "converged-badge" if clr_ok else "warn-badge"
        csym   = "✓" if clr_ok else "✗"

        st.markdown(
            f'<span class="{cbadge}">{csym} d_between = {res["d_between"]*1000:.1f} mm'
            f' (need > {ss.rz_D_prop_mm + ss.rz_c_margin_mm:.0f} mm)</span>',
            unsafe_allow_html=True,
        )
        st.markdown(f"""
<div style="background:#ffffff;border:1px solid #e5e7eb;border-left:3px solid {"#16a34a" if clr_ok else "#dc2626"};
            border-radius:0 8px 8px 0;padding:10px 14px;margin-top:10px;font-size:0.83rem;">
  <b>d_between</b> = {res['d_between']*1000:.1f} mm<br>
  <b>D_prop</b> = {ss.rz_D_prop_mm:.0f} mm &nbsp;+&nbsp;
  <b>margin</b> = {ss.rz_c_margin_mm:.0f} mm<br>
  <b>L_arm</b> = {res['L_arm_m']*1000:.1f} mm &nbsp;·&nbsp;
  <b>n_motors</b> = {ss.n_motors}
</div>
""", unsafe_allow_html=True)

    # Material reference
    with st.expander("Material reference"):
        import pandas as pd
        df = pd.DataFrame([
            {"Material": k, "ρ [kg/m³]": v["rho"],
             "σ_allow [MPa]": v["sigma_allow_MPa"]}
            for k, v in MATERIALS.items() if v["rho"] is not None
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)
