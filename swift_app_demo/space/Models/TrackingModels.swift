//
//  TrackingModels.swift
//  space
//
//  FastAPI tracking endpoint data models
//

import Foundation
import UIKit

// MARK: - Workout Session

/// Workout session data for FastAPI upload
struct WorkoutSessionData: Codable {
    let startAt: String  // ISO8601
    let endAt: String
    let workoutType: String
    let stepCount: Int?
    let distanceKm: Double?
    let activeEnergyKcal: Double?
    let exerciseMin: Double?
    let avgHr: Double?
    let walkingSpeedKmh: Double?
    let source: String?
    let deviceModel: String?
    let osVersion: String?

    enum CodingKeys: String, CodingKey {
        case startAt = "start_at"
        case endAt = "end_at"
        case workoutType = "workout_type"
        case stepCount = "step_count"
        case distanceKm = "distance_km"
        case activeEnergyKcal = "active_energy_kcal"
        case exerciseMin = "exercise_min"
        case avgHr = "avg_hr"
        case walkingSpeedKmh = "walking_speed_kmh"
        case source
        case deviceModel = "device_model"
        case osVersion = "os_version"
    }
}

/// Workout session response from FastAPI
struct WorkoutSessionRead: Codable {
    let id: String
    let userId: String
    let startAt: String
    let endAt: String
    let workoutType: String
    let stepCount: Int?
    let distanceKm: Double?
    let activeEnergyKcal: Double?
    let exerciseMin: Double?
    let avgHr: Double?
    let walkingSpeedKmh: Double?
    let source: String?
    let deviceModel: String?
    let osVersion: String?

    enum CodingKeys: String, CodingKey {
        case id
        case userId = "user_id"
        case startAt = "start_at"
        case endAt = "end_at"
        case workoutType = "workout_type"
        case stepCount = "step_count"
        case distanceKm = "distance_km"
        case activeEnergyKcal = "active_energy_kcal"
        case exerciseMin = "exercise_min"
        case avgHr = "avg_hr"
        case walkingSpeedKmh = "walking_speed_kmh"
        case source
        case deviceModel = "device_model"
        case osVersion = "os_version"
    }
}

// MARK: - Health Hourly

/// Hourly health data for FastAPI upload
struct HealthHourlyData: Codable {
    let tsHour: String  // ISO8601 (hourly)
    let heartRateBpm: Double?
    let restingHrBpm: Double?
    let walkingHrAvgBpm: Double?
    let hrvSdnnMs: Double?
    let vo2Max: Double?
    let spo2Pct: Double?
    let respiratoryRateCpm: Double?
    let wristTempC: Double?
    let source: String?
    let deviceModel: String?
    let osVersion: String?

    enum CodingKeys: String, CodingKey {
        case tsHour = "ts_hour"
        case heartRateBpm = "heart_rate_bpm"
        case restingHrBpm = "resting_hr_bpm"
        case walkingHrAvgBpm = "walking_hr_avg_bpm"
        case hrvSdnnMs = "hrv_sdnn_ms"
        case vo2Max = "vo2_max"
        case spo2Pct = "spo2_pct"
        case respiratoryRateCpm = "respiratory_rate_cpm"
        case wristTempC = "wrist_temp_c"
        case source
        case deviceModel = "device_model"
        case osVersion = "os_version"
    }
}

/// Hourly health data response from FastAPI
struct HealthHourlyRead: Codable {
    let id: String
    let userId: String
    let tsHour: String
    let heartRateBpm: Double?
    let restingHrBpm: Double?
    let walkingHrAvgBpm: Double?
    let hrvSdnnMs: Double?
    let syncedAt: String

    enum CodingKeys: String, CodingKey {
        case id
        case userId = "user_id"
        case tsHour = "ts_hour"
        case heartRateBpm = "heart_rate_bpm"
        case restingHrBpm = "resting_hr_bpm"
        case walkingHrAvgBpm = "walking_hr_avg_bpm"
        case hrvSdnnMs = "hrv_sdnn_ms"
        case syncedAt = "synced_at"
    }
}

// MARK: - Sleep Session

/// Sleep session data for FastAPI upload
struct SleepSessionData: Codable {
    let startAt: String  // ISO8601
    let endAt: String
    let inBedHr: Double?
    let asleepHr: Double?
    let awakeHr: Double?
    let coreHr: Double?
    let deepHr: Double?
    let remHr: Double?
    let respiratoryRate: Double?
    let heartRateAvg: Double?
    let efficiency: Double?
    let source: String?
    let deviceModel: String?
    let osVersion: String?

    enum CodingKeys: String, CodingKey {
        case startAt = "start_at"
        case endAt = "end_at"
        case inBedHr = "in_bed_hr"
        case asleepHr = "asleep_hr"
        case awakeHr = "awake_hr"
        case coreHr = "core_hr"
        case deepHr = "deep_hr"
        case remHr = "rem_hr"
        case respiratoryRate = "respiratory_rate"
        case heartRateAvg = "heart_rate_avg"
        case efficiency
        case source
        case deviceModel = "device_model"
        case osVersion = "os_version"
    }
}

/// Sleep session response from FastAPI
struct SleepSessionRead: Codable {
    let id: String
    let userId: String
    let startAt: String
    let endAt: String
    let asleepHr: Double?
    let heartRateAvg: Double?

    enum CodingKeys: String, CodingKey {
        case id
        case userId = "user_id"
        case startAt = "start_at"
        case endAt = "end_at"
        case asleepHr = "asleep_hr"
        case heartRateAvg = "heart_rate_avg"
    }
}

// MARK: - Time Slot

/// Time slot data for FastAPI upload
struct TimeSlotData: Codable {
    let tsHour: String  // ISO8601 (hourly)
    let latitude: Double?
    let longitude: Double?
    let altitude: Double?
    let horizontalAccuracy: Double?
    let verticalAccuracy: Double?
    let placeId: String?
    let gridNx: Int?
    let gridNy: Int?
    let weatherProvider: String?
    let status: String?

    enum CodingKeys: String, CodingKey {
        case tsHour = "ts_hour"
        case latitude
        case longitude
        case altitude
        case horizontalAccuracy = "horizontal_accuracy"
        case verticalAccuracy = "vertical_accuracy"
        case placeId = "place_id"
        case gridNx = "grid_nx"
        case gridNy = "grid_ny"
        case weatherProvider = "weather_provider"
        case status
    }
}

/// Time slot response from FastAPI
struct TimeSlotRead: Codable {
    let id: String
    let userId: String
    let tsHour: String
    let latitude: Double?
    let longitude: Double?
    let placeId: String?

    enum CodingKeys: String, CodingKey {
        case id
        case userId = "user_id"
        case tsHour = "ts_hour"
        case latitude
        case longitude
        case placeId = "place_id"
    }
}

// MARK: - Place

/// Place data for FastAPI upload
struct PlaceData: Codable {
    let label: String
    let category: String?
    let centerLat: Double
    let centerLon: Double
    let radiusM: Double
    let visitsCount: Int?
    let firstSeen: String?  // ISO8601
    let lastSeen: String?   // ISO8601

    enum CodingKeys: String, CodingKey {
        case label
        case category
        case centerLat = "center_lat"
        case centerLon = "center_lon"
        case radiusM = "radius_m"
        case visitsCount = "visits_count"
        case firstSeen = "first_seen"
        case lastSeen = "last_seen"
    }
}

/// Place response from FastAPI
struct PlaceRead: Codable {
    let id: String
    let userId: String
    let label: String
    let category: String?
    let centerLat: Double
    let centerLon: Double
    let radiusM: Double
    let visitsCount: Int

    enum CodingKeys: String, CodingKey {
        case id
        case userId = "user_id"
        case label
        case category
        case centerLat = "center_lat"
        case centerLon = "center_lon"
        case radiusM = "radius_m"
        case visitsCount = "visits_count"
    }
}

// MARK: - Helper Extensions

extension WorkoutSessionData {
    /// Get device model string
    static var currentDeviceModel: String {
        return UIDevice.current.model
    }

    /// Get OS version string
    static var currentOSVersion: String {
        return UIDevice.current.systemVersion
    }
}
