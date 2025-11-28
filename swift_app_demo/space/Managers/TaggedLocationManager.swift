//
//  TaggedLocationManager.swift
//  space
//
//  Created by Claude on 2025-11-27.
//

import Foundation
import CoreLocation
import Combine

@MainActor
class TaggedLocationManager: ObservableObject {
    static let shared = TaggedLocationManager()

    @Published var taggedLocations: [TaggedLocation] = []
    @Published var isLoading = false
    @Published var error: Error?

    private let supabase = SupabaseManager.shared
    private var cancellables = Set<AnyCancellable>()

    // Dedicated session with short timeouts so UI isn't blocked by long waits
    private let session: URLSession = {
        let config = URLSessionConfiguration.default
        config.timeoutIntervalForRequest = 10
        config.timeoutIntervalForResource = 10
        return URLSession(configuration: config)
    }()

    // Cache for last notification times to prevent duplicate notifications
    private var lastNotificationTimes: [UUID: Date] = [:]
    private let minimumNotificationInterval: TimeInterval = 3600 // 1 hour

    private init() {}

    // MARK: - Load Tagged Locations

    func loadTaggedLocations() async {
        isLoading = true
        defer { isLoading = false }

        guard let userId = supabase.currentUser?.id else {
            print("  User not authenticated")
            return
        }

        guard let accessToken = supabase.getAccessToken() else {
            print("  No access token available")
            return
        }

        guard let url = URL(string: "https://aghsjspkzivcpibwwzvu.supabase.co/rest/v1/tagged_locations?user_id=eq.\(userId)&order=created_at.desc") else {
            print("  Invalid URL")
            return
        }

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFnaHNqc3Breml2Y3BpYnd3enZ1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI0OTI0OTMsImV4cCI6MjA3ODA2ODQ5M30.vtas9X3hNPoJaepihOc2C3Yxx5l38U3_-bTkKnYLAew", forHTTPHeaderField: "apikey")
        request.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        do {
            let (data, response) = try await session.data(for: request)

            // Check for authentication errors
            if let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 401 || httpResponse.statusCode == 403 {
                print("  Authentication failed: \(httpResponse.statusCode)")
                self.error = TaggedLocationError.notAuthenticated
                return
            }

            let decoder = JSONDecoder()
            decoder.dateDecodingStrategy = .custom { decoder in
                let container = try decoder.singleValueContainer()
                let dateString = try container.decode(String.self)

                let formatter = ISO8601DateFormatter()
                formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]

                if let date = formatter.date(from: dateString) {
                    return date
                }

                // Fallback to standard ISO8601 without fractional seconds
                formatter.formatOptions = [.withInternetDateTime]
                if let date = formatter.date(from: dateString) {
                    return date
                }

                throw DecodingError.dataCorruptedError(in: container, debugDescription: "Cannot decode date string \(dateString)")
            }
            let locations = try decoder.decode([TaggedLocation].self, from: data)
            self.taggedLocations = locations
            print(" Loaded \(locations.count) tagged locations")
        } catch {
            print("  Failed to load tagged locations: \(error)")
            self.error = error
        }
    }

    // MARK: - Create Tagged Location

    func createTaggedLocation(
        coordinate: CLLocationCoordinate2D,
        tag: LocationTag,
        customName: String? = nil,
        isHome: Bool = false,
        notificationEnabled: Bool = true,
        notificationRadius: Int = 1000
    ) async throws -> TaggedLocation {
        guard let userId = supabase.currentUser?.id else {
            throw TaggedLocationError.notAuthenticated
        }

        guard let accessToken = supabase.getAccessToken() else {
            throw TaggedLocationError.notAuthenticated
        }

        // DELETE existing homes before creating new one
        if isHome {
            try await deleteOtherHomeLocations()
        }

        let newLocation = TaggedLocation(
            userId: userId,
            coordinate: coordinate,
            tag: tag,
            customName: customName,
            isHome: isHome,
            notificationEnabled: notificationEnabled,
            notificationRadius: notificationRadius
        )

        guard let url = URL(string: "https://aghsjspkzivcpibwwzvu.supabase.co/rest/v1/tagged_locations") else {
            throw TaggedLocationError.creationFailed
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFnaHNqc3Breml2Y3BpYnd3enZ1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI0OTI0OTMsImV4cCI6MjA3ODA2ODQ5M30.vtas9X3hNPoJaepihOc2C3Yxx5l38U3_-bTkKnYLAew", forHTTPHeaderField: "apikey")
        request.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("return=representation", forHTTPHeaderField: "Prefer")

        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .custom { date, encoder in
            var container = encoder.singleValueContainer()
            let formatter = ISO8601DateFormatter()
            formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
            try container.encode(formatter.string(from: date))
        }
        request.httpBody = try encoder.encode(newLocation)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 201 else {
            if let httpResponse = response as? HTTPURLResponse {
                if httpResponse.statusCode == 401 || httpResponse.statusCode == 403 {
                    throw TaggedLocationError.notAuthenticated
                }
            }
            throw TaggedLocationError.creationFailed
        }

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .custom { decoder in
            let container = try decoder.singleValueContainer()
            let dateString = try container.decode(String.self)

            let formatter = ISO8601DateFormatter()
            formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]

            if let date = formatter.date(from: dateString) {
                return date
            }

            formatter.formatOptions = [.withInternetDateTime]
            if let date = formatter.date(from: dateString) {
                return date
            }

            throw DecodingError.dataCorruptedError(in: container, debugDescription: "Cannot decode date string \(dateString)")
        }
        let locations = try decoder.decode([TaggedLocation].self, from: data)

        guard let created = locations.first else {
            print("  Creation returned no data. Response: \(String(data: data, encoding: .utf8) ?? "Unable to decode response")")
            throw TaggedLocationError.creationFailed
        }

        // Add to local array
        taggedLocations.insert(created, at: 0)

        print(" Created tagged location: \(created.fullDisplayName)")

        // Also create Place in FastAPI
        Task {
            let category = mapLocationTagToCategory(created.tag)
            _ = await AutoTrackingManager.shared.createPlaceFromLocation(
                label: created.fullDisplayName,
                category: category,
                coordinate: coordinate,
                radiusMeters: Double(notificationRadius)
            )
        }

        return created
    }

    /// Map LocationTag to FastAPI place category
    private func mapLocationTagToCategory(_ tag: LocationTag) -> String? {
        switch tag {
        case .home:
            return "HOME"
        case .dormitory:
            return "DORMITORY"
        case .office:
            return "WORK"
        case .school:
            return "SCHOOL"
        case .cafe:
            return "CAFE"
        case .custom:
            return "OTHER"
        }
    }

    // MARK: - Update Tagged Location

    func updateTaggedLocation(
        _ location: TaggedLocation,
        coordinate: CLLocationCoordinate2D? = nil,
        tag: LocationTag? = nil,
        customName: String? = nil,
        isHome: Bool? = nil,
        notificationEnabled: Bool? = nil,
        notificationRadius: Int? = nil
    ) async throws {
        guard let accessToken = supabase.getAccessToken() else {
            throw TaggedLocationError.notAuthenticated
        }

        let updated = location.updated(
            coordinate: coordinate,
            tag: tag,
            customName: customName,
            isHome: isHome,
            notificationEnabled: notificationEnabled,
            notificationRadius: notificationRadius
        )

        guard let url = URL(string: "https://aghsjspkzivcpibwwzvu.supabase.co/rest/v1/tagged_locations?id=eq.\(location.id.uuidString)") else {
            throw TaggedLocationError.updateFailed
        }

        var request = URLRequest(url: url)
        request.httpMethod = "PATCH"
        request.setValue("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFnaHNqc3Breml2Y3BpYnd3enZ1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI0OTI0OTMsImV4cCI6MjA3ODA2ODQ5M30.vtas9X3hNPoJaepihOc2C3Yxx5l38U3_-bTkKnYLAew", forHTTPHeaderField: "apikey")
        request.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("return=representation", forHTTPHeaderField: "Prefer")

        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .custom { date, encoder in
            var container = encoder.singleValueContainer()
            let formatter = ISO8601DateFormatter()
            formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
            try container.encode(formatter.string(from: date))
        }
        request.httpBody = try encoder.encode(updated)

        let (data, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 200 else {
            if let httpResponse = response as? HTTPURLResponse {
                if httpResponse.statusCode == 401 || httpResponse.statusCode == 403 {
                    throw TaggedLocationError.notAuthenticated
                }
            }
            throw TaggedLocationError.updateFailed
        }

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .custom { decoder in
            let container = try decoder.singleValueContainer()
            let dateString = try container.decode(String.self)

            let formatter = ISO8601DateFormatter()
            formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]

            if let date = formatter.date(from: dateString) {
                return date
            }

            formatter.formatOptions = [.withInternetDateTime]
            if let date = formatter.date(from: dateString) {
                return date
            }

            throw DecodingError.dataCorruptedError(in: container, debugDescription: "Cannot decode date string \(dateString)")
        }
        let locations = try decoder.decode([TaggedLocation].self, from: data)

        guard let result = locations.first else {
            print("  Update returned no data. Response: \(String(data: data, encoding: .utf8) ?? "Unable to decode response")")
            throw TaggedLocationError.updateFailed
        }

        // Update local array
        if let index = taggedLocations.firstIndex(where: { $0.id == location.id }) {
            taggedLocations[index] = result
        }

        print(" Updated tagged location: \(result.fullDisplayName)")
    }

    // MARK: - Delete Tagged Location

    func deleteTaggedLocation(_ location: TaggedLocation) async throws {
        guard let accessToken = supabase.getAccessToken() else {
            throw TaggedLocationError.notAuthenticated
        }

        guard let url = URL(string: "https://aghsjspkzivcpibwwzvu.supabase.co/rest/v1/tagged_locations?id=eq.\(location.id.uuidString)") else {
            throw TaggedLocationError.deletionFailed
        }

        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"
        request.setValue("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFnaHNqc3Breml2Y3BpYnd3enZ1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI0OTI0OTMsImV4cCI6MjA3ODA2ODQ5M30.vtas9X3hNPoJaepihOc2C3Yxx5l38U3_-bTkKnYLAew", forHTTPHeaderField: "apikey")
        request.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")

        let (_, response) = try await session.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse, httpResponse.statusCode == 204 else {
            if let httpResponse = response as? HTTPURLResponse {
                if httpResponse.statusCode == 401 || httpResponse.statusCode == 403 {
                    throw TaggedLocationError.notAuthenticated
                }
            }
            throw TaggedLocationError.deletionFailed
        }

        // Remove from local array
        taggedLocations.removeAll { $0.id == location.id }

        print(" Deleted tagged location: \(location.fullDisplayName)")
    }

    // MARK: - Find Tagged Location for Coordinate

    func findTaggedLocation(near coordinate: CLLocationCoordinate2D, within radius: CLLocationDistance = 100) -> TaggedLocation? {
        let searchLocation = CLLocation(latitude: coordinate.latitude, longitude: coordinate.longitude)

        return taggedLocations.first { location in
            let distance = searchLocation.distance(from: location.location)
            return distance <= radius
        }
    }

    // MARK: - Check Proximity to Tagged Locations

    func checkProximity(to currentLocation: CLLocation) -> [(location: TaggedLocation, distance: CLLocationDistance)] {
        var nearbyLocations: [(TaggedLocation, CLLocationDistance)] = []

        for taggedLocation in taggedLocations {
            guard taggedLocation.notificationEnabled else { continue }

            let distance = currentLocation.distance(from: taggedLocation.location)

            // Check if within notification radius
            if distance <= Double(taggedLocation.notificationRadius) {
                nearbyLocations.append((taggedLocation, distance))
            }
        }

        return nearbyLocations.sorted { $0.1 < $1.1 }
    }

    // MARK: - Should Send Notification

    func shouldSendNotification(for location: TaggedLocation) -> Bool {
        // Check if we've sent a notification recently
        if let lastTime = lastNotificationTimes[location.id] {
            let timeSinceLastNotification = Date().timeIntervalSince(lastTime)
            if timeSinceLastNotification < minimumNotificationInterval {
                return false
            }
        }

        return true
    }

    // MARK: - Record Notification

    func recordNotification(for location: TaggedLocation, distance: CLLocationDistance) async {
        guard let userId = supabase.currentUser?.id else { return }
        guard let accessToken = supabase.getAccessToken() else {
            print("  No access token available for notification recording")
            return
        }

        // Update last notification time
        lastNotificationTimes[location.id] = Date()

        // Save to database
        let notification = LocationNotification(
            userId: userId,
            taggedLocationId: location.id,
            distanceMeters: Int(distance)
        )

        guard let url = URL(string: "https://aghsjspkzivcpibwwzvu.supabase.co/rest/v1/location_notifications") else {
            print("  Invalid URL for notification recording")
            return
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFnaHNqc3Breml2Y3BpYnd3enZ1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI0OTI0OTMsImV4cCI6MjA3ODA2ODQ5M30.vtas9X3hNPoJaepihOc2C3Yxx5l38U3_-bTkKnYLAew", forHTTPHeaderField: "apikey")
        request.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        do {
            let encoder = JSONEncoder()
            encoder.dateEncodingStrategy = .custom { date, encoder in
                var container = encoder.singleValueContainer()
                let formatter = ISO8601DateFormatter()
                formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
                try container.encode(formatter.string(from: date))
            }
            request.httpBody = try encoder.encode(notification)

            let (_, response) = try await session.data(for: request)

            if let httpResponse = response as? HTTPURLResponse {
                if httpResponse.statusCode == 201 {
                    print(" Recorded notification for \(location.fullDisplayName)")
                } else if httpResponse.statusCode == 401 || httpResponse.statusCode == 403 {
                    print("  Authentication failed when recording notification")
                }
            }
        } catch {
            print("  Failed to record notification: \(error)")
        }
    }

    // MARK: - Get Home Locations

    var homeLocations: [TaggedLocation] {
        taggedLocations.filter { $0.isHome }
    }

    var primaryHomeLocation: TaggedLocation? {
        homeLocations.first
    }

    // MARK: - Get Locations by Tag

    func locations(with tag: LocationTag) -> [TaggedLocation] {
        taggedLocations.filter { $0.tag == tag }
    }

    // MARK: - Delete Other Home Locations

    /// Deletes all home locations except the specified one
    private func deleteOtherHomeLocations(except locationId: UUID? = nil) async throws {
        let homesToDelete = homeLocations.filter { location in
            if let exceptId = locationId {
                return location.id != exceptId
            }
            return true
        }

        for home in homesToDelete {
            try await deleteTaggedLocation(home)
        }
    }

    /// Clean up duplicate home locations, keeping only the most recent one
    func cleanupDuplicateHomes() async throws {
        let homes = homeLocations

        guard homes.count > 1 else {
            print("✅ No duplicate homes to clean up")
            return
        }

        // Keep the first one (most recent due to created_at.desc ordering)
        let homesToDelete = Array(homes.dropFirst())

        print("🧹 Cleaning up \(homesToDelete.count) duplicate home(s)")

        for home in homesToDelete {
            try await deleteTaggedLocation(home)
        }

        print("✅ Cleanup complete. Only 1 home location remains.")
    }

    // MARK: - Clear Cache

    func clearCache() {
        taggedLocations = []
        lastNotificationTimes = [:]
        error = nil
    }
}

// MARK: - Errors

enum TaggedLocationError: LocalizedError {
    case notAuthenticated
    case invalidCoordinate
    case creationFailed
    case updateFailed
    case deletionFailed

    var errorDescription: String? {
        switch self {
        case .notAuthenticated:
            return "사용자 인증이 필요합니다"
        case .invalidCoordinate:
            return "유효하지 않은 좌표입니다"
        case .creationFailed:
            return "위치 태그 생성에 실패했습니다"
        case .updateFailed:
            return "위치 태그 업데이트에 실패했습니다"
        case .deletionFailed:
            return "위치 태그 삭제에 실패했습니다"
        }
    }
}
