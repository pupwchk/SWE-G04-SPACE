//
//  AutoTrackingStatusView.swift
//  space
//
//  Auto-tracking status and control view
//

import SwiftUI

struct AutoTrackingStatusView: View {
    @StateObject private var autoTracking = AutoTrackingManager.shared

    var body: some View {
        List {
            Section {
                Toggle("자동 추적 활성화", isOn: $autoTracking.isAutoTrackingEnabled)
                    .onChange(of: autoTracking.isAutoTrackingEnabled) { _, newValue in
                        if newValue {
                            autoTracking.startAutoTracking()
                        } else {
                            autoTracking.stopAutoTracking()
                        }
                    }
            } header: {
                Text("자동 추적 설정")
            } footer: {
                Text("활성화 시 매 시간마다 건강 데이터를 자동으로 업로드하고, 매일 아침 수면 데이터를 업로드합니다.")
            }

            Section("상태") {
                StatusRow(
                    icon: "heart.fill",
                    title: "마지막 건강 데이터 업로드",
                    value: formatDate(autoTracking.lastHourlyUploadTime)
                )

                StatusRow(
                    icon: "bed.double.fill",
                    title: "마지막 수면 데이터 업로드",
                    value: formatDate(autoTracking.lastSleepUploadTime)
                )

                StatusRow(
                    icon: "externaldrive.fill",
                    title: "대기 중인 업로드",
                    value: "\(autoTracking.pendingUploads)개"
                )
            }

            Section {
                Button(action: {
                    Task {
                        await autoTracking.uploadHealthDataNow()
                    }
                }) {
                    HStack {
                        Image(systemName: "arrow.up.circle.fill")
                            .foregroundColor(.blue)
                        Text("건강 데이터 지금 업로드")
                    }
                }

                Button(action: {
                    Task {
                        await autoTracking.uploadSleepDataNow()
                    }
                }) {
                    HStack {
                        Image(systemName: "arrow.up.circle.fill")
                            .foregroundColor(.purple)
                        Text("수면 데이터 지금 업로드")
                    }
                }
            } header: {
                Text("수동 업로드")
            }

            Section {
                VStack(alignment: .leading, spacing: 12) {
                    FeatureRow(
                        icon: "clock.fill",
                        title: "매 시간 건강 데이터 업로드",
                        description: "심박수, HRV, 걸음 수 등을 매 시간마다 자동으로 집계하여 업로드합니다."
                    )

                    FeatureRow(
                        icon: "moon.fill",
                        title: "매일 아침 수면 데이터 업로드",
                        description: "전날 밤 수면 데이터를 매일 오전 9시에 자동으로 업로드합니다."
                    )

                    FeatureRow(
                        icon: "mappin.circle.fill",
                        title: "위치 태그 시 Place 자동 생성",
                        description: "사용자가 위치를 태그하면 자동으로 백엔드에 Place로 저장됩니다."
                    )

                    FeatureRow(
                        icon: "wifi.slash",
                        title: "오프라인 대기열",
                        description: "네트워크가 끊어진 경우 로컬에 저장 후 연결 시 자동 업로드합니다."
                    )
                }
            } header: {
                Text("기능")
            }
        }
        .navigationTitle("자동 추적")
        .navigationBarTitleDisplayMode(.inline)
    }

    private func formatDate(_ date: Date?) -> String {
        guard let date = date else { return "없음" }

        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .full
        formatter.locale = Locale(identifier: "ko_KR")
        return formatter.localizedString(for: date, relativeTo: Date())
    }
}

struct StatusRow: View {
    let icon: String
    let title: String
    let value: String

    var body: some View {
        HStack {
            Image(systemName: icon)
                .foregroundColor(.secondary)
                .frame(width: 24)

            Text(title)
                .foregroundColor(.primary)

            Spacer()

            Text(value)
                .foregroundColor(.secondary)
                .font(.subheadline)
        }
    }
}

struct FeatureRow: View {
    let icon: String
    let title: String
    let description: String

    var body: some View {
        HStack(alignment: .top, spacing: 12) {
            Image(systemName: icon)
                .foregroundColor(.blue)
                .font(.title3)
                .frame(width: 24)

            VStack(alignment: .leading, spacing: 4) {
                Text(title)
                    .font(.headline)
                    .foregroundColor(.primary)

                Text(description)
                    .font(.caption)
                    .foregroundColor(.secondary)
                    .fixedSize(horizontal: false, vertical: true)
            }
        }
        .padding(.vertical, 4)
    }
}

#Preview {
    NavigationView {
        AutoTrackingStatusView()
    }
}
