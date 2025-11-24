//
//  ToneManager.swift
//  space
//
//  Created by 임동현 on 11/6/25.
//

import Foundation

/// Available speaking tones for chat and phone interactions
enum SpeakingTone: String, CaseIterable, Identifiable {
    case friendly = "친근한"
    case formal = "정중한"
    case cheerful = "밝은"
    case calm = "차분한"
    case professional = "전문적인"
    case warm = "따뜻한"
    case casual = "편안한"
    case energetic = "활기찬"

    var id: String { self.rawValue }

    var description: String {
        switch self {
        case .friendly:
            return "친근하고 편안한 말투"
        case .formal:
            return "예의 바르고 격식있는 말투"
        case .cheerful:
            return "명랑하고 긍정적인 말투"
        case .calm:
            return "차분하고 안정적인 말투"
        case .professional:
            return "전문적이고 정확한 말투"
        case .warm:
            return "따뜻하고 부드러운 말투"
        case .casual:
            return "자연스럽고 편한 말투"
        case .energetic:
            return "활기차고 역동적인 말투"
        }
    }
}

/// Manager for storing and retrieving selected speaking tones
class ToneManager: ObservableObject {
    static let shared = ToneManager()

    @Published var selectedTones: Set<String> = []

    private let userDefaults = UserDefaults.standard
    private let tonesKey = "savedTones"
    private let supabaseManager = SupabaseManager.shared

    init() {
        loadTones()
    }

    // MARK: - Public Methods

    /// Save tones (to both local and Supabase)
    func saveTones(_ tones: Set<String>) {
        selectedTones = tones

        // Save to UserDefaults for offline access
        let tonesArray = Array(tones)
        userDefaults.set(tonesArray, forKey: tonesKey)
        userDefaults.synchronize()

        // Save to Supabase
        Task {
            do {
                try await supabaseManager.saveUserTones(tones)
            } catch {
                print("❌ Failed to save tones to Supabase: \(error.localizedDescription)")
            }
        }
    }

    /// Add a single tone
    func addTone(_ tone: String) {
        selectedTones.insert(tone)
        saveTones(selectedTones)
    }

    /// Remove a single tone
    func removeTone(_ tone: String) {
        selectedTones.remove(tone)
        saveTones(selectedTones)
    }

    /// Toggle a tone (add if not present, remove if present)
    func toggleTone(_ tone: String) {
        if selectedTones.contains(tone) {
            removeTone(tone)
        } else {
            addTone(tone)
        }
    }

    /// Load tones from both UserDefaults and Supabase
    func loadTones() {
        // Load from UserDefaults first (for offline support)
        if let tonesArray = userDefaults.array(forKey: tonesKey) as? [String] {
            selectedTones = Set(tonesArray)
        }

        // Try to sync with Supabase
        Task {
            await syncWithSupabase()
        }
    }

    /// Sync tones with Supabase
    func syncWithSupabase() async {
        do {
            let tones = try await supabaseManager.fetchUserTones()
            await MainActor.run {
                selectedTones = Set(tones)
                // Update UserDefaults
                userDefaults.set(tones, forKey: tonesKey)
                userDefaults.synchronize()
            }
        } catch {
            print("❌ Failed to sync tones from Supabase: \(error.localizedDescription)")
            // Keep using local data if sync fails
        }
    }

    /// Clear all tones
    func clearTones() {
        selectedTones = []
        userDefaults.removeObject(forKey: tonesKey)
        userDefaults.synchronize()

        // Clear from Supabase
        Task {
            do {
                try await supabaseManager.saveUserTones([])
            } catch {
                print("❌ Failed to clear tones in Supabase: \(error.localizedDescription)")
            }
        }
    }

    /// Get random tone from selected tones
    func getRandomTone() -> String? {
        return selectedTones.randomElement()
    }
}
