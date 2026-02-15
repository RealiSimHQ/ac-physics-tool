"""AC Physics Modifier Engine — takes parsed physics data + class preset → outputs corrected values."""
import math

# Class presets based on Ryan's X10DD tier system + real-world targets
CLASS_PRESETS = {
    "factory": {
        "label": "Factory",
        "hp_range": (100, 300),
        "max_angle": 38,
        "tire_type": "street",
        "tire_width_f": 0.205,
        "tire_width_r": 0.225,
        "spring_rate_f": 25000,   # N/m — stock comfort
        "spring_rate_r": 22000,
        "arb_rate_f": 15000,
        "arb_rate_r": 10000,
        "brake_torque": 1800,
        "brake_bias": 0.62,
        "diff_power": 0.0,
        "diff_coast": 0.0,
        "diff_preload": 0,
    },
    "grassroots": {
        "label": "Grassroots",
        "hp_range": (180, 350),
        "max_angle": 55,
        "tire_type": "semi_slick",
        "tire_width_f": 0.215,
        "tire_width_r": 0.235,
        "spring_rate_f": 35000,
        "spring_rate_r": 30000,
        "arb_rate_f": 20000,
        "arb_rate_r": 12000,
        "brake_torque": 2200,
        "brake_bias": 0.63,
        "diff_power": 0.3,
        "diff_coast": 0.15,
        "diff_preload": 30,
    },
    "street": {
        "label": "Street",
        "hp_range": (240, 500),
        "max_angle": 60,
        "tire_type": "semi_slick",
        "tire_width_f": 0.225,
        "tire_width_r": 0.255,
        "spring_rate_f": 45000,
        "spring_rate_r": 40000,
        "arb_rate_f": 28000,
        "arb_rate_r": 16000,
        "brake_torque": 2800,
        "brake_bias": 0.64,
        "diff_power": 0.5,
        "diff_coast": 0.25,
        "diff_preload": 50,
    },
    "pro": {
        "label": "Pro",
        "hp_range": (500, 800),
        "max_angle": 70,
        "tire_type": "slick",
        "tire_width_f": 0.245,
        "tire_width_r": 0.275,
        "spring_rate_f": 60000,
        "spring_rate_r": 50000,
        "arb_rate_f": 35000,
        "arb_rate_r": 20000,
        "brake_torque": 3500,
        "brake_bias": 0.65,
        "diff_power": 0.7,
        "diff_coast": 0.35,
        "diff_preload": 80,
    },
    "race": {
        "label": "Race",
        "hp_range": (600, 1000),
        "max_angle": 38,
        "tire_type": "slick",
        "tire_width_f": 0.265,
        "tire_width_r": 0.295,
        "spring_rate_f": 80000,
        "spring_rate_r": 70000,
        "arb_rate_f": 45000,
        "arb_rate_r": 30000,
        "brake_torque": 4200,
        "brake_bias": 0.58,
        "diff_power": 0.6,
        "diff_coast": 0.3,
        "diff_preload": 60,
    },
    "drift_grassroots": {
        "label": "Drift Grassroots",
        "hp_range": (180, 350),
        "max_angle": 55,
        "tire_type": "200tw",
        "tire_width_f": 0.215,
        "tire_width_r": 0.235,
        "spring_rate_f": 40000,
        "spring_rate_r": 35000,
        "arb_rate_f": 25000,
        "arb_rate_r": 14000,
        "brake_torque": 2400,
        "brake_bias": 0.63,
        "diff_power": 0.8,
        "diff_coast": 0.4,
        "diff_preload": 60,
    },
    "drift_street": {
        "label": "Drift Street",
        "hp_range": (240, 500),
        "max_angle": 60,
        "tire_type": "semi_slick",
        "tire_width_f": 0.225,
        "tire_width_r": 0.255,
        "spring_rate_f": 50000,
        "spring_rate_r": 45000,
        "arb_rate_f": 32000,
        "arb_rate_r": 18000,
        "brake_torque": 3000,
        "brake_bias": 0.64,
        "diff_power": 0.85,
        "diff_coast": 0.45,
        "diff_preload": 70,
    },
    "fd_prospec": {
        "label": "FD Pro Spec",
        "hp_range": (500, 800),
        "max_angle": 65,
        "tire_type": "pro_tire",
        "tire_width_f": 0.255,
        "tire_width_r": 0.275,
        "spring_rate_f": 65000,
        "spring_rate_r": 55000,
        "arb_rate_f": 38000,
        "arb_rate_r": 22000,
        "brake_torque": 3800,
        "brake_bias": 0.65,
        "diff_power": 0.9,
        "diff_coast": 0.5,
        "diff_preload": 90,
    },
    "fd_spec": {
        "label": "FD Spec",
        "hp_range": (800, 1200),
        "max_angle": 70,
        "tire_type": "fd_tire",
        "tire_width_f": 0.265,
        "tire_width_r": 0.295,
        "spring_rate_f": 75000,
        "spring_rate_r": 65000,
        "arb_rate_f": 42000,
        "arb_rate_r": 25000,
        "brake_torque": 4500,
        "brake_bias": 0.66,
        "diff_power": 1.0,
        "diff_coast": 0.6,
        "diff_preload": 100,
    },
}

# Tire compound lookup (grip multipliers for AC tire model)
TIRE_COMPOUNDS = {
    "street":     {"FRICTION_LIMIT_GRIP": 1.10, "DX_REF": 1.28, "DY_REF": 1.28, "wear_mult": 0.3},
    "200tw":      {"FRICTION_LIMIT_GRIP": 1.25, "DX_REF": 1.35, "DY_REF": 1.35, "wear_mult": 0.5},
    "semi_slick": {"FRICTION_LIMIT_GRIP": 1.35, "DX_REF": 1.42, "DY_REF": 1.42, "wear_mult": 0.7},
    "slick":      {"FRICTION_LIMIT_GRIP": 1.50, "DX_REF": 1.55, "DY_REF": 1.55, "wear_mult": 1.0},
    "pro_tire":   {"FRICTION_LIMIT_GRIP": 1.42, "DX_REF": 1.48, "DY_REF": 1.48, "wear_mult": 0.8},
    "fd_tire":    {"FRICTION_LIMIT_GRIP": 1.48, "DX_REF": 1.52, "DY_REF": 1.52, "wear_mult": 0.9},
}


def get_value(section_dict, key, default=0):
    """Extract numeric value from parsed INI data."""
    val = section_dict.get(key, section_dict.get(key.upper(), section_dict.get(key.lower(), default)))
    if isinstance(val, dict):
        return val.get("value", default)
    if isinstance(val, (int, float)):
        return val
    try:
        return float(val)
    except (TypeError, ValueError):
        return default


def calculate_wheel_rate(spring_rate, motion_ratio=1.0):
    """Wheel rate = spring rate × motion_ratio²"""
    return spring_rate * motion_ratio ** 2


def calculate_natural_freq(wheel_rate, sprung_mass_corner):
    """Natural frequency (Hz) = (1/2π) × √(wheel_rate / sprung_mass)"""
    if sprung_mass_corner <= 0:
        return 0
    return (1.0 / (2.0 * math.pi)) * math.sqrt(wheel_rate / sprung_mass_corner)


def calculate_critical_damping(spring_rate, sprung_mass_corner):
    """Critical damping coefficient = 2 × √(spring_rate × sprung_mass)"""
    return 2.0 * math.sqrt(spring_rate * sprung_mass_corner)


def calculate_damping(spring_rate, sprung_mass_corner, ratio_bump=0.25, ratio_rebound=0.40):
    """Calculate bump and rebound damping from spring rate and mass.
    Typical: bump 20-30% critical, rebound 35-50% critical.
    """
    cc = calculate_critical_damping(spring_rate, sprung_mass_corner)
    return {
        "bump": cc * ratio_bump,
        "fast_bump": cc * ratio_bump * 0.5,
        "rebound": cc * ratio_rebound,
        "fast_rebound": cc * ratio_rebound * 0.5,
    }


def calculate_arb_rate(target_rate, lever_length=0.15):
    """ARB torsion rate from target anti-roll rate and lever arm."""
    return target_rate * lever_length


def calculate_tire_radius(width_m, aspect_ratio=45, rim_diameter_inches=17):
    """Tire outer radius in meters from width, aspect ratio, rim diameter."""
    sidewall_m = width_m * (aspect_ratio / 100.0)
    rim_radius_m = (rim_diameter_inches * 0.0254) / 2.0
    return sidewall_m + rim_radius_m


def calculate_hub_mass(rim_diameter_inches=17, tire_width_m=0.225, brake_type="stock"):
    """Estimate unsprung mass per corner (kg): wheel + tire + brake + hub."""
    # Wheel mass estimate by diameter
    wheel_mass = 8.0 + (rim_diameter_inches - 15) * 1.5  # ~8kg for 15", +1.5kg per inch
    # Tire mass estimate
    tire_mass = 8.0 + tire_width_m * 20  # ~8kg base + width factor
    # Brake mass
    brake_masses = {"stock": 8.0, "sport": 10.0, "race": 14.0, "big_brake": 18.0}
    brake_mass = brake_masses.get(brake_type, 8.0)
    # Hub/knuckle
    hub_mass = 5.0
    return wheel_mass + tire_mass + brake_mass + hub_mass


def modify_car(parsed_files, class_key, car_mass=None):
    """
    Take parsed physics files and a class preset, return modified values.
    
    parsed_files: dict of {filename: parsed_ini_dict}
    class_key: key into CLASS_PRESETS
    car_mass: override total mass (kg) or None to read from car.ini
    
    Returns dict of modifications to apply.
    """
    preset = CLASS_PRESETS[class_key]
    mods = {"class": preset["label"], "changes": {}}
    
    # Get car mass
    car_ini = parsed_files.get("car.ini", {})
    basic = car_ini.get("BASIC", car_ini.get("basic", {}))
    total_mass = car_mass or get_value(basic, "TOTALMASS", 1300)
    
    # Sprung mass per corner (total - unsprung × 4) / 4
    tire_w = preset["tire_width_f"]
    hub_mass = calculate_hub_mass(17, tire_w)
    sprung_mass_total = total_mass - (hub_mass * 4)
    # Assume 55/45 front/rear weight distribution for typical FR car
    sprung_mass_f_corner = sprung_mass_total * 0.55 / 2.0
    sprung_mass_r_corner = sprung_mass_total * 0.45 / 2.0
    
    # Spring rates
    spring_f = preset["spring_rate_f"]
    spring_r = preset["spring_rate_r"]
    
    # Natural frequencies (target: 1.5-2.5 Hz street, 2.5-3.5 race)
    freq_f = calculate_natural_freq(spring_f, sprung_mass_f_corner)
    freq_r = calculate_natural_freq(spring_r, sprung_mass_r_corner)
    
    # Damping
    damp_f = calculate_damping(spring_f, sprung_mass_f_corner)
    damp_r = calculate_damping(spring_r, sprung_mass_r_corner)
    
    # Tire radius
    tire_radius_f = calculate_tire_radius(preset["tire_width_f"])
    tire_radius_r = calculate_tire_radius(preset["tire_width_r"])
    
    # Hub mass
    hub_mass_f = calculate_hub_mass(17, preset["tire_width_f"])
    hub_mass_r = calculate_hub_mass(17, preset["tire_width_r"])
    
    # Preload force (spring preload to support corner weight at ride height)
    corner_weight_f = sprung_mass_f_corner * 9.81
    corner_weight_r = sprung_mass_r_corner * 9.81
    
    mods["summary"] = {
        "total_mass": total_mass,
        "sprung_mass_f_corner": round(sprung_mass_f_corner, 1),
        "sprung_mass_r_corner": round(sprung_mass_r_corner, 1),
        "natural_freq_f": round(freq_f, 2),
        "natural_freq_r": round(freq_r, 2),
        "hub_mass_f": round(hub_mass_f, 1),
        "hub_mass_r": round(hub_mass_r, 1),
    }
    
    mods["changes"]["suspensions.ini"] = {
        "FRONT": {
            "HUB_MASS": round(hub_mass_f, 4),
        },
        "REAR": {
            "HUB_MASS": round(hub_mass_r, 4),
        },
        "FRONT_COILOVER_0": {
            "RATE": int(spring_f),
            "PRELOAD_FORCE": int(corner_weight_f),
        },
        "REAR_COILOVER_0": {
            "RATE": int(spring_r),
            "PRELOAD_FORCE": int(corner_weight_r),
        },
        "FRONT_DAMPER": {
            "DAMP_BUMP": int(damp_f["bump"]),
            "DAMP_FAST_BUMP": int(damp_f["fast_bump"]),
            "DAMP_REBOUND": int(damp_f["rebound"]),
            "DAMP_FAST_REBOUND": int(damp_f["fast_rebound"]),
            "DAMP_FAST_BUMPTHRESHOLD": 0.15,
            "DAMP_FAST_REBOUNDTHRESHOLD": 0.15,
        },
        "REAR_DAMPER": {
            "DAMP_BUMP": int(damp_r["bump"]),
            "DAMP_FAST_BUMP": int(damp_r["fast_bump"]),
            "DAMP_REBOUND": int(damp_r["rebound"]),
            "DAMP_FAST_REBOUND": int(damp_r["fast_rebound"]),
            "DAMP_FAST_BUMPTHRESHOLD": 0.15,
            "DAMP_FAST_REBOUNDTHRESHOLD": 0.15,
        },
    }
    
    # Tire modifications
    tire_compound = TIRE_COMPOUNDS[preset["tire_type"]]
    mods["changes"]["tyres.ini"] = {
        "FRONT": {
            "WIDTH": preset["tire_width_f"],
            "RADIUS": round(tire_radius_f, 4),
            "FRICTION_LIMIT_GRIP": tire_compound["FRICTION_LIMIT_GRIP"],
            "DX_REF": tire_compound["DX_REF"],
            "DY_REF": tire_compound["DY_REF"],
        },
        "REAR": {
            "WIDTH": preset["tire_width_r"],
            "RADIUS": round(tire_radius_r, 4),
            "FRICTION_LIMIT_GRIP": tire_compound["FRICTION_LIMIT_GRIP"],
            "DX_REF": tire_compound["DX_REF"],
            "DY_REF": tire_compound["DY_REF"],
        },
    }
    
    # Brake modifications
    mods["changes"]["brakes.ini"] = {
        "DATA": {
            "MAX_TORQUE": preset["brake_torque"],
            "FRONT_SHARE": preset["brake_bias"],
            "HANDBRAKE_TORQUE": int(preset["brake_torque"] * 0.25),
        }
    }
    
    # Differential modifications
    mods["changes"]["drivetrain.ini"] = {
        "DIFFERENTIAL": {
            "POWER": preset["diff_power"],
            "COAST": preset["diff_coast"],
            "PRELOAD": preset["diff_preload"],
        }
    }
    
    return mods
