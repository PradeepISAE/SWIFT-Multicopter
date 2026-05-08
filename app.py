"""
SWIFT — Systems Engineering Workflow for Integrated Feasible mulTicopter design

Entry point: streamlit run app.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

st.set_page_config(
    page_title="SWIFT | Multicopter Sizing",
    page_icon="🚁",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ── Custom CSS — Claude.ai inspired light theme ──────────────────────────────

def _inject_css():
    st.markdown("""
<style>
/* ===================================================================
   SWIFT LIGHT THEME — Claude.ai inspired
   Background   #f7f7f8   Accent    #d97706 (warm amber)
   Card         #ffffff   Border    #e5e7eb
   Text         #1a1a1a   Muted     #6b7280
   =================================================================== */

/* --- Base ---------------------------------------------------------- */
.stApp, [data-testid="stAppViewContainer"] {
    background-color: #f7f7f8 !important;
    color: #1a1a1a !important;
}
[data-testid="stHeader"], [data-testid="stToolbar"] {
    background-color: #f7f7f8 !important;
    border-bottom: 1px solid #e5e7eb !important;
}
[data-testid="collapsedControl"] { display: none !important; }
section[data-testid="stSidebar"] {
    background-color: #efefef !important;
}

/* --- Typography ---------------------------------------------------- */
body, p, span, div, label, li { color: #1a1a1a !important; }
h1 { color: #1a1a1a !important; font-size: 1.55rem !important; font-weight: 700 !important; }
h2 { color: #1a1a1a !important; font-size: 1.25rem !important; font-weight: 700 !important; margin-bottom: 4px !important; }
h3 { color: #1a1a1a !important; font-size: 1.02rem !important; font-weight: 600 !important; margin-bottom: 4px !important; }
a { color: #d97706 !important; }

/* --- Main content padding ------------------------------------------ */
.main .block-container {
    padding-top: 0 !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 1400px !important;
}

/* --- Tabs ---------------------------------------------------------- */
.stTabs [data-baseweb="tab-list"] {
    background-color: #ffffff !important;
    border-bottom: 2px solid #e5e7eb !important;
    padding: 0 4px !important;
    gap: 2px !important;
}
.stTabs [data-baseweb="tab"] {
    background-color: transparent !important;
    color: #6b7280 !important;
    border-radius: 6px 6px 0 0 !important;
    border: none !important;
    padding: 10px 18px !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.04em !important;
    transition: all 0.15s ease !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: #d97706 !important;
    background-color: #fef3c7 !important;
}
.stTabs [aria-selected="true"] {
    background-color: #ffffff !important;
    color: #d97706 !important;
}
[data-baseweb="tab-highlight"] {
    background-color: #d97706 !important;
    height: 2px !important;
}
[data-baseweb="tab-border"] { display: none !important; }
.stTabs [data-baseweb="tab-panel"] {
    background-color: #f7f7f8 !important;
    padding: 20px 2px !important;
}

/* --- Inputs -------------------------------------------------------- */
[data-testid="stNumberInputContainer"],
[data-baseweb="base-input"],
.stTextInput > div > div {
    background-color: #ffffff !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 8px !important;
}
[data-testid="stNumberInputContainer"]:focus-within,
.stTextInput > div > div:focus-within {
    border-color: #d97706 !important;
    box-shadow: 0 0 0 3px rgba(217,119,6,0.10) !important;
}
input[type="number"], input[type="text"] {
    background-color: #ffffff !important;
    color: #1a1a1a !important;
    caret-color: #d97706 !important;
}
[data-testid="stNumberInputContainer"] button {
    background-color: #f9fafb !important;
    color: #6b7280 !important;
    border: none !important;
}
[data-testid="stNumberInputContainer"] button:hover {
    background-color: #fef3c7 !important;
    color: #d97706 !important;
}

/* --- Select / Dropdown --------------------------------------------- */
[data-baseweb="select"] > div {
    background-color: #ffffff !important;
    border-color: #e5e7eb !important;
    border-radius: 8px !important;
    color: #1a1a1a !important;
}
[data-baseweb="select"] > div:focus-within {
    border-color: #d97706 !important;
    box-shadow: 0 0 0 3px rgba(217,119,6,0.10) !important;
}
[data-baseweb="popover"] {
    background-color: #ffffff !important;
    border: 1px solid #e5e7eb !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.10) !important;
    border-radius: 8px !important;
}
[data-baseweb="menu"] { background-color: #ffffff !important; }
[role="option"] {
    background-color: #ffffff !important;
    color: #1a1a1a !important;
}
[role="option"]:hover {
    background-color: #fef3c7 !important;
    color: #d97706 !important;
}
[role="option"][aria-selected="true"] {
    background-color: #fef3c7 !important;
    color: #d97706 !important;
}

/* --- Slider -------------------------------------------------------- */
[data-testid="stSlider"] > div > div > div > div {
    background-color: #d97706 !important;
}
[data-testid="stSlider"] [data-testid="stTickBar"] {
    color: #6b7280 !important;
}

/* --- Radio --------------------------------------------------------- */
[data-testid="stRadio"] label { color: #1a1a1a !important; font-size: 0.88rem !important; }

/* --- Checkbox ------------------------------------------------------ */
[data-testid="stCheckbox"] label { color: #1a1a1a !important; }

/* --- Buttons ------------------------------------------------------- */
.stButton > button {
    background-color: #d97706 !important;
    border: none !important;
    color: #ffffff !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    padding: 10px 28px !important;
    transition: all 0.18s ease !important;
    box-shadow: 0 2px 6px rgba(217,119,6,0.20) !important;
}
.stButton > button:hover {
    background-color: #b45309 !important;
    box-shadow: 0 4px 14px rgba(217,119,6,0.35) !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active { transform: translateY(0) !important; }

/* --- Download button ----------------------------------------------- */
[data-testid="stDownloadButton"] > button {
    background-color: #ffffff !important;
    border: 1px solid #d97706 !important;
    color: #d97706 !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
}
[data-testid="stDownloadButton"] > button:hover {
    background-color: #fef3c7 !important;
}

/* --- Metrics ------------------------------------------------------- */
[data-testid="metric-container"] {
    background-color: #ffffff !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 10px !important;
    padding: 14px 18px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06) !important;
}
[data-testid="stMetricValue"] {
    color: #d97706 !important;
    font-size: 1.4rem !important;
    font-weight: 700 !important;
}
[data-testid="stMetricLabel"] {
    color: #6b7280 !important;
    font-size: 0.72rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}
[data-testid="stMetricDelta"] { color: #16a34a !important; }

/* --- Info / Warning / Error boxes ---------------------------------- */
[data-testid="stAlert"] {
    border-radius: 8px !important;
}

/* --- DataFrame / Table --------------------------------------------- */
[data-testid="stDataFrame"] {
    background-color: #ffffff !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}

/* --- Caption ------------------------------------------------------- */
.stCaption, [data-testid="stCaptionContainer"] {
    color: #6b7280 !important;
    font-size: 0.80rem !important;
}

/* --- HR ------------------------------------------------------------ */
hr { border-color: #e5e7eb !important; margin: 20px 0 !important; }

/* --- Spinner ------------------------------------------------------- */
[data-testid="stSpinner"] > div { border-top-color: #d97706 !important; }

/* --- Scrollbar ----------------------------------------------------- */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #f7f7f8; }
::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #d97706; }

/* --- Custom component classes -------------------------------------- */
.section-tag {
    display: inline-block;
    background: #fef3c7;
    border: 1px solid #fde68a;
    color: #b45309 !important;
    font-size: 0.65rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    padding: 2px 10px;
    border-radius: 4px;
    margin-bottom: 8px;
}

.swift-card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 16px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}

.info-box {
    background: #f0f9ff;
    border: 1px solid #bae6fd;
    border-left: 4px solid #0ea5e9;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin: 10px 0 16px 0;
    font-size: 0.84rem;
    color: #0c4a6e !important;
    line-height: 1.6;
}

.eq-box {
    background: #fffbeb;
    border: 1px solid #fde68a;
    border-left: 4px solid #d97706;
    border-radius: 0 8px 8px 0;
    padding: 14px 18px;
    margin: 10px 0 16px 0;
    font-size: 0.84rem;
    color: #78350f !important;
    line-height: 1.7;
}

.converged-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #f0fdf4;
    border: 1px solid #86efac;
    color: #16a34a !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    padding: 6px 16px;
    border-radius: 20px;
}

.warn-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: #fef2f2;
    border: 1px solid #fca5a5;
    color: #dc2626 !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    padding: 6px 16px;
    border-radius: 20px;
}
</style>
""", unsafe_allow_html=True)


# ── Session-state initialisation ────────────────────────────────────────────

def _init_session_state():
    defaults = {
        # ── Sizing Phase inputs ──────────────────────────────────────────────
        "uav_name":      "SWIFT UAV",
        "n_motors":      4,
        "t_flight_min":  20.0,
        "P_avi":         1.0,
        "m_pay":         0.030,
        "MF_pay":        0.20,
        "P_pay":         1.0,
        "MF_str":        0.20,
        "MF_avi":        0.15,
        "motor_label":   "Generic 1806 2300KV",
        "M_motor_g":     7.2,
        "M_prop_g":      1.0,
        "P_max_W":       60.0,
        "V_batt":        11.1,
        "SED":           150.0,
        "DoD":           0.85,
        "eta_elec":      0.85,
        "PL_mode":       "Single Value",
        "PL":            8.0,
        # ── Sizing Phase results ─────────────────────────────────────────────
        "results":       None,
        "sweep_results": None,
        # ── Sizing → Resizing bridge ─────────────────────────────────────────
        "sizing_done":           False,
        "mtow_converged":        0.0,
        "m_struct_sizing":       0.0,
        "m_avi_sizing":          0.0,
        "m_prop_sizing":         0.0,
        "m_batt_sizing":         0.0,
        "pl_sizing":             8.0,
        "p_motor_target":        0.0,
        "t_motor_target":        0.0,
        "t_motor_50pct_target":  0.0,
        "c_battery_target":      0.0,
        "e_battery_target":      0.0,
        "p_total_target":        0.0,
        # ── Resizing Phase — mission ─────────────────────────────────────────
        "resizing_mission_segments": {
            "takeoff": {"active": True,  "duration_min": 0.5,  "a_TO_ms2": 19.62},
            "climb":   {"active": False, "duration_min": 2.0},
            "cruise":  {"active": False, "duration_min": 0.0},
            "hover":   {"active": True,  "duration_min": 20.0},
            "land":    {"active": True,  "duration_min": 0.5,  "k_land": 0.5},
        },
        "resizing_cruise_active": False,
        "resizing_a_TO_ms2":   19.62,
        "resizing_k_land":     0.5,
        "resizing_V_climb":    3.0,
        "resizing_V_cruise":   10.0,
        "resizing_config":     "Quad X",
        "resizing_DoD":        0.85,
        "resizing_eta_elec":   0.85,
        # ── Resizing Phase — avionics ────────────────────────────────────────
        "resizing_avi_architecture": "AIO Stack",
        "resizing_M_avi":  0.030,
        "resizing_P_avi":  1.3,
        # ── Resizing Phase — propulsion ──────────────────────────────────────
        "resizing_M_prop":        0.020,
        "resizing_PL_50pct_gW":   4.0,
        "resizing_T_100pct_g":    0.0,
        "resizing_D_prop_m":      0.127,
        # ── Resizing Phase — structure ───────────────────────────────────────
        "resizing_cross_section": "Circular Hollow Tube",
        "resizing_material":      "CF tube/rod",
        "resizing_rho_custom":    1600.0,
        "resizing_sigma_custom":  600.0,
        "resizing_k_arm":         1.2,
        "resizing_k_ratio":       0.7,
        "resizing_b_plate_m":     0.012,
        "resizing_FoS":           1.5,
        "resizing_c_margin_m":    0.010,
        "resizing_M_struct_sizing": 0.050,
        "resizing_body_diameter": 0.08,
        "resizing_M_body":        0.030,
        # ── Resizing Phase — computed structure ──────────────────────────────
        "resizing_L_arm":         0.076,
        "resizing_d_out":         0.003,
        "resizing_M_arms":        0.0,
        "resizing_M_body_calc":   0.0,
        "resizing_M_struct":      0.0,
        "resizing_FoS_actual":    0.0,
        "resizing_sigma_root_MPa":0.0,
        "resizing_stress_ok":     None,
        "resizing_clearance_ok":  None,
        "resizing_d_between_m":   0.0,
        "resizing_struct_dims":   {},
        # ── Resizing Phase — battery ─────────────────────────────────────────
        "resizing_SED":           150.0,
        "resizing_V_batt":        11.1,
        "resizing_selected_batt_idx": -1,
        "resizing_E_cruise_Wh":   0.0,
        # ── Resizing Phase — layout ──────────────────────────────────────────
        "resizing_S_top":   0.05,
        "resizing_S_front": 0.02,
        # ── Resizing Phase — aerodynamics ────────────────────────────────────
        "resizing_C_D":     0.35,
        "resizing_C_L":     0.0,
        "resizing_rho_air": 1.225,
        # ── Resizing Phase — results ─────────────────────────────────────────
        "resizing_results":         None,
        "resizing_done":            False,
        "resizing_MTOW_converged":  0.0,
        # ── Resizing Phase — optimisation ────────────────────────────────────
        "resizing_opt_k_arm":   0.0,
        "resizing_opt_k_ratio": 0.0,
        "resizing_opt_MTOW":    0.0,
        "resizing_opt_history": None,
        # ── Phase navigation ─────────────────────────────────────────────────
        "phase": "Sizing Phase",
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val


# ── App header ──────────────────────────────────────────────────────────────

def _render_header():
    st.markdown("""
<div style="
    background: #ffffff;
    border-bottom: 1px solid #e5e7eb;
    padding: 16px 28px;
    margin: -20px -32px 24px -32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
">
    <div style="display:flex;align-items:center;gap:20px;">
        <div style="
            font-size: 2.0rem;
            font-weight: 900;
            color: #d97706;
            letter-spacing: 0.10em;
            line-height: 1;
        ">⬡ SWIFT</div>
        <div>
            <div style="font-size:0.82rem;color:#1a1a1a;font-weight:600;line-height:1.4;">
                Systems Engineering Workflow for Integrated Feasible mulTicopter design
            </div>
            <div style="font-size:0.70rem;color:#6b7280;margin-top:2px;">
                Sizing Phase &nbsp;·&nbsp; Fixed-Point Mass Convergence &nbsp;·&nbsp;
                Resizing Phase &nbsp;·&nbsp; Real Hardware &amp; SLSQP Optimisation
            </div>
        </div>
    </div>
    <div style="
        font-size:0.65rem;color:#6b7280;letter-spacing:0.06em;
        border:1px solid #e5e7eb;padding:4px 12px;border-radius:6px;
        background:#f9fafb;
    ">v 3.0</div>
</div>
""", unsafe_allow_html=True)


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    _inject_css()
    _init_session_state()
    _render_header()

    # ── Phase navigation ──────────────────────────────────────────────────────
    phase = st.radio(
        "Phase",
        ["Sizing Phase", "Resizing Phase"],
        index=0 if st.session_state.phase == "Sizing Phase" else 1,
        horizontal=True,
        key="_radio_phase",
    )
    st.session_state.phase = phase

    st.markdown("<div style='height:4px;background:#e5e7eb;margin:0 0 16px 0;'></div>",
                unsafe_allow_html=True)

    if phase == "Sizing Phase":
        from ui.tabs import (
            tab_mission,
            tab_payload,
            tab_structures,
            tab_avionics,
            tab_propulsion,
            tab_battery,
            tab_results,
        )

        tabs = st.tabs([
            "01 · Mission",
            "02 · Payload",
            "03 · Structures",
            "04 · Avionics",
            "05 · Propulsion",
            "06 · Battery",
            "07 · Results",
        ])

        with tabs[0]: tab_mission.render()
        with tabs[1]: tab_payload.render()
        with tabs[2]: tab_structures.render()
        with tabs[3]: tab_avionics.render()
        with tabs[4]: tab_propulsion.render()
        with tabs[5]: tab_battery.render()
        with tabs[6]: tab_results.render()

    else:
        from ui.resizing_tabs import (
            rtab_overview,
            rtab_mission,
            rtab_avionics,
            rtab_propulsion,
            rtab_structure,
            rtab_battery,
            rtab_layout_2d,
            rtab_aerodynamics,
            rtab_results,
            rtab_optimisation,
        )

        cruise_active = st.session_state.get("resizing_cruise_active", False)

        # Build tab list — aerodynamics tab is conditional on cruise being active
        tab_labels = [
            "R0 · Overview",
            "R1 · Mission",
            "R2 · Avionics",
            "R3 · Propulsion",
            "R4 · Structure",
            "R5 · Battery",
            "R6 · Layout 2D",
        ]
        tab_modules = [
            rtab_overview,
            rtab_mission,
            rtab_avionics,
            rtab_propulsion,
            rtab_structure,
            rtab_battery,
            rtab_layout_2d,
        ]

        if cruise_active:
            tab_labels.append("R7 · Aerodynamics")
            tab_modules.append(rtab_aerodynamics)
            tab_labels.append("R8 · Results")
            tab_modules.append(rtab_results)
            tab_labels.append("R9 · Optimisation")
            tab_modules.append(rtab_optimisation)
        else:
            tab_labels.append("R7 · Results")
            tab_modules.append(rtab_results)
            tab_labels.append("R8 · Optimisation")
            tab_modules.append(rtab_optimisation)

        tabs = st.tabs(tab_labels)
        for tab, module in zip(tabs, tab_modules):
            with tab:
                module.render()


if __name__ == "__main__":
    main()
