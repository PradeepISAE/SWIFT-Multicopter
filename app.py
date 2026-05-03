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
        # Mission
        "uav_name":      "SWIFT UAV",
        "n_motors":      4,
        "t_flight_min":  20.0,
        "P_avi":         1.0,
        # Payload
        "m_pay":         0.030,
        "MF_pay":        0.20,
        "P_pay":         1.0,
        # Structures
        "MF_str":        0.20,
        # Avionics (fraction)
        "MF_avi":        0.15,
        # Propulsion — datasheet inputs
        "motor_label":   "Generic 1806 2300KV",
        "M_motor_g":     7.2,
        "M_prop_g":      1.0,
        "P_max_W":       60.0,
        "V_batt":        11.1,
        # Battery
        "SED":           150.0,
        "DoD":           0.85,
        "eta_elec":      0.85,
        "PL_mode":       "Single Value",
        "PL":            8.0,
        # Sizing results
        "results":       None,
        "sweep_results": None,
        # Sizing → Resizing bridge
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
        # Resizing phase — structure
        "rz_cs_type":       "Circular tube",
        "rz_material":      "CF tube",
        "rz_rho_custom":    1600.0,
        "rz_sigma_custom":  600.0,
        "rz_d_outer_mm":    10.0,
        "rz_t_wall_mm":     1.0,
        "rz_b_outer_mm":    10.0,
        "rz_b_plate_mm":    12.0,
        "rz_h_plate_mm":    2.0,
        "rz_k_arm":         2.5,
        "rz_D_prop_mm":     127.0,
        "rz_FoS_req":       1.5,
        "rz_c_margin_mm":   10.0,
        "rz_M_body_g":      15.0,
        # Resizing phase — computed structure outputs
        "rz_L_arm_m":       0.10,
        "rz_D_prop_m":      0.127,
        "rz_M_struct_fixed":0.05,
        "rz_stress_ok":     None,
        "rz_clearance_ok":  None,
        "rz_FoS_actual":    0.0,
        "rz_sigma_MPa":     0.0,
        "rz_d_between_m":   0.0,
        "rz_T_max_N":       0.0,
        "rz_m_one_arm_g":   0.0,
        # Resizing phase — avionics
        "rz_M_avi_fixed":   0.03,
        "rz_P_avi_W":       1.3,
        # Resizing phase — propulsion
        "rz_M_prop_fixed":  0.02,
        "rz_T_max_N":       0.0,
        "rz_PL":            8.0,
        # Resizing phase — battery
        "rz_SED":           150.0,
        "rz_V_batt":        11.1,
        # Resizing phase — mission
        "rz_t_flight_min":  20.0,
        "rz_DoD":           0.85,
        "rz_eta_elec":      0.85,
        "rz_config":        "Quad X",
        # Resizing phase — results
        "rz_results":       None,
        "rz_opt_result":    None,
        "rz_opt_history":   None,
        # Phase navigation
        "phase":            "Sizing Phase",
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
    ">v 2.0</div>
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
            rtab_structure,
            rtab_avionics,
            rtab_propulsion,
            rtab_battery,
            rtab_mission,
            rtab_results,
            rtab_optimisation,
        )

        tabs = st.tabs([
            "R0 · Overview",
            "R1 · Structure",
            "R2 · Avionics",
            "R3 · Propulsion",
            "R4 · Battery",
            "R5 · Mission",
            "R6 · Results",
            "R7 · Optimisation",
        ])

        with tabs[0]: rtab_overview.render()
        with tabs[1]: rtab_structure.render()
        with tabs[2]: rtab_avionics.render()
        with tabs[3]: rtab_propulsion.render()
        with tabs[4]: rtab_battery.render()
        with tabs[5]: rtab_mission.render()
        with tabs[6]: rtab_results.render()
        with tabs[7]: rtab_optimisation.render()


if __name__ == "__main__":
    main()
