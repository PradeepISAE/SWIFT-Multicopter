"""
Propulsion tab — datasheet motor/propeller inputs, voltage selection.
No empirical model — mass is computed directly from datasheet values.
"""

import streamlit as st
from core.propulsion import propulsion_mass_kg, specific_mass_ratio


_VOLT_OPTIONS = {
    "2S – 7.4 V":  7.4,
    "3S – 11.1 V": 11.1,
    "4S – 14.8 V": 14.8,
    "6S – 22.2 V": 22.2,
}
_VOLT_LABELS = list(_VOLT_OPTIONS.keys())
_VOLT_VALUES = list(_VOLT_OPTIONS.values())


def _volt_label(v: float) -> str:
    for label, val in _VOLT_OPTIONS.items():
        if abs(val - v) < 0.1:
            return label
    return f"{v:.1f} V"


def render():
    st.markdown('<div class="section-tag">Propulsion System Definition</div>', unsafe_allow_html=True)
    st.markdown("## 05 · Propulsion")

    st.markdown("**Governing equation**")
    st.latex(
        r"M_{prop} = n_{motors} \times \left(M_{motor} + M_{prop/motor}\right)"
    )

    st.markdown("""
<div class="info-box">
Propulsion mass is computed <b>directly from datasheet values</b> — no empirical model.
Enter the per-unit motor mass and propeller mass from the manufacturer's datasheet.
The result is a fixed mass added at every iteration of the sizing loop.
</div>
""", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown("**Motor identification**")
        motor_label = st.text_input(
            "Motor type / designation",
            value=str(st.session_state.motor_label),
            help="Free-text motor label (e.g. 'T-Motor MN1806 2300KV').",
            key="_inp_motor_label",
            label_visibility="collapsed",
            placeholder="e.g. T-Motor MN1806 2300KV",
        )
        st.session_state.motor_label = motor_label

        st.markdown("---")
        st.markdown("**Per-motor datasheet values**")

        M_motor_g = st.number_input(
            "Motor mass M_motor [g]",
            min_value=0.1, max_value=2000.0,
            value=float(st.session_state.M_motor_g),
            step=0.1, format="%.1f",
            help="Single motor body mass from datasheet (g).",
            key="_num_M_motor_g",
        )
        st.session_state.M_motor_g = M_motor_g

        M_prop_g = st.number_input(
            "Propeller mass M_prop [g]",
            min_value=0.1, max_value=500.0,
            value=float(st.session_state.M_prop_g),
            step=0.1, format="%.1f",
            help="Single propeller mass from datasheet (g). Include hub/nut if applicable.",
            key="_num_M_prop_g",
        )
        st.session_state.M_prop_g = M_prop_g

        P_max_W = st.number_input(
            "Max motor power P_max [W]  (reference only)",
            min_value=1.0, max_value=10000.0,
            value=float(st.session_state.P_max_W),
            step=1.0, format="%.0f",
            help="Datasheet maximum continuous power. Used only to compute specific mass ratio — NOT used in mass sizing.",
            key="_num_P_max_W",
        )
        st.session_state.P_max_W = P_max_W

        st.markdown("**Battery voltage**")
        default_label = _volt_label(st.session_state.V_batt)
        volt_label = st.selectbox(
            "V_batt [V]",
            options=_VOLT_LABELS,
            index=_VOLT_LABELS.index(default_label) if default_label in _VOLT_LABELS else 1,
            help="Nominal pack voltage. Used for battery capacity calculation (mAh).",
            key="_sel_V_batt",
            label_visibility="collapsed",
        )
        V_batt = _VOLT_OPTIONS[volt_label]
        st.session_state.V_batt = V_batt

    with col2:
        st.markdown("**Propulsion mass summary**")

        n_motors = st.session_state.n_motors
        prop = propulsion_mass_kg(n_motors, M_motor_g, M_prop_g)
        sm   = specific_mass_ratio(M_motor_g, P_max_W)

        c1, c2 = st.columns(2, gap="small")
        c1.metric("M_prop total", f"{prop['M_prop'] * 1000:.4g} g")
        c2.metric("M_prop total", f"{prop['M_prop']:.4g} kg")

        c3, c4 = st.columns(2, gap="small")
        c3.metric("All motors", f"{prop['m_motors_kg'] * 1000:.4g} g")
        c4.metric("All propellers", f"{prop['m_props_kg'] * 1000:.4g} g")

        st.markdown("""
<div class="info-box">
<b>Specific mass ratio (reference)</b><br>
M_motor / P_max = {:.4g} g/W<br>
<span style="font-size:0.80rem;">Lower = lighter motor per watt — better for efficiency.
Typical: 0.05 – 0.15 g/W for quality outrunners. <b>Not used in sizing calculations.</b></span>
</div>
""".format(sm), unsafe_allow_html=True)

        st.markdown("**Mass breakdown**")
        st.markdown(f"""
<div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 18px;">
<table style="width:100%;font-size:0.84rem;border-collapse:collapse;">
<tr>
  <th style="color:#d97706;padding:5px 10px;text-align:left;border-bottom:1px solid #e5e7eb;">Component</th>
  <th style="color:#d97706;padding:5px 10px;text-align:right;border-bottom:1px solid #e5e7eb;">Per unit [g]</th>
  <th style="color:#d97706;padding:5px 10px;text-align:right;border-bottom:1px solid #e5e7eb;">× {n_motors} total [g]</th>
</tr>
<tr>
  <td style="padding:6px 10px;color:#1a1a1a;">Motor ({motor_label})</td>
  <td style="padding:6px 10px;color:#1a1a1a;text-align:right;">{M_motor_g:.4g}</td>
  <td style="padding:6px 10px;color:#1a1a1a;text-align:right;">{M_motor_g * n_motors:.4g}</td>
</tr>
<tr>
  <td style="padding:6px 10px;color:#1a1a1a;">Propeller</td>
  <td style="padding:6px 10px;color:#1a1a1a;text-align:right;">{M_prop_g:.4g}</td>
  <td style="padding:6px 10px;color:#1a1a1a;text-align:right;">{M_prop_g * n_motors:.4g}</td>
</tr>
<tr style="border-top:2px solid #e5e7eb;">
  <td style="padding:6px 10px;color:#d97706;font-weight:700;">M_prop (total)</td>
  <td style="padding:6px 10px;color:#d97706;font-weight:700;text-align:right;">—</td>
  <td style="padding:6px 10px;color:#d97706;font-weight:700;text-align:right;">{prop['M_prop'] * 1000:.4g}</td>
</tr>
</table>
</div>
""", unsafe_allow_html=True)

        st.markdown("**Battery voltage selection**")
        st.markdown(f"""
<div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 18px;">
<table style="width:100%;font-size:0.83rem;border-collapse:collapse;">
<tr>
  <th style="color:#d97706;padding:5px 10px;border-bottom:1px solid #e5e7eb;">Config</th>
  <th style="color:#d97706;padding:5px 10px;border-bottom:1px solid #e5e7eb;">Voltage</th>
  <th style="color:#d97706;padding:5px 10px;border-bottom:1px solid #e5e7eb;">Typical class</th>
</tr>
<tr><td style="padding:5px 10px;color:#1a1a1a;">2S LiPo</td><td style="padding:5px 10px;color:#6b7280;">7.4 V</td><td style="padding:5px 10px;color:#6b7280;">Micro / nano</td></tr>
<tr><td style="padding:5px 10px;{'color:#d97706;font-weight:700' if abs(V_batt-11.1)<0.1 else 'color:#1a1a1a'};">3S LiPo</td><td style="padding:5px 10px;color:#6b7280;">11.1 V</td><td style="padding:5px 10px;color:#6b7280;">Mini / small</td></tr>
<tr><td style="padding:5px 10px;{'color:#d97706;font-weight:700' if abs(V_batt-14.8)<0.1 else 'color:#1a1a1a'};">4S LiPo</td><td style="padding:5px 10px;color:#6b7280;">14.8 V</td><td style="padding:5px 10px;color:#6b7280;">Medium / photo</td></tr>
<tr><td style="padding:5px 10px;color:#1a1a1a;">6S LiPo</td><td style="padding:5px 10px;color:#6b7280;">22.2 V</td><td style="padding:5px 10px;color:#6b7280;">Large / industrial</td></tr>
</table>
</div>
""", unsafe_allow_html=True)
