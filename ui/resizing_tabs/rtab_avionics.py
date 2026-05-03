"""
Resizing Phase — Avionics tab.
Component-level mass and power table replaces the MF_avi fraction.
"""
import streamlit as st
import pandas as pd
from resizing.avionics_resizing import total_avionics

_DEFAULT_COMPONENTS = [
    {"Component": "Flight Controller",   "Enabled": True,  "Mass_g": 9.0,  "Power_W": 0.5},
    {"Component": "GPS / Compass",       "Enabled": True,  "Mass_g": 16.0, "Power_W": 0.3},
    {"Component": "Telemetry (433 MHz)", "Enabled": True,  "Mass_g": 5.5,  "Power_W": 0.2},
    {"Component": "RC Receiver",         "Enabled": True,  "Mass_g": 2.5,  "Power_W": 0.1},
    {"Component": "Power Module",        "Enabled": True,  "Mass_g": 6.0,  "Power_W": 0.2},
    {"Component": "Video Transmitter",   "Enabled": False, "Mass_g": 12.0, "Power_W": 1.5},
    {"Component": "FPV Camera",          "Enabled": False, "Mass_g": 14.0, "Power_W": 0.4},
    {"Component": "Optical Flow Sensor", "Enabled": False, "Mass_g": 3.5,  "Power_W": 0.2},
    {"Component": "ToF Range Sensor",    "Enabled": False, "Mass_g": 2.0,  "Power_W": 0.1},
    {"Component": "LED / Lighting",      "Enabled": False, "Mass_g": 5.0,  "Power_W": 0.8},
    {"Component": "Custom 1",            "Enabled": False, "Mass_g": 0.0,  "Power_W": 0.0},
    {"Component": "Custom 2",            "Enabled": False, "Mass_g": 0.0,  "Power_W": 0.0},
]


def render():
    st.markdown('<div class="section-tag">Resizing Phase · Avionics</div>',
                unsafe_allow_html=True)
    st.markdown("## R2 · Avionics Components")

    st.markdown("""
<div class="info-box">
Enable each component actually installed on your UAV. Edit masses and power draws to match
your datasheets. The totals feed directly into the resizing convergence loop as
<b>M_avi_fixed</b> and <b>P_avi</b>.
</div>
""", unsafe_allow_html=True)

    ss = st.session_state

    # Initialise component list once
    if "rz_avi_components" not in ss:
        ss.rz_avi_components = [dict(r) for r in _DEFAULT_COMPONENTS]

    df = pd.DataFrame(ss.rz_avi_components)

    edited = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Component": st.column_config.TextColumn("Component", width="large"),
            "Enabled":   st.column_config.CheckboxColumn("Enabled", default=False),
            "Mass_g":    st.column_config.NumberColumn("Mass [g]",  min_value=0.0,
                                                        max_value=5000.0, step=0.1,
                                                        format="%.1f"),
            "Power_W":   st.column_config.NumberColumn("Power [W]", min_value=0.0,
                                                        max_value=200.0,  step=0.05,
                                                        format="%.2f"),
        },
        key="_de_avi",
    )

    # Persist edits
    ss.rz_avi_components = edited.to_dict("records")

    # Compute totals from enabled rows only
    enabled_rows = [r for r in ss.rz_avi_components if r.get("Enabled", False)]
    M_avi_kg, P_avi_W = total_avionics(enabled_rows)
    ss.rz_M_avi_fixed = M_avi_kg
    ss.rz_P_avi_W     = P_avi_W

    st.markdown("---")

    c1, c2, c3 = st.columns(3, gap="small")
    c1.metric("Enabled components", str(len(enabled_rows)))
    c2.metric("M_avi  (fixed)",     f"{M_avi_kg*1000:.2f} g")
    c3.metric("P_avi  (fixed)",     f"{P_avi_W:.2f} W")

    # Compare vs sizing fraction
    if ss.get("sizing_done", False):
        m_avi_sz = ss.get("m_avi_sizing", 0.0)
        delta_g  = (M_avi_kg - m_avi_sz) * 1000.0
        sign     = "+" if delta_g >= 0 else ""
        color    = "#dc2626" if delta_g > 0 else "#16a34a"
        st.markdown(f"""
<div style="background:#ffffff;border:1px solid #e5e7eb;border-left:3px solid {color};
            border-radius:0 8px 8px 0;padding:10px 14px;margin-top:8px;font-size:0.83rem;">
  <b>Sizing phase M_avi</b> = {m_avi_sz*1000:.2f} g &nbsp;→&nbsp;
  <b>Resizing M_avi</b> = {M_avi_kg*1000:.2f} g
  &nbsp;(<span style="color:{color};font-weight:700;">{sign}{delta_g:.2f} g</span>)
</div>
""", unsafe_allow_html=True)

    # Per-component bar breakdown
    if enabled_rows:
        import plotly.graph_objects as go

        names  = [r["Component"] for r in enabled_rows]
        masses = [r["Mass_g"]    for r in enabled_rows]
        powers = [r["Power_W"]   for r in enabled_rows]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Mass [g]", x=names, y=masses,
            marker_color="#d97706",
            hovertemplate="%{x}: %{y:.1f} g<extra></extra>",
        ))
        fig.add_trace(go.Bar(
            name="Power [W]", x=names, y=powers,
            marker_color="#3b82f6",
            hovertemplate="%{x}: %{y:.2f} W<extra></extra>",
        ))
        fig.update_layout(
            barmode="group",
            paper_bgcolor="#ffffff", plot_bgcolor="#f9fafb",
            font=dict(color="#374151", size=11),
            xaxis=dict(gridcolor="#e5e7eb", tickangle=-30),
            yaxis=dict(title="Value", gridcolor="#e5e7eb", title_font_color="#6b7280"),
            legend=dict(bgcolor="#ffffff", bordercolor="#e5e7eb", borderwidth=1),
            height=300,
            margin=dict(l=10, r=10, t=10, b=60),
        )
        st.plotly_chart(fig, use_container_width=True)
