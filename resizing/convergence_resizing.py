"""
Fixed-point mass convergence for the SWIFT Resizing Phase.

Unlike the Sizing Phase, M_struct, M_avi, and M_prop are ALL FIXED
from real hardware selections.  Only M_batt floats with MTOW.

Governing equations:
  MTOW_0 = m_pay / MF_pay

  Each iteration k:
    T_motor(k) = MTOW(k) / n_motors          [kg]
    P_motor(k) = T_motor(k) × 1000 / PL      [W]
    P_total(k) = n × P_motor + P_avi + P_pay  [W]
    E_req(k)   = P_total × t_flight           [Wh]
    M_batt(k)  = E_req / (SED × DoD × η)     [kg]
    MTOW(k+1)  = m_pay + M_struct + M_avi + M_prop + M_batt(k)

Converges when |MTOW(k+1) − MTOW(k)| < 1e-4 kg, max 50 iterations.
"""


def run_resizing(params: dict) -> dict:
    """Execute fixed-point resizing loop.

    Required keys in params:
        m_pay, MF_pay,
        M_struct_fixed, M_avi_fixed, M_prop_fixed  [kg — real hardware]
        n_motors, PL [g/W], P_avi [W], P_pay [W],
        t_flight [h], SED [Wh/kg], DoD, eta_elec, V_batt [V]
    """
    m_pay          = params["m_pay"]
    MF_pay         = params["MF_pay"]
    M_struct_fixed = params["M_struct_fixed"]
    M_avi_fixed    = params["M_avi_fixed"]
    M_prop_fixed   = params["M_prop_fixed"]
    n_motors       = int(params["n_motors"])
    PL             = params["PL"]
    P_avi          = params["P_avi"]
    P_pay          = params["P_pay"]
    t_flight       = params["t_flight"]
    SED            = params["SED"]
    DoD            = params["DoD"]
    eta_elec       = params["eta_elec"]
    V_batt         = params["V_batt"]

    MTOW      = m_pay / MF_pay
    history   = [MTOW]
    converged = False
    M_batt = E_req = P_total = P_motor = T_motor = 0.0

    for _ in range(50):
        T_motor = MTOW / n_motors
        P_motor = (T_motor * 1000.0) / PL
        P_total = n_motors * P_motor + P_avi + P_pay
        E_req   = P_total * t_flight
        M_batt  = E_req / (SED * DoD * eta_elec)

        MTOW_new = m_pay + M_struct_fixed + M_avi_fixed + M_prop_fixed + M_batt
        history.append(MTOW_new)

        if abs(MTOW_new - MTOW) < 1e-4:
            MTOW      = MTOW_new
            converged = True
            break
        MTOW = MTOW_new

    if not converged:
        MTOW = history[-1]

    C_mAh        = (E_req * 1000.0) / V_batt
    C_mAh_target = C_mAh * 1.15

    return {
        "M_TO":         MTOW,
        "history":      history,
        "n_iterations": len(history) - 1,
        "converged":    converged,
        "m_pay":        m_pay,
        "m_struct":     M_struct_fixed,
        "m_avi":        M_avi_fixed,
        "M_prop":       M_prop_fixed,
        "M_batt":       M_batt,
        "T_motor_g":    T_motor * 1000.0,
        "T_at_50pct_g": T_motor * 1000.0 / 2.0,
        "P_motor_W":    P_motor,
        "P_total_W":    P_total,
        "E_req_Wh":     E_req,
        "C_mAh":        C_mAh,
        "C_mAh_target": C_mAh_target,
        "PL":           PL,
    }
