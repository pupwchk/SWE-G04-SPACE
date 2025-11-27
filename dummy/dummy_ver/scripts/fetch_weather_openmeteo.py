"""
Open-Meteo API를 사용하여 날씨 데이터를 가져오는 스크립트
과거 날씨 데이터(당일, 1일전, 3일전, 7일전)를 조회할 수 있습니다.
"""

import requests
from datetime import datetime, timedelta
import pandas as pd


class OpenMeteoWeatherFetcher:
    """
    Open-Meteo API를 사용하여 날씨 데이터를 가져오는 클래스

    API 문서: https://open-meteo.com/en/docs
    """

    def __init__(self, latitude=37.5665, longitude=126.9780):
        """
        Initialize weather fetcher

        Args:
            latitude: 위도 (기본값: 서울)
            longitude: 경도 (기본값: 서울)
        """
        self.latitude = latitude
        self.longitude = longitude
        self.base_url = "https://archive-api.open-meteo.com/v1/archive"

    def fetch_historical_weather(self, date):
        """
        특정 날짜의 과거 날씨 데이터를 가져옵니다.

        Args:
            date: datetime 객체 또는 'YYYY-MM-DD' 형식의 문자열

        Returns:
            날씨 데이터 딕셔너리
        """
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d')

        date_str = date.strftime('%Y-%m-%d')

        # Open-Meteo API 파라미터
        params = {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'start_date': date_str,
            'end_date': date_str,
            'daily': [
                'temperature_2m_mean',      # 평균 온도
                'temperature_2m_max',       # 최고 온도
                'temperature_2m_min',       # 최저 온도
                'relative_humidity_2m_mean', # 평균 습도
                'precipitation_sum',        # 강수량 합계
                'wind_speed_10m_max',       # 최대 풍속
                'surface_pressure_mean',    # 평균 기압
                'uv_index_max'              # 최대 자외선 지수
            ],
            'timezone': 'Asia/Seoul'
        }

        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()

            # 응답 데이터 파싱
            daily_data = data.get('daily', {})

            weather_data = {
                'date': date_str,
                'temperature': daily_data.get('temperature_2m_mean', [None])[0],
                'temperature_max': daily_data.get('temperature_2m_max', [None])[0],
                'temperature_min': daily_data.get('temperature_2m_min', [None])[0],
                'humidity': daily_data.get('relative_humidity_2m_mean', [None])[0],
                'precipitation': daily_data.get('precipitation_sum', [None])[0],
                'wind_speed': daily_data.get('wind_speed_10m_max', [None])[0],
                'atmospheric_pressure': daily_data.get('surface_pressure_mean', [None])[0],
                'uv_index': daily_data.get('uv_index_max', [None])[0]
            }

            return weather_data

        except requests.RequestException as e:
            print(f"Error fetching weather data for {date_str}: {e}")
            return None

    def fetch_weather_with_offsets(self, current_date, offsets=[0, 1, 3, 7]):
        """
        현재 날짜 기준으로 여러 시점의 날씨 데이터를 가져옵니다.

        Args:
            current_date: 기준 날짜 (datetime 객체 또는 'YYYY-MM-DD' 문자열)
            offsets: 과거 일수 리스트 (예: [0, 1, 3, 7])

        Returns:
            모든 시점의 날씨 데이터를 포함한 딕셔너리
        """
        if isinstance(current_date, str):
            current_date = datetime.strptime(current_date, '%Y-%m-%d')

        all_weather_data = {}

        for offset in offsets:
            target_date = current_date - timedelta(days=offset)
            weather_data = self.fetch_historical_weather(target_date)

            if weather_data:
                # offset별로 피처명 생성 (예: temperature_d0, temperature_d1)
                for key, value in weather_data.items():
                    if key != 'date':
                        feature_name = f"{key}_d{offset}"
                        all_weather_data[feature_name] = value

        return all_weather_data

    def fetch_weather_for_model(self, current_date):
        """
        모델 학습/예측에 필요한 형식으로 날씨 데이터를 가져옵니다.

        Args:
            current_date: 기준 날짜

        Returns:
            모델에 입력 가능한 형식의 날씨 피처 딕셔너리
        """
        weather_data = self.fetch_weather_with_offsets(current_date)

        # 모델에 필요한 피처만 추출
        model_features = {}
        required_features = [
            'temperature', 'humidity', 'precipitation',
            'wind_speed', 'atmospheric_pressure', 'uv_index'
        ]

        for offset in [0, 1, 3, 7]:
            for feature in required_features:
                key = f"{feature}_d{offset}"
                model_features[key] = weather_data.get(key, 0.0)

        return model_features


def example_usage():
    """사용 예제"""
    print("="*70)
    print("Open-Meteo Weather API 사용 예제")
    print("="*70)

    # 서울의 날씨 데이터 가져오기
    fetcher = OpenMeteoWeatherFetcher(latitude=37.5665, longitude=126.9780)

    # 오늘 날짜 기준으로 데이터 가져오기
    today = datetime.now()
    print(f"\n기준 날짜: {today.strftime('%Y-%m-%d')}\n")

    # 당일, 1일전, 3일전, 7일전 날씨 데이터
    weather_data = fetcher.fetch_weather_with_offsets(today)

    print("가져온 날씨 데이터:")
    for key, value in sorted(weather_data.items()):
        print(f"  {key}: {value}")

    print("\n" + "="*70)
    print("모델 입력용 데이터:")
    print("="*70)

    model_features = fetcher.fetch_weather_for_model(today)
    for key, value in sorted(model_features.items()):
        print(f"  {key}: {value}")

    print("\n" + "="*70)
    print("특정 날짜 조회 예제 (2024-01-01)")
    print("="*70)

    specific_date = "2024-01-01"
    weather = fetcher.fetch_historical_weather(specific_date)
    if weather:
        print(f"\n{specific_date}의 날씨:")
        for key, value in weather.items():
            print(f"  {key}: {value}")


if __name__ == '__main__':
    example_usage()
