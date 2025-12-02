import Foundation

// MARK: - Weather Observation Models

/// Weather observation upload for `/api/weather/observation` PUT
struct WeatherObservationCreate: Codable {
    let nx: Int
    let ny: Int
    let asOf: Date
    let provider: String
    let conditionCode: String?
    let precipType: String?
    let tempC: Double?
    let humidityPct: Double?
    let windSpeedMps: Double?
    let pm10: Double?
    let pm2_5: Double?
    let rawJson: [String: AnyCodableValue]?

    enum CodingKeys: String, CodingKey {
        case nx, ny, provider
        case asOf = "as_of"
        case conditionCode = "condition_code"
        case precipType = "precip_type"
        case tempC = "temp_c"
        case humidityPct = "humidity_pct"
        case windSpeedMps = "wind_speed_mps"
        case pm10
        case pm2_5 = "pm2_5"
        case rawJson = "raw_json"
    }
}

/// Weather observation response from `/api/weather/observation` PUT
typealias WeatherObservationRead = WeatherObservationCreate

// MARK: - Weather Response Models

/// Weather data response from `/api/weather/current` GET
struct WeatherResponse: Codable {
    let temperature: Double?
    let humidity: Double?
    let precipitation: Double?
    let windSpeed: Double?
    let pm10: Double?
    let pm2_5: Double?
    let fetchedAt: Date

    enum CodingKeys: String, CodingKey {
        case temperature, humidity, precipitation
        case windSpeed = "wind_speed"
        case pm10
        case pm2_5 = "pm2_5"
        case fetchedAt = "fetched_at"
    }
}
