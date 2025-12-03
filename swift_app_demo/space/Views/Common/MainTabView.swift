//
//  MainTabView.swift
//  space
//
//  Created by 임동현 on 11/6/25.
//

import SwiftUI

/// Main tab bar view with Home, Appliance, Chat, and Menu tabs
struct MainTabView: View {
    @State private var selectedTab = 0
    @StateObject private var callsManager = SendbirdCallsManager.shared
    @StateObject private var callUIState = CallUIState()

    var body: some View {
        TabView(selection: $selectedTab) {
            // Home Tab
            HomeView()
                .tabItem {
                    Image(systemName: "house.fill")
                    Text("홈")
                }
                .tag(0)

            // Appliance Tab
            ApplianceView()
                .tabItem {
                    Image(systemName: "refrigerator")
                    Text("가전제품")
                }
                .tag(1)

            // Chat Tab
            ChatView()
                .tabItem {
                    Image(systemName: "message.fill")
                    Text("채팅")
                }
                .tag(2)

            // Menu Tab
            MenuView()
                .tabItem {
                    Image(systemName: "line.3.horizontal")
                    Text("메뉴")
                }
                .tag(3)
        }
        .accentColor(Color(hex: "A50034"))
        .fullScreenCover(isPresented: $callUIState.showIncomingCall) {
            IncomingCallView(
                callerId: callUIState.incomingCallerId,
                callerName: callUIState.incomingCallerName,
                callId: callUIState.incomingCallId
            )
        }
        .fullScreenCover(isPresented: $callUIState.showActiveCall) {
            PhoneCallView(
                contactName: callUIState.incomingCallerName,
                callId: callUIState.incomingCallId
            )
        }
        .onAppear {
            setupCallDelegate()
        }
        .onChange(of: callsManager.callState) { oldState, newState in
            handleCallStateChange(oldState: oldState, newState: newState)
        }
    }

    private func setupCallDelegate() {
        callsManager.delegate = callUIState
    }

    private func handleCallStateChange(oldState: CallState, newState: CallState) {
        switch newState {
        case .connected:
            // When call is connected, dismiss incoming call and show active call
            callUIState.showIncomingCall = false
            callUIState.showActiveCall = true
        case .ended, .error:
            // When call ends or errors, dismiss all call screens
            callUIState.showIncomingCall = false
            callUIState.showActiveCall = false
        default:
            break
        }
    }
}

// MARK: - SendbirdCallsDelegate

final class CallUIState: ObservableObject, SendbirdCallsDelegate {
    @Published var showIncomingCall = false
    @Published var showActiveCall = false
    @Published var incomingCallId = ""
    @Published var incomingCallerId = ""
    @Published var incomingCallerName = "My home"

    func didReceiveIncomingCall(callId: String, callerId: String) {
        print("📞 [MainTabView] Incoming call received: \(callId) from \(callerId)")

        // Update incoming call state
        incomingCallId = callId
        incomingCallerId = callerId

        // Set caller name based on caller ID
        if callerId == Config.aiUserId {
            incomingCallerName = "My home"
        } else {
            incomingCallerName = callerId
        }

        // Show incoming call UI
        showIncomingCall = true
    }

    func didCallConnect(callId: String) {
        print("✅ [MainTabView] Call connected: \(callId)")
        // State change will be handled by handleCallStateChange
    }

    func didCallEnd(callId: String, reason: CallEndReason) {
        print("📞 [MainTabView] Call ended: \(callId), reason: \(reason)")
        // Dismiss incoming call sheet when call ends
        showIncomingCall = false
        showActiveCall = false
    }

    func didCallError(callId: String, error: Error) {
        print("❌ [MainTabView] Call error: \(callId), error: \(error)")
        // Dismiss incoming call sheet on error
        showIncomingCall = false
        showActiveCall = false
    }
}

#Preview {
    MainTabView()
}
