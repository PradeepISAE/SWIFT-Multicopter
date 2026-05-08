"""
Resizing Phase — Avionics (R2).
Architecture selector: AIO Stack vs Separate FC+ESC.
Component-level mass and power replace the MF_avi sizing fraction.
"""
import streamlit as st
import pandas as pd
from resizing.avionics_resizing import (
    total_avionics, AIO_STACK_DEFAULTS, SEPARATE_FC_DEFAULTS,
)


def render():
    st.markdown('<div class="section-tag">Resizing Phase · Avionics</div>',
                unsafe_allow_html=True)
    st.markdown("## R2 · Avionics Components")

    st.markdown("""
<div class="info-box">
Select FC architecture, then enable each component on your UAV.
Totals feed into the resizing loop as <b>M_avi_fixed</b> and <b>P_avi</b>.
</div>
""", unsafe_allow_html=True)

    ss = st.session_state

    # ── Architecture selector ─────────────────────────────────────────────────
    arch = st.radio(
        "FC + ESC Architecture",
        ["AIO Stack", "Separate FC+ESC"],
        index=0 if ss.get("resizing_avi_architecture", "AIO Stack") == "AIO Stack" else 1,
        horizontal=True,
        key="_rz_avi_arch",
        help="AIO: ESC integrated in FC stack (e.g. Matek H743-SLIM). "
             "Separate: dedicated FC + individual ESCs.",
    )
    ss.resizing_avi_architecture = arch

    defaults = AIO_STACK_DEFAULTS if arch == "AIO Stack" else SEPARATE_FC_DEFAULTS

    # Initialise component list when architecture changes or first load
    arch_key = f"resizing_avi_components_{arch}"
    if arch_key not in ss:
        ss[arch_key] = [dict(r) for r in defaults]

    # Mirror to canonical key used by convergence loop
    ss.resizing_avi_components = ss[arch_key]

    st.caption(
        "AIO Stack: ESC mass counted here. "
        "Separate FC+ESC: ESC mass in R3 · Propulsion."
        if arch == "AIO Stack" else
        "Separate FC+ESC: ESC mass counted in R3 · Propulsion table."
    )

    # ── Component table ───────────────────────────────────────────────────────
    df = pd.DataFrame(ss.resizing_avi_components)

    edited = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Component": st.column_config.TextColumn("Component", width="large"),
            "Enabled":   st.column_config.CheckboxColumn("Enabled", default=False),
            "Mass_g":    st.column_config.NumberColumn(
                "Mass [g]", min_value=0.0, max_value=5000.0, step=0.1, format="%.1f"),
            "Power_W":   st.column_config.NumberColumn(
                "Power [W]", min_value=0.0, max_value=200.0, step=0.05, format="%.2f"),
            "Notes":     st.column_config.TextColumn("Notes", width="medium"),
        },
        key=f"_de_avi_{arch}",
    )

    ss[arch_key] = edited.to_dict("records")
    ss.resizing_avi_components = ss[arch_key]

    # ── Totals from enabled rows ──────────────────────────────────────────────
    enabled_rows = [r for r in ss.resizing_avi_components if r.get("Enabled", False)]
    M_avi_kg, P_avi_W = total_avionics(enabled_rows)
    ss.resizing_M_avi = M_avi_kg
    ss.resizing_P_avi = P_avi_W

    st.markdown("---")

    c1, c2, c3 = st.columns(3, gap="small")
    c1.metric("Enabled components", str(len(enabled_rows)))
    c2.metric("M_avi (fixed)",      f"{M_avi_kg*1000:.2f} g")
    c3.metric("P_avi (fixed)",      f"{P_avi_W:.2f} W")

    # Compare vs sizing fraction
    if ss.get("sizing_done", False):
        m_avi_sz = ss.get("m_avi_sizing", 0.0)
        delta_g  = (M_avi_kg - m_avi_sz) * 1000.0
        sign     = "+" if delta_g >= 0 else ""
        color    = "#dc2626" if delta_g > 0 else "#16a34a"
        st.markdown(f"""
<div style="background:#ffffff;border:1px solid #e5e7eb;border-left:3px solid {color};
            border-radius:0 8px 8px 0;padding:10px 14px;margin-top:8px;font-size:0.83rem;">
  Sizing M_avi = {m_avi_sz*1000:.2f} g &nbsp;→&nbsp;
  Resizing M_avi = {M_avi_kg*1000:.2f} g
  &nbsp;(<span style="color:{color};font-weight:700;">{sign}{delta_g:.2f} g</span>)
</div>
""", unsafe_allow_html=True)

    # Bar chart
    if enabled_rows:
        import plotly.graph_objects as go
        names  = [r["Component"] for r in enabled_rows]
        masses = [float(r.get("Mass_g", 0)) for r in enabled_rows]
        powers = [float(r.get("Power_W", 0)) for r in enabled_rows]

        fig = go.Figure()
        fig.add_trace(go.Bar(name="Mass [g]", x=names, y=masses,
                             marker_color="#d97706",
                             hovertemplate="%{x}: %{y:.1f} g<extra></extra>"))
        fig.add_trace(go.Bar(name="Power [W]", x=names, y=powers,
                             marker_color="#3b82f6",
                             hovertemplate="%{x}: %{y:.2f} W<extra></extra>"))
        fig.update_layout(
            barmode="group",
            paper_bgcolor="#ffffff", plot_bgcolor="#f9fafb",
            font=dict(color="#374151", size=11),
            xaxis=dict(gridcolor="#e5e7eb", tickangle=-30),
            yaxis=dict(title="Value", gridcolor="#e5e7eb", title_font_color="#6b7280"),
            legend=dict(bgcolor="#ffffff", bordercolor="#e5e7eb", borderwidth=1),
            height=280, margin=dict(l=10, r=10, t=10, b=60),
        )
        st.plotly_chart(fig, use_container_width=True)
