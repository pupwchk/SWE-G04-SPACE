//
//  HomeView.swift
//  space
//
//  Created by 임동현 on 11/6/25.
//

import SwiftUI

/// Home screen - main dashboard view
struct HomeView: View {
    @Binding var selectedTab: Int

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
                VStack(alignment: .leading, spacing: 16) {
                    // Section 1: 3 Fixed Widgets (Timeline, State, Persona)
                    VStack(alignment: .leading, spacing: 8) {
                        Text("타임라인, 상태, 페르소나")
                            .font(.system(size: 16, weight: .regular))
                            .foregroundColor(.black)
                            .padding(.horizontal, 20)

                        ScrollView(.horizontal, showsIndicators: false) {
                            HStack(spacing: 12) {
                                TimelineWidget()
                                StateWidget()
                                PersonaWidget()
                            }
                            .padding(.horizontal, 20)
                        }
                    }

                VStack(alignment: .leading, spacing: 16) {

                    // Device section
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Add devices")
                            .font(.system(size: 16, weight: .regular))
                            .foregroundColor(.black)
                            .padding(.horizontal, 20)

                        if hasDevices {
                            ScrollView(.horizontal, showsIndicators: false) {
                                HStack(spacing: 12) {
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
                                title: "Add devices",
                                action: {
                                    handleDeviceAdd()
                                }
                            )
                            .padding(.horizontal, 20)
                        }
                    }

                    // Appliance section
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Add home appliances")
                            .font(.system(size: 16, weight: .regular))
                            .foregroundColor(.black)
                            .padding(.horizontal, 20)

                        if hasAppliances {
                            ScrollView(.horizontal, showsIndicators: false) {
                                HStack(spacing: 12) {
                                    ForEach(0..<sampleAppliances.count, id: \.self) { index in
                                        Button(action: {
                                            // Navigate to Appliance tab
                                            selectedTab = 1
                                        }) {
                                            ApplianceCard(
                                                icon: sampleAppliances[index].icon,
                                                title: sampleAppliances[index].title,
                                                subtitle: sampleAppliances[index].subtitle,
                                                status: sampleAppliances[index].status,
                                                isOn: index == 0
                                            )
                                        }
                                        .buttonStyle(.plain)
                                    }
                                }
                                .padding(.horizontal, 20)
                            }
                        } else {
                            AddItemWidget(
                                title: "Add home appliances",
                                action: {
                                    handleApplianceAdd()
                                }
                            )
                            .padding(.horizontal, 20)
                        }
                    }

                    Spacer(minLength: 40)
                }
                .padding(.top, 8)
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
    HomeView(selectedTab: .constant(0))
}
