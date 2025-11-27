"""
ETRI 데이터 + 서울 날씨로 피로도 예측 모델 재학습 (병렬 처리 버전)
- PMData 로딩 병렬화 (ProcessPoolExecutor)
- PMData로 기본 모델 학습
- ETRI + 서울 날씨로 Incremental Learning
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBRegressor
import pickle
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor
import os

# ============================================================================
# 병렬 처리를 위한 단위 작업 함수 정의 (함수 밖으로 분리 필수)
# ============================================================================
def process_one_participant(args):
    """
    개별 참가자의 데이터를 처리하여 DataFrame으로 반환하는 함수
    """
    participant, pmdata_dir_str = args
    pmdata_dir = Path(pmdata_dir_str)
    participant_dir = pmdata_dir / participant

    wellness_file = participant_dir / "pmsys" / "wellness.csv"
    if not wellness_file.exists():
        return None

    try:
        wellness = pd.read_csv(wellness_file)
        fitbit_dir = participant_dir / "fitbit"

        # 1. 심박수 (Heart Rate)
        hr_file = fitbit_dir / "heart_rate.json"
        hr_daily = None
        if hr_file.exists():
            with open(hr_file) as f:
                hr_data = json.load(f)
                hr_list = []
                for record in hr_data:
                    if 'dateTime' in record and 'value' in record:
                        date = pd.to_datetime(record['dateTime']).date()
                        if isinstance(record['value'], dict) and 'bpm' in record['value']:
                            bpm = record['value']['bpm']
                            hr_list.append({'date': date, 'bpm': bpm})
                if hr_list:
                    hr_df = pd.DataFrame(hr_list)
                    hr_daily = hr_df.groupby('date')['bpm'].mean().reset_index()
                    hr_daily.columns = ['date', 'heart_rate']

        # 2. 휴식 심박수 (RHR)
        rhr_file = fitbit_dir / "resting_heart_rate.json"
        rhr_df = None
        if rhr_file.exists():
            with open(rhr_file) as f:
                rhr_data = json.load(f)
                rhr_df = pd.DataFrame(rhr_data)
                rhr_df['date'] = pd.to_datetime(rhr_df['dateTime']).dt.date
                rhr_df = rhr_df[['date', 'value']].rename(columns={'value': 'resting_heart_rate'})

        # 3. 걸음수 (Steps)
        steps_file = fitbit_dir / "steps.json"
        steps_df = None
        if steps_file.exists():
            with open(steps_file) as f:
                steps_data = json.load(f)
                steps_df = pd.DataFrame(steps_data)
                steps_df['date'] = pd.to_datetime(steps_df['dateTime']).dt.date
                steps_df['steps'] = steps_df['value'].astype(float)
                steps_df = steps_df.groupby('date')['steps'].sum().reset_index()

        # 4. 칼로리 (Calories)
        calories_file = fitbit_dir / "calories.json"
        calories_df = None
        if calories_file.exists():
            with open(calories_file) as f:
                calories_data = json.load(f)
                calories_df = pd.DataFrame(calories_data)
                calories_df['date'] = pd.to_datetime(calories_df['dateTime']).dt.date
                calories_df['calories'] = calories_df['value'].astype(float)
                calories_df = calories_df.groupby('date')['calories'].sum().reset_index()

        # 5. 거리 (Distance)
        distance_file = fitbit_dir / "distance.json"
        distance_df = None
        if distance_file.exists():
            with open(distance_file) as f:
                distance_data = json.load(f)
                distance_df = pd.DataFrame(distance_data)
                distance_df['date'] = pd.to_datetime(distance_df['dateTime']).dt.date
                distance_df['distance'] = distance_df['value'].astype(float)
                distance_df = distance_df.groupby('date')['distance'].sum().reset_index()

        # 6. 활동 강도 (Activity)
        activity_files = {
            'sedentary_minutes': 'sedentary_minutes.json',
            'lightly_active_minutes': 'lightly_active_minutes.json',
            'moderately_active_minutes': 'moderately_active_minutes.json',
            'very_active_minutes': 'very_active_minutes.json'
        }

        activity_dfs = []
        for col_name, filename in activity_files.items():
            file_path = fitbit_dir / filename
            if file_path.exists():
                with open(file_path) as f:
                    data = json.load(f)
                    df = pd.DataFrame(data)
                    df['date'] = pd.to_datetime(df['dateTime']).dt.date
                    df[col_name] = df['value'].astype(float)
                    df = df.groupby('date')[col_name].sum().reset_index()
                    activity_dfs.append(df)

        # Wellness 데이터 전처리
        wellness['date'] = pd.to_datetime(wellness['effective_time_frame']).dt.date

        # 모든 데이터 병합
        merged = wellness[['date', 'fatigue']].copy()
        merged['participant'] = participant

        if hr_daily is not None:
            merged = merged.merge(hr_daily, on='date', how='left')
        if rhr_df is not None:
            merged = merged.merge(rhr_df, on='date', how='left')
        if steps_df is not None:
            merged = merged.merge(steps_df, on='date', how='left')
        if calories_df is not None:
            merged = merged.merge(calories_df, on='date', how='left')
        if distance_df is not None:
            merged = merged.merge(distance_df, on='date', how='left')

        for activity_df in activity_dfs:
            merged = merged.merge(activity_df, on='date', how='left')
        
        return merged
        
    except Exception as e:
        print(f"Error processing {participant}: {e}")
        return None

# ============================================================================
# 메인 실행 블록
# ============================================================================
if __name__ == '__main__':
    print("=" * 80)
    print("ETRI + 서울 날씨 피로도 예측 모델 학습 (Parallel Processing)")
    print("=" * 80)

    # [1단계] PMData 로드 및 전처리 (병렬 처리)
    print("\n[1단계] PMData 로드 및 전처리 (병렬 실행 중...)")
    
    pmdata_dir = Path("/Users/eojunho/HYU/25-2/SWE/lifelog/pmdata")
    participants = [f"p{i:02d}" for i in range(1, 17)]
    
    # 병렬 처리를 위한 인자 준비 (Path 객체는 pickle 가능하지만 문자열로 넘기는게 안전)
    process_args = [(p, str(pmdata_dir)) for p in participants]
    
    pmdata_records = []
    
    # CPU 코어 수만큼 프로세스 생성 (max_workers=None이면 자동 설정)
    with ProcessPoolExecutor() as executor:
        results = list(executor.map(process_one_participant, process_args))
        
    # 결과 수집 (None 제외)
    for res in results:
        if res is not None:
            pmdata_records.append(res)

    # 모든 참가자 데이터 합치기
    if not pmdata_records:
        print("데이터를 로드하지 못했습니다. 경로를 확인하세요.")
        exit()
        
    pmdata_all = pd.concat(pmdata_records, ignore_index=True)

    print(f"  PMData 레코드: {len(pmdata_all):,}개")
    print(f"  참가자 수: {pmdata_all['participant'].nunique()}명")

    # 공통 피처
    common_features = [
        'heart_rate',
        'resting_heart_rate',
        'steps',
        'calories',
        'distance',
        'sedentary_minutes',
        'lightly_active_minutes',
        'moderately_active_minutes',
        'very_active_minutes'
    ]

    # 결측치 처리 + 타입 변환
    for feat in common_features:
        if feat in pmdata_all.columns:
            # dict나 다른 타입이 섞여있을 수 있으므로 숫자로 변환
            pmdata_all[feat] = pd.to_numeric(pmdata_all[feat], errors='coerce').fillna(0)
        else:
            pmdata_all[feat] = 0

    # 유효한 데이터만 (피로도 라벨 있음)
    pmdata_clean = pmdata_all[pmdata_all['fatigue'].notna()].copy()

    print(f"  유효 레코드: {len(pmdata_clean):,}개")
    print(f"  피로도 분포: {pmdata_clean['fatigue'].value_counts().sort_index().to_dict()}")

    # ============================================================================
    # [2단계] 라벨 → 피로도 점수 변환 (0~100)
    # ============================================================================
    print("\n[2단계] 라벨 → 피로도 점수 변환")

    def label_to_fatigue_score(label):
        if pd.isna(label):
            return np.nan
        label = int(label)
        ranges = {
            1: (0, 20),
            2: (20, 40),
            3: (40, 60),
            4: (60, 80),
            5: (80, 100)
        }
        if label in ranges:
            low, high = ranges[label]
            return np.random.uniform(low, high)
        return np.nan

    pmdata_clean['fatigue_score'] = pmdata_clean['fatigue'].apply(label_to_fatigue_score)

    # NaN 제거
    pmdata_clean = pmdata_clean[pmdata_clean['fatigue_score'].notna()].copy()

    print(f"  평균 피로도: {pmdata_clean['fatigue_score'].mean():.1f}")
    print(f"  최종 유효 레코드: {len(pmdata_clean):,}개")

    # ============================================================================
    # [3단계] PMData 모델 학습
    # ============================================================================
    print("\n[3단계] PMData 기본 모델 학습")

    X = pmdata_clean[common_features].values
    y = pmdata_clean['fatigue_score'].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # n_jobs=-1 : XGBoost 자체 병렬 처리 사용
    model = XGBRegressor(
        n_estimators=100,
        max_depth=6,
        learning_rate=0.1,
        random_state=42,
        n_jobs=-1 
    )

    model.fit(X_train_scaled, y_train)

    train_score = model.score(X_train_scaled, y_train)
    test_score = model.score(X_test_scaled, y_test)

    print(f"  Train R²: {train_score:.4f}")
    print(f"  Test R²: {test_score:.4f}")

    # ============================================================================
    # [4단계] ETRI 데이터 + 서울 날씨 로드 및 병합
    # ============================================================================
    print("\n[4단계] ETRI 데이터 + 서울 날씨 병합")

    etri_file = Path("/Users/eojunho/HYU/25-2/SWE/lifelog/ETRILifelog/processed/etri_pmdata_format.parquet")
    etri_data = pd.read_parquet(etri_file)

    # date 컬럼 타입 통일
    etri_data['date'] = pd.to_datetime(etri_data['date'])

    print(f"  ETRI 레코드: {len(etri_data):,}개")
    print(f"  날짜 범위: {etri_data['date'].min()} ~ {etri_data['date'].max()}")

    # 서울 날씨 로드
    weather_file = Path("/Users/eojunho/HYU/25-2/SWE/lifelog/ETRILifelog/processed/seoul_weather_2024.csv")
    weather_df = pd.read_csv(weather_file)
    weather_df['date'] = pd.to_datetime(weather_df['date'])

    print(f"\n  날씨 레코드: {len(weather_df):,}개")
    print(f"  날짜 범위: {weather_df['date'].min()} ~ {weather_df['date'].max()}")

    # ETRI와 날씨 병합
    etri_with_weather = etri_data.merge(weather_df, on='date', how='left')

    print(f"\n  병합 후 레코드: {len(etri_with_weather):,}개")
    print(f"  날씨 결측치: {etri_with_weather['air_temperature'].isna().sum()}개")

    # 날씨 결측치 처리 (평균값)
    weather_features = ['air_temperature', 'duration_of_sunshine', 'relative_humidity', 'precipitation_amount']
    for feat in weather_features:
        if feat in etri_with_weather.columns:
            etri_with_weather[feat] = etri_with_weather[feat].fillna(etri_with_weather[feat].mean())

    # 날씨 피처 추가
    all_features = common_features + weather_features

    # ETRI 피처 준비
    X_etri = etri_with_weather[all_features].fillna(0).values
    X_etri_scaled = scaler.transform(X_etri)

    # Pseudo-labeling (XGBoost 자체 병렬 처리)
    etri_with_weather['fatigue_score_pseudo'] = model.predict(X_etri_scaled).clip(0, 100)

    print(f"\n  Pseudo-label 평균: {etri_with_weather['fatigue_score_pseudo'].mean():.1f}")

    # ============================================================================
    # [5단계] Incremental Learning (PMData + ETRI + Weather)
    # ============================================================================
    print("\n[5단계] Incremental Learning with Weather")

    X_combined = np.vstack([X_train_scaled, X_etri_scaled])
    y_combined = np.concatenate([y_train, etri_with_weather['fatigue_score_pseudo'].values])

    print(f"  Combined 데이터: {len(X_combined):,}개")
    print(f"    - PMData: {len(X_train_scaled):,}개")
    print(f"    - ETRI: {len(X_etri_scaled):,}개")

    final_model = XGBRegressor(
        n_estimators=50,
        max_depth=6,
        learning_rate=0.05,
        random_state=42,
        n_jobs=-1
    )

    final_model.fit(
        X_combined,
        y_combined,
        xgb_model=model.get_booster()
    )

    final_test_score = final_model.score(X_test_scaled, y_test)
    y_final_pred = final_model.predict(X_test_scaled)
    final_mae = np.mean(np.abs(y_test - y_final_pred))

    print(f"\n  Final Test R²: {final_test_score:.4f} (Before: {test_score:.4f})")
    print(f"  Final MAE: {final_mae:.2f}")

    # ============================================================================
    # [6단계] 모델 및 결과 저장
    # ============================================================================
    print("\n[6단계] 모델 저장")

    output_dir = Path("/Users/eojunho/HYU/25-2/SWE/lifelog/models")
    output_dir.mkdir(exist_ok=True)

    model_file = output_dir / "fatigue_etri_weather_model.pkl"
    scaler_file = output_dir / "fatigue_etri_weather_scaler.pkl"
    metadata_file = output_dir / "etri_weather_metadata.json"

    with open(model_file, 'wb') as f:
        pickle.dump(final_model, f)

    with open(scaler_file, 'wb') as f:
        pickle.dump(scaler, f)

    metadata = {
        'features': all_features,
        'train_date': datetime.now().isoformat(),
        'pmdata_samples': len(X_train),
        'etri_samples': len(X_etri),
        'test_r2': float(final_test_score),
        'test_mae': float(final_mae),
        'score_range': [0, 100],
        'weather_source': 'Open-Meteo API (Seoul)',
        'etri_date_range': f"{etri_data['date'].min()} ~ {etri_data['date'].max()}"
    }

    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2, default=str)

    print(f"  ✅ 저장 완료:")
    print(f"    - {model_file}")
    print(f"    - {scaler_file}")
    print(f"    - {metadata_file}")

    # ============================================================================
    # [7단계] ETRI 날씨 데이터 저장 (etri_climate_data.csv)
    # ============================================================================
    print("\n[7단계] ETRI Climate 데이터 저장")

    etri_climate_output = Path("/Users/eojunho/HYU/25-2/SWE/SWEG04/SWE-G04-SPACE/src/Model/fatigue/output/etri_climate_data.csv")
    etri_climate_output.parent.mkdir(parents=True, exist_ok=True)

    # 일별 집계 (hourly → daily)
    etri_daily = etri_with_weather.groupby('date').agg({
        'subject_id': 'first',
        'heart_rate': 'mean',
        'resting_heart_rate': 'mean',
        'steps': 'sum',
        'distance': 'sum',
        'calories': 'sum',
        'sedentary_minutes': 'sum',
        'lightly_active_minutes': 'sum',
        'moderately_active_minutes': 'sum',
        'very_active_minutes': 'sum',
        'air_temperature': 'mean',
        'duration_of_sunshine': 'sum',
        'relative_humidity': 'mean',
        'precipitation_amount': 'sum',
        'fatigue_score_pseudo': 'mean'
    }).reset_index()

    etri_daily.to_csv(etri_climate_output, index=False)

    print(f"  ✅ {etri_climate_output}")
    print(f"  레코드: {len(etri_daily):,}개")

    print("\n" + "=" * 80)
    print("✅ 완료! ETRI + 서울 날씨 피로도 모델 학습 완료")
    print("=" * 80)
    print(f"\n사용 피처 ({len(all_features)}개):")
    for i, feat in enumerate(all_features, 1):
        print(f"  {i:2d}. {feat}")
    print(f"\n출력: 0~100 피로도 점수")