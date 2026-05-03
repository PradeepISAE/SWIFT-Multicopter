"""Mission parameter helpers for the Resizing Phase."""


def effective_pl(T_50pct_g: float, P_50pct_W: float) -> float:
    """Effective power loading [g/W] at 50% throttle (hover condition)."""
    return T_50pct_g / P_50pct_W if P_50pct_W > 0 else 0.0


def required_capacity_mAh(P_total_W: float, t_flight_h: float,
                           V_batt: float) -> float:
    """Minimum battery capacity [mAh]."""
    return (P_total_W * t_flight_h * 1000.0) / V_batt if V_batt > 0 else 0.0
