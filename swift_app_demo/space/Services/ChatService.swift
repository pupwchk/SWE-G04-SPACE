//
//  ChatService.swift
//  space
//
//  Created for business logic layer between UI and Sendbird/FastAPI
//

import Foundation
import Combine

/// Service layer for chat operations
/// Bridges UI (PersonaChatView) with Sendbird and FastAPI backend
class ChatService: ObservableObject {
    static let shared = ChatService()

    // MARK: - Dependencies

    private let sendbirdManager = SendbirdManager.shared
    private let chatManager = SendbirdChatManager.shared
    private let fastAPIService = FastAPIService.shared
    private let supabaseManager = SupabaseManager.shared

    // MARK: - Published Properties

    @Published var isProcessing = false
    @Published var lastError: Error?

    // MARK: - Initialization

    private init() {
        // Private initializer for singleton pattern
    }

    // MARK: - Chat Operations

    /// Send message to AI assistant via Sendbird
    /// - Parameters:
    ///   - text: User's message text
    ///   - personaId: Selected persona ID
    ///   - personaContext: Persona's final prompt for AI context
    /// - Returns: Sent message object
    func sendMessage(
        text: String,
        personaId: String,
        personaContext: String
    ) async throws -> ChatMessage {
        guard let userId = supabaseManager.currentUser?.id else {
            throw ChatServiceError.userNotAuthenticated
        }

        // Ensure Sendbird is connected
        if !sendbirdManager.isConnected {
            try await sendbirdManager.connect(userId: userId)
        }

        // Get or create channel
        let channelUrl = try await chatManager.getOrCreateChannel(
            userId: userId,
            personaId: personaId
        )

        // Send message via Sendbird with retry logic
        let message = try await chatManager.sendMessageWithRetry(
            channelUrl: channelUrl,
            text: text,
            personaContext: personaContext
        )

        print("✅ [ChatService] Message sent successfully")
        return message
    }

    /// Load conversation history for a persona
    /// - Parameters:
    ///   - personaId: Persona ID
    ///   - limit: Number of messages to load
    /// - Returns: Array of chat messages
    func loadHistory(
        personaId: String,
        limit: Int = 50
    ) async throws -> [ChatMessage] {
        guard let userId = supabaseManager.currentUser?.id else {
            throw ChatServiceError.userNotAuthenticated
        }

        // First try to load from FastAPI backend for persistence
        if let backendHistory = await loadHistoryFromBackend(userId: userId, limit: limit) {
            return backendHistory
        }

        // Fallback to Sendbird history
        do {
            // ✅ Get or create channel and use the REAL channel URL returned
            // This ensures we always use the correct Sendbird channel URL, not a custom one
            let channelUrl = try await chatManager.getOrCreateChannel(userId: userId, personaId: personaId)

            let messages = try await chatManager.loadMessages(
                channelUrl: channelUrl,  // ✅ Use real channel URL, not custom URL
                limit: limit
            )

            print("✅ [ChatService] Loaded \(messages.count) messages from Sendbird")
            return messages
        } catch {
            print("⚠️ [ChatService] Failed to load Sendbird history: \(error)")
            // Return empty array instead of throwing - first conversation will be empty
            return []
        }
    }

    /// Load conversation history from FastAPI backend
    /// - Parameters:
    ///   - userId: Current user ID
    ///   - limit: Number of messages to load
    /// - Returns: Array of chat messages or nil if failed
    private func loadHistoryFromBackend(userId: String, limit: Int) async -> [ChatMessage]? {
        print("📥 [ChatService] Attempting to load history from backend...")

        guard let historyItems = await fastAPIService.getChatHistory(
            userId: userId,
            limit: limit
        ) else {
            print("⚠️ [ChatService] Failed to load history from backend, will fallback to Sendbird")
            return nil
        }

        let messages = historyItems.map { item -> ChatMessage in
            // Parse timestamp (ISO8601 format expected)
            let timestamp: Date
            if let timestampStr = item.timestamp,
               let date = ISO8601DateFormatter().date(from: timestampStr) {
                timestamp = date
            } else {
                timestamp = Date()
            }

            // Generate unique ID from timestamp and role
            let messageId = "\(item.role)_\(timestamp.timeIntervalSince1970)"

            return ChatMessage(
                id: messageId,
                text: item.message,
                isFromUser: item.role == "user",
                timestamp: timestamp
            )
        }

        print("✅ [ChatService] Loaded \(messages.count) messages from backend")
        return messages
    }

    /// Parse appliance changes from AI message
    /// - Parameter message: Chat message to parse
    /// - Returns: Array of appliance changes
    func parseApplianceChanges(from message: ChatMessage) -> [ApplianceChange] {
        // Check if message has appliance suggestion metadata
        guard message.customType == "appliance_suggestion",
              let dataString = message.data else {
            print("ℹ️ [ChatService] No appliance suggestions in message")
            return []
        }

        do {
            // Parse JSON metadata
            guard let jsonData = dataString.data(using: .utf8) else {
                print("❌ [ChatService] Failed to convert data string to Data")
                return []
            }

            let metadata = try JSONDecoder().decode(MessageMetadata.self, from: jsonData)

            print("✅ [ChatService] Parsed metadata with \(metadata.applianceSuggestions.count) appliance suggestions")

            // Convert to ApplianceChange objects
            let changes = metadata.applianceSuggestions.map { suggestion -> ApplianceChange in
                ApplianceChange(
                    applianceName: suggestion.applianceType,
                    icon: iconForAppliance(suggestion.applianceType),
                    action: suggestion.action,
                    detail: detailForSettings(suggestion.settings),
                    isModified: false
                )
            }

            print("✅ [ChatService] Converted to \(changes.count) ApplianceChange objects")
            return changes

        } catch {
            print("❌ [ChatService] Failed to parse appliance metadata: \(error)")
            return []
        }
    }

    /// Approve appliance changes via backend
    /// - Parameters:
    ///   - userId: Current user ID
    ///   - changes: Array of appliance changes to approve
    ///   - userResponse: User's approval message (e.g., "좋아", "에어컨은 24도로")
    ///   - metadata: Original message metadata containing suggestions
    /// - Returns: Success status
    func approveChanges(userId: String, changes: [ApplianceChange], userResponse: String = "좋아", metadata: MessageMetadata?) async throws -> Bool {
        print("📤 [ChatService] Approving appliance changes for user: \(userId)")
        print("   Changes: \(changes.count) appliances")
        print("   User response: \(userResponse)")

        guard let metadata = metadata else {
            print("❌ [ChatService] No metadata available for approval")
            throw ChatServiceError.parseError
        }

        // Convert ApplianceSuggestion to original_plan format
        let recommendations = metadata.applianceSuggestions.map { suggestion -> [String: Any] in
            var dict: [String: Any] = [
                "appliance_type": suggestion.applianceType,
                "action": suggestion.action
            ]

            // Add settings if available
            if let settings = suggestion.settings {
                var settingsDict: [String: Any] = [:]
                for (key, value) in settings {
                    settingsDict[key] = value.value
                }
                dict["settings"] = settingsDict
            }

            return dict
        }

        let originalPlan: [String: Any] = [
            "recommendations": recommendations
        ]

        // Call FastAPI approval endpoint
        guard let response = await fastAPIService.approveChatChanges(
            userId: userId,
            userResponse: userResponse,
            originalPlan: originalPlan
        ) else {
            print("❌ [ChatService] Failed to approve appliance changes")
            return false
        }

        print("✅ [ChatService] Appliance changes approved")
        print("   Approved: \(response.approved)")
        print("   Has modification: \(response.hasModification)")
        print("   AI response: \(response.aiResponse)")

        return response.approved
    }

    /// Clear chat session
    /// - Parameter userId: Current user ID
    func clearSession(userId: String) async throws {
        // NOTE: Will be implemented when FastAPI session endpoint is added

        /*
        let success = await fastAPIService.clearChatSession(userId: userId)

        if success {
            print("✅ [ChatService] Session cleared")
        } else {
            throw ChatServiceError.sessionClearFailed
        }
        */

        print("ℹ️ [ChatService] Simulating session clear for user: \(userId)")
        try await Task.sleep(nanoseconds: 500_000_000)
        print("✅ [ChatService] Simulated session cleared")
    }

    // MARK: - Helper Methods

    /// Get icon name for appliance type
    private func iconForAppliance(_ type: String) -> String {
        switch type.lowercased() {
        case "에어컨", "airconditioner":
            return "air.conditioner.horizontal"
        case "조명", "light":
            return "lightbulb"
        case "공기청정기", "airpurifier":
            return "wind"
        case "가습기", "humidifier":
            return "humidity"
        case "제습기", "dehumidifier":
            return "humidity.fill"
        case "tv", "television":
            return "tv"
        default:
            return "powerplug"
        }
    }

    /// Generate detail string from settings
    private func detailForSettings(_ settings: [String: Any]?) -> String? {
        guard let settings = settings else { return nil }

        var details: [String] = []

        if let temp = settings["temperature"] as? Int {
            details.append("\(temp)°C")
        }

        if let brightness = settings["brightness"] as? Int {
            details.append("\(brightness)% 밝기")
        }

        if let fanSpeed = settings["fan_speed"] as? Int {
            details.append("바람 세기 \(fanSpeed)")
        }

        return details.isEmpty ? nil : details.joined(separator: ", ")
    }
}

// MARK: - Error Types

enum ChatServiceError: LocalizedError {
    case userNotAuthenticated
    case channelCreationFailed
    case messageSendFailed
    case historyLoadFailed
    case sessionClearFailed
    case parseError

    var errorDescription: String? {
        switch self {
        case .userNotAuthenticated:
            return "사용자 인증이 필요합니다."
        case .channelCreationFailed:
            return "채팅방 생성에 실패했습니다."
        case .messageSendFailed:
            return "메시지 전송에 실패했습니다."
        case .historyLoadFailed:
            return "대화 기록 로드에 실패했습니다."
        case .sessionClearFailed:
            return "세션 초기화에 실패했습니다."
        case .parseError:
            return "응답 처리 중 오류가 발생했습니다."
        }
    }
}

// MARK: - Data Models

/// Extended ChatMessage model for metadata support
extension ChatMessage {
    /// Metadata for additional message information
    struct Metadata: Codable {
        let personaId: String?
        let applianceSuggestions: [ApplianceSuggestion]?
    }
}

/// Message metadata model from Sendbird
struct MessageMetadata: Codable {
    let applianceSuggestions: [ApplianceSuggestion]
    let weather: WeatherInfo?
    let fatigueLevel: Int?

    enum CodingKeys: String, CodingKey {
        case applianceSuggestions = "appliance_suggestions"
        case weather
        case fatigueLevel = "fatigue_level"
    }
}

/// Weather info from metadata
struct WeatherInfo: Codable {
    let temperature: Double?
    let humidity: Double?
    let pm10: Double?
}

/// Appliance suggestion model from backend
struct ApplianceSuggestion: Codable {
    let applianceType: String
    let action: String
    let settings: [String: AnyCodable]?

    enum CodingKeys: String, CodingKey {
        case applianceType = "appliance_type"
        case action
        case settings
    }
}

/// Helper for encoding/decoding Any values in Codable
struct AnyCodable: Codable {
    let value: Any

    init(_ value: Any) {
        self.value = value
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.singleValueContainer()

        if let intValue = try? container.decode(Int.self) {
            value = intValue
        } else if let doubleValue = try? container.decode(Double.self) {
            value = doubleValue
        } else if let stringValue = try? container.decode(String.self) {
            value = stringValue
        } else if let boolValue = try? container.decode(Bool.self) {
            value = boolValue
        } else {
            value = ""
        }
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.singleValueContainer()

        if let intValue = value as? Int {
            try container.encode(intValue)
        } else if let doubleValue = value as? Double {
            try container.encode(doubleValue)
        } else if let stringValue = value as? String {
            try container.encode(stringValue)
        } else if let boolValue = value as? Bool {
            try container.encode(boolValue)
        }
    }
}
