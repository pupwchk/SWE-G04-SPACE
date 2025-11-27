//
//  SocialLoginButton.swift
//  space
//
//  Created by 임동현 on 11/3/25.
//

import SwiftUI

/// Reusable social login button with circular design and tap animation
struct SocialLoginButton: View {
    let imageName: String
    let action: () -> Void

    @State private var isPressed = false

    var body: some View {
        Button(action: {
            action()
        }) {
            Circle()
                .fill(Color.white)
                .frame(width: 60, height: 60)
                .shadow(color: Color.black.opacity(0.08), radius: 6, x: 0, y: 2)
                .overlay(
                    Image(imageName)
                        .resizable()
                        .scaledToFit()
                        .frame(width: 28, height: 28)
                )
        }
        .scaleEffect(isPressed ? 0.92 : 1.0)
        .animation(.spring(response: 0.3, dampingFraction: 0.6), value: isPressed)
        .simultaneousGesture(
            DragGesture(minimumDistance: 0)
                .onChanged { _ in
                    isPressed = true
                }
                .onEnded { _ in
                    isPressed = false
                }
        )
    }
}

#Preview {
    HStack(spacing: 20) {
        SocialLoginButton(imageName: "btn_google", action: {})
        SocialLoginButton(imageName: "btn_apple", action: {})
        SocialLoginButton(imageName: "btn_naver", action: {})
        SocialLoginButton(imageName: "btn_kakao", action: {})
    }
    .padding()
    .background(Color.gray.opacity(0.1))
}
