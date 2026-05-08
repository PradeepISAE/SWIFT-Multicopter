"""
Battery requirements and selection — SWIFT Resizing Phase.

Energy is now computed per mission segment (not a single flight time).
Reference: Pollet (2024) PhD Thesis §3.6.
"""


def battery_from_energy(E_total_Wh: float, SED: float, DoD: float,
                         eta_elec: float, V_batt: float) -> dict:
    """Required battery mass and capacity from total mission energy.

    M_batt = E_total / (SED × DoD × η)
    C_req  = E_total × 1000 / V_batt
    C_buf  = C_req × 1.15   (15 % buffer)
    """
    M_batt_kg  = E_total_Wh / (SED * DoD * eta_elec) if (SED * DoD * eta_elec) > 0 else 0.0
    C_req_mAh  = (E_total_Wh * 1000.0) / V_batt if V_batt > 0 else 0.0
    return {
        "M_batt_kg":    M_batt_kg,
        "C_req_mAh":    C_req_mAh,
        "C_target_mAh": C_req_mAh * 1.15,
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
    """Battery specific energy [Wh/kg]."""
    if mass_g <= 0:
        return 0.0
    E_Wh = capacity_mAh / 1000.0 * cells * cell_voltage_V
    return E_Wh / (mass_g / 1000.0)


def battery_total_voltage(cells: int, cell_voltage_V: float) -> float:
    """Pack voltage [V]."""
    return cells * cell_voltage_V
