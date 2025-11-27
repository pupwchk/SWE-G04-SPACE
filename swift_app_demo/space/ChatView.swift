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
                    // Persona chat list view
                    PersonaChatListView()
                }
            }
            .navigationTitle("채팅")
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

/// 페르소나 채팅방 목록 화면
struct PersonaChatListView: View {
    @StateObject private var viewModel = PersonaChatListViewModel()

    var body: some View {
        ZStack {
            Color.white
                .ignoresSafeArea()

            if viewModel.isLoading {
                ProgressView()
                    .progressViewStyle(CircularProgressViewStyle(tint: Color(hex: "A50034")))
            } else if viewModel.personas.isEmpty {
                // Empty state
                VStack(spacing: 20) {
                    Image(systemName: "message.circle")
                        .font(.system(size: 60))
                        .foregroundColor(Color(hex: "A50034").opacity(0.6))

                    Text("대화 가능한 페르소나가 없습니다")
                        .font(.system(size: 18, weight: .medium))
                        .foregroundColor(.gray)

                    Text("페르소나 탭에서 페르소나를 생성해주세요")
                        .font(.system(size: 14))
                        .foregroundColor(.gray.opacity(0.7))
                }
            } else {
                ScrollView {
                    LazyVStack(spacing: 0) {
                        ForEach(viewModel.personas) { persona in
                            NavigationLink(destination: PersonaChatView(persona: persona)) {
                                SimpleChatRoomCell(
                                    persona: persona,
                                    adjectives: viewModel.getAdjectivesFor(persona: persona)
                                )
                            }
                            .buttonStyle(.plain)

                            Divider()
                                .padding(.leading, 80)
                        }
                    }
                }
            }
        }
        .onAppear {
            Task {
                await viewModel.loadData()
            }
        }
    }
}

/// 간단한 채팅방 셀 컴포넌트 (편집/삭제 없는 버전)
struct SimpleChatRoomCell: View {
    let persona: Persona
    let adjectives: [Adjective]

    var body: some View {
        HStack(spacing: 16) {
            // 프로필 이미지
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
                .frame(width: 56, height: 56)
                .overlay(
                    Text(String(persona.nickname.prefix(1)))
                        .font(.system(size: 24, weight: .bold))
                        .foregroundColor(.white)
                )

            VStack(alignment: .leading, spacing: 6) {
                // 페르소나 이름
                Text(persona.nickname)
                    .font(.system(size: 17, weight: .semibold))
                    .foregroundColor(.black)

                // 형용사 태그들을 텍스트로 표시
                if !adjectives.isEmpty {
                    Text(adjectives.map { $0.adjectiveName }.joined(separator: " · "))
                        .font(.system(size: 14))
                        .foregroundColor(.gray)
                        .lineLimit(1)
                } else {
                    Text("대화를 시작해보세요")
                        .font(.system(size: 14))
                        .foregroundColor(.gray)
                        .lineLimit(1)
                }
            }

            Spacer()

            // 시간 표시 (나중에 실제 메시지 시간으로 교체 가능)
            Text("지금")
                .font(.system(size: 13))
                .foregroundColor(.gray)
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 12)
        .background(Color.white)
        .contentShape(Rectangle())
    }
}

/// PersonaChatListView의 ViewModel
@MainActor
class PersonaChatListViewModel: ObservableObject {
    @Published var personas: [Persona] = []
    @Published var adjectives: [Adjective] = []
    @Published var isLoading = false

    func loadData() async {
        isLoading = true

        do {
            // Load personas and adjectives in parallel
            async let personasTask = SupabaseManager.shared.fetchPersonas()
            async let adjectivesTask = SupabaseManager.shared.fetchAdjectives()

            personas = try await personasTask
            adjectives = try await adjectivesTask

            print(" Loaded \(personas.count) personas for chat")
        } catch {
            print("  Failed to load data: \(error)")
        }

        isLoading = false
    }

    func getAdjectivesFor(persona: Persona) -> [Adjective] {
        return adjectives.filter { persona.adjectiveIds.contains($0.id) }
    }
}

#Preview {
    ChatView()
}
