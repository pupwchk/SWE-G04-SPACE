//
//  HomeView.swift
//  space
//
//  Created by 임동현 on 11/6/25.
//

import SwiftUI

/// Home screen - main dashboard view
struct HomeView: View {
    @State private var hasAppliances = true
    @StateObject private var deviceManager = DeviceManager.shared
    @StateObject private var connectivityManager = WatchConnectivityManager.shared

    let sampleAppliances = [
        (icon: "wind", title: "거실", subtitle: "에어컨", status: "24°C · 냉방"),
        (icon: "lightbulb.fill", title: "거실", subtitle: "조명", status: "밝기 70%"),
        (icon: "aqi.medium", title: "거실", subtitle: "공기청정기", status: "자동 · 공기질 좋음"),
        (icon: "drop.circle.fill", title: "안방", subtitle: "제습기", status: "목표 45%"),
        (icon: "drop.fill", title: "아이방", subtitle: "가습기", status: "목표 50%"),
        (icon: "tv.fill", title: "거실", subtitle: "TV", status: "OTT · 볼륨 18")
    ]

    var body: some View {
        NavigationStack {
            ScrollView(showsIndicators: false) {
                VStack(alignment: .leading, spacing: 24) {
                    // Section 1: 3 Fixed Widgets (Timeline, State, Persona)
                    VStack(alignment: .leading, spacing: 12) {
                        HStack {
                            Text("나의 현황")
                                .font(.system(size: 18, weight: .semibold))
                                .foregroundColor(.black)

                            Spacer()
                        }
                        .padding(.horizontal, 20)

                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack(spacing: 16) {
                                TimelineWidget()
                                StateWidget()
                                PersonaBubbleWidgetNew()
                            }
                            .padding(.horizontal, 20)
                        }
                    }

                    // Device section - will be populated by WatchConnectivityManager and AudioDeviceManager
                    VStack(alignment: .leading, spacing: 12) {
                        HStack {
                            Text("기기")
                                .font(.system(size: 18, weight: .semibold))
                                .foregroundColor(.black)

                            Spacer()
                        }
                        .padding(.horizontal, 20)

                        // Connected devices
                        if deviceManager.connectedDevices.isEmpty {
                            // No devices connected
                            VStack(spacing: 8) {
                                Image(systemName: "applewatch.slash")
                                    .font(.system(size: 32))
                                    .foregroundColor(.gray.opacity(0.5))

                                Text("연결된 기기 없음")
                                    .font(.system(size: 14))
                                    .foregroundColor(.gray)

                                Text("Watch 앱을 실행하면 자동으로 표시됩니다")
                                    .font(.system(size: 12))
                                    .foregroundColor(.gray.opacity(0.7))
                            }
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 24)
                            .padding(.horizontal, 20)
                        } else {
                            // Show connected devices
                            VStack(spacing: 12) {
                                ForEach(deviceManager.connectedDevices) { device in
                                    deviceCard(device: device)
                                }
                            }
                            .padding(.horizontal, 20)
                        }
                    }

                    // Appliance section
                    VStack(alignment: .leading, spacing: 12) {
                        HStack {
                            Text("가전제품")
                                .font(.system(size: 18, weight: .semibold))
                                .foregroundColor(.black)

                            Spacer()

                            if hasAppliances {
                                Button(action: {
                                    withAnimation {
                                        hasAppliances = false
                                    }
                                }) {
                                    Image(systemName: "plus.circle.fill")
                                        .font(.system(size: 22))
                                        .foregroundColor(Color(hex: "A50034"))
                                }
                            }
                        }
                        .padding(.horizontal, 20)

                        if hasAppliances {
                            ScrollView(.horizontal, showsIndicators: false) {
                                HStack(spacing: 16) {
                                    ForEach(0..<sampleAppliances.count, id: \.self) { index in
                                        ApplianceCard(
                                                icon: sampleAppliances[index].icon,
                                                title: sampleAppliances[index].title,
                                                subtitle: sampleAppliances[index].subtitle,
                                                status: sampleAppliances[index].status,
                                                isOn: index == 0
                                            )
                                    }
                                }
                                .padding(.horizontal, 20)
                            }
                        } else {
                            AddItemWidget(
                                title: "가전제품 추가",
                                action: {
                                    handleApplianceAdd()
                                }
                            )
                            .padding(.horizontal, 20)
                        }
                    }

                    Spacer(minLength: 60)
                }
                .padding(.top, 16)
            }
            .background(Color(hex: "F9F9F9"))
            .navigationTitle("Home")
            .navigationBarTitleDisplayMode(.large)
            .onAppear {
                // Refresh device list when view appears
                deviceManager.refresh()
            }
        }
    }

    // MARK: - Device Card

    private func deviceCard(device: ConnectedDevice) -> some View {
        HStack(spacing: 12) {
            // Device icon
            Image(systemName: device.type.icon)
                .font(.system(size: 24))
                .foregroundColor(device.isConnected ? Color(hex: "A50034") : .gray)
                .frame(width: 40, height: 40)
                .background(device.isConnected ? Color(hex: "A50034").opacity(0.1) : Color.gray.opacity(0.1))
                .cornerRadius(8)

            // Device info
            VStack(alignment: .leading, spacing: 2) {
                Text(device.name)
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(.black)

                HStack(spacing: 4) {
                    Circle()
                        .fill(device.isConnected ? Color.green : Color.gray)
                        .frame(width: 6, height: 6)

                    Text(device.isConnected ? "연결됨" : "연결 끊김")
                        .font(.system(size: 11))
                        .foregroundColor(.gray)
                }
            }

            Spacer()

            // Battery indicator
            if let batteryLevel = device.batteryLevel {
                HStack(spacing: 4) {
                    Image(systemName: batteryIcon(for: batteryLevel))
                        .font(.system(size: 16))
                        .foregroundColor(Color(hex: device.batteryColor))

                    Text(device.batteryLevelFormatted)
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(Color(hex: device.batteryColor))
                }
            } else {
                // No battery data
                Image(systemName: "battery.100")
                    .font(.system(size: 16))
                    .foregroundColor(.gray.opacity(0.5))
            }
        }
        .padding(12)
        .background(Color.white)
        .cornerRadius(12)
        .shadow(color: Color.black.opacity(0.05), radius: 4, x: 0, y: 2)
    }

    private func batteryIcon(for level: Int) -> String {
        if level > 75 {
            return "battery.100"
        } else if level > 50 {
            return "battery.75"
        } else if level > 25 {
            return "battery.50"
        } else {
            return "battery.25"
        }
    }

    // MARK: - Actions

    private func handleApplianceAdd() {
        // Simulate adding appliances
        withAnimation {
            hasAppliances = true
        }
        print("Appliance add tapped")
    }
}

#Preview {
    HomeView()
}
