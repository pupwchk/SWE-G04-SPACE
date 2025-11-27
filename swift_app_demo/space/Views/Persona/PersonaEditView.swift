//
//  PersonaEditView.swift
//  space
//
//  페르소나 생성/편집 화면

import SwiftUI

/// 페르소나 생성/편집 화면
struct PersonaEditView: View {
    @Environment(\.dismiss) var dismiss
    @StateObject private var viewModel: PersonaEditViewModel

    init(persona: Persona? = nil) {
        _viewModel = StateObject(wrappedValue: PersonaEditViewModel(persona: persona))
    }

    var body: some View {
        ZStack {
            // Burgundy gradient background
            LinearGradient(
                gradient: Gradient(colors: [
                    Color(hex: "8B1538"),
                    Color(hex: "A50034")
                ]),
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()

            ScrollView(showsIndicators: false) {
                VStack(alignment: .leading, spacing: 24) {
                    // Title
                    Text(viewModel.isEditMode ? "페르소나 편집" : "페르소나 생성")
                        .font(.system(size: 40, weight: .bold))
                        .foregroundColor(.white)
                        .padding(.top, 20)
                        .padding(.horizontal, 20)

                    // Nickname input
                    VStack(alignment: .leading, spacing: 12) {
                        Text("닉네임")
                            .font(.system(size: 17, weight: .semibold))
                            .foregroundColor(.white)

                        TextField("페르소나 닉네임을 입력하세요", text: $viewModel.nickname)
                            .font(.system(size: 16))
                            .foregroundColor(.black)
                            .padding()
                            .background(Color.white)
                            .cornerRadius(12)
                    }
                    .padding(.horizontal, 20)

                    // Adjectives selection
                    VStack(alignment: .leading, spacing: 12) {
                        Text("특성 선택")
                            .font(.system(size: 17, weight: .semibold))
                            .foregroundColor(.white)

                        if viewModel.isLoadingAdjectives {
                            ProgressView()
                                .progressViewStyle(CircularProgressViewStyle(tint: .white))
                                .frame(maxWidth: .infinity, alignment: .center)
                                .padding()
                        } else {
                            FlexibleView(
                                data: viewModel.adjectives,
                                spacing: 10,
                                alignment: .leading
                            ) { adjective in
                                AdjectiveTag(
                                    adjective: adjective,
                                    isSelected: viewModel.selectedAdjectiveIds.contains(adjective.id),
                                    action: {
                                        viewModel.toggleAdjective(adjective.id)
                                    }
                                )
                            }
                        }
                    }
                    .padding(.horizontal, 20)

                    // Custom instructions
                    VStack(alignment: .leading, spacing: 12) {
                        Text("기타 지침 (선택)")
                            .font(.system(size: 17, weight: .semibold))
                            .foregroundColor(.white)

                        TextEditor(text: $viewModel.customInstructions)
                            .font(.system(size: 16))
                            .foregroundColor(.black)
                            .frame(minHeight: 120)
                            .padding(8)
                            .background(Color.white)
                            .cornerRadius(12)
                            .overlay(
                                Group {
                                    if viewModel.customInstructions.isEmpty {
                                        Text("추가 지침을 자유롭게 작성하세요")
                                            .font(.system(size: 16))
                                            .foregroundColor(.gray.opacity(0.6))
                                            .padding(.top, 16)
                                            .padding(.leading, 12)
                                            .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
                                            .allowsHitTesting(false)
                                    }
                                }
                            )
                    }
                    .padding(.horizontal, 20)

                    // Save button
                    Button(action: {
                        Task {
                            await viewModel.savePersona()
                            if viewModel.saveSuccess {
                                dismiss()
                            }
                        }
                    }) {
                        if viewModel.isSaving {
                            ProgressView()
                                .progressViewStyle(CircularProgressViewStyle(tint: Color(hex: "A50034")))
                                .frame(maxWidth: .infinity)
                                .padding(.vertical, 16)
                        } else {
                            Text("저장하기")
                                .font(.system(size: 18, weight: .semibold))
                                .foregroundColor(viewModel.canSave ? Color(hex: "A50034") : .white.opacity(0.5))
                                .frame(maxWidth: .infinity)
                                .padding(.vertical, 16)
                        }
                    }
                    .background(
                        viewModel.canSave ? Color.white : Color.white.opacity(0.2)
                    )
                    .cornerRadius(25)
                    .disabled(!viewModel.canSave || viewModel.isSaving)
                    .padding(.horizontal, 20)
                    .padding(.top, 12)

                    // Error message
                    if let errorMessage = viewModel.errorMessage {
                        Text(errorMessage)
                            .font(.system(size: 14))
                            .foregroundColor(.red)
                            .padding(.horizontal, 20)
                    }

                    Spacer(minLength: 40)
                }
            }
        }
        .navigationBarTitleDisplayMode(.inline)
        .navigationBarBackButtonHidden(true)
        .toolbar {
            ToolbarItem(placement: .navigationBarLeading) {
                Button(action: { dismiss() }) {
                    Image(systemName: "chevron.left")
                        .foregroundColor(.white)
                        .font(.system(size: 18, weight: .semibold))
                }
            }
        }
        .onAppear {
            Task {
                await viewModel.loadAdjectives()
            }
        }
    }
}

/// PersonaEditView의 ViewModel
@MainActor
class PersonaEditViewModel: ObservableObject {
    @Published var nickname: String = ""
    @Published var selectedAdjectiveIds: Set<String> = []
    @Published var customInstructions: String = ""
    @Published var adjectives: [Adjective] = []

    @Published var isLoadingAdjectives = false
    @Published var isSaving = false
    @Published var saveSuccess = false
    @Published var errorMessage: String?

    let isEditMode: Bool
    let existingPersona: Persona?

    var canSave: Bool {
        !nickname.isEmpty && !selectedAdjectiveIds.isEmpty
    }

    init(persona: Persona?) {
        self.existingPersona = persona
        self.isEditMode = persona != nil

        if let persona = persona {
            self.nickname = persona.nickname
            self.selectedAdjectiveIds = Set(persona.adjectiveIds)
            self.customInstructions = persona.customInstructions ?? ""
        }
    }

    func loadAdjectives() async {
        isLoadingAdjectives = true
        errorMessage = nil

        do {
            adjectives = try await SupabaseManager.shared.fetchAdjectives()
        } catch {
            errorMessage = "형용사를 불러오는데 실패했습니다: \(error.localizedDescription)"
            print("  Failed to load adjectives: \(error)")
        }

        isLoadingAdjectives = false
    }

    func toggleAdjective(_ id: String) {
        if selectedAdjectiveIds.contains(id) {
            selectedAdjectiveIds.remove(id)
        } else {
            selectedAdjectiveIds.insert(id)
        }
    }

    func savePersona() async {
        guard canSave else { return }

        isSaving = true
        errorMessage = nil
        saveSuccess = false

        do {
            let adjectiveIdsArray = Array(selectedAdjectiveIds)

            if let persona = existingPersona {
                // Update existing persona
                try await SupabaseManager.shared.updatePersona(
                    personaId: persona.id,
                    nickname: nickname,
                    adjectiveIds: adjectiveIdsArray,
                    customInstructions: customInstructions.isEmpty ? nil : customInstructions
                )
            } else {
                // Create new persona
                _ = try await SupabaseManager.shared.createPersona(
                    nickname: nickname,
                    adjectiveIds: adjectiveIdsArray,
                    customInstructions: customInstructions.isEmpty ? nil : customInstructions
                )
            }

            saveSuccess = true
            print(" Persona saved successfully")
        } catch {
            errorMessage = "저장 실패: \(error.localizedDescription)"
            print("  Failed to save persona: \(error)")
        }

        isSaving = false
    }
}

/// FlexibleView - 동적 그리드 레이아웃
struct FlexibleView<Data: Collection, Content: View>: View where Data.Element: Hashable {
    let data: Data
    let spacing: CGFloat
    let alignment: HorizontalAlignment
    let content: (Data.Element) -> Content

    @State private var totalHeight: CGFloat = 0

    var body: some View {
        VStack(alignment: alignment, spacing: spacing) {
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
            ForEach(Array(data.enumerated()), id: \.element) { index, item in
                content(item)
                    .padding(.trailing, spacing)
                    .padding(.bottom, spacing)
                    .alignmentGuide(.leading, computeValue: { d in
                        if (abs(width - d.width) > g.size.width) {
                            width = 0
                            height -= d.height
                        }
                        let result = width
                        if index == data.count - 1 {
                            width = 0
                        } else {
                            width -= d.width
                        }
                        return result
                    })
                    .alignmentGuide(.top, computeValue: { d in
                        let result = height
                        if index == data.count - 1 {
                            height = 0
                        }
                        return result
                    })
            }
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

#Preview {
    NavigationStack {
        PersonaEditView()
    }
}
