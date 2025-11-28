import SwiftUI
import MapKit

struct HomeLocationSetupView: View {
    @Environment(\.dismiss) private var dismiss
    @StateObject private var tagManager = TaggedLocationManager.shared
    @StateObject private var locationManager = LocationManager.shared

    @State private var cameraPosition: MapCameraPosition = .automatic
    @State private var centerCoordinate = CLLocationCoordinate2D(latitude: 37.5665, longitude: 126.9780)
    @State private var isNotificationEnabled = true
    @State private var notificationRadius: Int = 1000
    @State private var isSaving = false
    @State private var isLoading = true
    @State private var homeLocation: TaggedLocation?
    @State private var errorMessage: String?
    @State private var showError = false
    @State private var wasTrackingOnAppear = false

    private let radiusOptions = [500, 1000, 2000]
    private let defaultSpan = MKCoordinateSpan(latitudeDelta: 0.01, longitudeDelta: 0.01)

    var body: some View {
        VStack(spacing: 16) {
            mapSection
            settingsCard

            Spacer()

            saveButton
                .padding(.horizontal, 20)
                .padding(.bottom, 20)
        }
        .navigationTitle("홈 위치 설정")
        .navigationBarTitleDisplayMode(.inline)
        .background(Color(hex: "F9F9F9"))
        .onAppear {
            // Remember if location tracking was running
            wasTrackingOnAppear = locationManager.isTracking

            // Stop tracking while setting up home location to avoid conflicts
            if locationManager.isTracking {
                locationManager.stopTracking()
            }

            // Load data without blocking UI
            Task(priority: .userInitiated) {
                await loadInitialData()
            }
        }
        .onDisappear {
            // Restart tracking if it was running before and notifications are enabled
            let notificationsEnabled = UserDefaults.standard.object(forKey: "locationNotificationsEnabled") as? Bool ?? true
            if wasTrackingOnAppear && notificationsEnabled && tagManager.primaryHomeLocation != nil {
                locationManager.startTracking()
            }
        }
        .alert("오류", isPresented: $showError) {
            Button("확인", role: .cancel) { }
        } message: {
            Text(errorMessage ?? "알 수 없는 오류가 발생했습니다.")
        }
    }

    // MARK: - Map

    private var mapSection: some View {
        ZStack {
            Map(position: $cameraPosition, interactionModes: [.pan, .zoom]) {
                MapCircle(center: centerCoordinate, radius: CLLocationDistance(notificationRadius))
                    .foregroundStyle(Color(hex: "A50034").opacity(0.15))
                    .stroke(Color(hex: "A50034").opacity(0.4), lineWidth: 1)
            }
            .mapStyle(.standard)
            .mapControls {
                // Remove map controls to reduce location API calls
            }
            .onMapCameraChange(frequency: .onEnd) { context in
                centerCoordinate = context.region.center
            }
            .overlay(alignment: .center) {
                VStack(spacing: 4) {
                    Image(systemName: "mappin.circle.fill")
                        .font(.system(size: 32))
                        .foregroundColor(Color(hex: "A50034"))
                        .shadow(color: .black.opacity(0.25), radius: 6, x: 0, y: 4)

                    Capsule()
                        .fill(Color(hex: "A50034").opacity(0.3))
                        .frame(width: 6, height: 18)
                        .offset(y: -4)
                }
            }
            .overlay(alignment: .topTrailing) {
                VStack(alignment: .trailing, spacing: 6) {
                    coordinateLabel(title: "위도", value: centerCoordinate.latitude)
                    coordinateLabel(title: "경도", value: centerCoordinate.longitude)
                }
                .padding(10)
                .background(Color.white.opacity(0.95))
                .cornerRadius(10)
                .shadow(color: .black.opacity(0.08), radius: 6, x: 0, y: 3)
                .padding(12)
            }

            if isLoading {
                VStack(spacing: 12) {
                    ProgressView()
                        .scaleEffect(1.2)
                        .tint(Color(hex: "A50034"))

                    Text("위치 데이터 불러오는 중...")
                        .font(.system(size: 14, weight: .medium))
                        .foregroundColor(.gray)
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .background(Color.white.opacity(0.95))
            }
        }
        .frame(height: 340)
        .cornerRadius(16)
        .padding(.horizontal, 20)
        .padding(.top, 12)
    }

    // MARK: - Settings

    private var settingsCard: some View {
        VStack(alignment: .leading, spacing: 20) {
            HStack {
                VStack(alignment: .leading, spacing: 4) {
                    Text("알림 거리")
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundColor(.black)
                    Text("집 주변에 접근하면 알림을 보낼 거리를 선택하세요")
                        .font(.system(size: 12))
                        .foregroundColor(.gray)
                }

                Spacer()

                Picker("알림 거리", selection: $notificationRadius) {
                    ForEach(radiusOptions, id: \.self) { radius in
                        Text(radiusLabel(radius)).tag(radius)
                    }
                }
                .pickerStyle(.segmented)
                .frame(width: 200)
            }

            Toggle(isOn: $isNotificationEnabled) {
                VStack(alignment: .leading, spacing: 4) {
                    Text("근접 알림 활성화")
                        .font(.system(size: 14, weight: .semibold))
                        .foregroundColor(.black)
                    Text("집 반경 \(radiusLabel(notificationRadius)) 안에 들어오면 알림을 보냅니다")
                        .font(.system(size: 12))
                        .foregroundColor(.gray)
                }
            }
            .tint(Color(hex: "A50034"))

            if let home = homeLocation {
                Divider()
                VStack(alignment: .leading, spacing: 6) {
                    Text("현재 저장된 홈")
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(.gray)
                    Text(home.fullDisplayName)
                        .font(.system(size: 15, weight: .medium))
                        .foregroundColor(Color(hex: "A50034"))
                }
            }
        }
        .padding(20)
        .background(Color.white)
        .cornerRadius(16)
        .shadow(color: .black.opacity(0.05), radius: 6, x: 0, y: 3)
        .padding(.horizontal, 20)
    }

    // MARK: - Save Action

    private var saveButton: some View {
        Button(action: saveHomeLocation) {
            HStack {
                if isSaving {
                    ProgressView()
                        .progressViewStyle(.circular)
                        .tint(.white)
                }
                Text(homeLocation == nil ? "이 위치를 집으로 설정" : "홈 위치 업데이트")
                    .font(.system(size: 16, weight: .semibold))
            }
            .foregroundColor(.white)
            .frame(maxWidth: .infinity)
            .padding()
            .background(Color(hex: "A50034"))
            .cornerRadius(12)
        }
        .disabled(isSaving)
    }

    // MARK: - Helpers

    private func loadInitialData() async {
        // Show cached or current location immediately so the UI doesn't block
        let cachedHome = tagManager.primaryHomeLocation
        let currentLocation = locationManager.location
        let hasLocations = !tagManager.taggedLocations.isEmpty

        await MainActor.run {
            homeLocation = cachedHome
            if let home = cachedHome {
                centerCoordinate = home.coordinate
                notificationRadius = home.notificationRadius
                isNotificationEnabled = home.notificationEnabled
            } else if let current = currentLocation {
                centerCoordinate = current.coordinate
            }

            cameraPosition = .region(
                MKCoordinateRegion(
                    center: centerCoordinate,
                    span: defaultSpan
                )
            )

            // Remove spinner immediately - UI is ready
            isLoading = false
        }

        // Refresh from server in background only if we have no cached data
        // This won't block the UI since isLoading is already false
        if !hasLocations {
            Task(priority: .background) {
                await tagManager.loadTaggedLocations()

                // Update UI if we got new data
                await MainActor.run {
                    if let home = tagManager.primaryHomeLocation {
                        homeLocation = home
                        centerCoordinate = home.coordinate
                        notificationRadius = home.notificationRadius
                        isNotificationEnabled = home.notificationEnabled
                        cameraPosition = .region(
                            MKCoordinateRegion(
                                center: home.coordinate,
                                span: defaultSpan
                            )
                        )
                    }
                }
            }
        }
    }

    private func saveHomeLocation() {
        guard !isSaving else { return }
        isSaving = true
        errorMessage = nil

        Task {
            do {
                if let existing = homeLocation {
                    try await tagManager.updateTaggedLocation(
                        existing,
                        coordinate: centerCoordinate,
                        tag: .home,
                        customName: existing.customName ?? "집",
                        isHome: true,
                        notificationEnabled: isNotificationEnabled,
                        notificationRadius: notificationRadius
                    )
                } else {
                    let created = try await tagManager.createTaggedLocation(
                        coordinate: centerCoordinate,
                        tag: .home,
                        customName: "집",
                        isHome: true,
                        notificationEnabled: isNotificationEnabled,
                        notificationRadius: notificationRadius
                    )
                    homeLocation = created
                }

                await MainActor.run {
                    homeLocation = tagManager.primaryHomeLocation ?? homeLocation
                    isSaving = false
                    dismiss()
                }
            } catch {
                await MainActor.run {
                    errorMessage = error.localizedDescription
                    showError = true
                    isSaving = false
                }
            }
        }
    }

    private func coordinateLabel(title: String, value: Double) -> some View {
        HStack(spacing: 6) {
            Text(title)
                .font(.system(size: 11, weight: .semibold))
                .foregroundColor(.gray)
            Text(String(format: "%.5f", value))
                .font(.system(size: 13, weight: .medium))
                .foregroundColor(.black)
        }
    }

    private func radiusLabel(_ radius: Int) -> String {
        radius >= 1000 ? "\(radius / 1000)km" : "\(radius)m"
    }
}

#Preview {
    NavigationStack {
        HomeLocationSetupView()
    }
}
