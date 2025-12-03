"""
API 테스트 스크립트
서버가 실행 중일 때 이 스크립트로 심박수 데이터를 전송하고 스트레스 평가를 받을 수 있습니다.
"""

import requests
import time
import random
from datetime import datetime, timezone

# API 설정
BASE_URL = "http://localhost:11325/api/stress"
USER_ID = 1


def send_heart_rate(heart_rate: float):
    """심박수 데이터 전송"""
    url = f"{BASE_URL}/heart-rate"

    data = {
        "user_id": USER_ID,
        "heart_rate": heart_rate,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "device_id": "test-device"
    }

    response = requests.post(url, json=data)

    if response.status_code == 200:
        result = response.json()
        if result is None:
            print(f"[HR: {heart_rate:.0f} BPM] 데이터 수집 중...")
        else:
            print(f"[HR: {heart_rate:.0f} BPM] 스트레스: {result['stress_level_kr']} ({result['stress_score']:.0f}/100)")
        return result
    else:
        print(f"오류: {response.status_code} - {response.text}")
        return None


def get_current_stress():
    """현재 스트레스 조회"""
    url = f"{BASE_URL}/current/{USER_ID}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        return None


def get_stress_trend(duration_minutes=60):
    """스트레스 트렌드 조회"""
    url = f"{BASE_URL}/trend/{USER_ID}?duration_minutes={duration_minutes}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        return None


def reset_monitor():
    """모니터 초기화"""
    url = f"{BASE_URL}/reset/{USER_ID}"
    response = requests.delete(url)

    if response.status_code == 200:
        print("✓ 모니터 초기화 완료")
    else:
        print(f"오류: {response.status_code}")


def simulate_heart_rate_stream():
    """심박수 스트림 시뮬레이션"""
    print("=" * 60)
    print("심박수 스트림 시뮬레이션")
    print("=" * 60)
    print()

    # 시나리오 1: 이완 상태 → 스트레스 상승
    base_hr = 65

    print("시나리오: 이완 상태에서 점진적 스트레스 상승\n")

    for i in range(80):
        # 점진적 심박수 증가
        stress_factor = min(i / 40, 1.5)
        hr = base_hr + (30 * stress_factor) + random.gauss(0, 2)

        # 심박수 전송
        result = send_heart_rate(hr)

        # 고 스트레스 감지 시 알림
        if result and result.get('stress_score', 0) >= 80:
            print("  🚨 고 스트레스 감지! 스마트홈 자동화 트리거")

        time.sleep(0.5)

    print("\n" + "=" * 60)
    print("시뮬레이션 완료")
    print("=" * 60)


def show_summary():
    """결과 요약 표시"""
    print("\n현재 스트레스 상태:")
    print("-" * 40)

    current = get_current_stress()
    if current:
        print(f"레벨: {current['stress_level_kr']}")
        print(f"점수: {current['stress_score']:.0f}/100")
        print(f"신뢰도: {current['confidence']:.0%}")

    print("\n스트레스 트렌드 (최근 60분):")
    print("-" * 40)

    trend = get_stress_trend(60)
    if trend and trend['summary']:
        summary = trend['summary']
        print(f"평균 스트레스: {summary['average_stress']:.1f}/100")
        print(f"최소 스트레스: {summary['min_stress']:.1f}/100")
        print(f"최대 스트레스: {summary['max_stress']:.1f}/100")
        print(f"평가 횟수: {summary['count']}회")
        print(f"스트레스 증가 중: {'예' if summary['is_increasing'] else '아니오'}")

        print(f"\n스트레스 레벨 분포:")
        dist = summary['stress_level_distribution']
        print(f"  매우 낮음: {dist['very_low']}회")
        print(f"  낮음:     {dist['low']}회")
        print(f"  보통:     {dist['moderate']}회")
        print(f"  높음:     {dist['high']}회")
        print(f"  매우 높음: {dist['very_high']}회")


def main():
    """메인 함수"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 16 + "API 테스트 스크립트" + " " * 23 + "║")
    print("╚" + "═" * 58 + "╝")
    print("\n")

    # 서버 연결 확인
    try:
        response = requests.get("http://localhost:11325/")
        print("✓ 서버 연결 성공\n")
    except Exception as e:
        print(f"❌ 서버 연결 실패: {e}")
        print("\n서버를 먼저 시작하세요:")
        print("  cd BackEnd/fastapi-starter")
        print("  uvicorn app.main:app --reload --port 11325")
        return

    try:
        # 모니터 초기화
        reset_monitor()

        # 심박수 스트림 시뮬레이션
        simulate_heart_rate_stream()

        # 결과 요약
        show_summary()

    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단됨")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

    print("\n")


if __name__ == "__main__":
    main()
