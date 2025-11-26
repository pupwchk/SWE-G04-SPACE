//
//  ContentView.swift
//  space Watch App Watch App
//
//  Created by 임동현 on 11/25/25.
//

import SwiftUI

struct ContentView: View {
    @StateObject private var locationManager = WatchLocationManager.shared
    @StateObject private var connectivityManager = WatchConnectivityManager.shared

    var body: some View {
        NavigationStack {
            if connectivityManager.isAuthenticated {
                // Authenticated View - Show normal interface
                authenticatedView
            } else {
                // Not Authenticated View - Show login prompt
                notAuthenticatedView
            }
        }
    }

    // MARK: - Authenticated View

    private var authenticatedView: some View {
        VStack(spacing: 20) {
            // App Title
            Text("SPACE")
                .font(.system(size: 24, weight: .bold))
                .foregroundColor(Color(hex: "A50034"))

            // Tracking Status
            VStack(spacing: 8) {
                if locationManager.isTracking {
                    HStack {
                        Circle()
                            .fill(Color.green)
                            .frame(width: 8, height: 8)
                        Text("추적 중")
                            .font(.system(size: 14))
                            .foregroundColor(.green)
                    }
                } else {
                    HStack {
                        Circle()
                            .fill(Color.gray)
                            .frame(width: 8, height: 8)
                        Text("대기 중")
                            .font(.system(size: 14))
                            .foregroundColor(.gray)
                    }
                }

                // Phone connection status
                HStack {
                    Image(systemName: connectivityManager.isPhoneReachable ? "iphone.and.arrow.forward" : "iphone.slash")
                        .font(.system(size: 12))
                    Text(connectivityManager.isPhoneReachable ? "iPhone 연결됨" : "iPhone 연결 끊김")
                        .font(.system(size: 12))
                }
                .foregroundColor(connectivityManager.isPhoneReachable ? .green : .gray)
            }

            // Map Navigation Button
            NavigationLink(destination: WatchMapView()) {
                VStack(spacing: 4) {
                    Image(systemName: "map.fill")
                        .font(.system(size: 28))
                    Text("지도")
                        .font(.system(size: 14, weight: .semibold))
                }
                .frame(maxWidth: .infinity)
                .frame(height: 80)
                .background(Color(hex: "A50034"))
                .foregroundColor(.white)
                .cornerRadius(12)
            }
            .buttonStyle(.plain)

            // Quick Stats (if tracking)
            if locationManager.isTracking {
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text("거리:")
                            .font(.system(size: 12))
                            .foregroundColor(.secondary)
                        Spacer()
                        Text(distanceText)
                            .font(.system(size: 12, weight: .semibold))
                    }

                    HStack {
                        Text("포인트:")
                            .font(.system(size: 12))
                            .foregroundColor(.secondary)
                        Spacer()
                        Text("\(locationManager.coordinates.count)")
                            .font(.system(size: 12, weight: .semibold))
                    }
                }
                .padding(8)
                .background(Color.secondary.opacity(0.1))
                .cornerRadius(8)
            }

            Spacer()
        }
        .padding()
    }

    // MARK: - Not Authenticated View

    private var notAuthenticatedView: some View {
        VStack(spacing: 20) {
            Spacer()

            // Lock Icon
            Image(systemName: "lock.fill")
                .font(.system(size: 40))
                .foregroundColor(Color(hex: "A50034"))

            // Title
            Text("SPACE")
                .font(.system(size: 24, weight: .bold))
                .foregroundColor(Color(hex: "A50034"))

            // Message
            VStack(spacing: 8) {
                Text("iPhone 앱에서")
                    .font(.system(size: 14))
                    .foregroundColor(.secondary)

                Text("로그인이 필요합니다")
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(.primary)
            }

            // Connection Status
            HStack {
                Image(systemName: connectivityManager.isPhoneReachable ? "iphone.and.arrow.forward" : "iphone.slash")
                    .font(.system(size: 12))
                Text(connectivityManager.isPhoneReachable ? "iPhone 연결됨" : "iPhone 연결 끊김")
                    .font(.system(size: 12))
            }
            .foregroundColor(connectivityManager.isPhoneReachable ? .green : .gray)
            .padding(.top, 8)

            Spacer()

            // Help Text
            Text("iPhone 앱을 열어 로그인해주세요")
                .font(.system(size: 11))
                .foregroundColor(.secondary)
                .multilineTextAlignment(.center)
                .padding(.horizontal)
        }
        .padding()
    }

    // MARK: - Computed Properties

    private var distanceText: String {
        let km = locationManager.totalDistance / 1000.0
        if km >= 1.0 {
            return String(format: "%.2f km", km)
        } else {
            return String(format: "%.0f m", locationManager.totalDistance)
        }
    }
}

// MARK: - Color Extension

extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 3: // RGB (12-bit)
            (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6: // RGB (24-bit)
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8: // ARGB (32-bit)
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (1, 1, 1, 0)
        }

        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue:  Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}

#Preview {
    ContentView()
}
