"""
SLSQP optimisation — SWIFT Resizing Phase.

Design variables: x = [k_arm, k_ratio]
  k_arm   = arm length factor  (L_arm = k_arm × D_prop/2)
  k_ratio = inner/outer ratio  (d_in/d_out  or  b_in/b_out)

Objective:  minimise MTOW(k_arm, k_ratio)

Constraints (all ≥ 0):
  g1: σ_allow/FoS − σ_root ≥ 0          (structural — Pollet 2024 Eq. 3.23)
  g2: d_between − D_prop − c_margin ≥ 0 (prop clearance)
  g3: T_100pct×n − (T/W)_req × MTOW×g ≥ 0 (thrust-to-weight)
  g4: M_struct_sizing − M_arms ≥ 0      (positive body mass)

Reference: Pollet (2024) PhD Thesis §3.4.
"""
import numpy as np
from scipy.optimize import minimize

from .structure_resizing import (
    compute_structural_sizing, compute_F_max, prop_clearance, solve_arm,
)
from .convergence_resizing import run_resizing


def _mtow_from_x(x, base_params):
    """Objective: run full convergence loop for candidate [k_arm, k_ratio]."""
    k_arm, k_ratio = x
    p = dict(base_params)
    p["k_arm"]   = k_arm
    p["k_ratio"] = k_ratio
    try:
        return run_resizing(p)["M_TO"]
    except Exception:
        return 1e6  # large penalty on numerical failure


def run_optimisation(base_params: dict,
                     T_100pct_N: float,
                     TW_required: float = 2.0,
                     c_margin_m: float = 0.010,
                     x0: list = None,
                     bounds: list = None) -> tuple:
    """Run SLSQP optimisation over [k_arm, k_ratio].

    base_params: full params dict accepted by run_resizing().
                 Must also contain: D_prop_m, cs_type, rho, sigma_allow_Pa,
                                    FoS, n_motors, M_struct_sizing_kg, a_TO_ms2.
    T_100pct_N:  max thrust per motor at 100% throttle [N].
    TW_required: required thrust-to-weight ratio [-].
    Returns (OptimizeResult, history_list).
    """
    D_prop_m       = base_params["D_prop_m"]
    n_motors       = int(base_params["n_motors"])
    sigma_allow_Pa = base_params["sigma_allow_Pa"]
    FoS_req        = base_params["FoS"]
    a_TO           = base_params["a_TO_ms2"]
    M_struct_sz    = base_params["M_struct_sizing_kg"]
    cs_type        = base_params["cs_type"]
    k_ratio_init   = base_params.get("k_ratio", 0.7)
    k_arm_init     = base_params.get("k_arm", 1.2)

    if x0 is None:
        x0 = [k_arm_init, k_ratio_init]
    if bounds is None:
        bounds = [(1.0, 3.0), (0.3, 0.90)]

    history = []

    def objective(x):
        return _mtow_from_x(x, base_params)

    def g1_structural(x):
        """FoS_actual − FoS_req ≥ 0."""
        k_arm, k_ratio = x
        L_arm   = k_arm * D_prop_m / 2.0
        F_max   = compute_F_max(
            _mtow_from_x(x, base_params), a_TO, n_motors)
        M_root  = F_max * L_arm
        dims    = solve_arm(cs_type, M_root, sigma_allow_Pa, FoS_req,
                            k_ratio, base_params.get("b_plate_m", 0.012))
        return dims["FoS_actual"] - FoS_req

    def g2_clearance(x):
        """d_between − D_prop − margin ≥ 0."""
        k_arm, _k = x
        L_arm = k_arm * D_prop_m / 2.0
        d_between, _ = prop_clearance(L_arm, D_prop_m, n_motors, c_margin_m)
        return d_between - (D_prop_m + c_margin_m)

    def g3_thrust_weight(x):
        """T_100pct×n / (MTOW×g) − TW_req ≥ 0."""
        MTOW = _mtow_from_x(x, base_params)
        tw   = (T_100pct_N * n_motors) / (MTOW * 9.81) if MTOW > 0 else 0.0
        return tw - TW_required

    def g4_positive_body(x):
        """M_struct_sizing − M_arms ≥ 0."""
        k_arm, k_ratio = x
        L_arm   = k_arm * D_prop_m / 2.0
        F_max   = compute_F_max(
            _mtow_from_x(x, base_params), a_TO, n_motors)
        M_root  = F_max * L_arm
        dims    = solve_arm(cs_type, M_root, sigma_allow_Pa, FoS_req,
                            k_ratio, base_params.get("b_plate_m", 0.012))
        rho     = base_params["rho"]
        m_one   = rho * dims["A_m2"] * L_arm
        M_arms  = n_motors * m_one
        return M_struct_sz - M_arms

    def callback(x):
        f = _mtow_from_x(x, base_params)
        history.append({
            "iter":    len(history) + 1,
            "k_arm":   float(x[0]),
            "k_ratio": float(x[1]),
            "MTOW":    float(f),
        })

    constraints = [
        {"type": "ineq", "fun": g1_structural},
        {"type": "ineq", "fun": g2_clearance},
        {"type": "ineq", "fun": g3_thrust_weight},
        {"type": "ineq", "fun": g4_positive_body},
    ]

    res = minimize(
        objective, x0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        callback=callback,
        options={"maxiter": 200, "ftol": 1e-6, "disp": False},
    )
    return res, history
