"""Battery requirements and selection for the Resizing Phase."""


def battery_requirements(P_motor_W: float, n_motors: int,
                          P_avi_W: float, P_pay_W: float,
                          t_flight_h: float, SED: float,
                          DoD: float, eta: float, V_batt: float) -> dict:
    """Compute required battery energy, mass, and capacity.

    Returns dict with P_total_W, E_req_Wh, M_batt_req_kg,
    C_req_mAh, C_target_mAh (C_req × 1.15).
    """
    P_total    = n_motors * P_motor_W + P_avi_W + P_pay_W
    E_req      = P_total * t_flight_h
    M_batt_req = E_req / (SED * DoD * eta)
    C_req      = (E_req * 1000.0) / V_batt
    return {
        "P_total_W":    P_total,
        "E_req_Wh":     E_req,
        "M_batt_req_kg": M_batt_req,
        "C_req_mAh":    C_req,
        "C_target_mAh": C_req * 1.15,
    }


def match_battery(batteries: list, C_target_mAh: float) -> int:
    """Return index of lightest feasible battery (capacity ≥ C_target).

    Returns -1 if no battery meets the requirement.
    """
    feasible = [
        (i, float(b.get("Capacity_mAh", 0)), float(b.get("Mass_g", 9999)))
        for i, b in enumerate(batteries)
        if float(b.get("Capacity_mAh", 0)) >= C_target_mAh
    ]
    return min(feasible, key=lambda x: x[2])[0] if feasible else -1


def battery_specific_energy(capacity_mAh: float, cells: int,
                             cell_voltage_V: float, mass_g: float) -> float:
    """Compute battery specific energy [Wh/kg]."""
    if mass_g <= 0:
        return 0.0
    E_Wh = capacity_mAh / 1000.0 * cells * cell_voltage_V
    return E_Wh / (mass_g / 1000.0)
