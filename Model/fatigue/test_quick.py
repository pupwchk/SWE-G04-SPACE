"""
Quick test - 데이터 로드 및 빠른 학습 테스트
"""

import sys
print("Starting quick test...")
print(f"Python: {sys.executable}")

import config
print(f"PMDATA_DIR: {config.PMDATA_DIR}")
print(f"Checking if directory exists: {config.PMDATA_DIR.exists()}")

# p01 데이터만 빠르게 테스트
print("\nTesting p01 data load...")
from utils import load_json_file

p01_dir = config.PMDATA_DIR / "p01" / "fitbit"
steps_file = p01_dir / "steps.json"

if steps_file.exists():
    print(f"✓ Found {steps_file}")
    data = load_json_file(steps_file)
    print(f"✓ Loaded {len(data)} steps records")
else:
    print(f"✗ File not found: {steps_file}")

print("\nQuick test completed!")
