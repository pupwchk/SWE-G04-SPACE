//
//  AddItemWidget.swift
//  space
//
//  Created by 임동현 on 11/6/25.
//

import SwiftUI

/// Reusable widget for adding devices or appliances
struct AddItemWidget: View {
    let title: String
    let action: () -> Void

    @State private var isPressed = false

    var body: some View {
        Button(action: {
            action()
        }) {
            VStack(spacing: 0) {
                Spacer()

                // Plus icon centered
                Image(systemName: "plus")
                    .font(.system(size: 50, weight: .thin))
                    .foregroundColor(Color.white.opacity(0.7))

                Spacer()
            }
            .frame(maxWidth: .infinity)
            .frame(height: 160)
            .background(
                isPressed ? Color(hex: "E8C0CD") : Color(hex: "F3DEE5")
            )
            .cornerRadius(20)
        }
        .buttonStyle(PlainButtonStyle())
        .simultaneousGesture(
            DragGesture(minimumDistance: 0)
                .onChanged { _ in
                    withAnimation(.easeInOut(duration: 0.15)) {
                        isPressed = true
                    }
                }
                .onEnded { _ in
                    withAnimation(.easeInOut(duration: 0.15)) {
                        isPressed = false
                    }
                }
        )
    }
}

#Preview {
    VStack(spacing: 16) {
        AddItemWidget(
            title: "Add devices",
            action: {
                print("Device add tapped")
            }
        )

        AddItemWidget(
            title: "Add home appliances",
            action: {
                print("Appliance add tapped")
            }
        )
    }
    .padding()
    .background(Color(hex: "F9F9F9"))
}
