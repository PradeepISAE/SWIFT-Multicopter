"""
Mission segment energy calculations — SWIFT Resizing Phase.

Segments: Takeoff | Climb | Cruise | Hover | Land
Energy per segment: E_k = P_k × t_k  [Wh]

Reference: Pollet (2024) PhD Thesis §3.6.
"""


def compute_P_motors(MTOW_kg: float, PL_50pct_gW: float, n_motors: int) -> float:
    """Total motor power at hover condition [W].

    T_motor = MTOW / n_motors [kg] × 1000 [g/kg]
    P_motor = T_g / PL   [W]
    P_total = n × P_motor
    """
    T_motor_g = MTOW_kg * 1000.0 / n_motors
    P_motor_W = T_motor_g / PL_50pct_gW if PL_50pct_gW > 0 else 0.0
    return n_motors * P_motor_W


def segment_energy(P_motors_W: float, P_avi_W: float, P_pay_W: float,
                   t_min: float, k_throttle: float = 1.0) -> float:
    """Energy for one segment [Wh].

    E = (P_motors × k_throttle + P_avi + P_pay) × t_h
    """
    P = P_motors_W * k_throttle + P_avi_W + P_pay_W
    return P * (t_min / 60.0)


def compute_mission_energy(MTOW_kg: float, PL_50pct_gW: float, n_motors: int,
                           P_avi_W: float, P_pay_W: float,
                           segments: dict, E_cruise_Wh: float = 0.0) -> dict:
    """Compute total mission energy from all active segments.

    segments format:
      {
        "takeoff": {"active": bool, "duration_min": float, "a_TO_ms2": float},
        "climb":   {"active": bool, "duration_min": float},
        "cruise":  {"active": bool, "duration_min": float},
        "hover":   {"active": bool, "duration_min": float},
        "land":    {"active": bool, "duration_min": float, "k_land": float},
      }
    Cruise energy comes pre-computed from Aerodynamics Tab.
    """
    P_motors_W = compute_P_motors(MTOW_kg, PL_50pct_gW, n_motors)
    E = {}

    seg = segments.get("takeoff", {})
    if seg.get("active", True):
        a_TO = seg.get("a_TO_ms2", 19.62)
        k_TO = 1.0 + a_TO / 9.81
        E["takeoff"] = segment_energy(P_motors_W, P_avi_W, P_pay_W,
                                      seg.get("duration_min", 0.5), k_TO)
    else:
        E["takeoff"] = 0.0

    seg = segments.get("climb", {})
    E["climb"] = (segment_energy(P_motors_W, P_avi_W, P_pay_W,
                                 seg.get("duration_min", 2.0), 1.0)
                  if seg.get("active", False) else 0.0)

    seg = segments.get("cruise", {})
    E["cruise"] = E_cruise_Wh if seg.get("active", False) else 0.0

    seg = segments.get("hover", {})
    E["hover"] = (segment_energy(P_motors_W, P_avi_W, P_pay_W,
                                 seg.get("duration_min", 20.0), 1.0)
                  if seg.get("active", True) else 0.0)

    seg = segments.get("land", {})
    if seg.get("active", True):
        k_land = seg.get("k_land", 0.5)
        E["land"] = segment_energy(P_motors_W, P_avi_W, P_pay_W,
                                   seg.get("duration_min", 0.5), k_land)
    else:
        E["land"] = 0.0

    E_total = sum(E.values())
    t_total_h = sum(
        s.get("duration_min", 0.0)
        for s in segments.values() if s.get("active", False)
    ) / 60.0

    return {
        "E_segments": E,
        "E_total_Wh": E_total,
        "P_motors_W": P_motors_W,
        "t_total_h":  t_total_h,
    }
