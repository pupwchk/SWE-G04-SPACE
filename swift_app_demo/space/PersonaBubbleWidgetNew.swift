//
//  PersonaBubbleWidgetNew.swift
//  space
//
//  새로운 페르소나 위젯 (Supabase 기반)

import SwiftUI

/// 페르소나 위젯 - 활성 페르소나를 보여주고 페르소나 리스트로 이동
struct PersonaBubbleWidgetNew: View {
    @StateObject private var viewModel = PersonaBubbleWidgetViewModel()
    @State private var navigateToList = false

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(viewModel.activePersona?.nickname ?? "Choose persona")
                .font(.system(size: 16, weight: .regular))
                .foregroundColor(.black)
                .padding(.horizontal, 20)

            Button(action: {
                navigateToList = true
            }) {
                ZStack {
                    // Pink background
                    RoundedRectangle(cornerRadius: 20)
                        .fill(Color(hex: "E8C8D8"))

                    if viewModel.isLoading {
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: Color(hex: "A50034")))
                    } else if let persona = viewModel.activePersona, !viewModel.adjectives.isEmpty {
                        // Show adjective tags
                        VStack(spacing: 8) {
                            FlowLayout(spacing: 8) {
                                ForEach(viewModel.adjectives) { adjective in
                                    SelectedAdjectiveTag(text: adjective.adjectiveName)
                                }
                            }
                        }
                        .padding(16)
                    } else {
                        // Empty state - prompt to create persona
                        VStack(spacing: 12) {
                            Image(systemName: "person.crop.circle.badge.plus")
                                .font(.system(size: 40))
                                .foregroundColor(Color(hex: "A50034"))

                            Text("페르소나를 생성하세요")
                                .font(.system(size: 16, weight: .medium))
                                .foregroundColor(Color(hex: "A50034"))
                        }
                    }
                }
                .frame(height: 180)
            }
            .buttonStyle(.plain)
            .padding(.horizontal, 20)
            .sheet(isPresented: $navigateToList) {
                PersonaListView()
            }
        }
        .onAppear {
            Task {
                await viewModel.loadActivePersona()
            }
        }
    }
}

/// PersonaBubbleWidgetNew의 ViewModel
@MainActor
class PersonaBubbleWidgetViewModel: ObservableObject {
    @Published var activePersona: Persona?
    @Published var adjectives: [Adjective] = []
    @Published var isLoading = false

    func loadActivePersona() async {
        isLoading = true

        do {
            // Load active persona ID
            if let activePersonaId = try await SupabaseManager.shared.fetchActivePersona() {
                // Load all personas to find the active one
                let personas = try await SupabaseManager.shared.fetchPersonas()
                activePersona = personas.first { $0.id == activePersonaId }

                // Load adjectives for the active persona
                if let persona = activePersona {
                    let allAdjectives = try await SupabaseManager.shared.fetchAdjectives()
                    adjectives = allAdjectives.filter { persona.adjectiveIds.contains($0.id) }
                }
            }
        } catch {
            print("❌ Failed to load active persona: \(error)")
        }

        isLoading = false
    }
}

#Preview {
    PersonaBubbleWidgetNew()
        .background(Color(hex: "F9F9F9"))
}
