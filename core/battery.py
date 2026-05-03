"""
Battery sizing utility for SWIFT (reference module — not called by sizing_loop directly).

Hover power model:
  T_motor [kg] = M_TO [kg] / n_motors
  P_motor [W]  = (T_motor * 1000) / PL       PL in g/W
  P_total [W]  = n_motors * P_motor + P_avi + P_pay
  E_req   [Wh] = P_total * t_flight [h]
  M_batt  [kg] = E_req / (SED * DoD * eta_elec)
"""


def battery_sizing(
    M_TO_kg:     float,
    n_motors:    int,
    P_avi_W:     float,
    P_pay_W:     float,
    PL_gW:       float,
    t_flight_h:  float,
    SED_Whkg:    float,
    DoD:         float,
    eta_elec:    float,
) -> dict:
    """Compute battery mass and associated hover power budget."""
    T_motor_kg = M_TO_kg / n_motors
    T_motor_g  = T_motor_kg * 1000.0
    P_motor_W  = T_motor_g / PL_gW
    P_total_W  = n_motors * P_motor_W + P_avi_W + P_pay_W
    E_req_Wh   = P_total_W * t_flight_h
    M_batt_kg  = E_req_Wh / (SED_Whkg * DoD * eta_elec)

    return {
        "T_motor_g": T_motor_g,
        "P_motor_W": P_motor_W,
        "P_total_W": P_total_W,
        "E_req_Wh":  E_req_Wh,
        "M_batt_kg": M_batt_kg,
    }
