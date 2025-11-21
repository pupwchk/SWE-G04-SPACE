"""
Fatigue Prediction API 테스트 스크립트

사용법:
  python test_fatigue_api.py
"""

import requests
import json
from datetime import datetime, timedelta

# API 엔드포인트
BASE_URL = "http://localhost:11325/api/fatigue"

# 샘플 데이터 (실제 pmdata에서 추출한 평균값 기반)
def generate_sample_request():
    """샘플 예측 요청 생성"""

    # 건강 데이터 (Apple Watch HealthKit)
    health_data = {
        "sleep_duration": 420,  # 7시간 (분)
        "sleep_time_in_bed": 450,  # 7.5시간
        "sleep_deep": 120,  # 2시간
        "sleep_light": 200,  # 3.3시간
        "sleep_rem": 100,  # 1.7시간
        "sleep_wake": 30,  # 30분
        "hr_mean": 65,  # BPM
        "hr_min": 50,
        "hr_max": 120,
        "hr_std": 15,
        "resting_hr": 55,
        "total_steps": 8000,
        "total_distance": 5.2,  # km
        "total_calories": 2100,  # kcal
        "exercise_count": 1,
        "exercise_duration": 30,  # 분
        "exercise_calories": 250
    }

    # 날씨 데이터 (WeatherKit)
    weather_data = {
        "air_temperature": 15.5,  # °C
        "relative_humidity": 65.0,  # %
        "air_pressure_at_sea_level": 1013.25,  # hPa
        "precipitation_amount": 0,  # mm
        "cloud_area_fraction": 3.5,  # 0-10
        "duration_of_sunshine": 360  # 분 (6시간)
    }

    request_data = {
        "user_id": 1,
        "timestamp": datetime.now().isoformat(),
        "health_data": health_data,
        "weather_data": weather_data
    }

    return request_data


def test_predict_fatigue():
    """피로도 예측 테스트"""
    print("=" * 60)
    print("테스트 1: 피로도 예측 (POST /api/fatigue/predict)")
    print("=" * 60)

    request_data = generate_sample_request()

    print("\n요청 데이터:")
    print(json.dumps(request_data, indent=2))

    try:
        response = requests.post(
            f"{BASE_URL}/predict",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )

        print(f"\n응답 상태 코드: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("\n예측 결과:")
            print(f"  피로도 수준: {result['fatigue_level']} ({result['fatigue_level_kr']})")
            print(f"  피로도 클래스: {result['fatigue_class']}")
            print(f"  신뢰도: {result['confidence']:.2%}")
            print(f"\n  클래스 확률:")
            for level, prob in result['class_probabilities'].items():
                print(f"    {level}: {prob:.2%}")
            print(f"\n  권장사항:")
            for i, rec in enumerate(result['recommendations'], 1):
                print(f"    {i}. {rec}")
        else:
            print(f"\n오류: {response.text}")

    except Exception as e:
        print(f"\n예외 발생: {e}")


def test_get_history():
    """피로도 기록 조회 테스트"""
    print("\n" + "=" * 60)
    print("테스트 2: 피로도 기록 조회 (GET /api/fatigue/history/1)")
    print("=" * 60)

    try:
        response = requests.get(f"{BASE_URL}/history/1?days=7")

        print(f"\n응답 상태 코드: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"\n사용자 ID: {result['user_id']}")
            print(f"기록 개수: {len(result['history'])}개")

            if result['summary']:
                print(f"\n요약 통계:")
                print(f"  평균 클래스: {result['summary']['average_class']:.2f}")
                print(f"  분포:")
                for level, count in result['summary']['distribution'].items():
                    print(f"    {level}: {count}개")
        else:
            print(f"\n오류: {response.text}")

    except Exception as e:
        print(f"\n예외 발생: {e}")


def test_feature_importance():
    """피처 중요도 조회 테스트"""
    print("\n" + "=" * 60)
    print("테스트 3: 피처 중요도 조회 (GET /api/fatigue/feature-importance)")
    print("=" * 60)

    try:
        response = requests.get(f"{BASE_URL}/feature-importance?top_n=10")

        print(f"\n응답 상태 코드: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"\n상위 {result['top_n']}개 피처:")
            for i, feat in enumerate(result['feature_importance'], 1):
                print(f"  {i:2d}. {feat['feature']:30s}: {feat['importance']:.4f}")
        else:
            print(f"\n오류: {response.text}")

    except Exception as e:
        print(f"\n예외 발생: {e}")


def test_model_info():
    """모델 정보 조회 테스트"""
    print("\n" + "=" * 60)
    print("테스트 4: 모델 정보 조회 (GET /api/fatigue/model-info)")
    print("=" * 60)

    try:
        response = requests.get(f"{BASE_URL}/model-info")

        print(f"\n응답 상태 코드: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("\n모델 정보:")
            print(f"  모델 타입: {result['model_type']}")
            print(f"  클래스 개수: {result['num_classes']}")
            print(f"  클래스 이름: {', '.join(result['class_names'])}")
            print(f"  CV 전략: {result['cv_strategy']}")
            print(f"\n  피처 개수:")
            for key, value in result['features'].items():
                print(f"    {key}: {value}")
        else:
            print(f"\n오류: {response.text}")

    except Exception as e:
        print(f"\n예외 발생: {e}")


def test_scenario_low_fatigue():
    """시나리오 테스트: 낮은 피로도"""
    print("\n" + "=" * 60)
    print("시나리오 테스트: 낮은 피로도 (충분한 수면, 낮은 심박수)")
    print("=" * 60)

    request_data = generate_sample_request()

    # 낮은 피로도 시나리오: 충분한 수면, 낮은 심박수, 활동적
    request_data["health_data"]["sleep_duration"] = 480  # 8시간
    request_data["health_data"]["sleep_deep"] = 150  # 깊은 수면 많음
    request_data["health_data"]["resting_hr"] = 52  # 낮은 안정시 심박수
    request_data["health_data"]["total_steps"] = 12000  # 많은 활동량

    try:
        response = requests.post(f"{BASE_URL}/predict", json=request_data)

        if response.status_code == 200:
            result = response.json()
            print(f"\n예측: {result['fatigue_level']} (신뢰도 {result['confidence']:.2%})")
            print(f"권장사항: {result['recommendations'][0]}")
        else:
            print(f"오류: {response.text}")

    except Exception as e:
        print(f"예외 발생: {e}")


def test_scenario_high_fatigue():
    """시나리오 테스트: 높은 피로도"""
    print("\n" + "=" * 60)
    print("시나리오 테스트: 높은 피로도 (수면 부족, 높은 심박수)")
    print("=" * 60)

    request_data = generate_sample_request()

    # 높은 피로도 시나리오: 수면 부족, 높은 심박수, 낮은 활동량
    request_data["health_data"]["sleep_duration"] = 300  # 5시간
    request_data["health_data"]["sleep_deep"] = 60  # 깊은 수면 부족
    request_data["health_data"]["resting_hr"] = 68  # 높은 안정시 심박수
    request_data["health_data"]["total_steps"] = 3000  # 낮은 활동량
    request_data["health_data"]["exercise_duration"] = 0  # 운동 없음

    try:
        response = requests.post(f"{BASE_URL}/predict", json=request_data)

        if response.status_code == 200:
            result = response.json()
            print(f"\n예측: {result['fatigue_level']} (신뢰도 {result['confidence']:.2%})")
            print(f"권장사항: {result['recommendations'][0]}")
        else:
            print(f"오류: {response.text}")

    except Exception as e:
        print(f"예외 발생: {e}")


if __name__ == "__main__":
    print("\n")
    print("#" * 60)
    print("#  Fatigue Prediction API 테스트")
    print("#" * 60)
    print("\n")

    # 기본 테스트
    test_predict_fatigue()
    test_get_history()
    test_feature_importance()
    test_model_info()

    # 시나리오 테스트
    test_scenario_low_fatigue()
    test_scenario_high_fatigue()

    print("\n" + "#" * 60)
    print("#  테스트 완료")
    print("#" * 60 + "\n")
