import Foundation

// MARK: - HRV & Fatigue Models

/// HRV sync request for `/api/health/hrv/sync` POST
struct HRVSyncRequest: Codable {
    let userId: String
    let hrvValue: Double  // Must be > 0
    let measuredAt: Date

    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case hrvValue = "hrv_value"
        case measuredAt = "measured_at"
    }
}

/// HRV sync response from `/api/health/hrv/sync` POST
struct HRVSyncResponse: Codable {
    let success: Bool
    let hrvValue: Double
    let fatigueLevel: Int
    let fatigueLabel: String
    let measuredAt: Date
    let syncedAt: Date

    enum CodingKeys: String, CodingKey {
        case success
        case hrvValue = "hrv_value"
        case fatigueLevel = "fatigue_level"
        case fatigueLabel = "fatigue_label"
        case measuredAt = "measured_at"
        case syncedAt = "synced_at"
    }
}

/// Fatigue status response from `/api/health/fatigue/status/{user_id}` GET
struct FatigueStatusResponse: Codable {
    let userId: String
    let currentFatigueLevel: Int?
    let fatigueLabel: String?
    let latestHrvValue: Double?
    let measuredAt: Date?
    let averageFatigue7days: Double?

    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case currentFatigueLevel = "current_fatigue_level"
        case fatigueLabel = "fatigue_label"
        case latestHrvValue = "latest_hrv_value"
        case measuredAt = "measured_at"
        case averageFatigue7days = "average_fatigue_7days"
    }
}
