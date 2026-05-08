"""
Mission segment energy calculations — SWIFT Resizing Phase.

Segments: Takeoff | Climb | Cruise | Hover | Land
Energy per segment: E_k = P_k × t_k  [Wh]

Reference: Pollet (2024) PhD Thesis §3.6.
"""
import math


def isa_density(altitude_m: float) -> float:
    """ISA air density at altitude [m]. Valid for troposphere (0–11 000 m).

    rho = 1.225 × (1 − 2.2558e-5 × h)^4.2559

    Reference: ICAO Standard Atmosphere.
    Returns: air density [kg/m³]
    """
    h = min(max(0.0, float(altitude_m)), 11000.0)
    return 1.225 * (1.0 - 2.2558e-5 * h) ** 4.2559


def altitude_power_correction(altitude_m: float) -> float:
    """Power correction factor for altitude [-].

    From actuator disc / momentum theory: P_hover ∝ 1/√ρ
      P_alt = P_SL × √(ρ_SL / ρ_alt)
      correction = √(ρ_SL / ρ_alt)  ≥ 1.0

    Reference: Pollet (2024) §3.3.2 — momentum theory.
    Returns: correction factor (≥ 1.0, increases with altitude)
    """
    rho_alt = isa_density(altitude_m)
    return math.sqrt(1.225 / max(rho_alt, 1e-6))


def corrected_power_loading(pl_sl_gW: float, altitude_m: float) -> float:
    """Altitude-corrected power loading [g/W].

    PL_alt = PL_SL × √(ρ_alt / ρ_SL)
    Same thrust at altitude requires more power → effective PL decreases.

    Reference: actuator disc momentum theory.
    Returns: altitude-corrected power loading [g/W]
    """
    rho_alt = isa_density(altitude_m)
    return pl_sl_gW * math.sqrt(rho_alt / 1.225)


def compute_P_motors(MTOW_kg: float, PL_50pct_gW: float, n_motors: int,
                     altitude_m: float = 0.0) -> float:
    """Total motor power at hover condition [W].

    T_motor = MTOW / n_motors [kg] × 1000 [g/kg]
    P_motor_SL = T_g / PL   [W]
    P_motor_alt = P_motor_SL × √(ρ_SL / ρ_alt)   (altitude correction)
    P_total = n × P_motor_alt
    """
    T_motor_g = MTOW_kg * 1000.0 / n_motors
    P_motor_W = T_motor_g / PL_50pct_gW if PL_50pct_gW > 0 else 0.0
    if altitude_m > 0.0:
        P_motor_W *= altitude_power_correction(altitude_m)
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
                           segments: dict, E_cruise_Wh: float = 0.0,
                           altitude_m: float = 0.0) -> dict:
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
    P_motors_W = compute_P_motors(MTOW_kg, PL_50pct_gW, n_motors, altitude_m)
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
