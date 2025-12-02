import Foundation

// MARK: - Character Models

/// Character (AI persona) response from `/api/characters/{character_id}` GET
struct Character: Codable, Identifiable {
    let id: String
    let userId: String
    let nickname: String
    let persona: String  // Persona prompt text describing character behavior

    enum CodingKeys: String, CodingKey {
        case id, nickname, persona
        case userId = "user_id"
    }
}

/// Character creation request for `/api/characters/` POST
struct CharacterCreate: Codable {
    let userId: String
    let nickname: String
    let persona: String

    enum CodingKeys: String, CodingKey {
        case nickname, persona
        case userId = "user_id"
    }
}

/// Character update request for `/api/characters/{character_id}` PATCH
struct CharacterUpdate: Codable {
    let nickname: String?
    let persona: String?
}
