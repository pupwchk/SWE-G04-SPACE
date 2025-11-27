//
//  StateWidget.swift
//  space
//
//  Created by 임동현 on 11/6/25.
//

import SwiftUI

/// Health metrics widget showing sleep, stress, and calories
struct StateWidget: View {
    @StateObject private var healthManager = HealthKitManager.shared
    @State private var showDetailView = false

    var body: some View {
        Button(action: {
            showDetailView = true
        }) {
            VStack(spacing: 0) {
                // Header
                HStack {
                    Text("건강")
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(.black)

                    Spacer()

                    Image(systemName: "heart.fill")
                        .font(.system(size: 12))
                        .foregroundColor(Color(hex: "A50034"))
                }
                .padding(.horizontal, 12)
                .padding(.top, 12)
                .padding(.bottom, 8)

                // Metrics
                VStack(spacing: 6) {
                    // Heart Rate (Real-time from Watch)
                    if healthManager.currentHeartRate > 0 {
                        healthMetricRow(
                            icon: "heart.fill",
                            label: "심박수",
                            value: "\(Int(healthManager.currentHeartRate)) bpm",
                            color: .red
                        )

                        Divider()
                            .background(Color.gray.opacity(0.3))
                            .padding(.horizontal, 8)
                    }

                    // Active Calories (Real-time)
                    if healthManager.currentCalories > 0 {
                        healthMetricRow(
                            icon: "flame.fill",
                            label: "활동 칼로리",
                            value: String(format: "%.0f kcal", healthManager.currentCalories),
                            color: .orange
                        )

                        Divider()
                            .background(Color.gray.opacity(0.3))
                            .padding(.horizontal, 8)
                    }

                    // Steps (Real-time)
                    if healthManager.currentSteps > 0 {
                        healthMetricRow(
                            icon: "figure.walk",
                            label: "걸음 수",
                            value: "\(healthManager.currentSteps)",
                            color: .green
                        )

                        Divider()
                            .background(Color.gray.opacity(0.3))
                            .padding(.horizontal, 8)
                    }

                    // Stress (Daily)
                    if healthManager.stressLevel > 0 {
                        healthMetricRow(
                            icon: "brain.fill",
                            label: "스트레스",
                            value: "\(healthManager.stressLevel)%",
                            color: stressColor(for: healthManager.stressLevel)
                        )
                    }

                    // Fallback if no real-time data
                    if healthManager.currentHeartRate == 0 && healthManager.currentCalories == 0 && healthManager.currentSteps == 0 {
                        VStack(spacing: 4) {
                            Image(systemName: "applewatch")
                                .font(.system(size: 24))
                                .foregroundColor(.gray.opacity(0.5))

                            Text("Watch에서 추적 시작")
                                .font(.system(size: 10))
                                .foregroundColor(.gray)
                        }
                        .frame(maxHeight: .infinity)
                    }
                }
                .padding(.horizontal, 8)
                .padding(.vertical, 4)

                Spacer()

                // Footer indicator
                HStack(spacing: 4) {
                    Circle()
                        .fill(Color.green)
                        .frame(width: 6, height: 6)

                    Text("Apple Watch")
                        .font(.system(size: 9))
                        .foregroundColor(.gray)
                }
                .padding(.bottom, 8)
            }
            .frame(width: 160, height: 160)
            .background(Color(hex: "F3DEE5"))
            .cornerRadius(20)
        }
        .buttonStyle(.plain)
        .sheet(isPresented: $showDetailView) {
            StateDetailView(healthManager: healthManager)
        }
    }

    // MARK: - Metric Row

    private func healthMetricRow(icon: String, label: String, value: String, color: Color) -> some View {
        HStack(spacing: 8) {
            Image(systemName: icon)
                .font(.system(size: 16))
                .foregroundColor(color)
                .frame(width: 20)

            Text(label)
                .font(.system(size: 11, weight: .medium))
                .foregroundColor(.black)
                .frame(maxWidth: .infinity, alignment: .leading)

            Text(value)
                .font(.system(size: 13, weight: .bold))
                .foregroundColor(.black)
        }
        .padding(.horizontal, 8)
        .padding(.vertical, 4)
    }

    // MARK: - Helper Methods

    private func stressColor(for level: Int) -> Color {
        switch level {
        case 0..<30:
            return .green
        case 30..<60:
            return .yellow
        default:
            return .red
        }
    }
}

#Preview {
    StateWidget()
        .background(Color(hex: "F9F9F9"))
}
