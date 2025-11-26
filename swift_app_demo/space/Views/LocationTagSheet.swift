//
//  LocationTagSheet.swift
//  space
//
//  Created by Claude on 2025-11-27.
//

import SwiftUI
import CoreLocation

struct LocationTagSheet: View {
    @Environment(\.dismiss) private var dismiss
    @StateObject private var tagManager = TaggedLocationManager.shared

    let checkpoint: Checkpoint
    let onTagAdded: () -> Void

    @State private var selectedTag: LocationTag = .home
    @State private var customName: String = ""
    @State private var isHome: Bool = true
    @State private var notificationEnabled: Bool = true
    @State private var notificationRadius: Int = 1000
    @State private var isLoading = false
    @State private var showError = false
    @State private var errorMessage = ""

    // Notification radius options
    private let radiusOptions = [
        (label: "500m", value: 500),
        (label: "1km", value: 1000),
        (label: "2km", value: 2000)
    ]

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    // Location info
                    locationInfoSection

                    Divider()

                    // Tag selection
                    tagSelectionSection

                    Divider()

                    // Custom name
                    customNameSection

                    Divider()

                    // Home location toggle
                    homeLocationSection

                    Divider()

                    // Notification settings
                    notificationSection
                }
                .padding(20)
            }
            .background(Color(hex: "F9F9F9"))
            .navigationTitle("위치 태그 추가")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarLeading) {
                    Button("취소") {
                        dismiss()
                    }
                }

                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("저장") {
                        saveLocationTag()
                    }
                    .disabled(isLoading)
                }
            }
            .alert("오류", isPresented: $showError) {
                Button("확인", role: .cancel) {}
            } message: {
                Text(errorMessage)
            }
        }
    }

    // MARK: - Location Info Section

    private var locationInfoSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 8) {
                Image(systemName: "mappin.circle.fill")
                    .foregroundColor(Color(hex: "A50034"))
                    .font(.system(size: 20))

                Text("위치 정보")
                    .font(.system(size: 16, weight: .semibold))
                    .foregroundColor(.black)
            }

            VStack(alignment: .leading, spacing: 8) {
                // Mood
                HStack(spacing: 8) {
                    Text(checkpoint.mood.emoji)
                        .font(.system(size: 16))
                    Text(checkpoint.mood.label)
                        .font(.system(size: 14))
                        .foregroundColor(.gray)
                }

                // Coordinates
                Text("좌표: \(String(format: "%.6f", checkpoint.coordinate.coordinate.latitude)), \(String(format: "%.6f", checkpoint.coordinate.coordinate.longitude))")
                    .font(.system(size: 12))
                    .foregroundColor(.gray)

                // Stay duration
                Text("체류 시간: \(checkpoint.stayDurationFormatted)")
                    .font(.system(size: 12))
                    .foregroundColor(.gray)
            }
            .padding(12)
            .background(Color.white)
            .cornerRadius(12)
        }
    }

    // MARK: - Tag Selection Section

    private var tagSelectionSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("태그 선택")
                .font(.system(size: 16, weight: .semibold))
                .foregroundColor(.black)

            LazyVGrid(columns: [
                GridItem(.flexible()),
                GridItem(.flexible()),
                GridItem(.flexible())
            ], spacing: 12) {
                ForEach(LocationTag.allCases, id: \.self) { tag in
                    tagButton(tag: tag)
                }
            }
        }
    }

    private func tagButton(tag: LocationTag) -> some View {
        Button(action: {
            withAnimation(.spring(response: 0.3)) {
                selectedTag = tag
            }
        }) {
            VStack(spacing: 8) {
                Text(tag.icon)
                    .font(.system(size: 32))

                Text(tag.displayName)
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(selectedTag == tag ? Color(hex: "A50034") : .gray)
            }
            .frame(maxWidth: .infinity)
            .frame(height: 80)
            .background(selectedTag == tag ? Color(hex: "F3DEE5") : Color.white)
            .cornerRadius(12)
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(selectedTag == tag ? Color(hex: "A50034") : Color.gray.opacity(0.3), lineWidth: selectedTag == tag ? 2 : 1)
            )
        }
        .buttonStyle(.plain)
    }

    // MARK: - Custom Name Section

    private var customNameSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("커스텀 이름 (선택)")
                .font(.system(size: 16, weight: .semibold))
                .foregroundColor(.black)

            TextField("예: 우리 집, 회사 본사", text: $customName)
                .textFieldStyle(.plain)
                .padding(12)
                .background(Color.white)
                .cornerRadius(12)
                .overlay(
                    RoundedRectangle(cornerRadius: 12)
                        .stroke(Color.gray.opacity(0.3), lineWidth: 1)
                )
        }
    }

    // MARK: - Home Location Section

    private var homeLocationSection: some View {
        VStack(alignment: .leading, spacing: 12) {
            Toggle(isOn: $isHome) {
                VStack(alignment: .leading, spacing: 4) {
                    Text("홈 위치로 설정")
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(.black)

                    Text("이 위치를 주요 홈 위치로 표시합니다")
                        .font(.system(size: 12))
                        .foregroundColor(.gray)
                }
            }
            .tint(Color(hex: "A50034"))
            .padding(12)
            .background(Color.white)
            .cornerRadius(12)
        }
    }

    // MARK: - Notification Section

    private var notificationSection: some View {
        VStack(alignment: .leading, spacing: 16) {
            Toggle(isOn: $notificationEnabled) {
                VStack(alignment: .leading, spacing: 4) {
                    Text("근접 알림 활성화")
                        .font(.system(size: 16, weight: .semibold))
                        .foregroundColor(.black)

                    Text("이 위치에 가까이 갈 때 알림을 받습니다")
                        .font(.system(size: 12))
                        .foregroundColor(.gray)
                }
            }
            .tint(Color(hex: "A50034"))
            .padding(12)
            .background(Color.white)
            .cornerRadius(12)

            if notificationEnabled {
                VStack(alignment: .leading, spacing: 12) {
                    Text("알림 거리")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(.black)

                    Picker("알림 거리", selection: $notificationRadius) {
                        ForEach(radiusOptions, id: \.value) { option in
                            Text(option.label).tag(option.value)
                        }
                    }
                    .pickerStyle(.segmented)
                    .padding(12)
                    .background(Color.white)
                    .cornerRadius(12)
                }
            }
        }
    }

    // MARK: - Save Location Tag

    private func saveLocationTag() {
        isLoading = true

        Task {
            do {
                let trimmedName = customName.trimmingCharacters(in: .whitespacesAndNewlines)

                _ = try await tagManager.createTaggedLocation(
                    coordinate: checkpoint.coordinate.coordinate,
                    tag: selectedTag,
                    customName: trimmedName.isEmpty ? nil : trimmedName,
                    isHome: isHome,
                    notificationEnabled: notificationEnabled,
                    notificationRadius: notificationRadius
                )

                // Success
                await MainActor.run {
                    isLoading = false
                    onTagAdded()
                    dismiss()
                }
            } catch {
                await MainActor.run {
                    isLoading = false
                    errorMessage = error.localizedDescription
                    showError = true
                }
            }
        }
    }
}

#Preview {
    LocationTagSheet(
        checkpoint: Checkpoint(
            id: UUID(),
            coordinate: CoordinateData(
                coordinate: CLLocationCoordinate2D(
                    latitude: 37.5665,
                    longitude: 126.9780
                ),
                timestamp: Date()
            ),
            mood: .neutral,
            stayDuration: 300,
            stressChange: .unchanged,
            note: "Preview checkpoint",
            timestamp: Date(),
            heartRate: nil,
            calories: nil,
            steps: nil,
            distance: nil,
            hrv: nil,
            stressLevel: nil
        ),
        onTagAdded: {}
    )
}
