"""
Complete Pipeline Runner
전체 파이프라인을 순차적으로 실행
"""

import subprocess
import sys
from pathlib import Path

# Fatigue 디렉토리 경로
FATIGUE_DIR = Path(__file__).parent


def run_script(script_name: str, description: str):
    """Python 스크립트 실행"""
    print(f"\n{'#'*60}")
    print(f"# {description}")
    print(f"{'#'*60}\n")

    script_path = FATIGUE_DIR / script_name

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            check=True,
            cwd=FATIGUE_DIR
        )
        print(f"\n✓ {script_name} completed successfully!")
        return True

    except subprocess.CalledProcessError as e:
        print(f"\n✗ Error running {script_name}: {e}")
        return False


def main():
    """전체 파이프라인 실행"""
    print(f"\n{'='*60}")
    print(f"FATIGUE PREDICTION MODEL - FULL PIPELINE")
    print(f"{'='*60}\n")

    pipeline = [
        ("1_data_loader.py", "Step 1: Data Loading & Daily Aggregation"),
        ("2_feature_engineering.py", "Step 2: Feature Engineering"),
        ("3_train_xgboost.py", "Step 3: XGBoost Training with RandomSearch"),
        ("4_evaluate.py", "Step 4: Evaluation & Visualization")
    ]

    for script, description in pipeline:
        success = run_script(script, description)
        if not success:
            print(f"\n✗ Pipeline stopped due to error in {script}")
            sys.exit(1)

    print(f"\n{'='*60}")
    print(f"✓ FULL PIPELINE COMPLETED SUCCESSFULLY!")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
