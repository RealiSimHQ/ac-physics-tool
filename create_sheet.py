#!/usr/bin/env python3
"""Create a Google Sheet on Paddy's Drive with AC catalog data, one tab per category."""
import json
import subprocess
import csv
import requests
from pathlib import Path

# Get current token from rclone config
def get_token():
    conf = Path('/home/paddy-bot/.config/rclone/rclone.conf').read_text()
    for line in conf.split('\n'):
        if line.startswith('token = ') and 'paddy' not in line[:20]:
            continue
    
    # Parse the paddy section
    in_paddy = False
    for line in conf.split('\n'):
        if line.strip() == '[paddy]':
            in_paddy = True
            continue
        if in_paddy and line.startswith('['):
            break
        if in_paddy and line.startswith('token = '):
            token_json = json.loads(line[8:])
            return token_json['access_token']
    return None

# Refresh token if needed via rclone
def get_fresh_token():
    # Use rclone to get a fresh token by doing a simple operation
    result = subprocess.run(['rclone', 'about', 'paddy:', '--json'], 
                          capture_output=True, text=True, timeout=15)
    if result.returncode != 0:
        print(f"rclone error: {result.stderr}")
        return None
    
    # Re-read the config (rclone auto-refreshes tokens)
    conf = Path('/home/paddy-bot/.config/rclone/rclone.conf').read_text()
    in_paddy = False
    for line in conf.split('\n'):
        if line.strip() == '[paddy]':
            in_paddy = True
            continue
        if in_paddy and line.startswith('['):
            break
        if in_paddy and line.startswith('token = '):
            token_json = json.loads(line[8:])
            return token_json['access_token']
    return None

token = get_fresh_token()
if not token:
    print("❌ Could not get token")
    exit(1)

headers = {
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json',
}

# Read all catalog CSVs
catalog_dir = Path('/home/paddy-bot/.openclaw/workspace/ac-physics-tool/catalog')
tabs = {
    'Tracks (Released)': 'tracks_released.csv',
    'Tracks (AC Folder)': 'tracks_ac_folder.csv',
    'Cars': 'cars.csv',
    'Apps': 'apps.csv',
    'Servers': 'servers.csv',
    'Parts & Liveries': 'parts.csv',
}

# Build sheet creation request with all tabs
sheets = []
for i, (tab_name, csv_file) in enumerate(tabs.items()):
    csv_path = catalog_dir / csv_file
    if csv_path.exists() and csv_path.stat().st_size > 10:
        sheets.append({
            'properties': {
                'title': tab_name,
                'index': i,
                'sheetId': i,
            }
        })

create_body = {
    'properties': {
        'title': 'RealiSimHQ - AC Content Catalog',
    },
    'sheets': sheets if sheets else [{'properties': {'title': 'Sheet1'}}]
}

print("📊 Creating Google Sheet...")
resp = requests.post(
    'https://sheets.googleapis.com/v4/spreadsheets',
    headers=headers,
    json=create_body,
    timeout=30,
)

if resp.status_code != 200:
    print(f"❌ Error creating sheet: {resp.status_code}")
    print(resp.text)
    exit(1)

sheet_data = resp.json()
spreadsheet_id = sheet_data['spreadsheetId']
spreadsheet_url = sheet_data['spreadsheetUrl']
print(f"✅ Created: {spreadsheet_url}")

# Now populate each tab with data
for tab_name, csv_file in tabs.items():
    csv_path = catalog_dir / csv_file
    if not csv_path.exists() or csv_path.stat().st_size < 10:
        continue
    
    # Read CSV
    rows = []
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        for row in reader:
            rows.append(row)
    
    if not rows:
        continue
    
    # Write to sheet
    range_name = f"'{tab_name}'!A1"
    update_body = {
        'values': rows,
    }
    
    resp = requests.put(
        f'https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{range_name}?valueInputOption=USER_ENTERED',
        headers=headers,
        json=update_body,
        timeout=30,
    )
    
    if resp.status_code == 200:
        result = resp.json()
        print(f"  ✅ {tab_name}: {result.get('updatedRows', 0)} rows written")
    else:
        print(f"  ❌ {tab_name}: {resp.status_code} - {resp.text[:200]}")

# Format headers bold on each tab
format_requests = []
for i, (tab_name, csv_file) in enumerate(tabs.items()):
    csv_path = catalog_dir / csv_file
    if not csv_path.exists() or csv_path.stat().st_size < 10:
        continue
    format_requests.append({
        'repeatCell': {
            'range': {
                'sheetId': i,
                'startRowIndex': 0,
                'endRowIndex': 1,
            },
            'cell': {
                'userEnteredFormat': {
                    'textFormat': {'bold': True},
                    'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2},
                    'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
                }
            },
            'fields': 'userEnteredFormat(textFormat,backgroundColor)',
        }
    })
    # Auto-resize columns
    format_requests.append({
        'autoResizeDimensions': {
            'dimensions': {
                'sheetId': i,
                'dimension': 'COLUMNS',
                'startIndex': 0,
                'endIndex': 6,
            }
        }
    })

if format_requests:
    resp = requests.post(
        f'https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}:batchUpdate',
        headers=headers,
        json={'requests': format_requests},
        timeout=30,
    )
    if resp.status_code == 200:
        print("  ✅ Formatting applied")
    else:
        print(f"  ⚠️ Formatting: {resp.status_code}")

print(f"\n🔗 {spreadsheet_url}")
