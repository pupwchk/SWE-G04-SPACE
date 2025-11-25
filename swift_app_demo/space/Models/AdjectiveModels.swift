//
//  AdjectiveModels.swift
//  space
//
//  형용사 관련 데이터 모델

import Foundation

/// 형용사 데이터 모델
struct Adjective: Codable, Identifiable, Hashable {
    let id: String
    let adjectiveName: String
    let instructionText: String
    let category: String?
    let createdAt: String?
    let updatedAt: String?

    enum CodingKeys: String, CodingKey {
        case id
        case adjectiveName = "adjective_name"
        case instructionText = "instruction_text"
        case category
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

/// 페르소나 데이터 모델
struct Persona: Codable, Identifiable, Hashable {
    let id: String
    let userId: String
    let nickname: String
    let adjectiveIds: [String]
    let customInstructions: String?
    let finalPrompt: String?
    let createdAt: String?
    let updatedAt: String?

    enum CodingKeys: String, CodingKey {
        case id
        case userId = "user_id"
        case nickname
        case adjectiveIds = "adjective_ids"
        case customInstructions = "custom_instructions"
        case finalPrompt = "final_prompt"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

/// 활성 페르소나 데이터 모델
struct ActivePersona: Codable {
    let userId: String
    let personaId: String?
    let updatedAt: String?

    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case personaId = "persona_id"
        case updatedAt = "updated_at"
    }
}

/// 페르소나 생성/수정 요청 모델
struct PersonaRequest: Codable {
    let nickname: String
    let adjectiveIds: [String]
    let customInstructions: String?

    enum CodingKeys: String, CodingKey {
        case nickname
        case adjectiveIds = "adjective_ids"
        case customInstructions = "custom_instructions"
    }
}
