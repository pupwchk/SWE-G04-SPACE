//
//  TrackingAPITestView.swift
//  space
//
//  Tracking API 호출 테스트 뷰
//

import SwiftUI
import CoreLocation

struct TrackingAPITestView: View {
    @State private var testResults: [String] = []
    @State private var isTesting = false
    @State private var fastAPIUserID: String?

    var body: some View {
        List {
            Section("FastAPI User ID") {
                if let userId = fastAPIUserID {
                    Text(userId)
                        .font(.caption)
                        .foregroundColor(.green)
                } else {
                    Text("Not set")
                        .foregroundColor(.red)
                }

                Button("Check User ID") {
                    checkUserID()
                }
            }

            Section("Timeline Upload Test") {
                Button(action: testTimelineUpload) {
                    HStack {
                        if isTesting {
                            ProgressView()
                                .padding(.trailing, 8)
                        }
                        Text("Test Timeline Upload")
                    }
                }
                .disabled(isTesting)
            }

            Section("Health Hourly Test") {
                Button(action: testHealthHourlyUpload) {
                    HStack {
                        if isTesting {
                            ProgressView()
                                .padding(.trailing, 8)
                        }
                        Text("Test Health Hourly Upload")
                    }
                }
                .disabled(isTesting)
            }

            Section("Sleep Session Test") {
                Button(action: testSleepSessionUpload) {
                    HStack {
                        if isTesting {
                            ProgressView()
                                .padding(.trailing, 8)
                        }
                        Text("Test Sleep Session Upload")
                    }
                }
                .disabled(isTesting)
            }

            Section("Place Creation Test") {
                Button(action: testPlaceCreation) {
                    HStack {
                        if isTesting {
                            ProgressView()
                                .padding(.trailing, 8)
                        }
                        Text("Test Place Creation")
                    }
                }
                .disabled(isTesting)
            }

            Section("Test Results") {
                ForEach(testResults.indices, id: \.self) { index in
                    Text(testResults[index])
                        .font(.caption)
                        .foregroundColor(testResults[index].contains("✅") ? .green : (testResults[index].contains("❌") ? .red : .primary))
                }
            }

            Section {
                Button("Clear Results") {
                    testResults.removeAll()
                }
            }
        }
        .navigationTitle("Tracking API Test")
        .navigationBarTitleDisplayMode(.inline)
        .onAppear {
            checkUserID()
        }
    }

    // MARK: - Test Methods

    private func checkUserID() {
        fastAPIUserID = UserDefaults.standard.string(forKey: "fastapi_user_id")
        if fastAPIUserID != nil {
            addResult("✅ FastAPI User ID: \(fastAPIUserID!)")
        } else {
            addResult("❌ No FastAPI User ID found")

            // Try to register user
            Task {
                if let email = SupabaseManager.shared.currentUser?.email {
                    addResult("🔄 Attempting to register user with email: \(email)")
                    if let userId = await FastAPIService.shared.registerUser(email: email) {
                        UserDefaults.standard.set(userId, forKey: "fastapi_user_id")
                        fastAPIUserID = userId
                        addResult("✅ User registered/found: \(userId)")
                    } else {
                        addResult("❌ Failed to register/find user")
                    }
                }
            }
        }
    }

    private func testTimelineUpload() {
        guard let userId = fastAPIUserID else {
            addResult("❌ No FastAPI User ID")
            return
        }

        isTesting = true
        addResult("🔄 Testing Timeline Upload...")

        Task {
            // Create a mock timeline
            let mockTimeline = createMockTimeline()

            let success = await FastAPIService.shared.uploadTimelineComplete(
                userId: userId,
                timeline: mockTimeline
            )

            await MainActor.run {
                if success {
                    addResult("✅ Timeline uploaded successfully")
                } else {
                    addResult("❌ Timeline upload failed")
                }
                isTesting = false
            }
        }
    }

    private func testHealthHourlyUpload() {
        guard let userId = fastAPIUserID else {
            addResult("❌ No FastAPI User ID")
            return
        }

        isTesting = true
        addResult("🔄 Testing Health Hourly Upload...")

        Task {
            let mockHealthData = createMockHealthHourly()

            let success = await FastAPIService.shared.uploadHealthHourly(
                userId: userId,
                hourlyData: mockHealthData
            )

            await MainActor.run {
                if success {
                    addResult("✅ Health hourly uploaded successfully")
                } else {
                    addResult("❌ Health hourly upload failed")
                }
                isTesting = false
            }
        }
    }

    private func testSleepSessionUpload() {
        guard let userId = fastAPIUserID else {
            addResult("❌ No FastAPI User ID")
            return
        }

        isTesting = true
        addResult("🔄 Testing Sleep Session Upload...")

        Task {
            let mockSleepData = createMockSleepSession()

            let success = await FastAPIService.shared.uploadSleepSession(
                userId: userId,
                session: mockSleepData
            )

            await MainActor.run {
                if success {
                    addResult("✅ Sleep session uploaded successfully")
                } else {
                    addResult("❌ Sleep session upload failed")
                }
                isTesting = false
            }
        }
    }

    private func testPlaceCreation() {
        guard let userId = fastAPIUserID else {
            addResult("❌ No FastAPI User ID")
            return
        }

        isTesting = true
        addResult("🔄 Testing Place Creation...")

        Task {
            let mockPlace = createMockPlace()

            let placeId = await FastAPIService.shared.createPlace(
                userId: userId,
                place: mockPlace
            )

            await MainActor.run {
                if let placeId = placeId {
                    addResult("✅ Place created: \(placeId)")
                } else {
                    addResult("❌ Place creation failed")
                }
                isTesting = false
            }
        }
    }

    // MARK: - Mock Data Creation

    private func createMockTimeline() -> TimelineRecord {
        let now = Date()
        let startTime = now.addingTimeInterval(-300) // 5 minutes ago

        // Create mock coordinates (Seoul area)
        let coordinates = [
            CoordinateData(coordinate: CLLocationCoordinate2D(latitude: 37.5665, longitude: 126.9780), timestamp: startTime),
            CoordinateData(coordinate: CLLocationCoordinate2D(latitude: 37.5670, longitude: 126.9785), timestamp: startTime.addingTimeInterval(60)),
            CoordinateData(coordinate: CLLocationCoordinate2D(latitude: 37.5675, longitude: 126.9790), timestamp: startTime.addingTimeInterval(120))
        ]

        let checkpoint = Checkpoint(
            coordinate: coordinates[1],
            mood: .happy,
            stayDuration: 60,
            stressChange: .unchanged,
            note: "Test checkpoint",
            heartRate: 75,
            calories: 10,
            steps: 100,
            distance: 50
        )

        return TimelineRecord(
            id: UUID(),
            startTime: startTime,
            endTime: now,
            coordinates: coordinates,
            totalDistance: 150,
            averageSpeed: 3.5,
            maxSpeed: 5.0,
            duration: 300,
            checkpoints: [checkpoint],
            weather: nil
        )
    }

    private func createMockHealthHourly() -> HealthHourlyData {
        let formatter = ISO8601DateFormatter()
        let calendar = Calendar.current
        let now = Date()
        let hourComponents = calendar.dateComponents([.year, .month, .day, .hour], from: now)
        let hourTimestamp = calendar.date(from: hourComponents) ?? now

        return HealthHourlyData(
            tsHour: formatter.string(from: hourTimestamp),
            heartRateBpm: 72.0,
            restingHrBpm: 60.0,
            walkingHrAvgBpm: 85.0,
            hrvSdnnMs: 45.0,
            vo2Max: 35.0,
            spo2Pct: 98.0,
            respiratoryRateCpm: 16.0,
            wristTempC: 36.5,
            source: "TEST_APP",
            deviceModel: WorkoutSessionData.currentDeviceModel,
            osVersion: WorkoutSessionData.currentOSVersion
        )
    }

    private func createMockSleepSession() -> SleepSessionData {
        let formatter = ISO8601DateFormatter()
        let now = Date()
        let startTime = now.addingTimeInterval(-8 * 3600) // 8 hours ago

        return SleepSessionData(
            startAt: formatter.string(from: startTime),
            endAt: formatter.string(from: now),
            inBedHr: 8.0,
            asleepHr: 7.5,
            awakeHr: 0.5,
            coreHr: 4.0,
            deepHr: 2.0,
            remHr: 1.5,
            respiratoryRate: 15.0,
            heartRateAvg: 58.0,
            efficiency: 93.75,
            source: "TEST_APP",
            deviceModel: WorkoutSessionData.currentDeviceModel,
            osVersion: WorkoutSessionData.currentOSVersion
        )
    }

    private func createMockPlace() -> PlaceData {
        let formatter = ISO8601DateFormatter()
        let now = Date()

        return PlaceData(
            label: "Test Place",
            category: "HOME",
            centerLat: 37.5665,
            centerLon: 126.9780,
            radiusM: 100.0,
            visitsCount: 1,
            firstSeen: formatter.string(from: now),
            lastSeen: formatter.string(from: now)
        )
    }

    // MARK: - Helper

    private func addResult(_ result: String) {
        let timestamp = DateFormatter.localizedString(from: Date(), dateStyle: .none, timeStyle: .medium)
        testResults.append("[\(timestamp)] \(result)")
    }
}

#Preview {
    NavigationView {
        TrackingAPITestView()
    }
}
