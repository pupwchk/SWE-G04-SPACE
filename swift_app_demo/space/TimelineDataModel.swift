//
//  TimelineDataModel.swift
//  space
//
//  Data model for timeline tracking
//

import Foundation
import CoreLocation
import MapKit

/// Single timeline record
struct TimelineRecord: Identifiable, Codable, Equatable {
    let id: UUID
    let startTime: Date
    let endTime: Date
    let coordinates: [CoordinateData]
    let totalDistance: Double // meters
    let averageSpeed: Double // km/h
    let maxSpeed: Double // km/h
    let duration: TimeInterval // seconds
    var checkpoints: [Checkpoint] // checkpoints on the route

    var durationFormatted: String {
        let hours = Int(duration) / 3600
        let minutes = (Int(duration) % 3600) / 60
        let seconds = Int(duration) % 60

        if hours > 0 {
            return String(format: "%dh %dm %ds", hours, minutes, seconds)
        } else if minutes > 0 {
            return String(format: "%dm %ds", minutes, seconds)
        } else {
            return String(format: "%ds", seconds)
        }
    }

    var distanceFormatted: String {
        if totalDistance >= 1000 {
            return String(format: "%.2f km", totalDistance / 1000)
        } else {
            return String(format: "%.0f m", totalDistance)
        }
    }

    var centerCoordinate: CLLocationCoordinate2D? {
        guard !coordinates.isEmpty else { return nil }

        let latitudes = coordinates.map { $0.latitude }
        let longitudes = coordinates.map { $0.longitude }

        let avgLat = latitudes.reduce(0, +) / Double(latitudes.count)
        let avgLon = longitudes.reduce(0, +) / Double(longitudes.count)

        return CLLocationCoordinate2D(latitude: avgLat, longitude: avgLon)
    }

    var region: MKCoordinateRegion? {
        guard !coordinates.isEmpty else { return nil }

        let latitudes = coordinates.map { $0.latitude }
        let longitudes = coordinates.map { $0.longitude }

        let minLat = latitudes.min() ?? 0
        let maxLat = latitudes.max() ?? 0
        let minLon = longitudes.min() ?? 0
        let maxLon = longitudes.max() ?? 0

        let center = CLLocationCoordinate2D(
            latitude: (minLat + maxLat) / 2,
            longitude: (minLon + maxLon) / 2
        )

        let span = MKCoordinateSpan(
            latitudeDelta: (maxLat - minLat) * 1.5, // Add 50% padding
            longitudeDelta: (maxLon - minLon) * 1.5
        )

        return MKCoordinateRegion(center: center, span: span)
    }
}

/// Codable wrapper for CLLocationCoordinate2D
struct CoordinateData: Codable, Equatable {
    let latitude: Double
    let longitude: Double
    let timestamp: Date

    var coordinate: CLLocationCoordinate2D {
        CLLocationCoordinate2D(latitude: latitude, longitude: longitude)
    }

    init(coordinate: CLLocationCoordinate2D, timestamp: Date) {
        self.latitude = coordinate.latitude
        self.longitude = coordinate.longitude
        self.timestamp = timestamp
    }
}

// MARK: - Checkpoint Models

/// User mood type for checkpoint
enum CheckpointMood: String, Codable, CaseIterable {
    case veryHappy = "very_happy"
    case happy = "happy"
    case neutral = "neutral"
    case sad = "sad"
    case verySad = "very_sad"

    var emoji: String {
        switch self {
        case .veryHappy: return "😄"
        case .happy: return "🙂"
        case .neutral: return "😐"
        case .sad: return "😔"
        case .verySad: return "😢"
        }
    }

    var label: String {
        switch self {
        case .veryHappy: return "Very Happy"
        case .happy: return "Happy"
        case .neutral: return "Neutral"
        case .sad: return "Sad"
        case .verySad: return "Very Sad"
        }
    }

    var color: String {
        switch self {
        case .veryHappy: return "4CAF50"  // Green
        case .happy: return "8BC34A"      // Light Green
        case .neutral: return "FFC107"    // Amber
        case .sad: return "FF9800"        // Orange
        case .verySad: return "F44336"    // Red
        }
    }
}

/// Stress change direction
enum StressChange: String, Codable, CaseIterable {
    case increased = "increased"
    case unchanged = "unchanged"
    case decreased = "decreased"

    var icon: String {
        switch self {
        case .increased: return "arrow.up.circle.fill"
        case .unchanged: return "minus.circle.fill"
        case .decreased: return "arrow.down.circle.fill"
        }
    }

    var label: String {
        switch self {
        case .increased: return "Increased"
        case .unchanged: return "No Change"
        case .decreased: return "Decreased"
        }
    }

    var color: String {
        switch self {
        case .increased: return "F44336"   // Red
        case .unchanged: return "9E9E9E"   // Gray
        case .decreased: return "4CAF50"   // Green
        }
    }
}

/// Checkpoint data for a specific location on the route
struct Checkpoint: Identifiable, Codable, Equatable {
    let id: UUID
    let coordinate: CoordinateData
    let mood: CheckpointMood
    let stayDuration: TimeInterval  // seconds
    let stressChange: StressChange
    let note: String?
    let timestamp: Date

    // Health data from Watch (Phase 7)
    let heartRate: Double?  // bpm
    let calories: Double?   // kcal
    let steps: Int?         // steps
    let distance: Double?   // meters
    let hrv: Double?        // ms (Heart Rate Variability)
    let stressLevel: Int?   // 0-100 (calculated from HRV)

    init(
        id: UUID = UUID(),
        coordinate: CoordinateData,
        mood: CheckpointMood,
        stayDuration: TimeInterval,
        stressChange: StressChange,
        note: String? = nil,
        timestamp: Date = Date(),
        heartRate: Double? = nil,
        calories: Double? = nil,
        steps: Int? = nil,
        distance: Double? = nil,
        hrv: Double? = nil,
        stressLevel: Int? = nil
    ) {
        self.id = id
        self.coordinate = coordinate
        self.mood = mood
        self.stayDuration = stayDuration
        self.stressChange = stressChange
        self.note = note
        self.timestamp = timestamp
        self.heartRate = heartRate
        self.calories = calories
        self.steps = steps
        self.distance = distance
        self.hrv = hrv
        self.stressLevel = stressLevel
    }

    var stayDurationFormatted: String {
        let minutes = Int(stayDuration) / 60
        let seconds = Int(stayDuration) % 60

        if minutes > 0 {
            return "\(minutes)m \(seconds)s"
        } else {
            return "\(seconds)s"
        }
    }
}

/// Manager for timeline records
class TimelineManager: ObservableObject {
    static let shared = TimelineManager()

    @Published var timelines: [TimelineRecord] = []
    @Published var currentTimeline: TimelineRecord?

    private let userDefaultsKey = "saved_timelines"

    init() {
        loadTimelines()
    }

    // MARK: - CRUD Operations

    func saveTimeline(_ timeline: TimelineRecord) {
        timelines.insert(timeline, at: 0) // Add to beginning
        saveToUserDefaults()
        print("✅ Timeline saved: \(timeline.distanceFormatted), \(timeline.durationFormatted)")
    }

    func deleteTimeline(_ timeline: TimelineRecord) {
        timelines.removeAll { $0.id == timeline.id }
        saveToUserDefaults()
        print("🗑️ Timeline deleted")
    }

    func clearAllTimelines() {
        timelines.removeAll()
        saveToUserDefaults()
        print("🗑️ All timelines cleared")
    }

    // MARK: - Persistence

    private func saveToUserDefaults() {
        if let encoded = try? JSONEncoder().encode(timelines) {
            UserDefaults.standard.set(encoded, forKey: userDefaultsKey)
        }
    }

    private func loadTimelines() {
        if let data = UserDefaults.standard.data(forKey: userDefaultsKey),
           let decoded = try? JSONDecoder().decode([TimelineRecord].self, from: data) {
            timelines = decoded
            print("📂 Loaded \(timelines.count) timeline(s)")
        }
    }

    // MARK: - Create Timeline from Location Data

    func createTimeline(
        startTime: Date,
        endTime: Date,
        coordinates: [CLLocationCoordinate2D],
        timestamps: [Date],
        speeds: [Double],
        checkpoints: [Checkpoint] = []
    ) -> TimelineRecord? {
        guard !coordinates.isEmpty else { return nil }

        // Convert coordinates
        let coordinateData = zip(coordinates, timestamps).map { coord, time in
            CoordinateData(coordinate: coord, timestamp: time)
        }

        // Calculate total distance
        var totalDistance: Double = 0.0
        for i in 0..<coordinates.count - 1 {
            let loc1 = CLLocation(latitude: coordinates[i].latitude, longitude: coordinates[i].longitude)
            let loc2 = CLLocation(latitude: coordinates[i + 1].latitude, longitude: coordinates[i + 1].longitude)
            totalDistance += loc2.distance(from: loc1)
        }

        // Calculate speeds
        let validSpeeds = speeds.filter { $0 > 0 }
        let averageSpeed = validSpeeds.isEmpty ? 0.0 : validSpeeds.reduce(0, +) / Double(validSpeeds.count)
        let maxSpeed = speeds.max() ?? 0.0

        let duration = endTime.timeIntervalSince(startTime)

        return TimelineRecord(
            id: UUID(),
            startTime: startTime,
            endTime: endTime,
            coordinates: coordinateData,
            totalDistance: totalDistance,
            averageSpeed: averageSpeed,
            maxSpeed: maxSpeed,
            duration: duration,
            checkpoints: checkpoints
        )
    }

    // MARK: - Checkpoint Management

    func addCheckpoint(to timelineId: UUID, checkpoint: Checkpoint) {
        if let index = timelines.firstIndex(where: { $0.id == timelineId }) {
            timelines[index].checkpoints.append(checkpoint)
            saveToUserDefaults()
            print("📍 Checkpoint added: \(checkpoint.mood.emoji)")
        }
    }

    func removeCheckpoint(from timelineId: UUID, checkpointId: UUID) {
        if let index = timelines.firstIndex(where: { $0.id == timelineId }) {
            timelines[index].checkpoints.removeAll { $0.id == checkpointId }
            saveToUserDefaults()
            print("🗑️ Checkpoint removed")
        }
    }

    // MARK: - Automatic Checkpoint Generation (Phase 7)

    /// Automatically generate checkpoints based on GPS and health data
    /// Called when tracking stops on Watch
    func generateCheckpoints(
        coordinates: [CLLocationCoordinate2D],
        timestamps: [Date],
        healthData: [(heartRate: Double?, calories: Double?, steps: Int?, distance: Double?)]
    ) -> [Checkpoint] {
        guard coordinates.count >= 2 else { return [] }

        var checkpoints: [Checkpoint] = []

        // Strategy 1: Create checkpoints at significant stops (velocity < 0.5 km/h for > 30 seconds)
        var currentStopStart: Int?
        var currentStopDuration: TimeInterval = 0

        for i in 1..<coordinates.count {
            let loc1 = CLLocation(latitude: coordinates[i - 1].latitude, longitude: coordinates[i - 1].longitude)
            let loc2 = CLLocation(latitude: coordinates[i].latitude, longitude: coordinates[i].longitude)

            let distance = loc2.distance(from: loc1) // meters
            let timeInterval = timestamps[i].timeIntervalSince(timestamps[i - 1])
            let speed = timeInterval > 0 ? (distance / timeInterval) * 3.6 : 0 // km/h

            // Detect stop
            if speed < 0.5 {
                if currentStopStart == nil {
                    currentStopStart = i
                    currentStopDuration = 0
                }
                currentStopDuration += timeInterval
            } else {
                // Moving again, check if we had a significant stop
                if let stopStart = currentStopStart, currentStopDuration >= 30 {
                    // Create checkpoint for this stop
                    let checkpoint = createCheckpointAt(
                        index: stopStart,
                        coordinates: coordinates,
                        timestamps: timestamps,
                        healthData: healthData,
                        stayDuration: currentStopDuration,
                        previousCheckpoint: checkpoints.last
                    )
                    checkpoints.append(checkpoint)
                }

                currentStopStart = nil
                currentStopDuration = 0
            }
        }

        // Check for final stop
        if let stopStart = currentStopStart, currentStopDuration >= 30 {
            let checkpoint = createCheckpointAt(
                index: stopStart,
                coordinates: coordinates,
                timestamps: timestamps,
                healthData: healthData,
                stayDuration: currentStopDuration,
                previousCheckpoint: checkpoints.last
            )
            checkpoints.append(checkpoint)
        }

        print("📍 Auto-generated \(checkpoints.count) checkpoint(s)")
        return checkpoints
    }

    /// Create a checkpoint at a specific index with health data
    private func createCheckpointAt(
        index: Int,
        coordinates: [CLLocationCoordinate2D],
        timestamps: [Date],
        healthData: [(heartRate: Double?, calories: Double?, steps: Int?, distance: Double?)],
        stayDuration: TimeInterval,
        previousCheckpoint: Checkpoint? = nil
    ) -> Checkpoint {
        let coordinate = CoordinateData(
            coordinate: coordinates[index],
            timestamp: timestamps[index]
        )

        // Get health data for this point (if available)
        let health = index < healthData.count ? healthData[index] : (nil, nil, nil, nil)

        // Determine mood based on heart rate (simple heuristic)
        let mood: CheckpointMood
        if let hr = health.0 {  // health.0 = heartRate
            if hr < 60 {
                mood = .happy // Resting, relaxed
            } else if hr < 80 {
                mood = .neutral // Normal
            } else if hr < 100 {
                mood = .happy // Active, energized
            } else {
                mood = .neutral // High activity
            }
        } else {
            mood = .neutral // Default if no heart rate data
        }

        // Get current HRV and stress level from HealthKitManager
        let healthManager = HealthKitManager.shared
        let currentStressLevel = healthManager.stressLevel
        let currentHRV = healthManager.currentHRV

        // Determine stress change by comparing with previous checkpoint
        let stressChange: StressChange
        if let previousStress = previousCheckpoint?.stressLevel {
            let stressDiff = currentStressLevel - previousStress
            if stressDiff > 10 {  // Increased by more than 10%
                stressChange = .increased
            } else if stressDiff < -10 {  // Decreased by more than 10%
                stressChange = .decreased
            } else {
                stressChange = .unchanged
            }
        } else {
            stressChange = .unchanged  // No previous checkpoint to compare
        }

        return Checkpoint(
            coordinate: coordinate,
            mood: mood,
            stayDuration: stayDuration,
            stressChange: stressChange,
            note: nil,
            timestamp: timestamps[index],
            heartRate: health.0,  // health.0 = heartRate
            calories: health.1,   // health.1 = calories
            steps: health.2,      // health.2 = steps
            distance: health.3,   // health.3 = distance
            hrv: currentHRV > 0 ? currentHRV : nil,
            stressLevel: currentStressLevel > 0 ? currentStressLevel : nil
        )
    }

    /// Create a manual checkpoint with current health data
    func createManualCheckpoint(
        coordinate: CLLocationCoordinate2D,
        timestamp: Date,
        mood: CheckpointMood,
        note: String? = nil
    ) -> Checkpoint {
        // Get current health data from HealthKitManager
        let healthManager = HealthKitManager.shared
        let currentStressLevel = healthManager.stressLevel
        let currentHRV = healthManager.currentHRV

        // Determine stress change by comparing with previous checkpoint
        let stressChange: StressChange
        if let previousStress = currentTimeline?.checkpoints.last?.stressLevel {
            let stressDiff = currentStressLevel - previousStress
            if stressDiff > 10 {  // Increased by more than 10%
                stressChange = .increased
            } else if stressDiff < -10 {  // Decreased by more than 10%
                stressChange = .decreased
            } else {
                stressChange = .unchanged
            }
        } else {
            stressChange = .unchanged  // No previous checkpoint to compare
        }

        return Checkpoint(
            coordinate: CoordinateData(coordinate: coordinate, timestamp: timestamp),
            mood: mood,
            stayDuration: 0, // Manual checkpoint, no stay duration
            stressChange: stressChange,
            note: note,
            timestamp: timestamp,
            heartRate: healthManager.currentHeartRate > 0 ? healthManager.currentHeartRate : nil,
            calories: healthManager.currentCalories > 0 ? healthManager.currentCalories : nil,
            steps: healthManager.currentSteps > 0 ? healthManager.currentSteps : nil,
            distance: healthManager.currentDistance > 0 ? healthManager.currentDistance : nil,
            hrv: currentHRV > 0 ? currentHRV : nil,
            stressLevel: currentStressLevel > 0 ? currentStressLevel : nil
        )
    }

}
