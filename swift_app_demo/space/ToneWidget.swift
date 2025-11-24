//
//  ToneWidget.swift
//  space
//
//  Created by 임동현 on 11/6/25.
//

import SwiftUI

/// Widget showing selected tones in bubble format
struct ToneWidget: View {
    let tones: Set<String>
    @State private var bubblePositions: [ToneBubbleData] = []

    var body: some View {
        GeometryReader { geometry in
            ZStack {
                // Pink background
                Color(hex: "E8C8D8")
                    .cornerRadius(20)

                if tones.isEmpty {
                    // Show message when no tones selected
                    VStack(spacing: 8) {
                        Image(systemName: "bubble.left.and.bubble.right")
                            .font(.system(size: 32))
                            .foregroundColor(.white.opacity(0.6))

                        Text("말투를 선택해주세요")
                            .font(.system(size: 14, weight: .medium))
                            .foregroundColor(.white.opacity(0.8))
                    }
                } else {
                    // Floating bubbles for selected tones
                    ForEach(bubblePositions) { bubble in
                        FloatingBubble(
                            text: bubble.text,
                            isSelected: true,
                            onTap: { }
                        )
                        .position(bubble.position)
                        .animation(
                            .easeInOut(duration: bubble.duration)
                            .repeatForever(autoreverses: true),
                            value: bubble.position
                        )
                    }
                }
            }
            .onAppear {
                initializeBubbles(in: geometry.size)
                startAnimation(in: geometry.size)
            }
            .onChange(of: tones) { oldValue, newValue in
                // Reinitialize bubbles when tones change
                initializeBubbles(in: geometry.size)
                startAnimation(in: geometry.size)
            }
        }
        .frame(width: 160, height: 160)
    }

    // MARK: - Bubble Management

    private func initializeBubbles(in size: CGSize) {
        let tonesArray = Array(tones)
        bubblePositions = tonesArray.enumerated().map { index, text in
            let minX: CGFloat = 40
            let maxX = max(minX + 10, size.width - 40)
            let minY: CGFloat = 30
            let maxY = max(minY + 10, size.height - 30)

            let randomX = CGFloat.random(in: minX...maxX)
            let randomY = CGFloat.random(in: minY...maxY)

            return ToneBubbleData(
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
                let minX: CGFloat = 40
                let maxX = max(minX + 10, size.width - 40)
                let minY: CGFloat = 30
                let maxY = max(minY + 10, size.height - 30)

                let randomX = CGFloat.random(in: minX...maxX)
                let randomY = CGFloat.random(in: minY...maxY)
                newBubble.position = CGPoint(x: randomX, y: randomY)
                return newBubble
            }
        }
    }
}

// MARK: - Bubble Data Model for ToneWidget

struct ToneBubbleData: Identifiable {
    let id: UUID
    let text: String
    var position: CGPoint
    var duration: Double
}

#Preview {
    ToneWidget(tones: ["친근한", "밝은", "따뜻한"])
        .background(Color(hex: "F9F9F9"))
}
