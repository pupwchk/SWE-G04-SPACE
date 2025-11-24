//
//  PersonaRepository.swift
//  space
//
//  Repository pattern for Persona operations
//  Clean separation between data access and business logic

import Foundation

/// Persona Repository Protocol
protocol PersonaRepositoryProtocol {
    func fetchAdjectives() async throws -> [Adjective]
    func fetchPersonas(userId: String) async throws -> [Persona]
    func createPersona(_ request: CreatePersonaRequest) async throws -> Persona
    func updatePersona(id: String, _ request: UpdatePersonaRequest) async throws
    func deletePersona(id: String) async throws
    func fetchActivePersona(userId: String) async throws -> String?
    func setActivePersona(userId: String, personaId: String?) async throws
}

/// Create Persona Request DTO
struct CreatePersonaRequest: Encodable {
    let userId: String
    let nickname: String
    let adjectiveIds: [String]
    let customInstructions: String?
    let finalPrompt: String

    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case nickname
        case adjectiveIds = "adjective_ids"
        case customInstructions = "custom_instructions"
        case finalPrompt = "final_prompt"
    }
}

/// Update Persona Request DTO
struct UpdatePersonaRequest: Encodable {
    let nickname: String
    let adjectiveIds: [String]
    let customInstructions: String?
    let finalPrompt: String

    enum CodingKeys: String, CodingKey {
        case nickname
        case adjectiveIds = "adjective_ids"
        case customInstructions = "custom_instructions"
        case finalPrompt = "final_prompt"
    }
}

/// Set Active Persona Request DTO
struct SetActivePersonaRequest: Encodable {
    let userId: String
    let personaId: String?

    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case personaId = "persona_id"
    }
}

/// Persona Repository Implementation
class PersonaRepository: PersonaRepositoryProtocol {
    private let service: SupabaseService

    init(service: SupabaseService) {
        self.service = service
    }

    // MARK: - Adjectives

    func fetchAdjectives() async throws -> [Adjective] {
        return try await service.query(
            table: "adjectives",
            select: "*",
            filter: nil
        )
    }

    // MARK: - Personas

    func fetchPersonas(userId: String) async throws -> [Persona] {
        return try await service.query(
            table: "personas",
            select: "*",
            filter: "user_id=eq.\(userId)&order=created_at.desc"
        )
    }

    func createPersona(_ request: CreatePersonaRequest) async throws -> Persona {
        let data = try await service.insert(table: "personas", data: request)
        let decoder = JSONDecoder()
        // Note: Not using convertFromSnakeCase because Persona has explicit CodingKeys
        let personas = try decoder.decode([Persona].self, from: data)

        guard let persona = personas.first else {
            throw SupabaseError.queryFailed(statusCode: 500)
        }

        return persona
    }

    func updatePersona(id: String, _ request: UpdatePersonaRequest) async throws {
        try await service.update(
            table: "personas",
            filter: "id=eq.\(id)",
            data: request
        )
    }

    func deletePersona(id: String) async throws {
        try await service.delete(
            table: "personas",
            filter: "id=eq.\(id)"
        )
    }

    // MARK: - Active Persona

    func fetchActivePersona(userId: String) async throws -> String? {
        struct ActivePersonaResponse: Decodable {
            let personaId: String?
        }

        let results: [ActivePersonaResponse] = try await service.query(
            table: "user_active_persona",
            select: "persona_id",
            filter: "user_id=eq.\(userId)"
        )

        return results.first?.personaId
    }

    func setActivePersona(userId: String, personaId: String?) async throws {
        // Use upsert approach with Prefer header
        let request = SetActivePersonaRequest(userId: userId, personaId: personaId)

        // First try to delete existing
        try? await service.delete(
            table: "user_active_persona",
            filter: "user_id=eq.\(userId)"
        )

        // Then insert new
        _ = try await service.insert(table: "user_active_persona", data: request)
    }
}

// MARK: - Prompt Generation Helper

extension PersonaRepository {
    /// Generate final prompt from adjectives and custom instructions
    func generateFinalPrompt(
        adjectiveIds: [String],
        customInstructions: String?,
        adjectives: [Adjective]
    ) -> String {
        var promptParts: [String] = []

        // Filter selected adjectives
        let selectedAdjectives = adjectives.filter { adjectiveIds.contains($0.id) }

        // Add instruction texts
        for adjective in selectedAdjectives {
            promptParts.append(adjective.instructionText)
        }

        // Add custom instructions
        if let custom = customInstructions, !custom.isEmpty {
            promptParts.append(custom)
        }

        // Combine with line breaks
        return promptParts.joined(separator: "\n\n")
    }
}
