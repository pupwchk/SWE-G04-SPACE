"""
Quick Demo of SPACE Stress Detection Module
Auto-run version without user input
"""

import time
import random
from datetime import datetime

from hrv_calculator import HRVCalculator, RollingHRVCalculator
from stress_detector import StressDetector, StressLevel
from realtime_monitor import RealtimeStressMonitor


def demo_basic_hrv():
    """Demo: Basic HRV Calculation"""
    print("=" * 60)
    print("Demo 1: Basic HRV Calculation")
    print("=" * 60)

    # Simulate heart rate data (in BPM)
    heart_rates = [
        72, 75, 73, 76, 74, 77, 75, 73, 71, 74,
        76, 75, 77, 74, 73, 75, 76, 74, 72, 75
    ]

    # Calculate HRV metrics
    calculator = HRVCalculator()
    hrv_metrics = calculator.calculate_hrv_from_heart_rates(heart_rates)

    print(f"\nHeart Rate Data: {len(heart_rates)} measurements")
    print(f"Mean Heart Rate: {hrv_metrics.mean_hr:.1f} BPM")
    print(f"\nHRV Metrics:")
    print(f"  SDNN:  {hrv_metrics.sdnn:.2f} ms")
    print(f"  RMSSD: {hrv_metrics.rmssd:.2f} ms")
    print(f"  pNN50: {hrv_metrics.pnn50:.2f} %")
    print()


def demo_stress_detection():
    """Demo: Stress Detection"""
    print("=" * 60)
    print("Demo 2: Stress Detection from HRV")
    print("=" * 60)

    scenarios = [
        {
            'name': 'Relaxed State',
            'heart_rates': [60, 62, 61, 63, 62, 64, 63, 61, 60, 62] * 6
        },
        {
            'name': 'Moderate Stress',
            'heart_rates': [80, 82, 81, 82, 81, 83, 82, 81, 80, 82] * 6
        },
        {
            'name': 'High Stress',
            'heart_rates': [95, 96, 95, 97, 96, 98, 97, 96, 95, 96] * 6
        }
    ]

    calculator = HRVCalculator()
    detector = StressDetector()

    for scenario in scenarios:
        print(f"\n{scenario['name']}:")
        print("-" * 40)

        hrv_metrics = calculator.calculate_hrv_from_heart_rates(
            scenario['heart_rates']
        )

        assessment = detector.detect_stress(hrv_metrics)

        print(f"  Mean HR: {hrv_metrics.mean_hr:.1f} BPM")
        print(f"  RMSSD: {hrv_metrics.rmssd:.2f} ms")
        print(f"  Stress Level: {assessment.stress_level} ({assessment.stress_level.to_korean()})")
        print(f"  Stress Score: {assessment.stress_score:.1f}/100")
        print(f"  Confidence: {assessment.confidence:.2f}")

        recommendations = detector.get_stress_recommendations(assessment)
        print(f"  Recommendation: {recommendations['korean'][0]}")

    print()


def demo_realtime_monitoring():
    """Demo: Real-time Monitoring"""
    print("=" * 60)
    print("Demo 3: Real-time Stress Monitoring (10 seconds)")
    print("=" * 60)

    def on_high_stress(assessment):
        print(f"\n🚨 HIGH STRESS ALERT!")
        print(f"   Level: {assessment.stress_level.to_korean()}")
        print(f"   Score: {assessment.stress_score:.1f}/100")

    monitor = RealtimeStressMonitor(
        window_size=60,
        update_interval=2,
        on_high_stress_alert=on_high_stress
    )

    print("\nSimulating Apple Watch heart rate stream...")
    print("(Gradually increasing stress)\n")

    base_hr = 65
    for i in range(50):
        stress_factor = min(i / 25, 1.5)
        hr = base_hr + (25 * stress_factor) + random.gauss(0, 2)

        assessment = monitor.add_heart_rate(hr)

        if assessment and i % 5 == 0:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                  f"HR: {hr:.0f} BPM | "
                  f"Stress: {assessment.stress_level.name} "
                  f"({assessment.stress_score:.0f}/100)")

        time.sleep(0.2)

    print("\n" + "=" * 60)
    print("Monitoring Complete")
    print("=" * 60)

    trend = monitor.get_stress_trend(duration_minutes=10)
    if trend:
        avg_score = sum(a.stress_score for a in trend) / len(trend)
        print(f"Average Stress Score: {avg_score:.1f}/100")
        print(f"Number of Assessments: {len(trend)}")
        print(f"Stress Increasing: {monitor.is_stress_increasing()}")

    print()


def main():
    """Run all demos"""
    print("\n")
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "SPACE Stress Detection Demo" + " " * 21 + "║")
    print("╚" + "═" * 58 + "╝")
    print("\n")

    try:
        demo_basic_hrv()
        time.sleep(1)

        demo_stress_detection()
        time.sleep(1)

        demo_realtime_monitoring()

    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")

    print("\n✓ Demo completed!")
    print("\nFor more examples, run: python example_usage.py\n")


if __name__ == "__main__":
    main()
