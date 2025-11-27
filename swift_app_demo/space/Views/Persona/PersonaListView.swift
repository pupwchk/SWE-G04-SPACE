//
//  PersonaListView.swift
//  space
//
//  페르소나 리스트 화면

import SwiftUI

/// 페르소나 리스트 화면
struct PersonaListView: View {
    @StateObject private var viewModel = PersonaListViewModel()
    @State private var showingEditView = false
    @State private var personaToEdit: Persona?
    @State private var personaToDelete: Persona?
    @State private var showingDeleteAlert = false
    @State private var isSelectionMode = false
    @State private var selectedPersonaIds: Set<String> = []

    var body: some View {
        NavigationStack {
            ZStack {
                // Background
                Color.white
                    .ignoresSafeArea()

                if viewModel.isLoading {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: Color(hex: "A50034")))
                } else if viewModel.personas.isEmpty {
                    // Empty state
                    VStack(spacing: 20) {
                        Image(systemName: "person.crop.circle.badge.plus")
                            .font(.system(size: 60))
                            .foregroundColor(Color(hex: "A50034").opacity(0.6))

                        Text("생성된 페르소나가 없습니다")
                            .font(.system(size: 18, weight: .medium))
                            .foregroundColor(.gray)

                        Button(action: {
                            showingEditView = true
                        }) {
                            Text("페르소나 생성하기")
                                .font(.system(size: 16, weight: .semibold))
                                .foregroundColor(.white)
                                .padding(.horizontal, 24)
                                .padding(.vertical, 12)
                                .background(Color(hex: "A50034"))
                                .cornerRadius(25)
                        }
                    }
                } else {
                    VStack(spacing: 0) {
                        ScrollView {
                            LazyVStack(spacing: 0) {
                                ForEach(viewModel.personas) { persona in
                                    if isSelectionMode {
                                        // Selection mode - show checkbox
                                        Button(action: {
                                            toggleSelection(for: persona.id)
                                        }) {
                                            ChatRoomCell(
                                                persona: persona,
                                                adjectives: viewModel.getAdjectivesFor(persona: persona),
                                                onEdit: {
                                                    personaToEdit = persona
                                                },
                                                onDelete: {
                                                    personaToDelete = persona
                                                    showingDeleteAlert = true
                                                },
                                                isSelectionMode: true,
                                                isSelected: selectedPersonaIds.contains(persona.id)
                                            )
                                        }
                                        .buttonStyle(.plain)
                                    } else {
                                        // Normal mode - navigate to chat
                                        NavigationLink(destination: PersonaChatView(persona: persona)) {
                                            ChatRoomCell(
                                                persona: persona,
                                                adjectives: viewModel.getAdjectivesFor(persona: persona),
                                                onEdit: {
                                                    personaToEdit = persona
                                                },
                                                onDelete: {
                                                    personaToDelete = persona
                                                    showingDeleteAlert = true
                                                },
                                                isSelectionMode: false,
                                                isSelected: false
                                            )
                                        }
                                        .buttonStyle(.plain)
                                    }

                                    Divider()
                                        .padding(.leading, isSelectionMode ? 100 : 80)
                                }
                            }
                        }

                        // Selection mode bottom bar
                        if isSelectionMode {
                            VStack(spacing: 0) {
                                Divider()

                                HStack(spacing: 16) {
                                    Text("\(selectedPersonaIds.count)/5 선택됨")
                                        .font(.system(size: 14))
                                        .foregroundColor(.gray)

                                    Spacer()

                                    Button(action: {
                                        isSelectionMode = false
                                        selectedPersonaIds.removeAll()
                                    }) {
                                        Text("취소")
                                            .font(.system(size: 16, weight: .medium))
                                            .foregroundColor(.gray)
                                    }

                                    Button(action: {
                                        Task {
                                            await saveSelection()
                                        }
                                    }) {
                                        Text("선택 저장")
                                            .font(.system(size: 16, weight: .semibold))
                                            .foregroundColor(.white)
                                            .padding(.horizontal, 20)
                                            .padding(.vertical, 10)
                                            .background(Color(hex: "A50034"))
                                            .cornerRadius(20)
                                    }
                                    .disabled(selectedPersonaIds.isEmpty)
                                    .opacity(selectedPersonaIds.isEmpty ? 0.5 : 1.0)
                                }
                                .padding(.horizontal, 20)
                                .padding(.vertical, 12)
                                .background(Color.white)
                            }
                        }
                    }
                }

                // Success/Error message
                if let errorMessage = viewModel.errorMessage {
                    VStack {
                        Spacer()
                        Text(errorMessage)
                            .font(.system(size: 14))
                            .foregroundColor(.white)
                            .padding()
                            .background(errorMessage.contains("✅") ? Color.green : Color.red)
                            .cornerRadius(12)
                            .padding()
                    }
                }
            }
            .navigationTitle("페르소나")
            .navigationBarTitleDisplayMode(.large)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    if !viewModel.personas.isEmpty {
                        Button(action: {
                            toggleSelectionMode()
                        }) {
                            Text(isSelectionMode ? "완료" : "선택")
                                .font(.system(size: 16, weight: .medium))
                                .foregroundColor(Color(hex: "A50034"))
                        }
                    }
                }

                ToolbarItem(placement: .navigationBarTrailing) {
                    Button(action: {
                        showingEditView = true
                    }) {
                        Image(systemName: "plus")
                            .font(.system(size: 18, weight: .semibold))
                            .foregroundColor(Color(hex: "A50034"))
                    }
                    .disabled(isSelectionMode)
                    .opacity(isSelectionMode ? 0.3 : 1.0)
                }
            }
            .sheet(isPresented: $showingEditView, onDismiss: {
                Task {
                    await viewModel.loadData()
                }
            }) {
                NavigationStack {
                    PersonaEditView()
                }
            }
            .sheet(item: $personaToEdit, onDismiss: {
                Task {
                    await viewModel.loadData()
                }
            }) { persona in
                NavigationStack {
                    PersonaEditView(persona: persona)
                }
            }
            .alert("페르소나 삭제", isPresented: $showingDeleteAlert) {
                Button("취소", role: .cancel) { }
                Button("삭제", role: .destructive) {
                    if let persona = personaToDelete {
                        Task {
                            await viewModel.deletePersona(persona.id)
                        }
                    }
                }
            } message: {
                Text("'\(personaToDelete?.nickname ?? "")'를 삭제하시겠습니까?")
            }
            .refreshable {
                await viewModel.loadData()
            }
            .onAppear {
                Task {
                    await viewModel.loadData()
                    await loadSelectedPersonas()
                }
            }
        }
    }

    // MARK: - Helper Methods

    private func toggleSelectionMode() {
        isSelectionMode.toggle()
        if !isSelectionMode {
            selectedPersonaIds.removeAll()
        }
    }

    private func toggleSelection(for personaId: String) {
        if selectedPersonaIds.contains(personaId) {
            selectedPersonaIds.remove(personaId)
        } else {
            // 최대 5개까지만 선택 가능
            if selectedPersonaIds.count < 5 {
                selectedPersonaIds.insert(personaId)
            } else {
                viewModel.errorMessage = "최대 5개까지만 선택할 수 있습니다"
                DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
                    viewModel.errorMessage = nil
                }
            }
        }
    }

    private func loadSelectedPersonas() async {
        do {
            let selected = try await SupabaseManager.shared.fetchSelectedPersonas()
            selectedPersonaIds = Set(selected.map { $0.id })
        } catch {
            print("  Failed to load selected personas: \(error)")
        }
    }

    private func saveSelection() async {
        do {
            let personaIdsArray = Array(selectedPersonaIds)
            try await SupabaseManager.shared.setSelectedPersonas(personaIds: personaIdsArray)

            viewModel.errorMessage = " 선택이 저장되었습니다"
            isSelectionMode = false

            DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
                viewModel.errorMessage = nil
            }
        } catch {
            viewModel.errorMessage = "선택 저장에 실패했습니다"
            print("  Failed to save selection: \(error)")

            DispatchQueue.main.asyncAfter(deadline: .now() + 2) {
                viewModel.errorMessage = nil
            }
        }
    }
}

/// 채팅방 셀 컴포넌트 (채팅 앱 느낌)
struct ChatRoomCell: View {
    let persona: Persona
    let adjectives: [Adjective]
    let onEdit: () -> Void
    let onDelete: () -> Void
    var isSelectionMode: Bool = false
    var isSelected: Bool = false

    var body: some View {
        HStack(spacing: 16) {
            // 체크박스 (선택 모드일 때만 표시)
            if isSelectionMode {
                Image(systemName: isSelected ? "checkmark.circle.fill" : "circle")
                    .font(.system(size: 24))
                    .foregroundColor(isSelected ? Color(hex: "A50034") : .gray.opacity(0.3))
            }

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
                HStack {
                    // 페르소나 이름
                    Text(persona.nickname)
                        .font(.system(size: 17, weight: .semibold))
                        .foregroundColor(.black)

                    Spacer()

                    // 메뉴 버튼 (선택 모드가 아닐 때만 표시)
                    if !isSelectionMode {
                        Menu {
                            Button(action: onEdit) {
                                Label("편집", systemImage: "pencil")
                            }
                            Button(role: .destructive, action: onDelete) {
                                Label("삭제", systemImage: "trash")
                            }
                        } label: {
                            Image(systemName: "ellipsis")
                                .font(.system(size: 14))
                                .foregroundColor(.gray)
                                .frame(width: 30, height: 30)
                        }
                    }
                }

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

            // 읽지 않은 메시지 표시 (나중에 추가 가능)
            Spacer()
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 12)
        .background(Color.white)
        .contentShape(Rectangle())
    }
}

/// Flow layout for tags
struct FlowLayout<Content: View>: View {
    let spacing: CGFloat
    let content: () -> Content

    @State private var totalHeight: CGFloat = 0

    init(spacing: CGFloat = 8, @ViewBuilder content: @escaping () -> Content) {
        self.spacing = spacing
        self.content = content
    }

    var body: some View {
        VStack {
            GeometryReader { geometry in
                self.generateContent(in: geometry)
            }
        }
        .frame(height: totalHeight)
    }

    private func generateContent(in g: GeometryProxy) -> some View {
        var width = CGFloat.zero
        var height = CGFloat.zero

        return ZStack(alignment: .topLeading) {
            content()
                .padding(.trailing, spacing)
                .padding(.bottom, spacing)
                .alignmentGuide(.leading, computeValue: { d in
                    if (abs(width - d.width) > g.size.width) {
                        width = 0
                        height -= d.height
                    }
                    let result = width
                    width = 0
                    return result
                })
                .alignmentGuide(.top, computeValue: { d in
                    let result = height
                    height = 0
                    return result
                })
        }
        .background(viewHeightReader($totalHeight))
    }

    private func viewHeightReader(_ binding: Binding<CGFloat>) -> some View {
        return GeometryReader { geometry -> Color in
            let rect = geometry.frame(in: .local)
            DispatchQueue.main.async {
                binding.wrappedValue = rect.size.height
            }
            return .clear
        }
    }
}

/// PersonaListView의 ViewModel
@MainActor
class PersonaListViewModel: ObservableObject {
    @Published var personas: [Persona] = []
    @Published var adjectives: [Adjective] = []

    @Published var isLoading = false
    @Published var errorMessage: String?

    func loadData() async {
        isLoading = true
        errorMessage = nil

        do {
            // Load personas and adjectives in parallel
            async let personasTask = SupabaseManager.shared.fetchPersonas()
            async let adjectivesTask = SupabaseManager.shared.fetchAdjectives()

            personas = try await personasTask
            adjectives = try await adjectivesTask

            print(" Loaded \(personas.count) personas, \(adjectives.count) adjectives")
        } catch {
            errorMessage = "데이터를 불러오는데 실패했습니다"
            print("  Failed to load data: \(error)")
        }

        isLoading = false
    }

    func getAdjectivesFor(persona: Persona) -> [Adjective] {
        return adjectives.filter { persona.adjectiveIds.contains($0.id) }
    }

    func deletePersona(_ personaId: String) async {
        do {
            try await SupabaseManager.shared.deletePersona(personaId: personaId)
            personas.removeAll { $0.id == personaId }

            print(" Deleted persona: \(personaId)")
        } catch {
            errorMessage = "페르소나 삭제 실패"
            print("  Failed to delete persona: \(error)")
        }
    }
}

#Preview {
    PersonaListView()
}
