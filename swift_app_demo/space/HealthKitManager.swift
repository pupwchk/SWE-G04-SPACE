//
//  HealthKitManager.swift
//  space
//
//  HealthKit manager for Apple Watch health data
//

import Foundation
import HealthKit
import Combine
import SwiftUI

/// HealthKit manager for retrieving health data from Apple Watch
class HealthKitManager: ObservableObject {
    static let shared = HealthKitManager()

    // MARK: - Published Properties

    @Published var isAvailable = false
    @Published var authorizationStatus: HKAuthorizationStatus = .notDetermined

    // Today's health metrics
    @Published var sleepHours: Double = 0.0 // hours
    @Published var stressLevel: Int = 0 // 0-100
    @Published var caloriesBurned: Double = 0.0 // kcal

    // Real-time metrics (from Watch or live queries)
    @Published var currentHeartRate: Double = 0.0 // bpm
    @Published var currentCalories: Double = 0.0 // kcal (active calories)
    @Published var currentSteps: Int = 0 // steps
    @Published var currentDistance: Double = 0.0 // meters
    @Published var currentActiveMinutes: Int = 0 // minutes
    @Published var currentHRV: Double = 0.0 // ms (Heart Rate Variability)

    // Historical data (last 7 days)
    @Published var weeklySleepData: [DailyHealthData] = []
    @Published var weeklyStressData: [DailyHealthData] = []
    @Published var weeklyCaloriesData: [DailyHealthData] = []

    // MARK: - Private Properties

    private let healthStore = HKHealthStore()

    // Observer queries for real-time updates
    private var heartRateObserver: HKObserverQuery?
    private var caloriesObserver: HKObserverQuery?
    private var stepsObserver: HKObserverQuery?
    private var distanceObserver: HKObserverQuery?

    // MARK: - Initialization

    init() {
        checkAvailability()
    }

    // MARK: - Availability Check

    private func checkAvailability() {
        isAvailable = HKHealthStore.isHealthDataAvailable()

        if isAvailable {
            print("✅ HealthKit is available")
        } else {
            print("❌ HealthKit is not available on this device")
        }
    }

    // MARK: - Authorization

    func requestAuthorization(completion: ((Bool) -> Void)? = nil) {
        guard isAvailable else {
            print("❌ HealthKit not available")
            completion?(false)
            return
        }

        let readTypes: Set<HKObjectType> = [
            HKObjectType.categoryType(forIdentifier: .sleepAnalysis)!,
            HKObjectType.quantityType(forIdentifier: .activeEnergyBurned)!,
            HKObjectType.quantityType(forIdentifier: .heartRateVariabilitySDNN)!, // Proxy for stress
            HKObjectType.quantityType(forIdentifier: .restingHeartRate)!,
            HKObjectType.quantityType(forIdentifier: .heartRate)!, // Real-time heart rate
            HKObjectType.quantityType(forIdentifier: .stepCount)!, // Real-time steps
            HKObjectType.quantityType(forIdentifier: .distanceWalkingRunning)! // Real-time distance
        ]

        healthStore.requestAuthorization(toShare: nil, read: readTypes) { success, error in
            DispatchQueue.main.async {
                if success {
                    print("✅ HealthKit authorization granted")
                    self.authorizationStatus = .sharingAuthorized
                    self.fetchTodayHealthData()
                    self.fetchWeeklyHealthData()
                    completion?(true)
                } else {
                    print("❌ HealthKit authorization denied: \(error?.localizedDescription ?? "Unknown error")")
                    completion?(false)
                }
            }
        }
    }

    // MARK: - Fetch Real Data (for actual device)

    func fetchTodayHealthData() {
        let calendar = Calendar.current
        let today = calendar.startOfDay(for: Date())
        let tomorrow = calendar.date(byAdding: .day, value: 1, to: today)!

        fetchSleepData(from: today, to: tomorrow)
        fetchCaloriesData(from: today, to: tomorrow)
        fetchStressData(from: today, to: tomorrow)
    }

    func fetchWeeklyHealthData() {
        let calendar = Calendar.current
        let today = calendar.startOfDay(for: Date())
        let weekAgo = calendar.date(byAdding: .day, value: -7, to: today)!

        fetchWeeklySleep(from: weekAgo, to: today)
        fetchWeeklyCalories(from: weekAgo, to: today)
        fetchWeeklyStress(from: weekAgo, to: today)
    }

    private func fetchSleepData(from startDate: Date, to endDate: Date) {
        guard let sleepType = HKObjectType.categoryType(forIdentifier: .sleepAnalysis) else { return }

        let predicate = HKQuery.predicateForSamples(withStart: startDate, end: endDate, options: .strictStartDate)

        let query = HKSampleQuery(sampleType: sleepType, predicate: predicate, limit: HKObjectQueryNoLimit, sortDescriptors: nil) { _, samples, error in
            guard let samples = samples as? [HKCategorySample], error == nil else {
                print("❌ Sleep data fetch error: \(error?.localizedDescription ?? "Unknown")")
                return
            }

            var totalSleepSeconds: TimeInterval = 0

            for sample in samples {
                if sample.value == HKCategoryValueSleepAnalysis.asleepUnspecified.rawValue ||
                   sample.value == HKCategoryValueSleepAnalysis.asleepCore.rawValue ||
                   sample.value == HKCategoryValueSleepAnalysis.asleepDeep.rawValue ||
                   sample.value == HKCategoryValueSleepAnalysis.asleepREM.rawValue {
                    totalSleepSeconds += sample.endDate.timeIntervalSince(sample.startDate)
                }
            }

            DispatchQueue.main.async {
                self.sleepHours = totalSleepSeconds / 3600.0
                print("😴 Sleep: \(String(format: "%.1f", self.sleepHours)) hours")
            }
        }

        healthStore.execute(query)
    }

    private func fetchCaloriesData(from startDate: Date, to endDate: Date) {
        guard let caloriesType = HKObjectType.quantityType(forIdentifier: .activeEnergyBurned) else { return }

        let predicate = HKQuery.predicateForSamples(withStart: startDate, end: endDate, options: .strictStartDate)

        let query = HKStatisticsQuery(quantityType: caloriesType, quantitySamplePredicate: predicate, options: .cumulativeSum) { _, result, error in
            guard let result = result, let sum = result.sumQuantity(), error == nil else {
                print("❌ Calories data fetch error: \(error?.localizedDescription ?? "Unknown")")
                return
            }

            DispatchQueue.main.async {
                self.caloriesBurned = sum.doubleValue(for: .kilocalorie())
                print("🔥 Calories: \(String(format: "%.0f", self.caloriesBurned)) kcal")
            }
        }

        healthStore.execute(query)
    }

    private func fetchStressData(from startDate: Date, to endDate: Date) {
        // Note: There's no direct "stress" metric in HealthKit
        // We use Heart Rate Variability (HRV) as a proxy
        // Lower HRV typically indicates higher stress

        guard let hrvType = HKObjectType.quantityType(forIdentifier: .heartRateVariabilitySDNN) else { return }

        let predicate = HKQuery.predicateForSamples(withStart: startDate, end: endDate, options: .strictStartDate)

        let query = HKStatisticsQuery(quantityType: hrvType, quantitySamplePredicate: predicate, options: .discreteAverage) { _, result, error in
            guard let result = result, let average = result.averageQuantity(), error == nil else {
                print("❌ HRV data fetch error: \(error?.localizedDescription ?? "Unknown")")
                return
            }

            let hrvValue = average.doubleValue(for: HKUnit.secondUnit(with: .milli))

            // Convert HRV to stress level (inverse relationship)
            // Normal HRV range: 20-100ms
            // Higher HRV = Lower stress
            let stressLevel = max(0, min(100, Int(100 - hrvValue)))

            DispatchQueue.main.async {
                self.currentHRV = hrvValue
                self.stressLevel = stressLevel
                print("😰 Stress: \(stressLevel)% (HRV: \(String(format: "%.1f", hrvValue))ms)")
            }
        }

        healthStore.execute(query)
    }

    private func fetchWeeklySleep(from startDate: Date, to endDate: Date) {
        guard let sleepType = HKObjectType.categoryType(forIdentifier: .sleepAnalysis) else { return }

        let predicate = HKQuery.predicateForSamples(withStart: startDate, end: endDate, options: .strictStartDate)
        let sortDescriptor = NSSortDescriptor(key: HKSampleSortIdentifierStartDate, ascending: true)

        let query = HKSampleQuery(sampleType: sleepType, predicate: predicate, limit: HKObjectQueryNoLimit, sortDescriptors: [sortDescriptor]) { _, samples, error in
            guard let samples = samples as? [HKCategorySample], error == nil else {
                print("❌ Weekly sleep fetch error: \(error?.localizedDescription ?? "Unknown")")
                return
            }
            // Group samples by day
            let calendar = Calendar.current
            var sleepByDay: [Date: TimeInterval] = [:]

            for sample in samples {
                // Only count actual sleep states
                if sample.value == HKCategoryValueSleepAnalysis.asleepUnspecified.rawValue ||
                   sample.value == HKCategoryValueSleepAnalysis.asleepCore.rawValue ||
                   sample.value == HKCategoryValueSleepAnalysis.asleepDeep.rawValue ||
                   sample.value == HKCategoryValueSleepAnalysis.asleepREM.rawValue {

                    let dayStart = calendar.startOfDay(for: sample.startDate)
                    let duration = sample.endDate.timeIntervalSince(sample.startDate)
                    sleepByDay[dayStart, default: 0] += duration
                }
            }

            // Create array with all 7 days, filling missing days with 0
            var weeklyData: [DailyHealthData] = []
            for dayOffset in 0..<7 {
                if let date = calendar.date(byAdding: .day, value: dayOffset, to: startDate) {
                    let dayStart = calendar.startOfDay(for: date)
                    let totalSeconds = sleepByDay[dayStart] ?? 0
                    weeklyData.append(DailyHealthData(date: dayStart, value: totalSeconds / 3600.0, unit: "h"))
                }
            }

            DispatchQueue.main.async {
                self.weeklySleepData = weeklyData
                print("😴 Weekly sleep data loaded: \(weeklyData.count) days")
            }
        }

        healthStore.execute(query)
    }

    private func fetchWeeklyCalories(from startDate: Date, to endDate: Date) {
        guard let caloriesType = HKObjectType.quantityType(forIdentifier: .activeEnergyBurned) else { return }

        let calendar = Calendar.current
        var anchorComponents = calendar.dateComponents([.day, .month, .year], from: Date())
        anchorComponents.hour = 0
        guard let anchorDate = calendar.date(from: anchorComponents) else { return }

        let interval = DateComponents(day: 1)

        let query = HKStatisticsCollectionQuery(
            quantityType: caloriesType,
            quantitySamplePredicate: nil,
            options: .cumulativeSum,
            anchorDate: anchorDate,
            intervalComponents: interval
        )

        query.initialResultsHandler = { _, results, error in
            guard let results = results, error == nil else {
                print("❌ Weekly calories fetch error: \(error?.localizedDescription ?? "Unknown")")
                return
            }

            var caloriesByDay: [Date: Double] = [:]
            results.enumerateStatistics(from: startDate, to: endDate) { statistics, _ in
                if let sum = statistics.sumQuantity() {
                    let calories = sum.doubleValue(for: .kilocalorie())
                    caloriesByDay[statistics.startDate] = calories
                }
            }

            // Create array with all 7 days, filling missing days with 0
            var weeklyData: [DailyHealthData] = []
            for dayOffset in 0..<7 {
                if let date = calendar.date(byAdding: .day, value: dayOffset, to: startDate) {
                    let dayStart = calendar.startOfDay(for: date)
                    let calories = caloriesByDay[dayStart] ?? 0
                    weeklyData.append(DailyHealthData(date: dayStart, value: calories, unit: "kcal"))
                }
            }

            DispatchQueue.main.async {
                self.weeklyCaloriesData = weeklyData
                print("🔥 Weekly calories data loaded: \(weeklyData.count) days")
            }
        }

        healthStore.execute(query)
    }

    private func fetchWeeklyStress(from startDate: Date, to endDate: Date) {
        guard let hrvType = HKObjectType.quantityType(forIdentifier: .heartRateVariabilitySDNN) else { return }

        let calendar = Calendar.current
        var anchorComponents = calendar.dateComponents([.day, .month, .year], from: Date())
        anchorComponents.hour = 0
        guard let anchorDate = calendar.date(from: anchorComponents) else { return }

        let interval = DateComponents(day: 1)

        let query = HKStatisticsCollectionQuery(
            quantityType: hrvType,
            quantitySamplePredicate: nil,
            options: .discreteAverage,
            anchorDate: anchorDate,
            intervalComponents: interval
        )

        query.initialResultsHandler = { _, results, error in
            guard let results = results, error == nil else {
                print("❌ Weekly stress fetch error: \(error?.localizedDescription ?? "Unknown")")
                return
            }

            var stressByDay: [Date: Double] = [:]
            results.enumerateStatistics(from: startDate, to: endDate) { statistics, _ in
                if let average = statistics.averageQuantity() {
                    let hrvValue = average.doubleValue(for: HKUnit.secondUnit(with: .milli))
                    let stressLevel = max(0, min(100, 100 - hrvValue))
                    stressByDay[statistics.startDate] = stressLevel
                }
            }

            // Create array with all 7 days, filling missing days with 0
            var weeklyData: [DailyHealthData] = []
            for dayOffset in 0..<7 {
                if let date = calendar.date(byAdding: .day, value: dayOffset, to: startDate) {
                    let dayStart = calendar.startOfDay(for: date)
                    let stressLevel = stressByDay[dayStart] ?? 0
                    weeklyData.append(DailyHealthData(date: dayStart, value: stressLevel, unit: "%"))
                }
            }

            DispatchQueue.main.async {
                self.weeklyStressData = weeklyData
                print("😰 Weekly stress data loaded: \(weeklyData.count) days")
            }
        }

        healthStore.execute(query)
    }

    // MARK: - Real-time Observer Queries

    /// Start observing real-time health data changes
    func startRealtimeObservers() {
        guard isAvailable else {
            print("❌ HealthKit not available for observers")
            return
        }

        startHeartRateObserver()
        startCaloriesObserver()
        startStepsObserver()
        startDistanceObserver()

        print("✅ Real-time health observers started")
    }

    /// Stop all real-time observers
    func stopRealtimeObservers() {
        if let observer = heartRateObserver {
            healthStore.stop(observer)
        }
        if let observer = caloriesObserver {
            healthStore.stop(observer)
        }
        if let observer = stepsObserver {
            healthStore.stop(observer)
        }
        if let observer = distanceObserver {
            healthStore.stop(observer)
        }

        print("🛑 Real-time health observers stopped")
    }

    private func startHeartRateObserver() {
        guard let heartRateType = HKObjectType.quantityType(forIdentifier: .heartRate) else { return }

        let query = HKObserverQuery(sampleType: heartRateType, predicate: nil) { [weak self] _, completionHandler, error in
            if let error = error {
                print("❌ Heart rate observer error: \(error.localizedDescription)")
                completionHandler()
                return
            }

            // Fetch latest heart rate
            self?.fetchLatestHeartRate()
            completionHandler()
        }

        heartRateObserver = query
        healthStore.execute(query)

        // Enable background delivery for heart rate
        healthStore.enableBackgroundDelivery(for: heartRateType, frequency: .immediate) { success, error in
            if success {
                print("✅ Heart rate background delivery enabled")
            } else {
                print("❌ Heart rate background delivery failed: \(error?.localizedDescription ?? "Unknown")")
            }
        }
    }

    private func startCaloriesObserver() {
        guard let caloriesType = HKObjectType.quantityType(forIdentifier: .activeEnergyBurned) else { return }

        let query = HKObserverQuery(sampleType: caloriesType, predicate: nil) { [weak self] _, completionHandler, error in
            if let error = error {
                print("❌ Calories observer error: \(error.localizedDescription)")
                completionHandler()
                return
            }

            // Fetch latest calories
            self?.fetchLatestCalories()
            completionHandler()
        }

        caloriesObserver = query
        healthStore.execute(query)

        healthStore.enableBackgroundDelivery(for: caloriesType, frequency: .immediate) { success, error in
            if success {
                print("✅ Calories background delivery enabled")
            }
        }
    }

    private func startStepsObserver() {
        guard let stepsType = HKObjectType.quantityType(forIdentifier: .stepCount) else { return }

        let query = HKObserverQuery(sampleType: stepsType, predicate: nil) { [weak self] _, completionHandler, error in
            if let error = error {
                print("❌ Steps observer error: \(error.localizedDescription)")
                completionHandler()
                return
            }

            self?.fetchLatestSteps()
            completionHandler()
        }

        stepsObserver = query
        healthStore.execute(query)

        healthStore.enableBackgroundDelivery(for: stepsType, frequency: .immediate) { success, error in
            if success {
                print("✅ Steps background delivery enabled")
            }
        }
    }

    private func startDistanceObserver() {
        guard let distanceType = HKObjectType.quantityType(forIdentifier: .distanceWalkingRunning) else { return }

        let query = HKObserverQuery(sampleType: distanceType, predicate: nil) { [weak self] _, completionHandler, error in
            if let error = error {
                print("❌ Distance observer error: \(error.localizedDescription)")
                completionHandler()
                return
            }

            self?.fetchLatestDistance()
            completionHandler()
        }

        distanceObserver = query
        healthStore.execute(query)

        healthStore.enableBackgroundDelivery(for: distanceType, frequency: .immediate) { success, error in
            if success {
                print("✅ Distance background delivery enabled")
            }
        }
    }

    // MARK: - Fetch Latest Real-time Data

    private func fetchLatestHeartRate() {
        guard let heartRateType = HKObjectType.quantityType(forIdentifier: .heartRate) else { return }

        let sortDescriptor = NSSortDescriptor(key: HKSampleSortIdentifierEndDate, ascending: false)
        let query = HKSampleQuery(sampleType: heartRateType, predicate: nil, limit: 1, sortDescriptors: [sortDescriptor]) { _, samples, error in
            guard let sample = samples?.first as? HKQuantitySample else { return }

            let heartRate = sample.quantity.doubleValue(for: HKUnit(from: "count/min"))

            DispatchQueue.main.async {
                self.currentHeartRate = heartRate
                print("❤️ Real-time heart rate: \(Int(heartRate)) bpm")
            }
        }

        healthStore.execute(query)
    }

    private func fetchLatestCalories() {
        guard let caloriesType = HKObjectType.quantityType(forIdentifier: .activeEnergyBurned) else { return }

        let calendar = Calendar.current
        let today = calendar.startOfDay(for: Date())
        let predicate = HKQuery.predicateForSamples(withStart: today, end: Date(), options: .strictStartDate)

        let query = HKStatisticsQuery(quantityType: caloriesType, quantitySamplePredicate: predicate, options: .cumulativeSum) { _, result, error in
            guard let sum = result?.sumQuantity() else { return }

            let calories = sum.doubleValue(for: .kilocalorie())

            DispatchQueue.main.async {
                self.currentCalories = calories
                print("🔥 Real-time calories: \(Int(calories)) kcal")
            }
        }

        healthStore.execute(query)
    }

    private func fetchLatestSteps() {
        guard let stepsType = HKObjectType.quantityType(forIdentifier: .stepCount) else { return }

        let calendar = Calendar.current
        let today = calendar.startOfDay(for: Date())
        let predicate = HKQuery.predicateForSamples(withStart: today, end: Date(), options: .strictStartDate)

        let query = HKStatisticsQuery(quantityType: stepsType, quantitySamplePredicate: predicate, options: .cumulativeSum) { _, result, error in
            guard let sum = result?.sumQuantity() else { return }

            let steps = Int(sum.doubleValue(for: .count()))

            DispatchQueue.main.async {
                self.currentSteps = steps
                print("👟 Real-time steps: \(steps)")
            }
        }

        healthStore.execute(query)
    }

    private func fetchLatestDistance() {
        guard let distanceType = HKObjectType.quantityType(forIdentifier: .distanceWalkingRunning) else { return }

        let calendar = Calendar.current
        let today = calendar.startOfDay(for: Date())
        let predicate = HKQuery.predicateForSamples(withStart: today, end: Date(), options: .strictStartDate)

        let query = HKStatisticsQuery(quantityType: distanceType, quantitySamplePredicate: predicate, options: .cumulativeSum) { _, result, error in
            guard let sum = result?.sumQuantity() else { return }

            let distance = sum.doubleValue(for: .meter())

            DispatchQueue.main.async {
                self.currentDistance = distance
                print("🏃 Real-time distance: \(String(format: "%.2f", distance / 1000)) km")
            }
        }

        healthStore.execute(query)
    }
}

// MARK: - Daily Health Data Model

struct DailyHealthData: Identifiable {
    let id = UUID()
    let date: Date
    let value: Double
    let unit: String

    var dayName: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "EEE"
        return formatter.string(from: date)
    }

    var formattedValue: String {
        String(format: "%.0f", value)
    }
}
