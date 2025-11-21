//
//  PersonalWidget.swift
//  space
//
//  Created by 임동현 on 11/6/25.
//

import SwiftUI

/// Widget showing selected personas in bubble format (like PersonaBubbleWidget)
struct PersonalWidget: View {
    let personas: Set<String>
    @State private var bubblePositions: [PersonalBubbleData] = []

    var body: some View {
        GeometryReader { geometry in
            ZStack {
                // Pink background
                Color(hex: "E8C8D8")
                    .cornerRadius(20)

                // Floating bubbles
                ForEach(bubblePositions) { bubble in
                    FloatingBubble(
                        text: bubble.text,
                        isSelected: personas.contains(bubble.text),
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
            .onAppear {
                initializeBubbles(in: geometry.size)
                startAnimation(in: geometry.size)
            }
        }
        .frame(width: 160, height: 160)
    }

    // MARK: - Bubble Management

    private func initializeBubbles(in size: CGSize) {
        let personaArray = Array(personas)
        bubblePositions = personaArray.enumerated().map { index, text in
            let minX: CGFloat = 40
            let maxX = max(minX + 10, size.width - 40)
            let minY: CGFloat = 30
            let maxY = max(minY + 10, size.height - 30)

            let randomX = CGFloat.random(in: minX...maxX)
            let randomY = CGFloat.random(in: minY...maxY)

            return PersonalBubbleData(
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

// MARK: - Bubble Data Model for PersonalWidget

struct PersonalBubbleData: Identifiable {
    let id: UUID
    let text: String
    var position: CGPoint
    var duration: Double
}

#Preview {
    PersonalWidget(personas: ["Developer", "Running", "Webtoon"])
        .background(Color(hex: "F9F9F9"))
}
