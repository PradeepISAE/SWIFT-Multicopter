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


# ── Standard CF tube catalogue & physical-wall inverse solver ─────────────

STANDARD_CF_SIZES_MM = [
    (6.0, 0.5),  (6.0, 1.0),
    (8.0, 0.5),  (8.0, 1.0),  (8.0, 1.5),
    (10.0, 1.0), (10.0, 1.5),
    (12.0, 1.0), (12.0, 1.5), (12.0, 2.0),
    (14.0, 1.5), (14.0, 2.0),
    (16.0, 1.5), (16.0, 2.0),
    (20.0, 2.0),
]


def nearest_standard_cf_tube(d_out_mm: float, t_wall_mm: float) -> tuple:
    """Return (od_mm, wall_mm) of the smallest standard CF tube that covers d_out_mm."""
    candidates = [(d, t) for d, t in STANDARD_CF_SIZES_MM if d >= d_out_mm]
    if not candidates:
        return STANDARD_CF_SIZES_MM[-1]
    return min(candidates, key=lambda x: x[0])


def solve_outer_from_stress(
    profile: str, M_root_Nm: float, sigma_allow_mpa: float,
    fos: float, t_wall_m: float, b_plate_m: float = 0.010,
    tol: float = 1e-9, max_iter: int = 100,
) -> float:
    """Solve outer dimension from bending stress constraint with fixed wall thickness.

    Circular/square: iterative (k = (d-2t)/d depends on d).
    Flat plate: explicit h = sqrt(6M*FoS / (sigma*b)).
    Returns outer dimension [m].
    """
    import math
    sigma_design_pa = (sigma_allow_mpa * 1e6) / max(fos, 1e-12)
    M = max(M_root_Nm, 1e-12)
    prof = profile.lower().strip()

    if prof == "flat_plate":
        b = max(b_plate_m, 1e-6)
        return math.sqrt(6.0 * M / (sigma_design_pa * b))

    if prof == "circular":
        outer = (32.0 * M / (math.pi * sigma_design_pa)) ** (1.0 / 3.0)
        for _ in range(max_iter):
            t = min(t_wall_m, outer / 2.0 - 1e-9)
            k = (outer - 2.0 * t) / max(outer, 1e-12)
            factor = max(1.0 - k ** 4, 1e-12)
            outer_new = (32.0 * M / (math.pi * sigma_design_pa * factor)) ** (1.0 / 3.0)
            if abs(outer_new - outer) < tol:
                return max(outer_new, 2.0 * t_wall_m + 1e-6)
            outer = outer_new
        return max(outer, 2.0 * t_wall_m + 1e-6)

    if prof == "square":
        outer = (6.0 * M / sigma_design_pa) ** (1.0 / 3.0)
        for _ in range(max_iter):
            t = min(t_wall_m, outer / 2.0 - 1e-9)
            k = (outer - 2.0 * t) / max(outer, 1e-12)
            factor = max(1.0 - k ** 4, 1e-12)
            outer_new = (6.0 * M / (sigma_design_pa * factor)) ** (1.0 / 3.0)
            if abs(outer_new - outer) < tol:
                return max(outer_new, 2.0 * t_wall_m + 1e-6)
            outer = outer_new
        return max(outer, 2.0 * t_wall_m + 1e-6)

    raise ValueError(f"Unknown profile: {profile!r}")


def arm_cross_section_area(profile: str, outer_m: float, t_wall_m: float,
                           b_plate_m: float = 0.010) -> float:
    """Cross-sectional area [m²] for the given profile.

    Circular/square: annular area (outer² − inner²).
    Flat plate: b × h  where outer_m is the solved height h.
    """
    import math
    prof  = profile.lower().strip()
    outer = max(outer_m, 1e-9)
    t     = min(t_wall_m, outer / 2.0 - 1e-9)
    if prof == "circular":
        inner = outer - 2.0 * t
        return (math.pi / 4.0) * (outer ** 2 - inner ** 2)
    if prof == "square":
        inner = outer - 2.0 * t
        return outer ** 2 - inner ** 2
    if prof == "flat_plate":
        return max(b_plate_m, 1e-6) * max(outer_m, 1e-9)
    raise ValueError(f"Unknown profile: {profile!r}")


def compute_stress_mpa(profile: str, M_root_Nm: float, outer_m: float,
                       t_wall_m: float, b_plate_m: float = 0.010) -> float:
    """Bending stress [MPa] at the arm root for the given profile.

    Circular: 32M / (π d³ (1−k⁴)).  Square: 6M / (b³ (1−k⁴)).
    Flat plate: 6M / (b h²)  where outer_m = h.
    """
    import math
    prof  = profile.lower().strip()
    M     = max(M_root_Nm, 1e-12)
    outer = max(outer_m, 1e-9)
    t     = min(t_wall_m, outer / 2.0 - 1e-9)
    if prof == "circular":
        k = (outer - 2.0 * t) / outer
        return (32.0 * M / (math.pi * outer ** 3 * max(1.0 - k ** 4, 1e-12))) / 1e6
    if prof == "square":
        k = (outer - 2.0 * t) / outer
        return (6.0 * M / (outer ** 3 * max(1.0 - k ** 4, 1e-12))) / 1e6
    if prof == "flat_plate":
        return (6.0 * M / (max(b_plate_m, 1e-6) * max(outer_m, 1e-9) ** 2)) / 1e6
    raise ValueError(f"Unknown profile: {profile!r}")
