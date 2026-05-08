"""
SWIFT Configuration I/O — save, load, and export session state.
"""
import json
import os
from datetime import datetime

SWIFT_VERSION = "1.0"


def build_config(project_name: str, session_state: dict) -> dict:
    """Serialise non-private, JSON-safe session state keys into a config dict."""
    def _is_serialisable(v):
        try:
            json.dumps(v)
            return True
        except (TypeError, ValueError):
            return False

    safe_state = {
        k: v for k, v in session_state.items()
        if not k.startswith("_") and _is_serialisable(v)
    }
    return {
        "swift_version": SWIFT_VERSION,
        "saved_at":      datetime.now().isoformat(),
        "project_name":  project_name,
        "session_state": safe_state,
    }


def save_config(project_name: str, session_state: dict, save_dir: str = ".") -> str:
    """Write config JSON to disk and return the filepath."""
    config = build_config(project_name, session_state)
    os.makedirs(save_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in project_name)
    filepath = os.path.join(save_dir, f"SWIFT_{safe_name}_{timestamp}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    return filepath


def load_config(filepath_or_bytes) -> dict:
    """Load a config dict from a file path, bytes, or string."""
    if isinstance(filepath_or_bytes, (str, os.PathLike)):
        with open(filepath_or_bytes, "r", encoding="utf-8") as f:
            return json.load(f)
    raw = filepath_or_bytes
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8")
    return json.loads(raw)


def restore_session(config: dict, session_state) -> str:
    """Populate session_state from a loaded config. Returns project name."""
    for k, v in config.get("session_state", {}).items():
        session_state[k] = v
    return config.get("project_name", "Unnamed")


def export_summary_csv_string(config: dict) -> str:
    """Return a CSV string comparing Sizing / Resizing / Optimised results."""
    import io
    import csv

    ss = config.get("session_state", {})

    def _fmt(v):
        if isinstance(v, float):
            return f"{v:.4g}"
        if v is None or v == "":
            return ""
        return str(v)

    # (label, sizing_key, resizing_key, opt_key, unit)
    rows_def = [
        ("MTOW",             "mtow_converged",            "resizing_MTOW_converged",    "resizing_opt_MTOW",         "kg"),
        ("Structural mass",  "m_struct_sizing",            "resizing_M_struct",          "",                          "kg"),
        ("Avionics mass",    "m_avi_sizing",               "resizing_M_avi",             "",                          "kg"),
        ("Propulsion mass",  "m_prop_sizing",              "resizing_M_prop",            "",                          "kg"),
        ("Battery mass",     "m_batt_sizing",              "",                           "resizing_opt_M_batt",       "kg"),
        ("Battery energy",   "e_battery_target",           "",                           "",                          "Wh"),
        ("P_motor target",   "p_motor_target",             "",                           "",                          "W"),
        ("T_motor target",   "t_motor_target",             "",                           "",                          "g"),
        ("k_arm",            "",                           "resizing_k_arm",             "resizing_opt_k_arm",        "-"),
        ("t_wall",           "",                           "resizing_t_wall_mm",         "resizing_opt_t_wall_mm",    "mm"),
        ("d_out",            "",                           "resizing_d_out_mm",          "resizing_opt_d_out_mm",     "mm"),
        ("d_in",             "",                           "resizing_d_in_mm",           "resizing_opt_d_in_mm",      "mm"),
        ("L_arm",            "",                           "resizing_L_arm",             "resizing_opt_L_arm_mm",     "mm"),
        ("FoS_actual",       "",                           "resizing_FoS_actual",        "resizing_opt_FoS_actual",   "-"),
        ("M_arms",           "",                           "resizing_M_arms",            "resizing_opt_M_arms",       "g"),
        ("Std CF tube OD",   "",                           "resizing_std_cf_od_mm",      "resizing_std_cf_od_mm",     "mm"),
        ("Std CF wall",      "",                           "resizing_std_cf_wall_mm",    "resizing_std_cf_wall_mm",   "mm"),
    ]

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Parameter", "Sizing", "Resizing", "Optimised", "Unit"])
    for label, sk, rk, ok, unit in rows_def:
        sv = _fmt(ss.get(sk, "")) if sk else ""
        rv = _fmt(ss.get(rk, "")) if rk else ""
        ov = _fmt(ss.get(ok, "")) if ok else ""
        writer.writerow([label, sv, rv, ov, unit])
    return buf.getvalue()
