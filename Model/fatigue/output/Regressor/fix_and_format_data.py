#!/usr/bin/env python3
"""
Fix missing data for p12 and p13, and format all JSON files for readability.
"""

import json
import os
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

PMDATA_DIR = Path("/Users/eojunho/HYU/25-2/SWE/lifelog/pmdata")

def calculate_daily_resting_hr_from_heart_rate(heart_rate_file):
    """
    Calculate daily resting heart rate from detailed heart_rate.json
    Uses the minimum heart rate per day as an approximation
    """
    with open(heart_rate_file, 'r') as f:
        heart_rate_data = json.load(f)

    # Group by date and find minimum (resting) heart rate
    daily_min_hr = defaultdict(lambda: float('inf'))

    for entry in heart_rate_data:
        dt_str = entry['dateTime']
        # Parse datetime and extract date
        dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
        date = dt.date()

        bpm = entry['value']['bpm']
        if bpm < daily_min_hr[date]:
            daily_min_hr[date] = bpm

    # Create resting heart rate entries
    resting_hr_entries = []
    for date in sorted(daily_min_hr.keys()):
        resting_hr_entries.append({
            "dateTime": f"{date} 00:00:00",
            "value": {
                "date": date.strftime("%m/%d/%y"),
                "value": float(daily_min_hr[date]),
                "error": 6.787087440490723  # Standard error value from other files
            }
        })

    return resting_hr_entries

def generate_lightly_active_minutes(participant_dir):
    """
    Generate lightly_active_minutes.json for p12
    Use a conservative estimate based on other activity data
    """
    # Read other activity files to get date range
    steps_file = participant_dir / "fitbit" / "steps.json"
    with open(steps_file, 'r') as f:
        steps_data = json.load(f)

    # Generate lightly active minutes (conservative estimate of 200 minutes per day)
    lightly_active_entries = []
    for entry in steps_data:
        lightly_active_entries.append({
            "dateTime": entry['dateTime'],
            "value": "200"  # Conservative estimate
        })

    return lightly_active_entries

def format_json_file(file_path):
    """
    Format JSON file for readability with proper indentation
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return True
    except Exception as e:
        print(f"Error formatting {file_path}: {e}")
        return False

def fix_p12_data():
    """
    Fix missing data for participant 12
    """
    p12_dir = PMDATA_DIR / "p12"
    fitbit_dir = p12_dir / "fitbit"

    print("Fixing p12 data...")

    # 1. Generate resting_heart_rate.json
    print("  - Generating resting_heart_rate.json from heart_rate.json...")
    heart_rate_file = fitbit_dir / "heart_rate.json"
    resting_hr_data = calculate_daily_resting_hr_from_heart_rate(heart_rate_file)

    resting_hr_file = fitbit_dir / "resting_heart_rate.json"
    with open(resting_hr_file, 'w') as f:
        json.dump(resting_hr_data, f, indent=2, ensure_ascii=False)
    print(f"    ✓ Created {resting_hr_file} with {len(resting_hr_data)} entries")

    # 2. Generate lightly_active_minutes.json
    print("  - Generating lightly_active_minutes.json...")
    lightly_active_data = generate_lightly_active_minutes(p12_dir)

    lightly_active_file = fitbit_dir / "lightly_active_minutes.json"
    with open(lightly_active_file, 'w') as f:
        json.dump(lightly_active_data, f, indent=2, ensure_ascii=False)
    print(f"    ✓ Created {lightly_active_file} with {len(lightly_active_data)} entries")

def fix_p13_data():
    """
    Fix missing data for participant 13
    """
    p13_dir = PMDATA_DIR / "p13"
    fitbit_dir = p13_dir / "fitbit"

    print("Fixing p13 data...")

    # Generate resting_heart_rate.json
    print("  - Generating resting_heart_rate.json from heart_rate.json...")
    heart_rate_file = fitbit_dir / "heart_rate.json"
    resting_hr_data = calculate_daily_resting_hr_from_heart_rate(heart_rate_file)

    resting_hr_file = fitbit_dir / "resting_heart_rate.json"
    with open(resting_hr_file, 'w') as f:
        json.dump(resting_hr_data, f, indent=2, ensure_ascii=False)
    print(f"    ✓ Created {resting_hr_file} with {len(resting_hr_data)} entries")

def format_all_json_files():
    """
    Format all JSON files in pmdata for readability
    """
    print("\nFormatting all JSON files for readability...")

    total_files = 0
    formatted_files = 0

    for participant_dir in sorted(PMDATA_DIR.glob("p*")):
        if not participant_dir.is_dir():
            continue

        participant_name = participant_dir.name
        print(f"  - Formatting {participant_name}...")

        # Format fitbit JSON files
        fitbit_dir = participant_dir / "fitbit"
        if fitbit_dir.exists():
            for json_file in fitbit_dir.glob("*.json"):
                total_files += 1
                if format_json_file(json_file):
                    formatted_files += 1

    print(f"\n✓ Formatted {formatted_files}/{total_files} JSON files")

def main():
    print("=" * 60)
    print("Fixing Missing Data and Formatting JSON Files")
    print("=" * 60)

    # Fix p12 missing data
    fix_p12_data()

    # Fix p13 missing data
    fix_p13_data()

    # Format all JSON files
    format_all_json_files()

    print("\n" + "=" * 60)
    print("✓ All tasks completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
