"""
Open-Meteo API를 사용한 서울 날씨 데이터 수집
- 무료 API (API 키 불필요)
- 날짜 범위: 2024-06-03 ~ 2024-11-19 (ETRI 데이터 기간)
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
import time

print("=" * 80)
print("서울 날씨 데이터 수집 (Open-Meteo API)")
print("=" * 80)

# 서울 좌표 (City Hall)
LATITUDE = 37.5665
LONGITUDE = 126.9780

# ETRI 데이터 기간
START_DATE = "2024-06-03"
END_DATE = "2024-11-19"

# Open-Meteo API endpoint
BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

print(f"\n[1] 날씨 데이터 요청")
print(f"  위치: 서울 ({LATITUDE}, {LONGITUDE})")
print(f"  기간: {START_DATE} ~ {END_DATE}")

# 요청 파라미터
params = {
    'latitude': LATITUDE,
    'longitude': LONGITUDE,
    'start_date': START_DATE,
    'end_date': END_DATE,
    'daily': [
        'temperature_2m_mean',        # 평균 기온
        'temperature_2m_max',          # 최고 기온
        'temperature_2m_min',          # 최저 기온
        'precipitation_sum',           # 강수량
        'rain_sum',                    # 비
        'snowfall_sum',                # 눈
        'precipitation_hours',         # 강수 시간
        'sunshine_duration',           # 일조 시간 (초 단위)
        'wind_speed_10m_max',          # 최대 풍속
        'wind_gusts_10m_max',          # 최대 돌풍
        'relative_humidity_2m_mean',   # 평균 습도
    ],
    'timezone': 'Asia/Seoul'
}

print(f"\n  요청 중...")

try:
    response = requests.get(BASE_URL, params=params, timeout=30)
    response.raise_for_status()

    data = response.json()

    print(f"  ✅ 데이터 수신 성공")

    # DataFrame 생성
    daily = data['daily']

    df = pd.DataFrame({
        'date': pd.to_datetime(daily['time']),
        'temperature_mean': daily['temperature_2m_mean'],
        'temperature_max': daily['temperature_2m_max'],
        'temperature_min': daily['temperature_2m_min'],
        'precipitation_sum': daily['precipitation_sum'],
        'rain_sum': daily['rain_sum'],
        'snowfall_sum': daily['snowfall_sum'],
        'precipitation_hours': daily['precipitation_hours'],
        'sunshine_duration_hours': [s / 3600 if s is not None else 0 for s in daily['sunshine_duration']],  # 초 → 시간
        'wind_speed_max': daily['wind_speed_10m_max'],
        'wind_gusts_max': daily['wind_gusts_10m_max'],
        'relative_humidity_mean': daily['relative_humidity_2m_mean'],
    })

    print(f"\n[2] 데이터 통계")
    print(f"  레코드 수: {len(df):,}개")
    print(f"  날짜 범위: {df['date'].min()} ~ {df['date'].max()}")
    print(f"\n  기온 평균: {df['temperature_mean'].mean():.1f}°C")
    print(f"  강수량 합계: {df['precipitation_sum'].sum():.1f}mm")
    print(f"  일조 시간 평균: {df['sunshine_duration_hours'].mean():.1f}시간/일")
    print(f"  습도 평균: {df['relative_humidity_mean'].mean():.1f}%")

    # Oslo 날씨 데이터와 동일한 컬럼명으로 매핑
    df_oslo_format = df[['date']].copy()
    df_oslo_format['air_temperature'] = df['temperature_mean']
    df_oslo_format['duration_of_sunshine'] = df['sunshine_duration_hours'] * 3600  # 시간 → 초 (Oslo와 동일)
    df_oslo_format['relative_humidity'] = df['relative_humidity_mean']
    df_oslo_format['precipitation_amount'] = df['precipitation_sum']
    df_oslo_format['cloud_area_fraction'] = None  # Open-Meteo에서는 제공 안 함
    df_oslo_format['air_pressure_at_sea_level'] = None  # Open-Meteo 무료 버전에서 제공 안 함

    print(f"\n[3] Oslo 형식으로 변환")
    print(f"  컬럼: {df_oslo_format.columns.tolist()}")
    print(f"\n  샘플 데이터:")
    print(df_oslo_format.head())

    # 저장
    output_file = "/Users/eojunho/HYU/25-2/SWE/lifelog/ETRILifelog/processed/seoul_weather_2024.csv"
    df_oslo_format.to_csv(output_file, index=False)

    # 전체 데이터도 저장 (백업용)
    full_output_file = "/Users/eojunho/HYU/25-2/SWE/lifelog/ETRILifelog/processed/seoul_weather_2024_full.csv"
    df.to_csv(full_output_file, index=False)

    print(f"\n[4] 저장 완료")
    print(f"  Oslo 형식: {output_file}")
    print(f"  전체 데이터: {full_output_file}")

    print("\n" + "=" * 80)
    print("✅ 완료!")
    print("=" * 80)

except requests.exceptions.RequestException as e:
    print(f"\n❌ API 요청 실패: {e}")
except Exception as e:
    print(f"\n❌ 에러 발생: {e}")
