import Foundation

// MARK: - User Models

/// Base user model returned from `/api/users/` GET
struct User: Codable, Identifiable {
    let id: String
    let email: String
    let createdAt: Date
    let deletedAt: Date?

    enum CodingKeys: String, CodingKey {
        case id, email
        case createdAt = "created_at"
        case deletedAt = "deleted_at"
    }
}

/// User creation request for `/api/users/` POST
struct UserCreate: Codable {
    let email: String
}

// MARK: - User Phone Models

/// User phone response from `/api/users/{user_id}/phone` GET
struct UserPhone: Codable, Identifiable {
    let id: String
    let userId: String
    let e164Number: String
    let countryCode: String?
    let platform: String?
    let modelName: String?
    let displayName: String?
    let osVersion: String?
    let deviceIdHash: String?
    let pushToken: String?
    let isVerified: Bool?
    let registeredAt: Date
    let lastSeenAt: Date?

    enum CodingKeys: String, CodingKey {
        case id
        case userId = "user_id"
        case e164Number = "e164_number"
        case countryCode = "country_code"
        case platform
        case modelName = "model_name"
        case displayName = "display_name"
        case osVersion = "os_version"
        case deviceIdHash = "device_id_hash"
        case pushToken = "push_token"
        case isVerified = "is_verified"
        case registeredAt = "registered_at"
        case lastSeenAt = "last_seen_at"
    }
}

/// User phone upsert request for `/api/users/{user_id}/phone` PUT
struct UserPhoneBase: Codable {
    let e164Number: String
    let countryCode: String?
    let platform: String?
    let modelName: String?
    let displayName: String?
    let osVersion: String?
    let deviceIdHash: String?
    let pushToken: String?
    let isVerified: Bool?

    enum CodingKeys: String, CodingKey {
        case e164Number = "e164_number"
        case countryCode = "country_code"
        case platform
        case modelName = "model_name"
        case displayName = "display_name"
        case osVersion = "os_version"
        case deviceIdHash = "device_id_hash"
        case pushToken = "push_token"
        case isVerified = "is_verified"
    }
}

// MARK: - User Device Models

/// User device (wearable) response from `/api/users/{user_id}/device` GET
struct UserDevice: Codable, Identifiable {
    let id: String
    let userId: String
    let kind: String  // e.g., "apple_watch", "samsung_watch"
    let platform: String?
    let modelName: String?
    let displayName: String?
    let osVersion: String?
    let serialHash: String?
    let registeredAt: Date
    let lastSeenAt: Date?

    enum CodingKeys: String, CodingKey {
        case id
        case userId = "user_id"
        case kind, platform
        case modelName = "model_name"
        case displayName = "display_name"
        case osVersion = "os_version"
        case serialHash = "serial_hash"
        case registeredAt = "registered_at"
        case lastSeenAt = "last_seen_at"
    }
}

/// User device upsert request for `/api/users/{user_id}/device` PUT
struct UserDeviceBase: Codable {
    let kind: String
    let platform: String?
    let modelName: String?
    let displayName: String?
    let osVersion: String?
    let serialHash: String?

    enum CodingKeys: String, CodingKey {
        case kind, platform
        case modelName = "model_name"
        case displayName = "display_name"
        case osVersion = "os_version"
        case serialHash = "serial_hash"
    }
}

// MARK: - User Profile Model

/// User with phone and device info from `/api/users/{user_id}/profile` GET
struct UserWithRelations: Codable, Identifiable {
    let id: String
    let email: String
    let createdAt: Date
    let deletedAt: Date?
    let phone: UserPhone?
    let device: UserDevice?

    enum CodingKeys: String, CodingKey {
        case id, email, phone, device
        case createdAt = "created_at"
        case deletedAt = "deleted_at"
    }
}
