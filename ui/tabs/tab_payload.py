"""
Payload tab — payload mass, mass fraction, and power draw.
"""

import streamlit as st


def render():
    st.markdown('<div class="section-tag">Payload Definition</div>', unsafe_allow_html=True)
    st.markdown("## 02 · Payload")

    st.markdown("**Governing equations**")
    st.latex(r"\text{MTOW}_0 = \frac{m_{pay}}{MF_{pay}}")
    st.latex(r"P_{total} = n_{motors} \cdot P_{motor} + P_{avi} + P_{pay}")

    st.markdown("""
<div class="info-box">
The payload fraction <b>MF_pay</b> is the ratio of payload mass to total MTOW.
It provides the seed for the fixed-point loop. Typical range: 0.15–0.35.
Payload power <b>P_pay</b> is a fixed draw added on top of propulsion power.
</div>
""", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3, gap="medium")

    with col1:
        st.markdown("**Payload mass m_pay [kg]**")
        m_pay = st.number_input(
            "m_pay [kg]",
            min_value=0.001, max_value=25.0,
            value=float(st.session_state.m_pay),
            step=0.001, format="%.3f",
            help="Mass of the mission payload (camera, sensor, delivery package, etc.).",
            key="_inp_m_pay",
            label_visibility="collapsed",
        )
        st.session_state.m_pay = m_pay
        st.markdown("""
<div class="info-box">The payload mass is fixed throughout the sizing loop — it does not scale with MTOW.</div>
""", unsafe_allow_html=True)

    with col2:
        st.markdown("**Payload mass fraction MF_pay [—]**")
        MF_pay = st.number_input(
            "MF_pay [—]",
            min_value=0.05, max_value=0.60,
            value=float(st.session_state.MF_pay),
            step=0.01, format="%.2f",
            help="Fraction of MTOW allocated to payload. Start with 0.20–0.30 for early design.",
            key="_inp_MF_pay",
            label_visibility="collapsed",
        )
        st.session_state.MF_pay = MF_pay
        st.markdown("""
<div class="info-box">Used only to compute the seed MTOW. Final payload fraction is re-computed from the converged MTOW.</div>
""", unsafe_allow_html=True)

    with col3:
        st.markdown("**Payload power draw P_pay [W]**")
        P_pay = st.number_input(
            "P_pay [W]",
            min_value=0.0, max_value=500.0,
            value=float(st.session_state.P_pay),
            step=0.5, format="%.1f",
            help="Continuous power consumed by the payload (gimbal, sensors, etc.).",
            key="_inp_P_pay",
            label_visibility="collapsed",
        )
        st.session_state.P_pay = P_pay
        st.markdown("""
<div class="info-box">Added directly to P_total in the battery energy equation.</div>
""", unsafe_allow_html=True)

    st.markdown("---")

    M_TO0 = m_pay / MF_pay if MF_pay > 0 else 0.0

    c1, c2, c3, c4 = st.columns(4, gap="medium")
    c1.metric("m_pay", f"{m_pay * 1000:.0f} g")
    c2.metric("MF_pay", f"{MF_pay:.4g}")
    c3.metric("P_pay", f"{P_pay:.4g} W")
    c4.metric("MTOW₀ (seed)", f"{M_TO0:.4g} kg")

    if M_TO0 > 25:
        st.warning(
            f"Seed MTOW of **{M_TO0:.1f} kg** is unusually large. Check payload mass and fraction."
        )
    elif M_TO0 < 0.1:
        st.info(
            f"Seed MTOW of **{M_TO0*1000:.0f} g** — micro UAV regime. Verify MF_pay is appropriate."
        )

    st.markdown("---")
    st.markdown("### Payload Fraction Guidelines")
    st.markdown("""
<div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 18px;">
<table style="width:100%;font-size:0.83rem;border-collapse:collapse;">
<tr>
  <th style="color:#d97706;padding:5px 10px;text-align:left;border-bottom:1px solid #e5e7eb;">Mission type</th>
  <th style="color:#d97706;padding:5px 10px;text-align:left;border-bottom:1px solid #e5e7eb;">Typical MF_pay</th>
  <th style="color:#d97706;padding:5px 10px;text-align:left;border-bottom:1px solid #e5e7eb;">Notes</th>
</tr>
<tr><td style="padding:5px 10px;color:#1a1a1a;">Racing / Acrobatic</td><td style="padding:5px 10px;color:#6b7280;">0.05 – 0.10</td><td style="padding:5px 10px;color:#6b7280;">Minimal payload, maximise agility</td></tr>
<tr><td style="padding:5px 10px;color:#1a1a1a;">Aerial Photography</td><td style="padding:5px 10px;color:#1a1a1a;">0.15 – 0.25</td><td style="padding:5px 10px;color:#6b7280;">Camera + gimbal dominant</td></tr>
<tr><td style="padding:5px 10px;color:#1a1a1a;">Inspection / Survey</td><td style="padding:5px 10px;color:#1a1a1a;">0.20 – 0.30</td><td style="padding:5px 10px;color:#6b7280;">Sensor + data link mass</td></tr>
<tr><td style="padding:5px 10px;color:#1a1a1a;">Delivery / Cargo</td><td style="padding:5px 10px;color:#1a1a1a;">0.25 – 0.40</td><td style="padding:5px 10px;color:#6b7280;">High payload fraction target</td></tr>
</table>
</div>
""", unsafe_allow_html=True)
