import Foundation

// MARK: - Location Models

/// Location update request for `/api/location/update` POST
struct LocationUpdate: Codable {
    let userId: String
    let latitude: Double
    let longitude: Double
    let accuracy: Double?
    let timestamp: Double?

    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case latitude, longitude, accuracy, timestamp
    }
}

/// Geofence configuration for `/api/location/geofence/config` PUT and GET
struct GeofenceConfig: Codable {
    let latitude: Double
    let longitude: Double
    let radiusMeters: Double  // Default: 100

    enum CodingKeys: String, CodingKey {
        case latitude, longitude
        case radiusMeters = "radius_meters"
    }
}
