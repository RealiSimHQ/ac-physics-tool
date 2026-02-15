"""
Physics Engine — Takes car specs + selected parts → generates AC physics values.
Uses real formulas from Arch's physics pipeline reference.
"""
import math
from car_database import get_car
from parts_database import (
    COILOVERS, ANGLE_KITS, WHEEL_SETUPS, BRAKE_KITS, DIFF_TYPES, TIRE_COMPOUNDS
)


def calculate_tire_radius(width_m, aspect_ratio, rim_dia_inches):
    """Tire outer radius in meters."""
    sidewall = width_m * (aspect_ratio / 100.0)
    rim_r = (rim_dia_inches * 0.0254) / 2.0
    return sidewall + rim_r


def calculate_natural_freq(wheel_rate, sprung_mass_corner):
    """Natural frequency in Hz."""
    if sprung_mass_corner <= 0:
        return 0
    return (1.0 / (2.0 * math.pi)) * math.sqrt(wheel_rate / sprung_mass_corner)


def calculate_critical_damping(spring_rate, sprung_mass_corner):
    """Critical damping coefficient Cc = 2√(k·m)"""
    return 2.0 * math.sqrt(spring_rate * sprung_mass_corner)


def calculate_damping(spring_rate, sprung_mass_corner, quality="basic"):
    """Generate damping values based on spring rate and damper quality."""
    cc = calculate_critical_damping(spring_rate, sprung_mass_corner)
    # Damping ratios depend on quality
    ratios = {
        "basic":      {"bump": 0.22, "rebound": 0.35, "fast_mult": 0.45},
        "adjustable": {"bump": 0.25, "rebound": 0.40, "fast_mult": 0.50},
        "advanced":   {"bump": 0.28, "rebound": 0.45, "fast_mult": 0.55},
    }
    r = ratios.get(quality, ratios["adjustable"])
    return {
        "bump": round(cc * r["bump"]),
        "fast_bump": round(cc * r["bump"] * r["fast_mult"]),
        "rebound": round(cc * r["rebound"]),
        "fast_rebound": round(cc * r["rebound"] * r["fast_mult"]),
    }


def calculate_hub_mass(car, wheel_setup, brake_kit, angle_kit):
    """Calculate front/rear unsprung mass per corner."""
    ws = wheel_setup
    if "wheel_mass_kg" in ws:
        wheel_mass_f = ws["wheel_mass_kg"]
        wheel_mass_r = ws["wheel_mass_kg"]
    else:
        wheel_mass_f = 8.0 + (car["rim_dia_f"] - 15) * 1.2
        wheel_mass_r = 8.0 + (car["rim_dia_r"] - 15) * 1.2

    # Tire mass estimate from width
    tw_f = ws.get("tire_width", car["tire_width_f"])
    tw_r = ws.get("tire_width", car["tire_width_r"])
    tire_mass_f = 7.0 + tw_f * 25
    tire_mass_r = 7.0 + tw_r * 25

    # Base hub mass from car (includes knuckle, bearing, etc.)
    base_f = car["hub_mass_f"]
    base_r = car["hub_mass_r"]

    # Brake kit mass delta
    brake_add_f = brake_kit.get("mass_add_f_kg", 0)

    # Angle kit mass delta
    angle_add = angle_kit.get("hub_mass_add_kg", 0)

    hub_f = base_f + brake_add_f + angle_add
    hub_r = base_r

    return hub_f, hub_r


def generate_physics(car_id, parts_selection):
    """
    Main entry point. Generate complete physics modifications.
    
    car_id: key into CAR_DATABASE
    parts_selection: dict with keys 'coilovers', 'angle_kit', 'wheels_f', 'wheels_r', 'brakes', 'diff', 'tire_compound'
    
    Returns: dict with 'summary', 'changes', 'comparison' for before/after display
    """
    car = get_car(car_id)
    if not car:
        return {"error": f"Unknown car: {car_id}"}

    # Resolve parts
    coilover = COILOVERS.get(parts_selection.get("coilovers", "stock"), COILOVERS["stock"])
    angle_kit = ANGLE_KITS.get(parts_selection.get("angle_kit", "stock"), ANGLE_KITS["stock"])
    wheels_f = WHEEL_SETUPS.get(parts_selection.get("wheels_f", "stock"), WHEEL_SETUPS["stock"])
    wheels_r = WHEEL_SETUPS.get(parts_selection.get("wheels_r", "stock"), WHEEL_SETUPS["stock"])
    brake_kit = BRAKE_KITS.get(parts_selection.get("brakes", "stock"), BRAKE_KITS["stock"])
    diff = DIFF_TYPES.get(parts_selection.get("diff", "stock"), DIFF_TYPES["stock"])
    compound_key = parts_selection.get("tire_compound", None)

    # ── Tire/wheel specs ──────────────────────────────────────
    tire_width_f = wheels_f.get("tire_width", car["tire_width_f"])
    tire_width_r = wheels_r.get("tire_width", car["tire_width_r"])
    tire_aspect_f = wheels_f.get("tire_aspect", car["tire_aspect_f"])
    tire_aspect_r = wheels_r.get("tire_aspect", car["tire_aspect_r"])
    rim_dia_f = wheels_f.get("rim_dia", car["rim_dia_f"])
    rim_dia_r = wheels_r.get("rim_dia", car["rim_dia_r"])

    tire_radius_f = calculate_tire_radius(tire_width_f, tire_aspect_f, rim_dia_f)
    tire_radius_r = calculate_tire_radius(tire_width_r, tire_aspect_r, rim_dia_r)

    # Tire compound
    if compound_key and compound_key in TIRE_COMPOUNDS:
        compound = TIRE_COMPOUNDS[compound_key]
    elif "tire_compound" in wheels_f:
        compound = TIRE_COMPOUNDS.get(wheels_f["tire_compound"], TIRE_COMPOUNDS["street"])
    else:
        compound = TIRE_COMPOUNDS["street"]

    # ── Hub / unsprung mass ───────────────────────────────────
    hub_mass_f, hub_mass_r = calculate_hub_mass(car, wheels_f, brake_kit, angle_kit)

    # ── Total mass (car + driver ~75kg) ───────────────────────
    total_mass = car["mass_kg"]
    sprung_total = total_mass - (hub_mass_f * 2 + hub_mass_r * 2)
    wdf = car["weight_dist_f"]
    sprung_f_corner = sprung_total * wdf / 2.0
    sprung_r_corner = sprung_total * (1 - wdf) / 2.0

    # ── Spring rates ──────────────────────────────────────────
    if "spring_rate_f_nm" in coilover:
        spring_f = coilover["spring_rate_f_nm"]
        spring_r = coilover["spring_rate_r_nm"]
    else:
        spring_f = car["spring_rate_f"] * coilover.get("spring_rate_f_mult", 1.0)
        spring_r = car["spring_rate_r"] * coilover.get("spring_rate_r_mult", 1.0)

    # ── Natural frequencies ───────────────────────────────────
    freq_f = calculate_natural_freq(spring_f, sprung_f_corner)
    freq_r = calculate_natural_freq(spring_r, sprung_r_corner)

    # ── Damping ───────────────────────────────────────────────
    damping_quality = coilover.get("damping_quality", "basic")
    damp_f = calculate_damping(spring_f, sprung_f_corner, damping_quality)
    damp_r = calculate_damping(spring_r, sprung_r_corner, damping_quality)

    # ── ARB rates ─────────────────────────────────────────────
    # Scale ARB with spring rate ratio (stiffer springs → proportionally stiffer ARB)
    spring_ratio_f = spring_f / max(car["spring_rate_f"], 1)
    spring_ratio_r = spring_r / max(car["spring_rate_r"], 1)
    arb_f = int(car["arb_f"] * spring_ratio_f)
    arb_r = int(car["arb_r"] * spring_ratio_r)

    # ── Steering / angle ──────────────────────────────────────
    if angle_kit.get("max_angle_deg", 0) > 0:
        max_angle = angle_kit["max_angle_deg"]
        steer_lock = max_angle * car["steer_ratio"]
    else:
        max_angle = car["stock_max_angle"]
        steer_lock = car["steer_lock"]

    # ── Brakes ────────────────────────────────────────────────
    if "torque_mult" in brake_kit:
        brake_torque = int(car["brake_torque"] * brake_kit["torque_mult"])
        brake_bias = brake_kit["bias"]
    else:
        brake_torque = car["brake_torque"]
        brake_bias = car["brake_bias"]

    # ── Differential ──────────────────────────────────────────
    diff_power = diff.get("diff_power", car["diff_power"])
    diff_coast = diff.get("diff_coast", car["diff_coast"])
    diff_preload = diff.get("diff_preload", car["diff_preload"])

    # ── Preload force ─────────────────────────────────────────
    corner_weight_f = sprung_f_corner * 9.81
    corner_weight_r = sprung_r_corner * 9.81

    # ── Ride height (BASEY approximation) ─────────────────────
    drop_mm = coilover.get("ride_height_drop_mm", 0)
    # Stock tire radius vs new
    stock_radius_f = calculate_tire_radius(car["tire_width_f"], car["tire_aspect_f"], car["rim_dia_f"])
    stock_radius_r = calculate_tire_radius(car["tire_width_r"], car["tire_aspect_r"], car["rim_dia_r"])
    tire_radius_delta_f = tire_radius_f - stock_radius_f
    tire_radius_delta_r = tire_radius_r - stock_radius_r

    # ── Build comparison data ─────────────────────────────────
    stock_sprung_total = total_mass - (car["hub_mass_f"] * 2 + car["hub_mass_r"] * 2)
    stock_freq_f = calculate_natural_freq(car["spring_rate_f"], stock_sprung_total * wdf / 2.0)
    stock_freq_r = calculate_natural_freq(car["spring_rate_r"], stock_sprung_total * (1 - wdf) / 2.0)

    comparison = [
        {"param": "Spring Rate (F)", "stock": f"{car['spring_rate_f']:,} N/m", "modified": f"{int(spring_f):,} N/m", "category": "suspension"},
        {"param": "Spring Rate (R)", "stock": f"{car['spring_rate_r']:,} N/m", "modified": f"{int(spring_r):,} N/m", "category": "suspension"},
        {"param": "Natural Freq (F)", "stock": f"{stock_freq_f:.2f} Hz", "modified": f"{freq_f:.2f} Hz", "category": "suspension"},
        {"param": "Natural Freq (R)", "stock": f"{stock_freq_r:.2f} Hz", "modified": f"{freq_r:.2f} Hz", "category": "suspension"},
        {"param": "ARB (F)", "stock": f"{car['arb_f']:,} N/m", "modified": f"{arb_f:,} N/m", "category": "suspension"},
        {"param": "ARB (R)", "stock": f"{car['arb_r']:,} N/m", "modified": f"{arb_r:,} N/m", "category": "suspension"},
        {"param": "Hub Mass (F)", "stock": f"{car['hub_mass_f']:.1f} kg", "modified": f"{hub_mass_f:.1f} kg", "category": "unsprung"},
        {"param": "Hub Mass (R)", "stock": f"{car['hub_mass_r']:.1f} kg", "modified": f"{hub_mass_r:.1f} kg", "category": "unsprung"},
        {"param": "Max Steering Angle", "stock": f"{car['stock_max_angle']}°", "modified": f"{max_angle}°", "category": "steering"},
        {"param": "Steer Lock", "stock": f"{car['steer_lock']}°", "modified": f"{steer_lock:.0f}°", "category": "steering"},
        {"param": "Tire Width (F)", "stock": f"{car['tire_width_f']*1000:.0f}mm", "modified": f"{tire_width_f*1000:.0f}mm", "category": "tires"},
        {"param": "Tire Width (R)", "stock": f"{car['tire_width_r']*1000:.0f}mm", "modified": f"{tire_width_r*1000:.0f}mm", "category": "tires"},
        {"param": "Tire Radius (F)", "stock": f"{stock_radius_f:.4f}m", "modified": f"{tire_radius_f:.4f}m", "category": "tires"},
        {"param": "Tire Radius (R)", "stock": f"{stock_radius_r:.4f}m", "modified": f"{tire_radius_r:.4f}m", "category": "tires"},
        {"param": "Grip Level", "stock": f"{TIRE_COMPOUNDS['street']['grip_mult']:.2f}", "modified": f"{compound['grip_mult']:.2f}", "category": "tires"},
        {"param": "Brake Torque", "stock": f"{car['brake_torque']} Nm", "modified": f"{brake_torque} Nm", "category": "brakes"},
        {"param": "Brake Bias", "stock": f"{car['brake_bias']*100:.0f}% F", "modified": f"{brake_bias*100:.0f}% F", "category": "brakes"},
        {"param": "Diff Power Lock", "stock": f"{car['diff_power']*100:.0f}%", "modified": f"{diff_power*100:.0f}%", "category": "diff"},
        {"param": "Diff Coast Lock", "stock": f"{car['diff_coast']*100:.0f}%", "modified": f"{diff_coast*100:.0f}%", "category": "diff"},
        {"param": "Diff Preload", "stock": f"{car['diff_preload']} Nm", "modified": f"{diff_preload} Nm", "category": "diff"},
    ]

    # ── Build AC INI changes ──────────────────────────────────
    changes = {
        "car.ini": {
            "CONTROLS": {
                "STEER_LOCK": int(steer_lock),
            },
        },
        "suspensions.ini": {
            "FRONT": {
                "HUB_MASS": round(hub_mass_f, 4),
            },
            "REAR": {
                "HUB_MASS": round(hub_mass_r, 4),
            },
            "ARB": {
                "FRONT": arb_f,
                "REAR": arb_r,
            },
            "FRONT_SPRING": {
                "RATE": int(spring_f),
            },
            "REAR_SPRING": {
                "RATE": int(spring_r),
            },
            "FRONT_DAMPER": {
                "DAMP_BUMP": damp_f["bump"],
                "DAMP_FAST_BUMP": damp_f["fast_bump"],
                "DAMP_REBOUND": damp_f["rebound"],
                "DAMP_FAST_REBOUND": damp_f["fast_rebound"],
                "DAMP_FAST_BUMPTHRESHOLD": 0.15,
                "DAMP_FAST_REBOUNDTHRESHOLD": 0.15,
            },
            "REAR_DAMPER": {
                "DAMP_BUMP": damp_r["bump"],
                "DAMP_FAST_BUMP": damp_r["fast_bump"],
                "DAMP_REBOUND": damp_r["rebound"],
                "DAMP_FAST_REBOUND": damp_r["fast_rebound"],
                "DAMP_FAST_BUMPTHRESHOLD": 0.15,
                "DAMP_FAST_REBOUNDTHRESHOLD": 0.15,
            },
        },
        "tyres.ini": {
            "FRONT": {
                "WIDTH": tire_width_f,
                "RADIUS": round(tire_radius_f, 4),
                "FRICTION_LIMIT_GRIP": compound["grip_mult"],
                "DX_REF": compound["dx_ref"],
                "DY_REF": compound["dy_ref"],
            },
            "REAR": {
                "WIDTH": tire_width_r,
                "RADIUS": round(tire_radius_r, 4),
                "FRICTION_LIMIT_GRIP": compound["grip_mult"],
                "DX_REF": compound["dx_ref"],
                "DY_REF": compound["dy_ref"],
            },
        },
        "brakes.ini": {
            "DATA": {
                "MAX_TORQUE": brake_torque,
                "FRONT_SHARE": brake_bias,
                "HANDBRAKE_TORQUE": int(brake_torque * 0.25),
            },
        },
        "drivetrain.ini": {
            "DIFFERENTIAL": {
                "POWER": diff_power,
                "COAST": diff_coast,
                "PRELOAD": diff_preload,
            },
        },
    }

    summary = {
        "car_name": f"{car['make']} {car['model']}",
        "chassis": car["chassis"],
        "year": car["year"],
        "engine": car["engine"],
        "total_mass": total_mass,
        "sprung_f_corner": round(sprung_f_corner, 1),
        "sprung_r_corner": round(sprung_r_corner, 1),
        "natural_freq_f": round(freq_f, 2),
        "natural_freq_r": round(freq_r, 2),
        "hub_mass_f": round(hub_mass_f, 1),
        "hub_mass_r": round(hub_mass_r, 1),
        "max_angle": max_angle,
        "tire_compound": compound.get("name", "Unknown"),
        "parts": {
            "coilovers": coilover["name"],
            "angle_kit": angle_kit["name"],
            "wheels_f": wheels_f.get("name", "Stock"),
            "wheels_r": wheels_r.get("name", "Stock"),
            "brakes": brake_kit.get("name", "Stock"),
            "diff": diff.get("name", "Stock"),
        },
    }

    return {
        "summary": summary,
        "changes": changes,
        "comparison": comparison,
    }
