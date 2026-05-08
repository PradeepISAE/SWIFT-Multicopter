"""
Fixed-point mass convergence — SWIFT Resizing Phase.

Key difference from Sizing Phase: structural dimensions are RE-SOLVED at
every iteration as MTOW changes, giving M_struct(MTOW).

Governing loop (Pollet 2024 §3.4):
  MTOW_0 = m_pay / MF_pay

  Each iteration k:
    Solve arm dims → M_struct(k) = M_arms(k) + M_body
    P_motors(k)  = MTOW(k)×1000/n_motors / PL_50pct
    E_total(k)   = segment energies  +  E_cruise
    M_batt(k)    = E_total / (SED×DoD×η)
    MTOW(k+1)    = m_pay + M_avi + M_prop + M_struct(k) + M_batt(k)

  Converge when |MTOW(k+1) − MTOW(k)| < 1e-4 kg, max 50 iters.
"""
from .structure_resizing import compute_structural_sizing
from .mission_resizing import compute_mission_energy
from .battery_resizing import battery_from_energy


def run_resizing(params: dict) -> dict:
    """Execute fixed-point resizing loop.

    Required params keys:
      m_pay, MF_pay,
      M_avi_fixed, M_prop_fixed  [kg — real hardware],
      n_motors, PL_50pct_gW [g/W], P_avi_W [W], P_pay_W [W],
      segments (dict), E_cruise_Wh [Wh],
      SED [Wh/kg], DoD, eta_elec, V_batt [V],
      a_TO_ms2, k_arm, D_prop_m,
      cs_type, k_ratio, b_plate_m [m],
      rho [kg/m³], sigma_allow_Pa [Pa], FoS,
      M_struct_sizing_kg [kg],
    """
    m_pay          = params["m_pay"]
    MF_pay         = params["MF_pay"]
    M_avi          = params["M_avi_fixed"]
    M_prop         = params["M_prop_fixed"]
    n_motors       = int(params["n_motors"])
    PL             = params["PL_50pct_gW"]
    P_avi          = params["P_avi_W"]
    P_pay          = params["P_pay_W"]
    segments       = params["segments"]
    E_cruise       = params.get("E_cruise_Wh", 0.0)
    SED            = params["SED"]
    DoD            = params["DoD"]
    eta            = params["eta_elec"]
    V_batt         = params["V_batt"]
    a_TO           = params["a_TO_ms2"]
    k_arm          = params["k_arm"]
    D_prop_m       = params["D_prop_m"]
    cs_type        = params["cs_type"]
    k_ratio        = params["k_ratio"]
    b_plate_m      = params.get("b_plate_m", 0.012)
    rho            = params["rho"]
    sigma_allow_Pa = params["sigma_allow_Pa"]
    FoS            = params["FoS"]
    M_struct_sz    = params["M_struct_sizing_kg"]

    MTOW      = m_pay / MF_pay
    history   = [MTOW]
    converged = False

    struct_out  = {}
    mission_out = {}
    batt_out    = {}

    for _ in range(50):
        # ── Structure (re-solved every iteration) ─────────────────────────
        struct_out = compute_structural_sizing(
            MTOW, a_TO, n_motors, k_arm, D_prop_m,
            cs_type, k_ratio, b_plate_m, rho, sigma_allow_Pa, FoS, M_struct_sz,
        )
        M_struct = struct_out["M_struct_kg"]

        # ── Mission energy ────────────────────────────────────────────────
        mission_out = compute_mission_energy(
            MTOW, PL, n_motors, P_avi, P_pay, segments, E_cruise,
        )
        E_total = mission_out["E_total_Wh"]

        # ── Battery ───────────────────────────────────────────────────────
        batt_out = battery_from_energy(E_total, SED, DoD, eta, V_batt)
        M_batt   = batt_out["M_batt_kg"]

        MTOW_new = m_pay + M_avi + M_prop + M_struct + M_batt
        history.append(MTOW_new)

        if abs(MTOW_new - MTOW) < 1e-4:
            MTOW = MTOW_new
            converged = True
            break
        MTOW = MTOW_new

    if not converged:
        MTOW = history[-1]

    T_motor_g = MTOW * 1000.0 / n_motors
    P_motor_W = T_motor_g / PL if PL > 0 else 0.0

    return {
        "M_TO":          MTOW,
        "history":       history,
        "n_iterations":  len(history) - 1,
        "converged":     converged,
        # Mass breakdown
        "m_pay":         m_pay,
        "m_struct":      struct_out.get("M_struct_kg",  0.0),
        "M_arms":        struct_out.get("M_arms_kg",    0.0),
        "M_body":        struct_out.get("M_body_kg",    0.0),
        "m_avi":         M_avi,
        "M_prop":        M_prop,
        "M_batt":        batt_out.get("M_batt_kg",      0.0),
        # Structure details
        "struct_dims":   struct_out.get("dims",          {}),
        "L_arm_m":       struct_out.get("L_arm_m",       0.0),
        "M_root_Nm":     struct_out.get("M_root_Nm",     0.0),
        # Energy
        "E_total_Wh":    mission_out.get("E_total_Wh",   0.0),
        "E_segments":    mission_out.get("E_segments",    {}),
        "P_motors_W":    mission_out.get("P_motors_W",    0.0),
        # Battery sizing
        "C_req_mAh":     batt_out.get("C_req_mAh",       0.0),
        "C_target_mAh":  batt_out.get("C_target_mAh",    0.0),
        # Per-motor reference
        "T_motor_g":     T_motor_g,
        "P_motor_W":     P_motor_W,
        "PL":            PL,
    }
