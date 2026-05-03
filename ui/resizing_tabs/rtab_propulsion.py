"""
Resizing Phase — Propulsion tab.
Motor / prop / ESC database tables, active selection, feasibility check.
"""
import streamlit as st
import pandas as pd
from resizing.propulsion_resizing import propulsion_mass, power_loading, feasibility_check

_DEFAULT_MOTORS = [
    {"Label": "Generic 1806 2300KV",    "Mass_g": 7.2,  "T_max_g": 250.0, "P_max_W": 60.0,  "KV": 2300},
    {"Label": "T-Motor F1507 3800KV",   "Mass_g": 13.5, "T_max_g": 350.0, "P_max_W": 100.0, "KV": 3800},
    {"Label": "Emax RS2205S 2600KV",    "Mass_g": 28.0, "T_max_g": 800.0, "P_max_W": 250.0, "KV": 2600},
    {"Label": "T-Motor MN1806 2300KV",  "Mass_g": 16.0, "T_max_g": 320.0, "P_max_W": 80.0,  "KV": 2300},
    {"Label": "Custom motor",           "Mass_g": 10.0, "T_max_g": 300.0, "P_max_W": 80.0,  "KV": 2000},
]

_DEFAULT_PROPS = [
    {"Label": "5×4.5×3 tri-blade",  "Diameter_in": 5.0,  "Pitch_in": 4.5, "Blades": 3, "Mass_g": 1.0},
    {"Label": "6×4.5×3 tri-blade",  "Diameter_in": 6.0,  "Pitch_in": 4.5, "Blades": 3, "Mass_g": 3.0},
    {"Label": "7×4×2 bi-blade",     "Diameter_in": 7.0,  "Pitch_in": 4.0, "Blades": 2, "Mass_g": 6.0},
    {"Label": "3×2.5×3 micro",      "Diameter_in": 3.0,  "Pitch_in": 2.5, "Blades": 3, "Mass_g": 0.5},
    {"Label": "Custom prop",        "Diameter_in": 5.0,  "Pitch_in": 4.0, "Blades": 2, "Mass_g": 2.0},
]

_DEFAULT_ESCS = [
    {"Label": "Generic 20A BLHeli_S",  "Mass_g": 6.0,  "I_max_A": 20.0, "V_max_V": 25.2},
    {"Label": "BLHeli32 30A",          "Mass_g": 9.0,  "I_max_A": 30.0, "V_max_V": 33.6},
    {"Label": "T-Motor F30A",          "Mass_g": 12.0, "I_max_A": 30.0, "V_max_V": 33.6},
    {"Label": "AM32 40A",              "Mass_g": 14.0, "I_max_A": 40.0, "V_max_V": 50.4},
    {"Label": "Custom ESC",            "Mass_g": 8.0,  "I_max_A": 25.0, "V_max_V": 25.2},
]


def _init(ss):
    if "rz_motors" not in ss:
        ss.rz_motors       = [dict(r) for r in _DEFAULT_MOTORS]
    if "rz_props" not in ss:
        ss.rz_props        = [dict(r) for r in _DEFAULT_PROPS]
    if "rz_escs" not in ss:
        ss.rz_escs         = [dict(r) for r in _DEFAULT_ESCS]
    if "rz_active_motor" not in ss:
        ss.rz_active_motor = 0
    if "rz_active_prop" not in ss:
        ss.rz_active_prop  = 0
    if "rz_active_esc" not in ss:
        ss.rz_active_esc   = 0
    if "rz_PL" not in ss:
        ss.rz_PL = float(ss.get("pl_sizing", 8.0))


def render():
    st.markdown('<div class="section-tag">Resizing Phase · Propulsion</div>',
                unsafe_allow_html=True)
    st.markdown("## R3 · Motor / Propeller / ESC Selection")

    ss = st.session_state
    _init(ss)

    # ── Motors ────────────────────────────────────────────────────────────────
    st.markdown("### Motors")
    motor_df = pd.DataFrame(ss.rz_motors)
    motor_edited = st.data_editor(
        motor_df, use_container_width=True, num_rows="dynamic",
        column_config={
            "Label":    st.column_config.TextColumn("Label",       width="large"),
            "Mass_g":   st.column_config.NumberColumn("Mass [g]",  min_value=0.0, step=0.1, format="%.1f"),
            "T_max_g":  st.column_config.NumberColumn("T_max [g]", min_value=0.0, step=1.0, format="%.0f"),
            "P_max_W":  st.column_config.NumberColumn("P_max [W]", min_value=0.0, step=1.0, format="%.0f"),
            "KV":       st.column_config.NumberColumn("KV",        min_value=0,   step=100),
        },
        key="_de_motors",
    )
    ss.rz_motors = motor_edited.to_dict("records")

    motor_labels = [r.get("Label", f"Motor {i}") for i, r in enumerate(ss.rz_motors)]
    if motor_labels:
        active_motor_label = st.selectbox(
            "Active motor", motor_labels,
            index=min(ss.rz_active_motor, len(motor_labels) - 1),
            key="_sel_motor",
        )
        ss.rz_active_motor = motor_labels.index(active_motor_label)

    # ── Props ─────────────────────────────────────────────────────────────────
    st.markdown("### Propellers")
    prop_df = pd.DataFrame(ss.rz_props)
    prop_edited = st.data_editor(
        prop_df, use_container_width=True, num_rows="dynamic",
        column_config={
            "Label":       st.column_config.TextColumn("Label",         width="large"),
            "Diameter_in": st.column_config.NumberColumn("Diam [in]",  min_value=0.0, step=0.5, format="%.1f"),
            "Pitch_in":    st.column_config.NumberColumn("Pitch [in]", min_value=0.0, step=0.5, format="%.1f"),
            "Blades":      st.column_config.NumberColumn("Blades",     min_value=2,   step=1),
            "Mass_g":      st.column_config.NumberColumn("Mass [g]",   min_value=0.0, step=0.1, format="%.1f"),
        },
        key="_de_props",
    )
    ss.rz_props = prop_edited.to_dict("records")

    prop_labels = [r.get("Label", f"Prop {i}") for i, r in enumerate(ss.rz_props)]
    if prop_labels:
        active_prop_label = st.selectbox(
            "Active propeller", prop_labels,
            index=min(ss.rz_active_prop, len(prop_labels) - 1),
            key="_sel_prop",
        )
        ss.rz_active_prop = prop_labels.index(active_prop_label)

    # ── ESCs ──────────────────────────────────────────────────────────────────
    st.markdown("### ESCs")
    esc_df = pd.DataFrame(ss.rz_escs)
    esc_edited = st.data_editor(
        esc_df, use_container_width=True, num_rows="dynamic",
        column_config={
            "Label":   st.column_config.TextColumn("Label",         width="large"),
            "Mass_g":  st.column_config.NumberColumn("Mass [g]",   min_value=0.0, step=0.1, format="%.1f"),
            "I_max_A": st.column_config.NumberColumn("I_max [A]",  min_value=0.0, step=1.0, format="%.0f"),
            "V_max_V": st.column_config.NumberColumn("V_max [V]",  min_value=0.0, step=0.1, format="%.1f"),
        },
        key="_de_escs",
    )
    ss.rz_escs = esc_edited.to_dict("records")

    esc_labels = [r.get("Label", f"ESC {i}") for i, r in enumerate(ss.rz_escs)]
    if esc_labels:
        active_esc_label = st.selectbox(
            "Active ESC", esc_labels,
            index=min(ss.rz_active_esc, len(esc_labels) - 1),
            key="_sel_esc",
        )
        ss.rz_active_esc = esc_labels.index(active_esc_label)

    # ── Power loading ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Power Loading for Resizing Loop")

    col_pl, col_hint = st.columns([1, 1], gap="large")
    with col_pl:
        ss.rz_PL = st.number_input(
            "Power loading PL [g/W]",
            min_value=1.0, max_value=20.0,
            value=float(ss.rz_PL), step=0.5, format="%.1f",
            help="From motor datasheet: PL ≈ T_max / P_max. "
                 "Actual hover PL is lower due to partial throttle.",
            key="_num_rz_PL",
        )

    with col_hint:
        # Auto-fill hint from selected motor
        if ss.rz_motors and len(ss.rz_motors) > ss.rz_active_motor:
            m = ss.rz_motors[ss.rz_active_motor]
            t_max = float(m.get("T_max_g", 0) or 0)
            p_max = float(m.get("P_max_W",  1) or 1)
            pl_est = t_max / p_max if p_max > 0 else 0.0
            st.markdown(f"""
<div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:8px;padding:12px 14px;margin-top:28px;">
  <div style="font-size:0.70rem;font-weight:700;color:#d97706;text-transform:uppercase;
              letter-spacing:0.10em;margin-bottom:4px;">Motor estimate</div>
  <div style="font-size:0.85rem;color:#374151;">
    PL ≈ T_max / P_max = {t_max:.0f} / {p_max:.0f}
    = <b style="color:#d97706;">{pl_est:.2f} g/W</b>
  </div>
  <div style="font-size:0.75rem;color:#6b7280;margin-top:4px;">
    Hover PL is typically 60–80 % of this peak value.
  </div>
</div>
""", unsafe_allow_html=True)

    # ── Compute totals & feasibility ─────────────────────────────────────────
    st.markdown("---")

    n  = int(ss.n_motors)
    mi = ss.rz_active_motor
    pi = ss.rz_active_prop
    ei = ss.rz_active_esc

    m_motor_g = float((ss.rz_motors[mi]["Mass_g"]  if ss.rz_motors and mi < len(ss.rz_motors) else 0) or 0)
    m_prop_g  = float((ss.rz_props[pi]["Mass_g"]   if ss.rz_props  and pi < len(ss.rz_props)  else 0) or 0)
    m_esc_g   = float((ss.rz_escs[ei]["Mass_g"]    if ss.rz_escs   and ei < len(ss.rz_escs)   else 0) or 0)
    t_max_g   = float((ss.rz_motors[mi]["T_max_g"] if ss.rz_motors and mi < len(ss.rz_motors) else 0) or 0)

    M_prop_kg = propulsion_mass(n, m_motor_g, m_prop_g, m_esc_g)
    ss.rz_M_prop_fixed = M_prop_kg
    ss.rz_T_max_N      = t_max_g * 9.81 / 1000.0

    c1, c2, c3 = st.columns(3, gap="small")
    c1.metric("M_prop (fixed)", f"{M_prop_kg*1000:.2f} g")
    c2.metric("T_max / motor",  f"{t_max_g:.0f} g")
    c3.metric("PL (design)",    f"{ss.rz_PL:.2f} g/W")

    # Feasibility check
    if ss.get("sizing_done", False):
        mtow_kg      = ss.mtow_converged
        T_50pct_g    = ss.get("t_motor_50pct_target", ss.t_motor_target / 2.0)
        T_hover_req  = ss.t_motor_target

        feasible = feasibility_check(T_50pct_g, n, mtow_kg)
        motor_ok = t_max_g >= T_hover_req

        col_f1, col_f2 = st.columns(2, gap="small")
        with col_f1:
            badge = "converged-badge" if motor_ok else "warn-badge"
            sym   = "✓" if motor_ok else "✗"
            st.markdown(
                f'<span class="{badge}">{sym} Motor T_max = {t_max_g:.0f} g '
                f'(need ≥ {T_hover_req:.0f} g)</span>',
                unsafe_allow_html=True,
            )
        with col_f2:
            badge2 = "converged-badge" if feasible else "warn-badge"
            sym2   = "✓" if feasible else "✗"
            st.markdown(
                f'<span class="{badge2}">{sym2} T_50pct × n_motors '
                f'= {T_50pct_g*n:.0f} g vs MTOW×g = {mtow_kg*1000:.0f} g×g</span>',
                unsafe_allow_html=True,
            )

    # Per-motor mass breakdown
    st.markdown(f"""
<div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:10px;
            padding:14px 18px;margin-top:10px;font-size:0.84rem;">
  <b>Per motor set:</b> {m_motor_g:.1f} g (motor) + {m_prop_g:.1f} g (prop)
  + {m_esc_g:.1f} g (ESC) = <b style="color:#d97706;">
  {m_motor_g+m_prop_g+m_esc_g:.1f} g</b>
  &nbsp;×&nbsp; {n} = <b style="color:#d97706;">{M_prop_kg*1000:.2f} g total</b>
</div>
""", unsafe_allow_html=True)
