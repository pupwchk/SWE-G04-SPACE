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

    var body: some View {
        NavigationStack {
            ZStack {
                // Background
                Color(hex: "F9F9F9")
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
                    ScrollView {
                        LazyVStack(spacing: 16) {
                            ForEach(viewModel.personas) { persona in
                                PersonaCard(
                                    persona: persona,
                                    isActive: viewModel.activePersonaId == persona.id,
                                    adjectives: viewModel.getAdjectivesFor(persona: persona),
                                    onTap: {
                                        Task {
                                            await viewModel.setActivePersona(persona.id)
                                        }
                                    },
                                    onEdit: {
                                        personaToEdit = persona
                                    },
                                    onDelete: {
                                        personaToDelete = persona
                                        showingDeleteAlert = true
                                    }
                                )
                            }

                            // Add button at the end
                            Button(action: {
                                showingEditView = true
                            }) {
                                HStack {
                                    Image(systemName: "plus.circle.fill")
                                        .font(.system(size: 20))
                                    Text("페르소나 추가")
                                        .font(.system(size: 16, weight: .medium))
                                }
                                .foregroundColor(Color(hex: "A50034"))
                                .frame(maxWidth: .infinity)
                                .padding(.vertical, 16)
                                .background(Color.white)
                                .cornerRadius(12)
                            }
                        }
                        .padding(.horizontal, 20)
                        .padding(.top, 16)
                        .padding(.bottom, 40)
                    }
                }

                // Error message
                if let errorMessage = viewModel.errorMessage {
                    VStack {
                        Spacer()
                        Text(errorMessage)
                            .font(.system(size: 14))
                            .foregroundColor(.white)
                            .padding()
                            .background(Color.red)
                            .cornerRadius(12)
                            .padding()
                    }
                }
            }
            .navigationTitle("페르소나")
            .navigationBarTitleDisplayMode(.large)
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
                }
            }
        }
    }
}

/// 페르소나 카드 컴포넌트
struct PersonaCard: View {
    let persona: Persona
    let isActive: Bool
    let adjectives: [Adjective]
    let onTap: () -> Void
    let onEdit: () -> Void
    let onDelete: () -> Void

    var body: some View {
        Button(action: onTap) {
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    // Nickname
                    Text(persona.nickname)
                        .font(.system(size: 20, weight: .bold))
                        .foregroundColor(.black)

                    Spacer()

                    // Active indicator
                    if isActive {
                        Text("활성")
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(.white)
                            .padding(.horizontal, 10)
                            .padding(.vertical, 4)
                            .background(Color(hex: "A50034"))
                            .cornerRadius(12)
                    }

                    // Menu button
                    Menu {
                        Button(action: onEdit) {
                            Label("편집", systemImage: "pencil")
                        }
                        Button(role: .destructive, action: onDelete) {
                            Label("삭제", systemImage: "trash")
                        }
                    } label: {
                        Image(systemName: "ellipsis")
                            .font(.system(size: 16, weight: .semibold))
                            .foregroundColor(.gray)
                            .padding(8)
                    }
                }

                // Adjective tags
                if !adjectives.isEmpty {
                    FlowLayout(spacing: 8) {
                        ForEach(adjectives) { adjective in
                            SelectedAdjectiveTag(text: adjective.adjectiveName)
                        }
                    }
                }
            }
            .padding(16)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color.white)
            .cornerRadius(12)
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(isActive ? Color(hex: "A50034") : Color.clear, lineWidth: 2)
            )
            .shadow(color: .black.opacity(0.05), radius: 4, x: 0, y: 2)
        }
        .buttonStyle(.plain)
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
    @Published var activePersonaId: String?

    @Published var isLoading = false
    @Published var errorMessage: String?

    func loadData() async {
        isLoading = true
        errorMessage = nil

        do {
            // Load personas and adjectives in parallel
            async let personasTask = SupabaseManager.shared.fetchPersonas()
            async let adjectivesTask = SupabaseManager.shared.fetchAdjectives()
            async let activePersonaTask = SupabaseManager.shared.fetchActivePersona()

            personas = try await personasTask
            adjectives = try await adjectivesTask
            activePersonaId = try await activePersonaTask

            print("✅ Loaded \(personas.count) personas, \(adjectives.count) adjectives")
        } catch {
            errorMessage = "데이터를 불러오는데 실패했습니다"
            print("❌ Failed to load data: \(error)")
        }

        isLoading = false
    }

    func getAdjectivesFor(persona: Persona) -> [Adjective] {
        return adjectives.filter { persona.adjectiveIds.contains($0.id) }
    }

    func setActivePersona(_ personaId: String) async {
        do {
            try await SupabaseManager.shared.setActivePersona(personaId: personaId)
            activePersonaId = personaId
            print("✅ Set active persona: \(personaId)")
        } catch {
            errorMessage = "활성 페르소나 설정 실패"
            print("❌ Failed to set active persona: \(error)")
        }
    }

    func deletePersona(_ personaId: String) async {
        do {
            try await SupabaseManager.shared.deletePersona(personaId: personaId)
            personas.removeAll { $0.id == personaId }
            if activePersonaId == personaId {
                activePersonaId = nil
            }
            print("✅ Deleted persona: \(personaId)")
        } catch {
            errorMessage = "페르소나 삭제 실패"
            print("❌ Failed to delete persona: \(error)")
        }
    }
}

#Preview {
    PersonaListView()
}
