"""AC Physics Tool — Web UI for testing."""
import os, json, io, zipfile, shutil, tempfile
from flask import Flask, request, render_template_string, send_file, jsonify
from src.ini_parser import parse_ini_file
from src.car_detector import detect_car
from modifier import CLASS_PRESETS, modify_car, get_value

app = Flask(__name__)
UPLOAD_DIR = tempfile.mkdtemp()

HTML = """<!DOCTYPE html>
<html>
<head>
<title>RealiSimHQ Physics Tool</title>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { 
    background: #0a0a0f; color: #e0e0e0; font-family: 'Segoe UI', sans-serif; 
    min-height: 100vh; padding: 20px;
}
h1 { color: #00ffff; text-align: center; margin-bottom: 10px; font-size: 2em; }
h2 { color: #ff6b6b; margin: 20px 0 10px; }
h3 { color: #00ffff; margin: 15px 0 8px; }
.subtitle { text-align: center; color: #888; margin-bottom: 30px; }
.container { max-width: 900px; margin: 0 auto; }

/* Upload area */
.upload-area {
    border: 2px dashed #00ffff44; border-radius: 12px; padding: 40px;
    text-align: center; margin: 20px 0; cursor: pointer;
    transition: all 0.3s;
}
.upload-area:hover, .upload-area.dragover { 
    border-color: #00ffff; background: #00ffff08; 
}
.upload-area input { display: none; }

/* Class selector */
.class-grid {
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 20px 0;
}
.class-btn {
    background: #1a1a2e; border: 2px solid #333; border-radius: 8px;
    padding: 15px; cursor: pointer; transition: all 0.2s; text-align: center;
}
.class-btn:hover { border-color: #00ffff; transform: translateY(-2px); }
.class-btn.selected { border-color: #00ffff; background: #00ffff15; }
.class-btn .name { font-size: 1.1em; font-weight: bold; color: #fff; }
.class-btn .info { font-size: 0.8em; color: #888; margin-top: 4px; }

/* Results */
.results { display: none; margin-top: 30px; }
.stat-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; }
.stat-card {
    background: #1a1a2e; border: 1px solid #333; border-radius: 8px; padding: 15px;
}
.stat-card .label { color: #888; font-size: 0.85em; }
.stat-card .value { color: #00ffff; font-size: 1.4em; font-weight: bold; }
.stat-card .unit { color: #666; font-size: 0.8em; }

/* Changes table */
table { width: 100%; border-collapse: collapse; margin: 10px 0; }
th { background: #1a1a2e; color: #00ffff; padding: 8px; text-align: left; }
td { padding: 8px; border-bottom: 1px solid #222; }
td.old { color: #ff6b6b; }
td.new { color: #00ff88; }
td.file { color: #ffa500; font-weight: bold; }

/* Buttons */
.btn {
    background: #00ffff; color: #0a0a0f; border: none; border-radius: 8px;
    padding: 12px 30px; font-size: 1.1em; font-weight: bold; cursor: pointer;
    margin: 20px auto; display: block; transition: all 0.2s;
}
.btn:hover { background: #00dddd; transform: translateY(-2px); }
.btn:disabled { background: #333; color: #666; cursor: not-allowed; transform: none; }

/* Current car info */
.car-info {
    background: #1a1a2e; border: 1px solid #00ffff44; border-radius: 8px;
    padding: 20px; margin: 20px 0;
}
.car-info .car-name { font-size: 1.5em; color: #fff; }

.loading { display: none; text-align: center; color: #00ffff; padding: 20px; }
.loading.show { display: block; }

#log { 
    background: #111; border: 1px solid #333; border-radius: 8px; 
    padding: 15px; margin: 15px 0; font-family: monospace; font-size: 0.85em;
    max-height: 300px; overflow-y: auto; display: none;
}
#log.show { display: block; }
#log .line { padding: 2px 0; }
#log .ok { color: #00ff88; }
#log .warn { color: #ffa500; }
#log .info { color: #00ffff; }
</style>
</head>
<body>
<div class="container">
    <h1>⚡ RealiSimHQ Physics Tool</h1>
    <p class="subtitle">Trash mod in → Realistic physics out</p>
    
    <div class="upload-area" id="dropZone" onclick="document.getElementById('fileInput').click()">
        <p style="font-size:1.3em; color:#00ffff;">📁 Drop car data folder here</p>
        <p style="color:#666; margin-top:10px;">or click to select files (car.ini, suspensions.ini, tyres.ini, etc.)</p>
        <input type="file" id="fileInput" multiple webkitdirectory>
    </div>
    
    <div class="car-info" id="carInfo" style="display:none">
        <div class="car-name" id="carName">—</div>
        <div id="carStats" style="margin-top:10px; color:#888;"></div>
    </div>
    
    <div id="classSection" style="display:none">
        <h2>Choose Your Class</h2>
        <div class="class-grid" id="classGrid"></div>
    </div>
    
    <button class="btn" id="applyBtn" style="display:none" onclick="applyMods()">
        ⚡ APPLY PHYSICS
    </button>
    
    <div class="loading" id="loading">⏳ Calculating physics...</div>
    
    <div class="results" id="results">
        <h2>📊 Physics Report</h2>
        <div class="stat-grid" id="summaryStats"></div>
        
        <h3>Changes Applied</h3>
        <div id="log" class="show"></div>
        
        <button class="btn" onclick="downloadZip()" id="downloadBtn">
            📦 Download Modified Files
        </button>
    </div>
</div>

<script>
let uploadedFiles = {};
let selectedClass = null;
let modResult = null;

// Class data
const classes = CLASSES_JSON;

// Build class grid
const grid = document.getElementById('classGrid');
for (const [key, cls] of Object.entries(classes)) {
    const btn = document.createElement('div');
    btn.className = 'class-btn';
    btn.dataset.key = key;
    btn.innerHTML = `
        <div class="name">${cls.label}</div>
        <div class="info">${cls.hp_range[0]}-${cls.hp_range[1]} HP · ${cls.max_angle}° angle</div>
    `;
    btn.onclick = () => selectClass(key);
    grid.appendChild(btn);
}

function selectClass(key) {
    selectedClass = key;
    document.querySelectorAll('.class-btn').forEach(b => b.classList.remove('selected'));
    document.querySelector(`.class-btn[data-key="${key}"]`).classList.add('selected');
    document.getElementById('applyBtn').style.display = 'block';
}

// File upload
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');

dropZone.ondragover = (e) => { e.preventDefault(); dropZone.classList.add('dragover'); };
dropZone.ondragleave = () => dropZone.classList.remove('dragover');
dropZone.ondrop = (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    handleFiles(e.dataTransfer.files);
};
fileInput.onchange = (e) => handleFiles(e.target.files);

async function handleFiles(files) {
    const formData = new FormData();
    let count = 0;
    for (const file of files) {
        const name = file.webkitRelativePath || file.name;
        // Only upload .ini, .lut, .cfg files
        if (name.match(/\\.(ini|lut|cfg)$/i)) {
            formData.append('files', file, name);
            count++;
        }
    }
    if (count === 0) {
        alert('No physics files found. Make sure to select a folder with .ini files.');
        return;
    }
    
    dropZone.innerHTML = `<p style="color:#00ff88">📂 Uploading ${count} files...</p>`;
    
    const resp = await fetch('/upload', { method: 'POST', body: formData });
    const data = await resp.json();
    
    if (data.error) {
        dropZone.innerHTML = `<p style="color:#ff6b6b">❌ ${data.error}</p>`;
        return;
    }
    
    dropZone.innerHTML = `<p style="color:#00ff88">✅ ${count} files loaded</p>`;
    
    // Show car info
    document.getElementById('carInfo').style.display = 'block';
    document.getElementById('carName').textContent = data.car_name || 'Unknown Car';
    document.getElementById('carStats').innerHTML = data.stats_html || '';
    
    // Show class selector
    document.getElementById('classSection').style.display = 'block';
}

async function applyMods() {
    if (!selectedClass) return;
    
    document.getElementById('applyBtn').disabled = true;
    document.getElementById('loading').classList.add('show');
    document.getElementById('results').style.display = 'none';
    
    const resp = await fetch('/modify', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({class_key: selectedClass})
    });
    modResult = await resp.json();
    
    document.getElementById('loading').classList.remove('show');
    document.getElementById('applyBtn').disabled = false;
    
    // Show summary
    const statsDiv = document.getElementById('summaryStats');
    const s = modResult.summary;
    statsDiv.innerHTML = `
        <div class="stat-card"><div class="label">Total Mass</div><div class="value">${s.total_mass} <span class="unit">kg</span></div></div>
        <div class="stat-card"><div class="label">Front Corner (sprung)</div><div class="value">${s.sprung_mass_f_corner} <span class="unit">kg</span></div></div>
        <div class="stat-card"><div class="label">Rear Corner (sprung)</div><div class="value">${s.sprung_mass_r_corner} <span class="unit">kg</span></div></div>
        <div class="stat-card"><div class="label">Natural Freq (F/R)</div><div class="value">${s.natural_freq_f} / ${s.natural_freq_r} <span class="unit">Hz</span></div></div>
        <div class="stat-card"><div class="label">Hub Mass (F)</div><div class="value">${s.hub_mass_f} <span class="unit">kg</span></div></div>
        <div class="stat-card"><div class="label">Hub Mass (R)</div><div class="value">${s.hub_mass_r} <span class="unit">kg</span></div></div>
    `;
    
    // Show changes log
    const log = document.getElementById('log');
    log.innerHTML = '';
    for (const [file, sections] of Object.entries(modResult.changes)) {
        log.innerHTML += `<div class="line" style="color:#ffa500;font-weight:bold;">📄 ${file}</div>`;
        for (const [section, values] of Object.entries(sections)) {
            log.innerHTML += `<div class="line info">  [${section}]</div>`;
            for (const [key, val] of Object.entries(values)) {
                const oldVal = modResult.old_values?.[file]?.[section]?.[key];
                const oldStr = oldVal !== undefined ? ` (was: ${oldVal})` : '';
                log.innerHTML += `<div class="line ok">    ${key} = ${val}${oldStr}</div>`;
            }
        }
    }
    
    document.getElementById('results').style.display = 'block';
}

async function downloadZip() {
    window.location.href = '/download?class_key=' + selectedClass;
}
</script>
</body>
</html>"""

@app.route('/')
def index():
    # Inject class presets as JSON
    classes_json = {k: {"label": v["label"], "hp_range": v["hp_range"], "max_angle": v["max_angle"]} 
                    for k, v in CLASS_PRESETS.items()}
    html = HTML.replace('CLASSES_JSON', json.dumps(classes_json))
    return html

@app.route('/upload', methods=['POST'])
def upload():
    files = request.files.getlist('files')
    if not files:
        return jsonify({"error": "No files uploaded"})
    
    # Clear old uploads
    upload_dir = os.path.join(UPLOAD_DIR, "current")
    if os.path.exists(upload_dir):
        shutil.rmtree(upload_dir)
    os.makedirs(upload_dir)
    
    saved = []
    for f in files:
        # Get just the filename (strip directory paths)
        name = os.path.basename(f.filename)
        path = os.path.join(upload_dir, name)
        f.save(path)
        saved.append(name)
    
    # Parse files
    parsed = {}
    for name in saved:
        path = os.path.join(upload_dir, name)
        try:
            parsed[name] = parse_ini_file(path)
        except Exception as e:
            parsed[name] = {"_error": str(e)}
    
    # Try to detect car
    car_name = "Unknown Car"
    stats_html = ""
    
    # Look for car.ini
    car_ini = None
    for name in saved:
        if name.lower().endswith("car.ini"):
            car_ini = parsed.get(name, {})
            break
    
    if car_ini:
        basic = car_ini.get("BASIC", car_ini.get("basic", {}))
        mass = get_value(basic, "TOTALMASS", "?")
        
        # Try to get screen name
        header = car_ini.get("HEADER", car_ini.get("header", {}))
        screen_name = header.get("SCREEN_NAME", header.get("screen_name", ""))
        if isinstance(screen_name, dict):
            screen_name = screen_name.get("raw", "")
        
        if screen_name:
            car_name = screen_name
        
        stats_parts = [f"Mass: {mass}kg"]
        
        # Check for suspension type
        for name in saved:
            if "suspension" in name.lower():
                susp = parsed.get(name, {})
                front = susp.get("FRONT", susp.get("front", {}))
                susp_type = front.get("TYPE", front.get("type", "?"))
                if isinstance(susp_type, dict):
                    susp_type = susp_type.get("raw", "?")
                stats_parts.append(f"Suspension: {susp_type}")
                break
        
        stats_html = " · ".join(stats_parts)
    
    # Store parsed data in a temp file for later
    with open(os.path.join(UPLOAD_DIR, "parsed.json"), "w") as f:
        # Convert parsed data to serializable format
        serializable = {}
        for fname, data in parsed.items():
            serializable[fname] = {}
            for section, values in data.items():
                serializable[fname][section] = {}
                for k, v in values.items():
                    if isinstance(v, dict):
                        serializable[fname][section][k] = v.get("value", v.get("raw", str(v)))
                    else:
                        serializable[fname][section][k] = v
        json.dump(serializable, f)
    
    return jsonify({
        "files": saved,
        "car_name": car_name,
        "stats_html": stats_html,
    })


@app.route('/modify', methods=['POST'])
def modify():
    data = request.get_json()
    class_key = data.get("class_key")
    
    if class_key not in CLASS_PRESETS:
        return jsonify({"error": f"Unknown class: {class_key}"})
    
    # Load parsed files
    parsed_path = os.path.join(UPLOAD_DIR, "parsed.json")
    if not os.path.exists(parsed_path):
        return jsonify({"error": "No files uploaded yet"})
    
    with open(parsed_path) as f:
        parsed = json.load(f)
    
    # Find car.ini regardless of prefix
    car_ini_data = {}
    for fname, data in parsed.items():
        if fname.lower().endswith("car.ini"):
            car_ini_data = data
            break
    
    # Run modifier
    result = modify_car({"car.ini": car_ini_data}, class_key)
    
    # Collect old values for comparison
    old_values = {}
    for fname, sections in result["changes"].items():
        old_values[fname] = {}
        # Find matching uploaded file
        for uploaded_name, uploaded_data in parsed.items():
            if fname.split(".")[0].lower() in uploaded_name.lower():
                for section, values in sections.items():
                    old_values[fname][section] = {}
                    uploaded_section = uploaded_data.get(section, {})
                    for key in values:
                        old_val = uploaded_section.get(key, uploaded_section.get(key.upper(), uploaded_section.get(key.lower())))
                        if old_val is not None:
                            if isinstance(old_val, dict):
                                old_val = old_val.get("value", old_val.get("raw"))
                            old_values[fname][section][key] = old_val
                break
    
    result["old_values"] = old_values
    return jsonify(result)


@app.route('/download')
def download():
    class_key = request.args.get('class_key')
    if not class_key or class_key not in CLASS_PRESETS:
        return "Bad class", 400
    
    # Load parsed files
    with open(os.path.join(UPLOAD_DIR, "parsed.json")) as f:
        parsed = json.load(f)
    
    car_ini_data = {}
    for fname, data in parsed.items():
        if fname.lower().endswith("car.ini"):
            car_ini_data = data
            break
    
    result = modify_car({"car.ini": car_ini_data}, class_key)
    
    # Read original files and apply modifications
    upload_dir = os.path.join(UPLOAD_DIR, "current")
    
    # Create zip
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for fname in os.listdir(upload_dir):
            filepath = os.path.join(upload_dir, fname)
            
            # Check if we have modifications for this file
            modified = False
            for mod_fname, sections in result["changes"].items():
                if mod_fname.split(".")[0].lower() in fname.lower():
                    # Read original file and apply changes
                    with open(filepath, 'r') as f:
                        content = f.read()
                    
                    # Apply each change by finding [SECTION] and KEY= lines
                    for section, values in sections.items():
                        for key, new_val in values.items():
                            # Find the key in the file and replace its value
                            import re
                            # Look for key=value pattern (case insensitive)
                            pattern = rf'((?:^|\n)\s*{re.escape(key)}\s*=)\s*[^\n;]*'
                            replacement = rf'\g<1>{new_val}'
                            new_content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
                            if new_content != content:
                                content = new_content
                            else:
                                # Key not found — append to end of relevant section
                                section_pattern = rf'(\[{re.escape(section)}\][^\[]*)'
                                def append_key(m):
                                    return m.group(0).rstrip() + f'\n{key}={new_val}\n'
                                content = re.sub(section_pattern, append_key, content, count=1, flags=re.IGNORECASE)
                    
                    zf.writestr(f"data/{fname}", content)
                    modified = True
                    break
            
            if not modified:
                # Copy unmodified
                zf.write(filepath, f"data/{fname}")
    
    zip_buffer.seek(0)
    preset = CLASS_PRESETS[class_key]
    return send_file(zip_buffer, mimetype='application/zip',
                     as_attachment=True,
                     download_name=f"RealiSimHQ_{preset['label'].replace(' ', '_')}_physics.zip")


if __name__ == '__main__':
    print("🏎️  RealiSimHQ Physics Tool")
    print("   http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
