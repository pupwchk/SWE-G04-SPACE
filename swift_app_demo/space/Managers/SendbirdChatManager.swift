//
//  SendbirdChatManager.swift
//  space
//
//  Created for Sendbird channel management and messaging operations
//

import Foundation
import Combine
@preconcurrency import SendbirdChatSDK

// MARK: - Delegate Protocol

/// Delegate protocol for receiving Sendbird chat events
protocol SendbirdChatDelegate: AnyObject {
    func didReceiveMessage(_ message: ChatMessage, channelUrl: String)
    func didUpdateChannel(_ channelUrl: String)
    func didReceiveError(_ error: Error)
}

// MARK: - Chat Manager

/// Manager for Sendbird chat operations
/// Handles channel creation, message sending/receiving, and delegate notifications
class SendbirdChatManager: ObservableObject {
    static let shared = SendbirdChatManager()

    // MARK: - Properties

    weak var delegate: SendbirdChatDelegate?

    @Published var activeChannels: [String: GroupChannel] = [:]
    @Published var isLoading = false

    private var cancellables = Set<AnyCancellable>()

    // MARK: - Initialization

    private init() {
        // Private initializer for singleton pattern
        setupDelegates()
    }

    /// Setup Sendbird channel delegates
    private func setupDelegates() {
        SendbirdChat.addChannelDelegate(
            self,
            identifier: "ChatManager"
        )
        print("✅ [SendbirdChatManager] Channel delegate registered")
    }

    // MARK: - Channel Operations

    /// Create or get existing channel with AI assistant
    /// - Parameters:
    ///   - userId: Current user ID from Supabase
    ///   - personaId: Selected persona ID
    /// - Returns: Channel URL for the created/retrieved channel
    func getOrCreateChannel(userId: String, personaId: String) async throws -> String {
        // ✅ Step 1: Check if we have a saved channel URL in Supabase
        do {
            if let savedChannelUrl = try await SupabaseManager.shared.getPersonaChannelUrl(personaId: personaId) {
                print("📦 [SendbirdChatManager] Found saved channel URL in DB: \(savedChannelUrl)")

                // Try to get the channel with the saved URL
                do {
                    let channel = try await getChannel(channelUrl: savedChannelUrl)
                    print("✅ [SendbirdChatManager] Successfully retrieved channel from saved URL")
                    return channel.channelURL
                } catch {
                    print("⚠️ [SendbirdChatManager] Saved channel URL is invalid, will create new channel: \(error)")
                    // Channel doesn't exist anymore, fall through to create new one
                }
            } else {
                print("ℹ️ [SendbirdChatManager] No saved channel URL found, will create new channel")
            }
        } catch {
            print("⚠️ [SendbirdChatManager] Failed to fetch saved channel URL: \(error)")
            // Continue to create new channel
        }

        // ✅ Step 2: Create new channel with custom data to distinguish personas
        let params = GroupChannelCreateParams()
        params.name = "AI Chat with Persona \(personaId)"
        params.coverURL = ""
        params.isDistinct = false  // ✅ Don't reuse channels based on members
        params.userIds = [userId, SendbirdManager.shared.getAIUserId()]
        // ✅ Use customType to store persona ID for channel identification
        params.customType = "persona_\(personaId)"
        params.data = "{\"persona_id\":\"\(personaId)\"}"

        let channelUrl: String = try await withCheckedThrowingContinuation { continuation in
            GroupChannel.createChannel(params: params) { [weak self] channel, error in
                if let error = error {
                    print("❌ [SendbirdChatManager] Channel creation failed: \(error)")
                    continuation.resume(throwing: SendbirdChatError.channelCreationFailed)
                } else if let channel = channel {
                    print("✅ [SendbirdChatManager] Channel created: \(channel.channelURL)")
                    print("   Custom Type: \(channel.customType ?? "none")")
                    print("   Data: \(channel.data ?? "none")")

                    Task { @MainActor in
                        self?.activeChannels[channel.channelURL] = channel
                    }

                    continuation.resume(returning: channel.channelURL)
                }
            }
        }

        // ✅ Step 3: Save the real Sendbird channel URL to Supabase for future use
        do {
            try await SupabaseManager.shared.savePersonaChannelUrl(personaId: personaId, channelUrl: channelUrl)
            print("💾 [SendbirdChatManager] Saved channel URL to database")
        } catch {
            print("⚠️ [SendbirdChatManager] Failed to save channel URL to database: \(error)")
            // Non-critical error, channel still works even if we couldn't save
        }

        return channelUrl
    }

    /// Get existing channel by URL
    /// - Parameter channelUrl: The channel URL
    /// - Returns: Channel object
    func getChannel(channelUrl: String) async throws -> GroupChannel {
        // Check cache first
        if let channel = activeChannels[channelUrl] {
            return channel
        }

        // Fetch from Sendbird
        return try await withCheckedThrowingContinuation { continuation in
            GroupChannel.getChannel(url: channelUrl) { [weak self] channel, error in
                if let error = error {
                    print("❌ [SendbirdChatManager] Failed to get channel: \(error)")
                    continuation.resume(throwing: error)
                } else if let channel = channel {
                    Task { @MainActor in
                        self?.activeChannels[channelUrl] = channel
                    }
                    continuation.resume(returning: channel)
                }
            }
        }
    }

    // MARK: - Message Operations

    /// Send text message to channel
    /// - Parameters:
    ///   - channelUrl: Target channel URL
    ///   - text: Message text
    ///   - personaContext: Persona's final prompt for AI context
    /// - Returns: Sent message object
    func sendMessage(
        channelUrl: String,
        text: String,
        personaContext: String? = nil
    ) async throws -> ChatMessage {
        // Get channel first
        let channel = try await getChannel(channelUrl: channelUrl)

        let params = UserMessageCreateParams(message: text)

        // Add persona context as metadata for backend webhook
        if let context = personaContext {
            params.data = "{\"persona_context\":\"\(context)\"}"
        }

        return try await withCheckedThrowingContinuation { continuation in
            channel.sendUserMessage(params: params) { message, error in
                if let error = error {
                    print("❌ [SendbirdChatManager] Message send failed: \(error)")
                    continuation.resume(throwing: SendbirdChatError.messageSendFailed)
                } else if let message = message {
                    print("✅ [SendbirdChatManager] Message sent: \(message.messageId)")

                    let chatMessage = ChatMessage(
                        id: String(message.messageId),
                        text: message.message,
                        isFromUser: message.sender?.userId != SendbirdManager.shared.getAIUserId(),
                        timestamp: Date(timeIntervalSince1970: TimeInterval(message.createdAt) / 1000)
                    )

                    continuation.resume(returning: chatMessage)
                }
            }
        }
    }

    /// Send message with retry logic for network failures
    func sendMessageWithRetry(
        channelUrl: String,
        text: String,
        personaContext: String? = nil,
        maxRetries: Int = 3
    ) async throws -> ChatMessage {
        var lastError: Error?

        for attempt in 1...maxRetries {
            do {
                return try await sendMessage(
                    channelUrl: channelUrl,
                    text: text,
                    personaContext: personaContext
                )
            } catch {
                lastError = error
                print("⚠️ [SendbirdChatManager] Retry \(attempt)/\(maxRetries) failed: \(error)")

                if attempt < maxRetries {
                    // Exponential backoff
                    let delay = UInt64(attempt * 1_000_000_000) // 1s, 2s, 3s
                    try await Task.sleep(nanoseconds: delay)
                }
            }
        }

        throw lastError ?? SendbirdChatError.messageSendFailed
    }

    /// Load message history from channel
    /// - Parameters:
    ///   - channelUrl: Channel URL
    ///   - limit: Number of messages to load
    ///   - timestamp: Timestamp to load messages before (for pagination)
    /// - Returns: Array of chat messages
    func loadMessages(
        channelUrl: String,
        limit: Int = 50,
        timestamp: Int64? = nil
    ) async throws -> [ChatMessage] {
        let channel = try await getChannel(channelUrl: channelUrl)

        let params = MessageListParams()
        params.previousResultSize = limit
        params.reverse = false
        params.includeReactions = false

        return try await withCheckedThrowingContinuation { continuation in
            channel.getMessagesByTimestamp(
                timestamp ?? Int64(Date().timeIntervalSince1970 * 1000),
                params: params
            ) { messages, error in
                if let error = error {
                    print("❌ [SendbirdChatManager] Failed to load messages: \(error)")
                    continuation.resume(throwing: error)
                } else if let messages = messages {
                    print("✅ [SendbirdChatManager] Loaded \(messages.count) messages")

                    let chatMessages = messages.compactMap { message -> ChatMessage? in
                        guard let userMessage = message as? UserMessage else { return nil }

                        return ChatMessage(
                            id: String(userMessage.messageId),
                            text: userMessage.message,
                            isFromUser: userMessage.sender?.userId != SendbirdManager.shared.getAIUserId(),
                            timestamp: Date(timeIntervalSince1970: TimeInterval(userMessage.createdAt) / 1000)
                        )
                    }

                    continuation.resume(returning: chatMessages)
                }
            }
        }
    }

    /// Mark messages as read in channel
    /// - Parameter channelUrl: Channel URL
    func markAsRead(channelUrl: String) async {
        do {
            let channel = try await getChannel(channelUrl: channelUrl)
            channel.markAsRead { error in
                if let error = error {
                    print("❌ [SendbirdChatManager] Failed to mark as read: \(error)")
                } else {
                    print("✅ [SendbirdChatManager] Marked as read: \(channelUrl)")
                }
            }
        } catch {
            print("❌ [SendbirdChatManager] Failed to get channel for mark as read: \(error)")
        }
    }

    /// Leave a channel
    /// - Parameter channelUrl: Channel URL to leave
    func leaveChannel(channelUrl: String) async throws {
        // NOTE: Will be implemented once SDK is installed
        print("ℹ️ [SendbirdChatManager] Simulating channel leave: \(channelUrl)")

        _ = await MainActor.run {
            activeChannels.removeValue(forKey: channelUrl)
        }
    }
}

// MARK: - Sendbird Channel Delegate

extension SendbirdChatManager: GroupChannelDelegate {
    nonisolated func channel(_ channel: BaseChannel, didReceive message: BaseMessage) {
        guard let userMessage = message as? UserMessage else { return }

        let chatMessage = ChatMessage(
            id: String(userMessage.messageId),
            text: userMessage.message,
            isFromUser: userMessage.sender?.userId != SendbirdManager.shared.getAIUserId(),
            timestamp: Date(timeIntervalSince1970: TimeInterval(userMessage.createdAt) / 1000)
        )

        print("✅ [SendbirdChatManager] Received message: \(chatMessage.text)")

        // Notify delegate
        Task { @MainActor in
            self.delegate?.didReceiveMessage(chatMessage, channelUrl: channel.channelURL)
        }
    }

    nonisolated func channel(_ channel: BaseChannel, didUpdate message: BaseMessage) {
        print("ℹ️ [SendbirdChatManager] Message updated in channel: \(channel.channelURL)")

        Task { @MainActor in
            self.delegate?.didUpdateChannel(channel.channelURL)
        }
    }

    nonisolated func channel(_ channel: BaseChannel, messageWasDeleted messageId: Int64) {
        print("ℹ️ [SendbirdChatManager] Message deleted: \(messageId) in channel: \(channel.channelURL)")
    }
}

// MARK: - Error Types

enum SendbirdChatError: LocalizedError {
    case channelCreationFailed
    case channelNotFound
    case messageSendFailed
    case messageLoadFailed

    var errorDescription: String? {
        switch self {
        case .channelCreationFailed:
            return "채팅방 생성에 실패했습니다."
        case .channelNotFound:
            return "채팅방을 찾을 수 없습니다."
        case .messageSendFailed:
            return "메시지 전송에 실패했습니다."
        case .messageLoadFailed:
            return "메시지 로드에 실패했습니다."
        }
    }
}
