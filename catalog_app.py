#!/usr/bin/env python3
"""Generate a sleek single-file HTML catalog for RealiSimHQ content."""
import csv, json, os, re, base64
from collections import defaultdict

CATALOG_DIR = os.path.join(os.path.dirname(__file__), 'catalog')
GDRIVE_LINK = "https://drive.google.com/file/d/{}/view?usp=drive_link"

# Load Drive file ID mappings
def load_drive_ids():
    ids = {}
    for path in ['/tmp/car_ids.json', '/tmp/track_ids.json', '/tmp/track_ids2.json']:
        if os.path.exists(path):
            with open(path) as f:
                ids.update(json.load(f))
    return ids

DRIVE_IDS = load_drive_ids()

# Tracks that are misplaced in car folders (Initial D + RallyCross TRACKS subfolder)
MISPLACED_TRACK_NAMES = {
    'ek_akina', 'ek_irohazaka', 'pk_akina', 'pk_irohazaka', 'pk_usui_touge',
    'ac_gymkhana', 'rmi_sherbetland', 'yoshi_village', 'Monaco_Rallycross_DiRT3',
    'RX_blackwood', 'RX_holjes', 'RX_shibuya', 'battersea', 'hell_rallyx',
    'rmi_dirt2_battersea', 'tykkimaki_kouvola',
}

# Items to exclude from the car list entirely
EXCLUDED_CARS = {
    'Chase Bays x Grip Royal',  # parts pack, not a car
    'parts',  # generic parts entries
}

def parse_car_name(raw_name):
    name = raw_name
    prefix_found = ""
    for prefix in ['X10DD.Battle-', 'X10DD.Drift-', 'X10DD.Track-', 'X10DD.Street-', 'X10DD.Street+',
                   'X10DD.Rally-', 'X10DD.Grassroots-', 'X10DD.ProSpec-', 'X10DD.ProSpec+', 'X10DD.ProSpec.',
                   'X10DD.Muscle-', 'X10DD.Arch+', 'X10DD.Arch-', 'X10DD.FnF-',
                   'X10DD-', 'TAP-', 'TAProot-', 'USD-', 'IUSD-', 'LVL-', 'LVLGR8_', 'LVLRX_', 'LVLRX-',
                   'adl-proam-', 'adl_proam_', 'JDAM-', 'JDAM_', 'tdm_', 'tdm-',
                   'TANDEM-', 'TANDEM ', 'PDP_', '-Ai.5O-', '-AiO.Street-', 'LAWD-',
                   'LVL-240_55Deg-', 'LVL-240_50Deg-', 'LVL-250_50Deg-', 'LVL420-']:
        if name.startswith(prefix):
            prefix_found = prefix.rstrip('-_. ')
            name = name[len(prefix):]
            break
    
    makes = {
        'BMW': ['BMW', 'bmw', 'E46', 'E36', 'E30', 'E92', 'M3', 'M2', 'M4', '1M', 'F22', 'G82', 'G87', 'Eurofighter'],
        'Nissan': ['Nissan', 'nissan', 'Silvia', 'Sil80', 'Skyline', '180SX', '200SX', '240SX', '350Z', '350z', '370Z', '370z', '300ZX', '300zx', '400z', 'S13', 'S14', 'S15', 'S12', 'R34', 'R32', 'R33', 'R31', 'PS13', 'Onevia', 'Laurel', 'Fairlady', 'Sentra'],
        'Toyota': ['Toyota', 'toyota', 'AE86', 'Supra', 'Trueno', 'Levin', 'GT86', 'GR86', 'GR_86', 'Chaser', 'Mark', 'Soarer', 'JZX', 'Corolla', 'Aristo', 'Altezza'],
        'Lexus': ['Lexus', 'lexus', 'IS300', 'SC300', 'RCF', 'GS300'],
        'Honda': ['Honda', 'honda', 'Civic', 'S2000', 'NSX', 'Integra', 'CRX', 'S600'],
        'Acura': ['Acura', 'acura', 'NSX'],
        'Mazda': ['Mazda', 'mazda', 'RX-7', 'RX7', 'RX_7', 'RX-8', 'Miata', 'MX-5', 'MX5'],
        'Chevrolet': ['Chevy', 'chevy', 'Chevrolet', 'Corvette', 'Chevelle', 'C6', 'C5', 'C4', 'C7', 'C8', 'Camaro', 'C10', 'Nova', 'Impala'],
        'Ford': ['Ford', 'ford', 'Mustang', 'RS200', 'Interceptor', 'Crown', 'Foxbody', 'Fox', 'Focus', 'Mavri'],
        'Subaru': ['Subaru', 'subaru', 'WRX', 'Impreza', 'BRZ'],
        'Mitsubishi': ['Mitsubishi', 'mitsubishi', 'Evo', 'Lancer', 'Eclipse'],
        'Dodge': ['Dodge', 'dodge', 'Charger', 'Challenger', 'Viper'],
        'Suzuki': ['Suzuki', 'suzuki', 'Cappuccino', 'Hayabusa', 'Swift', 'Skywave'],
        'Kawasaki': ['Kawasaki', 'kawasaki', 'ZX'],
        'Yamaha': ['Yamaha', 'yamaha'],
        'Lancia': ['Lancia', 'lancia', 'Delta'],
        'Peugeot': ['Peugeot', 'peugeot'],
        'Porsche': ['Porsche', 'porsche', '718', '964', '959'],
        'MG': ['MG', 'Metro'],
        'Volkswagen': ['VW', 'Volkswagen', 'Golf', 'Corrado', 'Jetta'],
        'Datsun': ['Datsun', 'datsun', '240Z', '260Z', '280Z'],
        'Hyundai': ['Hyundai', 'hyundai', 'Genesis'],
        'Infiniti': ['Infiniti', 'infiniti', 'G35'],
        'Cadillac': ['Cadillac', 'cadillac', 'XLR'],
        'Pontiac': ['Pontiac', 'pontiac', 'Solstice', 'Transam'],
        'Scion': ['Scion', 'scion', 'TC'],
        'Mercury': ['Mercury', 'mercury', 'Cougar'],
        'Buick': ['Buick', 'buick', 'GNX'],
        'Plymouth': ['Plymouth', 'plymouth', 'Barracuda', 'Road Runner'],
        'GMC': ['GMC', 'gmc', 'Syclone'],
        'Mercedes': ['Mercedes', 'mercedes', 'SL65'],
        'Lada': ['Lada', 'lada'],
        'Harley-Davidson': ['harley'],
    }
    
    detected_make = "Other"
    for make, keywords in makes.items():
        for kw in keywords:
            if kw.lower() in name.lower():
                detected_make = make
                break
        if detected_make != "Other":
            break
    
    model = name.replace('_', ' ').replace('-', ' ').strip()
    
    # Strip physics specs from model name (they're shown in the Physics column)
    # Remove degree/angle info like "55Deg", "50Deg"
    model = re.sub(r'\b\d+Deg\b', '', model)
    # Remove leading power numbers like "240 ", "250 ", "420 " when followed by a make/model word
    model = re.sub(r'^\d{2,3}\s+', '', model.strip())
    # Clean up extra spaces
    model = re.sub(r'\s+', ' ', model).strip()
    
    return detected_make, model

def clean_track_name(raw_name):
    """Clean track name: extract creator prefix, proper case, readable.
    
    Pattern: "90sgdsp_kazekaeshi_touge" -> "Kazekaeshi Touge [90sGDSP]"
    The creator/prefix tag goes in square brackets after the track name.
    """
    name = raw_name.strip('_').strip()
    
    # Known creator prefixes that appear at the start of track folder names
    creator_prefixes = {
        '90sgdsp': '90sGDSP',
        'ek': 'EK',
        'pk': 'PK',
        'rmi': 'RMI',
        'cnds': 'CNDS',
        'srs': 'SRS',
        'emj': 'EMJ',
        'bhs': 'BHS',
    }
    
    extracted_creator = None
    # Try to extract creator prefix (before first _ or -)
    for sep in ['_', '-']:
        if sep in name:
            prefix_part = name.split(sep, 1)[0].lower()
            if prefix_part in creator_prefixes:
                extracted_creator = creator_prefixes[prefix_part]
                name = name.split(sep, 1)[1]
                break
    
    name = name.replace('_', ' ').replace('-', ' ').strip()
    # Fix double spaces
    name = re.sub(r'\s+', ' ', name)
    # Title case words that are all lower
    words = name.split()
    result = []
    preserve_upper = {'X10DD', 'HQ', 'RD', 'NC', 'TX', 'UK', 'FD', 'DCGP', 'DMEC', 'DSC', 'ADL',
                      'NOLA', 'ESDA', 'VDC', 'SCS', 'EMJ', 'FREE', 'USA', 'RX', 'II', 'III', 'IV',
                      'V2', 'RT', 'TANDEM', 'BHS', 'LZ', 'GRS', 'USA', 'DIRT3', 'CNDS', 'RX7'}
    for w in words:
        if w.upper() in preserve_upper:
            result.append(w.upper())
        elif w.islower() and len(w) > 2:
            result.append(w.capitalize())
        else:
            result.append(w)
    
    clean = ' '.join(result)
    
    # Append creator tag in brackets if found
    if extracted_creator:
        clean = f"{clean} [{extracted_creator}]"
    
    return clean

def classify_track(name, subcategory, category):
    """Classify track into Freeroam / Touge / Circuit / Competition."""
    n = name.lower()
    sub = (subcategory or '').lower()
    cat = (category or '').lower()
    
    if 'touge' in sub:
        return 'Touge'
    if 'competition' in sub or 'formula drift' in sub or 'dcgp' in sub:
        return 'Competition'
    if 'circuit' in sub:
        return 'Circuit'
    if 'road open world' in sub or 'freeroam' in sub:
        return 'Freeroam'
    
    freeroam_kw = ['freeroam', 'free roam', 'open world', 'la_canyons', 'la canyons', 'canyons', 'shuto', 'nihon_turismo', 'nihon turismo',
                   'interstate raceway', 'gymkhana', 'playground', 'daikoku', 'tuning lot', 'parking',
                   'forest paradise', 'houston_police', 'houston police']
    touge_kw = ['touge', 'switchback', 'dragon', 'akina', 'irohazaka', 'usui', 'happogahara', 'myogi',
                'akagi', 'momiji', 'nagao', 'nanamagari', 'sadamine', 'tsuchisaka', 'shomaru', 'tianmen',
                'blue ridge', 'appalachia', 'smokey', 'smokies', 'pisgah', 'shigemo', 'makime', 'ikawa',
                'tsuru', 'fruit', 'even flow', 'bravo', 'curva', 'tanemachi', 'knockin', 'ogasayama',
                'kazekaeshi', 'ebisu touge']
    competition_kw = ['dmec', 'formula drift', 'fd ', 'fd_', 'englishtown', 'irwindale', 'long beach',
                      'longbeach', 'nola', 'sebring', 'suzuka', 'usair', 'raceway', 'dcgp', 'barbagallo',
                      'yas_marina', 'yas marina', 'bikernieki', 'ferropolis', 'motoarena', 'chang_2023',
                      'chang 2023', 'plock', 'dsc_', 'dsc ', 'soldier field', 'ozarks']
    circuit_kw = ['circuit', 'park', 'docks', 'kunitomi', 'nikko', 'tamworth', 'klutch', 'ebisu_north',
                  'ebisu north', 'ebisu_minami', 'ebisu minami', 'limerock', 'driftpark', 'drift_track',
                  'drift track', 'grange', 'bihoku', 'meihan', 'compound', 'shadowvalley', 'shadow valley',
                  'sunrise', 'tykkimaki', 'tykkimaen', 'kouvola', 'flatbottom', 'clotkart', 'caffine',
                  'momentum', 'tandem', 'doors', 'feint', 'battersea', 'holjes', 'shibuya', 'hell rally',
                  'monaco', 'sherbet', 'yoshi', 'blackwood', 'zen track', 'pump track', 'playground']
    
    for kw in freeroam_kw:
        if kw in n:
            return 'Freeroam'
    for kw in touge_kw:
        if kw in n:
            return 'Touge'
    for kw in competition_kw:
        if kw in n:
            return 'Competition'
    for kw in circuit_kw:
        if kw in n:
            return 'Circuit'
    
    if 'touge' in cat:
        return 'Touge'
    if 'rallycross' in cat.lower():
        return 'Circuit'
    
    return 'Circuit'

def is_x10dd_edition(name, category, filename):
    """Check if track is an X10DD edition."""
    n = (name + ' ' + (category or '') + ' ' + (filename or '')).lower()
    return 'x10dd' in n

def load_data():
    cars = []
    misplaced_tracks = []  # tracks found in car CSV
    
    with open(os.path.join(CATALOG_DIR, 'cars.csv')) as f:
        for row in csv.DictReader(f):
            name = row['Name']
            cat = row['Category']
            subcat = row.get('Subcategory', '') or ''
            
            if not cat:
                # Skip entries with no category (like root parts.7z)
                continue
            
            # Skip excluded items
            if name in EXCLUDED_CARS:
                continue
            
            # Check if this is a misplaced track
            if name in MISPLACED_TRACK_NAMES or 'TRACKS' in subcat.upper() or 'Tracks X10DD' in subcat:
                file_id = DRIVE_IDS.get(row['Filename'], '')
                misplaced_tracks.append({
                    'name': name,
                    'category': cat,
                    'subcategory': subcat,
                    'size': round(float(row['Size (MB)']) if row['Size (MB)'] else 0, 1),
                    'file': row['Filename'],
                    'link': GDRIVE_LINK.format(file_id) if file_id else '',
                })
                continue
            
            make, model = parse_car_name(name)
            file_id = DRIVE_IDS.get(row['Filename'], '')
            cars.append({
                'name': name,
                'make': make,
                'model': model,
                'pack': cat,
                'physics': subcat,
                'size': round(float(row['Size (MB)']) if row['Size (MB)'] else 0, 1),
                'file': row['Filename'],
                'link': GDRIVE_LINK.format(file_id) if file_id else '',
            })
    
    # Load tracks from track CSVs + misplaced tracks from car CSV
    tracks = []
    seen_keys = set()  # for dedup by cleaned name + filename
    
    # First pass: collect all tracks from all sources
    all_raw_tracks = []
    
    for csv_file in ['tracks_ac_folder.csv', 'tracks_released.csv']:
        path = os.path.join(CATALOG_DIR, csv_file)
        if not os.path.exists(path):
            continue
        with open(path) as f:
            for row in csv.DictReader(f):
                file_id = DRIVE_IDS.get(row['Filename'], '')
                all_raw_tracks.append({
                    'raw_name': row['Name'],
                    'category': row.get('Category', '') or '',
                    'subcategory': row.get('Subcategory', '') or '',
                    'size': round(float(row['Size (MB)']) if row['Size (MB)'] else 0, 1),
                    'file': row['Filename'],
                    'link': GDRIVE_LINK.format(file_id) if file_id else '',
                    'source': csv_file,
                })
    
    # Add misplaced tracks from car folders
    for mt in misplaced_tracks:
        all_raw_tracks.append({
            'raw_name': mt['name'],
            'category': mt.get('category', ''),
            'subcategory': mt.get('subcategory', ''),
            'size': mt['size'],
            'file': mt['file'],
            'link': mt['link'],
            'source': 'car_folder',
        })
    
    # Deduplicate: prefer X10DD editions > RealSim HQ > Patreon > Free Versions > car_folder
    source_priority = {
        'X10DD Editions': 1,
        'RealSim HQ': 2,
        'Patreon Touge': 3,
        'Patreon Weekly': 4,
        'Free Versions RD': 5,
        'Zen Track Packs': 6,
        'Patreon Free': 7,
        'Patreon Only': 8,
    }
    
    # Group by filename for dedup
    by_filename = defaultdict(list)
    for t in all_raw_tracks:
        by_filename[t['file']].append(t)
    
    # Also group by cleaned name for further dedup
    by_clean_name = defaultdict(list)
    for t in all_raw_tracks:
        cn = clean_track_name(t['raw_name']).lower().strip()
        by_clean_name[cn].append(t)
    
    # Pick best version per filename
    deduped_by_file = {}
    for fname, entries in by_filename.items():
        best = min(entries, key=lambda e: source_priority.get(e['category'], 99))
        deduped_by_file[fname] = best
    
    # Now deduplicate by cleaned name (different filenames but same track)
    seen_clean = set()
    final_tracks = []
    
    for t in sorted(deduped_by_file.values(), key=lambda x: source_priority.get(x['category'], 99)):
        cn = clean_track_name(t['raw_name']).lower().strip()
        # For exact-name dupes, keep the higher priority one
        # But allow tracks with different actual content (e.g. X10DD vs original)
        dedup_key = t['file']  # unique by file
        if dedup_key in seen_clean:
            continue
        seen_clean.add(dedup_key)
        final_tracks.append(t)
    
    # Now build track objects with cleaned names and detect duplicates for disambiguation
    name_count = defaultdict(list)
    for t in final_tracks:
        cn = clean_track_name(t['raw_name'])
        name_count[cn].append(t)
    
    for t in final_tracks:
        cn = clean_track_name(t['raw_name'])
        x10dd = is_x10dd_edition(t['raw_name'], t['category'], t['file'])
        
        display_name = cn
        
        # Add (SurfaceFX) badge for X10DD editions
        if x10dd and 'surfacefx' not in display_name.lower():
            display_name = display_name + ' (SurfaceFX)'
        
        # Disambiguate duplicate names
        dupes = name_count[cn]
        if len(dupes) > 1:
            # Add source prefix for disambiguation
            src = t['category'] or t['source']
            if src and src != cn:
                short_src = src.replace('Free Versions RD', 'Free').replace('Patreon Weekly', 'Patreon').replace('Patreon Touge', 'Patreon').replace('X10DD Editions', 'X10DD').replace('RealSim HQ', 'HQ').replace('car_folder', 'Alt')
                sub = t.get('subcategory', '')
                if sub and 'Test' in sub:
                    short_src += ' Test'
                if not x10dd:  # already has SurfaceFX badge
                    display_name = f"{cn} ({short_src})"
        
        track_type = classify_track(t['raw_name'], t.get('subcategory', ''), t.get('category', ''))
        
        tracks.append({
            'name': display_name,
            'raw_name': t['raw_name'],
            'category': t.get('category', '') or 'Original',
            'type': track_type,
            'x10dd': x10dd,
            'size': t['size'],
            'file': t['file'],
            'link': t['link'],
        })
    
    return cars, tracks

def get_logo_data_uri():
    logo_path = os.path.join(os.path.dirname(__file__), 'realisimhq-ad.jpg')
    if os.path.exists(logo_path):
        with open(logo_path, 'rb') as f:
            data = base64.b64encode(f.read()).decode()
        return f"data:image/jpeg;base64,{data}"
    return ""

def main():
    cars, tracks = load_data()
    
    makes = sorted(set(c['make'] for c in cars))
    packs = sorted(set(c['pack'] for c in cars))
    physics_types = sorted(set(c['physics'] for c in cars if c['physics']))
    track_cats = sorted(set(t['category'] for t in tracks))
    track_types = ['Freeroam', 'Touge', 'Circuit', 'Competition']
    
    # Pack stats
    pack_stats = defaultdict(lambda: {'count': 0, 'size': 0, 'cars': [], 'physics': set()})
    for c in cars:
        pack_stats[c['pack']]['count'] += 1
        pack_stats[c['pack']]['size'] += c['size']
        pack_stats[c['pack']]['cars'].append(c)
        if c['physics']:
            pack_stats[c['pack']]['physics'].add(c['physics'])
    
    total_size_gb = (sum(c['size'] for c in cars) + sum(t['size'] for t in tracks)) / 1024

    # Parts pack info (for pinned required download)
    parts_id = DRIVE_IDS.get('parts.7z', '')
    parts_link = GDRIVE_LINK.format(parts_id) if parts_id else '#'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RealiSimHQ Content Catalog</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;600&display=swap');

* {{ margin:0; padding:0; box-sizing:border-box; }}

:root {{
  --bg: #0a0a1a;
  --surface: #12122a;
  --surface2: #1a1a3e;
  --surface3: #222255;
  --cyan: #00f0ff;
  --pink: #ff2d75;
  --gold: #ffd700;
  --orange: #ff8c00;
  --green: #00ff88;
  --purple: #b44dff;
  --red: #ff4444;
  --text: #e8e8f0;
  --text2: #8888aa;
  --border: #2a2a55;
  --glow: 0 0 20px rgba(0, 240, 255, 0.15);
}}

body {{
  font-family: 'Inter', -apple-system, sans-serif;
  background: var(--bg);
  color: var(--text);
  min-height: 100vh;
  overflow-x: hidden;
}}

body::before {{
  content: '';
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: 
    radial-gradient(ellipse at 20% 50%, rgba(0, 240, 255, 0.03) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 20%, rgba(255, 45, 117, 0.03) 0%, transparent 50%),
    radial-gradient(ellipse at 50% 80%, rgba(180, 77, 255, 0.02) 0%, transparent 50%);
  pointer-events: none;
  z-index: 0;
}}

.container {{ max-width: 1400px; margin: 0 auto; padding: 0 24px; position: relative; z-index: 1; }}

/* HERO */
.hero {{
  text-align: center;
  padding: 40px 0 30px;
}}
.hero-logo {{
  max-width: 320px;
  height: auto;
  margin-bottom: 16px;
  border-radius: 12px;
  filter: drop-shadow(0 0 30px rgba(0, 240, 255, 0.2));
}}
.hero h1 {{
  font-size: 3.2rem;
  font-weight: 900;
  background: linear-gradient(135deg, var(--cyan), var(--pink));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -1px;
  margin-bottom: 8px;
}}
.hero .sub {{
  font-size: 1.1rem;
  color: var(--text2);
  font-weight: 300;
  letter-spacing: 4px;
  text-transform: uppercase;
}}

/* STATS BAR */
.stats {{
  display: flex;
  justify-content: center;
  gap: 40px;
  margin: 30px 0 40px;
  flex-wrap: wrap;
}}
.stat {{
  text-align: center;
  padding: 20px 30px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  min-width: 150px;
  transition: all 0.3s;
}}
.stat:hover {{
  border-color: var(--cyan);
  box-shadow: var(--glow);
  transform: translateY(-2px);
}}
.stat .num {{
  font-size: 2.4rem;
  font-weight: 800;
  font-family: 'JetBrains Mono', monospace;
}}
.stat:nth-child(1) .num {{ color: var(--cyan); }}
.stat:nth-child(2) .num {{ color: var(--pink); }}
.stat:nth-child(3) .num {{ color: var(--gold); }}
.stat:nth-child(4) .num {{ color: var(--green); }}
.stat .label {{ color: var(--text2); font-size: 0.85rem; margin-top: 4px; text-transform: uppercase; letter-spacing: 2px; }}

/* TABS */
.tabs {{
  display: flex;
  gap: 4px;
  margin-bottom: 24px;
  border-bottom: 2px solid var(--border);
  padding-bottom: 0;
}}
.tab {{
  padding: 12px 28px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.95rem;
  color: var(--text2);
  border-bottom: 3px solid transparent;
  transition: all 0.2s;
  user-select: none;
  letter-spacing: 0.5px;
}}
.tab:hover {{ color: var(--text); }}
.tab.active {{
  color: var(--cyan);
  border-bottom-color: var(--cyan);
}}
.tab .count {{
  font-size: 0.75rem;
  background: var(--surface2);
  padding: 2px 8px;
  border-radius: 10px;
  margin-left: 8px;
  font-family: 'JetBrains Mono', monospace;
}}
.tab.active .count {{ background: rgba(0,240,255,0.15); color: var(--cyan); }}

/* FILTERS */
.filters {{
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  flex-wrap: wrap;
  align-items: center;
}}
.search {{
  flex: 1;
  min-width: 250px;
  padding: 12px 20px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  color: var(--text);
  font-size: 0.95rem;
  font-family: 'Inter', sans-serif;
  outline: none;
  transition: all 0.2s;
}}
.search:focus {{
  border-color: var(--cyan);
  box-shadow: 0 0 0 3px rgba(0,240,255,0.1);
}}
.search::placeholder {{ color: var(--text2); }}

select {{
  padding: 12px 16px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  color: var(--text);
  font-size: 0.9rem;
  font-family: 'Inter', sans-serif;
  outline: none;
  cursor: pointer;
  min-width: 160px;
  transition: all 0.2s;
  -webkit-appearance: none;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath d='M6 8L1 3h10z' fill='%238888aa'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  padding-right: 32px;
}}
select:focus {{ border-color: var(--cyan); }}

.filter-count {{
  color: var(--text2);
  font-size: 0.85rem;
  font-family: 'JetBrains Mono', monospace;
  padding: 8px 16px;
  background: var(--surface);
  border-radius: 10px;
}}

/* REQUIRED DOWNLOAD BANNER */
.required-download {{
  background: linear-gradient(135deg, rgba(255, 215, 0, 0.1), rgba(255, 140, 0, 0.08));
  border: 2px solid var(--gold);
  border-radius: 16px;
  padding: 20px 28px;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
  box-shadow: 0 0 30px rgba(255, 215, 0, 0.08);
}}
.required-download .req-icon {{
  font-size: 2rem;
}}
.required-download .req-info {{
  flex: 1;
}}
.required-download .req-info h3 {{
  color: var(--gold);
  font-size: 1.1rem;
  margin-bottom: 4px;
}}
.required-download .req-info p {{
  color: var(--text2);
  font-size: 0.9rem;
}}
.required-download .req-badge {{
  background: var(--gold);
  color: var(--bg);
  padding: 3px 10px;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 800;
  letter-spacing: 1px;
  text-transform: uppercase;
  margin-left: 8px;
}}
.dl-btn {{
  display: inline-block;
  padding: 12px 28px;
  background: linear-gradient(135deg, var(--gold), var(--orange));
  color: var(--bg);
  font-weight: 700;
  font-size: 0.9rem;
  border-radius: 12px;
  text-decoration: none;
  transition: all 0.2s;
  letter-spacing: 0.5px;
  white-space: nowrap;
}}
.dl-btn:hover {{
  transform: scale(1.05);
  box-shadow: 0 0 20px rgba(255, 215, 0, 0.3);
}}

/* TABLE */
.table-wrap {{
  background: var(--surface);
  border-radius: 16px;
  border: 1px solid var(--border);
  overflow: hidden;
  margin-bottom: 60px;
}}
table {{ width: 100%; border-collapse: collapse; }}
thead th {{
  padding: 14px 16px;
  text-align: left;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 2px;
  color: var(--text2);
  background: var(--surface2);
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
  position: sticky;
  top: 0;
  z-index: 10;
}}
thead th:hover {{ color: var(--cyan); }}
thead th .arrow {{ margin-left: 4px; opacity: 0.5; }}
thead th.sorted .arrow {{ opacity: 1; color: var(--cyan); }}

tbody tr {{
  border-bottom: 1px solid rgba(42, 42, 85, 0.5);
  transition: background 0.15s;
}}
tbody tr:hover {{ background: rgba(0, 240, 255, 0.04); }}
tbody tr:nth-child(even) {{ background: rgba(26, 26, 62, 0.3); }}
tbody tr:nth-child(even):hover {{ background: rgba(0, 240, 255, 0.06); }}

td {{
  padding: 12px 16px;
  font-size: 0.92rem;
}}
td.make {{
  font-weight: 600;
  color: var(--cyan);
}}
td.model {{
  color: var(--text);
  text-align: right;
}}
td.pack {{
  font-size: 0.8rem;
  padding: 4px 10px;
}}
.pack-badge {{
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.5px;
}}
.pack-X10DD {{ background: rgba(0,240,255,0.12); color: var(--cyan); }}
.pack-LEVEL {{ background: rgba(0,255,136,0.12); color: var(--green); }}
.pack-TANDEM {{ background: rgba(255,45,117,0.12); color: var(--pink); }}
.pack-RallyCross {{ background: rgba(255,140,0,0.12); color: var(--orange); }}
.pack-TAP {{ background: rgba(255,215,0,0.12); color: var(--gold); }}
.pack-ADL {{ background: rgba(180,77,255,0.12); color: var(--purple); }}
.pack-InitialD {{ background: rgba(255,45,117,0.12); color: var(--pink); }}
.pack-JDAM {{ background: rgba(255,140,0,0.12); color: var(--orange); }}
.pack-default {{ background: rgba(136,136,170,0.12); color: var(--text2); }}

.sfx-badge {{
  display: inline-block;
  padding: 2px 8px;
  border-radius: 8px;
  font-size: 0.7rem;
  font-weight: 700;
  background: rgba(0, 240, 255, 0.15);
  color: var(--cyan);
  margin-left: 6px;
  letter-spacing: 0.5px;
}}

td.physics {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  color: var(--green);
}}
td.size {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  color: var(--text2);
  text-align: right;
}}
td.model a:hover {{
  color: var(--cyan) !important;
  border-bottom-color: var(--cyan) !important;
}}
td.model a::after {{
  content: ' ↗';
  font-size: 0.7rem;
  opacity: 0.4;
}}
td.model a:hover::after {{
  opacity: 1;
  color: var(--cyan);
}}

/* SERVERS */
.servers {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
  margin-bottom: 60px;
}}
.server-card {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 24px;
  transition: all 0.3s;
  position: relative;
  overflow: hidden;
}}
.server-card::before {{
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
}}
.server-card:nth-child(1)::before {{ background: linear-gradient(90deg, var(--cyan), var(--purple)); }}
.server-card:nth-child(2)::before {{ background: linear-gradient(90deg, var(--orange), var(--gold)); }}
.server-card:nth-child(3)::before {{ background: linear-gradient(90deg, var(--pink), var(--orange)); }}
.server-card:nth-child(4)::before {{ background: linear-gradient(90deg, var(--green), var(--cyan)); }}

.server-card:hover {{
  border-color: var(--cyan);
  box-shadow: var(--glow);
  transform: translateY(-3px);
}}
.server-card h3 {{
  font-size: 1.2rem;
  margin-bottom: 4px;
}}
.server-card .theme {{
  color: var(--text2);
  font-size: 0.85rem;
  margin-bottom: 16px;
}}
.server-card .meta {{
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}}
.server-card .meta span {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  padding: 4px 10px;
  background: var(--surface2);
  border-radius: 8px;
  color: var(--text2);
}}
.server-live {{
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: var(--surface2);
  border-radius: 10px;
  font-size: 0.85rem;
}}
.server-live .live-dot {{
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--green);
  animation: pulse 2s infinite;
}}
.server-live.offline .live-dot {{
  background: var(--text2);
  animation: none;
}}
@keyframes pulse {{
  0%, 100% {{ opacity: 1; }}
  50% {{ opacity: 0.4; }}
}}
.server-live .player-count {{
  font-family: 'JetBrains Mono', monospace;
  color: var(--green);
  font-weight: 600;
}}
.server-live .current-track {{
  color: var(--text2);
  font-size: 0.8rem;
  margin-left: auto;
  max-width: 160px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}}
.server-card .features {{
  font-size: 0.85rem;
  color: var(--text2);
  margin-bottom: 16px;
  line-height: 1.6;
}}
.join-btn {{
  display: inline-block;
  padding: 10px 24px;
  background: linear-gradient(135deg, var(--cyan), var(--purple));
  color: var(--bg);
  font-weight: 700;
  font-size: 0.85rem;
  border-radius: 10px;
  text-decoration: none;
  transition: all 0.2s;
  letter-spacing: 0.5px;
}}
.join-btn:hover {{
  transform: scale(1.05);
  box-shadow: 0 0 20px rgba(0, 240, 255, 0.3);
}}

/* PACK CARDS - uniform blocks with expandable car lists */
.packs {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 20px;
  margin-bottom: 60px;
}}
.pack-card {{
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 14px;
  padding: 24px;
  transition: all 0.3s;
  display: flex;
  flex-direction: column;
}}
.pack-card:hover {{
  border-color: var(--cyan);
  transform: translateY(-2px);
}}
.pack-card .pack-header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}}
.pack-card h4 {{ font-size: 1.05rem; }}
.pack-card .pack-stats {{ display: flex; gap: 16px; margin-bottom: 12px; }}
.pack-card .pack-stats span {{
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  color: var(--text2);
}}
.pack-card .pack-stats .n {{ color: var(--cyan); font-weight: 600; }}
.pack-expand-btn {{
  background: var(--surface2);
  border: 1px solid var(--border);
  color: var(--text2);
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.82rem;
  font-family: 'Inter', sans-serif;
  transition: all 0.2s;
  width: 100%;
  text-align: center;
}}
.pack-expand-btn:hover {{
  border-color: var(--cyan);
  color: var(--cyan);
}}
.pack-car-list {{
  display: none;
  margin-top: 12px;
  max-height: 300px;
  overflow-y: auto;
  border-top: 1px solid var(--border);
  padding-top: 8px;
}}
.pack-car-list.open {{ display: block; }}
.pack-car-item {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  border-bottom: 1px solid rgba(42, 42, 85, 0.3);
  font-size: 0.85rem;
}}
.pack-car-item:last-child {{ border-bottom: none; }}
.pack-car-item .car-name {{ color: var(--text); }}
.pack-car-item .car-dl {{
  color: var(--cyan);
  text-decoration: none;
  font-size: 0.8rem;
  padding: 2px 10px;
  border: 1px solid var(--cyan);
  border-radius: 6px;
  transition: all 0.2s;
  white-space: nowrap;
}}
.pack-car-item .car-dl:hover {{
  background: rgba(0, 240, 255, 0.1);
}}

/* Panels */
.panel {{ display: none; }}
.panel.active {{ display: block; }}

/* Responsive */
@media (max-width: 768px) {{
  .hero h1 {{ font-size: 2rem; }}
  .hero-logo {{ max-width: 200px; }}
  .stats {{ gap: 12px; }}
  .stat {{ min-width: 120px; padding: 14px 18px; }}
  .stat .num {{ font-size: 1.6rem; }}
  .filters {{ flex-direction: column; }}
  .search {{ min-width: unset; }}
  td {{ padding: 8px 10px; font-size: 0.82rem; }}
  .required-download {{ flex-direction: column; text-align: center; }}
}}

::-webkit-scrollbar {{ width: 8px; }}
::-webkit-scrollbar-track {{ background: var(--bg); }}
::-webkit-scrollbar-thumb {{ background: var(--border); border-radius: 4px; }}
::-webkit-scrollbar-thumb:hover {{ background: var(--surface3); }}

.hidden {{ display: none !important; }}

footer {{
  text-align: center;
  padding: 40px 0;
  color: var(--text2);
  font-size: 0.85rem;
  border-top: 1px solid var(--border);
}}
footer a {{ color: var(--cyan); text-decoration: none; }}
</style>
</head>
<body>

<div class="container">
  <div class="hero">
    <img src="realisimhq-ad.jpg" alt="RealiSimHQ" class="hero-logo" />
    <h1>RealiSimHQ</h1>
    <div class="sub">Assetto Corsa Content Catalog</div>
  </div>
  
  <div class="stats">
    <div class="stat"><div class="num">{len(cars)}</div><div class="label">Cars</div></div>
    <div class="stat"><div class="num">{len(tracks)}</div><div class="label">Tracks</div></div>
    <div class="stat"><div class="num">{len(packs)}</div><div class="label">Car Packs</div></div>
    <div class="stat"><div class="num">{total_size_gb:.0f} GB</div><div class="label">Total Content</div></div>
  </div>
  
  <div class="tabs">
    <div class="tab active" data-tab="cars">🏎️ Cars <span class="count">{len(cars)}</span></div>
    <div class="tab" data-tab="tracks">🏁 Tracks <span class="count">{len(tracks)}</span></div>
    <div class="tab" data-tab="packs">📦 Packs <span class="count">{len(packs)}</span></div>
    <div class="tab" data-tab="servers">🖥️ Servers <span class="count">4</span></div>
  </div>
  
  <!-- CARS -->
  <div class="panel active" id="panel-cars">
    <div class="required-download">
      <div class="req-icon">⚡</div>
      <div class="req-info">
        <h3>RealiSimHQ Rims and Parts <span class="req-badge">Required</span></h3>
        <p>This parts pack is required for all cars to display correctly. Download and install before adding cars.</p>
      </div>
      <a href="{parts_link}" target="_blank" class="dl-btn">⬇ DOWNLOAD PARTS PACK</a>
    </div>
    <div class="filters">
      <input type="text" class="search" id="car-search" placeholder="Search cars..." />
      <select id="filter-make"><option value="">All Makes</option>{"".join(f'<option value="{m}">{m}</option>' for m in makes)}</select>
      <select id="filter-pack"><option value="">All Packs</option>{"".join(f'<option value="{p}">{p}</option>' for p in packs)}</select>
      <select id="filter-physics"><option value="">All Physics</option>{"".join(f'<option value="{p}">{p}</option>' for p in physics_types)}</select>
      <span class="filter-count" id="car-count">{len(cars)} cars</span>
    </div>
    <div class="table-wrap">
      <table id="car-table">
        <thead><tr>
          <th data-sort="make">Make <span class="arrow">↕</span></th>
          <th data-sort="model" style="text-align:right">Model <span class="arrow">↕</span></th>
          <th data-sort="pack">Pack <span class="arrow">↕</span></th>
          <th data-sort="physics">Physics <span class="arrow">↕</span></th>
          <th data-sort="size" style="text-align:right">Size <span class="arrow">↕</span></th>
        </tr></thead>
        <tbody id="car-body"></tbody>
      </table>
    </div>
  </div>
  
  <!-- TRACKS -->
  <div class="panel" id="panel-tracks">
    <div class="filters">
      <input type="text" class="search" id="track-search" placeholder="Search tracks..." />
      <select id="filter-track-type"><option value="">All Types</option>{"".join(f'<option value="{t}">{t}</option>' for t in track_types)}</select>
      <select id="filter-track-cat"><option value="">All Sources</option>{"".join(f'<option value="{c}">{c}</option>' for c in track_cats)}</select>
      <span class="filter-count" id="track-count">{len(tracks)} tracks</span>
    </div>
    <div class="table-wrap">
      <table id="track-table">
        <thead><tr>
          <th data-sort="name">Track Name <span class="arrow">↕</span></th>
          <th data-sort="type">Type <span class="arrow">↕</span></th>
          <th data-sort="category">Source <span class="arrow">↕</span></th>
          <th data-sort="size" style="text-align:right">Size (MB) <span class="arrow">↕</span></th>
        </tr></thead>
        <tbody id="track-body"></tbody>
      </table>
    </div>
  </div>
  
  <!-- PACKS -->
  <div class="panel" id="panel-packs">
    <div class="packs" id="packs-grid"></div>
  </div>
  
  <!-- SERVERS -->
  <div class="panel" id="panel-servers">
    <div class="servers" id="servers-grid"></div>
  </div>
  
  <footer>
    RealiSimHQ · Extended Physics · COSMIC Suspension · Built with 🐘
  </footer>
</div>

<script>
const CARS = {json.dumps(sorted(cars, key=lambda x: (x['make'], x['model'])), indent=None)};
const TRACKS = {json.dumps(sorted(tracks, key=lambda x: x['name']), indent=None)};

const SERVERS = [
  {{ name:"TAProot Circuit", theme:"Drift · 17 Track Rotation · Vote Every 90min", http:9001, tcp:10001, cars:6, track:"Klutch Kickers (Rotating)", features:"Extended Physics, COSMIC Suspension, VotingPreset, WeatherFX", link:"https://acstuff.club/s/q:race/online/join?ip=152.53.83.105&httpPort=9001" }},
  {{ name:"LA Canyons", theme:"Open World · AI Traffic · Cruising", http:9004, tcp:10004, cars:16, track:"LA Canyons", features:"AI Traffic, Open World, Extended Physics, JDM + Muscle + Bikes", link:"https://acstuff.club/s/q:race/online/join?ip=152.53.83.105&httpPort=9004" }},
  {{ name:"Initial D Battle", theme:"Touge · Japanese Street Racing", http:9006, tcp:9606, cars:13, track:"Akina / Irohazaka / Usui (Rotating)", features:"X10DD Battle Cars, Touge Tracks, Extended Physics", link:"https://acstuff.club/s/q:race/online/join?ip=152.53.83.105&httpPort=9006" }},
  {{ name:"RallyX Chaos Mode", theme:"Group B Legends · Hayabusa Mini Trucks", http:9008, tcp:9608, cars:11, track:"RallyCross Tracks (Rotating)", features:"Group B Rally, Mini Trucks, SurfaceFX, Gravel/Dirt", link:"https://acstuff.club/s/q:race/online/join?ip=152.53.83.105&httpPort=9008" }},
];

const API_HOST = "152.53.83.105";

function packClass(pack) {{
  if (pack.includes('X10DD')) return 'pack-X10DD';
  if (pack.includes('L.E.V.E.L') || pack.includes('LVL')) return 'pack-LEVEL';
  if (pack.includes('T.A.N.D.E.M') || pack.includes('TANDEM')) return 'pack-TANDEM';
  if (pack.includes('Rally')) return 'pack-RallyCross';
  if (pack.includes('TAP')) return 'pack-TAP';
  if (pack.includes('ADL')) return 'pack-ADL';
  if (pack.includes('Initial')) return 'pack-InitialD';
  if (pack.includes('JDAM')) return 'pack-JDAM';
  return 'pack-default';
}}

function renderCars(data) {{
  const tbody = document.getElementById('car-body');
  tbody.innerHTML = data.map(c => `
    <tr>
      <td class="make">${{c.make}}</td>
      <td class="model">${{c.link ? `<a href="${{c.link}}" target="_blank" style="color:var(--text);text-decoration:none;border-bottom:1px dashed var(--border)">${{c.model}}</a>` : c.model}}</td>
      <td class="pack"><span class="pack-badge ${{packClass(c.pack)}}">${{c.pack}}</span></td>
      <td class="physics">${{c.physics || '—'}}</td>
      <td class="size">${{c.size}} MB</td>
    </tr>
  `).join('');
  document.getElementById('car-count').textContent = data.length + ' cars';
}}

function trackTypeClass(type) {{
  const map = {{ 'Freeroam':'pack-LEVEL', 'Touge':'pack-X10DD', 'Circuit':'pack-TAP', 'Competition':'pack-TANDEM' }};
  return map[type] || 'pack-default';
}}

function renderTracks(data) {{
  const tbody = document.getElementById('track-body');
  tbody.innerHTML = data.map(t => {{
    let nameHtml = t.link ? `<a href="${{t.link}}" target="_blank" style="color:var(--text);text-decoration:none;border-bottom:1px dashed var(--border)">${{t.name}}</a>` : t.name;
    if (t.x10dd) nameHtml += ' <span class="sfx-badge">SurfaceFX</span>';
    return `
    <tr>
      <td class="model" style="text-align:left">${{nameHtml}}</td>
      <td class="pack"><span class="pack-badge ${{trackTypeClass(t.type)}}">${{t.type}}</span></td>
      <td class="pack"><span class="pack-badge pack-default">${{t.category}}</span></td>
      <td class="size">${{t.size}} MB</td>
    </tr>`;
  }}).join('');
  document.getElementById('track-count').textContent = data.length + ' tracks';
}}

function renderPacks() {{
  const packs = {{}};
  CARS.forEach(c => {{
    if (!packs[c.pack]) packs[c.pack] = {{ count: 0, size: 0, cars: [] }};
    packs[c.pack].count++;
    packs[c.pack].size += c.size;
    packs[c.pack].cars.push(c);
  }});
  
  const sorted = Object.entries(packs).sort((a,b) => b[1].count - a[1].count);
  document.getElementById('packs-grid').innerHTML = sorted.map(([name, data], idx) => {{
    const carItems = data.cars.map(c => `
      <div class="pack-car-item">
        <span class="car-name">${{c.model}}</span>
        ${{c.link ? `<a href="${{c.link}}" target="_blank" class="car-dl">⬇ DL</a>` : '<span style="color:var(--text2);font-size:0.8rem">—</span>'}}
      </div>
    `).join('');
    return `
    <div class="pack-card">
      <div class="pack-header">
        <h4><span class="pack-badge ${{packClass(name)}}">${{name}}</span></h4>
      </div>
      <div class="pack-stats">
        <span><span class="n">${{data.count}}</span> cars</span>
        <span><span class="n">${{(data.size/1024).toFixed(1)}}</span> GB</span>
      </div>
      <button class="pack-expand-btn" onclick="togglePack(this)">▶ Show Cars</button>
      <div class="pack-car-list" id="pack-list-${{idx}}">
        ${{carItems}}
      </div>
    </div>`;
  }}).join('');
}}

function togglePack(btn) {{
  const list = btn.nextElementSibling;
  const open = list.classList.toggle('open');
  btn.textContent = open ? '▼ Hide Cars' : '▶ Show Cars';
}}

function renderServers() {{
  document.getElementById('servers-grid').innerHTML = SERVERS.map(s => `
    <div class="server-card">
      <h3>${{s.name}}</h3>
      <div class="theme">${{s.theme}}</div>
      <div class="server-live">
        <span class="live-dot"></span>
        <span class="player-count">Online</span>
        <span class="current-track">🏁 ${{s.track}}</span>
      </div>
      <div class="meta">
        <span>HTTP :${{s.http}}</span>
        <span>TCP :${{s.tcp}}</span>
        <span>${{s.cars}} cars</span>
      </div>
      <div class="features">${{s.features}}</div>
      <p style="font-size:0.75rem;color:var(--text2);margin-bottom:12px;">Live player count available via Content Manager or direct connection.</p>
      <a href="${{s.link}}" target="_blank" class="join-btn">JOIN SERVER →</a>
    </div>
  `).join('');
}}

function filterCars() {{
  const q = document.getElementById('car-search').value.toLowerCase();
  const make = document.getElementById('filter-make').value;
  const pack = document.getElementById('filter-pack').value;
  const physics = document.getElementById('filter-physics').value;
  
  const filtered = CARS.filter(c => {{
    if (q && !c.make.toLowerCase().includes(q) && !c.model.toLowerCase().includes(q) && !c.name.toLowerCase().includes(q) && !c.pack.toLowerCase().includes(q)) return false;
    if (make && c.make !== make) return false;
    if (pack && c.pack !== pack) return false;
    if (physics && c.physics !== physics) return false;
    return true;
  }});
  renderCars(filtered);
}}

function filterTracks() {{
  const q = document.getElementById('track-search').value.toLowerCase();
  const type = document.getElementById('filter-track-type').value;
  const cat = document.getElementById('filter-track-cat').value;
  
  const filtered = TRACKS.filter(t => {{
    if (q && !t.name.toLowerCase().includes(q) && !t.category.toLowerCase().includes(q) && !t.type.toLowerCase().includes(q)) return false;
    if (type && t.type !== type) return false;
    if (cat && t.category !== cat) return false;
    return true;
  }});
  renderTracks(filtered);
}}

// Sorting
let sortState = {{}};
document.querySelectorAll('th[data-sort]').forEach(th => {{
  th.addEventListener('click', () => {{
    const key = th.dataset.sort;
    const table = th.closest('table');
    const isCarTable = table.id === 'car-table';
    const stateKey = table.id + key;
    
    sortState[stateKey] = sortState[stateKey] === 'asc' ? 'desc' : 'asc';
    const dir = sortState[stateKey] === 'asc' ? 1 : -1;
    
    table.querySelectorAll('th').forEach(t => t.classList.remove('sorted'));
    th.classList.add('sorted');
    
    const data = isCarTable ? CARS : TRACKS;
    data.sort((a,b) => {{
      let va = a[key], vb = b[key];
      if (key === 'size') return (va - vb) * dir;
      return String(va).localeCompare(String(vb)) * dir;
    }});
    
    if (isCarTable) filterCars();
    else filterTracks();
  }});
}});

// Tabs
document.querySelectorAll('.tab').forEach(tab => {{
  tab.addEventListener('click', () => {{
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    tab.classList.add('active');
    document.getElementById('panel-' + tab.dataset.tab).classList.add('active');
  }});
}});

document.getElementById('car-search').addEventListener('input', filterCars);
document.getElementById('filter-make').addEventListener('change', filterCars);
document.getElementById('filter-pack').addEventListener('change', filterCars);
document.getElementById('filter-physics').addEventListener('change', filterCars);
document.getElementById('track-search').addEventListener('input', filterTracks);
document.getElementById('filter-track-type').addEventListener('change', filterTracks);
document.getElementById('filter-track-cat').addEventListener('change', filterTracks);

// Init
renderCars(CARS);
renderTracks(TRACKS);
renderPacks();
renderServers();
</script>
</body>
</html>"""
    
    out = os.path.join(os.path.dirname(__file__), 'catalog.html')
    with open(out, 'w') as f:
        f.write(html)
    print(f"Generated: {out} ({len(html)//1024}KB)")

if __name__ == '__main__':
    main()
