//
//  ChatView.swift
//  space
//
//  Created by 임동현 on 11/6/25.
//

import SwiftUI

struct Message: Identifiable {
    let id = UUID()
    let text: String
    let isFromUser: Bool
    let timestamp: Date
}

/// Chat screen - messaging and communication
struct ChatView: View {
    @State private var selectedMode: CommunicationMode?
    @State private var showPhoneCall = false

    var body: some View {
        NavigationStack {
            Group {
                if selectedMode == nil {
                    // Selection screen
                    SelectionView(selectedMode: $selectedMode, showPhoneCall: $showPhoneCall)
                } else if selectedMode == .text {
                    // Text chat view
                    TextChatView(onBack: {
                        selectedMode = nil
                    })
                }
            }
            .navigationTitle("chat")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                if selectedMode != nil {
                    ToolbarItem(placement: .navigationBarLeading) {
                        Button(action: {
                            selectedMode = nil
                        }) {
                            Image(systemName: "chevron.left")
                                .font(.system(size: 18, weight: .semibold))
                                .foregroundColor(.black)
                        }
                    }
                }
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {}) {
                        Image(systemName: "square.dashed")
                            .font(.system(size: 18))
                            .foregroundColor(.black)
                    }
                }
            }
        }
        .fullScreenCover(isPresented: $showPhoneCall) {
            PhoneCallView(contactName: "My home")
        }
    }
}

enum CommunicationMode {
    case text
    case call
}

struct SelectionView: View {
    @Binding var selectedMode: CommunicationMode?
    @Binding var showPhoneCall: Bool

    var body: some View {
        VStack(spacing: 0) {
            Spacer()

            VStack(spacing: 24) {
                // Text message button
                Button(action: {
                    selectedMode = .text
                }) {
                    VStack(spacing: 16) {
                        Image(systemName: "message.fill")
                            .font(.system(size: 50))
                            .foregroundColor(Color(hex: "A50034"))

                        Text("문자")
                            .font(.system(size: 24, weight: .semibold))
                            .foregroundColor(.black)
                    }
                    .frame(maxWidth: .infinity)
                    .frame(height: 200)
                    .background(
                        RoundedRectangle(cornerRadius: 20)
                            .fill(Color(red: 0.98, green: 0.95, blue: 0.98))
                            .shadow(color: .black.opacity(0.08), radius: 10, x: 0, y: 4)
                    )
                }
                .padding(.horizontal, 40)

                // Phone call button
                Button(action: {
                    showPhoneCall = true
                }) {
                    VStack(spacing: 16) {
                        Image(systemName: "phone.fill")
                            .font(.system(size: 50))
                            .foregroundColor(Color(hex: "A50034"))

                        Text("전화")
                            .font(.system(size: 24, weight: .semibold))
                            .foregroundColor(.black)
                    }
                    .frame(maxWidth: .infinity)
                    .frame(height: 200)
                    .background(
                        RoundedRectangle(cornerRadius: 20)
                            .fill(Color(red: 0.98, green: 0.95, blue: 0.98))
                            .shadow(color: .black.opacity(0.08), radius: 10, x: 0, y: 4)
                    )
                }
                .padding(.horizontal, 40)
            }

            Spacer()
        }
        .background(Color.white)
    }
}

struct TextChatView: View {
    @State private var messages: [Message] = [
        Message(text: "안녕하세요! 오늘 집에 언제 도착하시나요?", isFromUser: false, timestamp: Date().addingTimeInterval(-7200)),
        Message(text: "6시쯤 도착할 것 같아요", isFromUser: true, timestamp: Date().addingTimeInterval(-7100)),
        Message(text: "알겠습니다. 저녁은 준비해놓을게요", isFromUser: false, timestamp: Date().addingTimeInterval(-7000)),
        Message(text: "감사합니다!", isFromUser: true, timestamp: Date().addingTimeInterval(-6900)),
        Message(text: "장 봐올 게 있나요?", isFromUser: false, timestamp: Date().addingTimeInterval(-3600)),
        Message(text: "우유랑 빵 좀 부탁드려요", isFromUser: true, timestamp: Date().addingTimeInterval(-3500))
    ]
    @State private var messageText = ""
    @StateObject private var toneManager = ToneManager.shared

    let onBack: () -> Void

    private var currentTone: String {
        if let tone = toneManager.getRandomTone() {
            return tone
        }
        return "말투 선택 안함"
    }

    var body: some View {
        VStack(spacing: 0) {
            // Current tone indicator
            HStack {
                Image(systemName: "bubble.left.and.bubble.right.fill")
                    .font(.system(size: 14))
                    .foregroundColor(Color(hex: "A50034"))

                Text("현재 말투: \(currentTone)")
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(.black.opacity(0.7))

                Spacer()
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 8)
            .background(Color(hex: "F9F9F9"))

            Divider()

            // Messages
            ScrollView {
                VStack(spacing: 12) {
                    ForEach(messages) { message in
                        HStack(alignment: .bottom, spacing: 8) {
                            if message.isFromUser {
                                Spacer()

                                Text(timeString(from: message.timestamp))
                                    .font(.system(size: 11))
                                    .foregroundColor(.gray)
                                    .padding(.bottom, 4)
                            }

                            Text(message.text)
                                .font(.system(size: 15))
                                .foregroundColor(.black)
                                .padding(.horizontal, 16)
                                .padding(.vertical, 12)
                                .background(
                                    RoundedRectangle(cornerRadius: 18)
                                        .fill(message.isFromUser ?
                                              Color(red: 0.98, green: 0.95, blue: 0.98) :
                                              Color(red: 0.95, green: 0.95, blue: 0.97))
                                )
                                .frame(maxWidth: 250, alignment: message.isFromUser ? .trailing : .leading)

                            if !message.isFromUser {
                                Text(timeString(from: message.timestamp))
                                    .font(.system(size: 11))
                                    .foregroundColor(.gray)
                                    .padding(.bottom, 4)

                                Spacer()
                            }
                        }
                        .padding(.horizontal, 16)
                    }
                }
                .padding(.vertical, 16)
            }
            .background(Color.white)

            // Input bar
            HStack(spacing: 12) {
                Button(action: {}) {
                    Image(systemName: "plus.circle.fill")
                        .font(.system(size: 28))
                        .foregroundColor(Color(hex: "A50034"))
                }

                HStack {
                    TextField("메시지를 입력하세요", text: $messageText)
                        .font(.system(size: 15))
                        .padding(.vertical, 10)
                        .padding(.horizontal, 16)

                    if !messageText.isEmpty {
                        Button(action: {
                            sendMessage()
                        }) {
                            Image(systemName: "arrow.up.circle.fill")
                                .font(.system(size: 24))
                                .foregroundColor(Color(hex: "A50034"))
                        }
                        .padding(.trailing, 8)
                    }
                }
                .background(
                    RoundedRectangle(cornerRadius: 20)
                        .fill(Color(red: 0.96, green: 0.96, blue: 0.98))
                )
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
            .background(
                Color.white
                    .shadow(color: .black.opacity(0.05), radius: 1, x: 0, y: -1)
            )
        }
    }

    private func sendMessage() {
        guard !messageText.isEmpty else { return }
        messages.append(Message(text: messageText, isFromUser: true, timestamp: Date()))
        messageText = ""
    }

    private func timeString(from date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "a h:mm"
        formatter.locale = Locale(identifier: "ko_KR")
        return formatter.string(from: date)
    }
}

#Preview {
    ChatView()
}
