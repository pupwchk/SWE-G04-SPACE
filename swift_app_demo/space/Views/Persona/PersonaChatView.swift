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
    @StateObject private var callsManager = SendbirdCallsManager.shared
    @State private var messageText = ""
    @State private var showPhoneCall = false
    @State private var showCallError = false
    @State private var callErrorMessage = ""
    @FocusState private var isInputFocused: Bool

    var body: some View {
        VStack(spacing: 0) {
            // 메시지 리스트
            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(spacing: 12) {
                        // Loading indicator
                        if viewModel.isLoading && viewModel.messages.isEmpty {
                            ProgressView("대화 기록을 불러오는 중...")
                                .padding()
                        }

                        // Messages
                        ForEach(viewModel.messages) { message in
                            MessageBubble(message: message, personaName: persona.nickname)
                                .id(message.id)
                        }

                        // Typing indicator
                        if viewModel.isLoading && !viewModel.messages.isEmpty {
                            HStack(alignment: .bottom, spacing: 8) {
                                Circle()
                                    .fill(LinearGradient(
                                        gradient: Gradient(colors: [Color(hex: "A50034"), Color(hex: "A50034").opacity(0.7)]),
                                        startPoint: .topLeading,
                                        endPoint: .bottomTrailing
                                    ))
                                    .frame(width: 32, height: 32)
                                    .overlay(
                                        Text(String(persona.nickname.prefix(1)))
                                            .font(.system(size: 14, weight: .bold))
                                            .foregroundColor(.white)
                                    )

                                HStack(spacing: 4) {
                                    ForEach(0..<3) { index in
                                        Circle()
                                            .fill(Color.gray.opacity(0.6))
                                            .frame(width: 8, height: 8)
                                            .scaleEffect(viewModel.isLoading ? 1.0 : 0.5)
                                            .animation(
                                                Animation.easeInOut(duration: 0.6)
                                                    .repeatForever()
                                                    .delay(Double(index) * 0.2),
                                                value: viewModel.isLoading
                                            )
                                    }
                                }
                                .padding(.horizontal, 16)
                                .padding(.vertical, 10)
                                .background(Color.white)
                                .cornerRadius(18)

                                Spacer()
                            }
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

            // Error message
            if let error = viewModel.errorMessage {
                HStack {
                    Image(systemName: "exclamationmark.triangle.fill")
                        .foregroundColor(.red)
                    Text(error)
                        .font(.system(size: 14))
                        .foregroundColor(.red)
                    Spacer()
                    Button("닫기") {
                        viewModel.errorMessage = nil
                    }
                    .font(.system(size: 14, weight: .medium))
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 8)
                .background(Color.red.opacity(0.1))
            }

            // 가전 수정사항 위젯
            if viewModel.showChangeSummary && !viewModel.applianceChanges.isEmpty {
                ApplianceChangeSummaryWidget(
                    changes: viewModel.applianceChanges,
                    isExpanded: $viewModel.isWidgetExpanded,
                    onApprove: {
                        viewModel.approveChanges()
                    },
                    onReject: {
                        viewModel.showChangeSummary = false
                        viewModel.applianceChanges = []
                    }
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
        .toolbar {
            ToolbarItem(placement: .navigationBarTrailing) {
                Button(action: {
                    startVoiceCall()
                }) {
                    Image(systemName: "phone.fill")
                        .foregroundColor(Color(hex: "A50034"))
                }
            }
        }
        .sheet(isPresented: $showPhoneCall) {
            PhoneCallView(contactName: persona.nickname, callId: callsManager.currentCallId)
        }
        .alert("통화 오류", isPresented: $showCallError) {
            Button("확인", role: .cancel) { }
        } message: {
            Text(callErrorMessage)
        }
        .onAppear {
            viewModel.loadMessages(for: persona.id, personaName: persona.nickname)

            // 해당 채널의 알림 제거 및 배지 카운트 초기화
            Task {
                if let userId = SupabaseManager.shared.currentUser?.id {
                    do {
                        let channelUrl = try await SendbirdChatManager.shared.getOrCreateChannel(
                            userId: userId,
                            personaId: persona.id
                        )
                        NotificationManager.shared.removeNotifications(for: channelUrl)
                    } catch {
                        print("⚠️ [PersonaChatView] Failed to get channel for notification cleanup: \(error)")
                    }
                }
            }

            // Authenticate user with SendBird Calls using FastAPI user_id
            // NOTE: Must use FastAPI user_id (stored in UserDefaults), not Supabase UUID
            if let fastapiUserId = UserDefaults.standard.string(forKey: "fastapi_user_id") {
                callsManager.authenticate(userId: fastapiUserId) { result in
                    switch result {
                    case .success(let user):
                        print("✅ [PersonaChatView] Authenticated with SendBird Calls: \(user.userId)")
                    case .failure(let error):
                        print("❌ [PersonaChatView] SendBird Calls authentication failed: \(error)")
                    }
                }
            } else {
                print("⚠️ [PersonaChatView] FastAPI user_id not found in UserDefaults")
            }
        }
    }

    private func startVoiceCall() {
        // Make a call to the AI assistant
        callsManager.makeCall(to: Config.aiUserId) { result in
            switch result {
            case .success(_):
                print("✅ [PersonaChatView] Call initiated successfully")
                showPhoneCall = true
            case .failure(let error):
                print("❌ [PersonaChatView] Call failed: \(error)")
                callErrorMessage = error.localizedDescription
                showCallError = true
            }
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
    let customType: String?
    let data: String?

    init(id: String = UUID().uuidString, text: String, isFromUser: Bool, timestamp: Date = Date(), customType: String? = nil, data: String? = nil) {
        self.id = id
        self.text = text
        self.isFromUser = isFromUser
        self.timestamp = timestamp
        self.customType = customType
        self.data = data
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
    @Published var errorMessage: String?

    // MARK: - Dependencies
    private let chatService = ChatService.shared
    private let chatManager = SendbirdChatManager.shared
    private let supabaseManager = SupabaseManager.shared

    // Current persona context
    private var currentPersonaId: String?
    private var currentPersonaContext: String?

    // Store metadata for approval
    private var currentMetadata: MessageMetadata?

    init() {
        // Set delegate to receive real-time messages
        chatManager.delegate = self
    }

    // MARK: - Load Messages

    func loadMessages(for personaId: String, personaName: String) {
        self.currentPersonaId = personaId

        // Load persona context (final prompt)
        Task {
            await loadPersonaContext(personaId: personaId)
            await loadChatHistory(personaId: personaId)
        }
    }

    private func loadPersonaContext(personaId: String) async {
        // Get persona details from Supabase to retrieve final_prompt
        do {
            let personas = try await supabaseManager.fetchPersonas()
            guard let persona = personas.first(where: { $0.id == personaId }) else {
                print("⚠️ [PersonaChatViewModel] Persona not found: \(personaId)")
                return
            }

            self.currentPersonaContext = persona.finalPrompt
            print("✅ [PersonaChatViewModel] Loaded persona context: \(persona.finalPrompt?.prefix(50) ?? "nil")")
        } catch {
            print("❌ [PersonaChatViewModel] Failed to load persona context: \(error)")
        }
    }

    private func loadChatHistory(personaId: String) async {
        isLoading = true
        errorMessage = nil

        do {
            // Load message history from ChatService
            let history = try await chatService.loadHistory(personaId: personaId, limit: 50)

            self.messages = history
            print("✅ [PersonaChatViewModel] Loaded \(history.count) messages")

        } catch {
            print("❌ [PersonaChatViewModel] Failed to load history: \(error)")
            self.errorMessage = "대화 기록을 불러올 수 없습니다."
            self.messages = []
        }

        isLoading = false
    }

    // MARK: - Send Message

    func sendMessage(text: String, personaId: String, personaName: String) {
        guard supabaseManager.currentUser != nil else {
            errorMessage = "로그인이 필요합니다."
            return
        }

        // Add user message to UI immediately
        let userMessage = ChatMessage(text: text, isFromUser: true)
        messages.append(userMessage)

        // Send via ChatService
        Task {
            do {
                isLoading = true

                // Send message with persona context
                _ = try await chatService.sendMessage(
                    text: text,
                    personaId: personaId,
                    personaContext: currentPersonaContext ?? ""
                )

                print("✅ [PersonaChatViewModel] Message sent successfully")

                // AI response will arrive via SendbirdChatDelegate

            } catch {
                print("❌ [PersonaChatViewModel] Failed to send message: \(error)")

                // Show error message
                await MainActor.run {
                    self.errorMessage = "메시지 전송에 실패했습니다."

                    // Remove user message on error
                    if let index = self.messages.firstIndex(where: { $0.id == userMessage.id }) {
                        self.messages.remove(at: index)
                    }
                }
            }

            isLoading = false
        }
    }

    // MARK: - Appliance Changes

    private func parseApplianceChanges(from message: ChatMessage) {
        // Parse appliance changes from AI message
        let changes = chatService.parseApplianceChanges(from: message)

        if !changes.isEmpty {
            self.applianceChanges = changes
            self.showChangeSummary = true

            // Store metadata for later approval
            if let dataString = message.data,
               let jsonData = dataString.data(using: .utf8),
               let metadata = try? JSONDecoder().decode(MessageMetadata.self, from: jsonData) {
                self.currentMetadata = metadata
                print("✅ [PersonaChatViewModel] Stored metadata for approval")
            }

            print("✅ [PersonaChatViewModel] Parsed \(changes.count) appliance changes")
        }
    }

    func approveChanges() {
        guard let userId = supabaseManager.currentUser?.id else { return }

        Task {
            do {
                let success = try await chatService.approveChanges(
                    userId: userId,
                    changes: applianceChanges,
                    userResponse: "좋아",
                    metadata: currentMetadata
                )

                if success {
                    print("✅ [PersonaChatViewModel] Appliance changes approved")

                    // Hide widget after approval
                    await MainActor.run {
                        self.showChangeSummary = false
                        self.applianceChanges = []
                        self.currentMetadata = nil
                    }
                }
            } catch {
                print("❌ [PersonaChatViewModel] Failed to approve changes: \(error)")
                self.errorMessage = "가전 제어에 실패했습니다."
            }
        }
    }
}

// MARK: - SendbirdChatDelegate

extension PersonaChatViewModel: SendbirdChatDelegate {
    nonisolated func didReceiveMessage(_ message: ChatMessage, channelUrl: String) {
        print("✅ [PersonaChatViewModel] Received message: \(message.text)")

        Task { @MainActor in
            // Add AI message to UI
            self.messages.append(message)

            // Parse appliance changes if this is an AI message
            if !message.isFromUser {
                self.parseApplianceChanges(from: message)
            }
        }
    }

    nonisolated func didUpdateChannel(_ channelUrl: String) {
        print("ℹ️ [PersonaChatViewModel] Channel updated: \(channelUrl)")
    }

    nonisolated func didReceiveError(_ error: Error) {
        print("❌ [PersonaChatViewModel] Received error: \(error)")
        Task { @MainActor in
            self.errorMessage = error.localizedDescription
        }
    }
}

/// 가전 수정사항 위젯
struct ApplianceChangeSummaryWidget: View {
    let changes: [ApplianceChange]
    @Binding var isExpanded: Bool
    let onApprove: () -> Void
    let onReject: () -> Void

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

                    VStack(alignment: .leading, spacing: 2) {
                        Text("가전 제어 요청")
                            .font(.system(size: 15, weight: .semibold))
                            .foregroundColor(.black)

                        Text("\(changes.count)개의 기기를 제어하려고 합니다")
                            .font(.system(size: 12))
                            .foregroundColor(.gray)
                    }

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

                Divider()

                // Action buttons
                HStack(spacing: 12) {
                    // Reject button
                    Button(action: onReject) {
                        HStack {
                            Image(systemName: "xmark.circle.fill")
                                .font(.system(size: 16))
                            Text("거부")
                                .font(.system(size: 15, weight: .medium))
                        }
                        .foregroundColor(.gray)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 12)
                        .background(Color.gray.opacity(0.1))
                        .cornerRadius(8)
                    }
                    .buttonStyle(.plain)

                    // Approve button
                    Button(action: onApprove) {
                        HStack {
                            Image(systemName: "checkmark.circle.fill")
                                .font(.system(size: 16))
                            Text("승인")
                                .font(.system(size: 15, weight: .medium))
                        }
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 12)
                        .background(Color(hex: "A50034"))
                        .cornerRadius(8)
                    }
                    .buttonStyle(.plain)
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
            VStack(alignment: .leading, spacing: 6) {
                // 가전 이름
                HStack(spacing: 6) {
                    Text(change.applianceName)
                        .font(.system(size: 15, weight: .semibold))
                        .foregroundColor(.black)

                    if change.isModified {
                        Image(systemName: "pencil.circle.fill")
                            .font(.system(size: 12))
                            .foregroundColor(Color(hex: "A50034").opacity(0.7))
                    }
                }

                // 동작 상태와 세부 정보를 한 줄로 표시
                HStack(spacing: 8) {
                    // 동작 상태 (on/off 등)
                    HStack(spacing: 4) {
                        Image(systemName: getActionIcon(for: change.action))
                            .font(.system(size: 12))
                            .foregroundColor(getActionColor(for: change.action))

                        Text(getActionText(for: change.action))
                            .font(.system(size: 13, weight: .medium))
                            .foregroundColor(getActionColor(for: change.action))
                    }

                    // 세부 정보 (온도, 모드 등)
                    if let detail = change.detail, !detail.isEmpty {
                        Text("•")
                            .font(.system(size: 12))
                            .foregroundColor(.gray)

                        Text(detail)
                            .font(.system(size: 13))
                            .foregroundColor(.gray)
                    }
                }
            }

            Spacer()
        }
        .padding(.vertical, 6)
    }

    // 동작에 따른 아이콘 반환
    private func getActionIcon(for action: String) -> String {
        let lowercased = action.lowercased()
        if lowercased.contains("on") || lowercased.contains("켜") {
            return "power.circle.fill"
        } else if lowercased.contains("off") || lowercased.contains("끄") {
            return "power.circle"
        } else {
            return "gearshape.fill"
        }
    }

    // 동작에 따른 색상 반환
    private func getActionColor(for action: String) -> Color {
        let lowercased = action.lowercased()
        if lowercased.contains("on") || lowercased.contains("켜") {
            return Color(hex: "A50034")
        } else if lowercased.contains("off") || lowercased.contains("끄") {
            return .gray
        } else {
            return Color(hex: "A50034").opacity(0.8)
        }
    }

    // 동작 텍스트 한글화
    private func getActionText(for action: String) -> String {
        let lowercased = action.lowercased()
        if lowercased == "on" {
            return "켜기"
        } else if lowercased == "off" {
            return "끄기"
        } else {
            return action
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
