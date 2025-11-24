//
//  PersonaBubbleWidgetNew.swift
//  space
//
//  새로운 페르소나 위젯 (Supabase 기반)

import SwiftUI

/// 페르소나 위젯 - 선택된 페르소나들을 보여주고 페르소나 리스트로 이동
struct PersonaBubbleWidgetNew: View {
    @StateObject private var viewModel = PersonaBubbleWidgetViewModel()
    @State private var navigateToList = false

    var body: some View {
        Button(action: {
            navigateToList = true
        }) {
            ZStack {
                // Background
                Color(hex: "F3DEE5")

                if viewModel.isLoading {
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: Color(hex: "A50034")))
                } else if let firstPersona = viewModel.selectedPersonas.first {
                    // Show first selected persona
                    VStack(alignment: .leading, spacing: 8) {
                        HStack {
                            Text("Persona")
                                .font(.system(size: 13, weight: .semibold))
                                .foregroundColor(.black)

                            Spacer()

                            // Count badge
                            if viewModel.selectedPersonas.count > 1 {
                                Text("+\(viewModel.selectedPersonas.count - 1)")
                                    .font(.system(size: 11, weight: .semibold))
                                    .foregroundColor(Color(hex: "A50034"))
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 4)
                                    .background(Color.white.opacity(0.8))
                                    .cornerRadius(8)
                            }
                        }
                        .padding(.horizontal, 12)
                        .padding(.top, 12)

                        Spacer()

                        // Persona name
                        Text(firstPersona.nickname)
                            .font(.system(size: 16, weight: .bold))
                            .foregroundColor(.black)
                            .padding(.horizontal, 12)

                        // Adjectives
                        let adjectives = viewModel.getAdjectivesFor(persona: firstPersona)
                        if !adjectives.isEmpty {
                            FlowLayout(spacing: 6) {
                                ForEach(adjectives.prefix(3)) { adjective in
                                    Text(adjective.adjectiveName)
                                        .font(.system(size: 10))
                                        .foregroundColor(Color(hex: "A50034"))
                                        .padding(.horizontal, 8)
                                        .padding(.vertical, 4)
                                        .background(Color.white.opacity(0.8))
                                        .cornerRadius(8)
                                }
                            }
                            .padding(.horizontal, 12)
                        }

                        Spacer()
                    }
                } else {
                    // Empty state
                    VStack(spacing: 8) {
                        Image(systemName: "person.crop.circle.badge.plus")
                            .font(.system(size: 36))
                            .foregroundColor(Color(hex: "A50034"))

                        Text("페르소나 선택")
                            .font(.system(size: 14, weight: .medium))
                            .foregroundColor(.black)
                    }
                }
            }
            .frame(width: 160, height: 160)
            .cornerRadius(20)
        }
        .buttonStyle(.plain)
        .sheet(isPresented: $navigateToList, onDismiss: {
            Task {
                await viewModel.loadSelectedPersonas()
            }
        }) {
            PersonaListView()
        }
        .onAppear {
            Task {
                await viewModel.loadSelectedPersonas()
            }
        }
    }
}

/// PersonaBubbleWidgetNew의 ViewModel
@MainActor
class PersonaBubbleWidgetViewModel: ObservableObject {
    @Published var selectedPersonas: [Persona] = []
    @Published var allAdjectives: [Adjective] = []
    @Published var isLoading = false

    func loadSelectedPersonas() async {
        isLoading = true

        do {
            // Load selected personas
            selectedPersonas = try await SupabaseManager.shared.fetchSelectedPersonas()

            // Load all adjectives
            allAdjectives = try await SupabaseManager.shared.fetchAdjectives()

            print("✅ Widget loaded \(selectedPersonas.count) selected personas")
        } catch {
            print("❌ Failed to load selected personas: \(error)")
        }

        isLoading = false
    }

    func getAdjectivesFor(persona: Persona) -> [Adjective] {
        return allAdjectives.filter { persona.adjectiveIds.contains($0.id) }
    }
}

#Preview {
    PersonaBubbleWidgetNew()
        .background(Color(hex: "F9F9F9"))
}
