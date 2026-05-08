"""
Avionics mass and power aggregation — SWIFT Resizing Phase.

M_avi = Σ m_component / 1000  [kg]
P_avi = Σ P_component          [W]
"""


def total_avionics(components: list) -> tuple:
    """Sum enabled component masses and power draws.

    components: list of dicts with keys 'Mass_g', 'Power_W'.
    Returns (M_avi_kg, P_avi_W).
    """
    mass_g  = sum(float(c.get("Mass_g",  0.0)) for c in components)
    power_W = sum(float(c.get("Power_W", 0.0)) for c in components)
    return mass_g / 1000.0, power_W


# Default component lists per architecture
AIO_STACK_DEFAULTS = [
    {"Component": "FC + ESC AIO Stack",  "Enabled": True,  "Mass_g": 9.0,  "Power_W": 0.8,  "Notes": "e.g. Matek H743-SLIM"},
    {"Component": "GPS / Compass",        "Enabled": True,  "Mass_g": 16.0, "Power_W": 0.3,  "Notes": "e.g. M8N"},
    {"Component": "Telemetry (433 MHz)",  "Enabled": True,  "Mass_g": 5.5,  "Power_W": 0.2,  "Notes": "e.g. SiK 100mW"},
    {"Component": "RC Receiver",          "Enabled": True,  "Mass_g": 2.5,  "Power_W": 0.1,  "Notes": "e.g. ExpressLRS"},
    {"Component": "Power Module",         "Enabled": True,  "Mass_g": 6.0,  "Power_W": 0.2,  "Notes": "Current/voltage sensor"},
    {"Component": "Buzzer",               "Enabled": True,  "Mass_g": 1.5,  "Power_W": 0.05, "Notes": ""},
    {"Component": "Video Transmitter",    "Enabled": False, "Mass_g": 12.0, "Power_W": 1.5,  "Notes": "FPV VTx"},
    {"Component": "Optical Flow Sensor",  "Enabled": False, "Mass_g": 3.5,  "Power_W": 0.2,  "Notes": ""},
    {"Component": "ToF Range Sensor",     "Enabled": False, "Mass_g": 2.0,  "Power_W": 0.1,  "Notes": ""},
    {"Component": "LED Strip",            "Enabled": False, "Mass_g": 5.0,  "Power_W": 0.8,  "Notes": ""},
    {"Component": "Custom 1",             "Enabled": False, "Mass_g": 0.0,  "Power_W": 0.0,  "Notes": ""},
    {"Component": "Custom 2",             "Enabled": False, "Mass_g": 0.0,  "Power_W": 0.0,  "Notes": ""},
]

SEPARATE_FC_DEFAULTS = [
    {"Component": "Flight Controller",    "Enabled": True,  "Mass_g": 9.0,  "Power_W": 0.5,  "Notes": "e.g. Pixhawk 6C Mini"},
    {"Component": "GPS / Compass",        "Enabled": True,  "Mass_g": 16.0, "Power_W": 0.3,  "Notes": "e.g. M8N"},
    {"Component": "Telemetry (433 MHz)",  "Enabled": True,  "Mass_g": 5.5,  "Power_W": 0.2,  "Notes": "e.g. SiK"},
    {"Component": "RC Receiver",          "Enabled": True,  "Mass_g": 2.5,  "Power_W": 0.1,  "Notes": ""},
    {"Component": "Power Module",         "Enabled": True,  "Mass_g": 6.0,  "Power_W": 0.2,  "Notes": ""},
    {"Component": "Buzzer",               "Enabled": True,  "Mass_g": 1.5,  "Power_W": 0.05, "Notes": ""},
    {"Component": "Video Transmitter",    "Enabled": False, "Mass_g": 12.0, "Power_W": 1.5,  "Notes": ""},
    {"Component": "Optical Flow Sensor",  "Enabled": False, "Mass_g": 3.5,  "Power_W": 0.2,  "Notes": ""},
    {"Component": "ToF Range Sensor",     "Enabled": False, "Mass_g": 2.0,  "Power_W": 0.1,  "Notes": ""},
    {"Component": "LED Strip",            "Enabled": False, "Mass_g": 5.0,  "Power_W": 0.8,  "Notes": ""},
    {"Component": "Custom 1",             "Enabled": False, "Mass_g": 0.0,  "Power_W": 0.0,  "Notes": ""},
    {"Component": "Custom 2",             "Enabled": False, "Mass_g": 0.0,  "Power_W": 0.0,  "Notes": ""},
]
