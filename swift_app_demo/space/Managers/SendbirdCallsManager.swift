//
//  SendbirdCallsManager.swift
//  space
//
//  Created for Sendbird voice/video call handling
//

import Foundation
import AVFoundation
import Combine
import SendBirdCalls

// MARK: - Call State Enum

enum CallState {
    case idle
    case dialing
    case ringing
    case connecting
    case connected
    case ended
    case error
}

// MARK: - End Reason Enum

enum CallEndReason {
    case completed
    case canceled
    case declined
    case timeout
    case connectionFailed
    case unknown
}

// MARK: - Delegate Protocol

/// Delegate protocol for receiving Sendbird call events
protocol SendbirdCallsDelegate: AnyObject {
    func didReceiveIncomingCall(callId: String, callerId: String)
    func didCallConnect(callId: String)
    func didCallEnd(callId: String, reason: CallEndReason)
    func didCallError(callId: String, error: Error)
}

// MARK: - Calls Manager

/// Manager for Sendbird voice/video calls
/// Handles incoming calls, call states, and audio session management
class SendbirdCallsManager: NSObject, ObservableObject {
    static let shared = SendbirdCallsManager()

    // MARK: - Published Properties

    @Published var currentCallId: String?
    @Published var callState: CallState = .idle
    @Published var isMuted: Bool = false
    @Published var isSpeakerOn: Bool = false
    @Published var callDuration: TimeInterval = 0

    // MARK: - Properties

    weak var delegate: SendbirdCallsDelegate?

    private var currentCall: DirectCall?
    private var audioSession: AVAudioSession = .sharedInstance()
    private var durationTimer: Timer?
    private var cancellables = Set<AnyCancellable>()

    // MARK: - Initialization

    private override init() {
        super.init()
        setupAudioSession()
        setupCallDelegates()
    }

    /// Setup audio session for calls
    private func setupAudioSession() {
        do {
            try audioSession.setCategory(.playAndRecord, mode: .voiceChat, options: [.allowBluetooth, .defaultToSpeaker])
            try audioSession.setActive(false)
            print("✅ [SendbirdCallsManager] Audio session configured")
        } catch {
            print("❌ [SendbirdCallsManager] Audio session setup failed: \(error)")
        }
    }

    /// Setup Sendbird call delegates
    private func setupCallDelegates() {
        SendBirdCall.addDelegate(self, identifier: "CallsManager")
        print("✅ [SendbirdCallsManager] Call delegates registered")
    }

    /// Initialize SendBird Calls SDK
    /// - Parameters:
    ///   - appId: SendBird Application ID
    ///   - completion: Completion handler with success status
    func initializeSDK(appId: String, completion: @escaping (Bool) -> Void) {
        SendBirdCall.configure(appId: appId)
        print("✅ [SendbirdCallsManager] SDK initialized with App ID: \(appId)")
        completion(true)
    }

    /// Authenticate user with SendBird Calls
    /// - Parameters:
    ///   - userId: User ID to authenticate
    ///   - accessToken: Optional access token
    ///   - completion: Completion handler with authentication result
    func authenticate(userId: String, accessToken: String? = nil, completion: @escaping (Result<SendBirdCalls.User, Error>) -> Void) {
        let authParams = AuthenticateParams(userId: userId, accessToken: accessToken)

        SendBirdCall.authenticate(with: authParams) { user, error in
            if let error = error {
                print("❌ [SendbirdCallsManager] Authentication failed: \(error)")
                completion(.failure(error))
            } else if let user = user {
                print("✅ [SendbirdCallsManager] Authenticated as: \(user.userId)")
                completion(.success(user))
            }
        }
    }

    /// Register push token for incoming call notifications
    /// - Parameters:
    ///   - token: APNS device token
    ///   - isProduction: Whether to use production APNS environment
    func registerPushToken(_ token: Data, isProduction: Bool = false) {
        SendBirdCall.registerVoIPPush(token: token, unique: true) { error in
            if let error = error {
                print("❌ [SendbirdCallsManager] Push token registration failed: \(error)")
            } else {
                print("✅ [SendbirdCallsManager] Push token registered successfully")
            }
        }
    }

    // MARK: - Call Management

    /// Handle incoming call from AI assistant
    /// - Parameters:
    ///   - callId: Unique call identifier
    ///   - callerId: ID of the caller (usually AI assistant)
    func handleIncomingCall(callId: String, callerId: String) {
        print("📞 [SendbirdCallsManager] Incoming call from: \(callerId)")

        DispatchQueue.main.async {
            self.currentCallId = callId
            self.callState = .ringing
            self.delegate?.didReceiveIncomingCall(callId: callId, callerId: callerId)
        }

        // Activate audio session for ringing
        activateAudioSession()
    }

    /// Accept incoming call
    /// - Parameter callId: Call ID to accept
    func acceptCall(callId: String) async throws {
        guard callId == currentCallId else {
            throw CallError.invalidCallId
        }

        guard let call = currentCall else {
            throw CallError.callNotFound
        }

        let acceptParams = AcceptParams(callOptions: CallOptions())

        call.accept(with: acceptParams)
        print("✅ [SendbirdCallsManager] Call accept requested")
    }

    /// Decline incoming call
    /// - Parameter callId: Call ID to decline
    func declineCall(callId: String) async {
        guard callId == currentCallId else { return }
        guard let call = currentCall else { return }

        call.end()
        print("✅ [SendbirdCallsManager] Call declined: \(callId)")
    }

    /// End current call
    func endCall() async {
        guard let callId = currentCallId else { return }
        guard let call = currentCall else { return }

        call.end()
        print("✅ [SendbirdCallsManager] Call ended: \(callId)")
    }

    /// Make an outgoing call to a user
    /// - Parameters:
    ///   - calleeId: User ID to call
    ///   - completion: Completion handler with call result
    func makeCall(to calleeId: String, completion: @escaping (Result<DirectCall, Error>) -> Void) {
        let callParams = DialParams(calleeId: calleeId, isVideoCall: false, callOptions: CallOptions(), customItems: [:])

        SendBirdCall.dial(with: callParams) { call, error in
            if let error = error {
                print("❌ [SendbirdCallsManager] Call dial failed: \(error)")
                completion(.failure(error))
            } else if let call = call {
                print("✅ [SendbirdCallsManager] Call initiated: \(call.callId)")

                DispatchQueue.main.async {
                    self.currentCall = call
                    self.currentCallId = call.callId
                    self.callState = .dialing
                }

                // Set delegate for this call
                call.delegate = self

                completion(.success(call))
            }
        }
    }

    // MARK: - Audio Controls

    /// Toggle mute state
    /// - Parameter muted: Whether to mute the microphone
    func setMute(_ muted: Bool) {
        guard let call = currentCall else { return }

        if muted {
            call.muteMicrophone()
        } else {
            call.unmuteMicrophone()
        }

        DispatchQueue.main.async {
            self.isMuted = muted
            print("🎤 [SendbirdCallsManager] Microphone \(muted ? "muted" : "unmuted")")
        }
    }

    /// Toggle speaker state
    /// - Parameter enabled: Whether to enable speaker
    func setSpeaker(_ enabled: Bool) {
        do {
            if enabled {
                try audioSession.overrideOutputAudioPort(.speaker)
            } else {
                try audioSession.overrideOutputAudioPort(.none)
            }

            DispatchQueue.main.async {
                self.isSpeakerOn = enabled
                print("🔊 [SendbirdCallsManager] Speaker \(enabled ? "enabled" : "disabled")")
            }
        } catch {
            print("❌ [SendbirdCallsManager] Failed to toggle speaker: \(error)")
        }
    }

    // MARK: - Audio Session Management

    /// Activate audio session for call
    private func activateAudioSession() {
        do {
            try audioSession.setActive(true)
            print("✅ [SendbirdCallsManager] Audio session activated")
        } catch {
            print("❌ [SendbirdCallsManager] Audio session activation failed: \(error)")
        }
    }

    /// Deactivate audio session after call
    private func deactivateAudioSession() {
        do {
            try audioSession.setActive(false, options: .notifyOthersOnDeactivation)
            print("✅ [SendbirdCallsManager] Audio session deactivated")
        } catch {
            print("❌ [SendbirdCallsManager] Audio session deactivation failed: \(error)")
        }
    }

    // MARK: - Call Duration Tracking

    /// Start tracking call duration
    private func startCallDurationTimer() {
        callDuration = 0

        durationTimer?.invalidate()
        durationTimer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { [weak self] _ in
            DispatchQueue.main.async {
                self?.callDuration += 1
            }
        }

        print("⏱️ [SendbirdCallsManager] Call duration timer started")
    }

    /// Stop tracking call duration
    private func stopCallDurationTimer() {
        durationTimer?.invalidate()
        durationTimer = nil
        print("⏱️ [SendbirdCallsManager] Call duration timer stopped: \(callDuration)s")
    }

    // MARK: - Cleanup

    /// Clean up call resources
    private func cleanup() {
        stopCallDurationTimer()
        deactivateAudioSession()

        currentCallId = nil
        currentCall = nil
        callState = .idle
        isMuted = false
        isSpeakerOn = false
        callDuration = 0

        print("🧹 [SendbirdCallsManager] Call cleanup completed")
    }

    /// Handle call error
    private func handleCallError(_ error: Error) {
        print("❌ [SendbirdCallsManager] Call error: \(error)")

        DispatchQueue.main.async {
            self.callState = .error

            if let callId = self.currentCallId {
                self.delegate?.didCallError(callId: callId, error: error)
            }

            self.cleanup()
        }
    }
}

// MARK: - SendBird Call Delegate

extension SendbirdCallsManager: SendBirdCallDelegate {
    func didStartRinging(_ call: DirectCall) {
        print("📞 [SendbirdCallsManager] Incoming call ringing: \(call.callId)")

        DispatchQueue.main.async {
            self.currentCall = call
            self.currentCallId = call.callId
            self.callState = .ringing
            self.delegate?.didReceiveIncomingCall(
                callId: call.callId,
                callerId: call.caller?.userId ?? "unknown"
            )
        }

        // Set call delegate
        call.delegate = self

        activateAudioSession()
    }
}

// MARK: - DirectCall Delegate

extension SendbirdCallsManager: DirectCallDelegate {
    func didEstablish(_ call: DirectCall) {
        print("✅ [SendbirdCallsManager] Call established: \(call.callId)")

        DispatchQueue.main.async {
            self.callState = .connected
            self.delegate?.didCallConnect(callId: call.callId)
        }

        startCallDurationTimer()
    }

    func didConnect(_ call: DirectCall) {
        print("✅ [SendbirdCallsManager] Call connected: \(call.callId)")

        DispatchQueue.main.async {
            self.callState = .connected
        }
    }

    func didEnd(_ call: DirectCall) {
        print("📞 [SendbirdCallsManager] Call ended: \(call.callId)")

        // Determine end reason from call object
        let reason: CallEndReason
        switch call.endResult {
        case .completed:
            reason = .completed
        case .canceled:
            reason = .canceled
        case .declined:
            reason = .declined
        case .timedOut, .noAnswer:
            reason = .timeout
        case .connectionLost, .dialFailed, .acceptFailed, .otherDeviceAccepted, .notConnected, .none:
            reason = .connectionFailed
        case .unknown:
            reason = .unknown
        @unknown default:
            reason = .unknown
        }

        DispatchQueue.main.async {
            self.delegate?.didCallEnd(callId: call.callId, reason: reason)
            self.cleanup()
        }
    }

    func didRemoteAudioSettingsChange(_ call: DirectCall) {
        print("ℹ️ [SendbirdCallsManager] Remote audio settings changed - muted: \(call.isRemoteAudioEnabled)")
    }

    func didAudioDeviceChange(_ call: DirectCall, session: AVAudioSession, previousRoute: AVAudioSessionRouteDescription, reason: AVAudioSession.RouteChangeReason) {
        print("ℹ️ [SendbirdCallsManager] Audio device changed: \(reason.rawValue)")
    }
}

// MARK: - Error Types

enum CallError: LocalizedError {
    case invalidCallId
    case callNotFound
    case callConnectionFailed
    case audioSessionFailed
    case callAlreadyInProgress

    var errorDescription: String? {
        switch self {
        case .invalidCallId:
            return "유효하지 않은 통화 ID입니다."
        case .callNotFound:
            return "통화를 찾을 수 없습니다."
        case .callConnectionFailed:
            return "통화 연결에 실패했습니다."
        case .audioSessionFailed:
            return "오디오 세션 설정에 실패했습니다."
        case .callAlreadyInProgress:
            return "이미 진행 중인 통화가 있습니다."
        }
    }
}
