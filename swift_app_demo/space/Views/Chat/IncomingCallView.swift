//
//  IncomingCallView.swift
//  space
//
//  Incoming call UI with accept/decline buttons
//

import SwiftUI

struct IncomingCallView: View {
    @Environment(\.dismiss) var dismiss
    @StateObject private var callsManager = SendbirdCallsManager.shared

    let callerId: String
    let callerName: String
    let callId: String

    @State private var isAccepting = false
    @State private var showError = false
    @State private var errorMessage = ""

    var body: some View {
        ZStack {
            // Background gradient
            LinearGradient(
                gradient: Gradient(colors: [
                    Color(hex: "A50034"),
                    Color(hex: "8B0028")
                ]),
                startPoint: .top,
                endPoint: .bottom
            )
            .ignoresSafeArea()

            VStack(spacing: 0) {
                Spacer()
                    .frame(height: 100)

                // Caller info
                VStack(spacing: 24) {
                    // Profile image with pulse animation
                    ZStack {
                        // Pulse rings
                        ForEach(0..<3) { index in
                            Circle()
                                .stroke(Color.white.opacity(0.3), lineWidth: 2)
                                .frame(width: 120 + CGFloat(index * 40), height: 120 + CGFloat(index * 40))
                                .scaleEffect(pulseScale)
                                .opacity(pulseOpacity)
                                .animation(
                                    Animation.easeOut(duration: 1.5)
                                        .repeatForever(autoreverses: false)
                                        .delay(Double(index) * 0.3),
                                    value: pulseScale
                                )
                        }

                        // Profile image
                        Circle()
                            .fill(Color.white.opacity(0.2))
                            .frame(width: 120, height: 120)
                            .overlay(
                                Image(systemName: "person.fill")
                                    .font(.system(size: 50))
                                    .foregroundColor(.white)
                            )
                    }

                    // Caller name
                    Text(callerName)
                        .font(.system(size: 32, weight: .semibold))
                        .foregroundColor(.white)

                    // Incoming call label
                    Text("전화가 왔습니다")
                        .font(.system(size: 18))
                        .foregroundColor(.white.opacity(0.9))
                }

                Spacer()

                // Call action buttons
                HStack(spacing: 80) {
                    // Decline button
                    VStack(spacing: 12) {
                        Button(action: {
                            declineCall()
                        }) {
                            Circle()
                                .fill(Color.red)
                                .frame(width: 70, height: 70)
                                .overlay(
                                    Image(systemName: "phone.down.fill")
                                        .font(.system(size: 28))
                                        .foregroundColor(.white)
                                )
                        }
                        .disabled(isAccepting)

                        Text("거절")
                            .font(.system(size: 14))
                            .foregroundColor(.white.opacity(0.9))
                    }

                    // Accept button
                    VStack(spacing: 12) {
                        Button(action: {
                            acceptCall()
                        }) {
                            Circle()
                                .fill(Color.green)
                                .frame(width: 70, height: 70)
                                .overlay(
                                    Group {
                                        if isAccepting {
                                            ProgressView()
                                                .tint(.white)
                                        } else {
                                            Image(systemName: "phone.fill")
                                                .font(.system(size: 28))
                                                .foregroundColor(.white)
                                        }
                                    }
                                )
                        }
                        .disabled(isAccepting)

                        Text("수락")
                            .font(.system(size: 14))
                            .foregroundColor(.white.opacity(0.9))
                    }
                }
                .padding(.bottom, 100)
            }
        }
        .alert("통화 오류", isPresented: $showError) {
            Button("확인", role: .cancel) {
                dismiss()
            }
        } message: {
            Text(errorMessage)
        }
        .onAppear {
            startPulseAnimation()
        }
    }

    // MARK: - Animation State

    @State private var pulseScale: CGFloat = 1.0
    @State private var pulseOpacity: Double = 0.8

    private func startPulseAnimation() {
        pulseScale = 1.5
        pulseOpacity = 0.0
    }

    // MARK: - Call Actions

    private func acceptCall() {
        isAccepting = true

        Task {
            do {
                try await callsManager.acceptCall(callId: callId)

                // Dismiss and let PhoneCallView handle the active call
                await MainActor.run {
                    dismiss()
                }
            } catch {
                await MainActor.run {
                    errorMessage = error.localizedDescription
                    showError = true
                    isAccepting = false
                }
            }
        }
    }

    private func declineCall() {
        Task {
            await callsManager.declineCall(callId: callId)

            await MainActor.run {
                dismiss()
            }
        }
    }
}

#Preview {
    IncomingCallView(
        callerId: "ai_assistant",
        callerName: "My home",
        callId: "preview_call_id"
    )
}
