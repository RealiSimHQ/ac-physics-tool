"""RealiSimHQ AC Physics Tool v2 — Drag & Drop Workflow"""
import os, json, io, zipfile, re, math, shutil, tempfile
from flask import Flask, request, render_template_string, send_file, jsonify
from src.ini_parser import parse_ini_file, parse_ini_string, get_value, get_raw
from src.car_detector import detect_car, _identify_from_name, CarIdentity
from parts_database import (
    COILOVERS, ANGLE_KITS, WHEEL_SETUPS, BRAKE_KITS, DIFF_TYPES, TIRE_COMPOUNDS,
    get_compatible_parts,
)

app = Flask(__name__)
UPLOAD_DIR = tempfile.mkdtemp(prefix="rsimhq_")

# ── Helpers ───────────────────────────────────────────────────────

def _session_dir():
    d = os.path.join(UPLOAD_DIR, "session")
    os.makedirs(d, exist_ok=True)
    return d

def _clear_session():
    d = os.path.join(UPLOAD_DIR, "session")
    if os.path.exists(d):
        shutil.rmtree(d)
    os.makedirs(d, exist_ok=True)

def _parse_uploaded_files(directory):
    """Parse all .ini files in a directory, return {logical_name: parsed_dict}."""
    parsed = {}
    raw_contents = {}
    for f in os.listdir(directory):
        fp = os.path.join(directory, f)
        if os.path.isfile(fp) and f.lower().endswith('.ini'):
            try:
                parsed[f.lower()] = parse_ini_file(fp)
                with open(fp, 'r', encoding='utf-8', errors='replace') as fh:
                    raw_contents[f.lower()] = fh.read()
            except Exception:
                pass
    return parsed, raw_contents


def _extract_stock_values(parsed):
    """Extract key physics values from parsed ini files as stock baseline."""
    stock = {}
    
    # car.ini
    car = parsed.get('car.ini', {})
    stock['total_mass'] = get_value(car, 'BASIC', 'TOTALMASS', 0)
    stock['steer_lock'] = get_value(car, 'CONTROLS', 'STEER_LOCK', 0)
    stock['steer_ratio'] = get_value(car, 'CONTROLS', 'STEER_RATIO', 15.0)
    stock['screen_name'] = get_raw(car, 'INFO', 'SCREEN_NAME', '') or get_raw(car, 'HEADER', 'SCREEN_NAME', '')
    
    # suspensions.ini
    susp = parsed.get('suspensions.ini', {})
    stock['wheelbase'] = get_value(susp, 'BASIC', 'WHEELBASE', 2.5)
    stock['cg_location'] = get_value(susp, 'BASIC', 'CG_LOCATION', 0.55)
    stock['spring_rate_f'] = get_value(susp, 'FRONT', 'SPRING_RATE', 30000)
    stock['spring_rate_r'] = get_value(susp, 'REAR', 'SPRING_RATE', 25000)
    stock['hub_mass_f'] = get_value(susp, 'FRONT', 'HUB_MASS', 35.0)
    stock['hub_mass_r'] = get_value(susp, 'REAR', 'HUB_MASS', 30.0)
    stock['track_f'] = get_value(susp, 'FRONT', 'TRACK', 1.48)
    stock['track_r'] = get_value(susp, 'REAR', 'TRACK', 1.48)
    stock['arb_f'] = get_value(susp, 'ARB', 'FRONT', 20000)
    stock['arb_r'] = get_value(susp, 'ARB', 'REAR', 10000)
    stock['damp_bump_f'] = get_value(susp, 'FRONT', 'DAMP_BUMP', 3000)
    stock['damp_rebound_f'] = get_value(susp, 'FRONT', 'DAMP_REBOUND', 5000)
    stock['damp_bump_r'] = get_value(susp, 'REAR', 'DAMP_BUMP', 2500)
    stock['damp_rebound_r'] = get_value(susp, 'REAR', 'DAMP_REBOUND', 4500)
    stock['susp_type_f'] = get_raw(susp, 'FRONT', 'TYPE', 'STRUT')
    stock['susp_type_r'] = get_raw(susp, 'REAR', 'TYPE', 'STRUT')
    
    # tyres.ini
    tyres = parsed.get('tyres.ini', {})
    stock['tire_width_f'] = get_value(tyres, 'FRONT', 'WIDTH', 0.225)
    stock['tire_width_r'] = get_value(tyres, 'REAR', 'WIDTH', 0.225)
    stock['tire_radius_f'] = get_value(tyres, 'FRONT', 'RADIUS', 0.31)
    stock['tire_radius_r'] = get_value(tyres, 'REAR', 'RADIUS', 0.31)
    stock['grip_f'] = get_value(tyres, 'FRONT', 'FRICTION_LIMIT_GRIP', 1.0)
    stock['grip_r'] = get_value(tyres, 'REAR', 'FRICTION_LIMIT_GRIP', 1.0)
    stock['dx_ref_f'] = get_value(tyres, 'FRONT', 'DX_REF', 1.28)
    stock['dy_ref_f'] = get_value(tyres, 'FRONT', 'DY_REF', 1.28)
    
    # brakes.ini
    brakes = parsed.get('brakes.ini', {})
    stock['brake_torque'] = get_value(brakes, 'DATA', 'MAX_TORQUE', 2000)
    stock['brake_bias'] = get_value(brakes, 'DATA', 'FRONT_SHARE', 0.62)
    
    # drivetrain.ini
    dt = parsed.get('drivetrain.ini', {})
    stock['drivetrain_type'] = get_raw(dt, 'TRACTION', 'TYPE', 'RWD')
    stock['diff_power'] = get_value(dt, 'DIFFERENTIAL', 'POWER', 0.0)
    stock['diff_coast'] = get_value(dt, 'DIFFERENTIAL', 'COAST', 0.0)
    stock['diff_preload'] = get_value(dt, 'DIFFERENTIAL', 'PRELOAD', 0)
    
    # Derived
    wdf = stock['cg_location'] if stock['cg_location'] > 0 else 0.55
    stock['weight_dist_f'] = wdf
    sprung_total = stock['total_mass'] - (stock['hub_mass_f'] * 2 + stock['hub_mass_r'] * 2)
    stock['sprung_f_corner'] = round(sprung_total * wdf / 2.0, 1)
    stock['sprung_r_corner'] = round(sprung_total * (1 - wdf) / 2.0, 1)
    
    if stock['steer_ratio'] > 0 and stock['steer_lock'] > 0:
        stock['stock_max_angle'] = round(stock['steer_lock'] / stock['steer_ratio'], 1)
    else:
        stock['stock_max_angle'] = 35
    
    # Natural freq
    def nat_freq(k, m):
        return round((1/(2*math.pi)) * math.sqrt(k/m), 2) if m > 0 and k > 0 else 0
    stock['nat_freq_f'] = nat_freq(stock['spring_rate_f'], stock['sprung_f_corner'])
    stock['nat_freq_r'] = nat_freq(stock['spring_rate_r'], stock['sprung_r_corner'])
    
    return stock


def _calculate_physics(stock, parts_selection):
    """Calculate modified physics from stock values + selected parts."""
    coilover = COILOVERS.get(parts_selection.get("coilovers", "stock"), COILOVERS["stock"])
    angle_kit = ANGLE_KITS.get(parts_selection.get("angle_kit", "stock"), ANGLE_KITS["stock"])
    wheels = WHEEL_SETUPS.get(parts_selection.get("wheels", "stock"), WHEEL_SETUPS["stock"])
    brake_kit = BRAKE_KITS.get(parts_selection.get("brakes", "stock"), BRAKE_KITS["stock"])
    diff = DIFF_TYPES.get(parts_selection.get("diff", "stock"), DIFF_TYPES["stock"])
    compound = TIRE_COMPOUNDS.get(parts_selection.get("tire_compound", "street"), TIRE_COMPOUNDS["street"])

    total_mass = stock['total_mass']
    wdf = stock['weight_dist_f']

    # Springs
    if "spring_rate_f_nm" in coilover:
        spring_f = coilover["spring_rate_f_nm"]
        spring_r = coilover["spring_rate_r_nm"]
    else:
        spring_f = stock['spring_rate_f'] * coilover.get("spring_rate_f_mult", 1.0)
        spring_r = stock['spring_rate_r'] * coilover.get("spring_rate_r_mult", 1.0)

    # Hub mass
    hub_mass_f = stock['hub_mass_f'] + brake_kit.get("mass_add_f_kg", 0) + angle_kit.get("hub_mass_add_kg", 0)
    hub_mass_r = stock['hub_mass_r']

    sprung_total = total_mass - (hub_mass_f * 2 + hub_mass_r * 2)
    sprung_f = sprung_total * wdf / 2.0
    sprung_r = sprung_total * (1 - wdf) / 2.0

    def nat_freq(k, m):
        return round((1/(2*math.pi)) * math.sqrt(k/m), 2) if m > 0 and k > 0 else 0
    freq_f = nat_freq(spring_f, sprung_f)
    freq_r = nat_freq(spring_r, sprung_r)

    # Damping
    damping_quality = coilover.get("damping_quality", "basic")
    ratios = {"basic": (0.22, 0.35), "adjustable": (0.25, 0.40), "advanced": (0.28, 0.45)}
    br, rr = ratios.get(damping_quality, (0.25, 0.40))
    def calc_damp(k, m, bump_r, reb_r):
        cc = 2 * math.sqrt(k * m)
        return {
            "bump": round(cc * bump_r),
            "fast_bump": round(cc * bump_r * 0.5),
            "rebound": round(cc * reb_r),
            "fast_rebound": round(cc * reb_r * 0.5),
        }
    damp_f = calc_damp(spring_f, sprung_f, br, rr)
    damp_r = calc_damp(spring_r, sprung_r, br, rr)

    # ARB
    spring_ratio_f = spring_f / max(stock['spring_rate_f'], 1)
    spring_ratio_r = spring_r / max(stock['spring_rate_r'], 1)
    arb_f = int(stock['arb_f'] * spring_ratio_f)
    arb_r = int(stock['arb_r'] * spring_ratio_r)

    # Steering
    if angle_kit.get("max_angle_deg", 0) > 0:
        max_angle = angle_kit["max_angle_deg"]
        steer_lock = max_angle * stock['steer_ratio']
    else:
        max_angle = stock['stock_max_angle']
        steer_lock = stock['steer_lock']

    # Brakes
    if "torque_mult" in brake_kit:
        brake_torque = int(stock['brake_torque'] * brake_kit["torque_mult"])
        brake_bias = brake_kit["bias"]
    else:
        brake_torque = stock['brake_torque']
        brake_bias = stock['brake_bias']

    # Diff
    diff_power = diff.get("diff_power", stock['diff_power'])
    diff_coast = diff.get("diff_coast", stock['diff_coast'])
    diff_preload = diff.get("diff_preload", stock['diff_preload'])

    # Tires
    tire_width_f = wheels.get("tire_width", stock['tire_width_f'])
    tire_width_r = wheels.get("tire_width", stock['tire_width_r'])
    if "rim_dia" in wheels:
        def tire_radius(w, asp, rim):
            return w * (asp/100.0) + (rim * 0.0254)/2.0
        tire_radius_f = round(tire_radius(tire_width_f, wheels.get("tire_aspect", 45), wheels["rim_dia"]), 4)
        tire_radius_r = round(tire_radius(tire_width_r, wheels.get("tire_aspect", 45), wheels["rim_dia"]), 4)
    else:
        tire_radius_f = stock['tire_radius_f']
        tire_radius_r = stock['tire_radius_r']

    # Build comparison
    comparison = [
        {"param": "Spring Rate (F)", "stock": f"{stock['spring_rate_f']:,.0f} N/m", "modified": f"{int(spring_f):,} N/m", "category": "suspension"},
        {"param": "Spring Rate (R)", "stock": f"{stock['spring_rate_r']:,.0f} N/m", "modified": f"{int(spring_r):,} N/m", "category": "suspension"},
        {"param": "Natural Freq (F)", "stock": f"{stock['nat_freq_f']:.2f} Hz", "modified": f"{freq_f:.2f} Hz", "category": "suspension"},
        {"param": "Natural Freq (R)", "stock": f"{stock['nat_freq_r']:.2f} Hz", "modified": f"{freq_r:.2f} Hz", "category": "suspension"},
        {"param": "Damper Bump (F)", "stock": f"{stock['damp_bump_f']:,.0f}", "modified": f"{damp_f['bump']:,}", "category": "suspension"},
        {"param": "Damper Rebound (F)", "stock": f"{stock['damp_rebound_f']:,.0f}", "modified": f"{damp_f['rebound']:,}", "category": "suspension"},
        {"param": "ARB (F)", "stock": f"{stock['arb_f']:,.0f} N/m", "modified": f"{arb_f:,} N/m", "category": "suspension"},
        {"param": "ARB (R)", "stock": f"{stock['arb_r']:,.0f} N/m", "modified": f"{arb_r:,} N/m", "category": "suspension"},
        {"param": "Hub Mass (F)", "stock": f"{stock['hub_mass_f']:.1f} kg", "modified": f"{hub_mass_f:.1f} kg", "category": "unsprung"},
        {"param": "Hub Mass (R)", "stock": f"{stock['hub_mass_r']:.1f} kg", "modified": f"{hub_mass_r:.1f} kg", "category": "unsprung"},
        {"param": "Max Steering Angle", "stock": f"{stock['stock_max_angle']}°", "modified": f"{max_angle}°", "category": "steering"},
        {"param": "Steer Lock", "stock": f"{stock['steer_lock']}°", "modified": f"{steer_lock:.0f}°", "category": "steering"},
        {"param": "Tire Width (F)", "stock": f"{stock['tire_width_f']*1000:.0f}mm", "modified": f"{tire_width_f*1000:.0f}mm", "category": "tires"},
        {"param": "Tire Width (R)", "stock": f"{stock['tire_width_r']*1000:.0f}mm", "modified": f"{tire_width_r*1000:.0f}mm", "category": "tires"},
        {"param": "Tire Radius (F)", "stock": f"{stock['tire_radius_f']:.4f}m", "modified": f"{tire_radius_f:.4f}m", "category": "tires"},
        {"param": "Tire Radius (R)", "stock": f"{stock['tire_radius_r']:.4f}m", "modified": f"{tire_radius_r:.4f}m", "category": "tires"},
        {"param": "Grip Level", "stock": f"{stock['grip_f']:.2f}", "modified": f"{compound['grip_mult']:.2f}", "category": "tires"},
        {"param": "Brake Torque", "stock": f"{stock['brake_torque']:,.0f} Nm", "modified": f"{brake_torque:,} Nm", "category": "brakes"},
        {"param": "Brake Bias", "stock": f"{stock['brake_bias']*100:.0f}% F", "modified": f"{brake_bias*100:.0f}% F", "category": "brakes"},
        {"param": "Diff Power Lock", "stock": f"{stock['diff_power']*100:.0f}%", "modified": f"{diff_power*100:.0f}%", "category": "diff"},
        {"param": "Diff Coast Lock", "stock": f"{stock['diff_coast']*100:.0f}%", "modified": f"{diff_coast*100:.0f}%", "category": "diff"},
        {"param": "Diff Preload", "stock": f"{stock['diff_preload']} Nm", "modified": f"{diff_preload} Nm", "category": "diff"},
    ]

    # INI changes to apply
    changes = {
        "car.ini": {
            "CONTROLS": {"STEER_LOCK": int(steer_lock)},
        },
        "suspensions.ini": {
            "FRONT": {"HUB_MASS": round(hub_mass_f, 4), "SPRING_RATE": int(spring_f)},
            "REAR": {"HUB_MASS": round(hub_mass_r, 4), "SPRING_RATE": int(spring_r)},
            "ARB": {"FRONT": arb_f, "REAR": arb_r},
        },
        "tyres.ini": {
            "FRONT": {
                "WIDTH": tire_width_f, "RADIUS": tire_radius_f,
                "FRICTION_LIMIT_GRIP": compound["grip_mult"],
                "DX_REF": compound["dx_ref"], "DY_REF": compound["dy_ref"],
            },
            "REAR": {
                "WIDTH": tire_width_r, "RADIUS": tire_radius_r,
                "FRICTION_LIMIT_GRIP": compound["grip_mult"],
                "DX_REF": compound["dx_ref"], "DY_REF": compound["dy_ref"],
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
                "POWER": diff_power, "COAST": diff_coast, "PRELOAD": diff_preload,
            },
        },
    }

    summary = {
        "total_mass": total_mass,
        "sprung_f_corner": round(sprung_f, 1),
        "sprung_r_corner": round(sprung_r, 1),
        "natural_freq_f": freq_f,
        "natural_freq_r": freq_r,
        "hub_mass_f": round(hub_mass_f, 1),
        "hub_mass_r": round(hub_mass_r, 1),
        "max_angle": max_angle,
        "tire_compound": compound.get("name", "Unknown"),
        "parts": {
            "coilovers": coilover["name"],
            "angle_kit": angle_kit["name"],
            "wheels": wheels.get("name", "Stock"),
            "brakes": brake_kit.get("name", "Stock"),
            "diff": diff.get("name", "Stock"),
            "tire_compound": compound.get("name", "Unknown"),
        },
    }

    return {"summary": summary, "changes": changes, "comparison": comparison}


def _apply_changes_to_content(content, sections_changes):
    """Apply key=value changes to an INI file's raw content, preserving structure."""
    for section, values in sections_changes.items():
        for key, new_val in values.items():
            pattern = rf'((?:^|\n)(\s*){re.escape(key)}\s*=)\s*[^\n;]*'
            new_content = re.sub(pattern, rf'\g<1>{new_val}', content, flags=re.IGNORECASE)
            if new_content != content:
                content = new_content
            else:
                # Key not found — try to append in section
                sec_pattern = rf'(\[{re.escape(section)}\][^\[]*)'
                def append_key(m):
                    return m.group(0).rstrip() + f'\n{key}={new_val}\n'
                content = re.sub(sec_pattern, append_key, content, count=1, flags=re.IGNORECASE)
    return content


# ── API Routes ────────────────────────────────────────────────────

@app.route('/api/upload', methods=['POST'])
def api_upload():
    """Handle file upload — zip, folder, or individual files."""
    _clear_session()
    sdir = _session_dir()
    
    # Check for zip file
    if 'zipfile' in request.files:
        zf = request.files['zipfile']
        try:
            with zipfile.ZipFile(io.BytesIO(zf.read())) as z:
                for name in z.namelist():
                    if name.endswith('/'):
                        continue
                    basename = os.path.basename(name)
                    if basename.lower().endswith(('.ini', '.lut')):
                        with z.open(name) as src:
                            with open(os.path.join(sdir, basename), 'wb') as dst:
                                dst.write(src.read())
        except zipfile.BadZipFile:
            return jsonify({"error": "Invalid zip file"}), 400
    else:
        # Individual files
        files = request.files.getlist('files')
        if not files:
            return jsonify({"error": "No files received"}), 400
        for f in files:
            name = os.path.basename(f.filename or '')
            if name.lower().endswith(('.ini', '.lut')):
                f.save(os.path.join(sdir, name))

    # Parse everything
    parsed, raw = _parse_uploaded_files(sdir)
    if not parsed:
        return jsonify({"error": "No .ini files found in upload"}), 400

    stock = _extract_stock_values(parsed)

    # Detect car identity
    identity_name = stock.get('screen_name', '')
    detected = CarIdentity()
    if identity_name:
        _identify_from_name(detected, identity_name, 'SCREEN_NAME')
    if detected.confidence < 0.5:
        # Try folder-level detection on any available name
        for key in ['short_name']:
            v = get_raw(parsed.get('car.ini', {}), 'INFO', key.upper(), '')
            if v:
                _identify_from_name(detected, v, key)
                if detected.confidence >= 0.5:
                    break

    # Save stock values for later
    # Make stock JSON-serializable
    stock_ser = {}
    for k, v in stock.items():
        if isinstance(v, (int, float, str, bool, type(None))):
            stock_ser[k] = v
        else:
            stock_ser[k] = str(v)
    with open(os.path.join(sdir, '_stock.json'), 'w') as f:
        json.dump(stock_ser, f)

    files_found = [f for f in os.listdir(sdir) if not f.startswith('_')]

    return jsonify({
        "car": {
            "name": identity_name or detected.model or "Unknown Car",
            "make": detected.make,
            "model": detected.model,
            "chassis": detected.chassis_code,
            "year": detected.year_range,
            "confidence": detected.confidence,
        },
        "stock": stock_ser,
        "files": files_found,
    })


@app.route('/api/parts')
def api_parts():
    return jsonify({
        "coilovers": COILOVERS,
        "angle_kits": ANGLE_KITS,
        "wheels": WHEEL_SETUPS,
        "brakes": BRAKE_KITS,
        "diffs": DIFF_TYPES,
        "tire_compounds": TIRE_COMPOUNDS,
    })


@app.route('/api/generate', methods=['POST'])
def api_generate():
    data = request.get_json()
    parts = data.get("parts", {})
    sdir = _session_dir()
    stock_path = os.path.join(sdir, '_stock.json')
    if not os.path.exists(stock_path):
        return jsonify({"error": "No car data uploaded yet"}), 400
    with open(stock_path) as f:
        stock = json.load(f)
    result = _calculate_physics(stock, parts)
    return jsonify(result)


@app.route('/api/download', methods=['POST'])
def api_download():
    data = request.get_json()
    parts = data.get("parts", {})
    sdir = _session_dir()
    stock_path = os.path.join(sdir, '_stock.json')
    if not os.path.exists(stock_path):
        return jsonify({"error": "No car data uploaded yet"}), 400
    with open(stock_path) as f:
        stock = json.load(f)
    result = _calculate_physics(stock, parts)

    car_name = stock.get('screen_name', 'Unknown').replace(' ', '_').replace('/', '-')

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fname in os.listdir(sdir):
            if fname.startswith('_') or not fname.lower().endswith(('.ini', '.lut')):
                continue
            fpath = os.path.join(sdir, fname)
            with open(fpath, 'r', encoding='utf-8', errors='replace') as fh:
                content = fh.read()
            
            # Apply changes if we have them for this file
            fl = fname.lower()
            if fl in result['changes']:
                content = _apply_changes_to_content(content, result['changes'][fl])
            
            zf.writestr(f"data/{fname}", content)

        # Readme
        readme = f"""RealiSimHQ Physics Modifications
================================
Car: {stock.get('screen_name', 'Unknown')}
Mass: {stock.get('total_mass', '?')} kg

Selected Parts:
"""
        for k, v in result['summary']['parts'].items():
            readme += f"  {k}: {v}\n"
        readme += f"""
Physics Summary:
  Natural Freq: {result['summary']['natural_freq_f']} / {result['summary']['natural_freq_r']} Hz
  Max Angle: {result['summary']['max_angle']}°

Instructions:
  1. Extract this zip into your AC car's folder
  2. The data/ folder will overlay the car's physics
  3. Back up your original data/ folder first!
"""
        zf.writestr("README.txt", readme)

    zip_buf.seek(0)
    return send_file(zip_buf, mimetype='application/zip', as_attachment=True,
                     download_name=f"RealiSimHQ_{car_name}_physics.zip")


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


# ── HTML ──────────────────────────────────────────────────────────

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RealiSimHQ Physics Tool</title>
<style>
:root {
    --bg: #08080f; --bg2: #0e0e1a; --bg3: #151525;
    --border: #1a1a35; --border-hi: #00e5ff;
    --cyan: #00e5ff; --cyan-dim: #00e5ff44; --cyan-glow: #00e5ff22;
    --green: #00ff88; --red: #ff4466; --orange: #ffaa00;
    --text: #e0e0e8; --text2: #8888aa; --text3: #555577;
    --radius: 10px;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: var(--bg); color: var(--text); font-family: 'Inter','Segoe UI',system-ui,sans-serif; line-height: 1.5; }
.app { max-width: 1100px; margin: 0 auto; padding: 20px; }
header { text-align: center; padding: 30px 0 20px; border-bottom: 1px solid var(--border); margin-bottom: 30px; }
header h1 { font-size: 2.2em; letter-spacing: -1px; }
header h1 span { color: var(--cyan); }
header p { color: var(--text2); margin-top: 4px; }

.step { display: none; animation: fadeIn .3s ease; }
.step.active { display: block; }
@keyframes fadeIn { from { opacity:0; transform:translateY(10px); } to { opacity:1; transform:none; } }

.progress { display: flex; gap: 6px; margin-bottom: 30px; }
.progress-dot { height: 4px; flex: 1; background: var(--border); border-radius: 2px; transition: background .3s; }
.progress-dot.done { background: var(--cyan); }
.progress-dot.current { background: linear-gradient(90deg, var(--cyan), var(--cyan-dim)); }

/* ── Drop Zone ── */
.drop-zone {
    border: 2px dashed var(--border); border-radius: 16px; padding: 60px 40px;
    text-align: center; cursor: pointer; transition: all .3s ease;
    background: linear-gradient(135deg, var(--bg2), var(--bg3));
    position: relative; overflow: hidden;
}
.drop-zone::before {
    content: ''; position: absolute; inset: 0; border-radius: 16px;
    background: radial-gradient(circle at 50% 50%, var(--cyan-glow) 0%, transparent 70%);
    opacity: 0; transition: opacity .3s;
}
.drop-zone:hover, .drop-zone.dragover {
    border-color: var(--cyan); box-shadow: 0 0 40px var(--cyan-glow);
}
.drop-zone:hover::before, .drop-zone.dragover::before { opacity: 1; }
.drop-zone .icon { font-size: 3em; margin-bottom: 12px; filter: drop-shadow(0 0 20px var(--cyan)); }
.drop-zone .title { font-size: 1.3em; font-weight: 700; color: var(--cyan); position: relative; }
.drop-zone .subtitle { color: var(--text2); margin-top: 8px; font-size: .9em; position: relative; }
.drop-zone .formats { color: var(--text3); margin-top: 16px; font-size: .8em; position: relative;
    display: flex; gap: 12px; justify-content: center; flex-wrap: wrap; }
.drop-zone .formats span { background: var(--bg); padding: 4px 10px; border-radius: 6px; border: 1px solid var(--border); }
.drop-zone input { display: none; }
.drop-zone.loading .icon { animation: pulse 1.5s ease infinite; }
@keyframes pulse { 0%,100% { opacity:.5; } 50% { opacity:1; } }
.drop-zone.success { border-color: var(--green); }
.drop-zone.success .icon { filter: drop-shadow(0 0 20px var(--green)); }

/* ── Car Banner ── */
.car-banner {
    background: var(--bg2); border: 1px solid var(--cyan-dim); border-radius: var(--radius);
    padding: 16px 20px; margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between;
}
.car-banner .name { font-size: 1.3em; font-weight: 700; }
.car-banner .detail { color: var(--text2); font-size: .85em; margin-top: 2px; }
.car-banner .stats { display: flex; gap: 12px; flex-wrap: wrap; }
.car-banner .stat { background: var(--bg3); padding: 4px 10px; border-radius: 6px; font-size: .8em; color: var(--text2); }

/* ── Parts ── */
.parts-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
@media (max-width:768px) { .parts-grid { grid-template-columns: 1fr; } }
.part-group { background: var(--bg2); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; }
.part-group h3 { font-size: 1em; color: var(--cyan); margin-bottom: 10px; }
.part-option { padding: 10px 12px; border: 1px solid var(--border); border-radius: 6px; margin-bottom: 6px; cursor: pointer; transition: all .15s; font-size: .9em; }
.part-option:hover { border-color: var(--cyan-dim); }
.part-option.selected { border-color: var(--cyan); background: #00e5ff08; }
.part-option .part-name { font-weight: 600; }
.part-option .part-brand { color: var(--text2); font-size: .85em; }
.part-option .part-desc { color: var(--text3); font-size: .8em; margin-top: 2px; }
.part-option .part-spec { color: var(--orange); font-size: .8em; margin-top: 2px; }

/* ── Results ── */
.summary-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px,1fr)); gap: 10px; margin-bottom: 24px; }
.summary-card { background: var(--bg2); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px; }
.summary-card .label { color: var(--text2); font-size: .8em; text-transform: uppercase; letter-spacing: 1px; }
.summary-card .value { color: var(--cyan); font-size: 1.6em; font-weight: 700; margin-top: 2px; }
.summary-card .unit { color: var(--text3); font-size: .7em; }

.comp-section { margin-bottom: 20px; }
.comp-section h3 { color: var(--text2); font-size: .85em; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 8px; }
table { width: 100%; border-collapse: collapse; }
th { background: var(--bg3); color: var(--text2); padding: 8px 12px; text-align: left; font-size: .8em; text-transform: uppercase; letter-spacing: 1px; }
td { padding: 8px 12px; border-bottom: 1px solid var(--border); font-size: .9em; }
td.stock { color: var(--text2); }
td.changed { color: var(--orange); font-weight: 600; }
tr:hover { background: var(--bg2); }

.btn { background: var(--cyan); color: var(--bg); border: none; border-radius: var(--radius);
    padding: 14px 32px; font-size: 1.05em; font-weight: 700; cursor: pointer; transition: all .2s;
    display: inline-flex; align-items: center; gap: 8px; }
.btn:hover { filter: brightness(1.15); transform: translateY(-1px); }
.btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text);
    border-radius: var(--radius); padding: 10px 20px; font-size: .9em; cursor: pointer; transition: all .2s; }
.btn-outline:hover { border-color: var(--cyan); color: var(--cyan); }
.btn-row { display: flex; gap: 10px; margin-top: 24px; justify-content: center; flex-wrap: wrap; }

footer { text-align: center; color: var(--text3); font-size: .8em; padding: 40px 0 20px; border-top: 1px solid var(--border); margin-top: 40px; }
</style>
</head>
<body>
<div class="app">
    <header>
        <h1>⚡ <span>RealiSimHQ</span> Physics Tool</h1>
        <p>Drop your car → Pick your parts → Download real physics</p>
    </header>

    <div class="progress" id="progress">
        <div class="progress-dot current" data-step="1"></div>
        <div class="progress-dot" data-step="2"></div>
        <div class="progress-dot" data-step="3"></div>
    </div>

    <!-- STEP 1: Upload -->
    <div class="step active" id="step1">
        <div class="drop-zone" id="dropZone">
            <div class="icon">📁</div>
            <div class="title">Drop your car's data folder here</div>
            <div class="subtitle">Drag & drop a zip, folder, or individual .ini files</div>
            <div class="formats">
                <span>car.ini</span><span>suspensions.ini</span><span>tyres.ini</span>
                <span>drivetrain.ini</span><span>brakes.ini</span><span>.zip</span>
            </div>
            <input type="file" id="fileInput" multiple>
            <input type="file" id="folderInput" webkitdirectory multiple>
        </div>
        <p style="text-align:center;color:var(--text3);margin-top:12px;font-size:.85em;">
            Find your car's data in: <code style="color:var(--cyan);">assettocorsa/content/cars/YOUR_CAR/data/</code>
        </p>
    </div>

    <!-- STEP 2: Parts -->
    <div class="step" id="step2">
        <div class="car-banner" id="carBanner"></div>
        <div class="parts-grid" id="partsGrid"></div>
        <div class="btn-row">
            <button class="btn-outline" onclick="goStep(1)">← Upload Different Car</button>
            <button class="btn" onclick="generatePhysics()">⚡ Generate Physics</button>
        </div>
    </div>

    <!-- STEP 3: Results -->
    <div class="step" id="step3">
        <div class="car-banner" id="resultBanner"></div>
        <div class="summary-grid" id="summaryGrid"></div>
        <div id="comparisonTables"></div>
        <div class="btn-row">
            <button class="btn-outline" onclick="goStep(2)">← Modify Parts</button>
            <button class="btn" onclick="downloadZip()">📦 Download Modified Data</button>
        </div>
    </div>

    <footer>RealiSimHQ &copy; 2025 — Real parts, real physics.</footer>
</div>

<script>
let state = { step:1, stock:null, carInfo:null, partsDb:null, selectedParts:{}, result:null };

function goStep(n) {
    state.step = n;
    document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
    document.getElementById('step'+n).classList.add('active');
    document.querySelectorAll('.progress-dot').forEach(d => {
        const ds = +d.dataset.step;
        d.className = 'progress-dot' + (ds<n?' done':ds===n?' current':'');
    });
    window.scrollTo({top:0,behavior:'smooth'});
}

// ── Drop Zone ──
const dz = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const folderInput = document.getElementById('folderInput');

dz.addEventListener('click', (e) => {
    // Show a choice — hold shift for folder
    if (e.shiftKey) folderInput.click();
    else fileInput.click();
});
dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('dragover'); });
dz.addEventListener('dragleave', () => dz.classList.remove('dragover'));
dz.addEventListener('drop', e => { e.preventDefault(); dz.classList.remove('dragover'); handleDrop(e.dataTransfer); });
fileInput.addEventListener('change', e => handleFileInput(e.target.files));
folderInput.addEventListener('change', e => handleFileInput(e.target.files));

async function handleDrop(dt) {
    // Check for zip
    const files = dt.files;
    if (files.length === 1 && files[0].name.toLowerCase().endsWith('.zip')) {
        await uploadZip(files[0]);
        return;
    }
    // Try webkitGetAsEntry for folder drops
    const items = dt.items;
    if (items && items.length > 0 && items[0].webkitGetAsEntry) {
        const allFiles = [];
        const promises = [];
        for (const item of items) {
            const entry = item.webkitGetAsEntry();
            if (entry) promises.push(traverseEntry(entry, allFiles));
        }
        await Promise.all(promises);
        if (allFiles.length > 0) {
            await uploadFiles(allFiles);
            return;
        }
    }
    // Fallback: plain files
    await uploadFiles(Array.from(files));
}

function traverseEntry(entry, result) {
    return new Promise(resolve => {
        if (entry.isFile) {
            entry.file(f => {
                // Preserve relative path
                f._path = entry.fullPath;
                result.push(f);
                resolve();
            });
        } else if (entry.isDirectory) {
            const reader = entry.createReader();
            reader.readEntries(async entries => {
                for (const e of entries) await traverseEntry(e, result);
                resolve();
            });
        } else {
            resolve();
        }
    });
}

async function handleFileInput(files) {
    if (files.length === 1 && files[0].name.toLowerCase().endsWith('.zip')) {
        await uploadZip(files[0]);
    } else {
        await uploadFiles(Array.from(files));
    }
}

async function uploadZip(file) {
    setDropState('loading', `Uploading ${file.name}...`);
    const fd = new FormData();
    fd.append('zipfile', file);
    const resp = await fetch('/api/upload', {method:'POST', body:fd});
    await handleUploadResp(resp);
}

async function uploadFiles(files) {
    const ini = files.filter(f => {
        const n = (f._path || f.webkitRelativePath || f.name).toLowerCase();
        return n.endsWith('.ini') || n.endsWith('.lut');
    });
    if (!ini.length) {
        setDropState('error', 'No .ini files found!');
        return;
    }
    setDropState('loading', `Uploading ${ini.length} files...`);
    const fd = new FormData();
    for (const f of ini) fd.append('files', f, f.name);
    const resp = await fetch('/api/upload', {method:'POST', body:fd});
    await handleUploadResp(resp);
}

async function handleUploadResp(resp) {
    const data = await resp.json();
    if (data.error) { setDropState('error', data.error); return; }
    state.stock = data.stock;
    state.carInfo = data.car;
    setDropState('success', `✅ ${data.car.name || 'Car detected'} — ${data.files.length} files loaded`);
    
    // Fetch parts
    const pr = await fetch('/api/parts');
    state.partsDb = await pr.json();
    state.selectedParts = {
        coilovers:'stock', angle_kit:'stock', wheels:'stock',
        brakes:'stock', diff:'stock', tire_compound:'street'
    };
    
    setTimeout(() => { renderParts(); goStep(2); }, 600);
}

function setDropState(mode, msg) {
    dz.className = 'drop-zone ' + mode;
    if (mode === 'loading') {
        dz.querySelector('.icon').textContent = '⏳';
        dz.querySelector('.title').textContent = msg;
        dz.querySelector('.subtitle').textContent = 'Reading physics files...';
    } else if (mode === 'success') {
        dz.querySelector('.icon').textContent = '🏎️';
        dz.querySelector('.title').textContent = msg;
        dz.querySelector('.subtitle').textContent = 'Proceeding to parts selection...';
    } else if (mode === 'error') {
        dz.querySelector('.icon').textContent = '❌';
        dz.querySelector('.title').textContent = msg;
        dz.querySelector('.subtitle').textContent = 'Try again with different files';
        setTimeout(() => { dz.className = 'drop-zone'; dz.querySelector('.icon').textContent = '📁';
            dz.querySelector('.title').textContent = "Drop your car's data folder here";
            dz.querySelector('.subtitle').textContent = 'Drag & drop a zip, folder, or individual .ini files'; }, 3000);
    }
}

// ── Parts Selection ──
function renderParts() {
    const s = state.stock;
    const c = state.carInfo;
    document.getElementById('carBanner').innerHTML = `
        <div>
            <div class="name">${c.name || c.model || 'Unknown Car'}</div>
            <div class="detail">${c.make} ${c.model}${c.chassis ? ' · '+c.chassis : ''}${c.year ? ' · '+c.year : ''}</div>
        </div>
        <div class="stats">
            <span class="stat">${s.total_mass} kg</span>
            <span class="stat">${s.drivetrain_type}</span>
            <span class="stat">${s.susp_type_f} / ${s.susp_type_r}</span>
            <span class="stat">${s.spring_rate_f} / ${s.spring_rate_r} N/m</span>
        </div>
    `;

    const grid = document.getElementById('partsGrid');
    grid.innerHTML = '';
    const groups = [
        {key:'coilovers', title:'🔧 Coilovers', data:state.partsDb.coilovers, pk:'coilovers',
         spec: c => c.spring_rate_f_nm ? `${Math.round(c.spring_rate_f_nm/9810)}/${Math.round(c.spring_rate_r_nm/9810)} kg/mm` : 'Stock rates'},
        {key:'angle_kits', title:'🔄 Angle Kit', data:state.partsDb.angle_kits, pk:'angle_kit',
         spec: c => c.max_angle_deg > 0 ? `${c.max_angle_deg}° max` : 'Stock angle'},
        {key:'wheels', title:'🛞 Wheels & Tires', data:state.partsDb.wheels, pk:'wheels',
         spec: c => c.rim_dia ? `${c.rim_dia}×${c.rim_width} ET${c.offset_mm}` : 'Stock'},
        {key:'brakes', title:'🛑 Brakes', data:state.partsDb.brakes, pk:'brakes',
         spec: c => c.torque_mult ? `+${Math.round((c.torque_mult-1)*100)}% torque` : 'Stock'},
        {key:'diffs', title:'⚙️ Differential', data:state.partsDb.diffs, pk:'diff',
         spec: c => c.diff_power!==undefined ? `${Math.round(c.diff_power*100)}% lock` : 'Stock'},
        {key:'compounds', title:'🏁 Tire Compound', data:state.partsDb.tire_compounds, pk:'tire_compound',
         spec: c => `Grip: ${c.grip_mult.toFixed(2)}`},
    ];

    for (const g of groups) {
        const div = document.createElement('div');
        div.className = 'part-group';
        div.innerHTML = `<h3>${g.title}</h3>`;
        for (const [id, part] of Object.entries(g.data)) {
            const sel = state.selectedParts[g.pk] === id;
            const opt = document.createElement('div');
            opt.className = 'part-option' + (sel ? ' selected' : '');
            opt.innerHTML = `<div class="part-name">${part.name}</div>
                <div class="part-brand">${part.brand||''}</div>
                <div class="part-desc">${part.description||''}</div>
                <div class="part-spec">${g.spec(part)}</div>`;
            opt.onclick = () => { state.selectedParts[g.pk] = id; renderParts(); };
            div.appendChild(opt);
        }
        grid.appendChild(div);
    }
}

// ── Generate ──
async function generatePhysics() {
    const resp = await fetch('/api/generate', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({parts: state.selectedParts})
    });
    state.result = await resp.json();
    renderResults();
    goStep(3);
}

function renderResults() {
    const r = state.result;
    const sm = r.summary;
    const c = state.carInfo;
    document.getElementById('resultBanner').innerHTML = `
        <div>
            <div class="name">${c.name || c.model}</div>
            <div class="detail">${Object.values(sm.parts).filter(v=>v!=='Stock Suspension'&&v!=='Stock Steering'&&v!=='Stock Wheels & Tires'&&v!=='Stock Brakes'&&v!=='Stock Differential').join(' · ') || 'Stock configuration'}</div>
        </div>`;
    
    const grid = document.getElementById('summaryGrid');
    grid.innerHTML = [
        ['Mass', sm.total_mass, 'kg'],
        ['Sprung F', sm.sprung_f_corner, 'kg/corner'],
        ['Sprung R', sm.sprung_r_corner, 'kg/corner'],
        ['Nat Freq F', sm.natural_freq_f, 'Hz'],
        ['Nat Freq R', sm.natural_freq_r, 'Hz'],
        ['Max Angle', sm.max_angle, '°'],
        ['Hub F', sm.hub_mass_f, 'kg'],
        ['Hub R', sm.hub_mass_r, 'kg'],
    ].map(([l,v,u]) => `<div class="summary-card"><div class="label">${l}</div><div class="value">${v} <span class="unit">${u}</span></div></div>`).join('');

    const cats = {suspension:'Suspension',unsprung:'Unsprung Mass',steering:'Steering',tires:'Tires & Wheels',brakes:'Brakes',diff:'Differential'};
    const tables = document.getElementById('comparisonTables');
    tables.innerHTML = '';
    for (const [ck,cn] of Object.entries(cats)) {
        const items = r.comparison.filter(c => c.category===ck);
        if (!items.length) continue;
        const sec = document.createElement('div');
        sec.className = 'comp-section';
        let h = `<h3>${cn}</h3><table><tr><th>Parameter</th><th>Stock (Your File)</th><th>Modified</th></tr>`;
        for (const it of items) {
            const ch = it.stock !== it.modified;
            h += `<tr><td>${it.param}</td><td class="stock">${it.stock}</td><td class="${ch?'changed':'stock'}">${it.modified}</td></tr>`;
        }
        h += '</table>';
        sec.innerHTML = h;
        tables.appendChild(sec);
    }
}

async function downloadZip() {
    const resp = await fetch('/api/download', {
        method:'POST', headers:{'Content-Type':'application/json'},
        body: JSON.stringify({parts: state.selectedParts})
    });
    const blob = await resp.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `RealiSimHQ_physics.zip`; a.click();
    URL.revokeObjectURL(url);
}
</script>
</body>
</html>"""


if __name__ == '__main__':
    print("🏎️  RealiSimHQ Physics Tool v2")
    print("   http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
