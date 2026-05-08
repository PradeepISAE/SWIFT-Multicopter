"""
Resizing Phase — Battery (R5).
Real battery database; per-segment energy display; SED extraction.
"""
import streamlit as st
import pandas as pd
from resizing.battery_resizing import (
    battery_from_energy, match_battery,
    battery_specific_energy, battery_total_voltage,
)
from resizing.mission_resizing import compute_mission_energy


_DEFAULT_BATTERIES = [
    {"Label": "GNB 300mAh 3S",    "Capacity_mAh": 300,  "Cells": 3, "V_cell_V": 3.7, "Mass_g": 24.0},
    {"Label": "Tattu 450mAh 3S",  "Capacity_mAh": 450,  "Cells": 3, "V_cell_V": 3.7, "Mass_g": 33.0},
    {"Label": "GNB 550mAh 4S",    "Capacity_mAh": 550,  "Cells": 4, "V_cell_V": 3.7, "Mass_g": 43.0},
    {"Label": "Tattu 650mAh 4S",  "Capacity_mAh": 650,  "Cells": 4, "V_cell_V": 3.7, "Mass_g": 55.0},
    {"Label": "Tattu 850mAh 3S",  "Capacity_mAh": 850,  "Cells": 3, "V_cell_V": 3.7, "Mass_g": 58.0},
    {"Label": "ANAFI 2700mAh 3S", "Capacity_mAh": 2700, "Cells": 3, "V_cell_V": 3.8, "Mass_g": 195.0},
    {"Label": "Custom",           "Capacity_mAh": 500,  "Cells": 3, "V_cell_V": 3.7, "Mass_g": 40.0},
]

_SEG_LABELS = {"takeoff": "Takeoff", "climb": "Climb", "cruise": "Cruise",
               "hover": "Hover", "land": "Land"}
_SEG_COLORS = {"takeoff": "#d97706", "climb": "#3b82f6", "cruise": "#10b981",
               "hover": "#6b7280", "land": "#8b5cf6"}


def render():
    st.markdown('<div class="section-tag">Resizing Phase · Battery</div>',
                unsafe_allow_html=True)
    st.markdown("## R5 · Battery Selection")

    ss = st.session_state

    if "resizing_batteries" not in ss:
        ss.resizing_batteries = [dict(r) for r in _DEFAULT_BATTERIES]
    if "resizing_selected_batt_idx" not in ss:
        ss.resizing_selected_batt_idx = -1

    # ── Capacity target from sizing ───────────────────────────────────────────
    if ss.get("sizing_done", False):
        c_tgt = ss.c_battery_target
        e_tgt = ss.e_battery_target
        st.markdown(f"""
<div style="background:#fffbeb;border:1px solid #fde68a;border-left:4px solid #d97706;
            border-radius:0 8px 8px 0;padding:12px 16px;margin-bottom:12px;">
  <span style="font-size:0.70rem;font-weight:700;color:#b45309;text-transform:uppercase;">
    Target from sizing phase</span><br>
  <b style="color:#d97706;font-size:1.05rem;">C_target = {c_tgt:.0f} mAh</b>
  &nbsp;·&nbsp;
  <b style="color:#d97706;font-size:1.05rem;">E_req = {e_tgt:.3f} Wh</b>
</div>
""", unsafe_allow_html=True)
    else:
        c_tgt = 0.0

    # ── Per-segment energy preview ────────────────────────────────────────────
    segs = ss.get("resizing_mission_segments")
    PL   = float(ss.get("resizing_PL_50pct_gW", 4.0))
    n    = int(ss.get("n_motors", 4))
    P_avi = float(ss.get("resizing_P_avi", 1.3))
    P_pay = float(ss.get("P_pay", 1.0))
    MTOW  = float(ss.get("resizing_MTOW_converged", ss.get("mtow_converged", 0.5)))
    E_cruise = float(ss.get("resizing_E_cruise_Wh", 0.0))

    if segs and PL > 0 and MTOW > 0:
        m_out = compute_mission_energy(MTOW, PL, n, P_avi, P_pay, segs, E_cruise)
        E_segs = m_out["E_segments"]
        E_total = m_out["E_total_Wh"]

        st.markdown("### Per-Segment Energy Preview")
        seg_rows_html = ""
        for seg_name in ["takeoff", "climb", "cruise", "hover", "land"]:
            E_k = E_segs.get(seg_name, 0.0)
            if E_k > 0:
                pct = E_k / E_total * 100.0 if E_total > 0 else 0.0
                color = _SEG_COLORS.get(seg_name, "#6b7280")
                bar_w = max(4, int(pct * 2))
                seg_rows_html += (
                    f'<tr>'
                    f'<td style="padding:5px 12px;color:{color};font-weight:600;font-size:0.83rem;">'
                    f'{_SEG_LABELS.get(seg_name, seg_name)}</td>'
                    f'<td style="padding:5px 12px;color:#374151;font-size:0.83rem;">{E_k:.3f} Wh</td>'
                    f'<td style="padding:5px 12px;color:#6b7280;font-size:0.83rem;">{pct:.1f}%</td>'
                    f'<td style="padding:5px 8px;">'
                    f'<div style="background:{color};height:8px;width:{bar_w}px;border-radius:4px;"></div>'
                    f'</td>'
                    f'</tr>'
                )

        st.markdown(f"""
<div style="background:#ffffff;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;margin-bottom:12px;">
<table style="width:100%;border-collapse:collapse;">
<tr style="background:#f9fafb;">
  <th style="color:#d97706;padding:7px 12px;text-align:left;font-size:0.70rem;text-transform:uppercase;
             border-bottom:1px solid #e5e7eb;">Segment</th>
  <th style="color:#d97706;padding:7px 12px;text-align:left;font-size:0.70rem;text-transform:uppercase;
             border-bottom:1px solid #e5e7eb;">Energy</th>
  <th style="color:#d97706;padding:7px 12px;text-align:left;font-size:0.70rem;text-transform:uppercase;
             border-bottom:1px solid #e5e7eb;">%</th>
  <th style="border-bottom:1px solid #e5e7eb;"></th>
</tr>
{seg_rows_html}
<tr style="background:#fffbeb;">
  <td style="padding:6px 12px;font-weight:700;color:#d97706;font-size:0.85rem;">Total</td>
  <td style="padding:6px 12px;font-weight:700;color:#d97706;font-size:0.85rem;">{E_total:.3f} Wh</td>
  <td colspan="2"></td>
</tr>
</table>
</div>
""", unsafe_allow_html=True)
        # Store preview energy for battery matching
        c_tgt_preview = E_total * 1000.0 / float(ss.get("resizing_V_batt", 11.1)) * 1.15
        if c_tgt == 0.0:
            c_tgt = c_tgt_preview

    # ── Battery database ──────────────────────────────────────────────────────
    st.markdown("### Battery Database")
    batt_df = pd.DataFrame(ss.resizing_batteries)
    batt_edited = st.data_editor(
        batt_df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Label":        st.column_config.TextColumn("Label", width="large"),
            "Capacity_mAh": st.column_config.NumberColumn("Cap. [mAh]", min_value=0, step=50),
            "Cells":        st.column_config.NumberColumn("Cells (S)", min_value=1, step=1),
            "V_cell_V":     st.column_config.NumberColumn("V_cell [V]", min_value=0.0, step=0.1, format="%.2f"),
            "Mass_g":       st.column_config.NumberColumn("Mass [g]", min_value=0.0, step=1.0, format="%.1f"),
        },
        key="_de_batts",
    )
    ss.resizing_batteries = batt_edited.to_dict("records")

    # ── Auto-match ────────────────────────────────────────────────────────────
    col_btn, col_status = st.columns([1, 3], gap="medium")
    with col_btn:
        if st.button("Auto-Match Battery", use_container_width=True,
                     help="Select lightest battery meeting capacity target."):
            idx = match_battery(ss.resizing_batteries, c_tgt)
            ss.resizing_selected_batt_idx = idx

    with col_status:
        idx = ss.resizing_selected_batt_idx
        if idx >= 0 and idx < len(ss.resizing_batteries):
            b = ss.resizing_batteries[idx]
            st.markdown(
                f'<span class="converged-badge">✓ Matched: {b["Label"]} — '
                f'{b["Capacity_mAh"]} mAh, {b["Mass_g"]:.1f} g</span>',
                unsafe_allow_html=True,
            )
        elif c_tgt > 0:
            st.markdown(
                '<span class="warn-badge">⚠ No match — add a larger battery</span>',
                unsafe_allow_html=True,
            )

    # Manual select
    batt_labels = [r.get("Label", f"Battery {i}") for i, r in enumerate(ss.resizing_batteries)]
    if batt_labels:
        default_i = max(0, ss.resizing_selected_batt_idx) if ss.resizing_selected_batt_idx >= 0 else 0
        sel_label = st.selectbox(
            "Active battery", batt_labels,
            index=min(default_i, len(batt_labels) - 1),
            key="_sel_batt",
        )
        ss.resizing_selected_batt_idx = batt_labels.index(sel_label)

    st.markdown("---")

    # ── Selected battery card ─────────────────────────────────────────────────
    idx = ss.resizing_selected_batt_idx
    if idx >= 0 and idx < len(ss.resizing_batteries):
        b       = ss.resizing_batteries[idx]
        cap     = float(b.get("Capacity_mAh", 0) or 0)
        cells   = int(b.get("Cells", 3) or 3)
        v_cell  = float(b.get("V_cell_V", 3.7) or 3.7)
        mass_g  = float(b.get("Mass_g", 0) or 0)
        V_pack  = cells * v_cell
        SED     = battery_specific_energy(cap, cells, v_cell, mass_g)
        meets   = (cap >= c_tgt) if c_tgt > 0 else True

        ss.resizing_battery_selected = dict(b)
        ss.resizing_SED    = SED if SED > 0 else float(ss.get("resizing_SED", 150.0))
        ss.resizing_V_batt = V_pack

        c1, c2, c3, c4 = st.columns(4, gap="small")
        c1.metric("Capacity",  f"{cap:.0f} mAh")
        c2.metric("Voltage",   f"{V_pack:.1f} V ({cells}S)")
        c3.metric("Mass",      f"{mass_g:.1f} g")
        c4.metric("SED",       f"{SED:.1f} Wh/kg")

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
  These values are passed to the resizing convergence loop.
</div>
""", unsafe_allow_html=True)
