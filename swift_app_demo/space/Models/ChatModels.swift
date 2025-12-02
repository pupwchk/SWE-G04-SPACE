import Foundation

// MARK: - Chat Request Models

/// Chat message request for `/api/chat/{user_id}/message` POST
struct ChatMessageRequest: Codable {
    let message: String
    let context: [String: AnyCodableValue]?
    let characterId: String?

    enum CodingKeys: String, CodingKey {
        case message, context
        case characterId = "character_id"
    }
}

/// Appliance approval request for `/api/chat/{user_id}/approve` POST
struct ApplianceApprovalRequest: Codable {
    let userResponse: String
    let originalPlan: [String: Any]
    let sessionId: String?

    enum CodingKeys: String, CodingKey {
        case userResponse = "user_response"
        case originalPlan = "original_plan"
        case sessionId = "session_id"
    }

    func encode(to encoder: Encoder) throws {
        var container = encoder.container(keyedBy: CodingKeys.self)
        try container.encode(userResponse, forKey: .userResponse)
        // Convert originalPlan to AnyCodableValue for encoding
        let codablePlan = originalPlan.mapValues { AnyCodableValue($0) }
        try container.encode(codablePlan, forKey: .originalPlan)
        try container.encodeIfPresent(sessionId, forKey: .sessionId)
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        userResponse = try container.decode(String.self, forKey: .userResponse)
        let codablePlan = try container.decode([String: AnyCodableValue].self, forKey: .originalPlan)
        originalPlan = codablePlan.mapValues { $0.value }
        sessionId = try container.decodeIfPresent(String.self, forKey: .sessionId)
    }

    init(userResponse: String, originalPlan: [String: Any], sessionId: String? = nil) {
        self.userResponse = userResponse
        self.originalPlan = originalPlan
        self.sessionId = sessionId
    }
}

// MARK: - Chat Response Models

/// Chat message response from `/api/chat/{user_id}/message` POST
struct ChatMessageResponse: Codable {
    let userMessage: String
    let aiResponse: String
    let intentType: String
    let needsControl: Bool
    let suggestions: [[String: AnyCodableValue]]?
    let sessionId: String?

    enum CodingKeys: String, CodingKey {
        case userMessage = "user_message"
        case aiResponse = "ai_response"
        case intentType = "intent_type"
        case needsControl = "needs_control"
        case suggestions
        case sessionId = "session_id"
    }
}

/// Appliance suggestion from AI
struct ApplianceSuggestionResponse: Codable {
    let applianceType: String
    let action: String
    let settings: [String: AnyCodableValue]?

    enum CodingKeys: String, CodingKey {
        case applianceType = "appliance_type"
        case action
        case settings
    }
}

/// Response from approve endpoint `/api/chat/{user_id}/approve` POST
struct ApplianceApprovalResponse: Codable {
    let approved: Bool
    let hasModification: Bool
    let modifications: [String: AnyCodableValue]?
    let executionResults: [[String: AnyCodableValue]]?
    let aiResponse: String

    enum CodingKeys: String, CodingKey {
        case approved
        case hasModification = "has_modification"
        case modifications
        case executionResults = "execution_results"
        case aiResponse = "ai_response"
    }

    // Computed properties for backward compatibility
    var status: String {
        return approved ? "success" : "failed"
    }

    var message: String {
        return aiResponse
    }

    var results: [[String: AnyCodableValue]]? {
        return executionResults
    }
}

/// Result of appliance control operation
struct ApplianceControlResult: Codable {
    let applianceType: String
    let success: Bool
    let message: String?

    enum CodingKeys: String, CodingKey {
        case applianceType = "appliance_type"
        case success
        case message
    }
}

/// Chat history response from `/api/chat/{user_id}/history` GET
struct ChatHistoryResponse: Codable {
    let userId: String
    let sessionId: String
    let conversationHistory: [ChatHistoryItem]

    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case sessionId = "session_id"
        case conversationHistory = "conversation_history"
    }
}

/// Individual chat history item
struct ChatHistoryItem: Codable {
    let role: String  // "user" or "assistant"
    let message: String
    let intent: [String: AnyCodableValue]?
    let suggestions: [ApplianceSuggestionResponse]?
    let timestamp: String?
}

// MARK: - Helper for Any Values

/// Helper for decoding/encoding Any values in JSON (e.g., settings, suggestions)
struct AnyCodableValue: Codable {
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
        } else if let arrayValue = try? container.decode([AnyCodableValue].self) {
            value = arrayValue.map { $0.value }
        } else if let dictValue = try? container.decode([String: AnyCodableValue].self) {
            value = dictValue.mapValues { $0.value }
        } else {
            value = NSNull()
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
        } else if let arrayValue = value as? [Any] {
            let codableArray = arrayValue.map { AnyCodableValue($0) }
            try container.encode(codableArray)
        } else if let dictValue = value as? [String: Any] {
            let codableDict = dictValue.mapValues { AnyCodableValue($0) }
            try container.encode(codableDict)
        } else {
            try container.encodeNil()
        }
    }
}
