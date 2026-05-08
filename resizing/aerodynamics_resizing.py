"""
Cruise aerodynamics — SWIFT Resizing Phase.

Reference: Pollet (2024) PhD Thesis §3.6.1, Tyan et al. (2017) Eq. 17.

Level forward-flight equilibrium (multirotor with tilted thrust vector):
  N_rotors × F_cruise = sqrt((W + L_f)² + D_f²)
  (W dominates; L_f ≈ 0 for symmetric multirotor bodies, C_L default = 0)

Figure-of-merit (Tyan 2017, Eq. 17):
  FM = 0.4742 × T^0.0793   (T in Newtons, per motor)
"""
import numpy as np


def figure_of_merit(T_N: float) -> float:
    """Tyan 2017 Eq. 17 figure-of-merit. T in Newtons."""
    T = max(T_N, 1e-9)
    return 0.4742 * T ** 0.0793


def cruise_induced_velocity(F_motor_N: float, D_prop_m: float,
                            rho_air: float) -> float:
    """Momentum theory induced velocity at disk [m/s].

    v_i = sqrt(F / (2 × rho × A_disk))
    """
    A_disk = np.pi * (D_prop_m / 2.0) ** 2
    denom  = 2.0 * rho_air * A_disk
    return np.sqrt(F_motor_N / denom) if denom > 0 else 0.0


def compute_cruise(MTOW_kg: float, V_cruise_ms: float,
                   C_D: float, C_L: float, rho_air: float,
                   S_top: float, S_front: float,
                   D_prop_m: float, n_motors: int,
                   P_avi_W: float, P_pay_W: float,
                   t_cruise_h: float) -> dict:
    """Full cruise aerodynamics + energy budget.

    Returns dict with F_cruise, P_cruise, E_cruise and intermediate values.
    """
    W = MTOW_kg * 9.81  # N

    # Reference area: use S_front for cruise (drag on frontal area)
    S_ref = S_front if S_front > 0 else S_top

    D_f = 0.5 * C_D * rho_air * V_cruise_ms ** 2 * S_ref
    L_f = 0.5 * C_L * rho_air * V_cruise_ms ** 2 * S_ref

    # Total rotor thrust required
    F_cruise_total = np.sqrt((W + L_f) ** 2 + D_f ** 2)
    F_cruise_motor = F_cruise_total / n_motors  # per motor [N]

    # Power via figure-of-merit + induced velocity
    v_i    = cruise_induced_velocity(F_cruise_motor, D_prop_m, rho_air)
    FM     = figure_of_merit(F_cruise_motor)
    P_mech = F_cruise_motor * v_i / FM if FM > 0 else 0.0

    P_cruise_total = n_motors * P_mech + P_avi_W + P_pay_W
    E_cruise_Wh    = P_cruise_total * t_cruise_h

    # Power loading in cruise
    PL_cruise = (MTOW_kg * 1000.0) / P_cruise_total if P_cruise_total > 0 else 0.0

    return {
        "D_f_N":            D_f,
        "L_f_N":            L_f,
        "S_ref_m2":         S_ref,
        "F_cruise_total_N": F_cruise_total,
        "F_cruise_motor_N": F_cruise_motor,
        "v_i_ms":           v_i,
        "FM":               FM,
        "P_motor_cruise_W": P_mech,
        "P_cruise_total_W": P_cruise_total,
        "E_cruise_Wh":      E_cruise_Wh,
        "PL_cruise_gW":     PL_cruise,
    }
