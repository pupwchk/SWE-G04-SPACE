//
//  DeviceView.swift
//  space
//
//  Created by 임동현 on 11/6/25.
//

import SwiftUI

/// Device screen - manages connected devices
struct DeviceView: View {
    var body: some View {
        NavigationStack {
            ZStack {
                Color(hex: "F9F9F9")
                    .ignoresSafeArea()

                VStack(spacing: 20) {
                    Image(systemName: "laptopcomputer")
                        .font(.system(size: 80))
                        .foregroundColor(Color(hex: "A50034"))

                    Text("기기")
                        .font(.system(size: 32, weight: .bold))
                        .foregroundColor(.black)

                    Text("연결된 기기를 관리하세요")
                        .font(.system(size: 16))
                        .foregroundColor(.gray)
                }
            }
            .navigationTitle("기기")
            .navigationBarTitleDisplayMode(.inline)
        }
    }
}

#Preview {
    DeviceView()
}
