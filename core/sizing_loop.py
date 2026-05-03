"""
Fixed-point mass convergence loop for SWIFT sizing.

Governing equations:
  MTOW_0 = m_pay / MF_pay   (seed — DIVISION not multiplication)

  At each iteration k:
    M_str(k)   = MF_str × MTOW(k)
    M_avi(k)   = MF_avi × MTOW(k)
    T_motor(k) = MTOW(k) / n_motors              [kg]
    P_motor(k) = (T_motor(k) × 1000) / PL        [W]   PL in g/W
    P_total(k) = n_motors × P_motor(k) + P_avi + P_pay  [W]
    E_req(k)   = P_total(k) × t_flight            [Wh]  t in hours
    M_batt(k)  = E_req(k) / (SED × DoD × eta_elec) [kg]
    MTOW(k+1)  = m_pay + M_str(k) + M_avi(k) + M_prop_fixed + M_batt(k)

Converges when |MTOW(k+1) - MTOW(k)| < 1e-4 kg, or after 50 iterations.
"""


def run_sizing(params: dict) -> dict:
    """Execute fixed-point sizing loop for a single power loading value.

    Required keys in params:
        m_pay, MF_pay, MF_str, MF_avi,
        n_motors, M_motor_g, M_prop_g,
        PL [g/W], P_avi [W], P_pay [W],
        t_flight [h], SED [Wh/kg], DoD, eta_elec, V_batt [V]
    """
    m_pay    = params["m_pay"]
    MF_pay   = params["MF_pay"]
    MF_str   = params["MF_str"]
    MF_avi   = params["MF_avi"]
    n_motors = int(params["n_motors"])
    PL       = params["PL"]        # g/W
    P_avi    = params["P_avi"]     # W
    P_pay    = params["P_pay"]     # W
    t_flight = params["t_flight"]  # hours
    SED      = params["SED"]       # Wh/kg
    DoD      = params["DoD"]
    eta_elec = params["eta_elec"]
    V_batt   = params["V_batt"]    # V

    M_motor_kg   = params["M_motor_g"] / 1000.0
    M_prop_kg    = params["M_prop_g"]  / 1000.0
    M_prop_fixed = n_motors * (M_motor_kg + M_prop_kg)

    # Seed MTOW from payload fraction
    MTOW = m_pay / MF_pay
    history = [MTOW]
    converged = False

    # Working variables (populated inside loop, referenced after)
    M_str = M_avi = T_motor = P_motor = P_total = E_req = M_batt = 0.0

    for _ in range(50):
        M_str   = MF_str * MTOW
        M_avi   = MF_avi * MTOW
        T_motor = MTOW / n_motors           # kg — hover thrust per motor
        P_motor = (T_motor * 1000.0) / PL   # W  (T in g, PL in g/W)
        P_total = n_motors * P_motor + P_avi + P_pay
        E_req   = P_total * t_flight
        M_batt  = E_req / (SED * DoD * eta_elec)

        MTOW_new = m_pay + M_str + M_avi + M_prop_fixed + M_batt
        history.append(MTOW_new)

        if abs(MTOW_new - MTOW) < 1e-4:
            MTOW = MTOW_new
            converged = True
            break
        MTOW = MTOW_new

    if not converged:
        MTOW = history[-1]

    C_mAh        = (E_req * 1000.0) / V_batt
    C_mAh_target = C_mAh * 1.15

    return {
        "M_TO":           MTOW,
        "history":        history,
        "n_iterations":   len(history) - 1,
        "converged":      converged,
        # mass breakdown
        "m_pay":          m_pay,
        "m_struct":       M_str,
        "m_avi":          M_avi,
        "M_prop":         M_prop_fixed,
        "M_batt":         M_batt,
        # propulsion detail
        "T_motor_g":      T_motor * 1000.0,
        "T_at_50pct_g":   T_motor * 1000.0 / 2.0,
        "P_motor_W":      P_motor,
        # power / energy
        "P_total_W":      P_total,
        "E_req_Wh":       E_req,
        # battery capacity
        "C_mAh":          C_mAh,
        "C_mAh_target":   C_mAh_target,
        "PL":             PL,
    }


def run_sizing_sweep(params: dict, pl_values: list) -> list:
    """Run sizing loop for a list of power loading values."""
    results = []
    for pl in pl_values:
        p = dict(params)
        p["PL"] = pl
        results.append(run_sizing(p))
    return results
