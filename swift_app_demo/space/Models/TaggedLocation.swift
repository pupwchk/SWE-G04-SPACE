//
//  TaggedLocation.swift
//  space
//
//  Created by Claude on 2025-11-27.
//

import Foundation
import CoreLocation

// MARK: - Location Tag Types

enum LocationTag: String, CaseIterable, Codable {
    case home = "집"
    case dormitory = "기숙사"
    case office = "회사"
    case school = "학교"
    case cafe = "카페"
    case custom = "기타"

    var icon: String {
        switch self {
        case .home: return "🏠"
        case .dormitory: return "🏢"
        case .office: return "💼"
        case .school: return "🎓"
        case .cafe: return "☕️"
        case .custom: return "📍"
        }
    }

    var displayName: String {
        return self.rawValue
    }
}

// MARK: - Tagged Location Model

struct TaggedLocation: Codable, Identifiable, Equatable {
    let id: UUID
    let userId: String
    let latitude: Double
    let longitude: Double
    let tag: LocationTag
    let customName: String?
    let isHome: Bool
    let notificationEnabled: Bool
    let notificationRadius: Int  // in meters
    let createdAt: Date
    let updatedAt: Date

    var coordinate: CLLocationCoordinate2D {
        CLLocationCoordinate2D(latitude: latitude, longitude: longitude)
    }

    var location: CLLocation {
        CLLocation(latitude: latitude, longitude: longitude)
    }

    var displayName: String {
        customName ?? tag.displayName
    }

    var fullDisplayName: String {
        if let customName = customName {
            return "\(tag.icon) \(customName)"
        }
        return "\(tag.icon) \(tag.displayName)"
    }

    init(
        id: UUID = UUID(),
        userId: String,
        coordinate: CLLocationCoordinate2D,
        tag: LocationTag,
        customName: String? = nil,
        isHome: Bool = false,
        notificationEnabled: Bool = true,
        notificationRadius: Int = 1000,
        createdAt: Date = Date(),
        updatedAt: Date = Date()
    ) {
        self.id = id
        self.userId = userId
        self.latitude = coordinate.latitude
        self.longitude = coordinate.longitude
        self.tag = tag
        self.customName = customName
        self.isHome = isHome
        self.notificationEnabled = notificationEnabled
        self.notificationRadius = notificationRadius
        self.createdAt = createdAt
        self.updatedAt = updatedAt
    }

    // MARK: - Codable

    enum CodingKeys: String, CodingKey {
        case id
        case userId = "user_id"
        case latitude
        case longitude
        case tag
        case customName = "custom_name"
        case isHome = "is_home"
        case notificationEnabled = "notification_enabled"
        case notificationRadius = "notification_radius"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)

        id = try container.decode(UUID.self, forKey: .id)
        userId = try container.decode(String.self, forKey: .userId)
        latitude = try container.decode(Double.self, forKey: .latitude)
        longitude = try container.decode(Double.self, forKey: .longitude)

        // Handle tag as either enum or string
        if let tagString = try? container.decode(String.self, forKey: .tag) {
            tag = LocationTag(rawValue: tagString) ?? .custom
        } else {
            tag = try container.decode(LocationTag.self, forKey: .tag)
        }

        customName = try container.decodeIfPresent(String.self, forKey: .customName)
        isHome = try container.decode(Bool.self, forKey: .isHome)
        notificationEnabled = try container.decode(Bool.self, forKey: .notificationEnabled)
        notificationRadius = try container.decode(Int.self, forKey: .notificationRadius)

        createdAt = try container.decode(Date.self, forKey: .createdAt)
        updatedAt = try container.decode(Date.self, forKey: .updatedAt)
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)

        try container.encode(id, forKey: .id)
        try container.encode(userId, forKey: .userId)
        try container.encode(latitude, forKey: .latitude)
        try container.encode(longitude, forKey: .longitude)
        try container.encode(tag.rawValue, forKey: .tag)
        try container.encodeIfPresent(customName, forKey: .customName)
        try container.encode(isHome, forKey: .isHome)
        try container.encode(notificationEnabled, forKey: .notificationEnabled)
        try container.encode(notificationRadius, forKey: .notificationRadius)
        try container.encode(createdAt, forKey: .createdAt)
        try container.encode(updatedAt, forKey: .updatedAt)
    }

    // MARK: - Equatable

    static func == (lhs: TaggedLocation, rhs: TaggedLocation) -> Bool {
        lhs.id == rhs.id
    }

    // MARK: - Helper Methods

    func distance(from location: CLLocation) -> CLLocationDistance {
        return location.distance(from: self.location)
    }

    func isWithinRadius(of location: CLLocation) -> Bool {
        return distance(from: location) <= Double(notificationRadius)
    }

    func updated(
        coordinate: CLLocationCoordinate2D? = nil,
        tag: LocationTag? = nil,
        customName: String? = nil,
        isHome: Bool? = nil,
        notificationEnabled: Bool? = nil,
        notificationRadius: Int? = nil
    ) -> TaggedLocation {
        let targetCoordinate = coordinate ?? self.coordinate
        return TaggedLocation(
            id: self.id,
            userId: self.userId,
            coordinate: targetCoordinate,
            tag: tag ?? self.tag,
            customName: customName ?? self.customName,
            isHome: isHome ?? self.isHome,
            notificationEnabled: notificationEnabled ?? self.notificationEnabled,
            notificationRadius: notificationRadius ?? self.notificationRadius,
            createdAt: self.createdAt,
            updatedAt: Date()
        )
    }
}

// MARK: - Location Notification Model

struct LocationNotification: Codable, Identifiable {
    let id: UUID
    let userId: String
    let taggedLocationId: UUID
    let triggeredAt: Date
    let distanceMeters: Int
    let acknowledged: Bool

    enum CodingKeys: String, CodingKey {
        case id
        case userId = "user_id"
        case taggedLocationId = "tagged_location_id"
        case triggeredAt = "triggered_at"
        case distanceMeters = "distance_meters"
        case acknowledged
    }

    init(
        id: UUID = UUID(),
        userId: String,
        taggedLocationId: UUID,
        triggeredAt: Date = Date(),
        distanceMeters: Int,
        acknowledged: Bool = false
    ) {
        self.id = id
        self.userId = userId
        self.taggedLocationId = taggedLocationId
        self.triggeredAt = triggeredAt
        self.distanceMeters = distanceMeters
        self.acknowledged = acknowledged
    }
}
