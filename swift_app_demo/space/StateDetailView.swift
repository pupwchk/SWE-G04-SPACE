//
//  StateDetailView.swift
//  space
//
//  Detailed health metrics view with charts and history
//

import SwiftUI
import Charts

/// Detailed health metrics view with weekly data
struct StateDetailView: View {
    @Environment(\.dismiss) private var dismiss
    @ObservedObject var healthManager: HealthKitManager

    @State private var selectedMetric: HealthMetric = .sleep

    var body: some View {
        NavigationStack {
            ZStack {
                Color(hex: "F9F9F9")
                    .ignoresSafeArea()

                ScrollView(showsIndicators: false) {
                    VStack(spacing: 20) {
                        // Today's summary cards
                        todaySummarySection

                        // Metric selector
                        metricPickerSection

                        // Weekly chart
                        weeklyChartSection

                        // Insights
                        insightsSection

                        Spacer(minLength: 40)
                    }
                    .padding(.top, 20)
                }
            }
            .navigationTitle("건강 지표")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("닫기") {
                        dismiss()
                    }
                }
            }
        }
    }

    // MARK: - Today's Summary Section

    private var todaySummarySection: some View {
        VStack(spacing: 12) {
            Text("오늘의 요약")
                .font(.system(size: 16, weight: .semibold))
                .foregroundColor(.black)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.horizontal, 20)

            HStack(spacing: 12) {
                summaryCard(
                    icon: "moon.fill",
                    title: "수면",
                    value: String(format: "%.1f", healthManager.sleepHours),
                    unit: "시간",
                    color: .blue
                )

                summaryCard(
                    icon: "brain.fill",
                    title: "스트레스",
                    value: "\(healthManager.stressLevel)",
                    unit: "%",
                    color: stressColor(for: healthManager.stressLevel)
                )

                summaryCard(
                    icon: "flame.fill",
                    title: "칼로리",
                    value: String(format: "%.0f", healthManager.caloriesBurned),
                    unit: "kcal",
                    color: .orange
                )
            }
            .padding(.horizontal, 20)
        }
    }

    private func summaryCard(icon: String, title: String, value: String, unit: String, color: Color) -> some View {
        VStack(spacing: 8) {
            Image(systemName: icon)
                .font(.system(size: 24))
                .foregroundColor(color)

            VStack(spacing: 2) {
                Text(value)
                    .font(.system(size: 20, weight: .bold))
                    .foregroundColor(.black)

                Text(unit)
                    .font(.system(size: 10))
                    .foregroundColor(.gray)
            }

            Text(title)
                .font(.system(size: 12, weight: .medium))
                .foregroundColor(.black)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 16)
        .background(Color.white)
        .cornerRadius(16)
    }

    // MARK: - Metric Picker Section

    private var metricPickerSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("주간 추이")
                .font(.system(size: 16, weight: .semibold))
                .foregroundColor(.black)
                .padding(.horizontal, 20)

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 10) {
                    metricButton(.sleep, icon: "moon.fill", color: Color(hex: "2980B9"))
                    metricButton(.stress, icon: "brain.fill", color: Color(hex: "FF8B94"))
                    metricButton(.calories, icon: "flame.fill", color: Color(hex: "FF6B6B"))
                }
                .padding(.horizontal, 20)
            }
        }
    }

    private func metricButton(_ metric: HealthMetric, icon: String, color: Color) -> some View {
        Button(action: {
            withAnimation {
                selectedMetric = metric
            }
        }) {
            HStack(spacing: 8) {
                Image(systemName: icon)
                    .font(.system(size: 14))

                Text(metric.rawValue)
                    .font(.system(size: 13, weight: .medium))
            }
            .foregroundColor(selectedMetric == metric ? .white : color)
            .padding(.horizontal, 16)
            .padding(.vertical, 10)
            .background(
                Group {
                    if selectedMetric == metric {
                        color
                    } else {
                        Color.white
                    }
                }
            )
            .overlay(
                RoundedRectangle(cornerRadius: 20)
                    .stroke(selectedMetric == metric ? Color.clear : color.opacity(0.3), lineWidth: 1.5)
            )
            .cornerRadius(20)
        }
    }

    // MARK: - Weekly Chart Section

    private var weeklyChartSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text(selectedMetric.rawValue)
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundColor(.black)

                Spacer()

                Text("최근 7일")
                    .font(.system(size: 12))
                    .foregroundColor(.gray)
            }
            .padding(.horizontal, 20)

            // Chart
            Chart {
                ForEach(weeklyData) { data in
                    BarMark(
                        x: .value("Day", data.dayName),
                        y: .value(selectedMetric.rawValue, data.value)
                    )
                    .foregroundStyle(chartColor)
                    .cornerRadius(6)
                }
            }
            .frame(height: 200)
            .padding(.horizontal, 20)
            .background(Color.white)
            .cornerRadius(16)
            .padding(.horizontal, 20)
        }
    }

    // MARK: - Insights Section

    private var insightsSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("인사이트")
                .font(.system(size: 16, weight: .semibold))
                .foregroundColor(.black)
                .padding(.horizontal, 20)

            VStack(spacing: 12) {
                ForEach(insights, id: \.self) { insight in
                    insightCard(insight)
                }
            }
            .padding(.horizontal, 20)
        }
    }

    private func insightCard(_ insight: String) -> some View {
        HStack(spacing: 12) {
            Image(systemName: "lightbulb.fill")
                .font(.system(size: 16))
                .foregroundColor(Color(hex: "A50034"))

            Text(insight)
                .font(.system(size: 13))
                .foregroundColor(.black)
                .fixedSize(horizontal: false, vertical: true)
        }
        .padding(12)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Color.white)
        .cornerRadius(12)
    }

    // MARK: - Computed Properties

    private var weeklyData: [DailyHealthData] {
        switch selectedMetric {
        case .sleep:
            return healthManager.weeklySleepData
        case .stress:
            return healthManager.weeklyStressData
        case .calories:
            return healthManager.weeklyCaloriesData
        }
    }

    private var chartColor: LinearGradient {
        switch selectedMetric {
        case .sleep:
            return LinearGradient(
                colors: [Color(hex: "6DD5FA"), Color(hex: "2980B9")],
                startPoint: .top,
                endPoint: .bottom
            )
        case .stress:
            return LinearGradient(
                colors: [Color(hex: "A8E6CF"), Color(hex: "FF8B94")],
                startPoint: .top,
                endPoint: .bottom
            )
        case .calories:
            return LinearGradient(
                colors: [Color(hex: "FFD89B"), Color(hex: "FF6B6B")],
                startPoint: .top,
                endPoint: .bottom
            )
        }
    }

    private var insights: [String] {
        switch selectedMetric {
        case .sleep:
            return [
                "이번 주 평균 \(String(format: "%.1f", averageValue))시간 수면을 취했습니다.",
                "최적의 건강을 위해 매일 밤 7-9시간 수면을 목표로 하세요.",
                healthManager.sleepHours >= 7 ? "건강한 수면 습관 유지 중이에요! 😴" : "오늘 밤은 더 많은 휴식을 취해보세요. 😴"
            ]
        case .stress:
            return [
                "이번 주 평균 스트레스 수준은 \(String(format: "%.0f", averageValue))%였습니다.",
                "명상이나 호흡 운동으로 스트레스를 줄여보세요.",
                healthManager.stressLevel < 40 ? "스트레스가 잘 관리되고 있어요! 😌" : "하루 중 휴식 시간을 가져보세요. 😰"
            ]
        case .calories:
            return [
                "하루 평균 \(String(format: "%.0f", averageValue)) 칼로리를 소모했습니다.",
                "매일 최소 30분의 운동으로 활동적인 생활을 유지하세요.",
                healthManager.caloriesBurned > 500 ? "훌륭한 활동량이에요! 🔥" : "일일 활동량을 늘려보세요. 🔥"
            ]
        }
    }

    private var averageValue: Double {
        guard !weeklyData.isEmpty else { return 0 }
        return weeklyData.map { $0.value }.reduce(0, +) / Double(weeklyData.count)
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

// MARK: - Health Metric Enum

enum HealthMetric: String, CaseIterable {
    case sleep = "수면"
    case stress = "스트레스"
    case calories = "칼로리"
}

#Preview {
    StateDetailView(healthManager: HealthKitManager.shared)
}
