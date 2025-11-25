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

    // Historical data (last 7 days)
    @Published var weeklySleepData: [DailyHealthData] = []
    @Published var weeklyStressData: [DailyHealthData] = []
    @Published var weeklyCaloriesData: [DailyHealthData] = []

    // MARK: - Private Properties

    private let healthStore = HKHealthStore()

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

    func requestAuthorization() {
        guard isAvailable else {
            print("❌ HealthKit not available")
            return
        }

        let readTypes: Set<HKObjectType> = [
            HKObjectType.categoryType(forIdentifier: .sleepAnalysis)!,
            HKObjectType.quantityType(forIdentifier: .activeEnergyBurned)!,
            HKObjectType.quantityType(forIdentifier: .heartRateVariabilitySDNN)!, // Proxy for stress
            HKObjectType.quantityType(forIdentifier: .restingHeartRate)!
        ]

        healthStore.requestAuthorization(toShare: nil, read: readTypes) { success, error in
            DispatchQueue.main.async {
                if success {
                    print("✅ HealthKit authorization granted")
                    self.fetchTodayHealthData()
                    self.fetchWeeklyHealthData()
                } else {
                    print("❌ HealthKit authorization denied: \(error?.localizedDescription ?? "Unknown error")")
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
                self.stressLevel = stressLevel
                print("😰 Stress: \(stressLevel)% (HRV: \(String(format: "%.1f", hrvValue))ms)")
            }
        }

        healthStore.execute(query)
    }

    private func fetchWeeklySleep(from startDate: Date, to endDate: Date) {
        guard let sleepType = HKObjectType.categoryType(forIdentifier: .sleepAnalysis) else { return }

        let calendar = Calendar.current
        var anchorComponents = calendar.dateComponents([.day, .month, .year], from: Date())
        anchorComponents.hour = 0
        guard let anchorDate = calendar.date(from: anchorComponents) else { return }

        let interval = DateComponents(day: 1)

        let query = HKStatisticsCollectionQuery(
            quantityType: sleepType as! HKQuantityType,
            quantitySamplePredicate: nil,
            options: [],
            anchorDate: anchorDate,
            intervalComponents: interval
        )

        query.initialResultsHandler = { _, results, error in
            guard let results = results, error == nil else {
                print("❌ Weekly sleep fetch error: \(error?.localizedDescription ?? "Unknown")")
                return
            }

            var weeklyData: [DailyHealthData] = []
            results.enumerateStatistics(from: startDate, to: startDate) { statistics, _ in
                // Process sleep samples for each day
                let predicate = HKQuery.predicateForSamples(withStart: statistics.startDate, end: statistics.endDate, options: .strictStartDate)

                let dayQuery = HKSampleQuery(sampleType: sleepType, predicate: predicate, limit: HKObjectQueryNoLimit, sortDescriptors: nil) { _, samples, _ in
                    guard let samples = samples as? [HKCategorySample] else { return }

                    var totalSleepSeconds: TimeInterval = 0
                    for sample in samples {
                        if sample.value == HKCategoryValueSleepAnalysis.asleepUnspecified.rawValue ||
                           sample.value == HKCategoryValueSleepAnalysis.asleepCore.rawValue ||
                           sample.value == HKCategoryValueSleepAnalysis.asleepDeep.rawValue ||
                           sample.value == HKCategoryValueSleepAnalysis.asleepREM.rawValue {
                            totalSleepSeconds += sample.endDate.timeIntervalSince(sample.startDate)
                        }
                    }

                    let sleepHours = totalSleepSeconds / 3600.0
                    weeklyData.append(DailyHealthData(date: statistics.startDate, value: sleepHours, unit: "h"))
                }

                self.healthStore.execute(dayQuery)
            }

            DispatchQueue.main.async {
                self.weeklySleepData = weeklyData.sorted { $0.date < $1.date }
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

            var weeklyData: [DailyHealthData] = []
            results.enumerateStatistics(from: startDate, to: endDate) { statistics, _ in
                if let sum = statistics.sumQuantity() {
                    let calories = sum.doubleValue(for: .kilocalorie())
                    weeklyData.append(DailyHealthData(date: statistics.startDate, value: calories, unit: "kcal"))
                }
            }

            DispatchQueue.main.async {
                self.weeklyCaloriesData = weeklyData.sorted { $0.date < $1.date }
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

            var weeklyData: [DailyHealthData] = []
            results.enumerateStatistics(from: startDate, to: endDate) { statistics, _ in
                if let average = statistics.averageQuantity() {
                    let hrvValue = average.doubleValue(for: HKUnit.secondUnit(with: .milli))
                    let stressLevel = max(0, min(100, 100 - hrvValue))
                    weeklyData.append(DailyHealthData(date: statistics.startDate, value: stressLevel, unit: "%"))
                }
            }

            DispatchQueue.main.async {
                self.weeklyStressData = weeklyData.sorted { $0.date < $1.date }
                print("😰 Weekly stress data loaded: \(weeklyData.count) days")
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
