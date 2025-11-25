//
//  HomeView.swift
//  space
//
//  Created by 임동현 on 11/6/25.
//

import SwiftUI

/// Home screen - main dashboard view
struct HomeView: View {
    @State private var hasAppliances = false

    // Sample appliances data (keeping for smart home appliances)
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

                    // Device section - will be populated by WatchConnectivityManager and AudioDeviceManager
                    VStack(alignment: .leading, spacing: 12) {
                        HStack {
                            Text("기기")
                                .font(.system(size: 18, weight: .semibold))
                                .foregroundColor(.black)

                            Spacer()
                        }
                        .padding(.horizontal, 20)

                        // Devices will be dynamically shown when connected
                        // This section will be implemented in Phase 8
                        Text("기기 연결 기능은 Phase 8에서 구현됩니다")
                            .font(.system(size: 14))
                            .foregroundColor(.gray)
                            .padding(.horizontal, 20)
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
