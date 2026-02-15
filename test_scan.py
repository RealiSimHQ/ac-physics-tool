#!/usr/bin/env python3
"""Test the scanner and detector against real AC car data."""
import sys
sys.path.insert(0, '/home/paddy-bot/.openclaw/workspace/ac-physics-tool')

from src.folder_scanner import scan_folder
from src.ini_parser import parse_ini_file, get_value, get_raw
from src.car_detector import detect_car, CarIdentity

# Test against Ryan's E46 from Google Drive
test_path = '/tmp/ac-test/bmw_e46/data'
print(f"\n🔍 Scanning: {test_path}\n")

scan = scan_folder(test_path)
print(scan.summary())
print()

# Now try detection
if scan.is_valid:
    car_ini_path = scan.core_files['car.ini']
    print(f"📋 Parsing car.ini: {car_ini_path}")
    car = parse_ini_file(car_ini_path)
    
    # Show what we parsed
    for section_name, section in car.items():
        print(f"\n  [{section_name}]")
        for key, entry in section.items():
            val = entry['value']
            comment = entry.get('comment', '')
            print(f"    {key} = {val}" + (f"  ; {comment}" if comment else ""))

# Try the full data subfolder too
print(f"\n{'='*60}")
inner_path = '/tmp/ac-test/bmw_e46/data/data'
print(f"\n🔍 Scanning inner data: {inner_path}\n")
inner_scan = scan_folder(inner_path)
print(inner_scan.summary())

# Parse drivetrain if available
if 'drivetrain.ini' in inner_scan.core_files:
    dt = parse_ini_file(inner_scan.core_files['drivetrain.ini'])
    print(f"\n📋 Drivetrain:")
    ttype = get_raw(dt, 'TRACTION', 'TYPE', '?')
    print(f"  Type: {ttype}")
    gears = get_value(dt, 'GEARS', 'COUNT', 0)
    print(f"  Gears: {gears}")
    final = get_value(dt, 'GEARS', 'FINAL', 0)
    print(f"  Final drive: {final}")
    for i in range(1, 7):
        g = get_value(dt, 'GEARS', f'GEAR_{i}', None)
        if g is not None:
            print(f"  Gear {i}: {g}")

# Parse engine
if 'engine.ini' in inner_scan.core_files:
    eng = parse_ini_file(inner_scan.core_files['engine.ini'])
    print(f"\n📋 Engine:")
    limiter = get_value(eng, 'ENGINE_DATA', 'LIMITER', 0)
    idle = get_value(eng, 'ENGINE_DATA', 'MINIMUM', 0)
    print(f"  RPM: {idle} - {limiter}")

# Test detector
print(f"\n{'='*60}")
print(f"\n🚗 Running car detector...\n")

# The detector expects a data/ folder structure
identity = detect_car('/tmp/ac-test/bmw_e46/data')  
print(identity.summary())
