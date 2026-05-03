"""
Propulsion mass model for SWIFT.

Propulsion mass is computed directly from datasheet inputs — no empirical model:
    M_propulsion = n_motors × (M_motor_kg + M_prop_kg)

M_mot/P_max is provided as a reference-only ratio for display.
"""


def propulsion_mass_kg(
    n_motors:  int,
    M_motor_g: float,
    M_prop_g:  float,
) -> dict:
    """Total propulsion group mass [kg] from per-unit datasheet values.

    Returns a dict with breakdown and the total M_prop [kg].
    """
    M_motor_kg = M_motor_g / 1000.0
    M_prop_kg  = M_prop_g  / 1000.0

    m_motors_kg = n_motors * M_motor_kg
    m_props_kg  = n_motors * M_prop_kg
    M_prop      = m_motors_kg + m_props_kg

    return {
        "M_prop":       M_prop,
        "m_motors_kg":  m_motors_kg,
        "m_props_kg":   m_props_kg,
        "M_motor_g":    M_motor_g,
        "M_prop_g":     M_prop_g,
    }


def specific_mass_ratio(M_motor_g: float, P_max_W: float) -> float:
    """Reference specific mass ratio [g/W] = M_motor [g] / P_max [W].

    Not used in mass calculations — displayed as a motor quality indicator.
    Lower is better (lighter motor per watt of power).
    """
    if P_max_W <= 0:
        return 0.0
    return M_motor_g / P_max_W
