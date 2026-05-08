"""
Resizing Phase — Propulsion (R3).
Motor / prop / ESC database with T_50pct, T_100pct, PL_50pct, PL_100pct.
"""
import streamlit as st
import pandas as pd
from resizing.propulsion_resizing import (
    MOTOR_DEFAULTS, PROP_DEFAULTS, ESC_DEFAULTS,
    propulsion_mass, feasibility_check,
    fill_power_loadings, fill_prop_diameters,
)


def _best_pl_idx(motors: list, key: str = "PL_50pct_gW") -> int:
    """Index of motor with highest PL value."""
    if not motors:
        return -1
    vals = [float(m.get(key, 0) or 0) for m in motors]
    return int(max(range(len(vals)), key=lambda i: vals[i]))


def render():
    st.markdown('<div class="section-tag">Resizing Phase · Propulsion</div>',
                unsafe_allow_html=True)
    st.markdown("## R3 · Motor / Propeller / ESC Selection")

    ss = st.session_state
    arch = ss.get("resizing_avi_architecture", "AIO Stack")

    # ── Initialise tables ─────────────────────────────────────────────────────
    if "resizing_motors" not in ss:
        ss.resizing_motors = fill_power_loadings([dict(r) for r in MOTOR_DEFAULTS])
    if "resizing_props" not in ss:
        ss.resizing_props  = fill_prop_diameters([dict(r) for r in PROP_DEFAULTS])
    if "resizing_escs" not in ss:
        ss.resizing_escs   = [dict(r) for r in ESC_DEFAULTS]

    # ── Motors ────────────────────────────────────────────────────────────────
    st.markdown("### Motors")
    st.markdown("""
<div class="info-box" style="margin-bottom:8px;">
PL_50pct and PL_100pct are auto-calculated from T/P values.
The row with the highest PL_50pct is highlighted. Check the <b>Selected</b> box
for the motor you want to use.
</div>
""", unsafe_allow_html=True)

    motor_df = pd.DataFrame(ss.resizing_motors)
    best_idx = _best_pl_idx(ss.resizing_motors, "PL_50pct_gW")

    motor_edited = st.data_editor(
        motor_df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Motor":          st.column_config.TextColumn("Motor", width="large"),
            "Mass_g":         st.column_config.NumberColumn("Mass [g]", min_value=0.0, step=0.5, format="%.1f"),
            "T_50pct_g":      st.column_config.NumberColumn("T_50% [g]", min_value=0.0, step=1.0, format="%.0f"),
            "P_50pct_W":      st.column_config.NumberColumn("P_50% [W]", min_value=0.0, step=0.5, format="%.1f"),
            "T_100pct_g":     st.column_config.NumberColumn("T_100% [g]", min_value=0.0, step=1.0, format="%.0f"),
            "P_100pct_W":     st.column_config.NumberColumn("P_100% [W]", min_value=0.0, step=0.5, format="%.1f"),
            "PL_50pct_gW":    st.column_config.NumberColumn("PL_50% [g/W]", disabled=True, format="%.2f"),
            "PL_100pct_gW":   st.column_config.NumberColumn("PL_100% [g/W]", disabled=True, format="%.2f"),
            "Selected":       st.column_config.CheckboxColumn("Selected", default=False),
        },
        key="_de_motors",
    )

    # Recompute PL after edit, then persist
    motors_updated = fill_power_loadings(motor_edited.to_dict("records"))
    ss.resizing_motors = motors_updated

    # Show best-PL hint
    if best_idx >= 0 and best_idx < len(motors_updated):
        m_best = motors_updated[best_idx]
        st.markdown(
            f'<span class="converged-badge">Best PL_50%: <b>{m_best["Motor"]}</b> — '
            f'{m_best["PL_50pct_gW"]:.2f} g/W</span>',
            unsafe_allow_html=True,
        )

    # ── Propellers ────────────────────────────────────────────────────────────
    st.markdown("### Propellers")
    st.caption("Diameter_m is auto-computed from Diameter_in × 0.0254.")

    prop_df = pd.DataFrame(ss.resizing_props)
    prop_edited = st.data_editor(
        prop_df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Propeller":   st.column_config.TextColumn("Propeller", width="large"),
            "Diameter_in": st.column_config.NumberColumn("Diam [in]", min_value=0.0, step=0.5, format="%.1f"),
            "Diameter_m":  st.column_config.NumberColumn("Diam [m]",  disabled=True, format="%.4f"),
            "Mass_g":      st.column_config.NumberColumn("Mass [g]",  min_value=0.0, step=0.1, format="%.1f"),
            "Selected":    st.column_config.CheckboxColumn("Selected", default=False),
        },
        key="_de_props",
    )
    props_updated = fill_prop_diameters(prop_edited.to_dict("records"))
    ss.resizing_props = props_updated

    # ── ESCs (only if Separate FC architecture) ───────────────────────────────
    if arch == "Separate FC+ESC":
        st.markdown("### ESCs")
        esc_df = pd.DataFrame(ss.resizing_escs)
        esc_edited = st.data_editor(
            esc_df,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "ESC":        st.column_config.TextColumn("ESC", width="large"),
                "Mass_g":     st.column_config.NumberColumn("Mass [g]", min_value=0.0, step=0.5, format="%.1f"),
                "Current_A":  st.column_config.NumberColumn("I_max [A]", min_value=0.0, step=1.0, format="%.0f"),
                "Selected":   st.column_config.CheckboxColumn("Selected", default=False),
            },
            key="_de_escs",
        )
        ss.resizing_escs = esc_edited.to_dict("records")

    # ── Derived quantities ────────────────────────────────────────────────────
    st.markdown("---")

    # Find selected motor, prop, ESC
    sel_motors = [m for m in ss.resizing_motors if m.get("Selected", False)]
    sel_props  = [p for p in ss.resizing_props  if p.get("Selected", False)]
    sel_escs   = [e for e in ss.resizing_escs   if e.get("Selected", False)] if arch == "Separate FC+ESC" else []

    m_motor = sel_motors[0] if sel_motors else ss.resizing_motors[0] if ss.resizing_motors else {}
    m_prop  = sel_props[0]  if sel_props  else ss.resizing_props[0]  if ss.resizing_props  else {}
    m_esc   = sel_escs[0]   if sel_escs   else {}

    mass_motor = float(m_motor.get("Mass_g", 0) or 0)
    mass_prop  = float(m_prop.get("Mass_g",  0) or 0)
    mass_esc   = float(m_esc.get("Mass_g",   0) or 0) if arch == "Separate FC+ESC" else 0.0

    n = int(ss.get("n_motors", 4))
    M_prop_kg = propulsion_mass(n, mass_motor, mass_prop, mass_esc)

    PL_50pct = float(m_motor.get("PL_50pct_gW",  0) or 0)
    T_100pct_g = float(m_motor.get("T_100pct_g", 0) or 0)
    D_prop_m   = float(m_prop.get("Diameter_m",  0) or 0)

    ss.resizing_motor_selected = m_motor
    ss.resizing_prop_selected  = m_prop
    ss.resizing_M_prop         = M_prop_kg
    ss.resizing_PL_50pct_gW    = PL_50pct if PL_50pct > 0 else float(ss.get("resizing_PL_50pct_gW", 4.0))
    ss.resizing_T_100pct_g     = T_100pct_g
    if D_prop_m > 0:
        ss.resizing_D_prop_m   = D_prop_m

    c1, c2, c3, c4 = st.columns(4, gap="small")
    c1.metric("M_prop (fixed)",  f"{M_prop_kg*1000:.2f} g")
    c2.metric("PL_50% selected", f"{PL_50pct:.2f} g/W")
    c3.metric("T_100% / motor",  f"{T_100pct_g:.0f} g")
    c4.metric("D_prop",          f"{D_prop_m*1000:.0f} mm" if D_prop_m > 0 else "—")

    # Feasibility checks
    if ss.get("sizing_done", False) or ss.get("resizing_done", False):
        MTOW_kg   = ss.get("resizing_MTOW_converged", ss.get("mtow_converged", 0.5))
        T_50pct_g = float(m_motor.get("T_50pct_g",  0) or 0)
        if MTOW_kg > 0 and T_50pct_g > 0:
            fc = feasibility_check(T_50pct_g, T_100pct_g, n, MTOW_kg, TW_req=2.0)
            MTOW_g = MTOW_kg * 1000.0

            b1 = "converged-badge" if fc["check1_ok"] else "warn-badge"
            b2 = "converged-badge" if fc["check2_ok"] else "warn-badge"
            b3 = "converged-badge" if fc["check3_ok"] else "warn-badge"
            s1, s2, s3 = ("✓" if fc[k] else "✗" for k in ("check1_ok","check2_ok","check3_ok"))
            sign = "+" if fc["delta_T_g"] >= 0 else ""

            st.markdown(f"""
<div style="display:flex;flex-direction:column;gap:6px;margin-top:4px;">
  <span class="{b1}">{s1} Check 1 — Hover at 50% throttle:
    T_50% = {T_50pct_g:.0f} g ≥ T_hover/motor = {MTOW_g:.0f}/{n} = {fc["T_hover_per_motor_g"]:.1f} g</span>
  <span class="{b2}">{s2} Check 2 — T/W at 100% (all motors):
    TW = {fc["T_total_100pct_g"]:.0f} g / {MTOW_g:.0f} g = {fc["TW_actual"]:.2f} (need ≥ 2.0)</span>
  <span class="{b3}">{s3} Check 3 — Thrust margin:
    {T_100pct_g:.0f} × {n} − {MTOW_g:.0f} × 2.0 = {sign}{fc["delta_T_g"]:.1f} g
    ({sign}{fc["delta_T_g"]/1000:.3f} kg)</span>
</div>
""", unsafe_allow_html=True)

    # Summary card
    st.markdown(f"""
<div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:10px;
            padding:14px 18px;margin-top:10px;font-size:0.84rem;">
  <b>Motor:</b> {m_motor.get("Motor","—")} ({mass_motor:.1f} g)<br>
  <b>Propeller:</b> {m_prop.get("Propeller","—")} ({mass_prop:.1f} g, {D_prop_m*1000:.0f} mm)<br>
  {"<b>ESC:</b> " + m_esc.get("ESC","—") + f" ({mass_esc:.1f} g)<br>" if arch == "Separate FC+ESC" else ""}
  <b>Per set:</b> {mass_motor+mass_prop+mass_esc:.1f} g &nbsp;×&nbsp; {n} =
  <b style="color:#d97706;">{M_prop_kg*1000:.2f} g total</b>
</div>
""", unsafe_allow_html=True)
