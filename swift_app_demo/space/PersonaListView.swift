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
                    VStack(spacing: 0) {
                        // Selection count header
                        HStack {
                            Text("선택된 페르소나: \(viewModel.selectedPersonaIds.count)/5")
                                .font(.system(size: 14, weight: .medium))
                                .foregroundColor(Color(hex: "A50034"))

                            Spacer()

                            if !viewModel.selectedPersonaIds.isEmpty {
                                Button("선택 저장") {
                                    Task {
                                        await viewModel.saveSelectedPersonas()
                                    }
                                }
                                .font(.system(size: 14, weight: .semibold))
                                .foregroundColor(.white)
                                .padding(.horizontal, 16)
                                .padding(.vertical, 8)
                                .background(Color(hex: "A50034"))
                                .cornerRadius(20)
                            }
                        }
                        .padding(.horizontal, 20)
                        .padding(.vertical, 12)
                        .background(Color.white)

                        ScrollView {
                            LazyVStack(spacing: 16) {
                                ForEach(viewModel.personas) { persona in
                                    PersonaCard(
                                        persona: persona,
                                        isSelected: viewModel.selectedPersonaIds.contains(persona.id),
                                        adjectives: viewModel.getAdjectivesFor(persona: persona),
                                        onTap: {
                                            viewModel.togglePersonaSelection(persona.id)
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
    let isSelected: Bool
    let adjectives: [Adjective]
    let onTap: () -> Void
    let onEdit: () -> Void
    let onDelete: () -> Void

    var body: some View {
        Button(action: onTap) {
            HStack(spacing: 12) {
                // Selection checkbox
                Image(systemName: isSelected ? "checkmark.circle.fill" : "circle")
                    .font(.system(size: 24))
                    .foregroundColor(isSelected ? Color(hex: "A50034") : .gray.opacity(0.3))

                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        // Nickname
                        Text(persona.nickname)
                            .font(.system(size: 18, weight: .bold))
                            .foregroundColor(.black)

                        Spacer()

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
            }
            .padding(16)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(Color.white)
            .cornerRadius(12)
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(isSelected ? Color(hex: "A50034") : Color.clear, lineWidth: 2)
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
    @Published var selectedPersonaIds: [String] = [] // Multi-selection support
    private let maxSelection = 5

    @Published var isLoading = false
    @Published var errorMessage: String?

    func loadData() async {
        isLoading = true
        errorMessage = nil

        do {
            // Load personas, adjectives, and selected personas in parallel
            async let personasTask = SupabaseManager.shared.fetchPersonas()
            async let adjectivesTask = SupabaseManager.shared.fetchAdjectives()
            async let selectedPersonasTask = SupabaseManager.shared.fetchSelectedPersonas()

            personas = try await personasTask
            adjectives = try await adjectivesTask
            let selectedPersonas = try await selectedPersonasTask

            // Extract IDs from selected personas
            selectedPersonaIds = selectedPersonas.map { $0.id }

            print("✅ Loaded \(personas.count) personas, \(adjectives.count) adjectives, \(selectedPersonaIds.count) selected")
        } catch {
            errorMessage = "데이터를 불러오는데 실패했습니다"
            print("❌ Failed to load data: \(error)")
        }

        isLoading = false
    }

    func getAdjectivesFor(persona: Persona) -> [Adjective] {
        return adjectives.filter { persona.adjectiveIds.contains($0.id) }
    }

    /// Toggle persona selection (max 5)
    func togglePersonaSelection(_ personaId: String) {
        if let index = selectedPersonaIds.firstIndex(of: personaId) {
            // Deselect
            selectedPersonaIds.remove(at: index)
        } else {
            // Select (if not at max)
            if selectedPersonaIds.count < maxSelection {
                selectedPersonaIds.append(personaId)
            } else {
                errorMessage = "최대 5개까지만 선택할 수 있습니다"
                // Clear error after 2 seconds
                Task {
                    try? await Task.sleep(nanoseconds: 2_000_000_000)
                    errorMessage = nil
                }
            }
        }
    }

    /// Save selected personas to database
    func saveSelectedPersonas() async {
        guard !selectedPersonaIds.isEmpty else { return }

        do {
            try await SupabaseManager.shared.setSelectedPersonas(personaIds: selectedPersonaIds)
            print("✅ Saved \(selectedPersonaIds.count) selected personas")

            // Show success message
            errorMessage = "✅ 선택이 저장되었습니다"

            // Clear success message after 2 seconds
            Task {
                try? await Task.sleep(nanoseconds: 2_000_000_000)
                errorMessage = nil
            }
        } catch {
            errorMessage = "❌ 선택 저장 실패"
            print("❌ Failed to save selected personas: \(error)")

            // Clear error message after 3 seconds
            Task {
                try? await Task.sleep(nanoseconds: 3_000_000_000)
                errorMessage = nil
            }
        }
    }

    func deletePersona(_ personaId: String) async {
        do {
            try await SupabaseManager.shared.deletePersona(personaId: personaId)
            personas.removeAll { $0.id == personaId }

            // Also remove from selection if it was selected
            if let index = selectedPersonaIds.firstIndex(of: personaId) {
                selectedPersonaIds.remove(at: index)
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
