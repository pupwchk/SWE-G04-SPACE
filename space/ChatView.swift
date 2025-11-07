//
//  ChatView.swift
//  space
//
//  Created by 임동현 on 11/6/25.
//

import SwiftUI

/// Chat screen - messaging and communication
struct ChatView: View {
    var body: some View {
        NavigationStack {
            ZStack {
                Color(hex: "F9F9F9")
                    .ignoresSafeArea()

                VStack(spacing: 20) {
                    Image(systemName: "message.fill")
                        .font(.system(size: 80))
                        .foregroundColor(Color(hex: "A50034"))

                    Text("Chat")
                        .font(.system(size: 32, weight: .bold))
                        .foregroundColor(.black)

                    Text("Messages and conversations")
                        .font(.system(size: 16))
                        .foregroundColor(.gray)
                }
            }
            .navigationTitle("Chat")
            .navigationBarTitleDisplayMode(.inline)
        }
    }
}

#Preview {
    ChatView()
}
