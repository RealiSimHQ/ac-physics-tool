#!/usr/bin/env python3
"""Catalog all of Ryan's AC tracks and cars from Google Drive into a CSV/spreadsheet."""
import csv
import os
import re
from pathlib import Path

def parse_file_list(raw_output, base_path):
    """Parse rclone ls output into structured data."""
    items = []
    for line in raw_output.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        # Format: SIZE PATH
        match = re.match(r'^\s*(\d+)\s+(.+)$', line)
        if match:
            size = int(match.group(1))
            filepath = match.group(2)
            
            # Split into category/subcategory/filename
            parts = filepath.split('/')
            filename = parts[-1]
            category = parts[0] if len(parts) > 1 else ''
            subcategory = '/'.join(parts[1:-1]) if len(parts) > 2 else ''
            
            # Clean name from filename
            name = filename
            for ext in ['.7z', '.zip', '.rar']:
                name = name.replace(ext, '')
            
            # Size in MB
            size_mb = size / (1024 * 1024)
            
            items.append({
                'name': name,
                'category': category,
                'subcategory': subcategory,
                'filename': filename,
                'path': f"{base_path}/{filepath}",
                'size_mb': round(size_mb, 1),
                'extension': Path(filename).suffix,
            })
    return items

# Read the raw file lists
tracks_ac = """Pods Touge Paradise Free Version.7z	565831678
Drift Appalachia.7z	175773899
Patreon Free/X10DD_Pump Track.7z	75814430
Patreon Only/Great State of Touge.7z	440045773
Patreon Only/Pods Touge Tandem.7z	69629216
Patreon Only/Pods Touge Paradise Test Version.7z	478981898
Patreon Only/Pods Touge Paradise.7z	565613700
The Great Smokey Mountain Touge Project/The Great Smokey Mountain Touge Project.7z	357934293"""

# We'll use rclone output directly
import subprocess

def run_rclone(path):
    result = subprocess.run(['rclone', 'ls', f'gdrive:{path}'], 
                          capture_output=True, text=True, timeout=30)
    return result.stdout

def catalog_to_csv(items, output_path, sheet_name=""):
    """Write items to CSV."""
    if not items:
        return
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Name', 'Category', 'Subcategory', 'Filename', 'Size (MB)', 'Full Path'])
        for item in sorted(items, key=lambda x: (x['category'], x['subcategory'], x['name'])):
            writer.writerow([
                item['name'],
                item['category'],
                item['subcategory'], 
                item['filename'],
                item['size_mb'],
                item['path'],
            ])

print("📂 Cataloging Google Drive AC content...")
print()

# Tracks - Released
print("  Scanning Tracks/Released...")
tracks_released = parse_file_list(run_rclone("Tracks/Released"), "Tracks/Released")
print(f"    Found {len(tracks_released)} items")

# Tracks - AC folder
print("  Scanning Assetto Corsa/Tracks...")
tracks_ac = parse_file_list(run_rclone("Assetto Corsa/Tracks"), "Assetto Corsa/Tracks")
print(f"    Found {len(tracks_ac)} items")

# Cars
print("  Scanning Assetto Corsa/Cars...")
cars = parse_file_list(run_rclone("Assetto Corsa/Cars"), "Assetto Corsa/Cars")
print(f"    Found {len(cars)} items")

# Apps
print("  Scanning Assetto Corsa/Assetto Apps...")
apps = parse_file_list(run_rclone("Assetto Corsa/Assetto Apps"), "Assetto Corsa/Assetto Apps")
print(f"    Found {len(apps)} items")

# Servers
print("  Scanning Assetto Corsa/Servers...")
servers = parse_file_list(run_rclone("Assetto Corsa/Servers"), "Assetto Corsa/Servers")
print(f"    Found {len(servers)} items")

# Parts
print("  Scanning Assetto Corsa/Parts Folders and Liverys...")
parts = parse_file_list(run_rclone("Assetto Corsa/Parts Folders and Liverys"), "Assetto Corsa/Parts")
print(f"    Found {len(parts)} items")

# Write CSVs
outdir = '/home/paddy-bot/.openclaw/workspace/ac-physics-tool/catalog'
os.makedirs(outdir, exist_ok=True)

catalog_to_csv(tracks_released, f'{outdir}/tracks_released.csv')
catalog_to_csv(tracks_ac, f'{outdir}/tracks_ac_folder.csv')
catalog_to_csv(cars, f'{outdir}/cars.csv')
catalog_to_csv(apps, f'{outdir}/apps.csv')
catalog_to_csv(servers, f'{outdir}/servers.csv')
catalog_to_csv(parts, f'{outdir}/parts.csv')

# Combined summary
print()
print("=" * 60)
print("📊 CATALOG SUMMARY")
print("=" * 60)

all_items = tracks_released + tracks_ac + cars + apps + servers + parts
total_size = sum(i['size_mb'] for i in all_items)

print(f"  Tracks (Released):     {len(tracks_released):>4} files  ({sum(i['size_mb'] for i in tracks_released)/1024:.1f} GB)")
print(f"  Tracks (AC folder):    {len(tracks_ac):>4} files  ({sum(i['size_mb'] for i in tracks_ac)/1024:.1f} GB)")
print(f"  Cars:                  {len(cars):>4} files  ({sum(i['size_mb'] for i in cars)/1024:.1f} GB)")
print(f"  Apps:                  {len(apps):>4} files  ({sum(i['size_mb'] for i in apps)/1024:.1f} GB)")
print(f"  Servers:               {len(servers):>4} files  ({sum(i['size_mb'] for i in servers)/1024:.1f} GB)")
print(f"  Parts/Liveries:        {len(parts):>4} files  ({sum(i['size_mb'] for i in parts)/1024:.1f} GB)")
print(f"  {'─'*50}")
print(f"  TOTAL:                 {len(all_items):>4} files  ({total_size/1024:.1f} GB)")
print()

# Track categories breakdown
print("📍 Track Categories:")
categories = {}
for t in tracks_ac:
    cat = t['category']
    if cat not in categories:
        categories[cat] = 0
    categories[cat] += 1
for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
    print(f"  {cat}: {count}")

print()
print("🚗 Car Series:")
car_categories = {}
for c in cars:
    cat = c['category']
    if cat not in car_categories:
        car_categories[cat] = 0
    car_categories[cat] += 1
for cat, count in sorted(car_categories.items(), key=lambda x: -x[1]):
    print(f"  {cat}: {count}")

print()
print(f"✅ CSVs saved to {outdir}/")
