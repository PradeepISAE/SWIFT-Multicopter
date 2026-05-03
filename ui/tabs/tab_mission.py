"""
Mission tab — UAV name, number of motors, flight time, avionics power.
"""

import streamlit as st


def render():
    st.markdown('<div class="section-tag">Mission Definition</div>', unsafe_allow_html=True)
    st.markdown("## 01 · Mission")

    st.markdown("""
<div class="info-box">
Define the top-level mission parameters. These drive the seed MTOW estimate
and appear throughout the sizing loop. Work left-to-right through the tabs to
complete the sizing.
</div>
""", unsafe_allow_html=True)

    st.markdown("**Sizing seed equation**")
    st.latex(r"\text{MTOW}_0 = \frac{m_{pay}}{MF_{pay}}")
    st.caption("The seed MTOW (set in the Payload tab) is the starting point of the fixed-point iteration.")

    st.markdown("---")

    col1, col2, col3, col4 = st.columns(4, gap="medium")

    with col1:
        st.markdown("**UAV name / designation**")
        uav_name = st.text_input(
            "UAV name",
            value=str(st.session_state.uav_name),
            help="Free-text identifier for this sizing run.",
            key="_inp_uav_name",
            label_visibility="collapsed",
        )
        st.session_state.uav_name = uav_name
        st.markdown("""
<div class="info-box">Label used in results header and CSV export.</div>
""", unsafe_allow_html=True)

    with col2:
        st.markdown("**Number of motors**")
        n_motors = st.selectbox(
            "n_motors",
            options=[4, 6, 8],
            index=[4, 6, 8].index(int(st.session_state.n_motors)),
            help="4 = quadrotor · 6 = hexacopter · 8 = octocopter",
            key="_sel_n_motors",
            label_visibility="collapsed",
        )
        st.session_state.n_motors = int(n_motors)
        st.markdown("""
<div class="info-box">Determines how total MTOW is divided across motors for thrust and power calculations.</div>
""", unsafe_allow_html=True)

    with col3:
        st.markdown("**Target flight time [min]**")
        t_flight_min = st.number_input(
            "t_flight [min]",
            min_value=1.0, max_value=120.0,
            value=float(st.session_state.t_flight_min),
            step=1.0, format="%.0f",
            help="Target hover-equivalent flight endurance.",
            key="_num_t_flight",
            label_visibility="collapsed",
        )
        st.session_state.t_flight_min = t_flight_min
        st.markdown("""
<div class="info-box">Converted to hours inside the battery energy equation: E = P × t.</div>
""", unsafe_allow_html=True)

    with col4:
        st.markdown("**Avionics power P_avi [W]**")
        P_avi = st.number_input(
            "P_avi [W]",
            min_value=0.0, max_value=100.0,
            value=float(st.session_state.P_avi),
            step=0.5, format="%.1f",
            help="Continuous power draw of all avionics (FC, GPS, telemetry, etc.).",
            key="_num_P_avi",
            label_visibility="collapsed",
        )
        st.session_state.P_avi = P_avi
        st.markdown("""
<div class="info-box">Added to propulsion power in the total power equation: P_total = n × P_motor + P_avi + P_pay.</div>
""", unsafe_allow_html=True)

    st.markdown("---")

    # Quick summary metrics
    c1, c2, c3, c4 = st.columns(4, gap="medium")
    c1.metric("UAV", st.session_state.uav_name)
    c2.metric("Motors", f"{n_motors}×")
    c3.metric("Flight time", f"{t_flight_min:.0f} min  ({t_flight_min/60:.3f} h)")
    c4.metric("P_avi", f"{P_avi:.1f} W")

    st.markdown("---")
    st.markdown("### Sizing Flow Overview")

    st.markdown("""
<div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:10px;padding:18px 22px;
            font-family:monospace;font-size:0.82rem;line-height:1.9;color:#374151;">
<span style="color:#d97706;font-weight:700;">①</span> PAYLOAD    →  m_pay, MF_pay, P_pay<br>
<span style="color:#d97706;font-weight:700;">②</span> SEED       →  MTOW₀ = m_pay / MF_pay<br>
<span style="color:#d97706;font-weight:700;">③</span> STRUCTURE  →  M_str = MF_str × MTOW<br>
<span style="color:#d97706;font-weight:700;">④</span> AVIONICS   →  M_avi = MF_avi × MTOW<br>
<span style="color:#d97706;font-weight:700;">⑤</span> PROPULSION →  M_prop = n_motors × (M_motor + M_prop/motor)  [fixed]<br>
<span style="color:#d97706;font-weight:700;">⑥</span> BATTERY    →  T→P→E→M_batt<br>
<span style="color:#d97706;font-weight:700;">⑦</span> UPDATE     →  MTOW_new = m_pay + M_str + M_avi + M_prop + M_batt<br>
<span style="color:#6b7280;font-weight:700;">⑧</span> CHECK      →  |ΔMTOW| &lt; 1×10⁻⁴ kg  →  <span style="color:#16a34a;font-weight:700;">CONVERGED</span>
</div>
""", unsafe_allow_html=True)

    st.markdown("### Symbol Reference")
    st.markdown("""
<div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 18px;">
<table style="width:100%;font-size:0.83rem;border-collapse:collapse;">
<tr>
  <th style="color:#d97706;padding:5px 10px;text-align:left;border-bottom:1px solid #e5e7eb;">Symbol</th>
  <th style="color:#d97706;padding:5px 10px;text-align:left;border-bottom:1px solid #e5e7eb;">Description</th>
  <th style="color:#d97706;padding:5px 10px;text-align:left;border-bottom:1px solid #e5e7eb;">Unit</th>
</tr>
<tr><td style="padding:5px 10px;color:#1a1a1a;">MTOW</td><td style="padding:5px 10px;color:#6b7280;">Max Take-Off mass</td><td style="padding:5px 10px;color:#1a1a1a;">kg</td></tr>
<tr><td style="padding:5px 10px;color:#1a1a1a;">MF_pay</td><td style="padding:5px 10px;color:#6b7280;">Payload mass fraction = m_pay / MTOW</td><td style="padding:5px 10px;color:#1a1a1a;">—</td></tr>
<tr><td style="padding:5px 10px;color:#1a1a1a;">MF_str</td><td style="padding:5px 10px;color:#6b7280;">Structural mass fraction</td><td style="padding:5px 10px;color:#1a1a1a;">—</td></tr>
<tr><td style="padding:5px 10px;color:#1a1a1a;">MF_avi</td><td style="padding:5px 10px;color:#6b7280;">Avionics mass fraction</td><td style="padding:5px 10px;color:#1a1a1a;">—</td></tr>
<tr><td style="padding:5px 10px;color:#1a1a1a;">PL</td><td style="padding:5px 10px;color:#6b7280;">Power loading = thrust / motor power</td><td style="padding:5px 10px;color:#1a1a1a;">g/W</td></tr>
<tr><td style="padding:5px 10px;color:#1a1a1a;">SED</td><td style="padding:5px 10px;color:#6b7280;">Battery specific energy density</td><td style="padding:5px 10px;color:#1a1a1a;">Wh/kg</td></tr>
<tr><td style="padding:5px 10px;color:#1a1a1a;">DoD</td><td style="padding:5px 10px;color:#6b7280;">Depth of Discharge</td><td style="padding:5px 10px;color:#1a1a1a;">—</td></tr>
<tr><td style="padding:5px 10px;color:#1a1a1a;">η_elec</td><td style="padding:5px 10px;color:#6b7280;">Electrical efficiency (ESC + motor + wiring)</td><td style="padding:5px 10px;color:#1a1a1a;">—</td></tr>
</table>
</div>
""", unsafe_allow_html=True)
