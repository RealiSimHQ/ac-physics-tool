#!/usr/bin/env python3
"""Analyze all of Ryan's cars from Google Drive."""
import sys
sys.path.insert(0, '/home/paddy-bot/.openclaw/workspace/ac-physics-tool')

from src.analyzer import analyze_car

cars = [
    ('/tmp/ac-test/bmw_e46/data', 'BMW E46'),
    ('/tmp/ac-test/S Chassis', 'S Chassis (180SX)'),
    ('/tmp/ac-test/Chevy C6', 'Chevy C6'),
    ('/tmp/ac-test/Toyota AE86', 'Toyota AE86'),
]

print("🏎️  AC Physics Tool — Multi-Car Analysis")
print("=" * 60)

for path, label in cars:
    print(f"\n📂 {label}")
    try:
        report = analyze_car(path)
        print(report.summary())
    except Exception as e:
        print(f"  ❌ Error: {e}")
    print()
