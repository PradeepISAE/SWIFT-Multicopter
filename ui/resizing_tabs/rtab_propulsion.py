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
    if not motors:
        return -1
    vals = [float(m.get(key, 0) or 0) for m in motors]
    return int(max(range(len(vals)), key=lambda i: vals[i]))


def _eq_ref():
    with st.expander("Equations & References"):
        st.markdown("**Power loading**")
        st.latex(r"PL_{50\%} = \frac{T_{50\%}}{P_{50\%}} \quad [g/W]")
        st.latex(r"PL_{100\%} = \frac{T_{100\%}}{P_{100\%}} \quad [g/W]")

        st.markdown("**Propulsion group mass**")
        st.latex(
            r"M_{prop} = \frac{n \bigl(m_{motor} + m_{prop}\bigr)}{1000} \quad \text{[kg, AIO]}"
        )
        st.latex(
            r"M_{prop} = \frac{n \bigl(m_{motor} + m_{prop} + m_{ESC}\bigr)}{1000} \quad \text{[kg, Separate FC]}"
        )

        st.markdown("**Motor selection conditions**")
        st.latex(
            r"\text{(C1)}\quad T_{50\%,\,motor} \;\geq\; \frac{MTOW_g}{n} \quad \text{(hover at 50\% throttle)}"
        )
        st.latex(
            r"\text{(C2)}\quad \frac{T_{100\%} \cdot n}{MTOW_g} \;\geq\; TW_{req} \quad \text{(T/W ratio at 100\%)}"
        )
        st.latex(
            r"\text{(C3)}\quad \Delta T_g = T_{100\%} \cdot n \;-\; MTOW_g \cdot TW_{req} \;\geq\; 0 \quad \text{(thrust margin)}"
        )

        st.markdown("**Propeller diameter conversion**")
        st.latex(r"D_{prop,m} = D_{in} \times 0.0254 \quad [m]")

        st.caption(
            "References: Pollet (2024) PhD Thesis §3.3 — Propulsion sizing. "
            "PL definition: standard UAV design practice."
        )


def render():
    st.markdown('<div class="section-tag">Resizing Phase · Propulsion</div>',
                unsafe_allow_html=True)
    st.markdown("## R3 · Motor / Propeller / ESC Selection")

    _eq_ref()

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
PL = T/P is auto-calculated. Highest PL_50% row is highlighted.
Tick <b>Selected</b> on the motor you want to use.
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
            "Mass_g":         st.column_config.NumberColumn("Mass [g]",      min_value=0.0, step=0.5,  format="%.1f"),
            "T_50pct_g":      st.column_config.NumberColumn("T₅₀% [g]",      min_value=0.0, step=1.0,  format="%.0f"),
            "P_50pct_W":      st.column_config.NumberColumn("P₅₀% [W]",      min_value=0.0, step=0.5,  format="%.1f"),
            "T_100pct_g":     st.column_config.NumberColumn("T₁₀₀% [g]",     min_value=0.0, step=1.0,  format="%.0f"),
            "P_100pct_W":     st.column_config.NumberColumn("P₁₀₀% [W]",     min_value=0.0, step=0.5,  format="%.1f"),
            "PL_50pct_gW":    st.column_config.NumberColumn("PL₅₀% [g/W]",   disabled=True, format="%.2f"),
            "PL_100pct_gW":   st.column_config.NumberColumn("PL₁₀₀% [g/W]",  disabled=True, format="%.2f"),
            "Selected":       st.column_config.CheckboxColumn("Selected", default=False),
        },
        key="_de_motors",
    )
    motors_updated = fill_power_loadings(motor_edited.to_dict("records"))
    ss.resizing_motors = motors_updated

    if best_idx >= 0 and best_idx < len(motors_updated):
        m_best = motors_updated[best_idx]
        st.markdown(
            f'<span class="converged-badge">Best PL₅₀%: <b>{m_best["Motor"]}</b> — '
            f'{m_best["PL_50pct_gW"]:.2f} g/W</span>',
            unsafe_allow_html=True,
        )

    # ── Propellers ────────────────────────────────────────────────────────────
    st.markdown("### Propellers")
    st.caption("Diameter_m = Diameter_in × 0.0254 (auto-calculated).")

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
    ss.resizing_props = fill_prop_diameters(prop_edited.to_dict("records"))

    # ── ESCs (Separate only) ──────────────────────────────────────────────────
    if arch == "Separate FC+ESC":
        st.markdown("### ESCs")
        esc_df = pd.DataFrame(ss.resizing_escs)
        esc_edited = st.data_editor(
            esc_df,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "ESC":        st.column_config.TextColumn("ESC", width="large"),
                "Mass_g":     st.column_config.NumberColumn("Mass [g]",   min_value=0.0, step=0.5, format="%.1f"),
                "Current_A":  st.column_config.NumberColumn("I_max [A]",  min_value=0.0, step=1.0, format="%.0f"),
                "Selected":   st.column_config.CheckboxColumn("Selected", default=False),
            },
            key="_de_escs",
        )
        ss.resizing_escs = esc_edited.to_dict("records")

    # ── Resolve selected motor / prop / ESC ───────────────────────────────────
    sel_motors = [m for m in ss.resizing_motors if m.get("Selected", False)]
    sel_props  = [p for p in ss.resizing_props  if p.get("Selected", False)]
    sel_escs   = [e for e in ss.resizing_escs   if e.get("Selected", False)] if arch == "Separate FC+ESC" else []

    m_motor = sel_motors[0] if sel_motors else (ss.resizing_motors[0] if ss.resizing_motors else {})
    m_prop  = sel_props[0]  if sel_props  else (ss.resizing_props[0]  if ss.resizing_props  else {})
    m_esc   = sel_escs[0]   if sel_escs   else {}

    mass_motor  = float(m_motor.get("Mass_g",      0) or 0)
    mass_prop   = float(m_prop.get("Mass_g",       0) or 0)
    mass_esc    = float(m_esc.get("Mass_g",        0) or 0) if arch == "Separate FC+ESC" else 0.0
    T_50pct_g   = float(m_motor.get("T_50pct_g",   0) or 0)
    T_100pct_g  = float(m_motor.get("T_100pct_g",  0) or 0)
    PL_50pct    = float(m_motor.get("PL_50pct_gW", 0) or 0)
    D_prop_m    = float(m_prop.get("Diameter_m",   0) or 0)

    n          = int(ss.get("n_motors", 4))
    M_prop_kg  = propulsion_mass(n, mass_motor, mass_prop, mass_esc)

    ss.resizing_motor_selected = m_motor
    ss.resizing_prop_selected  = m_prop
    ss.resizing_M_prop         = M_prop_kg
    ss.resizing_PL_50pct_gW    = PL_50pct if PL_50pct > 0 else float(ss.get("resizing_PL_50pct_gW", 4.0))
    ss.resizing_T_100pct_g     = T_100pct_g
    if D_prop_m > 0:
        ss.resizing_D_prop_m = D_prop_m

    # ── Quick metrics ─────────────────────────────────────────────────────────
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4, gap="small")
    c1.metric("M_prop (fixed)",  f"{M_prop_kg*1000:.2f} g")
    c2.metric("PL₅₀% selected", f"{PL_50pct:.2f} g/W")
    c3.metric("T₁₀₀% / motor",  f"{T_100pct_g:.0f} g")
    c4.metric("D_prop",          f"{D_prop_m*1000:.0f} mm" if D_prop_m > 0 else "—")

    # ── Motor Selection Conditions ────────────────────────────────────────────
    st.markdown("### Motor Selection Conditions")

    MTOW_kg = ss.get("resizing_MTOW_converged", ss.get("mtow_converged", 0.0))
    has_mtow = MTOW_kg > 0 and T_50pct_g > 0 and T_100pct_g > 0

    if not has_mtow:
        st.info(
            "Run **R8 · Results** (or complete the Sizing Phase) to get a converged "
            "MTOW, then return here to verify the selected motor."
        )
    else:
        fc     = feasibility_check(T_50pct_g, T_100pct_g, n, MTOW_kg, TW_req=2.0)
        MTOW_g = MTOW_kg * 1000.0
        motor_name = m_motor.get("Motor", "Selected motor")
        sign3 = "+" if fc["delta_T_g"] >= 0 else ""

        # Colour helpers
        def _col(ok): return "#16a34a" if ok else "#dc2626"
        def _sym(ok): return "✓" if ok else "✗"
        def _bd(ok):  return "converged-badge" if ok else "warn-badge"

        st.markdown(f"""
<div style="background:#ffffff;border:1px solid #e5e7eb;border-top:3px solid #d97706;
            border-radius:10px;padding:16px 20px;margin-bottom:12px;">
  <div style="font-size:0.70rem;font-weight:700;color:#b45309;text-transform:uppercase;
              letter-spacing:0.10em;margin-bottom:10px;">
    Motor: {motor_name} &nbsp;·&nbsp; MTOW = {MTOW_g:.1f} g &nbsp;·&nbsp; n = {n}
  </div>
""", unsafe_allow_html=True)

        # Condition 1
        col1, col2 = st.columns([1, 1], gap="large")
        with col1:
            st.markdown("**C1 — Hover feasibility at 50% throttle**")
            st.latex(r"T_{50\%,\,motor} \;\geq\; \frac{MTOW_g}{n}")
            c1ok = fc["check1_ok"]
            st.markdown(f"""
<div style="background:#f9fafb;border:1px solid #e5e7eb;border-left:4px solid {_col(c1ok)};
            border-radius:0 8px 8px 0;padding:10px 14px;font-size:0.85rem;font-family:monospace;">
  {T_50pct_g:.1f} g &nbsp; {"≥" if c1ok else "&lt;"} &nbsp; {MTOW_g:.1f} / {n} = {fc["T_hover_per_motor_g"]:.1f} g
  <br><span style="font-size:1.0rem;font-weight:700;color:{_col(c1ok)};">
  {_sym(c1ok)} {"PASS" if c1ok else "FAIL"}</span>
  {"— motor can sustain hover at 50% throttle" if c1ok else "— motor cannot hover at 50% throttle"}
</div>
""", unsafe_allow_html=True)

        with col2:
            st.markdown("**C2 — T/W ratio at 100% throttle**")
            st.latex(r"\frac{T_{100\%} \cdot n}{MTOW_g} \;\geq\; TW_{req} = 2.0")
            c2ok = fc["check2_ok"]
            st.markdown(f"""
<div style="background:#f9fafb;border:1px solid #e5e7eb;border-left:4px solid {_col(c2ok)};
            border-radius:0 8px 8px 0;padding:10px 14px;font-size:0.85rem;font-family:monospace;">
  {T_100pct_g:.1f} × {n} / {MTOW_g:.1f} = {fc["TW_actual"]:.3f}
  &nbsp; {"≥" if c2ok else "&lt;"} &nbsp; 2.0
  <br><span style="font-size:1.0rem;font-weight:700;color:{_col(c2ok)};">
  {_sym(c2ok)} {"PASS" if c2ok else "FAIL"}</span>
  {"— sufficient T/W for aggressive manoeuvres" if c2ok else "— insufficient T/W"}
</div>
""", unsafe_allow_html=True)

        # Condition 3
        st.markdown("**C3 — Thrust margin**")
        st.latex(
            r"\Delta T = T_{100\%} \cdot n \;-\; MTOW_g \cdot TW_{req} \;\geq\; 0 \;[\mathrm{g}]"
        )
        c3ok = fc["check3_ok"]
        T_required_g = MTOW_g * 2.0
        st.markdown(f"""
<div style="background:#f9fafb;border:1px solid #e5e7eb;border-left:4px solid {_col(c3ok)};
            border-radius:0 8px 8px 0;padding:10px 14px;font-size:0.85rem;font-family:monospace;">
  ΔT = {T_100pct_g:.1f} × {n} − {MTOW_g:.1f} × 2.0
  = {fc["T_total_100pct_g"]:.1f} − {T_required_g:.1f}
  = <b style="color:{_col(c3ok)};">{sign3}{fc["delta_T_g"]:.1f} g
  ({sign3}{fc["delta_T_g"]/1000:.3f} kg)</b>
  <br><span style="font-size:1.0rem;font-weight:700;color:{_col(c3ok)};">
  {_sym(c3ok)} {"SURPLUS" if c3ok else "DEFICIT"}</span>
</div>
""", unsafe_allow_html=True)

        # Overall badge
        st.markdown("")
        all_ok = fc["all_ok"]
        badge_cls = "converged-badge" if all_ok else "warn-badge"
        st.markdown(
            f'<span class="{badge_cls}" style="font-size:0.90rem;">'
            f'{"✓ All conditions met — motor is suitable" if all_ok else "✗ One or more conditions failed — consider a higher-thrust motor"}'
            f'</span>',
            unsafe_allow_html=True,
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Summary card ──────────────────────────────────────────────────────────
    st.markdown("---")
    esc_line = f"<b>ESC:</b> {m_esc.get('ESC','—')} ({mass_esc:.1f} g)<br>" if arch == "Separate FC+ESC" else ""
    st.markdown(f"""
<div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:10px;
            padding:14px 18px;font-size:0.84rem;">
  <b>Motor:</b> {m_motor.get("Motor","—")} ({mass_motor:.1f} g) &nbsp;·&nbsp;
  PL₅₀% = {PL_50pct:.2f} g/W<br>
  <b>Propeller:</b> {m_prop.get("Propeller","—")} ({mass_prop:.1f} g,
  {D_prop_m*1000:.0f} mm)<br>
  {esc_line}
  <b>Per set:</b> {mass_motor+mass_prop+mass_esc:.1f} g &nbsp;×&nbsp; {n}
  = <b style="color:#d97706;">{M_prop_kg*1000:.2f} g total</b>
</div>
""", unsafe_allow_html=True)
