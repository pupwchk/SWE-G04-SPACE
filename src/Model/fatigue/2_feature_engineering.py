"""
Step 2: Feature Engineering
- 시계열 피처 생성 (이동 평균, 변화량)
- 파생 피처 생성
- 결측치 처리
"""

import pandas as pd
import numpy as np
from pathlib import Path

import config
from utils import (
    load_dataframe,
    save_dataframe,
    calculate_rolling_features,
    calculate_diff_features,
    add_temporal_features,
    encode_participant,
    print_data_summary
)
from handle_missing_strategy import handle_missing_values_strategic


def create_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """파생 피처 생성"""
    df = df.copy()

    # 1. 수면 효율성
    df['sleep_efficiency'] = np.where(
        df['sleep_time_in_bed'] > 0,
        df['sleep_duration'] / df['sleep_time_in_bed'],
        0
    )

    # 2. 수면의 질 점수 (깊은 수면 + REM 비율)
    total_sleep = df['sleep_deep'] + df['sleep_light'] + df['sleep_rem']
    df['sleep_quality_score'] = np.where(
        total_sleep > 0,
        (df['sleep_deep'] + df['sleep_rem']) / total_sleep,
        0
    )

    # 3. 깊은 수면 비율
    df['sleep_deep_ratio'] = np.where(
        total_sleep > 0,
        df['sleep_deep'] / total_sleep,
        0
    )

    # 4. REM 수면 비율
    df['sleep_rem_ratio'] = np.where(
        total_sleep > 0,
        df['sleep_rem'] / total_sleep,
        0
    )

    # 5. 활동-수면 균형
    df['exercise_sleep_ratio'] = np.where(
        df['sleep_duration'] > 0,
        df['exercise_duration'] / df['sleep_duration'],
        0
    )

    # 6. 심박수 범위
    df['hr_range'] = df['hr_max'] - df['hr_min']

    # 7. 안정시 심박수 비율 (안정시/평균)
    df['hr_resting_ratio'] = np.where(
        df['hr_mean'] > 0,
        df['resting_hr'] / df['hr_mean'],
        0
    )

    # 8. 칼로리/걸음수 효율
    df['calories_per_step'] = np.where(
        df['total_steps'] > 0,
        df['total_calories'] / df['total_steps'],
        0
    )

    # 9. 거리/걸음수 (보폭)
    df['distance_per_step'] = np.where(
        df['total_steps'] > 0,
        df['total_distance'] / df['total_steps'],
        0
    )

    # 10. 운동 강도 (운동 칼로리/운동 시간)
    df['exercise_intensity'] = np.where(
        df['exercise_duration'] > 0,
        df['exercise_calories'] / df['exercise_duration'],
        0
    )

    # 11. 날씨 파생 피처 (있을 경우)
    weather_features_count = 0
    if 'air_temperature' in df.columns:
        # 체감 온도 (온도 + 습도 효과)
        df['feels_like_temp'] = df['air_temperature'] - (df['relative_humidity'] / 100) * 2
        weather_features_count += 1

    if 'precipitation_amount' in df.columns:
        # 비 여부 (이진)
        df['is_rainy'] = (df['precipitation_amount'] > 0).astype(int)
        weather_features_count += 1

    if 'cloud_area_fraction' in df.columns:
        # 맑음 정도 (역수)
        df['clearness'] = 10 - df['cloud_area_fraction']
        weather_features_count += 1

    print(f"✓ Created {10 + weather_features_count} derived features")

    return df


def normalize_by_participant(df: pd.DataFrame) -> pd.DataFrame:
    """참가자별 정규화 (Z-score normalization)"""
    print(f"\nNormalizing features by participant...")

    df = df.copy()

    # 정규화 제외 컬럼
    exclude_cols = [
        'participant', 'participant_encoded', 'date',
        'fatigue', 'mood', 'stress', 'sleep_quality', 'soreness',
        'day_of_week', 'is_weekend', 'day_of_month', 'week_of_year',  # 시간 피처
        'is_rainy'  # 이진 피처
    ]

    # 정규화할 숫자형 컬럼 선택
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    normalize_cols = [col for col in numeric_cols if col not in exclude_cols]

    print(f"  Normalizing {len(normalize_cols)} features...")

    # 참가자별로 정규화
    normalized_count = 0
    skipped_count = 0

    for participant in df['participant'].unique():
        mask = df['participant'] == participant

        for col in normalize_cols:
            mean = df.loc[mask, col].mean()
            std = df.loc[mask, col].std()

            # 표준편차가 0이 아닌 경우만 정규화 (모두 같은 값인 경우 스킵)
            if std > 1e-6:  # 매우 작은 값도 0으로 간주
                df.loc[mask, col] = (df.loc[mask, col] - mean) / std
                normalized_count += 1
            else:
                # 표준편차가 0이면 0으로 설정 (변화 없음)
                df.loc[mask, col] = 0
                skipped_count += 1

    print(f"  ✓ Normalized {normalized_count} features (skipped {skipped_count} zero-variance features)")

    return df


def create_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """시계열 피처 생성"""
    print(f"\nCreating temporal features...")

    df = df.sort_values(['participant', 'date']).copy()

    # 이동 평균 피처
    rolling_columns = [
        'total_steps',
        'total_calories',
        'total_distance',
        'resting_hr',
        'hr_mean',
        'hr_std',
        'sleep_duration',
        'sleep_deep',
        'sleep_rem',
        'exercise_duration'
    ]

    # 날씨 피처도 이동 평균에 추가
    weather_columns = ['air_temperature', 'relative_humidity', 'air_pressure_at_sea_level']
    for col in weather_columns:
        if col in df.columns:
            rolling_columns.append(col)

    # 참가자별로 이동 평균 계산
    for participant in df['participant'].unique():
        mask = df['participant'] == participant
        participant_df = df[mask].copy()

        # 7일 이동 평균
        participant_df = calculate_rolling_features(
            participant_df,
            rolling_columns,
            window=config.ROLLING_WINDOW_DAYS,
            suffix='_7d_avg'
        )

        # 3일 이동 평균 (단기 트렌드)
        participant_df = calculate_rolling_features(
            participant_df,
            rolling_columns,
            window=3,
            suffix='_3d_avg'
        )

        df.loc[mask, participant_df.columns] = participant_df.values

    print(f"  ✓ Added rolling average features (7d, 3d)")

    # 전날 대비 변화량
    diff_columns = [
        'total_steps',
        'resting_hr',
        'sleep_duration',
        'hr_mean'
    ]

    for participant in df['participant'].unique():
        mask = df['participant'] == participant
        participant_df = df[mask].copy()

        participant_df = calculate_diff_features(
            participant_df,
            diff_columns,
            suffix='_diff_1d'
        )

        df.loc[mask, participant_df.columns] = participant_df.values

    print(f"  ✓ Added diff features (1d)")

    # 요일, 주말 피처
    df = add_temporal_features(df)
    print(f"  ✓ Added temporal features (day_of_week, is_weekend, etc.)")

    return df


def engineer_features(input_file: Path, output_file: Path):
    """전체 피처 엔지니어링 파이프라인"""
    print(f"\n{'#'*60}")
    print(f"# Feature Engineering")
    print(f"{'#'*60}")

    # 데이터 로드
    df = load_dataframe(input_file)
    print(f"\n✓ Loaded data from {input_file}")
    print(f"  Shape: {df.shape}")

    # 참가자 인코딩
    df = encode_participant(df)
    print(f"✓ Encoded participant IDs")

    # 파생 피처 생성
    df = create_derived_features(df)

    # 시계열 피처 생성
    df = create_temporal_features(df)

    # 결측치 처리 (전략적)
    print(f"\n결측치 처리 전: {df.isnull().sum().sum()}개")
    df = handle_missing_values_strategic(df)
    print(f"결측치 처리 후: {df.isnull().sum().sum()}개")

    # 무한대 값 처리
    df = df.replace([np.inf, -np.inf], 0)

    # 개인별 정규화
    df = normalize_by_participant(df)

    # 최종 데이터 요약
    print_data_summary(df, "Engineered Features")

    # 저장
    save_dataframe(df, output_file)

    print(f"\n{'='*60}")
    print(f"✓ Feature engineering completed!")
    print(f"  Input: {input_file}")
    print(f"  Output: {output_file}")
    print(f"  Final shape: {df.shape}")
    print(f"  Total features: {len(df.columns) - 3}")  # participant, date, fatigue 제외
    print(f"{'='*60}\n")

    # 피처 목록 저장
    feature_list_file = config.OUTPUT_DIR / "feature_list.txt"
    with open(feature_list_file, 'w') as f:
        f.write("Feature List\n")
        f.write("="*60 + "\n\n")
        for i, col in enumerate(sorted(df.columns), 1):
            f.write(f"{i:3d}. {col}\n")

    print(f"✓ Feature list saved to {feature_list_file}")


if __name__ == "__main__":
    input_file = config.OUTPUT_DIR / "daily_aggregated.csv"
    output_file = config.OUTPUT_DIR / "features_engineered.csv"

    engineer_features(input_file, output_file)
