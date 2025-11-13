"""
결측값 처리 전략

피처 특성에 맞는 결측값 처리 방법을 적용
"""

import pandas as pd
import numpy as np


def handle_missing_values_strategic(df: pd.DataFrame) -> pd.DataFrame:
    """
    피처별 특성에 맞는 결측값 처리

    전략:
    1. Exercise 피처 (34.88% 결측): 0으로 채우기 (운동 안 한 날)
    2. Sleep 피처 (13.82% 결측): Forward Fill → Backward Fill
    3. Resting HR (15.50% 결측): 참가자별 7일 이동 평균
    4. Health 피처 (5.71% 결측): 참가자별 평균
    5. Heart Rate 통계 (3.41% 결측): Forward Fill
    """
    df = df.copy()
    df = df.sort_values(['participant', 'date'])

    print("\n" + "="*60)
    print("결측값 처리 전략 적용")
    print("="*60)

    # 1. Exercise 피처: 0으로 채우기 (운동 안 한 날)
    exercise_cols = ['exercise_count', 'exercise_duration', 'exercise_calories']
    for col in exercise_cols:
        if col in df.columns:
            missing_before = df[col].isnull().sum()
            df[col] = df[col].fillna(0)
            print(f"✓ {col:25s}: {missing_before:4d} → 0 (운동 안 함)")

    # 2. Sleep 피처: Forward Fill → Backward Fill (참가자별)
    sleep_cols = ['sleep_duration', 'sleep_time_in_bed', 'sleep_deep',
                  'sleep_light', 'sleep_rem', 'sleep_wake']
    for col in sleep_cols:
        if col in df.columns:
            missing_before = df[col].isnull().sum()
            df[col] = df.groupby('participant')[col].transform(
                lambda x: x.ffill().bfill()
            )
            missing_after = df[col].isnull().sum()
            print(f"✓ {col:25s}: {missing_before:4d} → {missing_after:4d} (Forward/Backward Fill)")

    # 3. Resting HR: 7일 이동 평균 (참가자별)
    if 'resting_hr' in df.columns:
        missing_before = df['resting_hr'].isnull().sum()

        # 참가자별로 7일 이동 평균 계산 후 채우기
        for participant in df['participant'].unique():
            mask = df['participant'] == participant

            # 7일 이동 평균
            rolling_mean = df.loc[mask, 'resting_hr'].rolling(
                window=7, min_periods=1, center=True
            ).mean()

            # 결측값만 채우기
            df.loc[mask & df['resting_hr'].isnull(), 'resting_hr'] = rolling_mean

        missing_after = df['resting_hr'].isnull().sum()
        print(f"✓ {'resting_hr':25s}: {missing_before:4d} → {missing_after:4d} (7일 이동 평균)")

    # 4. Health 피처: 참가자별 평균
    health_cols = ['total_steps', 'total_calories', 'total_distance']
    for col in health_cols:
        if col in df.columns:
            missing_before = df[col].isnull().sum()

            # 참가자별 평균으로 채우기
            participant_means = df.groupby('participant')[col].transform('mean')
            df.loc[df[col].isnull(), col] = participant_means

            missing_after = df[col].isnull().sum()
            print(f"✓ {col:25s}: {missing_before:4d} → {missing_after:4d} (참가자별 평균)")

    # 5. Heart Rate 통계: Forward Fill (참가자별)
    hr_stats_cols = ['hr_mean', 'hr_max', 'hr_min', 'hr_std']
    for col in hr_stats_cols:
        if col in df.columns:
            missing_before = df[col].isnull().sum()
            df[col] = df.groupby('participant')[col].transform(
                lambda x: x.ffill().bfill()
            )
            missing_after = df[col].isnull().sum()
            print(f"✓ {col:25s}: {missing_before:4d} → {missing_after:4d} (Forward Fill)")

    # 6. 여전히 남은 결측값: 전체 평균 또는 0
    remaining_missing = df.isnull().sum().sum()
    if remaining_missing > 0:
        print(f"\n⚠️  남은 결측값: {remaining_missing}개")

        # 숫자형 컬럼: 전체 평균
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if df[col].isnull().sum() > 0:
                df[col] = df[col].fillna(df[col].mean())

        # 여전히 남은 것: 0
        df = df.fillna(0)
        print(f"✓ 남은 결측값을 평균/0으로 처리")

    print("\n" + "="*60)
    print(f"✓ 결측값 처리 완료: {df.isnull().sum().sum()}개 남음")
    print("="*60 + "\n")

    return df


if __name__ == "__main__":
    import config

    # 테스트
    input_file = config.OUTPUT_DIR / "daily_aggregated.csv"
    df = pd.read_csv(input_file)

    print("처리 전 결측값:", df.isnull().sum().sum())

    df_cleaned = handle_missing_values_strategic(df)

    print("처리 후 결측값:", df_cleaned.isnull().sum().sum())

    # 저장
    output_file = config.OUTPUT_DIR / "daily_aggregated_cleaned.csv"
    df_cleaned.to_csv(output_file, index=False)
    print(f"\n✓ Saved to {output_file}")
