import Foundation

// MARK: - Rule & Control Models

/// Rule modification request for `/api/appliances/rule/modify` POST
struct RuleModifyRequest: Codable {
    let applianceType: String
    let fatigueLevel: Int?  // 1-4
    let operation: String  // "enable", "disable", "modify_threshold"
    let newThreshold: [String: AnyCodableValue]?
    let isEnabled: Bool?

    enum CodingKeys: String, CodingKey {
        case applianceType = "appliance_type"
        case fatigueLevel = "fatigue_level"
        case operation
        case newThreshold = "new_threshold"
        case isEnabled = "is_enabled"
    }
}

/// Appliance recommendation request for `/api/appliances/recommend/{user_id}` POST
struct ApplianceRecommendRequest: Codable {
    let latitude: Double
    let longitude: Double
    let sido: String  // Default: "서울"
}

/// Appliance control request for `/api/appliances/smart-control/{user_id}` POST
struct ApplianceControlRequest: Codable {
    let applianceType: String
    let action: String  // "on", "off", "set"
    let settings: [String: AnyCodableValue]?

    enum CodingKeys: String, CodingKey {
        case applianceType = "appliance_type"
        case action, settings
    }
}
