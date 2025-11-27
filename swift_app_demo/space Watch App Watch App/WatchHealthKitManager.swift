//
//  WatchHealthKitManager.swift
//  space Watch App
//
//  HealthKit manager for Apple Watch - collects health data during workouts
//

import Foundation
import HealthKit
import Combine

/// HealthKit manager for Apple Watch
class WatchHealthKitManager: NSObject, ObservableObject {
    static let shared = WatchHealthKitManager()

    // MARK: - Published Properties

    @Published var isAvailable = false
    @Published var authorizationStatus: HKAuthorizationStatus = .notDetermined
    @Published var isWorkoutActive = false

    // Real-time metrics
    @Published var currentHeartRate: Double = 0.0 // bpm
    @Published var totalCalories: Double = 0.0 // kcal
    @Published var totalSteps: Int = 0
    @Published var totalDistance: Double = 0.0 // meters
    @Published var activeMinutes: Int = 0

    // MARK: - Private Properties

    private let healthStore = HKHealthStore()
    private var workoutSession: HKWorkoutSession?
    private var workoutBuilder: HKLiveWorkoutBuilder?
    private var startDate: Date?

    // Queries
    private var heartRateQuery: HKQuery?
    private var activeEnergyQuery: HKQuery?

    // MARK: - Initialization

    private override init() {
        super.init()
        checkAvailability()
    }

    // MARK: - Availability

    private func checkAvailability() {
        isAvailable = HKHealthStore.isHealthDataAvailable()

        if isAvailable {
            print("⌚ HealthKit is available on Watch")
        } else {
            print("  HealthKit is not available on this Watch")
        }
    }

    // MARK: - Authorization

    func requestAuthorization() {
        guard isAvailable else {
            print("  HealthKit not available")
            return
        }

        let typesToRead: Set<HKObjectType> = [
            HKObjectType.quantityType(forIdentifier: .heartRate)!,
            HKObjectType.quantityType(forIdentifier: .activeEnergyBurned)!,
            HKObjectType.quantityType(forIdentifier: .stepCount)!,
            HKObjectType.quantityType(forIdentifier: .distanceWalkingRunning)!,
            HKObjectType.quantityType(forIdentifier: .appleExerciseTime)!
        ]

        let typesToShare: Set<HKSampleType> = [
            HKObjectType.workoutType(),
            HKObjectType.quantityType(forIdentifier: .heartRate)!,
            HKObjectType.quantityType(forIdentifier: .activeEnergyBurned)!,
            HKObjectType.quantityType(forIdentifier: .stepCount)!,
            HKObjectType.quantityType(forIdentifier: .distanceWalkingRunning)!
        ]

        healthStore.requestAuthorization(toShare: typesToShare, read: typesToRead) { success, error in
            DispatchQueue.main.async {
                if success {
                    print(" HealthKit authorization granted on Watch")
                } else {
                    print("  HealthKit authorization denied: \(error?.localizedDescription ?? "Unknown error")")
                }
            }
        }
    }

    // MARK: - Workout Session

    func startWorkout() {
        guard !isWorkoutActive else {
            print("⚠️ Workout already active")
            return
        }

        // Request authorization if needed
        if authorizationStatus == .notDetermined {
            requestAuthorization()
        }

        // Create workout configuration
        let configuration = HKWorkoutConfiguration()
        configuration.activityType = .walking // Can be changed to .running, .cycling, etc.
        configuration.locationType = .outdoor

        do {
            // Create workout session
            workoutSession = try HKWorkoutSession(healthStore: healthStore, configuration: configuration)
            workoutBuilder = workoutSession?.associatedWorkoutBuilder()

            // Set delegate
            workoutSession?.delegate = self
            workoutBuilder?.delegate = self

            // Set data source
            workoutBuilder?.dataSource = HKLiveWorkoutDataSource(
                healthStore: healthStore,
                workoutConfiguration: configuration
            )

            // Start session
            startDate = Date()
            workoutSession?.startActivity(with: startDate)
            workoutBuilder?.beginCollection(withStart: startDate!) { success, error in
                if success {
                    print(" Workout session started")
                    DispatchQueue.main.async {
                        self.isWorkoutActive = true
                        self.startRealtimeQueries()
                    }
                } else {
                    print("  Failed to start workout: \(error?.localizedDescription ?? "Unknown")")
                }
            }

        } catch {
            print("  Failed to create workout session: \(error.localizedDescription)")
        }
    }

    func stopWorkout() {
        guard isWorkoutActive, let session = workoutSession else {
            print("⚠️ No active workout")
            return
        }

        // Stop real-time queries
        stopRealtimeQueries()

        // End workout session
        let endDate = Date()
        session.end()

        // Finish collection
        workoutBuilder?.endCollection(withEnd: endDate) { success, error in
            if success {
                print(" Workout collection ended")

                // Finish workout
                self.workoutBuilder?.finishWorkout { workout, error in
                    if let workout = workout {
                        print(" Workout finished and saved to HealthKit")
                        print("📊 Duration: \(workout.duration)s, Calories: \(workout.totalEnergyBurned?.doubleValue(for: .kilocalorie()) ?? 0) kcal")

                        // Send final data to iPhone
                        self.sendHealthDataToiPhone()
                    } else {
                        print("  Failed to finish workout: \(error?.localizedDescription ?? "Unknown")")
                    }

                    DispatchQueue.main.async {
                        self.isWorkoutActive = false
                        self.resetMetrics()
                    }
                }
            } else {
                print("  Failed to end collection: \(error?.localizedDescription ?? "Unknown")")
            }
        }
    }

    // MARK: - Real-time Queries

    private func startRealtimeQueries() {
        startHeartRateQuery()
        startActiveEnergyQuery()
    }

    private func stopRealtimeQueries() {
        if let query = heartRateQuery {
            healthStore.stop(query)
        }
        if let query = activeEnergyQuery {
            healthStore.stop(query)
        }
    }

    private func startHeartRateQuery() {
        guard let heartRateType = HKObjectType.quantityType(forIdentifier: .heartRate) else { return }

        let predicate = HKQuery.predicateForSamples(
            withStart: startDate,
            end: nil,
            options: .strictStartDate
        )

        let query = HKAnchoredObjectQuery(
            type: heartRateType,
            predicate: predicate,
            anchor: nil,
            limit: HKObjectQueryNoLimit
        ) { _, samples, _, _, error in
            self.processHeartRateSamples(samples)
        }

        query.updateHandler = { _, samples, _, _, error in
            self.processHeartRateSamples(samples)
        }

        heartRateQuery = query
        healthStore.execute(query)
    }

    private func processHeartRateSamples(_ samples: [HKSample]?) {
        guard let samples = samples as? [HKQuantitySample] else { return }

        for sample in samples {
            let heartRate = sample.quantity.doubleValue(for: HKUnit(from: "count/min"))

            DispatchQueue.main.async {
                self.currentHeartRate = heartRate
                print("❤️ Heart Rate: \(Int(heartRate)) bpm")
            }
        }
    }

    private func startActiveEnergyQuery() {
        guard let energyType = HKObjectType.quantityType(forIdentifier: .activeEnergyBurned) else { return }

        let predicate = HKQuery.predicateForSamples(
            withStart: startDate,
            end: nil,
            options: .strictStartDate
        )

        let query = HKStatisticsQuery(
            quantityType: energyType,
            quantitySamplePredicate: predicate,
            options: .cumulativeSum
        ) { _, result, error in
            if let sum = result?.sumQuantity() {
                let calories = sum.doubleValue(for: .kilocalorie())

                DispatchQueue.main.async {
                    self.totalCalories = calories
                    print("🔥 Calories: \(Int(calories)) kcal")
                }
            }
        }

        activeEnergyQuery = query
        healthStore.execute(query)
    }

    // MARK: - Send Data to iPhone

    private func sendHealthDataToiPhone() {
        WatchConnectivityManager.shared.sendHealthData(
            heartRate: currentHeartRate > 0 ? currentHeartRate : nil,
            calories: totalCalories > 0 ? totalCalories : nil,
            steps: totalSteps > 0 ? totalSteps : nil,
            distance: totalDistance > 0 ? totalDistance : nil
        )

        print("📤 Health data sent to iPhone")
    }

    // Periodic data sending (every 30 seconds during workout)
    private var sendTimer: Timer?

    private func startPeriodicSending() {
        sendTimer = Timer.scheduledTimer(withTimeInterval: 30, repeats: true) { [weak self] _ in
            self?.sendHealthDataToiPhone()
        }
    }

    private func stopPeriodicSending() {
        sendTimer?.invalidate()
        sendTimer = nil
    }

    // MARK: - Reset

    private func resetMetrics() {
        currentHeartRate = 0.0
        totalCalories = 0.0
        totalSteps = 0
        totalDistance = 0.0
        activeMinutes = 0
    }
}

// MARK: - HKWorkoutSessionDelegate

extension WatchHealthKitManager: HKWorkoutSessionDelegate {

    func workoutSession(_ workoutSession: HKWorkoutSession, didChangeTo toState: HKWorkoutSessionState, from fromState: HKWorkoutSessionState, date: Date) {
        DispatchQueue.main.async {
            switch toState {
            case .running:
                print(" Workout session running")
                self.startPeriodicSending()
            case .ended:
                print("🛑 Workout session ended")
                self.stopPeriodicSending()
            case .paused:
                print("⏸️ Workout session paused")
            case .prepared:
                print("📝 Workout session prepared")
            case .stopped:
                print("🛑 Workout session stopped")
            default:
                break
            }
        }
    }

    func workoutSession(_ workoutSession: HKWorkoutSession, didFailWithError error: Error) {
        print("  Workout session failed: \(error.localizedDescription)")
        DispatchQueue.main.async {
            self.isWorkoutActive = false
        }
    }
}

// MARK: - HKLiveWorkoutBuilderDelegate

extension WatchHealthKitManager: HKLiveWorkoutBuilderDelegate {

    func workoutBuilder(_ workoutBuilder: HKLiveWorkoutBuilder, didCollectDataOf collectedTypes: Set<HKSampleType>) {
        // Process collected statistics
        for type in collectedTypes {
            guard let quantityType = type as? HKQuantityType else { continue }

            if let statistics = workoutBuilder.statistics(for: quantityType) {
                updateMetrics(for: quantityType, statistics: statistics)
            }
        }
    }

    func workoutBuilderDidCollectEvent(_ workoutBuilder: HKLiveWorkoutBuilder) {
        // Handle workout events if needed
    }

    private func updateMetrics(for type: HKQuantityType, statistics: HKStatistics) {
        DispatchQueue.main.async {
            switch type.identifier {
            case HKQuantityTypeIdentifier.heartRate.rawValue:
                if let average = statistics.averageQuantity() {
                    self.currentHeartRate = average.doubleValue(for: HKUnit(from: "count/min"))
                }

            case HKQuantityTypeIdentifier.activeEnergyBurned.rawValue:
                if let sum = statistics.sumQuantity() {
                    self.totalCalories = sum.doubleValue(for: .kilocalorie())
                }

            case HKQuantityTypeIdentifier.stepCount.rawValue:
                if let sum = statistics.sumQuantity() {
                    self.totalSteps = Int(sum.doubleValue(for: .count()))
                }

            case HKQuantityTypeIdentifier.distanceWalkingRunning.rawValue:
                if let sum = statistics.sumQuantity() {
                    self.totalDistance = sum.doubleValue(for: .meter())
                }

            case HKQuantityTypeIdentifier.appleExerciseTime.rawValue:
                if let sum = statistics.sumQuantity() {
                    self.activeMinutes = Int(sum.doubleValue(for: .minute()))
                }

            default:
                break
            }
        }
    }
}
