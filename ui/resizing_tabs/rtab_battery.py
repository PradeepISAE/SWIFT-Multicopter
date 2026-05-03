"""
Resizing Phase — Battery tab.
Database of real batteries; match against capacity target; extract SED.
"""
import streamlit as st
import pandas as pd
from resizing.battery_resizing import match_battery, battery_specific_energy

_DEFAULT_BATTERIES = [
    {"Label": "GNB 300mAh 3S",   "Capacity_mAh": 300,  "Cells": 3, "V_cell_V": 3.7, "Mass_g": 24.0},
    {"Label": "Tattu 450mAh 3S", "Capacity_mAh": 450,  "Cells": 3, "V_cell_V": 3.7, "Mass_g": 33.0},
    {"Label": "GNB 450mAh 3S",   "Capacity_mAh": 450,  "Cells": 3, "V_cell_V": 3.7, "Mass_g": 31.0},
    {"Label": "Tattu 550mAh 3S", "Capacity_mAh": 550,  "Cells": 3, "V_cell_V": 3.7, "Mass_g": 39.0},
    {"Label": "Tattu 650mAh 3S", "Capacity_mAh": 650,  "Cells": 3, "V_cell_V": 3.7, "Mass_g": 47.0},
    {"Label": "Tattu 850mAh 3S", "Capacity_mAh": 850,  "Cells": 3, "V_cell_V": 3.7, "Mass_g": 58.0},
    {"Label": "GNB 550mAh 4S",   "Capacity_mAh": 550,  "Cells": 4, "V_cell_V": 3.7, "Mass_g": 43.0},
    {"Label": "Tattu 650mAh 4S", "Capacity_mAh": 650,  "Cells": 4, "V_cell_V": 3.7, "Mass_g": 55.0},
    {"Label": "Custom",          "Capacity_mAh": 500,  "Cells": 3, "V_cell_V": 3.7, "Mass_g": 40.0},
]


def _init(ss):
    if "rz_batteries" not in ss:
        ss.rz_batteries      = [dict(r) for r in _DEFAULT_BATTERIES]
    if "rz_selected_batt" not in ss:
        ss.rz_selected_batt  = -1
    if "rz_SED" not in ss:
        ss.rz_SED            = float(ss.get("SED", 150.0))
    if "rz_V_batt" not in ss:
        ss.rz_V_batt         = float(ss.get("V_batt", 11.1))


def render():
    st.markdown('<div class="section-tag">Resizing Phase · Battery</div>',
                unsafe_allow_html=True)
    st.markdown("## R4 · Battery Selection")

    ss = st.session_state
    _init(ss)

    # ── Capacity target banner ────────────────────────────────────────────────
    if ss.get("sizing_done", False):
        c_tgt = ss.c_battery_target
        e_tgt = ss.e_battery_target
        st.markdown(f"""
<div style="background:#fffbeb;border:1px solid #fde68a;border-left:4px solid #d97706;
            border-radius:0 8px 8px 0;padding:12px 16px;margin-bottom:16px;">
  <span style="font-size:0.70rem;font-weight:700;color:#b45309;text-transform:uppercase;
               letter-spacing:0.10em;">Target from sizing phase</span><br>
  <b style="color:#d97706;font-size:1.05rem;">C_target = {c_tgt:.0f} mAh</b>
  &nbsp;·&nbsp;
  <b style="color:#d97706;font-size:1.05rem;">E_req = {e_tgt:.3f} Wh</b>
  <span style="color:#6b7280;font-size:0.80rem;margin-left:8px;">
    (raw capacity × 1.15 buffer)
  </span>
</div>
""", unsafe_allow_html=True)
    else:
        c_tgt = 0.0
        st.info("Run the Sizing Phase first to get a capacity target.")

    # ── Battery database ──────────────────────────────────────────────────────
    st.markdown("### Battery Database")
    batt_df = pd.DataFrame(ss.rz_batteries)
    batt_edited = st.data_editor(
        batt_df, use_container_width=True, num_rows="dynamic",
        column_config={
            "Label":        st.column_config.TextColumn("Label",          width="large"),
            "Capacity_mAh": st.column_config.NumberColumn("Cap. [mAh]",  min_value=0, step=50),
            "Cells":        st.column_config.NumberColumn("Cells (S)",    min_value=1, step=1),
            "V_cell_V":     st.column_config.NumberColumn("V_cell [V]",  min_value=0.0, step=0.1,
                                                           format="%.2f"),
            "Mass_g":       st.column_config.NumberColumn("Mass [g]",    min_value=0.0, step=1.0,
                                                           format="%.1f"),
        },
        key="_de_batts",
    )
    ss.rz_batteries = batt_edited.to_dict("records")

    # ── Auto-match button ─────────────────────────────────────────────────────
    col_btn, col_status = st.columns([1, 3], gap="medium")
    with col_btn:
        if st.button("Auto-Match Battery", help="Select lightest battery meeting C_target.",
                     use_container_width=True):
            idx = match_battery(ss.rz_batteries, c_tgt)
            ss.rz_selected_batt = idx

    with col_status:
        if ss.rz_selected_batt >= 0:
            b = ss.rz_batteries[ss.rz_selected_batt]
            st.markdown(
                f'<span class="converged-badge">✓ Matched: {b["Label"]} — '
                f'{b["Capacity_mAh"]} mAh, {b["Mass_g"]:.1f} g</span>',
                unsafe_allow_html=True,
            )
        elif ss.rz_selected_batt == -1 and c_tgt > 0:
            st.markdown(
                '<span class="warn-badge">⚠ No match — add a larger battery or reduce C_target</span>',
                unsafe_allow_html=True,
            )

    # ── Manual selection ──────────────────────────────────────────────────────
    st.markdown("**Or select manually:**")
    batt_labels = [r.get("Label", f"Battery {i}") for i, r in enumerate(ss.rz_batteries)]
    if batt_labels:
        default_idx = max(0, ss.rz_selected_batt) if ss.rz_selected_batt >= 0 else 0
        sel_label   = st.selectbox("Active battery", batt_labels,
                                   index=min(default_idx, len(batt_labels) - 1),
                                   key="_sel_batt")
        ss.rz_selected_batt = batt_labels.index(sel_label)

    st.markdown("---")

    # ── Selected battery card ─────────────────────────────────────────────────
    if ss.rz_selected_batt >= 0 and ss.rz_selected_batt < len(ss.rz_batteries):
        b        = ss.rz_batteries[ss.rz_selected_batt]
        cap      = float(b.get("Capacity_mAh", 0) or 0)
        cells    = int(b.get("Cells",    3) or 3)
        v_cell   = float(b.get("V_cell_V", 3.7) or 3.7)
        mass_g   = float(b.get("Mass_g", 0) or 0)
        V_pack   = cells * v_cell
        SED      = battery_specific_energy(cap, cells, v_cell, mass_g)
        meets    = cap >= c_tgt if c_tgt > 0 else True

        ss.rz_SED    = SED if SED > 0 else ss.rz_SED
        ss.rz_V_batt = V_pack

        c1, c2, c3, c4 = st.columns(4, gap="small")
        c1.metric("Capacity",  f"{cap:.0f} mAh")
        c2.metric("Voltage",   f"{V_pack:.1f} V ({cells}S)")
        c3.metric("Mass",      f"{mass_g:.1f} g")
        c4.metric("SED",       f"{SED:.1f} Wh/kg")

        color = "#16a34a" if meets else "#dc2626"
        badge = "converged-badge" if meets else "warn-badge"
        sym   = "✓" if meets else "✗"
        st.markdown(
            f'<span class="{badge}">{sym} {cap:.0f} mAh '
            f'{"≥" if meets else "<"} target {c_tgt:.0f} mAh</span>',
            unsafe_allow_html=True,
        )

        st.markdown(f"""
<div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:10px;
            padding:14px 18px;margin-top:8px;font-size:0.84rem;">
  <b>SED</b> = {SED:.1f} Wh/kg &nbsp;·&nbsp;
  <b>V_batt</b> = {V_pack:.2f} V &nbsp;·&nbsp;
  These values are passed to the Resizing convergence loop.
</div>
""", unsafe_allow_html=True)

    elif not ss.rz_batteries:
        st.warning("Battery database is empty — add at least one battery.")
