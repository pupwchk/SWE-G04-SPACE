//
//  FloatingBubble.swift
//  space
//
//  Created by 임동현 on 11/6/25.
//

import SwiftUI

/// Individual floating bubble for persona selection
struct FloatingBubble: View {
    let text: String
    let isSelected: Bool
    let onTap: () -> Void

    var body: some View {
        Button(action: onTap) {
            Text(text)
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(isSelected ? .white : Color.white.opacity(0.85))
                .padding(.horizontal, 14)
                .padding(.vertical, 8)
                .background(
                    isSelected ?
                    Color(hex: "8B1538") :
                    Color.white.opacity(0.0)
                )
                .cornerRadius(18)
                .overlay(
                    RoundedRectangle(cornerRadius: 18)
                        .stroke(
                            Color.white.opacity(0.7),
                            lineWidth: 1.5
                        )
                )
        }
        .buttonStyle(PlainButtonStyle())
    }
}

#Preview {
    VStack(spacing: 20) {
        FloatingBubble(text: "편안함", isSelected: false, onTap: {})
        FloatingBubble(text: "활동적", isSelected: true, onTap: {})
    }
    .padding()
    .background(Color(hex: "F9F9F9"))
}
