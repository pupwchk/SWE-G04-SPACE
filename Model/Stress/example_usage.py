"""
Example Usage of SPACE Stress Detection Module

Demonstrates how to use the stress monitoring system with simulated
Apple Watch heart rate data.
"""

import time
import random
from datetime import datetime

from hrv_calculator import HRVCalculator, RollingHRVCalculator
from stress_detector import StressDetector, StressLevel
from realtime_monitor import RealtimeStressMonitor, StressMonitorSession


def example_1_basic_hrv_calculation():
    """
    Example 1: Calculate HRV metrics from a list of heart rates
    """
    print("=" * 60)
    print("Example 1: Basic HRV Calculation")
    print("=" * 60)

    # Simulate heart rate data (in BPM)
    heart_rates = [
        72, 75, 73, 76, 74, 77, 75, 73, 71, 74,
        76, 75, 77, 74, 73, 75, 76, 74, 72, 75,
        73, 76, 75, 74, 77, 73, 75, 76, 74, 72
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


def example_2_stress_detection():
    """
    Example 2: Detect stress level from HRV metrics
    """
    print("=" * 60)
    print("Example 2: Stress Detection from HRV")
    print("=" * 60)

    # Simulate different stress scenarios
    scenarios = [
        {
            'name': 'Relaxed State',
            'heart_rates': [60, 62, 61, 63, 62, 64, 63, 61, 60, 62] * 6
        },
        {
            'name': 'Normal State',
            'heart_rates': [70, 72, 71, 73, 72, 74, 73, 71, 70, 72] * 6
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

        # Calculate HRV
        hrv_metrics = calculator.calculate_hrv_from_heart_rates(
            scenario['heart_rates']
        )

        # Detect stress
        assessment = detector.detect_stress(hrv_metrics)

        print(f"  Mean HR: {hrv_metrics.mean_hr:.1f} BPM")
        print(f"  RMSSD: {hrv_metrics.rmssd:.2f} ms")
        print(f"  Stress Level: {assessment.stress_level} ({assessment.stress_level.to_korean()})")
        print(f"  Stress Score: {assessment.stress_score:.1f}/100")
        print(f"  Confidence: {assessment.confidence:.2f}")
        print(f"  Reasoning: {assessment.reasoning}")

        # Get recommendations
        recommendations = detector.get_stress_recommendations(assessment)
        print(f"  Recommendations:")
        for rec in recommendations['korean'][:2]:
            print(f"    - {rec}")

    print()


def example_3_realtime_monitoring():
    """
    Example 3: Real-time stress monitoring with callbacks
    """
    print("=" * 60)
    print("Example 3: Real-time Stress Monitoring")
    print("=" * 60)

    def on_stress_change(assessment: 'StressAssessment'):
        """Callback when stress level changes"""
        print(f"\n⚠️  Stress Level Changed: {assessment.stress_level} "
              f"({assessment.stress_level.to_korean()})")
        print(f"   Score: {assessment.stress_score:.1f}/100")

    def on_high_stress(assessment: 'StressAssessment'):
        """Callback for high stress alert"""
        print(f"\n🚨 HIGH STRESS ALERT! 🚨")
        print(f"   Level: {assessment.stress_level.to_korean()}")
        print(f"   Score: {assessment.stress_score:.1f}/100")
        print(f"   Take a break and practice deep breathing!")

    # Create monitor with callbacks
    monitor = RealtimeStressMonitor(
        window_size=60,
        update_interval=5,  # Update every 5 seconds
        on_stress_change=on_stress_change,
        on_high_stress_alert=on_high_stress
    )

    print("\nSimulating Apple Watch heart rate stream...")
    print("(Gradually increasing stress scenario)")
    print()

    # Simulate heart rate stream with increasing stress
    base_hr = 65
    for i in range(100):
        # Simulate gradually increasing heart rate (stress)
        stress_factor = min(i / 50, 1.5)
        hr = base_hr + (25 * stress_factor) + random.gauss(0, 2)

        # Add heart rate measurement
        assessment = monitor.add_heart_rate(hr)

        if assessment:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                  f"HR: {hr:.0f} BPM | "
                  f"Stress: {assessment.stress_level.name} "
                  f"({assessment.stress_score:.0f}/100)")

        # Simulate real-time delay
        time.sleep(0.1)

    # Get session summary
    print("\n" + "=" * 60)
    print("Monitoring Session Summary")
    print("=" * 60)

    trend = monitor.get_stress_trend(duration_minutes=10)
    if trend:
        avg_score = sum(a.stress_score for a in trend) / len(trend)
        print(f"Average Stress Score: {avg_score:.1f}/100")
        print(f"Number of Assessments: {len(trend)}")
        print(f"Stress Increasing: {monitor.is_stress_increasing()}")

    print()


def example_4_session_context_manager():
    """
    Example 4: Using session context manager
    """
    print("=" * 60)
    print("Example 4: Monitoring Session with Context Manager")
    print("=" * 60)

    monitor = RealtimeStressMonitor(window_size=60, update_interval=2)

    with StressMonitorSession(monitor) as session:
        print("\nMonitoring session started...")

        # Simulate heart rate data
        for i in range(50):
            hr = 70 + random.gauss(0, 5)
            monitor.add_heart_rate(hr)
            time.sleep(0.05)

        print("Monitoring session ended.")

    # Get session summary
    summary = session.get_session_summary()
    print("\nSession Summary:")
    print(f"  Duration: {summary['duration_minutes']:.1f} minutes")
    print(f"  Assessments: {summary['num_assessments']}")
    if summary['num_assessments'] > 0:
        print(f"  Average Stress: {summary['average_stress_score']:.1f}/100")
        print(f"  Stress Range: {summary['min_stress_score']:.1f} - {summary['max_stress_score']:.1f}")
        print(f"  High Stress Episodes: {summary['high_stress_episodes']}")
    print()


def example_5_apple_watch_integration():
    """
    Example 5: Simulated Apple Watch integration
    """
    print("=" * 60)
    print("Example 5: Simulated Apple Watch Integration")
    print("=" * 60)

    print("""
This example shows how to integrate with Apple Watch HealthKit data.

In a real iOS app, you would:

1. Request HealthKit permissions:
   - HKQuantityTypeIdentifierHeartRate

2. Start background heart rate updates:
   ```swift
   let heartRateType = HKQuantityType.quantityType(
       forIdentifier: .heartRate
   )!

   let query = HKAnchoredObjectQuery(
       type: heartRateType,
       predicate: nil,
       anchor: nil,
       limit: HKObjectQueryNoLimit
   ) { query, samples, deletedObjects, anchor, error in
       guard let samples = samples as? [HKQuantitySample] else {
           return
       }

       for sample in samples {
           let hr = sample.quantity.doubleValue(
               for: HKUnit(from: "count/min")
           )

           // Send to backend API
           sendHeartRateToBackend(hr, timestamp: sample.startDate)
       }
   }

   healthStore.execute(query)
   ```

3. Backend receives heart rate and updates stress monitor:
   ```python
   @app.post("/api/health/heart-rate")
   async def receive_heart_rate(hr: float, timestamp: datetime):
       assessment = monitor.add_heart_rate(hr, timestamp)

       if assessment and assessment.stress_level in [
           StressLevel.HIGH, StressLevel.VERY_HIGH
       ]:
           # Trigger smart home automation
           await trigger_stress_relief_scenario(assessment)

       return assessment.to_dict()
   ```
    """)

    # Simulate receiving data from Apple Watch
    print("\nSimulating Apple Watch data stream:")
    print("-" * 40)

    monitor = RealtimeStressMonitor(window_size=60, update_interval=3)

    # Simulate Apple Watch sending HR every 5 seconds
    for i in range(20):
        hr = 72 + random.gauss(0, 3)
        timestamp = datetime.now()

        assessment = monitor.add_heart_rate(hr, timestamp)

        if assessment:
            print(f"[Apple Watch] {timestamp.strftime('%H:%M:%S')}")
            print(f"  HR: {hr:.0f} BPM")
            print(f"  Stress: {assessment.stress_level.to_korean()} "
                  f"({assessment.stress_score:.0f}/100)")

            if assessment.stress_level in [StressLevel.HIGH, StressLevel.VERY_HIGH]:
                print(f"  🏠 Triggering stress relief scenario:")
                print(f"     - Dimming lights")
                print(f"     - Playing relaxing music")
                print(f"     - Adjusting temperature")

        time.sleep(0.5)

    print()


def main():
    """Run all examples"""
    examples = [
        example_1_basic_hrv_calculation,
        example_2_stress_detection,
        example_3_realtime_monitoring,
        example_4_session_context_manager,
        example_5_apple_watch_integration
    ]

    for i, example in enumerate(examples, 1):
        try:
            example()
        except KeyboardInterrupt:
            print("\n\nExample interrupted by user.")
            break
        except Exception as e:
            print(f"\n❌ Error in example {i}: {e}")

        if i < len(examples):
            input("Press Enter to continue to next example...")
            print("\n" * 2)


if __name__ == "__main__":
    main()
