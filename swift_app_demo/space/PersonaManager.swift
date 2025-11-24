//
//  PersonaManager.swift
//  space
//
//  Created by 임동현 on 11/6/25.
//

import Foundation

/// Manager for storing and retrieving persona test results
/// ⚠️ DEPRECATED: This is a legacy manager using UserDefaults.
/// Consider migrating to Supabase-based Persona system (PersonaRepository, SupabaseManager)
/// Currently used by PersonalTestView for persona test results.
class PersonaManager: ObservableObject {
    static let shared = PersonaManager()

    @Published var selectedPersonas: Set<String> = []

    private let userDefaults = UserDefaults.standard
    private let personasKey = "savedPersonas"

    init() {
        loadPersonas()
    }

    // MARK: - Public Methods

    /// Save personas to UserDefaults
    func savePersonas(_ personas: Set<String>) {
        selectedPersonas = personas
        let personasArray = Array(personas)
        userDefaults.set(personasArray, forKey: personasKey)
        userDefaults.synchronize()
    }

    /// Add a single persona
    func addPersona(_ persona: String) {
        selectedPersonas.insert(persona)
        savePersonas(selectedPersonas)
    }

    /// Remove a single persona
    func removePersona(_ persona: String) {
        selectedPersonas.remove(persona)
        savePersonas(selectedPersonas)
    }

    /// Load personas from UserDefaults
    func loadPersonas() {
        if let personasArray = userDefaults.array(forKey: personasKey) as? [String] {
            selectedPersonas = Set(personasArray)
        }
    }

    /// Clear all personas
    func clearPersonas() {
        selectedPersonas = []
        userDefaults.removeObject(forKey: personasKey)
        userDefaults.synchronize()
    }

    /// Generate persona based on test answers
    func generatePersona(from answers: [Int?]) -> String {
        // Simple logic to determine persona based on answers
        // This is a placeholder - you can implement more sophisticated logic

        guard answers.count >= 8,
              let q1 = answers[0], // Energy time: 아침/점심/저녁
              let q4 = answers[3], // Morning/Night person
              let q6 = answers[5]  // Timeline
        else {
            return "Developer" // Default
        }

        // Morning person + 운동 타임라인 = "Running"
        if q1 == 0 && q4 == 0 && (q6 == 0 || q6 == 1) {
            return "Running"
        }

        // 저녁형 + 웹툰/게임 취미 = "Webtoon"
        if q1 == 2 && q4 == 2 {
            return "Webtoon"
        }

        // 스트레스 민감 = "Stress"
        if let q3 = answers[2], q3 == 2 {
            return "Stress"
        }

        // 아침형 = "School"
        if q4 == 0 {
            return "School"
        }

        // 밤형 = "Developer"
        if q4 == 2 {
            return "Developer"
        }

        // 수면 많이 = "Sleep"
        if let q5 = answers[4], q5 == 2 {
            return "Sleep"
        }

        // 산책 타임라인 = "Walking"
        if q6 == 1 {
            return "Walking"
        }

        // 카페 타임라인 = "home"
        if q6 == 2 {
            return "home"
        }

        // Default
        return "Developer"
    }
}
