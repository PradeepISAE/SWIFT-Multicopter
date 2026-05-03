"""
Resizing Phase — Mission tab.
Flight time, DoD, eta, configuration selector, and 2D top-view drawing.
"""
import streamlit as st
from resizing.drawing_2d import draw_top_view, fig_to_png_bytes, CONFIG_ANGLES


def render():
    st.markdown('<div class="section-tag">Resizing Phase · Mission</div>',
                unsafe_allow_html=True)
    st.markdown("## R5 · Mission Parameters & Layout")

    ss = st.session_state

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown("**Mission inputs**")

        ss.rz_t_flight_min = st.number_input(
            "Flight time t [min]",
            min_value=1.0, max_value=120.0,
            value=float(ss.get("rz_t_flight_min", ss.t_flight_min)),
            step=0.5, format="%.1f",
            help="Target endurance for the resizing loop.",
            key="_num_rz_t",
        )
        ss.rz_DoD = st.slider(
            "Depth of Discharge DoD [—]",
            min_value=0.50, max_value=0.99,
            value=float(ss.get("rz_DoD", ss.DoD)),
            step=0.01, format="%.2f",
            key="_sl_rz_dod",
        )
        ss.rz_eta_elec = st.slider(
            "Electrical efficiency η [—]",
            min_value=0.60, max_value=0.99,
            value=float(ss.get("rz_eta_elec", ss.eta_elec)),
            step=0.01, format="%.2f",
            key="_sl_rz_eta",
        )

        st.markdown("**Multirotor configuration**")
        configs = list(CONFIG_ANGLES.keys())
        n_motors = int(ss.n_motors)

        # Filter configs compatible with n_motors
        valid_configs = [c for c in configs if len(CONFIG_ANGLES[c]) >= n_motors]
        if not valid_configs:
            valid_configs = configs

        current_cfg = ss.get("rz_config", valid_configs[0])
        if current_cfg not in valid_configs:
            current_cfg = valid_configs[0]

        ss.rz_config = st.selectbox(
            "Configuration",
            valid_configs,
            index=valid_configs.index(current_cfg),
            key="_sel_rz_cfg",
        )

        # Summary
        L_arm_m  = ss.get("rz_L_arm_m",  0.10)
        D_prop_m = ss.get("rz_D_prop_m", 0.127)
        span_mm  = (2 * L_arm_m + D_prop_m) * 1000.0

        st.markdown(f"""
<div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:8px;
            padding:12px 14px;margin-top:12px;font-size:0.84rem;">
  <b>L_arm</b> = {L_arm_m*1000:.1f} mm &nbsp;·&nbsp;
  <b>D_prop</b> = {D_prop_m*1000:.0f} mm<br>
  <b>Span</b> = {span_mm:.0f} mm &nbsp;·&nbsp;
  <b>{n_motors}× motors</b> &nbsp;·&nbsp;
  <b>{ss.rz_config}</b>
</div>
""", unsafe_allow_html=True)

    with col_right:
        st.markdown("**Top-view layout**")
        clearance_ok = ss.get("rz_clearance_ok", True)
        c_margin_m   = ss.get("rz_c_margin_mm", 10.0) / 1000.0

        if L_arm_m > 0 and D_prop_m > 0:
            fig = draw_top_view(
                L_arm_m, D_prop_m, n_motors,
                ss.rz_config, clearance_ok, c_margin_m,
            )
            st.pyplot(fig, use_container_width=True)

            png_bytes = fig_to_png_bytes(fig)
            st.download_button(
                label="⬇  Download drawing (PNG)",
                data=png_bytes,
                file_name=f"swift_{ss.rz_config.replace(' ', '_')}_top_view.png",
                mime="image/png",
                help="Save the top-view layout as a PNG image.",
            )
            import matplotlib.pyplot as plt
            plt.close(fig)
        else:
            st.info("Set arm geometry in R1 · Structure first.")

    st.markdown("---")
    st.markdown("""
<div class="info-box">
<b>CW/CCW spin directions</b> are alternated automatically for torque balance.
Motor numbering follows the configuration angles clockwise from the first arm.
</div>
""", unsafe_allow_html=True)
