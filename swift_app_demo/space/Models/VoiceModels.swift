import Foundation

// MARK: - Voice Models

/// Text-to-speech request for `/api/voice/tts` POST and `/api/voice/tts-stream` POST
struct TTSRequest: Codable {
    let text: String
    let voice: String?  // Default: "alloy"
    let userId: String?

    enum CodingKeys: String, CodingKey {
        case text, voice
        case userId = "user_id"
    }
}

// Note: STT (Speech-to-Text) uploads use multipart/form-data
// Audio data should be sent as binary Data, not JSON
// Use URLRequest with multipart/form-data for `/api/voice/stt` POST
// and `/api/voice/conversation` POST
