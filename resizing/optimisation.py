"""
SLSQP optimisation: minimise MTOW by tuning arm geometry.

Design variables x = [k_arm, dim1_mm, dim2_mm]
  Circular tube:  dim1 = d_outer, dim2 = t_wall
  Square tube:    dim1 = b_outer, dim2 = t_wall
  Flat plate:     dim1 = width b, dim2 = height h
"""
import numpy as np
from scipy.optimize import minimize

from .structure_resizing import section_properties, stress_check, arm_mass_one, prop_clearance
from .convergence_resizing import run_resizing


def _build_dims_m(cs_type, dim1_mm, dim2_mm):
    if cs_type == "Circular tube":
        return {"d_outer": dim1_mm / 1000.0, "t_wall": dim2_mm / 1000.0}
    if cs_type == "Square tube":
        return {"b_outer": dim1_mm / 1000.0, "t_wall": dim2_mm / 1000.0}
    return {"b": dim1_mm / 1000.0, "h": dim2_mm / 1000.0}


def _mtow_from_x(x, cs_type, rho, sigma_allow_MPa,
                 T_max_N, D_prop_m, base_params):
    k_arm, dim1, dim2 = x
    L_arm   = k_arm * D_prop_m / 2.0
    dims_m  = _build_dims_m(cs_type, dim1, dim2)
    _, _, A = section_properties(cs_type, dims_m)

    m_one_arm   = arm_mass_one(rho, A, L_arm)
    M_arms      = base_params["n_motors"] * m_one_arm
    M_struct_sz = base_params["M_struct_sizing"]
    M_body      = max(0.0, M_struct_sz - M_arms)

    p = dict(base_params)
    p["M_struct_fixed"] = M_arms + M_body
    return run_resizing(p)["M_TO"]


def run_optimisation(base_params: dict, cs_type: str,
                     rho: float, sigma_allow_MPa: float,
                     T_max_N: float, D_prop_m: float,
                     x0: list, bounds: list,
                     FoS_req: float = 1.5,
                     c_margin_m: float = 0.010) -> tuple:
    """Run SLSQP optimisation.

    base_params: dict accepted by run_resizing(), plus 'M_struct_sizing' and 'T_50pct_N'.
    x0:     initial [k_arm, dim1_mm, dim2_mm]
    bounds: [(lo,hi), (lo,hi), (lo,hi)]
    Returns (OptimizeResult, history_list).
    history_list elements: {'iter', 'k_arm', 'dim1', 'dim2', 'MTOW'}
    """
    history = []

    def objective(x):
        return _mtow_from_x(x, cs_type, rho, sigma_allow_MPa,
                             T_max_N, D_prop_m, base_params)

    def g_structural(x):
        k_arm, dim1, dim2 = x
        L_arm  = k_arm * D_prop_m / 2.0
        dims_m = _build_dims_m(cs_type, dim1, dim2)
        I, c, _ = section_properties(cs_type, dims_m)
        _, FoS_actual, _ = stress_check(T_max_N, L_arm, I, c,
                                         sigma_allow_MPa, FoS_req)
        return FoS_actual - FoS_req

    def g_clearance(x):
        k_arm, dim1, dim2 = x
        L_arm = k_arm * D_prop_m / 2.0
        d_between, _ = prop_clearance(L_arm, D_prop_m,
                                       base_params["n_motors"], c_margin_m)
        return d_between - (D_prop_m + c_margin_m)

    def g_feasibility(x):
        k_arm, dim1, dim2 = x
        L_arm  = k_arm * D_prop_m / 2.0
        dims_m = _build_dims_m(cs_type, dim1, dim2)
        _, _, A = section_properties(cs_type, dims_m)
        m_one  = arm_mass_one(rho, A, L_arm)
        M_arms = base_params["n_motors"] * m_one
        M_body = max(0.0, base_params["M_struct_sizing"] - M_arms)
        p = dict(base_params)
        p["M_struct_fixed"] = M_arms + M_body
        MTOW = run_resizing(p)["M_TO"]
        T_50_N = base_params.get("T_50pct_N", 0.0)
        return T_50_N * base_params["n_motors"] - MTOW * 9.81 * 2.0

    def callback(x):
        f = objective(x)
        history.append({
            "iter":  len(history) + 1,
            "k_arm": x[0], "dim1": x[1], "dim2": x[2],
            "MTOW":  f,
        })

    constraints = [
        {"type": "ineq", "fun": g_structural},
        {"type": "ineq", "fun": g_clearance},
        {"type": "ineq", "fun": g_feasibility},
    ]

    res = minimize(
        objective, x0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        callback=callback,
        options={"maxiter": 100, "ftol": 1e-6, "disp": False},
    )
    return res, history
