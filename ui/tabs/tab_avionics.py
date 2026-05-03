"""
Avionics tab — avionics mass fraction with estimated mass note.
"""

import streamlit as st


def render():
    st.markdown('<div class="section-tag">Avionics Mass Estimate</div>', unsafe_allow_html=True)
    st.markdown("## 04 · Avionics")

    st.markdown("**Governing equation**")
    st.latex(r"M_{avi} = MF_{avi} \times \text{MTOW}")

    st.markdown("""
<div class="info-box">
The avionics mass fraction <b>MF_avi</b> accounts for the flight controller, ESC stack,
GPS, telemetry, RC receiver, and other electronics. It scales with MTOW at every
iteration of the sizing loop. Typical range: 0.08 – 0.20 for small multicopters.
</div>
""", unsafe_allow_html=True)

    col1, col2 = st.columns([2, 3], gap="large")

    with col1:
        st.markdown("**Avionics mass fraction MF_avi [—]**")
        MF_avi = st.slider(
            "MF_avi [—]",
            min_value=0.02, max_value=0.35,
            value=float(st.session_state.MF_avi),
            step=0.01, format="%.2f",
            help="Typical range 0.08–0.20 for small multicopters.",
            key="_sl_MF_avi",
        )
        st.session_state.MF_avi = MF_avi

        MF_avi_num = st.number_input(
            "Or type directly:",
            min_value=0.02, max_value=0.35,
            value=float(MF_avi),
            step=0.01, format="%.3f",
            key="_num_MF_avi",
        )
        if abs(MF_avi_num - MF_avi) > 1e-6:
            st.session_state.MF_avi = MF_avi_num
            MF_avi = MF_avi_num

        m_pay  = st.session_state.m_pay
        MF_pay = st.session_state.MF_pay
        MF_str = st.session_state.MF_str
        M_TO_est  = m_pay / MF_pay if MF_pay > 0 else 0.0
        M_avi_est = MF_avi * M_TO_est

        st.markdown("---")
        st.metric("MF_avi", f"{MF_avi:.4g}")
        st.metric("M_avi at MTOW₀", f"{M_avi_est * 1000:.4g} g",
                  help="Estimated avionics mass at the seed MTOW (updates at convergence).")

        pct = MF_avi * 100
        st.caption(
            f"With MF_str = {MF_str:.2f}, MF_avi = {MF_avi:.2f}: "
            f"structural + avionics = **{(MF_str + MF_avi)*100:.1f} %** of MTOW."
        )

    with col2:
        st.markdown("**Avionics mass fraction reference**")
        st.markdown("""
<div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 18px;margin-bottom:16px;">
<table style="width:100%;font-size:0.82rem;border-collapse:collapse;">
<tr>
  <th style="color:#d97706;padding:5px 10px;text-align:left;border-bottom:1px solid #e5e7eb;">Configuration</th>
  <th style="color:#d97706;padding:5px 10px;text-align:left;border-bottom:1px solid #e5e7eb;">MF_avi</th>
  <th style="color:#d97706;padding:5px 10px;text-align:left;border-bottom:1px solid #e5e7eb;">Notes</th>
</tr>
<tr><td style="padding:5px 10px;color:#1a1a1a;">Minimal (AIO + RX only)</td><td style="padding:5px 10px;color:#6b7280;">0.06 – 0.10</td><td style="padding:5px 10px;color:#6b7280;">Racing / micro UAV</td></tr>
<tr><td style="padding:5px 10px;color:#1a1a1a;">Standard (FC + GPS + telem)</td><td style="padding:5px 10px;color:#1a1a1a;font-weight:600;">0.10 – 0.18</td><td style="padding:5px 10px;color:#6b7280;">Typical survey quad</td></tr>
<tr><td style="padding:5px 10px;color:#1a1a1a;">Full (Pixhawk + full suite)</td><td style="padding:5px 10px;color:#6b7280;">0.15 – 0.25</td><td style="padding:5px 10px;color:#6b7280;">Professional / redundant</td></tr>
</table>
</div>
""", unsafe_allow_html=True)

        st.markdown("**Estimated avionics mass vs MTOW**")
        if M_TO_est > 0:
            import numpy as np
            import plotly.graph_objects as go

            mtow_range = np.linspace(0.05, 2.0, 200)
            m_avi_range = MF_avi * mtow_range * 1000  # grams

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=mtow_range, y=m_avi_range,
                mode="lines",
                line=dict(color="#d97706", width=2.5),
                name=f"M_avi (MF_avi = {MF_avi:.2f})",
                hovertemplate="MTOW=%{x:.3f} kg<br>M_avi=%{y:.0f} g<extra></extra>",
            ))
            fig.add_vline(
                x=M_TO_est, line_dash="dash", line_color="#6b7280",
                annotation_text=f"MTOW₀={M_TO_est:.3f} kg",
                annotation_font_color="#6b7280",
            )
            fig.update_layout(
                paper_bgcolor="#ffffff", plot_bgcolor="#f9fafb",
                font=dict(color="#374151", size=11),
                xaxis=dict(title="MTOW [kg]", gridcolor="#e5e7eb",
                           title_font_color="#6b7280"),
                yaxis=dict(title="M_avi [g]", gridcolor="#e5e7eb",
                           title_font_color="#6b7280"),
                showlegend=False,
                height=230,
                margin=dict(l=10, r=10, t=10, b=10),
            )
            st.plotly_chart(fig, use_container_width=True)
