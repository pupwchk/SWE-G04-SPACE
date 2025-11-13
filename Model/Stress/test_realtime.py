"""
Test script for realtime_monitor.py
실시간 모니터 테스트 스크립트
"""

import time
import random
from datetime import datetime
from realtime_monitor import RealtimeStressMonitor


def test_realtime_monitor():
    """실시간 스트레스 모니터 테스트"""

    print("=" * 60)
    print("실시간 스트레스 모니터 테스트")
    print("=" * 60)
    print()

    # 콜백 함수 정의
    def on_stress_change(assessment):
        print(f"✓ 스트레스 변화: {assessment.stress_level.to_korean()} "
              f"({assessment.stress_score:.0f}/100)")

    def on_high_stress(assessment):
        print(f"\n🚨 고 스트레스 경고!")
        print(f"   레벨: {assessment.stress_level.to_korean()}")
        print(f"   점수: {assessment.stress_score:.0f}/100")
        print(f"   권장: 휴식을 취하세요\n")

    # 모니터 생성
    monitor = RealtimeStressMonitor(
        window_size=60,
        update_interval=3,
        on_stress_change=on_stress_change,
        on_high_stress_alert=on_high_stress
    )

    print("심박수 스트림 시뮬레이션 시작...")
    print("(30초 동안 스트레스가 점진적으로 증가)")
    print()

    # 심박수 시뮬레이션
    base_hr = 65
    for i in range(60):
        # 점진적 증가
        stress_factor = min(i / 30, 1.5)
        hr = base_hr + (30 * stress_factor) + random.gauss(0, 2)

        # 심박수 추가
        assessment = monitor.add_heart_rate(hr)

        # 5회마다 출력
        if i % 5 == 0:
            if assessment:
                print(f"[{i:2d}] HR: {hr:.0f} BPM | "
                      f"스트레스: {assessment.stress_level.name:12s} "
                      f"({assessment.stress_score:.0f}/100)")
            else:
                print(f"[{i:2d}] HR: {hr:.0f} BPM | 데이터 수집 중...")

        time.sleep(0.5)

    # 결과 요약
    print("\n" + "=" * 60)
    print("모니터링 완료 - 결과 요약")
    print("=" * 60)

    # 트렌드 분석
    trend = monitor.get_stress_trend(duration_minutes=10)
    if trend:
        avg = sum(a.stress_score for a in trend) / len(trend)
        min_score = min(a.stress_score for a in trend)
        max_score = max(a.stress_score for a in trend)

        print(f"평균 스트레스: {avg:.1f}/100")
        print(f"최소 스트레스: {min_score:.1f}/100")
        print(f"최대 스트레스: {max_score:.1f}/100")
        print(f"평가 횟수: {len(trend)}회")
        print(f"스트레스 증가 중: {'예' if monitor.is_stress_increasing() else '아니오'}")

    print()


if __name__ == "__main__":
    try:
        test_realtime_monitor()
        print("✓ 테스트 완료!")
    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단됨")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
