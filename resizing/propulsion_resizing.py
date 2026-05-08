"""
Propulsion mass and feasibility — SWIFT Resizing Phase.

Architecture modes
  AIO Stack  : ESC integrated in avionics; M_prop = n×(m_motor+m_prop)/1000
  Separate FC: ESC counted here;           M_prop = n×(m_motor+m_prop+m_ESC)/1000

Power loading
  PL_50pct  = T_50pct_g  / P_50pct_W   [g/W]
  PL_100pct = T_100pct_g / P_100pct_W  [g/W]
"""


# ── Default catalogues ────────────────────────────────────────────────────────

MOTOR_DEFAULTS = [
    {
        "Motor":           "T-Motor F40 PRO IV 2400KV",
        "Mass_g":          32.0,
        "T_50pct_g":       420.0,
        "P_50pct_W":        85.0,
        "T_100pct_g":      760.0,
        "P_100pct_W":      210.0,
        "PL_50pct_gW":     0.0,
        "PL_100pct_gW":    0.0,
        "Selected":        False,
    },
    {
        "Motor":           "T-Motor F60 PRO IV 1750KV",
        "Mass_g":          65.0,
        "T_50pct_g":       850.0,
        "P_50pct_W":       180.0,
        "T_100pct_g":     1500.0,
        "P_100pct_W":      420.0,
        "PL_50pct_gW":     0.0,
        "PL_100pct_gW":    0.0,
        "Selected":        False,
    },
    {
        "Motor":           "Sunnysky X2212 980KV",
        "Mass_g":          53.0,
        "T_50pct_g":       550.0,
        "P_50pct_W":       110.0,
        "T_100pct_g":     1050.0,
        "P_100pct_W":      280.0,
        "PL_50pct_gW":     0.0,
        "PL_100pct_gW":    0.0,
        "Selected":        False,
    },
    {
        "Motor":           "Parrot Bebop 2 (ANAFI proxy)",
        "Mass_g":          10.0,
        "T_50pct_g":       117.0,
        "P_50pct_W":        25.4,
        "T_100pct_g":      210.0,
        "P_100pct_W":       56.0,
        "PL_50pct_gW":     0.0,
        "PL_100pct_gW":    0.0,
        "Selected":        True,
    },
    {
        "Motor":           "Custom",
        "Mass_g":          0.0,
        "T_50pct_g":       0.0,
        "P_50pct_W":       0.0,
        "T_100pct_g":      0.0,
        "P_100pct_W":      0.0,
        "PL_50pct_gW":     0.0,
        "PL_100pct_gW":    0.0,
        "Selected":        False,
    },
]

PROP_DEFAULTS = [
    {"Propeller": "6×3 GemFan", "Diameter_in": 6.0,  "Diameter_m": 0.0, "Mass_g": 4.5,  "Selected": False},
    {"Propeller": "7×4 T-Motor", "Diameter_in": 7.0,  "Diameter_m": 0.0, "Mass_g": 7.0,  "Selected": False},
    {"Propeller": "8×4.5 APC",  "Diameter_in": 8.0,  "Diameter_m": 0.0, "Mass_g": 9.0,  "Selected": False},
    {"Propeller": "9×5 Tarot",  "Diameter_in": 9.0,  "Diameter_m": 0.0, "Mass_g": 12.0, "Selected": False},
    {"Propeller": "10×4.7 DJI", "Diameter_in": 10.0, "Diameter_m": 0.0, "Mass_g": 14.0, "Selected": True},
    {"Propeller": "Parrot 6.6in","Diameter_in": 6.6, "Diameter_m": 0.0, "Mass_g": 3.0,  "Selected": False},
    {"Propeller": "Custom",      "Diameter_in": 0.0,  "Diameter_m": 0.0, "Mass_g": 0.0,  "Selected": False},
]

ESC_DEFAULTS = [
    {"ESC": "Hobbywing XRotor 20A",  "Mass_g": 8.0,  "Current_A": 20.0, "Selected": False},
    {"ESC": "Hobbywing XRotor 40A",  "Mass_g": 14.0, "Current_A": 40.0, "Selected": False},
    {"ESC": "T-Motor F35A",          "Mass_g": 9.0,  "Current_A": 35.0, "Selected": True},
    {"ESC": "BLHeli-S 30A",          "Mass_g": 7.0,  "Current_A": 30.0, "Selected": False},
    {"ESC": "Custom",                "Mass_g": 0.0,  "Current_A": 0.0,  "Selected": False},
]


# ── Calculation helpers ───────────────────────────────────────────────────────

def power_loading(T_g: float, P_W: float) -> float:
    """Power loading [g/W]."""
    return T_g / P_W if P_W > 0 else 0.0


def fill_power_loadings(motors: list) -> list:
    """Return copy of motors list with PL_50pct_gW and PL_100pct_gW filled in."""
    out = []
    for m in motors:
        mc = dict(m)
        mc["PL_50pct_gW"]  = power_loading(mc.get("T_50pct_g",  0.0), mc.get("P_50pct_W",  0.0))
        mc["PL_100pct_gW"] = power_loading(mc.get("T_100pct_g", 0.0), mc.get("P_100pct_W", 0.0))
        out.append(mc)
    return out


def fill_prop_diameters(props: list) -> list:
    """Return copy of props list with Diameter_m computed from Diameter_in."""
    out = []
    for p in props:
        pc = dict(p)
        pc["Diameter_m"] = round(pc.get("Diameter_in", 0.0) * 0.0254, 4)
        out.append(pc)
    return out


def propulsion_mass(n_motors: int, m_motor_g: float,
                    m_prop_g: float, m_esc_g: float = 0.0) -> float:
    """Total propulsion group mass [kg].

    Pass m_esc_g=0.0 for AIO architecture (ESC is in avionics table).
    """
    return n_motors * (m_motor_g + m_prop_g + m_esc_g) / 1000.0


def feasibility_check(T_50pct_g_per_motor: float,
                      n_motors: int, MTOW_kg: float,
                      TW_req: float = 2.0) -> tuple:
    """Check T/W ≥ TW_req.

    Returns (TW_actual, margin_N, passed).
    """
    T_total_N  = T_50pct_g_per_motor / 1000.0 * 9.81 * n_motors
    W_N        = MTOW_kg * 9.81
    TW_actual  = T_total_N / W_N if W_N > 0 else 0.0
    margin_N   = T_total_N - TW_req * W_N
    return TW_actual, margin_N, margin_N >= 0.0
