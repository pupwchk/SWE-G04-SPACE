//
//  PersonaChatView.swift
//  space
//
//  페르소나와의 채팅 화면
//

import SwiftUI

/// 페르소나와의 1:1 채팅 화면
struct PersonaChatView: View {
    let persona: Persona

    @StateObject private var viewModel = PersonaChatViewModel()
    @State private var messageText = ""
    @FocusState private var isInputFocused: Bool

    var body: some View {
        VStack(spacing: 0) {
            // 메시지 리스트
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(spacing: 12) {
                        ForEach(viewModel.messages) { message in
                            MessageBubble(message: message, personaName: persona.nickname)
                                .id(message.id)
                        }
                    }
                    .padding(.horizontal, 16)
                    .padding(.vertical, 12)
                }
                .onChange(of: viewModel.messages.count) {
                    if let lastMessage = viewModel.messages.last {
                        withAnimation {
                            proxy.scrollTo(lastMessage.id, anchor: .bottom)
                        }
                    }
                }
            }

            // 가전 수정사항 위젯
            if viewModel.showChangeSummary && !viewModel.applianceChanges.isEmpty {
                ApplianceChangeSummaryWidget(
                    changes: viewModel.applianceChanges,
                    isExpanded: $viewModel.isWidgetExpanded
                )
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .transition(.move(edge: .bottom).combined(with: .opacity))
            }

            Divider()

            // 입력 영역
            HStack(spacing: 12) {
                TextField("메시지를 입력하세요...", text: $messageText, axis: .vertical)
                    .textFieldStyle(.plain)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 10)
                    .background(Color(hex: "F5F5F5"))
                    .cornerRadius(20)
                    .lineLimit(1...5)
                    .focused($isInputFocused)

                Button(action: sendMessage) {
                    Image(systemName: "arrow.up.circle.fill")
                        .font(.system(size: 32))
                        .foregroundColor(messageText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? .gray : Color(hex: "A50034"))
                }
                .disabled(messageText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
            .background(Color.white)
        }
        .background(Color(hex: "F9F9F9"))
        .navigationTitle(persona.nickname)
        .navigationBarTitleDisplayMode(.inline)
        .onAppear {
            viewModel.loadMessages(for: persona.id, personaName: persona.nickname)
        }
    }

    private func sendMessage() {
        let text = messageText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }

        viewModel.sendMessage(text: text, personaId: persona.id, personaName: persona.nickname)
        messageText = ""
    }
}

/// 메시지 버블 컴포넌트
struct MessageBubble: View {
    let message: ChatMessage
    let personaName: String

    var body: some View {
        HStack(alignment: .bottom, spacing: 8) {
            if message.isFromUser {
                Spacer()

                VStack(alignment: .trailing, spacing: 4) {
                    Text(message.text)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 10)
                        .background(Color(hex: "A50034"))
                        .foregroundColor(.white)
                        .cornerRadius(18)
                        .frame(maxWidth: UIScreen.main.bounds.width * 0.7, alignment: .trailing)

                    Text(formatTime(message.timestamp))
                        .font(.system(size: 11))
                        .foregroundColor(.gray)
                }
            } else {
                // 페르소나 프로필
                Circle()
                    .fill(
                        LinearGradient(
                            gradient: Gradient(colors: [
                                Color(hex: "A50034"),
                                Color(hex: "A50034").opacity(0.7)
                            ]),
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .frame(width: 32, height: 32)
                    .overlay(
                        Text(String(personaName.prefix(1)))
                            .font(.system(size: 14, weight: .bold))
                            .foregroundColor(.white)
                    )

                VStack(alignment: .leading, spacing: 4) {
                    Text(message.text)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 10)
                        .background(Color.white)
                        .foregroundColor(.black)
                        .cornerRadius(18)
                        .frame(maxWidth: UIScreen.main.bounds.width * 0.7, alignment: .leading)

                    Text(formatTime(message.timestamp))
                        .font(.system(size: 11))
                        .foregroundColor(.gray)
                }

                Spacer()
            }
        }
    }

    private func formatTime(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm"
        return formatter.string(from: date)
    }
}

/// 채팅 메시지 모델
struct ChatMessage: Identifiable {
    let id: String
    let text: String
    let isFromUser: Bool
    let timestamp: Date

    init(id: String = UUID().uuidString, text: String, isFromUser: Bool, timestamp: Date = Date()) {
        self.id = id
        self.text = text
        self.isFromUser = isFromUser
        self.timestamp = timestamp
    }
}

/// 가전 제품 변경 사항 모델
struct ApplianceChange: Identifiable {
    let id: UUID
    let applianceName: String      // "에어컨", "조명" 등
    let icon: String                // SF Symbol 아이콘
    let action: String              // "켜기", "끄기"
    let detail: String?             // "22°C", "30% 밝기" 등 추가 정보
    let isModified: Bool            // 사용자가 수정한 항목인지 여부

    init(id: UUID = UUID(), applianceName: String, icon: String, action: String, detail: String? = nil, isModified: Bool = false) {
        self.id = id
        self.applianceName = applianceName
        self.icon = icon
        self.action = action
        self.detail = detail
        self.isModified = isModified
    }
}

/// 채팅 ViewModel
@MainActor
class PersonaChatViewModel: ObservableObject {
    @Published var messages: [ChatMessage] = []
    @Published var isLoading = false
    @Published var applianceChanges: [ApplianceChange] = []
    @Published var showChangeSummary: Bool = false
    @Published var isWidgetExpanded: Bool = true

    func loadMessages(for personaId: String, personaName: String) {
        // "하루" 페르소나인 경우 더미 데이터 로드
        if personaName == "하루" {
            loadDemoMessages()
            loadDemoApplianceChanges()
        } else {
            // 다른 페르소나는 빈 배열로 시작
            messages = []
            applianceChanges = []
            showChangeSummary = false
        }
    }

    private func loadDemoMessages() {
        let now = Date()

        messages = [
            ChatMessage(
                text: "곧 집에 도착하시네요! 오늘 운동하시느라 고생 많으셨어요~ 지금 날씨가 많이 춥던데 괜찮으세요? 😊",
                isFromUser: false,
                timestamp: now.addingTimeInterval(-600)
            ),
            ChatMessage(
                text: "응 진짜 춥다ㅠㅠ 집 도착하기 전에 미리 따뜻하게 해놔줄래?",
                isFromUser: true,
                timestamp: now.addingTimeInterval(-540)
            ),
            ChatMessage(
                text: "알겠어요! 지금 상태 확인해볼게요. 현재 실내 온도는 10°C네요. 제가 이렇게 준비해드릴까요?\n\n• 난방 켜기 (22°C로 설정)\n• 공기청정기 켜기\n• 가습기 켜기 (습도 50%)\n• 거실 조명 50% 밝기로 켜기\n\n어떻게 하면 좋을까요?",
                isFromUser: false,
                timestamp: now.addingTimeInterval(-480)
            ),
            ChatMessage(
                text: "좋은데 난방은 24도로 해주고, 조명은 30%만 켜줘",
                isFromUser: true,
                timestamp: now.addingTimeInterval(-360)
            ),
            ChatMessage(
                text: "네, 알겠어요! 수정해드릴게요 👍\n\n• 난방 24°C로 조정\n• 조명 30% 밝기로 변경\n\n나머지는 그대로 적용할게요. 이대로 진행해도 될까요?",
                isFromUser: false,
                timestamp: now.addingTimeInterval(-300)
            ),
            ChatMessage(
                text: "응 좋아!",
                isFromUser: true,
                timestamp: now.addingTimeInterval(-240)
            ),
            ChatMessage(
                text: "설정 완료했어요! 집에 도착하시면 따뜻하게 준비되어 있을 거예요 😊 안전하게 들어오세요!",
                isFromUser: false,
                timestamp: now.addingTimeInterval(-180)
            ),
            ChatMessage(
                text: "고마워~",
                isFromUser: true,
                timestamp: now.addingTimeInterval(-120)
            )
        ]
    }

    private func loadDemoApplianceChanges() {
        applianceChanges = [
            ApplianceChange(
                applianceName: "난방",
                icon: "flame.fill",
                action: "켜기",
                detail: "24°C",
                isModified: true
            ),
            ApplianceChange(
                applianceName: "조명",
                icon: "lightbulb.fill",
                action: "켜기",
                detail: "30% 밝기",
                isModified: true
            ),
            ApplianceChange(
                applianceName: "공기청정기",
                icon: "wind",
                action: "켜기",
                detail: nil,
                isModified: false
            ),
            ApplianceChange(
                applianceName: "가습기",
                icon: "humidity.fill",
                action: "켜기",
                detail: "습도 50%",
                isModified: false
            )
        ]
        showChangeSummary = true
    }

    func sendMessage(text: String, personaId: String, personaName: String) {
        // 사용자 메시지 추가
        let userMessage = ChatMessage(text: text, isFromUser: true)
        messages.append(userMessage)

        // TODO: 실제로 API 호출해서 페르소나의 응답 받기
        // 지금은 임시로 자동 응답 생성
        Task {
            try? await Task.sleep(nanoseconds: 1_000_000_000) // 1초 대기

            let responseText = generateDummyResponse(for: text, personaName: personaName)
            let personaMessage = ChatMessage(text: responseText, isFromUser: false)
            messages.append(personaMessage)
        }
    }

    private func generateDummyResponse(for userMessage: String, personaName: String) -> String {
        // 임시 응답 생성
        let responses = [
            "안녕하세요! \(personaName)입니다.",
            "그렇군요. 더 자세히 말씀해주시겠어요?",
            "좋은 질문이네요!",
            "제 생각에는...",
            "이해했습니다!"
        ]
        return responses.randomElement() ?? "메시지를 받았습니다."
    }
}

/// 가전 수정사항 위젯
struct ApplianceChangeSummaryWidget: View {
    let changes: [ApplianceChange]
    @Binding var isExpanded: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // 헤더 (탭 가능)
            Button(action: {
                withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) {
                    isExpanded.toggle()
                }
            }) {
                HStack {
                    Image(systemName: "checklist")
                        .font(.system(size: 16))
                        .foregroundColor(Color(hex: "A50034"))
                    Text("설정 변경 사항")
                        .font(.system(size: 15, weight: .semibold))
                        .foregroundColor(.black)
                    Spacer()
                    Image(systemName: isExpanded ? "chevron.up" : "chevron.down")
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundColor(.gray)
                }
            }
            .buttonStyle(.plain)

            if isExpanded {
                Divider()

                // 변경 사항 리스트
                ForEach(changes) { change in
                    ApplianceChangeRow(change: change)
                }
            }
        }
        .padding(16)
        .background(Color.white)
        .cornerRadius(12)
        .shadow(color: .black.opacity(0.1), radius: 8, x: 0, y: 2)
    }
}

/// 가전 변경 사항 행
struct ApplianceChangeRow: View {
    let change: ApplianceChange

    var body: some View {
        HStack(spacing: 10) {
            // 아이콘
            Image(systemName: change.icon)
                .font(.system(size: 18))
                .foregroundColor(Color(hex: "A50034"))
                .frame(width: 24)

            // 텍스트
            VStack(alignment: .leading, spacing: 2) {
                HStack(spacing: 6) {
                    Text("\(change.applianceName) \(change.action)")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(.black)

                    if change.isModified {
                        Image(systemName: "pencil.circle.fill")
                            .font(.system(size: 14))
                            .foregroundColor(Color(hex: "A50034").opacity(0.7))
                    }
                }

                if let detail = change.detail {
                    Text(detail)
                        .font(.system(size: 12))
                        .foregroundColor(.gray)
                }
            }

            Spacer()
        }
    }
}

#Preview {
    NavigationStack {
        PersonaChatView(persona: Persona(
            id: "1",
            userId: "user1",
            nickname: "테스트",
            adjectiveIds: [],
            customInstructions: nil,
            finalPrompt: nil,
            createdAt: nil,
            updatedAt: nil
        ))
    }
}
