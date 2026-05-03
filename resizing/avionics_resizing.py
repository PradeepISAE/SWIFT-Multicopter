"""Avionics mass and power aggregation for the Resizing Phase."""


def total_avionics(components: list) -> tuple:
    """Sum component masses and power draws.

    components: list of dicts with keys 'Mass_g' and 'Power_W'.
    Returns (M_avi_kg, P_avi_W).
    """
    mass_g  = sum(float(c.get("Mass_g",  0.0)) for c in components)
    power_W = sum(float(c.get("Power_W", 0.0)) for c in components)
    return mass_g / 1000.0, power_W
