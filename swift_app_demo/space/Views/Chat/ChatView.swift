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
    @EnvironmentObject var navigationCoordinator: NavigationCoordinator

    var body: some View {
        NavigationStack {
            PersonaChatListView()
                .navigationTitle("채팅")
                .navigationBarTitleDisplayMode(.inline)
                .navigationDestination(item: $navigationCoordinator.personaToOpen) { persona in
                    PersonaChatView(persona: persona)
                        .onAppear {
                            print("📱 [ChatView] PersonaChatView appeared for: \(persona.nickname)")
                        }
                        .onDisappear {
                            print("📱 [ChatView] PersonaChatView disappeared for: \(persona.nickname)")
                            // Clear navigation state when user manually navigates back
                            navigationCoordinator.clearNavigationState()
                        }
                }
                .onChange(of: navigationCoordinator.personaToOpen) { oldValue, newValue in
                    if let persona = newValue {
                        print("📱 [ChatView] personaToOpen changed to: \(persona.nickname)")
                    } else {
                        print("📱 [ChatView] personaToOpen cleared")
                    }
                }
        }
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
