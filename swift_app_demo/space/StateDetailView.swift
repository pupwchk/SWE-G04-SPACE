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
            .navigationTitle("Health Metrics")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Close") {
                        dismiss()
                    }
                }
            }
        }
    }

    // MARK: - Today's Summary Section

    private var todaySummarySection: some View {
        VStack(spacing: 12) {
            Text("Today's Summary")
                .font(.system(size: 16, weight: .semibold))
                .foregroundColor(.black)
                .frame(maxWidth: .infinity, alignment: .leading)
                .padding(.horizontal, 20)

            HStack(spacing: 12) {
                summaryCard(
                    icon: "moon.fill",
                    title: "Sleep",
                    value: String(format: "%.1f", healthManager.sleepHours),
                    unit: "hours",
                    color: .blue
                )

                summaryCard(
                    icon: "brain.fill",
                    title: "Stress",
                    value: "\(healthManager.stressLevel)",
                    unit: "%",
                    color: stressColor(for: healthManager.stressLevel)
                )

                summaryCard(
                    icon: "flame.fill",
                    title: "Calories",
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
            Text("Weekly Trends")
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

                Text("Last 7 Days")
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
            Text("Insights")
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
                "You averaged \(String(format: "%.1f", averageValue)) hours of sleep this week.",
                "Aim for 7-9 hours of sleep per night for optimal health.",
                healthManager.sleepHours >= 7 ? "Great job maintaining healthy sleep habits! 😴" : "Try to get more rest tonight. 😴"
            ]
        case .stress:
            return [
                "Your average stress level was \(String(format: "%.0f", averageValue))% this week.",
                "Try meditation or breathing exercises to reduce stress.",
                healthManager.stressLevel < 40 ? "Your stress levels are well managed! 😌" : "Consider taking breaks throughout the day. 😰"
            ]
        case .calories:
            return [
                "You burned an average of \(String(format: "%.0f", averageValue)) calories per day.",
                "Stay active with at least 30 minutes of exercise daily.",
                healthManager.caloriesBurned > 500 ? "Excellent activity level! 🔥" : "Try to increase your daily activity. 🔥"
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
    case sleep = "Sleep"
    case stress = "Stress"
    case calories = "Calories"
}

#Preview {
    StateDetailView(healthManager: HealthKitManager.shared)
}
