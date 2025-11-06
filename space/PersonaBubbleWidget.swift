//
//  PersonaBubbleWidget.swift
//  space
//
//  Created by 임동현 on 11/6/25.
//

import SwiftUI

/// Persona bubble widget with floating animation
struct PersonaBubbleWidget: View {
    @State private var bubblePositions: [BubbleData] = []
    @State private var selectedPersonas: Set<String> = []

    let personas = ["Running", "Webtoon", "Stress", "School", "Sleep", "Developer", "TV", "Walking", "home"]

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("Choose personal")
                .font(.system(size: 16, weight: .regular))
                .foregroundColor(.black)
                .padding(.horizontal, 20)

            GeometryReader { geometry in
                ZStack {
                    // Pink background
                    RoundedRectangle(cornerRadius: 20)
                        .fill(Color(hex: "E8C8D8"))

                    // Floating bubbles
                    ForEach(bubblePositions) { bubble in
                        FloatingBubble(
                            text: bubble.text,
                            isSelected: selectedPersonas.contains(bubble.text),
                            onTap: {
                                togglePersona(bubble.text)
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
            }
            .frame(height: 250)
            .padding(.horizontal, 20)
        }
    }

    // MARK: - Bubble Management

    private func initializeBubbles(in size: CGSize) {
        bubblePositions = personas.enumerated().map { index, text in
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

    private func togglePersona(_ persona: String) {
        withAnimation(.spring(response: 0.3, dampingFraction: 0.7)) {
            if selectedPersonas.contains(persona) {
                selectedPersonas.remove(persona)
            } else {
                selectedPersonas.insert(persona)
            }
        }
    }
}

// MARK: - Bubble Data Model

struct BubbleData: Identifiable {
    let id: UUID
    let text: String
    var position: CGPoint
    var duration: Double
}

#Preview {
    PersonaBubbleWidget()
        .background(Color(hex: "F9F9F9"))
}
