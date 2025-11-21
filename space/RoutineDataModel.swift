//
//  RoutineDataModel.swift
//  space
//
//  Data model for routine tracking
//

import Foundation
import CoreLocation
import MapKit

/// Single routine record
struct RoutineRecord: Identifiable, Codable, Equatable {
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

    init(
        id: UUID = UUID(),
        coordinate: CoordinateData,
        mood: CheckpointMood,
        stayDuration: TimeInterval,
        stressChange: StressChange,
        note: String? = nil,
        timestamp: Date = Date()
    ) {
        self.id = id
        self.coordinate = coordinate
        self.mood = mood
        self.stayDuration = stayDuration
        self.stressChange = stressChange
        self.note = note
        self.timestamp = timestamp
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

/// Manager for routine records
class RoutineManager: ObservableObject {
    static let shared = RoutineManager()

    @Published var routines: [RoutineRecord] = []
    @Published var currentRoutine: RoutineRecord?

    private let userDefaultsKey = "saved_routines"

    init() {
        loadRoutines()
    }

    // MARK: - CRUD Operations

    func saveRoutine(_ routine: RoutineRecord) {
        routines.insert(routine, at: 0) // Add to beginning
        saveToUserDefaults()
        print("✅ Routine saved: \(routine.distanceFormatted), \(routine.durationFormatted)")
    }

    func deleteRoutine(_ routine: RoutineRecord) {
        routines.removeAll { $0.id == routine.id }
        saveToUserDefaults()
        print("🗑️ Routine deleted")
    }

    func clearAllRoutines() {
        routines.removeAll()
        saveToUserDefaults()
        print("🗑️ All routines cleared")
    }

    // MARK: - Persistence

    private func saveToUserDefaults() {
        if let encoded = try? JSONEncoder().encode(routines) {
            UserDefaults.standard.set(encoded, forKey: userDefaultsKey)
        }
    }

    private func loadRoutines() {
        if let data = UserDefaults.standard.data(forKey: userDefaultsKey),
           let decoded = try? JSONDecoder().decode([RoutineRecord].self, from: data) {
            routines = decoded
            print("📂 Loaded \(routines.count) routine(s)")
        }
    }

    // MARK: - Create Routine from Location Data

    func createRoutine(
        startTime: Date,
        endTime: Date,
        coordinates: [CLLocationCoordinate2D],
        timestamps: [Date],
        speeds: [Double],
        checkpoints: [Checkpoint] = []
    ) -> RoutineRecord? {
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

        return RoutineRecord(
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

    func addCheckpoint(to routineId: UUID, checkpoint: Checkpoint) {
        if let index = routines.firstIndex(where: { $0.id == routineId }) {
            routines[index].checkpoints.append(checkpoint)
            saveToUserDefaults()
            print("📍 Checkpoint added: \(checkpoint.mood.emoji)")
        }
    }

    func removeCheckpoint(from routineId: UUID, checkpointId: UUID) {
        if let index = routines.firstIndex(where: { $0.id == routineId }) {
            routines[index].checkpoints.removeAll { $0.id == checkpointId }
            saveToUserDefaults()
            print("🗑️ Checkpoint removed")
        }
    }

    // MARK: - Dummy Data for Testing

    func loadDummyData() {
        guard routines.isEmpty else { return }

        // Seoul area sample coordinates (Gangnam)
        let baseLatitude = 37.5012
        let baseLongitude = 127.0396

        let startTime = Date().addingTimeInterval(-3600) // 1 hour ago
        let coordinates: [CoordinateData] = (0..<20).map { i in
            CoordinateData(
                coordinate: CLLocationCoordinate2D(
                    latitude: baseLatitude + Double(i) * 0.001,
                    longitude: baseLongitude + Double(i) * 0.0005
                ),
                timestamp: startTime.addingTimeInterval(Double(i) * 180) // every 3 minutes
            )
        }

        // Sample checkpoints
        let checkpoints: [Checkpoint] = [
            Checkpoint(
                coordinate: coordinates[3],
                mood: .happy,
                stayDuration: 600, // 10 minutes
                stressChange: .decreased,
                note: "Coffee break"
            ),
            Checkpoint(
                coordinate: coordinates[8],
                mood: .neutral,
                stayDuration: 300, // 5 minutes
                stressChange: .unchanged,
                note: nil
            ),
            Checkpoint(
                coordinate: coordinates[14],
                mood: .veryHappy,
                stayDuration: 1200, // 20 minutes
                stressChange: .decreased,
                note: "Lunch at restaurant"
            ),
            Checkpoint(
                coordinate: coordinates[18],
                mood: .sad,
                stayDuration: 180, // 3 minutes
                stressChange: .increased,
                note: "Stuck in traffic"
            )
        ]

        let dummyRoutine = RoutineRecord(
            id: UUID(),
            startTime: startTime,
            endTime: Date(),
            coordinates: coordinates,
            totalDistance: 2500, // 2.5 km
            averageSpeed: 4.5,
            maxSpeed: 6.2,
            duration: 3600, // 1 hour
            checkpoints: checkpoints
        )

        routines.append(dummyRoutine)
        saveToUserDefaults()
        print("📂 Dummy data loaded with \(checkpoints.count) checkpoints")
    }
}
