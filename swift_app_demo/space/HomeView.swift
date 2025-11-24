//
//  HomeView.swift
//  space
//
//  Created by 임동현 on 11/6/25.
//

import SwiftUI

/// Home screen - main dashboard view
struct HomeView: View {
    @State private var hasDevices = false
    @State private var hasAppliances = false

    // Sample devices data
    let sampleDevices = [
        (icon: "applewatch", modelName: "Apple Watch"),
        (icon: "airpodspro", modelName: "AirPods Pro")
    ]

    // Sample appliances data
    let sampleAppliances = [
        (icon: "refrigerator.fill", title: "주방", subtitle: "냉장고", status: "동작 중"),
        (icon: "dishwasher.fill", title: "거실", subtitle: "청소기", status: "오프라인")
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

                    // Device section
                    VStack(alignment: .leading, spacing: 12) {
                        HStack {
                            Text("기기")
                                .font(.system(size: 18, weight: .semibold))
                                .foregroundColor(.black)

                            Spacer()

                            if hasDevices {
                                Button(action: {
                                    withAnimation {
                                        hasDevices = false
                                    }
                                }) {
                                    Image(systemName: "plus.circle.fill")
                                        .font(.system(size: 22))
                                        .foregroundColor(Color(hex: "A50034"))
                                }
                            }
                        }
                        .padding(.horizontal, 20)

                        if hasDevices {
                            ScrollView(.horizontal, showsIndicators: false) {
                                HStack(spacing: 16) {
                                    ForEach(0..<sampleDevices.count, id: \.self) { index in
                                        DeviceCard(
                                            icon: sampleDevices[index].icon,
                                            modelName: sampleDevices[index].modelName
                                        )
                                    }
                                }
                                .padding(.horizontal, 20)
                            }
                        } else {
                            AddItemWidget(
                                title: "기기 추가",
                                action: {
                                    handleDeviceAdd()
                                }
                            )
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
        }
    }

    // MARK: - Actions

    private func handleDeviceAdd() {
        // Simulate adding devices
        withAnimation {
            hasDevices = true
        }
        print("Device add tapped")
    }

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
