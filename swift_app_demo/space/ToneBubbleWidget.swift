//
//  ToneBubbleWidget.swift
//  space
//
//  Created by 임동현 on 11/6/25.
//

import SwiftUI

/// Tone bubble widget with floating animation for tone selection
struct ToneBubbleWidget: View {
    @State private var bubblePositions: [BubbleData] = []
    @Binding var selectedTones: Set<String>
    @State private var navigateToSelection = false
    @StateObject private var toneManager = ToneManager.shared

    let tones = SpeakingTone.allCases.map { $0.rawValue }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(selectedTones.isEmpty ? "말투 선택하기" : selectedTones.joined(separator: ", "))
                .font(.system(size: 16, weight: .regular))
                .foregroundColor(.black)
                .padding(.horizontal, 20)

            NavigationLink(destination: ToneSelectionView(selectedTones: $selectedTones), isActive: $navigateToSelection) {
                EmptyView()
            }

            GeometryReader { geometry in
                ZStack {
                    // Pink background
                    RoundedRectangle(cornerRadius: 20)
                        .fill(Color(hex: "E8C8D8"))

                    // Floating bubbles
                    ForEach(bubblePositions) { bubble in
                        FloatingBubble(
                            text: bubble.text,
                            isSelected: selectedTones.contains(bubble.text),
                            onTap: {
                                toggleTone(bubble.text)
                            }
                        )
                        .position(bubble.position)
                        .animation(
                            .easeInOut(duration: bubble.duration)
                            .repeatForever(autoreverses: true),
                            value: bubble.position
                        )
                    }
                }
                .onAppear {
                    initializeBubbles(in: geometry.size)
                    startAnimation(in: geometry.size)
                }
                .onTapGesture {
                    navigateToSelection = true
                }
            }
            .frame(height: 250)
            .padding(.horizontal, 20)
        }
        .onAppear {
            // Load saved tones
            selectedTones = toneManager.selectedTones
        }
    }

    // MARK: - Bubble Management

    private func initializeBubbles(in size: CGSize) {
        bubblePositions = tones.enumerated().map { index, text in
            let minX: CGFloat = 60
            let maxX = max(minX + 10, size.width - 60)
            let minY: CGFloat = 40
            let maxY = max(minY + 10, size.height - 40)

            let randomX = CGFloat.random(in: minX...maxX)
            let randomY = CGFloat.random(in: minY...maxY)

            return BubbleData(
                id: UUID(),
                text: text,
                position: CGPoint(x: randomX, y: randomY),
                duration: Double.random(in: 3.0...6.0)
            )
        }
    }

    private func startAnimation(in size: CGSize) {
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            bubblePositions = bubblePositions.map { bubble in
                var newBubble = bubble
                let minX: CGFloat = 60
                let maxX = max(minX + 10, size.width - 60)
                let minY: CGFloat = 40
                let maxY = max(minY + 10, size.height - 40)

                let randomX = CGFloat.random(in: minX...maxX)
                let randomY = CGFloat.random(in: minY...maxY)
                newBubble.position = CGPoint(x: randomX, y: randomY)
                return newBubble
            }
        }
    }

    private func toggleTone(_ tone: String) {
        withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) {
            toneManager.toggleTone(tone)
            selectedTones = toneManager.selectedTones
        }
    }
}

#Preview {
    ToneBubbleWidget(selectedTones: .constant([]))
        .background(Color(hex: "F9F9F9"))
}
