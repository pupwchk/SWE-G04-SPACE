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

                    Text("Device")
                        .font(.system(size: 32, weight: .bold))
                        .foregroundColor(.black)

                    Text("Manage your connected devices")
                        .font(.system(size: 16))
                        .foregroundColor(.gray)
                }
            }
            .navigationTitle("Device")
            .navigationBarTitleDisplayMode(.inline)
        }
    }
}

#Preview {
    DeviceView()
}
