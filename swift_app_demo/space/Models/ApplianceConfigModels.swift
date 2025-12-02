import Foundation

// MARK: - Air Conditioner Config Models

/// Air conditioner configuration response from `/api/appliances/config/ac/{appliance_id}` GET
struct AirConditionerConfig: Codable, Identifiable {
    let id: String
    let applianceId: String
    let powerState: String
    let mode: String?
    let targetTempC: Double?
    let fanSpeed: String?
    let swingMode: String?
    let targetHumidityPct: Double?
    let updatedAt: Date

    enum CodingKeys: String, CodingKey {
        case id
        case applianceId = "appliance_id"
        case powerState = "power_state"
        case mode
        case targetTempC = "target_temp_c"
        case fanSpeed = "fan_speed"
        case swingMode = "swing_mode"
        case targetHumidityPct = "target_humidity_pct"
        case updatedAt = "updated_at"
    }
}

/// Air conditioner configuration upsert for `/api/appliances/config/ac` POST
struct AirConditionerConfigCreate: Codable {
    let applianceId: String
    let powerState: String
    let mode: String?
    let targetTempC: Double?
    let fanSpeed: String?
    let swingMode: String?
    let targetHumidityPct: Double?

    enum CodingKeys: String, CodingKey {
        case applianceId = "appliance_id"
        case powerState = "power_state"
        case mode
        case targetTempC = "target_temp_c"
        case fanSpeed = "fan_speed"
        case swingMode = "swing_mode"
        case targetHumidityPct = "target_humidity_pct"
    }
}

// MARK: - TV Config Models

/// TV configuration response from `/api/appliances/config/tv/{appliance_id}` GET
struct TvConfig: Codable, Identifiable {
    let id: String
    let applianceId: String
    let powerState: String
    let volume: Int?
    let channel: Int?
    let inputSource: String?
    let brightness: Int?
    let contrast: Int?
    let color: Int?
    let updatedAt: Date

    enum CodingKeys: String, CodingKey {
        case id
        case applianceId = "appliance_id"
        case powerState = "power_state"
        case volume, channel
        case inputSource = "input_source"
        case brightness, contrast, color
        case updatedAt = "updated_at"
    }
}

/// TV configuration upsert for `/api/appliances/config/tv` POST
struct TvConfigCreate: Codable {
    let applianceId: String
    let powerState: String
    let volume: Int?
    let channel: Int?
    let inputSource: String?
    let brightness: Int?
    let contrast: Int?
    let color: Int?

    enum CodingKeys: String, CodingKey {
        case applianceId = "appliance_id"
        case powerState = "power_state"
        case volume, channel
        case inputSource = "input_source"
        case brightness, contrast, color
    }
}

// MARK: - Air Purifier Config Models

/// Air purifier configuration response from `/api/appliances/config/air_purifier/{appliance_id}` GET
struct AirPurifierConfig: Codable, Identifiable {
    let id: String
    let applianceId: String
    let powerState: String
    let mode: String?
    let fanSpeed: String?
    let ionizerOn: Bool?
    let targetPm10: Int?
    let targetPm2_5: Int?
    let updatedAt: Date

    enum CodingKeys: String, CodingKey {
        case id
        case applianceId = "appliance_id"
        case powerState = "power_state"
        case mode
        case fanSpeed = "fan_speed"
        case ionizerOn = "ionizer_on"
        case targetPm10 = "target_pm10"
        case targetPm2_5 = "target_pm2_5"
        case updatedAt = "updated_at"
    }
}

/// Air purifier configuration upsert for `/api/appliances/config/air_purifier` POST
struct AirPurifierConfigCreate: Codable {
    let applianceId: String
    let powerState: String
    let mode: String?
    let fanSpeed: String?
    let ionizerOn: Bool?
    let targetPm10: Int?
    let targetPm2_5: Int?

    enum CodingKeys: String, CodingKey {
        case applianceId = "appliance_id"
        case powerState = "power_state"
        case mode
        case fanSpeed = "fan_speed"
        case ionizerOn = "ionizer_on"
        case targetPm10 = "target_pm10"
        case targetPm2_5 = "target_pm2_5"
    }
}

// MARK: - Light Config Models

/// Light configuration response from `/api/appliances/config/light/{appliance_id}` GET
struct LightConfig: Codable, Identifiable {
    let id: String
    let applianceId: String
    let powerState: String
    let brightnessPct: Int?
    let colorTemperatureK: Int?
    let colorHex: String?
    let scene: String?
    let updatedAt: Date

    enum CodingKeys: String, CodingKey {
        case id
        case applianceId = "appliance_id"
        case powerState = "power_state"
        case brightnessPct = "brightness_pct"
        case colorTemperatureK = "color_temperature_k"
        case colorHex = "color_hex"
        case scene
        case updatedAt = "updated_at"
    }
}

/// Light configuration upsert for `/api/appliances/config/light` POST
struct LightConfigCreate: Codable {
    let applianceId: String
    let powerState: String
    let brightnessPct: Int?
    let colorTemperatureK: Int?
    let colorHex: String?
    let scene: String?

    enum CodingKeys: String, CodingKey {
        case applianceId = "appliance_id"
        case powerState = "power_state"
        case brightnessPct = "brightness_pct"
        case colorTemperatureK = "color_temperature_k"
        case colorHex = "color_hex"
        case scene
    }
}

// MARK: - Humidifier Config Models

/// Humidifier configuration response from `/api/appliances/config/humidifier/{appliance_id}` GET
struct HumidifierConfig: Codable, Identifiable {
    let id: String
    let applianceId: String
    let powerState: String
    let mode: String?
    let mistLevel: Int?
    let targetHumidityPct: Int?
    let warmMist: Bool?
    let updatedAt: Date

    enum CodingKeys: String, CodingKey {
        case id
        case applianceId = "appliance_id"
        case powerState = "power_state"
        case mode
        case mistLevel = "mist_level"
        case targetHumidityPct = "target_humidity_pct"
        case warmMist = "warm_mist"
        case updatedAt = "updated_at"
    }
}

/// Humidifier configuration upsert for `/api/appliances/config/humidifier` POST
struct HumidifierConfigCreate: Codable {
    let applianceId: String
    let powerState: String
    let mode: String?
    let mistLevel: Int?
    let targetHumidityPct: Int?
    let warmMist: Bool?

    enum CodingKeys: String, CodingKey {
        case applianceId = "appliance_id"
        case powerState = "power_state"
        case mode
        case mistLevel = "mist_level"
        case targetHumidityPct = "target_humidity_pct"
        case warmMist = "warm_mist"
    }
}

// Note: Dehumidifier config models can be added similarly if needed
// They follow the same pattern as other appliance configs
