//
//  MenuRow.swift
//  space
//
//  Created by 임동현 on 11/6/25.
//

import SwiftUI

/// Menu row component with icon, title, and chevron
struct MenuRow: View {
    let icon: String
    let title: String
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 16) {
                // Icon
                Image(systemName: icon)
                    .font(.system(size: 24))
                    .foregroundColor(.black)
                    .frame(width: 28, height: 28)

                // Title
                Text(title)
                    .font(.system(size: 17, weight: .regular))
                    .foregroundColor(.black)

                Spacer()

                // Chevron
                Image(systemName: "chevron.right")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(.gray.opacity(0.5))
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 16)
            .background(Color.white)
        }
        .buttonStyle(.plain)
    }
}

#Preview {
    VStack(spacing: 0) {
        MenuRow(icon: "person", title: "My page", action: {})
        Divider().padding(.leading, 64)
        MenuRow(icon: "gearshape", title: "General", action: {})
        Divider().padding(.leading, 64)
        MenuRow(icon: "questionmark.circle", title: "FAQ", action: {})
    }
    .background(Color(hex: "F9F9F9"))
}
