"""
Arm structural sizing — SWIFT Resizing Phase.

Cantilever beam model: tip load = F_max per arm (takeoff worst-case).
Dimensions are SOLVED from the stress constraint (not just checked).

Reference: Pollet (2024) PhD Thesis, Eq. 3.23 / 3.47.

Verification (circular, CF tube):
  n=4, T_100=200g/motor → MTOW≈0.8kg, a_TO=2g, D_prop=5in=0.127m
  k_arm=1.2, k_ratio=0.7, σ_allow=600MPa, FoS=1.5
  F_max = 0.8×9.81×3/4 = 5.886 N, M_root = 5.886×0.0762 = 0.4485 N·m
  d_out = (32×0.4485×1.5 / (π×600e6×0.7599))^(1/3) = 2.47 mm
"""
import numpy as np

MATERIALS = {
    "CF tube/rod":              {"rho": 1600.0,  "sigma_allow_MPa": 600.0},
    "Aluminium 6061":           {"rho": 2700.0,  "sigma_allow_MPa": 276.0},
    "Steel mild":               {"rho": 7850.0,  "sigma_allow_MPa": 250.0},
    "Titanium Ti-6Al-4V":       {"rho": 4500.0,  "sigma_allow_MPa": 880.0},
    "3D Print - PLA":           {"rho": 1240.0,  "sigma_allow_MPa": 50.0},
    "3D Print - PETG":          {"rho": 1270.0,  "sigma_allow_MPa": 53.0},
    "3D Print - ABS":           {"rho": 1050.0,  "sigma_allow_MPa": 40.0},
    "3D Print - Nylon PA12":    {"rho": 1010.0,  "sigma_allow_MPa": 50.0},
    "3D Print - Onyx CF-Nylon": {"rho": 1400.0,  "sigma_allow_MPa": 320.0},
    "Custom":                   {"rho": None,    "sigma_allow_MPa": None},
}


# ── Loading ────────────────────────────────────────────────────────────────

def compute_F_max(MTOW_kg: float, a_TO_ms2: float, n_motors: int) -> float:
    """Max tip load per arm during takeoff [N].

    F_max = MTOW × g × (1 + a_TO/g) / n_motors   (Pollet 2024 Eq. 3.6b)
    """
    return MTOW_kg * 9.81 * (1.0 + a_TO_ms2 / 9.81) / n_motors


def compute_M_root(F_max_N: float, L_arm_m: float) -> float:
    """Root bending moment [N·m]. M_root = F_max × L_arm."""
    return F_max_N * L_arm_m


# ── Dimension solvers ──────────────────────────────────────────────────────

def solve_circular(M_root_Nm: float, sigma_allow_Pa: float,
                   FoS: float, k_ratio: float) -> dict:
    """Solve d_out for circular hollow tube from stress constraint.

    σ_root = 32 M / (π d_out³ (1-k⁴)) ≤ σ_allow/FoS
    → d_out = (32 M FoS / (π σ_allow (1−k⁴)))^(1/3)
    """
    factor = 1.0 - k_ratio ** 4
    d_out = (32.0 * M_root_Nm * FoS / (np.pi * sigma_allow_Pa * factor)) ** (1.0 / 3.0)
    d_in = k_ratio * d_out
    t_wall = (d_out - d_in) / 2.0
    I = np.pi / 64.0 * (d_out ** 4 - d_in ** 4)
    c = d_out / 2.0
    A = np.pi / 4.0 * (d_out ** 2 - d_in ** 2)
    sigma_root_Pa = (32.0 * M_root_Nm / (np.pi * d_out ** 3 * factor)) if d_out > 0 else 0.0
    FoS_actual = sigma_allow_Pa / sigma_root_Pa if sigma_root_Pa > 0 else float("inf")
    return {
        "type": "circular",
        "d_out_m": d_out, "d_in_m": d_in, "t_wall_m": t_wall,
        "I_m4": I, "c_m": c, "A_m2": A,
        "sigma_root_Pa": sigma_root_Pa, "FoS_actual": FoS_actual,
        "passed": FoS_actual >= FoS,
    }


def solve_square(M_root_Nm: float, sigma_allow_Pa: float,
                 FoS: float, k_ratio: float) -> dict:
    """Solve b_out for square hollow tube from stress constraint.

    σ_root = 6 M / (b_out³ (1−k⁴)) ≤ σ_allow/FoS
    → b_out = (6 M FoS / (σ_allow (1−k⁴)))^(1/3)
    """
    factor = 1.0 - k_ratio ** 4
    b_out = (6.0 * M_root_Nm * FoS / (sigma_allow_Pa * factor)) ** (1.0 / 3.0)
    b_in = k_ratio * b_out
    t_wall = (b_out - b_in) / 2.0
    I = (b_out ** 4 - b_in ** 4) / 12.0
    c = b_out / 2.0
    A = b_out ** 2 - b_in ** 2
    sigma_root_Pa = (6.0 * M_root_Nm / (b_out ** 3 * factor)) if b_out > 0 else 0.0
    FoS_actual = sigma_allow_Pa / sigma_root_Pa if sigma_root_Pa > 0 else float("inf")
    return {
        "type": "square",
        "b_out_m": b_out, "b_in_m": b_in, "t_wall_m": t_wall,
        "I_m4": I, "c_m": c, "A_m2": A,
        "sigma_root_Pa": sigma_root_Pa, "FoS_actual": FoS_actual,
        "passed": FoS_actual >= FoS,
    }


def solve_plate(M_root_Nm: float, sigma_allow_Pa: float,
                FoS: float, b_m: float) -> dict:
    """Solve h for flat plate from stress constraint (b given by user).

    σ_root = 6 M / (b h²) ≤ σ_allow/FoS
    → h = sqrt(6 M FoS / (σ_allow b))
    """
    h = np.sqrt(6.0 * M_root_Nm * FoS / (sigma_allow_Pa * b_m)) if b_m > 0 else 0.0
    I = b_m * h ** 3 / 12.0 if h > 0 else 0.0
    c = h / 2.0
    A = b_m * h
    sigma_root_Pa = (6.0 * M_root_Nm / (b_m * h ** 2)) if h > 0 else 0.0
    FoS_actual = sigma_allow_Pa / sigma_root_Pa if sigma_root_Pa > 0 else float("inf")
    return {
        "type": "plate",
        "h_m": h, "b_m": b_m, "t_wall_m": h,
        "I_m4": I, "c_m": c, "A_m2": A,
        "sigma_root_Pa": sigma_root_Pa, "FoS_actual": FoS_actual,
        "passed": FoS_actual >= FoS,
    }


def solve_arm(cs_type: str, M_root_Nm: float, sigma_allow_Pa: float,
              FoS: float, k_ratio: float, b_plate_m: float = 0.012) -> dict:
    """Dispatch to correct solver. Returns dims dict."""
    if cs_type == "Circular Hollow Tube":
        return solve_circular(M_root_Nm, sigma_allow_Pa, FoS, k_ratio)
    elif cs_type == "Square Hollow Tube":
        return solve_square(M_root_Nm, sigma_allow_Pa, FoS, k_ratio)
    else:
        return solve_plate(M_root_Nm, sigma_allow_Pa, FoS, b_plate_m)


# ── Mass & clearance ───────────────────────────────────────────────────────

def arm_mass_one(rho_kg_m3: float, A_m2: float, L_arm_m: float) -> float:
    """Single arm mass [kg]."""
    return rho_kg_m3 * A_m2 * L_arm_m


def prop_clearance(L_arm_m: float, D_prop_m: float,
                   n_motors: int, c_margin_m: float = 0.010) -> tuple:
    """Adjacent propeller clearance.

    d_between = 2 × L_arm × sin(π / n_motors)
    Returns (d_between_m, passes).
    """
    d_between = 2.0 * L_arm_m * np.sin(np.pi / n_motors)
    passes = d_between > (D_prop_m + c_margin_m)
    return d_between, passes


# ── Full structural sizing for one MTOW iterate ────────────────────────────

def compute_structural_sizing(MTOW_kg: float, a_TO_ms2: float, n_motors: int,
                               k_arm: float, D_prop_m: float,
                               cs_type: str, k_ratio: float, b_plate_m: float,
                               rho: float, sigma_allow_Pa: float, FoS: float,
                               M_struct_sizing_kg: float) -> dict:
    """Solve arm dimensions and return full structural sizing dict.

    M_struct = M_arms + M_body
    M_body   = max(0, M_struct_sizing − M_arms)
    """
    L_arm   = k_arm * D_prop_m / 2.0
    F_max   = compute_F_max(MTOW_kg, a_TO_ms2, n_motors)
    M_root  = compute_M_root(F_max, L_arm)
    dims    = solve_arm(cs_type, M_root, sigma_allow_Pa, FoS, k_ratio, b_plate_m)
    A       = dims["A_m2"]
    m_one   = arm_mass_one(rho, A, L_arm)
    M_arms  = n_motors * m_one
    M_body  = max(0.0, M_struct_sizing_kg - M_arms)
    M_struct = M_arms + M_body
    return {
        "L_arm_m":  L_arm,
        "F_max_N":  F_max,
        "M_root_Nm": M_root,
        "dims":     dims,
        "m_one_arm_kg": m_one,
        "M_arms_kg":    M_arms,
        "M_body_kg":    M_body,
        "M_struct_kg":  M_struct,
    }
