"""
Resizing Phase — 2D Layout (R6).
Top-view drawing, reference areas S_top and S_front.
"""
import streamlit as st
import matplotlib.pyplot as plt
from resizing.drawing_2d import (
    draw_top_view, fig_to_png_bytes, compute_reference_areas, CONFIG_ANGLES,
)


def render():
    st.markdown('<div class="section-tag">Resizing Phase · 2D Layout</div>',
                unsafe_allow_html=True)
    st.markdown("## R6 · 2D Top-View Layout & Reference Areas")

    ss = st.session_state

    col_inputs, col_drawing = st.columns([1, 1.4], gap="large")

    with col_inputs:
        st.markdown("**Layout parameters**")

        ss.resizing_D_prop_m = st.number_input(
            "Propeller diameter D [m]", 0.05, 1.0,
            float(ss.get("resizing_D_prop_m", 0.127)),
            step=0.005, format="%.4f", key="_ly_Dp",
            help="Auto-filled from R3 · Propulsion.",
        )
        ss.resizing_k_arm = st.slider(
            "k_arm  (L_arm = k × D/2)",
            1.0, 4.0, float(ss.get("resizing_k_arm", 1.2)),
            step=0.05, format="%.2f", key="_ly_karm",
        )
        ss.resizing_body_diameter = st.number_input(
            "Body diameter [m]", 0.01, 0.50,
            float(ss.get("resizing_body_diameter", 0.08)),
            step=0.005, format="%.3f", key="_ly_body",
            help="Central frame diameter for reference area computation.",
        )
        c_margin_mm = st.number_input(
            "Clearance margin [mm]", 0.0, 50.0,
            float(ss.get("resizing_c_margin_m", 0.010) * 1000),
            step=1.0, format="%.0f", key="_ly_cm",
        )
        ss.resizing_c_margin_m = c_margin_mm / 1000.0

        configs = list(CONFIG_ANGLES.keys())
        ss.resizing_config = st.selectbox(
            "Configuration",
            configs,
            index=configs.index(ss.get("resizing_config", "Quad X")),
            key="_ly_cfg",
        )

        # ── Derived quantities ────────────────────────────────────────────────
        L_arm_m   = ss.resizing_k_arm * ss.resizing_D_prop_m / 2.0
        D_prop_m  = ss.resizing_D_prop_m
        n_motors  = int(ss.get("n_motors", 4))
        span_mm   = (2.0 * L_arm_m + D_prop_m) * 1000.0

        # Prop clearance check
        from resizing.structure_resizing import prop_clearance
        d_between, clear_ok = prop_clearance(
            L_arm_m, D_prop_m, n_motors, ss.resizing_c_margin_m)
        ss.resizing_clearance_ok = clear_ok

        st.markdown(f"""
<div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:8px;
            padding:12px 14px;margin-top:10px;font-size:0.84rem;">
  <b>L_arm</b> = {L_arm_m*1000:.1f} mm &nbsp;·&nbsp;
  <b>Span</b> = {span_mm:.0f} mm<br>
  <b>{n_motors}× motors</b> &nbsp;·&nbsp;
  <b>{ss.resizing_config}</b><br>
  d_between = {d_between*1000:.1f} mm
  {'&nbsp;<span style="color:#16a34a;">✓ clear</span>' if clear_ok else
   '&nbsp;<span style="color:#dc2626;">✗ overlap</span>'}
</div>
""", unsafe_allow_html=True)

        # ── Reference areas ───────────────────────────────────────────────────
        st.markdown("**Reference Areas**")
        with st.expander("Equations & References"):
            st.markdown("**Top-view (hover/drag) reference area**")
            st.latex(r"S_{top} = n_m \pi R_{prop}^2 + n_m L_{arm} \cdot d_{out} + \pi r_{body}^2")
            st.markdown("**Frontal (cruise drag) reference area**")
            st.latex(r"S_{front} = n_m D_{prop} \cdot d_{out} + D_{body} \cdot \bar{h}_{body}")
            st.markdown("**Arm length and propeller span**")
            st.latex(r"L_{arm} = k_{arm} \cdot \frac{D_{prop}}{2}")
            st.latex(r"\mathrm{Span} = 2\,L_{arm} + D_{prop}")
            st.markdown("**Propeller tip clearance**")
            st.latex(r"d_{between} = 2\,L_{arm}\,\sin\!\left(\frac{\pi}{n_m}\right) > D_{prop} + c_{margin}")
            st.caption(
                "R_prop = D_prop/2; d_out = arm outer diameter from R4 · Structure. "
                "References: Pollet (2024) PhD Thesis §3.4; Tyan et al. (2017) §3.3"
            )
        d_out_m = float(ss.get("resizing_d_out", 0.010))  # from structure tab
        S_top, S_front = compute_reference_areas(
            L_arm_m, D_prop_m, n_motors, ss.resizing_config,
            ss.resizing_body_diameter, d_out_m,
        )
        ss.resizing_S_top   = S_top
        ss.resizing_S_front = S_front

        c1, c2 = st.columns(2)
        c1.metric("S_top",   f"{S_top*1e4:.2f} cm²")
        c2.metric("S_front", f"{S_front*1e4:.2f} cm²")
        st.latex(r"S_{top} = n_m \pi R^2 + n_m L_{arm} d_{out} + \pi r_{body}^2")
        st.caption(
            f"d_out = {d_out_m*1000:.2f} mm (from R4 · Structure). "
            "Set arm dimensions first for accurate S_front."
        )

    with col_drawing:
        st.markdown("**Top-view**")
        if L_arm_m > 0 and D_prop_m > 0:
            fig = draw_top_view(
                L_arm_m, D_prop_m, n_motors,
                ss.resizing_config, clear_ok,
                ss.resizing_c_margin_m,
                ss.resizing_body_diameter,
            )
            st.pyplot(fig, use_container_width=True)

            png_bytes = fig_to_png_bytes(fig)
            st.download_button(
                label="Download drawing (PNG)",
                data=png_bytes,
                file_name=f"swift_{ss.resizing_config.replace(' ', '_')}_top_view.png",
                mime="image/png",
            )
            plt.close(fig)
        else:
            st.info("Set propeller diameter and k_arm to generate layout.")

    st.markdown("---")
    st.markdown("""
<div class="info-box">
<b>S_top</b> is the drag reference area for hover/climb.
<b>S_front</b> is the frontal drag area used in the Aerodynamics tab for cruise.
CW/CCW spin directions are alternated for torque balance.
</div>
""", unsafe_allow_html=True)
