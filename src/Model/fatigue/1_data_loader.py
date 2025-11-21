"""
Step 1: Data Loader
- pmdata에서 JSON 파일 로드
- 일일 집계 수행
- wellness.csv와 병합
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from multiprocessing import Pool, cpu_count

import config
from utils import (
    load_json_file,
    extract_date,
    save_dataframe,
    print_data_summary
)


def load_participant_data(participant_id: str) -> pd.DataFrame:
    """참가자 1명의 모든 데이터 로드 및 일일 집계"""
    # 병렬 처리 시 출력 최소화
    # print(f"Loading {participant_id}...")

    participant_dir = config.PMDATA_DIR / participant_id
    fitbit_dir = participant_dir / "fitbit"

    # 일일 집계 딕셔너리 {날짜: {피처: 값}}
    daily_data = defaultdict(lambda: {
        'participant': participant_id,
        'date': None
    })

    # 1. Steps (걸음수) - 분당 데이터 → 일일 합계
    steps_file = fitbit_dir / "steps.json"
    if steps_file.exists():
        steps_data = load_json_file(steps_file)
        steps_by_date = defaultdict(int)

        for entry in steps_data:
            date = extract_date(entry.get('dateTime'))
            if date:
                steps = int(entry.get('value', 0))
                steps_by_date[date] += steps

        for date, total in steps_by_date.items():
            daily_data[date]['total_steps'] = total

        print(f"  ✓ Loaded {len(steps_data)} steps records → {len(steps_by_date)} days")

    # 2. Calories (칼로리) - 분당 소모 칼로리 → 일일 합계
    calories_file = fitbit_dir / "calories.json"
    if calories_file.exists():
        calories_data = load_json_file(calories_file)
        calories_by_date = defaultdict(float)

        for entry in calories_data:
            date = extract_date(entry.get('dateTime'))
            if date:
                calories = float(entry.get('value', 0))
                calories_by_date[date] += calories

        for date, total in calories_by_date.items():
            daily_data[date]['total_calories'] = total

        print(f"  ✓ Loaded {len(calories_data)} calories records → {len(calories_by_date)} days")

    # 3. Distance (거리) - 분당 거리(cm) → 일일 합계(km)
    distance_file = fitbit_dir / "distance.json"
    if distance_file.exists():
        distance_data = load_json_file(distance_file)
        distance_by_date = defaultdict(float)

        for entry in distance_data:
            date = extract_date(entry.get('dateTime'))
            if date:
                distance_cm = float(entry.get('value', 0))
                distance_by_date[date] += distance_cm

        for date, total_cm in distance_by_date.items():
            daily_data[date]['total_distance'] = total_cm / 100000  # cm → km

        print(f"  ✓ Loaded {len(distance_data)} distance records → {len(distance_by_date)} days")

    # 4. Resting Heart Rate (안정시 심박수)
    resting_hr_file = fitbit_dir / "resting_heart_rate.json"
    if resting_hr_file.exists():
        resting_hr_data = load_json_file(resting_hr_file)
        for entry in resting_hr_data:
            date = extract_date(entry.get('dateTime'))
            if date:
                value = entry.get('value', {})
                if isinstance(value, dict):
                    daily_data[date]['resting_hr'] = value.get('value', 0)
                else:
                    daily_data[date]['resting_hr'] = value
        print(f"  ✓ Loaded {len(resting_hr_data)} resting HR records")

    # 5. Heart Rate (심박수 - 일일 통계 계산) - 스트리밍 방식
    heart_rate_file = fitbit_dir / "heart_rate.json"
    if heart_rate_file.exists():
        hr_by_date = defaultdict(list)
        hr_count = 0

        # 스트리밍 방식으로 JSON 파싱 (메모리 효율적)
        import json
        with open(heart_rate_file, 'r') as f:
            hr_data = json.load(f)

        # 100개씩 처리 (메모리 절약)
        batch_size = 10000
        for i in range(0, len(hr_data), batch_size):
            batch = hr_data[i:i+batch_size]
            for entry in batch:
                date = extract_date(entry.get('dateTime'))
                if date:
                    value = entry.get('value', {})
                    bpm = value.get('bpm', 0) if isinstance(value, dict) else 0
                    if bpm > 0:
                        hr_by_date[date].append(bpm)
                        hr_count += 1

        # 일일 통계 계산
        for date, bpms in hr_by_date.items():
            daily_data[date]['hr_mean'] = np.mean(bpms)
            daily_data[date]['hr_max'] = np.max(bpms)
            daily_data[date]['hr_min'] = np.min(bpms)
            daily_data[date]['hr_std'] = np.std(bpms)

        print(f"  ✓ Loaded {hr_count} HR records → {len(hr_by_date)} days")

    # 6. Sleep (수면)
    sleep_file = fitbit_dir / "sleep.json"
    if sleep_file.exists():
        sleep_data = load_json_file(sleep_file)

        for entry in sleep_data:
            date = extract_date(entry.get('dateOfSleep'))
            if date:
                # 총 수면시간 (분)
                daily_data[date]['sleep_duration'] = entry.get('minutesAsleep', 0)
                daily_data[date]['sleep_time_in_bed'] = entry.get('timeInBed', 0)

                # 수면 단계별 시간
                levels = entry.get('levels', {}).get('summary', {})
                daily_data[date]['sleep_deep'] = levels.get('deep', {}).get('minutes', 0)
                daily_data[date]['sleep_light'] = levels.get('light', {}).get('minutes', 0)
                daily_data[date]['sleep_rem'] = levels.get('rem', {}).get('minutes', 0)
                daily_data[date]['sleep_wake'] = levels.get('wake', {}).get('minutes', 0)

        print(f"  ✓ Loaded {len(sleep_data)} sleep records")

    # 7. Exercise (운동)
    exercise_file = fitbit_dir / "exercise.json"
    if exercise_file.exists():
        exercise_data = load_json_file(exercise_file)

        # 날짜별로 그룹화
        exercise_by_date = defaultdict(lambda: {
            'count': 0,
            'total_duration': 0,
            'total_calories': 0
        })

        for entry in exercise_data:
            date = extract_date(entry.get('startTime'))
            if date:
                exercise_by_date[date]['count'] += 1
                exercise_by_date[date]['total_duration'] += entry.get('activeDuration', 0) / 60000  # ms to min
                exercise_by_date[date]['total_calories'] += entry.get('calories', 0)

        for date, stats in exercise_by_date.items():
            daily_data[date]['exercise_count'] = stats['count']
            daily_data[date]['exercise_duration'] = stats['total_duration']
            daily_data[date]['exercise_calories'] = stats['total_calories']

        print(f"  ✓ Loaded {len(exercise_data)} exercise records → {len(exercise_by_date)} days")

    # 8. Wellness (타겟 변수)
    wellness_file = participant_dir / config.WELLNESS_FILE
    if wellness_file.exists():
        wellness_df = pd.read_csv(wellness_file)

        for _, row in wellness_df.iterrows():
            date = extract_date(row['effective_time_frame'])
            if date:
                daily_data[date]['fatigue'] = row['fatigue']
                daily_data[date]['mood'] = row['mood']
                daily_data[date]['stress'] = row['stress']
                daily_data[date]['sleep_quality'] = row['sleep_quality']
                daily_data[date]['soreness'] = row['soreness']

        print(f"  ✓ Loaded {len(wellness_df)} wellness records")

    # DataFrame으로 변환
    df = pd.DataFrame.from_dict(daily_data, orient='index')
    df['date'] = df.index
    df = df.reset_index(drop=True)

    # 날짜순 정렬
    df = df.sort_values('date')

    print(f"\n  → Daily aggregated: {len(df)} days")

    return df


def load_all_participants() -> pd.DataFrame:
    """모든 참가자 데이터 로드 (병렬 처리)"""
    print(f"\n{'#'*60}")
    print(f"# Loading All Participants Data (Parallel)")
    print(f"{'#'*60}")
    print(f"Using {cpu_count()} CPU cores\n")

    # 병렬 처리로 참가자 데이터 로드
    with Pool(processes=cpu_count()) as pool:
        all_data = pool.map(load_participant_data, config.PARTICIPANTS)

    # None 제거 (에러 발생한 참가자)
    all_data = [df for df in all_data if df is not None and len(df) > 0]

    # 전체 병합
    combined_df = pd.concat(all_data, ignore_index=True)

    # 날씨 데이터 병합
    weather_file = config.OUTPUT_DIR / "oslo_weather_2019_2020.csv"
    if weather_file.exists():
        print(f"\n✓ Loading weather data from {weather_file}")
        weather_df = pd.read_csv(weather_file)
        weather_df = weather_df.rename(columns={'time': 'date'})

        # 날씨 데이터 병합 (날짜 기준)
        combined_df = combined_df.merge(weather_df, on='date', how='left')
        print(f"  ✓ Merged weather data: {len(weather_df)} days")
    else:
        print(f"  ⚠️  Weather data not found: {weather_file}")

    # 타겟 변수가 있는 행만 선택
    combined_df = combined_df.dropna(subset=['fatigue'])

    print_data_summary(combined_df, "Combined Dataset")

    return combined_df


if __name__ == "__main__":
    output_file = config.OUTPUT_DIR / "daily_aggregated.csv"

    # 이미 집계된 파일이 있으면 재사용
    if output_file.exists():
        print(f"\n✓ Found existing aggregated data: {output_file}")
        print(f"  Skipping data loading (delete file to reload)")
        df = pd.read_csv(output_file)
        print(f"  Loaded {len(df)} records, {df['participant'].nunique()} participants")
    else:
        # 전체 데이터 로드
        df = load_all_participants()

        # 저장
        save_dataframe(df, output_file)

        print(f"\n{'='*60}")
        print(f"✓ Data loading completed!")
        print(f"  Total records: {len(df)}")
        print(f"  Participants: {df['participant'].nunique()}")
        print(f"  Output: {output_file}")
        print(f"{'='*60}\n")
