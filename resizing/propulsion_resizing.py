"""Propulsion mass and feasibility utilities for the Resizing Phase."""


def propulsion_mass(n_motors: int, m_motor_g: float,
                    m_prop_g: float, m_esc_g: float = 0.0) -> float:
    """Total propulsion group mass [kg].

    m_esc_g is per-ESC mass; pass 0.0 for AIO (ESC in avionics table).
    """
    return n_motors * (m_motor_g + m_prop_g + m_esc_g) / 1000.0


def power_loading(T_g: float, P_W: float) -> float:
    """Power loading [g/W]."""
    return T_g / P_W if P_W > 0 else 0.0


def feasibility_check(T_50pct_g_per_motor: float,
                      n_motors: int, MTOW_kg: float) -> tuple:
    """Thrust-feasibility: T_50% × n_motors ≥ MTOW × g × 2.0.

    Returns (margin_N, passed).
    """
    T_total_N  = T_50pct_g_per_motor / 1000.0 * 9.81 * n_motors
    required_N = MTOW_kg * 9.81 * 2.0
    margin_N   = T_total_N - required_N
    return margin_N, margin_N >= 0.0
