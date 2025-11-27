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
        Group {
            if viewModel.isLoading {
                // Loading state
                ZStack {
                    Color(hex: "F3DEE5")
                    ProgressView()
                        .progressViewStyle(CircularProgressViewStyle(tint: Color(hex: "A50034")))
                }
                .frame(width: 160, height: 160)
                .cornerRadius(20)
            } else if viewModel.selectedPersonas.isEmpty {
                // Empty state - show add button
                Button(action: {
                    navigateToList = true
                }) {
                    ZStack {
                        Color(hex: "F3DEE5")

                        VStack(spacing: 8) {
                            Image(systemName: "person.crop.circle.badge.plus")
                                .font(.system(size: 36))
                                .foregroundColor(Color(hex: "A50034"))

                            Text("페르소나 선택")
                                .font(.system(size: 14, weight: .medium))
                                .foregroundColor(.black)
                        }
                    }
                    .frame(width: 160, height: 160)
                    .cornerRadius(20)
                }
                .buttonStyle(.plain)
            } else {
                // Show all selected personas
                ForEach(viewModel.selectedPersonas) { persona in
                    Button(action: {
                        navigateToList = true
                    }) {
                        PersonaBubbleCard(
                            persona: persona,
                            adjectives: viewModel.getAdjectivesFor(persona: persona),
                            showCount: false
                        )
                    }
                    .buttonStyle(.plain)
                }
            }
        }
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

/// 개별 페르소나 카드
struct PersonaBubbleCard: View {
    let persona: Persona
    let adjectives: [Adjective]
    let showCount: Bool

    var body: some View {
        ZStack(alignment: .topLeading) {
            // Background with gradient
            LinearGradient(
                gradient: Gradient(colors: [
                    Color(hex: "F3DEE5"),
                    Color(hex: "F8E9EF")
                ]),
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )

            VStack(alignment: .leading, spacing: 0) {
                // Header
                Text("Persona")
                    .font(.system(size: 12, weight: .semibold))
                    .foregroundColor(Color(hex: "A50034").opacity(0.7))
                    .padding(.horizontal, 16)
                    .padding(.top, 14)

                Spacer()

                // Persona name
                Text(persona.nickname)
                    .font(.system(size: 18, weight: .bold))
                    .foregroundColor(.black)
                    .lineLimit(1)
                    .padding(.horizontal, 16)
                    .padding(.bottom, 8)

                // Adjectives
                if !adjectives.isEmpty {
                    ScrollView(.horizontal, showsIndicators: false) {
                        HStack(spacing: 6) {
                            ForEach(adjectives.prefix(2)) { adjective in
                                Text(adjective.adjectiveName)
                                    .font(.system(size: 11, weight: .medium))
                                    .foregroundColor(Color(hex: "A50034"))
                                    .padding(.horizontal, 10)
                                    .padding(.vertical, 5)
                                    .background(Color.white)
                                    .cornerRadius(12)
                                    .shadow(color: Color.black.opacity(0.05), radius: 2, x: 0, y: 1)
                            }

                            // Show "+N" if there are more adjectives
                            if adjectives.count > 2 {
                                Text("+\(adjectives.count - 2)")
                                    .font(.system(size: 11, weight: .semibold))
                                    .foregroundColor(Color(hex: "A50034").opacity(0.6))
                                    .padding(.horizontal, 8)
                                    .padding(.vertical, 5)
                                    .background(Color.white.opacity(0.7))
                                    .cornerRadius(12)
                            }
                        }
                        .padding(.horizontal, 16)
                    }
                    .padding(.bottom, 14)
                } else {
                    Spacer()
                        .frame(height: 14)
                }
            }
        }
        .frame(width: 160, height: 160)
        .cornerRadius(20)
        .shadow(color: Color.black.opacity(0.08), radius: 8, x: 0, y: 4)
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
