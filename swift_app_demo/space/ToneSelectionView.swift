//
//  ToneSelectionView.swift
//  space
//
//  Created by 임동현 on 11/6/25.
//

import SwiftUI

/// View for selecting multiple speaking tones
struct ToneSelectionView: View {
    @Environment(\.dismiss) var dismiss
    @Binding var selectedTones: Set<String>
    @StateObject private var toneManager = ToneManager.shared

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
                VStack(alignment: .leading, spacing: 32) {
                    // Title
                    VStack(alignment: .leading, spacing: 8) {
                        Text("말투 선택")
                            .font(.system(size: 40, weight: .bold))
                            .foregroundColor(.white)

                        Text("채팅과 전화에서 사용할 말투를 선택하세요")
                            .font(.system(size: 16, weight: .regular))
                            .foregroundColor(.white.opacity(0.9))
                    }
                    .padding(.top, 20)
                    .padding(.horizontal, 20)

                    // Tone selection grid
                    VStack(spacing: 16) {
                        ForEach(SpeakingTone.allCases) { tone in
                            ToneCard(
                                tone: tone,
                                isSelected: toneManager.selectedTones.contains(tone.rawValue),
                                onToggle: {
                                    withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) {
                                        toneManager.toggleTone(tone.rawValue)
                                    }
                                }
                            )
                        }
                    }
                    .padding(.horizontal, 20)

                    // Save button
                    Button(action: {
                        saveAndDismiss()
                    }) {
                        Text("저장하기")
                            .font(.system(size: 18, weight: .semibold))
                            .foregroundColor(toneManager.selectedTones.isEmpty ? .white.opacity(0.5) : Color(hex: "A50034"))
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 16)
                            .background(
                                toneManager.selectedTones.isEmpty ? Color.white.opacity(0.2) : Color.white
                            )
                            .cornerRadius(25)
                    }
                    .disabled(toneManager.selectedTones.isEmpty)
                    .padding(.horizontal, 20)
                    .padding(.top, 12)

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

            ToolbarItem(placement: .navigationBarTrailing) {
                if !toneManager.selectedTones.isEmpty {
                    Button(action: {
                        withAnimation {
                            toneManager.clearTones()
                        }
                    }) {
                        Text("전체 해제")
                            .font(.system(size: 14, weight: .medium))
                            .foregroundColor(.white)
                    }
                }
            }
        }
        .onAppear {
            // Sync with binding
            selectedTones = toneManager.selectedTones
        }
    }

    // MARK: - Actions

    private func saveAndDismiss() {
        // Update the binding
        selectedTones = toneManager.selectedTones

        print("Saved tones: \(toneManager.selectedTones)")

        // Navigate back to home
        dismiss()
    }
}

// MARK: - Tone Card Component

struct ToneCard: View {
    let tone: SpeakingTone
    let isSelected: Bool
    let onToggle: () -> Void

    var body: some View {
        Button(action: onToggle) {
            HStack(spacing: 16) {
                // Checkmark
                ZStack {
                    Circle()
                        .stroke(Color.white, lineWidth: 2)
                        .frame(width: 28, height: 28)

                    if isSelected {
                        Circle()
                            .fill(Color.white)
                            .frame(width: 28, height: 28)

                        Image(systemName: "checkmark")
                            .font(.system(size: 14, weight: .bold))
                            .foregroundColor(Color(hex: "A50034"))
                    }
                }

                // Tone info
                VStack(alignment: .leading, spacing: 4) {
                    Text(tone.rawValue)
                        .font(.system(size: 18, weight: .semibold))
                        .foregroundColor(.white)

                    Text(tone.description)
                        .font(.system(size: 14, weight: .regular))
                        .foregroundColor(.white.opacity(0.8))
                }

                Spacer()
            }
            .padding(20)
            .background(
                RoundedRectangle(cornerRadius: 16)
                    .fill(isSelected ? Color.white.opacity(0.25) : Color.white.opacity(0.1))
                    .overlay(
                        RoundedRectangle(cornerRadius: 16)
                            .stroke(isSelected ? Color.white : Color.white.opacity(0.3), lineWidth: isSelected ? 2 : 1)
                    )
            )
        }
        .buttonStyle(.plain)
    }
}

#Preview {
    NavigationStack {
        ToneSelectionView(selectedTones: .constant([]))
    }
}
