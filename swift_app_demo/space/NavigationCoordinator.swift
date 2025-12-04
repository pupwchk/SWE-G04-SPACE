//
//  NavigationCoordinator.swift
//  space
//
//  Manages deep linking and navigation throughout the app
//

import SwiftUI
import Combine

/// Coordinates navigation throughout the app, especially from notifications
class NavigationCoordinator: ObservableObject {
    static let shared = NavigationCoordinator()

    // MARK: - Published Properties

    /// Current selected tab (0: Home, 1: Appliance, 2: Chat, 3: Menu)
    @Published var selectedTab: Int = 0

    /// Channel URL to navigate to when opening chat
    @Published var channelToOpen: String?

    /// Persona to open in chat view
    @Published var personaToOpen: Persona?

    // MARK: - Initialization

    private init() {
        setupNotificationObserver()
    }

    // MARK: - Notification Observer

    private func setupNotificationObserver() {
        // Listen for notification taps
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(handleOpenChatChannel(_:)),
            name: NSNotification.Name("OpenChatChannel"),
            object: nil
        )
    }

    @objc private func handleOpenChatChannel(_ notification: Notification) {
        guard let userInfo = notification.userInfo,
              let channelUrl = userInfo["channelUrl"] as? String else {
            print("⚠️ [NavigationCoordinator] No channel URL in notification")
            return
        }

        print("📱 [NavigationCoordinator] Handling navigation to channel: \(channelUrl)")

        // Get persona ID from channel data
        Task {
            await extractPersonaIdAndNavigate(channelUrl: channelUrl)
        }
    }

    /// Extract persona ID from channel and navigate
    @MainActor
    private func extractPersonaIdAndNavigate(channelUrl: String) async {
        do {
            // Get persona ID from channel data
            let personaId = try await SendbirdChatManager.shared.getPersonaIdFromChannel(channelUrl: channelUrl)
            print("📱 [NavigationCoordinator] Extracted persona ID from channel: \(personaId)")

            await loadAndNavigateToPersona(personaId: personaId, channelUrl: channelUrl)
        } catch {
            print("❌ [NavigationCoordinator] Failed to extract persona ID from channel: \(error)")
        }
    }

    // MARK: - Navigation Methods

    /// Navigate to a chat channel
    /// - Parameters:
    ///   - channelUrl: Sendbird channel URL
    ///   - personaId: Persona ID to open
    @MainActor
    func navigateToChannel(channelUrl: String, personaId: String) async {
        await loadAndNavigateToPersona(personaId: personaId, channelUrl: channelUrl)
    }

    /// Load persona details and navigate to chat
    @MainActor
    private func loadAndNavigateToPersona(personaId: String, channelUrl: String) async {
        do {
            // Fetch personas from Supabase
            let personas = try await SupabaseManager.shared.fetchPersonas()

            guard let persona = personas.first(where: { $0.id == personaId }) else {
                print("⚠️ [NavigationCoordinator] Persona not found: \(personaId)")
                print("   Available persona IDs: \(personas.map { $0.id })")
                return
            }

            print("✅ [NavigationCoordinator] Found persona: \(persona.nickname)")

            // Switch to chat tab first
            self.selectedTab = 2

            // Small delay to ensure tab switch completes
            try? await Task.sleep(nanoseconds: 100_000_000) // 0.1 second

            // Update navigation state on main thread
            self.channelToOpen = channelUrl
            self.personaToOpen = persona

            print("✅ [NavigationCoordinator] Navigation state updated - tab: \(self.selectedTab), persona: \(persona.nickname)")

        } catch {
            print("❌ [NavigationCoordinator] Failed to load persona: \(error)")
        }
    }

    /// Clear navigation state after navigation is complete
    @MainActor
    func clearNavigationState() {
        channelToOpen = nil
        personaToOpen = nil
        print("ℹ️ [NavigationCoordinator] Navigation state cleared")
    }

    deinit {
        NotificationCenter.default.removeObserver(self)
    }
}
