"""
Structures tab — structural mass fraction.
"""

import streamlit as st
import numpy as np
import plotly.graph_objects as go


def render():
    st.markdown('<div class="section-tag">Structural Mass Estimate</div>', unsafe_allow_html=True)
    st.markdown("## 03 · Structures")

    st.markdown("**Governing equation**")
    st.latex(r"M_{str} = MF_{str} \times \text{MTOW}")

    st.markdown("""
<div class="info-box">
The structural mass fraction <b>MF_str</b> accounts for the airframe, arms, landing gear,
vibration dampers, fasteners, and wiring harness — everything except motors, propellers,
avionics, battery, and payload. It scales with MTOW at every iteration.
</div>
""", unsafe_allow_html=True)

    col1, col2 = st.columns([2, 3], gap="large")

    with col1:
        st.markdown("**Structural mass fraction MF_str [—]**")
        MF_str = st.slider(
            "MF_str [—]",
            min_value=0.10, max_value=0.50,
            value=float(st.session_state.MF_str),
            step=0.01, format="%.2f",
            help="Typical range 0.15–0.35 for commercial multicopters.",
            key="_sl_MF_str",
        )
        st.session_state.MF_str = MF_str

        MF_str_num = st.number_input(
            "Or type directly:",
            min_value=0.10, max_value=0.50,
            value=float(MF_str),
            step=0.01, format="%.3f",
            key="_num_MF_str",
        )
        if abs(MF_str_num - MF_str) > 1e-6:
            st.session_state.MF_str = MF_str_num
            MF_str = MF_str_num

        m_pay  = st.session_state.m_pay
        MF_pay = st.session_state.MF_pay
        M_TO_est  = m_pay / MF_pay if MF_pay > 0 else 0.0
        M_str_est = MF_str * M_TO_est

        st.markdown("---")
        st.metric("MF_str", f"{MF_str:.4g}")
        st.metric("M_str at MTOW₀", f"{M_str_est * 1000:.4g} g",
                  help="Structural mass at the seed MTOW (updates at convergence).")

    with col2:
        st.markdown("**MTOW multiplier vs MF_str**")
        st.caption("Shows how structural fraction amplifies the non-structural mass into total MTOW.")

        fs_range = np.linspace(0.10, 0.50, 200)
        factor   = 1.0 / (1.0 - fs_range)

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=fs_range, y=factor,
            mode="lines",
            line=dict(color="#d97706", width=2.5),
            fill="tozeroy",
            fillcolor="rgba(217,119,6,0.06)",
            name="MTOW / non-structural",
            hovertemplate="MF_str=%{x:.2f}<br>Multiplier=%{y:.3f}×<extra></extra>",
        ))
        fig.add_vline(
            x=MF_str, line_dash="dash", line_color="#d97706",
            annotation_text=f"Current: {MF_str:.2f}",
            annotation_font_color="#d97706",
        )
        fig.update_layout(
            paper_bgcolor="#ffffff", plot_bgcolor="#f9fafb",
            font=dict(color="#374151", size=11),
            xaxis=dict(title="MF_str [—]", gridcolor="#e5e7eb",
                       title_font_color="#6b7280"),
            yaxis=dict(title="MTOW multiplier [—]", gridcolor="#e5e7eb",
                       title_font_color="#6b7280"),
            showlegend=False,
            height=240,
            margin=dict(l=10, r=10, t=10, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("**Frame architecture reference**")
        st.markdown("""
<div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 18px;">
<table style="width:100%;font-size:0.82rem;border-collapse:collapse;">
<tr>
  <th style="color:#d97706;padding:5px 10px;text-align:left;border-bottom:1px solid #e5e7eb;">Frame / Architecture</th>
  <th style="color:#d97706;padding:5px 10px;text-align:left;border-bottom:1px solid #e5e7eb;">MF_str</th>
  <th style="color:#d97706;padding:5px 10px;text-align:left;border-bottom:1px solid #e5e7eb;">Material</th>
</tr>
<tr><td style="padding:5px 10px;color:#1a1a1a;">Mini quad (100–250 mm)</td><td style="padding:5px 10px;color:#6b7280;">0.12 – 0.20</td><td style="padding:5px 10px;color:#6b7280;">CF plate</td></tr>
<tr><td style="padding:5px 10px;color:#1a1a1a;">Racing quad (210–350 mm)</td><td style="padding:5px 10px;color:#6b7280;">0.15 – 0.22</td><td style="padding:5px 10px;color:#6b7280;">CF frame</td></tr>
<tr><td style="padding:5px 10px;color:#1a1a1a;">Photogrammetry quad</td><td style="padding:5px 10px;color:#1a1a1a;font-weight:600;">0.20 – 0.30</td><td style="padding:5px 10px;color:#6b7280;">CF tube frame</td></tr>
<tr><td style="padding:5px 10px;color:#1a1a1a;">Hexacopter (450–900 mm)</td><td style="padding:5px 10px;color:#6b7280;">0.25 – 0.35</td><td style="padding:5px 10px;color:#6b7280;">CF/Al hybrid</td></tr>
<tr><td style="padding:5px 10px;color:#1a1a1a;">Heavy-lift octocopter</td><td style="padding:5px 10px;color:#6b7280;">0.28 – 0.42</td><td style="padding:5px 10px;color:#6b7280;">Al/CF folding arms</td></tr>
</table>
</div>
""", unsafe_allow_html=True)
