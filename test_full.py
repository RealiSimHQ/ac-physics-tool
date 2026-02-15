#!/usr/bin/env python3
"""Full analysis test against Ryan's E46."""
import sys
sys.path.insert(0, '/home/paddy-bot/.openclaw/workspace/ac-physics-tool')

from src.analyzer import analyze_car

# Test the E46
print("🏎️  AC Physics Tool — Car Analyzer")
print()

report = analyze_car('/tmp/ac-test/bmw_e46/data')
print(report.summary())
