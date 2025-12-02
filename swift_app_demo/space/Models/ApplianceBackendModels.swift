import Foundation

/// Base appliance info returned from `/api/appliances/user/{user_id}`
struct BackendAppliance: Codable {
    let id: String
    let applianceCode: String
    let displayName: String
    let placeId: String?
    let vendor: String?
    let modelName: String?
    let connectionType: String?
    let status: String?

    enum CodingKeys: String, CodingKey {
        case id
        case applianceCode = "appliance_code"
        case displayName = "display_name"
        case placeId = "place_id"
        case vendor
        case modelName = "model_name"
        case connectionType = "connection_type"
        case status
    }
}

/// Real-time appliance status returned from `/api/appliances/smart-status/{user_id}`
struct BackendApplianceStatus: Codable {
    let applianceType: String
    let isOn: Bool
    let currentSettings: [String: AnyCodableValue]?
    let lastCommand: [String: AnyCodableValue]?
    let lastUpdated: String?

    enum CodingKeys: String, CodingKey {
        case applianceType = "appliance_type"
        case isOn = "is_on"
        case currentSettings = "current_settings"
        case lastCommand = "last_command"
        case lastUpdated = "last_updated"
    }
}

struct SmartStatusResponse: Codable {
    let userId: String
    let appliances: [BackendApplianceStatus]

    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case appliances
    }
}

extension ApplianceType {
    init?(backendCode: String) {
        switch backendCode.uppercased() {
        case "AC", "AIR_CONDITIONER", "AIRCON":
            self = .airConditioner
        case "LIGHT", "LIGHTING":
            self = .lighting
        case "AIR_PURIFIER", "AIRPURIFIER":
            self = .airPurifier
        case "DEHUMIDIFIER":
            self = .dehumidifier
        case "HUMIDIFIER":
            self = .humidifier
        case "TV", "TELEVISION":
            self = .tv
        default:
            return nil
        }
    }

    init?(backendLabel: String) {
        switch backendLabel.lowercased() {
        case "에어컨", "air conditioner", "ac":
            self = .airConditioner
        case "조명", "light":
            self = .lighting
        case "공기청정기", "air purifier":
            self = .airPurifier
        case "제습기", "dehumidifier":
            self = .dehumidifier
        case "가습기", "humidifier":
            self = .humidifier
        case "tv", "티비", "television":
            self = .tv
        default:
            return nil
        }
    }

    static func resolve(backendCode: String?, backendLabel: String? = nil) -> ApplianceType? {
        if let code = backendCode, let type = ApplianceType(backendCode: code) {
            return type
        }

        if let label = backendLabel, let type = ApplianceType(backendLabel: label) {
            return type
        }

        return nil
    }
}

extension ApplianceItem {
    /// Create UI model from backend base info + status. Returns nil if required fields are missing.
    init?(backend: BackendAppliance, status: BackendApplianceStatus?) {
        guard let resolvedType = ApplianceType.resolve(
            backendCode: backend.applianceCode,
            backendLabel: status?.applianceType
        ) else {
            return nil
        }

        let settings = status?.currentSettings ?? [:]

        func number(for key: String) -> Double? {
            guard let raw = settings[key]?.value else { return nil }
            return ApplianceItem.numericValue(from: raw)
        }

        let mode = (settings["mode"]?.value as? String)
            ?? (settings["scene"]?.value as? String)
            ?? ""

        let statusText = backend.status
            ?? (settings["status"]?.value as? String)
            ?? ""

        var primary: Double?
        var secondary: Double?

        switch resolvedType {
        case .airConditioner:
            primary = number(for: "target_temp_c")
            secondary = number(for: "fan_speed")
        case .lighting:
            primary = number(for: "brightness_pct")
            secondary = number(for: "color_temperature_k")
        case .airPurifier:
            primary = number(for: "fan_speed")
            secondary = number(for: "target_pm2_5") ?? number(for: "target_pm10")
        case .dehumidifier:
            primary = number(for: "target_humidity_pct")
            secondary = number(for: "fan_speed")
        case .humidifier:
            primary = number(for: "target_humidity_pct")
            secondary = number(for: "mist_level")
        case .tv:
            primary = number(for: "volume")
            secondary = number(for: "brightness")
        }

        guard let primaryValue = primary else { return nil }

        self.init(
            id: UUID(uuidString: backend.id) ?? UUID(),
            backendId: backend.id,  // Store original backend ID
            type: resolvedType,
            location: backend.displayName,
            status: statusText,
            mode: mode,
            isOn: status?.isOn ?? false,
            primaryValue: primaryValue,
            secondaryValue: secondary,
            hasCustomStatus: false
        )
    }

    /// Convert backend-encoded numeric values (Double/Int/String levels) into Double.
    private static func numericValue(from value: Any?) -> Double? {
        switch value {
        case let number as NSNumber:
            return number.doubleValue
        case let double as Double:
            return double
        case let int as Int:
            return Double(int)
        case let string as String:
            switch string.lowercased() {
            case "low":
                return 1
            case "mid", "medium":
                return 3
            case "high":
                return 5
            default:
                return Double(string)
            }
        default:
            return nil
        }
    }
}
