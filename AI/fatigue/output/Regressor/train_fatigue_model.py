"""
피로도 예측 모델 학습 파이프라인
1. PMData로 기본 모델 학습 (라벨 1~5 → 0~100 피로도 점수)
2. ETRI 데이터로 Incremental Learning
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

print("=" * 80)
print("피로도 예측 모델 학습 파이프라인")
print("=" * 80)

# ============================================================================
# [1단계] PMData 로드 및 공통 피처 추출
# ============================================================================
print("\n[1단계] PMData 로드 및 전처리")

pmdata_dir = Path("/Users/eojunho/HYU/25-2/SWE/lifelog/pmdata")
participants = [f"p{i:02d}" for i in range(1, 17)]

pmdata_records = []

for participant in participants:
    participant_dir = pmdata_dir / participant

    # Wellness 데이터 (피로도 라벨 포함)
    wellness_file = participant_dir / "pmsys" / "wellness.csv"
    if not wellness_file.exists():
        continue

    wellness = pd.read_csv(wellness_file)

    # Fitbit 데이터
    fitbit_dir = participant_dir / "fitbit"

    # 심박수
    hr_file = fitbit_dir / "heart_rate.json"
    hr_daily = None
    if hr_file.exists():
        with open(hr_file) as f:
            hr_data = json.load(f)
            # 날짜별 평균 심박수 계산
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

    # 휴식 심박수
    rhr_file = fitbit_dir / "resting_heart_rate.json"
    if rhr_file.exists():
        with open(rhr_file) as f:
            rhr_data = json.load(f)
            rhr_df = pd.DataFrame(rhr_data)
            rhr_df['date'] = pd.to_datetime(rhr_df['dateTime']).dt.date
            rhr_df = rhr_df[['date', 'value']].rename(columns={'value': 'resting_heart_rate'})

    # 걸음수
    steps_file = fitbit_dir / "steps.json"
    if steps_file.exists():
        with open(steps_file) as f:
            steps_data = json.load(f)
            steps_df = pd.DataFrame(steps_data)
            steps_df['date'] = pd.to_datetime(steps_df['dateTime']).dt.date
            steps_df['steps'] = steps_df['value'].astype(float)
            steps_df = steps_df.groupby('date')['steps'].sum().reset_index()

    # 칼로리
    calories_file = fitbit_dir / "calories.json"
    if calories_file.exists():
        with open(calories_file) as f:
            calories_data = json.load(f)
            calories_df = pd.DataFrame(calories_data)
            calories_df['date'] = pd.to_datetime(calories_df['dateTime']).dt.date
            calories_df['calories'] = calories_df['value'].astype(float)
            calories_df = calories_df.groupby('date')['calories'].sum().reset_index()

    # 거리
    distance_file = fitbit_dir / "distance.json"
    if distance_file.exists():
        with open(distance_file) as f:
            distance_data = json.load(f)
            distance_df = pd.DataFrame(distance_data)
            distance_df['date'] = pd.to_datetime(distance_df['dateTime']).dt.date
            distance_df['distance'] = distance_df['value'].astype(float)
            distance_df = distance_df.groupby('date')['distance'].sum().reset_index()

    # 활동 강도
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
    if rhr_file.exists() and 'rhr_df' in locals():
        merged = merged.merge(rhr_df, on='date', how='left')
    if steps_file.exists() and 'steps_df' in locals():
        merged = merged.merge(steps_df, on='date', how='left')
    if calories_file.exists() and 'calories_df' in locals():
        merged = merged.merge(calories_df, on='date', how='left')
    if distance_file.exists() and 'distance_df' in locals():
        merged = merged.merge(distance_df, on='date', how='left')

    for activity_df in activity_dfs:
        merged = merged.merge(activity_df, on='date', how='left')

    pmdata_records.append(merged)

# 모든 참가자 데이터 합치기
pmdata_all = pd.concat(pmdata_records, ignore_index=True)

print(f"  PMData 레코드: {len(pmdata_all):,}개")
print(f"  참가자 수: {pmdata_all['participant'].nunique()}명")
print(f"  피처: {pmdata_all.columns.tolist()}")

# 공통 피처만 선택
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

# 결측치 처리
for feat in common_features:
    if feat in pmdata_all.columns:
        pmdata_all[feat] = pmdata_all[feat].fillna(0)
    else:
        pmdata_all[feat] = 0

# 유효한 데이터만 (피로도 라벨 있음)
pmdata_clean = pmdata_all[pmdata_all['fatigue'].notna()].copy()

print(f"  유효 레코드 (라벨 있음): {len(pmdata_clean):,}개")
print(f"  피로도 라벨 분포:\n{pmdata_clean['fatigue'].value_counts().sort_index()}")

# ============================================================================
# [2단계] 라벨 1~5를 0~100 피로도 점수로 변환 (균등 샘플링)
# ============================================================================
print("\n[2단계] 라벨 → 피로도 점수 변환")

def label_to_fatigue_score(label):
    """라벨 1~5를 0~100 피로도 점수로 변환 (균등 분포 샘플링)"""
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

print(f"  변환된 피로도 점수 통계:")
print(pmdata_clean['fatigue_score'].describe())

# ============================================================================
# [3단계] XGBRegressor로 PMData 학습
# ============================================================================
print("\n[3단계] PMData 모델 학습")

X = pmdata_clean[common_features].values
y = pmdata_clean['fatigue_score'].values

# Train/Test 분리
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# 스케일링
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# XGBoost 회귀 모델
print("  모델 학습 중...")
model = XGBRegressor(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    random_state=42,
    n_jobs=-1
)

model.fit(X_train_scaled, y_train)

# 평가
train_score = model.score(X_train_scaled, y_train)
test_score = model.score(X_test_scaled, y_test)

y_pred = model.predict(X_test_scaled)
mae = np.mean(np.abs(y_test - y_pred))
rmse = np.sqrt(np.mean((y_test - y_pred) ** 2))

print(f"  Train R²: {train_score:.4f}")
print(f"  Test R²: {test_score:.4f}")
print(f"  MAE: {mae:.2f}")
print(f"  RMSE: {rmse:.2f}")

# ============================================================================
# [4단계] ETRI 데이터로 Pseudo-labeling
# ============================================================================
print("\n[4단계] ETRI 데이터 Pseudo-labeling")

etri_file = Path("/Users/eojunho/HYU/25-2/SWE/lifelog/ETRILifelog/processed/etri_pmdata_format.parquet")
etri_data = pd.read_parquet(etri_file)

print(f"  ETRI 레코드: {len(etri_data):,}개")

# ETRI 피처 준비
X_etri = etri_data[common_features].fillna(0).values
X_etri_scaled = scaler.transform(X_etri)

# PMData 모델로 예측 (Pseudo-label)
etri_data['fatigue_score_pseudo'] = model.predict(X_etri_scaled)

# 0~100 범위로 클리핑
etri_data['fatigue_score_pseudo'] = etri_data['fatigue_score_pseudo'].clip(0, 100)

print(f"  Pseudo-label 통계:")
print(etri_data['fatigue_score_pseudo'].describe())

# ============================================================================
# [5단계] Incremental Learning (PMData + ETRI)
# ============================================================================
print("\n[5단계] Incremental Learning")

# PMData와 ETRI 합치기
X_combined = np.vstack([X_train_scaled, X_etri_scaled])
y_combined = np.concatenate([y_train, etri_data['fatigue_score_pseudo'].values])

print(f"  Combined 데이터: {len(X_combined):,}개")
print(f"    - PMData: {len(X_train_scaled):,}개")
print(f"    - ETRI: {len(X_etri_scaled):,}개")

# Incremental Learning (warm start)
print("  Incremental Learning 중...")
final_model = XGBRegressor(
    n_estimators=50,  # 추가 학습
    max_depth=6,
    learning_rate=0.05,  # learning rate 낮춤
    random_state=42,
    n_jobs=-1
)

# 기존 모델을 warm start로 사용
final_model.fit(
    X_combined,
    y_combined,
    xgb_model=model.get_booster()  # 기존 모델 활용
)

# 최종 평가
final_test_score = final_model.score(X_test_scaled, y_test)
y_final_pred = final_model.predict(X_test_scaled)
final_mae = np.mean(np.abs(y_test - y_final_pred))
final_rmse = np.sqrt(np.mean((y_test - y_final_pred) ** 2))

print(f"  Final Test R²: {final_test_score:.4f} (Before: {test_score:.4f})")
print(f"  Final MAE: {final_mae:.2f} (Before: {mae:.2f})")
print(f"  Final RMSE: {final_rmse:.2f} (Before: {rmse:.2f})")

# ============================================================================
# [6단계] 모델 저장
# ============================================================================
print("\n[6단계] 모델 저장")

output_dir = Path("/Users/eojunho/HYU/25-2/SWE/lifelog/models")
output_dir.mkdir(exist_ok=True)

# 모델 저장
model_file = output_dir / "fatigue_model_final.pkl"
scaler_file = output_dir / "fatigue_scaler.pkl"
metadata_file = output_dir / "model_metadata.json"

with open(model_file, 'wb') as f:
    pickle.dump(final_model, f)

with open(scaler_file, 'wb') as f:
    pickle.dump(scaler, f)

metadata = {
    'features': common_features,
    'train_date': datetime.now().isoformat(),
    'pmdata_samples': len(X_train),
    'etri_samples': len(X_etri),
    'test_r2': float(final_test_score),
    'test_mae': float(final_mae),
    'test_rmse': float(final_rmse),
    'score_range': [0, 100]
}

with open(metadata_file, 'w') as f:
    json.dump(metadata, f, indent=2)

print(f"  ✅ 모델 저장:")
print(f"    - {model_file}")
print(f"    - {scaler_file}")
print(f"    - {metadata_file}")

print("\n" + "=" * 80)
print("✅ 완료! 피로도 예측 모델 학습 완료")
print("=" * 80)
print(f"\n사용 방법:")
print(f"  입력: {', '.join(common_features)}")
print(f"  출력: 0~100 피로도 점수 (연속형)")
