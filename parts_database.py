"""
Aftermarket Parts Database — Real parts with real specs.
Each part modifies specific physics parameters.
"""

# ── COILOVERS ────────────────────────────────────────────────────
COILOVERS = {
    "stock": {
        "name": "Stock Suspension",
        "brand": "OEM",
        "price_tier": "stock",
        "description": "Factory springs and shocks",
        # These are multipliers/overrides — actual values come from car database
        "spring_rate_f_mult": 1.0,
        "spring_rate_r_mult": 1.0,
        "damping_quality": "basic",  # basic, adjustable, advanced
        "ride_height_drop_mm": 0,
        "camber_adjust": False,
    },
    "bc_br": {
        "name": "BC Racing BR Series",
        "brand": "BC Racing",
        "price_tier": "budget",
        "description": "Entry-level adjustable coilovers, 30-way damping adjust",
        "spring_rate_f_nm": 44100,  # 8kg/mm
        "spring_rate_r_nm": 33075,  # 6kg/mm
        "damping_quality": "adjustable",
        "ride_height_drop_mm": 35,
        "camber_adjust": False,
    },
    "tein_flex_z": {
        "name": "Tein Flex Z",
        "brand": "Tein",
        "price_tier": "budget",
        "description": "16-way adjustable, steel body",
        "spring_rate_f_nm": 39240,  # ~4kg/mm linear
        "spring_rate_r_nm": 29430,
        "damping_quality": "adjustable",
        "ride_height_drop_mm": 30,
        "camber_adjust": False,
    },
    "ksport_kontrol_pro": {
        "name": "KSport Kontrol Pro",
        "brand": "KSport",
        "price_tier": "mid",
        "description": "36-way adjustable, pillow ball mounts",
        "spring_rate_f_nm": 49050,  # 10kg/mm option
        "spring_rate_r_nm": 39240,  # 8kg/mm
        "damping_quality": "adjustable",
        "ride_height_drop_mm": 40,
        "camber_adjust": True,
    },
    "hks_hipermax_iv": {
        "name": "HKS Hipermax IV GT",
        "brand": "HKS",
        "price_tier": "mid",
        "description": "30-way adjustable, inverted monotube",
        "spring_rate_f_nm": 49050,
        "spring_rate_r_nm": 44100,
        "damping_quality": "adjustable",
        "ride_height_drop_mm": 35,
        "camber_adjust": False,
    },
    "stance_xr1": {
        "name": "Stance XR1",
        "brand": "Stance",
        "price_tier": "mid",
        "description": "Motorsport-oriented, 15-way adjustable",
        "spring_rate_f_nm": 58860,  # 12kg/mm
        "spring_rate_r_nm": 49050,  # 10kg/mm
        "damping_quality": "adjustable",
        "ride_height_drop_mm": 45,
        "camber_adjust": True,
    },
    "ohlins_road_track": {
        "name": "Öhlins Road & Track",
        "brand": "Öhlins",
        "price_tier": "premium",
        "description": "DFV technology, 20-way adjustable",
        "spring_rate_f_nm": 58860,
        "spring_rate_r_nm": 49050,
        "damping_quality": "advanced",
        "ride_height_drop_mm": 30,
        "camber_adjust": False,
    },
    "kw_v3": {
        "name": "KW Variant 3",
        "brand": "KW",
        "price_tier": "premium",
        "description": "Separate rebound/compression adjust, inox-line",
        "spring_rate_f_nm": 53955,
        "spring_rate_r_nm": 44100,
        "damping_quality": "advanced",
        "ride_height_drop_mm": 30,
        "camber_adjust": False,
    },
    "fortune_auto_500": {
        "name": "Fortune Auto 500 Series",
        "brand": "Fortune Auto",
        "price_tier": "premium",
        "description": "24-way adjustable, swift springs, digressive valving",
        "spring_rate_f_nm": 58860,
        "spring_rate_r_nm": 49050,
        "damping_quality": "advanced",
        "ride_height_drop_mm": 35,
        "camber_adjust": True,
    },
    "mca_blue": {
        "name": "MCA Blue Series",
        "brand": "MCA Suspension",
        "price_tier": "race",
        "description": "2-way adjustable, race-spec valving",
        "spring_rate_f_nm": 68670,  # 14kg/mm
        "spring_rate_r_nm": 58860,  # 12kg/mm
        "damping_quality": "advanced",
        "ride_height_drop_mm": 45,
        "camber_adjust": True,
    },
    "bc_zr": {
        "name": "BC Racing ZR Series",
        "brand": "BC Racing",
        "price_tier": "race",
        "description": "3-way adjustable, remote reservoir",
        "spring_rate_f_nm": 78480,  # 16kg/mm
        "spring_rate_r_nm": 68670,  # 14kg/mm
        "damping_quality": "advanced",
        "ride_height_drop_mm": 50,
        "camber_adjust": True,
    },
}

# ── ANGLE KITS ───────────────────────────────────────────────────
ANGLE_KITS = {
    "stock": {
        "name": "Stock Steering",
        "brand": "OEM",
        "max_angle_deg": 0,  # 0 = use car's stock angle
        "ackermann_pct": 100,
        "description": "Factory steering geometry",
        "compatible": ["all"],
    },
    "wisefab_s13": {
        "name": "Wisefab S-Chassis Lock Kit",
        "brand": "Wisefab",
        "max_angle_deg": 65,
        "ackermann_pct": 40,
        "description": "Full kit — new knuckles, extended LCA, tie rods",
        "compatible": ["nissan_s13_sr20", "nissan_s14_sr20", "nissan_s15_sr20"],
        "hub_mass_add_kg": 2.5,
    },
    "wisefab_e46": {
        "name": "Wisefab E46 Lock Kit",
        "brand": "Wisefab",
        "max_angle_deg": 60,
        "ackermann_pct": 35,
        "description": "Full replacement front knuckle kit",
        "compatible": ["bmw_e46_m3", "bmw_e46_325"],
        "hub_mass_add_kg": 3.0,
    },
    "wisefab_z33": {
        "name": "Wisefab 350Z Lock Kit",
        "brand": "Wisefab",
        "max_angle_deg": 63,
        "ackermann_pct": 38,
        "description": "Full front knuckle kit",
        "compatible": ["nissan_z33"],
        "hub_mass_add_kg": 2.8,
    },
    "drift_knuckles_generic": {
        "name": "Drift Knuckles (Generic)",
        "brand": "Various",
        "max_angle_deg": 55,
        "ackermann_pct": 50,
        "description": "Extended lower arm + modified knuckle",
        "compatible": ["all"],
        "hub_mass_add_kg": 1.5,
    },
    "megan_s_chassis": {
        "name": "Megan Racing Angle Kit",
        "brand": "Megan Racing",
        "max_angle_deg": 50,
        "ackermann_pct": 60,
        "description": "Tie rod + lower arm spacer kit",
        "compatible": ["nissan_s13_sr20", "nissan_s14_sr20", "nissan_s15_sr20"],
        "hub_mass_add_kg": 1.0,
    },
}

# ── WHEELS & TIRES ───────────────────────────────────────────────
WHEEL_SETUPS = {
    "stock": {
        "name": "Stock Wheels & Tires",
        "brand": "OEM",
        "description": "Factory wheel and tire setup",
        # Use car's stock specs
    },
    "15x8_et0_195_50": {
        "name": "15×8 ET0 + 195/50R15",
        "brand": "Various (Rota, Konig)",
        "description": "Lightweight drift setup, narrow",
        "rim_dia": 15, "rim_width": 8, "offset_mm": 0,
        "tire_width": 0.195, "tire_aspect": 50,
        "wheel_mass_kg": 7.5,
        "tire_compound": "street",
    },
    "17x9_et22_215_45": {
        "name": "17×9 ET22 + 215/45R17",
        "brand": "Work / Rays",
        "description": "Standard drift fitment",
        "rim_dia": 17, "rim_width": 9, "offset_mm": 22,
        "tire_width": 0.215, "tire_aspect": 45,
        "wheel_mass_kg": 9.5,
        "tire_compound": "semi_slick",
    },
    "17x9_et22_235_40": {
        "name": "17×9 ET22 + 235/40R17",
        "brand": "Work / Rays / SSR",
        "description": "Wider drift fitment",
        "rim_dia": 17, "rim_width": 9, "offset_mm": 22,
        "tire_width": 0.235, "tire_aspect": 40,
        "wheel_mass_kg": 9.5,
        "tire_compound": "semi_slick",
    },
    "18x95_et22_255_35": {
        "name": "18×9.5 ET22 + 255/35R18",
        "brand": "Work / Rays / Advan",
        "description": "Wide grip fitment, 18-inch",
        "rim_dia": 18, "rim_width": 9.5, "offset_mm": 22,
        "tire_width": 0.255, "tire_aspect": 35,
        "wheel_mass_kg": 11.0,
        "tire_compound": "semi_slick",
    },
    "18x10_et15_265_35": {
        "name": "18×10 ET15 + 265/35R18",
        "brand": "Volk / BBS / Advan",
        "description": "Pro-level wide fitment",
        "rim_dia": 18, "rim_width": 10, "offset_mm": 15,
        "tire_width": 0.265, "tire_aspect": 35,
        "wheel_mass_kg": 11.5,
        "tire_compound": "slick",
    },
    "18x105_et12_275_35": {
        "name": "18×10.5 ET12 + 275/35R18",
        "brand": "Volk TE37 / Advan GT",
        "description": "FD Pro Spec level, maximum grip",
        "rim_dia": 18, "rim_width": 10.5, "offset_mm": 12,
        "tire_width": 0.275, "tire_aspect": 35,
        "wheel_mass_kg": 12.0,
        "tire_compound": "slick",
    },
}

# ── BRAKE KITS ───────────────────────────────────────────────────
BRAKE_KITS = {
    "stock": {
        "name": "Stock Brakes",
        "brand": "OEM",
        "description": "Factory brake system",
        # Use car's stock specs
    },
    "z32_caliper_swap": {
        "name": "Z32 4-Pot Caliper Swap",
        "brand": "Nissan OEM",
        "description": "300ZX front caliper upgrade, popular S-chassis swap",
        "rotor_f_mm": 296,
        "torque_mult": 1.30,
        "bias": 0.64,
        "mass_add_f_kg": 3.0,
        "compatible": ["nissan_s13_sr20", "nissan_s14_sr20", "nissan_s15_sr20"],
    },
    "wilwood_dynapro": {
        "name": "Wilwood Dynapro 4-Piston",
        "brand": "Wilwood",
        "description": "Lightweight 4-piston forged caliper kit",
        "rotor_f_mm": 310,
        "torque_mult": 1.40,
        "bias": 0.64,
        "mass_add_f_kg": 1.5,
        "compatible": ["all"],
    },
    "ap_5200": {
        "name": "AP Racing CP5200 4-Piston",
        "brand": "AP Racing",
        "description": "Pro-level 4-piston endurance caliper",
        "rotor_f_mm": 330,
        "torque_mult": 1.55,
        "bias": 0.65,
        "mass_add_f_kg": 2.0,
        "compatible": ["all"],
    },
    "brembo_gt": {
        "name": "Brembo GT 6-Piston",
        "brand": "Brembo",
        "description": "6-piston monobloc front, 380mm rotor",
        "rotor_f_mm": 380,
        "torque_mult": 1.80,
        "bias": 0.66,
        "mass_add_f_kg": 4.0,
        "compatible": ["all"],
    },
    "stoptech_trophy": {
        "name": "StopTech Trophy Race",
        "brand": "StopTech",
        "description": "Asymmetric 4-piston, 355mm rotor",
        "rotor_f_mm": 355,
        "torque_mult": 1.60,
        "bias": 0.65,
        "mass_add_f_kg": 2.5,
        "compatible": ["all"],
    },
}

# ── DIFFERENTIALS ────────────────────────────────────────────────
DIFF_TYPES = {
    "stock": {
        "name": "Stock Differential",
        "brand": "OEM",
        "description": "Factory differential",
        # Use car's stock specs
    },
    "kaaz_15plate": {
        "name": "Kaaz 1.5-Way LSD",
        "brand": "Kaaz",
        "description": "1.5-way clutch-type, strong power lock",
        "diff_power": 0.75,
        "diff_coast": 0.35,
        "diff_preload": 60,
    },
    "kaaz_2way": {
        "name": "Kaaz 2-Way LSD",
        "brand": "Kaaz",
        "description": "Full 2-way clutch-type, drift spec",
        "diff_power": 0.90,
        "diff_coast": 0.55,
        "diff_preload": 80,
    },
    "os_giken_superlock": {
        "name": "OS Giken Super Lock",
        "brand": "OS Giken",
        "description": "Multi-plate, progressive lockup",
        "diff_power": 0.85,
        "diff_coast": 0.45,
        "diff_preload": 70,
    },
    "cusco_rs": {
        "name": "Cusco RS 1.5-Way",
        "brand": "Cusco",
        "description": "1.5-way clutch-type, street/track",
        "diff_power": 0.65,
        "diff_coast": 0.30,
        "diff_preload": 50,
    },
    "cusco_mz": {
        "name": "Cusco Type MZ 2-Way",
        "brand": "Cusco",
        "description": "Full 2-way, drift competition spec",
        "diff_power": 0.95,
        "diff_coast": 0.60,
        "diff_preload": 90,
    },
    "welded": {
        "name": "Welded / Spool",
        "brand": "N/A",
        "description": "Fully locked (welded or mini spool)",
        "diff_power": 1.0,
        "diff_coast": 1.0,
        "diff_preload": 200,
    },
}

# ── TIRE COMPOUNDS ───────────────────────────────────────────────
TIRE_COMPOUNDS = {
    "street": {
        "name": "All-Season / Street",
        "treadwear": "400+",
        "grip_mult": 1.10,
        "dx_ref": 1.28, "dy_ref": 1.28,
        "wear_rate": 0.3,
    },
    "200tw": {
        "name": "200TW (Hankook RS4, Federal 595)",
        "treadwear": "200",
        "grip_mult": 1.25,
        "dx_ref": 1.35, "dy_ref": 1.35,
        "wear_rate": 0.5,
    },
    "semi_slick": {
        "name": "Semi-Slick (RE-71RS, AD09, RT660)",
        "treadwear": "100-200",
        "grip_mult": 1.38,
        "dx_ref": 1.44, "dy_ref": 1.44,
        "wear_rate": 0.7,
    },
    "slick": {
        "name": "Racing Slick (Hoosier, Nitto NT01)",
        "treadwear": "DOT R-Comp",
        "grip_mult": 1.50,
        "dx_ref": 1.55, "dy_ref": 1.55,
        "wear_rate": 1.0,
    },
}


def get_compatible_parts(car_id, parts_dict):
    """Filter parts to those compatible with a given car."""
    result = {}
    for part_id, part in parts_dict.items():
        compat = part.get("compatible", ["all"])
        if "all" in compat or car_id in compat:
            result[part_id] = part
    return result
