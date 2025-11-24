//
//  PhoneCallView.swift
//  space
//
//  Created by 임동현 on 11/24/25.
//

import SwiftUI

struct PhoneCallView: View {
    @Environment(\.dismiss) var dismiss
    @StateObject private var callHistoryManager = CallHistoryManager.shared

    @State private var callDuration: TimeInterval = 0
    @State private var timer: Timer?
    @State private var isMuted = false
    @State private var isSpeakerOn = false
    @State private var showEndCallConfirmation = false

    let contactName: String

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
                    .frame(height: 80)

                // Contact info
                VStack(spacing: 16) {
                    // Profile image
                    Circle()
                        .fill(Color.white.opacity(0.2))
                        .frame(width: 120, height: 120)
                        .overlay(
                            Image(systemName: "person.fill")
                                .font(.system(size: 50))
                                .foregroundColor(.white)
                        )

                    // Contact name
                    Text(contactName)
                        .font(.system(size: 32, weight: .semibold))
                        .foregroundColor(.white)

                    // Call duration
                    Text(formattedDuration)
                        .font(.system(size: 18))
                        .foregroundColor(.white.opacity(0.9))
                        .monospacedDigit()
                }

                Spacer()

                // Call controls
                VStack(spacing: 40) {
                    // First row: mute and speaker
                    HStack(spacing: 60) {
                        // Mute button
                        VStack(spacing: 12) {
                            Button(action: {
                                isMuted.toggle()
                            }) {
                                Circle()
                                    .fill(isMuted ? Color.white : Color.white.opacity(0.3))
                                    .frame(width: 70, height: 70)
                                    .overlay(
                                        Image(systemName: isMuted ? "mic.slash.fill" : "mic.fill")
                                            .font(.system(size: 28))
                                            .foregroundColor(isMuted ? Color(hex: "A50034") : .white)
                                    )
                            }

                            Text("음소거")
                                .font(.system(size: 14))
                                .foregroundColor(.white.opacity(0.9))
                        }

                        // Speaker button
                        VStack(spacing: 12) {
                            Button(action: {
                                isSpeakerOn.toggle()
                            }) {
                                Circle()
                                    .fill(isSpeakerOn ? Color.white : Color.white.opacity(0.3))
                                    .frame(width: 70, height: 70)
                                    .overlay(
                                        Image(systemName: isSpeakerOn ? "speaker.wave.3.fill" : "speaker.fill")
                                            .font(.system(size: 28))
                                            .foregroundColor(isSpeakerOn ? Color(hex: "A50034") : .white)
                                    )
                            }

                            Text("스피커")
                                .font(.system(size: 14))
                                .foregroundColor(.white.opacity(0.9))
                        }
                    }

                    // End call button
                    Button(action: {
                        endCall()
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
                }
                .padding(.bottom, 80)
            }
        }
        .onAppear {
            startTimer()
        }
        .onDisappear {
            stopTimer()
        }
    }

    private var formattedDuration: String {
        let minutes = Int(callDuration) / 60
        let seconds = Int(callDuration) % 60
        return String(format: "%02d:%02d", minutes, seconds)
    }

    private func startTimer() {
        timer = Timer.scheduledTimer(withTimeInterval: 1.0, repeats: true) { _ in
            callDuration += 1
        }
    }

    private func stopTimer() {
        timer?.invalidate()
        timer = nil
    }

    private func endCall() {
        stopTimer()

        // Save call record
        let callRecord = CallRecord(
            contactName: contactName,
            callType: .voice,
            timestamp: Date(),
            duration: callDuration,
            summary: generateCallSummary()
        )
        callHistoryManager.addCallRecord(callRecord)

        dismiss()
    }

    private func generateCallSummary() -> String {
        let summaries = [
            "가족과의 일상적인 통화였습니다.",
            "집에 도착 예정 시간에 대해 이야기했습니다.",
            "저녁 식사 계획에 대해 논의했습니다.",
            "일정 변경 사항을 전달했습니다.",
            "안부 인사를 나누었습니다."
        ]
        return summaries.randomElement() ?? summaries[0]
    }
}

#Preview {
    PhoneCallView(contactName: "My home")
}
