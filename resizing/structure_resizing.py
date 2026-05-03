"""
Arm structural sizing for SWIFT Resizing Phase.

Cantilever beam model: tip load = T_max per motor (worst-case bending).
"""
import numpy as np

MATERIALS = {
    "CF tube":          {"rho": 1600.0, "sigma_allow_MPa": 600.0},
    "Aluminium 6061":   {"rho": 2700.0, "sigma_allow_MPa": 276.0},
    "Steel mild":       {"rho": 7850.0, "sigma_allow_MPa": 250.0},
    "Titanium":         {"rho": 4500.0, "sigma_allow_MPa": 880.0},
    "3D PLA":           {"rho": 1240.0, "sigma_allow_MPa": 50.0},
    "3D PETG":          {"rho": 1270.0, "sigma_allow_MPa": 53.0},
    "3D ABS":           {"rho": 1050.0, "sigma_allow_MPa": 40.0},
    "3D Nylon PA12":    {"rho": 1010.0, "sigma_allow_MPa": 50.0},
    "3D Onyx CF-Nylon": {"rho": 1400.0, "sigma_allow_MPa": 320.0},
    "Custom":           {"rho": None,   "sigma_allow_MPa": None},
}


def section_properties(cs_type: str, dims_m: dict) -> tuple:
    """Return (I [m⁴], c [m], A [m²]) for the given cross-section.

    dims_m keys:
      Circular tube: d_outer, t_wall
      Square tube:   b_outer, t_wall
      Flat plate:    b, h
    """
    if cs_type == "Circular tube":
        d_o = dims_m["d_outer"]
        d_i = max(0.0, d_o - 2.0 * dims_m["t_wall"])
        I = np.pi / 64.0 * (d_o**4 - d_i**4)
        c = d_o / 2.0
        A = np.pi / 4.0 * (d_o**2 - d_i**2)

    elif cs_type == "Square tube":
        b_o = dims_m["b_outer"]
        b_i = max(0.0, b_o - 2.0 * dims_m["t_wall"])
        I = (b_o**4 - b_i**4) / 12.0
        c = b_o / 2.0
        A = b_o**2 - b_i**2

    elif cs_type == "Flat plate":
        b, h = dims_m["b"], dims_m["h"]
        I = b * h**3 / 12.0
        c = h / 2.0
        A = b * h

    else:
        raise ValueError(f"Unknown cross-section type: {cs_type}")

    return I, c, A


def stress_check(T_max_N: float, L_arm_m: float,
                 I_m4: float, c_m: float,
                 sigma_allow_MPa: float, FoS_req: float) -> tuple:
    """Cantilever tip-load bending stress check.

    Returns (sigma_root_MPa, FoS_actual, passed).
    """
    M_bend = T_max_N * L_arm_m
    if I_m4 > 0 and c_m > 0:
        sigma_Pa = M_bend * c_m / I_m4
    else:
        return float("inf"), 0.0, False

    sigma_MPa = sigma_Pa / 1e6
    FoS_actual = sigma_allow_MPa / sigma_MPa if sigma_MPa > 0 else float("inf")
    return sigma_MPa, FoS_actual, FoS_actual >= FoS_req


def arm_mass_one(rho_kg_m3: float, A_m2: float, L_arm_m: float) -> float:
    """Single arm mass [kg]."""
    return rho_kg_m3 * A_m2 * L_arm_m


def prop_clearance(L_arm_m: float, D_prop_m: float,
                   n_motors: int, c_margin_m: float = 0.010) -> tuple:
    """Adjacent propeller clearance check.

    d_between = 2 × L_arm × sin(π / n_motors)
    Returns (d_between_m, passes).
    """
    d_between = 2.0 * L_arm_m * np.sin(np.pi / n_motors)
    passes = d_between > (D_prop_m + c_margin_m)
    return d_between, passes
