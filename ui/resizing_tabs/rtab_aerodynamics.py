"""
Resizing Phase — Aerodynamics (R7).
CONDITIONAL — only shown when cruise segment is active (resizing_cruise_active = True).
Computes drag, lift, induced velocity, cruise motor power and energy.
Reference: Tyan (2017) Eq. 17.
"""
import streamlit as st
from resizing.aerodynamics_resizing import compute_cruise


def render():
    st.markdown('<div class="section-tag">Resizing Phase · Aerodynamics</div>',
                unsafe_allow_html=True)
    st.markdown("## R7 · Cruise Aerodynamics")

    ss = st.session_state

    if not ss.get("resizing_cruise_active", False):
        st.markdown("""
<div style="background:#ffffff;border:1px dashed #e5e7eb;border-radius:12px;
            padding:56px;text-align:center;margin-top:24px;">
  <div style="font-size:2.4rem;color:#d97706;margin-bottom:12px;">✈</div>
  <div style="color:#1a1a1a;font-size:1.0rem;font-weight:600;">Cruise segment not active</div>
  <div style="color:#6b7280;font-size:0.83rem;margin-top:6px;">
    Enable <b>Cruise</b> in <b>R1 · Mission</b> to unlock this tab.
  </div>
</div>
""", unsafe_allow_html=True)
        return

    st.markdown("""
<div class="eq-box">
<b>Cruise drag model (Tyan 2017)</b><br>
D_f = ½ C_D ρ V² S_front &nbsp;·&nbsp; L_f = ½ C_L ρ V² S_top<br>
F_cruise/motor = √((W + L_f)² + D_f²) / n_motors<br>
v_i = √(F / (2 ρ A_disk)) &nbsp;·&nbsp;
FM = 0.4742 × T^0.0793 &nbsp;(Figure of Merit)<br>
P_cruise = n × F_motor × v_i / FM + P_avi + P_pay
</div>
""", unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown("**Aerodynamic coefficients**")

        ss.resizing_C_D = st.number_input(
            "Drag coefficient C_D", 0.01, 2.0,
            float(ss.get("resizing_C_D", 0.35)),
            step=0.01, format="%.3f",
            help="Whole-vehicle drag coefficient. Typical multirotor: 0.3–0.5.",
            key="_aero_cd",
        )
        ss.resizing_C_L = st.number_input(
            "Lift coefficient C_L", 0.0, 2.0,
            float(ss.get("resizing_C_L", 0.0)),
            step=0.01, format="%.3f",
            help="Non-zero only for winged or tilted-body configurations.",
            key="_aero_cl",
        )

        st.markdown("**Flight conditions**")
        ss.resizing_rho_air = st.number_input(
            "Air density ρ [kg/m³]", 0.5, 1.5,
            float(ss.get("resizing_rho_air", 1.225)),
            step=0.005, format="%.3f", key="_aero_rho",
        )
        ss.resizing_V_cruise = st.number_input(
            "Cruise speed V [m/s]", 1.0, 50.0,
            float(ss.get("resizing_V_cruise", 10.0)),
            step=0.5, format="%.1f", key="_aero_v",
        )

        segs = ss.get("resizing_mission_segments", {})
        t_cruise_h = segs.get("cruise", {}).get("duration_min", 5.0) / 60.0

        st.markdown(f"Cruise duration from mission: **{t_cruise_h*60:.1f} min**")

    with col_right:
        st.markdown("**Reference areas** (from R6 · Layout 2D)")
        S_top   = float(ss.get("resizing_S_top",   0.05))
        S_front = float(ss.get("resizing_S_front", 0.02))
        D_prop_m = float(ss.get("resizing_D_prop_m", 0.127))
        n_motors = int(ss.get("n_motors", 4))
        P_avi    = float(ss.get("resizing_P_avi", 1.3))
        P_pay    = float(ss.get("P_pay", 1.0))
        MTOW     = float(ss.get("resizing_MTOW_converged",
                          ss.get("mtow_converged", 0.5)))
        if MTOW <= 0:
            MTOW = 0.5

        c1, c2 = st.columns(2)
        c1.metric("S_top",   f"{S_top*1e4:.2f} cm²",
                  help="Set in R6 · Layout 2D")
        c2.metric("S_front", f"{S_front*1e4:.2f} cm²",
                  help="Set in R6 · Layout 2D")

        if S_top <= 0 or S_front <= 0:
            st.warning("Set reference areas in R6 · Layout 2D first.")

    # ── Compute cruise ────────────────────────────────────────────────────────
    if S_front > 0 and S_top > 0 and t_cruise_h > 0:
        try:
            cr = compute_cruise(
                MTOW, ss.resizing_V_cruise, ss.resizing_C_D, ss.resizing_C_L,
                ss.resizing_rho_air, S_top, S_front,
                D_prop_m, n_motors, P_avi, P_pay, t_cruise_h,
            )

            ss.resizing_E_cruise_Wh = cr["E_cruise_Wh"]

            st.markdown("---")
            st.markdown("### Cruise Results")

            c1, c2, c3 = st.columns(3, gap="small")
            c1.metric("D_f (drag)",   f"{cr['D_f_N']:.3f} N")
            c2.metric("L_f (lift)",   f"{cr['L_f_N']:.3f} N")
            c3.metric("FM (Tyan)",    f"{cr['FM']:.4f}")

            c4, c5, c6 = st.columns(3, gap="small")
            c4.metric("F / motor",    f"{cr['F_cruise_motor_N']:.3f} N")
            c5.metric("v_i (induced)",f"{cr['v_i_ms']:.3f} m/s")
            c6.metric("P_cruise",     f"{cr['P_cruise_total_W']:.2f} W")

            c7, c8 = st.columns(2, gap="small")
            c7.metric("E_cruise",     f"{cr['E_cruise_Wh']:.3f} Wh")
            c8.metric("Cruise time",  f"{t_cruise_h*60:.1f} min")

            st.markdown(f"""
<div style="background:#f0fdf4;border:1px solid #86efac;border-radius:10px;
            padding:14px 18px;margin-top:8px;font-size:0.84rem;">
  <b>E_cruise = {cr['E_cruise_Wh']:.3f} Wh</b> will be added to the mission energy
  in R8 · Results when the convergence loop runs.
</div>
""", unsafe_allow_html=True)

        except Exception as exc:
            st.error(f"Aerodynamics computation failed: {exc}")

    else:
        st.info("Complete R6 · Layout 2D (reference areas) and R1 · Mission (cruise duration) first.")
