//
//  PersonaWidget.swift
//  space
//
//  Widget for displaying selected personas (up to 5)
//

import SwiftUI

/// Persona Widget - Displays selected personas in a fixed-size widget
struct PersonaWidget: View {
    @StateObject private var viewModel = PersonaWidgetViewModel()
    @State private var showPersonaList = false

    var body: some View {
        Button(action: {
            showPersonaList = true
        }) {
            ZStack {
                Color(hex: "F3DEE5")

                if viewModel.isLoading {
                    // Loading state
                    ProgressView()
                        .tint(Color(hex: "A50034"))
                } else if viewModel.selectedPersonas.isEmpty {
                    // Empty state - show prompt to select personas
                    VStack(spacing: 8) {
                        Image(systemName: "person.2.fill")
                            .font(.system(size: 36))
                            .foregroundColor(Color(hex: "A50034"))

                        Text("페르소나 선택")
                            .font(.system(size: 14, weight: .medium))
                            .foregroundColor(.black)
                    }
                } else {
                    // Show selected personas
                    VStack(alignment: .leading, spacing: 8) {
                        Text("My Personas")
                            .font(.system(size: 12, weight: .semibold))
                            .foregroundColor(Color(hex: "A50034"))
                            .padding(.horizontal, 12)
                            .padding(.top, 8)

                        // Persona bubbles
                        ScrollView(.vertical, showsIndicators: false) {
                            VStack(spacing: 6) {
                                ForEach(viewModel.selectedPersonas) { persona in
                                    PersonaBubble(nickname: persona.nickname)
                                }
                            }
                            .padding(.horizontal, 12)
                            .padding(.bottom, 8)
                        }
                    }
                }
            }
            .frame(width: 160, height: 160)
            .cornerRadius(20)
        }
        .buttonStyle(.plain)
        .sheet(isPresented: $showPersonaList) {
            PersonaListView()
        }
        .onAppear {
            Task {
                await viewModel.loadSelectedPersonas()
            }
        }
    }
}

/// Individual persona bubble view
struct PersonaBubble: View {
    let nickname: String

    var body: some View {
        HStack {
            Image(systemName: "person.circle.fill")
                .font(.system(size: 14))
                .foregroundColor(Color(hex: "A50034"))

            Text(nickname)
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(.black)
                .lineLimit(1)

            Spacer()
        }
        .padding(.horizontal, 10)
        .padding(.vertical, 8)
        .background(Color.white.opacity(0.7))
        .cornerRadius(12)
    }
}

/// ViewModel for PersonaWidget
class PersonaWidgetViewModel: ObservableObject {
    @Published var selectedPersonas: [Persona] = []
    @Published var isLoading = false

    /// Load selected personas from Supabase
    func loadSelectedPersonas() async {
        await MainActor.run {
            isLoading = true
        }

        do {
            let personas = try await SupabaseManager.shared.fetchSelectedPersonas()

            await MainActor.run {
                self.selectedPersonas = personas
                self.isLoading = false
            }
        } catch {
            print("  Failed to load selected personas: \(error.localizedDescription)")
            await MainActor.run {
                self.selectedPersonas = []
                self.isLoading = false
            }
        }
    }
}

#Preview {
    PersonaWidget()
        .background(Color(hex: "F9F9F9"))
}
