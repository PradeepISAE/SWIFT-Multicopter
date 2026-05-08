"""
SLSQP optimisation — SWIFT Resizing Phase.

Design variables: x = [k_arm, t_wall_m]
  k_arm    = arm length factor  (L_arm = k_arm × D_prop/2)
  t_wall_m = physical wall thickness [m]

Objective:  minimise MTOW(k_arm, t_wall_m)  — direct single-step computation.

Constraints (all ≥ 0):
  g1: FoS_actual − FoS_req ≥ 0              (structural — Pollet 2024 Eq. 3.23)
  g2: d_between − D_prop − c_margin ≥ 0     (prop clearance)
  g3: T_100pct×n / (MTOW×g) − TW_req ≥ 0   (thrust-to-weight)
  g4: M_struct_sizing − M_arms ≥ 0          (positive body mass)

struct_params keys:
  profile          "circular" | "square" | "flat_plate"
  t_wall_m         initial/fixed wall thickness guess [m]   (DV, lower bound)
  b_plate_m        flat-plate width [m]
  rho_mat          arm material density [kg/m³]
  sigma_allow_mpa  allowable bending stress [MPa]
  fos              required factor of safety [-]
  n_motors         number of motors/arms
  d_prop_m         propeller diameter [m]
  altitude_m       operating altitude [m] (ISA)
  t_motor_100pct_g motor max thrust [g/motor]   (constraint g3)
  a_to_ms2         takeoff acceleration [m/s²]
  m_struct_sizing  structural mass budget from sizing loop [kg]
  c_margin_m       minimum prop clearance margin [m]
  tw_required      required T/W ratio [-]

base_params keys  (mission / battery / fixed masses):
  mtow_estimate    seed MTOW from last convergence run [kg]
  m_pay            payload mass [kg]
  m_avi            avionics mass [kg]
  m_prop           propulsion mass [kg]
  pl_gW            hover power loading at 50% throttle [g/W]
  t_hover_h        hover time [h]
  P_avi_W          avionics power [W]
  P_pay_W          payload power [W]
  SED_whkg         battery specific energy density [Wh/kg]
  DoD              depth of discharge [-]
  eta_elec         electrical efficiency [-]
  k_arm            current arm factor (used as x0 default)
  segments         mission segments dict (passed to compute_mission_energy)
  E_cruise_Wh      cruise segment energy [Wh]
  V_batt           battery pack voltage [V]

Reference: Pollet (2024) PhD Thesis §3.4 & §3.8.
"""
import math
import numpy as np
from scipy.optimize import minimize

from .structure_resizing import (
    compute_F_max, prop_clearance, solve_arm,
    solve_outer_from_stress, nearest_standard_cf_tube,
    arm_cross_section_area, compute_stress_mpa,
)
from .mission_resizing import compute_mission_energy
from .convergence_resizing import run_resizing


# ── Profile translation helpers ───────────────────────────────────────────────

def _profile_to_cs_type(profile: str) -> str:
    """Translate lowercase profile key → display label used by solve_arm / run_resizing."""
    p = profile.lower().strip()
    if p == "circular":
        return "Circular Hollow Tube"
    if p == "square":
        return "Square Hollow Tube"
    return "Flat Plate"


def _cs_type_to_profile(cs_type: str) -> str:
    """Translate display label → lowercase profile key."""
    if cs_type == "Circular Hollow Tube":
        return "circular"
    if cs_type == "Square Hollow Tube":
        return "square"
    return "flat_plate"


# ── Direct MTOW computation (single step, no iterative run_resizing) ──────────

def _compute_mtow(k_arm: float, t_wall_m: float,
                  base_params: dict, struct_params: dict) -> float:
    """Estimate MTOW in one pass given design variables.

    Uses base_params["mtow_estimate"] as loading seed (fixed MTOW for power calc)
    then recomputes component masses.
    """
    profile      = struct_params["profile"]
    n_motors     = int(struct_params["n_motors"])
    d_prop_m     = struct_params["d_prop_m"]
    rho_mat      = struct_params["rho_mat"]
    sigma_mpa    = struct_params["sigma_allow_mpa"]
    fos          = struct_params["fos"]
    b_plate_m    = struct_params.get("b_plate_m", 0.010)
    a_to         = struct_params.get("a_to_ms2", 19.62)
    altitude_m   = struct_params.get("altitude_m", 0.0)
    m_struct_sz  = struct_params.get("m_struct_sizing", 0.050)

    mtow_seed    = base_params.get("mtow_estimate", 0.500)
    m_pay        = base_params.get("m_pay",   0.030)
    m_avi        = base_params.get("m_avi",   0.030)
    m_prop       = base_params.get("m_prop",  0.020)
    SED          = base_params.get("SED_whkg", 150.0)
    DoD          = base_params.get("DoD",       0.85)
    eta          = base_params.get("eta_elec",  0.85)
    segments     = base_params.get("segments", {})
    E_cruise_Wh  = base_params.get("E_cruise_Wh", 0.0)
    pl_gW        = base_params.get("pl_gW",   4.0)
    P_avi_W      = base_params.get("P_avi_W", 1.3)
    P_pay_W      = base_params.get("P_pay_W", 1.0)

    # Arm geometry
    L_arm  = k_arm * d_prop_m / 2.0
    F_max  = compute_F_max(mtow_seed, a_to, n_motors)
    M_root = F_max * L_arm

    # Solved outer dimension for this t_wall
    try:
        outer_m = solve_outer_from_stress(profile, M_root, sigma_mpa, fos,
                                          t_wall_m, b_plate_m)
    except Exception:
        outer_m = 2.0 * t_wall_m + 1e-4

    # Arm mass
    A_cs   = arm_cross_section_area(profile, outer_m, t_wall_m, b_plate_m)
    m_one  = rho_mat * A_cs * L_arm
    M_arms = n_motors * m_one
    M_body = max(0.0, m_struct_sz - M_arms)
    M_struct = M_arms + M_body

    # Battery mass from mission energy
    try:
        m_out  = compute_mission_energy(
            mtow_seed, pl_gW, n_motors, P_avi_W, P_pay_W,
            segments, E_cruise_Wh, altitude_m=altitude_m,
        )
        E_total = m_out["E_total_Wh"]
    except Exception:
        E_total = 0.0

    if E_total > 0 and SED > 0 and DoD > 0 and eta > 0:
        M_batt = E_total / (SED * DoD * eta)
    else:
        M_batt = 0.0

    return m_pay + m_avi + m_prop + M_struct + M_batt


# ── Constraint helpers ────────────────────────────────────────────────────────

def _arm_dims(k_arm: float, t_wall_m: float,
              base_params: dict, struct_params: dict):
    """Return (outer_m, M_arms, L_arm, M_root, A_cs) for the given DVs."""
    profile    = struct_params["profile"]
    n_motors   = int(struct_params["n_motors"])
    d_prop_m   = struct_params["d_prop_m"]
    rho_mat    = struct_params["rho_mat"]
    sigma_mpa  = struct_params["sigma_allow_mpa"]
    fos        = struct_params["fos"]
    b_plate_m  = struct_params.get("b_plate_m", 0.010)
    a_to       = struct_params.get("a_to_ms2", 19.62)
    mtow_seed  = base_params.get("mtow_estimate", 0.500)

    L_arm  = k_arm * d_prop_m / 2.0
    F_max  = compute_F_max(mtow_seed, a_to, n_motors)
    M_root = F_max * L_arm
    try:
        outer_m = solve_outer_from_stress(profile, M_root, sigma_mpa, fos,
                                          t_wall_m, b_plate_m)
    except Exception:
        outer_m = 2.0 * t_wall_m + 1e-4
    A_cs   = arm_cross_section_area(profile, outer_m, t_wall_m, b_plate_m)
    m_one  = rho_mat * A_cs * L_arm
    M_arms = n_motors * m_one
    return outer_m, M_arms, L_arm, M_root, A_cs


def _g1_stress(x, struct_params, base_params):
    """g1 = FoS_actual − FoS_req ≥ 0."""
    k_arm, t_wall_m = x
    fos     = struct_params["fos"]
    profile = struct_params["profile"]
    sigma_mpa = struct_params["sigma_allow_mpa"]
    b_plate_m = struct_params.get("b_plate_m", 0.010)

    outer_m, _, _, M_root, _ = _arm_dims(k_arm, t_wall_m, base_params, struct_params)
    sigma_actual = compute_stress_mpa(profile, M_root, outer_m, t_wall_m, b_plate_m)
    FoS_actual   = sigma_mpa / max(sigma_actual, 1e-12)
    return FoS_actual - fos


def _g2_clearance(x, struct_params):
    """g2 = d_between − D_prop − c_margin ≥ 0."""
    k_arm, _  = x
    n_motors  = int(struct_params["n_motors"])
    d_prop_m  = struct_params["d_prop_m"]
    c_margin  = struct_params.get("c_margin_m", 0.010)
    L_arm     = k_arm * d_prop_m / 2.0
    d_between, _ = prop_clearance(L_arm, d_prop_m, n_motors, c_margin)
    return d_between - (d_prop_m + c_margin)


def _g3_tw(x, struct_params, base_params):
    """g3 = T_100pct×n / (MTOW×g) − TW_req ≥ 0."""
    k_arm, t_wall_m = x
    n_motors    = int(struct_params["n_motors"])
    T_100pct_N  = struct_params.get("t_motor_100pct_g", 0.0) * 9.81 / 1000.0
    tw_req      = struct_params.get("tw_required", 2.0)
    MTOW        = _compute_mtow(k_arm, t_wall_m, base_params, struct_params)
    if MTOW <= 0 or T_100pct_N <= 0:
        return -1.0
    return (T_100pct_N * n_motors) / (MTOW * 9.81) - tw_req


def _g4_body_mass(x, struct_params, base_params):
    """g4 = M_struct_sizing − M_arms ≥ 0."""
    k_arm, t_wall_m = x
    m_struct_sz = struct_params.get("m_struct_sizing", 0.050)
    _, M_arms, _, _, _ = _arm_dims(k_arm, t_wall_m, base_params, struct_params)
    return m_struct_sz - M_arms


# ── Public API ────────────────────────────────────────────────────────────────

def run_optimisation(base_params: dict,
                     struct_params: dict,
                     x0: list = None,
                     bounds: list = None) -> tuple:
    """Run SLSQP optimisation over [k_arm, t_wall_m].

    Returns (OptimizeResult, history_list, phys_dims_dict).
    phys_dims keys: profile, k_arm, t_wall_mm, d_out_mm, d_in_mm, k_ratio,
                    L_arm_mm, FoS_actual, sigma_mpa, M_arms_g, M_batt_g,
                    std_cf_od_mm, std_cf_wall_mm.
    """
    profile  = struct_params["profile"]
    d_prop_m = struct_params["d_prop_m"]
    fos      = struct_params["fos"]
    sigma_mpa = struct_params["sigma_allow_mpa"]
    b_plate_m = struct_params.get("b_plate_m", 0.010)

    if x0 is None:
        x0 = [
            float(base_params.get("k_arm", 1.2)),
            float(struct_params.get("t_wall_m", 0.001)),
        ]
    if bounds is None:
        bounds = [(1.0, 3.0), (0.0003, 0.003)]

    history = []

    def objective(x):
        try:
            return _compute_mtow(x[0], x[1], base_params, struct_params)
        except Exception:
            return 1e6

    def callback(x):
        f = objective(x)
        history.append({
            "iter":      len(history) + 1,
            "k_arm":     float(x[0]),
            "t_wall_mm": float(x[1]) * 1000.0,
            "MTOW":      float(f),
        })

    constraints = [
        {"type": "ineq", "fun": _g1_stress,    "args": (struct_params, base_params)},
        {"type": "ineq", "fun": _g2_clearance, "args": (struct_params,)},
        {"type": "ineq", "fun": _g3_tw,        "args": (struct_params, base_params)},
        {"type": "ineq", "fun": _g4_body_mass, "args": (struct_params, base_params)},
    ]

    res = minimize(
        objective, x0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        callback=callback,
        options={"maxiter": 200, "ftol": 1e-6, "disp": False},
    )

    # ── Post-process at optimum ───────────────────────────────────────────────
    k_arm_opt, t_wall_opt = float(res.x[0]), float(res.x[1])
    outer_opt, M_arms_opt, L_arm_opt, M_root_opt, A_cs_opt = _arm_dims(
        k_arm_opt, t_wall_opt, base_params, struct_params)

    d_in_opt = max(0.0, outer_opt - 2.0 * t_wall_opt)
    k_ratio_opt = (
        max(0.01, min(0.99, (outer_opt - 2.0 * t_wall_opt) / outer_opt))
        if profile in ("circular", "square") and outer_opt > 2.0 * t_wall_opt
        else 0.0
    )

    sigma_opt    = compute_stress_mpa(profile, M_root_opt, outer_opt, t_wall_opt, b_plate_m)
    FoS_actual   = sigma_mpa / max(sigma_opt, 1e-12)
    std_cf       = nearest_standard_cf_tube(outer_opt * 1000.0, t_wall_opt * 1000.0)

    # Battery mass at optimum via full run_resizing (best estimate)
    cs_type_old = _profile_to_cs_type(profile)
    try:
        p_opt = {
            **base_params,
            "k_arm":   k_arm_opt,
            "k_ratio": k_ratio_opt,
            "cs_type": cs_type_old,
        }
        rz_opt     = run_resizing(p_opt)
        M_batt_opt = rz_opt.get("M_batt", 0.0)
    except Exception:
        M_batt_opt = 0.0

    phys_dims = {
        "profile":       profile,
        "k_arm":         k_arm_opt,
        "t_wall_mm":     t_wall_opt * 1000.0,
        "d_out_mm":      outer_opt  * 1000.0,
        "d_in_mm":       d_in_opt   * 1000.0,
        "k_ratio":       k_ratio_opt,
        "L_arm_mm":      L_arm_opt  * 1000.0,
        "FoS_actual":    FoS_actual,
        "sigma_mpa":     sigma_opt,
        "M_arms_g":      M_arms_opt * 1000.0,
        "M_batt_g":      M_batt_opt * 1000.0,
        "std_cf_od_mm":  std_cf[0],
        "std_cf_wall_mm": std_cf[1],
    }

    return res, history, phys_dims
