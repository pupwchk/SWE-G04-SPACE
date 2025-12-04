//
//  SendbirdManager.swift
//  space
//
//  Created for Sendbird SDK initialization and user authentication
//

import Foundation
import Combine
@preconcurrency import SendbirdChatSDK

/// Manager for Sendbird SDK initialization and user connection
/// Handles both Chat and Calls SDK initialization
class SendbirdManager: ObservableObject {
    static let shared = SendbirdManager()

    // MARK: - Published Properties

    @Published var isConnected = false
    @Published var connectionError: Error?
    @Published var currentSendbirdUser: String?

    // MARK: - Constants

    private let appId = Config.sendbirdAppId
    private let aiUserId = Config.aiUserId

    // MARK: - Initialization

    private init() {
        // Private initializer for singleton pattern
    }

    // MARK: - SDK Initialization

    /// Initialize Sendbird Chat SDK
    /// Call this once in app's initialization (AppDelegate or App struct)
    func initializeChat() {
        let initParams = InitParams(
            applicationId: appId,
            isLocalCachingEnabled: true,
            logLevel: Config.debugLoggingEnabled ? .info : .none
        )

        SendbirdChat.initialize(params: initParams, completionHandler: { error in
            if let error = error {
                print("❌ [Sendbird] Chat SDK initialization failed: \(error)")
                Task { @MainActor in
                    self.connectionError = error
                }
            } else {
                print("✅ [Sendbird] Chat SDK initialized successfully")
                print("   App ID: \(self.appId)")
            }
        })
    }


    // MARK: - User Connection

    /// Connect user to Sendbird
    /// - Parameters:
    ///   - userId: User ID from Supabase authentication
    ///   - accessToken: Optional access token for authentication
    func connect(userId: String, accessToken: String? = nil) async throws {
        try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<Void, Error>) in
            SendbirdChat.connect(userId: userId, authToken: accessToken) { [weak self] user, error in
                if let error = error {
                    print("❌ [Sendbird] Connection failed: \(error)")
                    continuation.resume(throwing: error)
                } else if let user = user {
                    print("✅ [Sendbird] Connected as user: \(user.userId)")

                    Task { @MainActor in
                        self?.isConnected = true
                        self?.currentSendbirdUser = user.userId
                        self?.connectionError = nil
                    }

                    continuation.resume()
                }
            }
        }
    }

    /// Disconnect current user from Sendbird
    func disconnect() async {
        await withCheckedContinuation { (continuation: CheckedContinuation<Void, Never>) in
            SendbirdChat.disconnect { [weak self] in
                print("✅ [Sendbird] Disconnected successfully")

                Task { @MainActor in
                    self?.isConnected = false
                    self?.currentSendbirdUser = nil
                }

                continuation.resume()
            }
        }
    }


    // MARK: - Push Notifications

    /// Register device token for push notifications
    /// - Parameter deviceToken: Device token from APNs
    func registerPushToken(_ deviceToken: Data) {
        SendbirdChat.registerDevicePushToken(deviceToken, unique: true) { status, error in
            if let error = error {
                print("❌ [Sendbird] Failed to register push token: \(error)")
            } else {
                print("✅ [Sendbird] Push token registered successfully")
                print("   Status: \(status)")
            }
        }
    }

    /// Unregister device token for push notifications
    /// - Parameter deviceToken: Device token to unregister
    func unregisterPushToken(_ deviceToken: Data) {
        SendbirdChat.unregisterPushToken(deviceToken) { error in
            if let error = error {
                print("❌ [Sendbird] Failed to unregister push token: \(error)")
            } else {
                print("✅ [Sendbird] Push token unregistered successfully")
            }
        }
    }

    // MARK: - Helper Methods

    /// Check if Sendbird is properly initialized
    var isInitialized: Bool {
        return !appId.isEmpty
    }

    /// Get AI assistant user ID
    func getAIUserId() -> String {
        return aiUserId
    }
}

// MARK: - Error Types

enum SendbirdError: LocalizedError {
    case initializationFailed
    case connectionFailed
    case authenticationFailed
    case sdkNotInstalled

    var errorDescription: String? {
        switch self {
        case .initializationFailed:
            return "Sendbird 초기화에 실패했습니다."
        case .connectionFailed:
            return "서버에 연결할 수 없습니다."
        case .authenticationFailed:
            return "인증에 실패했습니다."
        case .sdkNotInstalled:
            return "Sendbird SDK가 설치되지 않았습니다. SPM을 통해 설치해주세요."
        }
    }
}
