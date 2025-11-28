//
//  AutoTrackingManager.swift
//  space
//
//  Automatic health data tracking and upload manager
//

import Foundation
import HealthKit
import CoreLocation

/// Manages automatic upload of health and location data to FastAPI backend
class AutoTrackingManager: NSObject, ObservableObject {
    static let shared = AutoTrackingManager()

    // MARK: - Properties

    @Published var isAutoTrackingEnabled = true
    @Published var lastHourlyUploadTime: Date?
    @Published var lastSleepUploadTime: Date?
    @Published var pendingUploads: Int = 0

    private let healthStore = HKHealthStore()
    private var hourlyUploadTimer: Timer?
    private var sleepCheckTimer: Timer?
    private var offlineQueue: OfflineUploadQueue

    // MARK: - Initialization

    private override init() {
        self.offlineQueue = OfflineUploadQueue()
        super.init()

        loadSettings()
        setupNetworkMonitoring()
    }

    // MARK: - Public Methods

    /// Start automatic tracking
    func startAutoTracking() {
        guard isAutoTrackingEnabled else { return }

        print("🤖 [AutoTracking] Starting automatic tracking...")

        // Start hourly health data upload (every hour)
        startHourlyHealthUpload()

        // Start daily sleep data check (every morning at 9 AM)
        scheduleDailySleepUpload()

        // Process any pending offline uploads
        processOfflineQueue()
    }

    /// Stop automatic tracking
    func stopAutoTracking() {
        print("🛑 [AutoTracking] Stopping automatic tracking...")

        hourlyUploadTimer?.invalidate()
        hourlyUploadTimer = nil

        sleepCheckTimer?.invalidate()
        sleepCheckTimer = nil
    }

    /// Manually trigger health data upload
    func uploadHealthDataNow() async {
        await uploadCurrentHourHealthData()
    }

    /// Manually trigger sleep data upload
    func uploadSleepDataNow() async {
        await uploadYesterdaySleepData()
    }

    // MARK: - Hourly Health Upload

    private func startHourlyHealthUpload() {
        // Upload immediately on start
        Task {
            await uploadCurrentHourHealthData()
        }

        // Schedule hourly uploads
        // Run every hour at the top of the hour
        let calendar = Calendar.current
        let now = Date()
        let nextHour = calendar.date(byAdding: .hour, value: 1, to: calendar.startOfDay(for: now))!
        let timeUntilNextHour = nextHour.timeIntervalSince(now)

        hourlyUploadTimer = Timer.scheduledTimer(withTimeInterval: timeUntilNextHour, repeats: false) { [weak self] _ in
            self?.setupRecurringHourlyTimer()
        }
    }

    private func setupRecurringHourlyTimer() {
        // Upload health data
        Task {
            await uploadCurrentHourHealthData()
        }

        // Schedule next hourly upload (every 3600 seconds = 1 hour)
        hourlyUploadTimer = Timer.scheduledTimer(withTimeInterval: 3600, repeats: true) { [weak self] _ in
            Task {
                await self?.uploadCurrentHourHealthData()
            }
        }
    }

    private func uploadCurrentHourHealthData() async {
        print("📊 [AutoTracking] Uploading hourly health data...")

        // Get current hour timestamp
        let calendar = Calendar.current
        let now = Date()
        let hourComponents = calendar.dateComponents([.year, .month, .day, .hour], from: now)
        guard let hourTimestamp = calendar.date(from: hourComponents) else { return }

        // Collect health data from the past hour
        let startTime = calendar.date(byAdding: .hour, value: -1, to: hourTimestamp) ?? hourTimestamp
        let endTime = hourTimestamp

        // Query HealthKit for data
        guard let healthData = await collectHealthData(from: startTime, to: endTime) else {
            print("⚠️ [AutoTracking] No health data available for this hour")
            return
        }

        // Get user ID
        guard let userId = UserDefaults.standard.string(forKey: "fastapi_user_id") else {
            print("❌ [AutoTracking] No FastAPI user ID found")
            offlineQueue.addHealthHourly(healthData)
            return
        }

        // Upload to FastAPI
        let success = await FastAPIService.shared.uploadHealthHourly(userId: userId, hourlyData: healthData)

        if success {
            lastHourlyUploadTime = Date()
            saveSettings()
            print("✅ [AutoTracking] Hourly health data uploaded successfully")
        } else {
            print("❌ [AutoTracking] Failed to upload hourly health data, adding to offline queue")
            offlineQueue.addHealthHourly(healthData)
        }
    }

    private func collectHealthData(from startTime: Date, to endTime: Date) async -> HealthHourlyData? {
        let formatter = ISO8601DateFormatter()

        // Use HealthKitManager to get current data
        let healthManager = HealthKitManager.shared

        // For production: Query HealthKit for the specific hour range
        // For now, use current values from HealthKitManager

        let heartRate = healthManager.currentHeartRate > 0 ? healthManager.currentHeartRate : nil
        let hrv = healthManager.currentHRV > 0 ? healthManager.currentHRV : nil

        // Only upload if we have at least some data
        guard heartRate != nil || hrv != nil else {
            return nil
        }

        return HealthHourlyData(
            tsHour: formatter.string(from: startTime),
            heartRateBpm: heartRate,
            restingHrBpm: nil,  // TODO: Query from HealthKit
            walkingHrAvgBpm: nil,  // TODO: Query from HealthKit
            hrvSdnnMs: hrv,
            vo2Max: nil,  // TODO: Query from HealthKit
            spo2Pct: nil,  // TODO: Query from HealthKit
            respiratoryRateCpm: nil,  // TODO: Query from HealthKit
            wristTempC: nil,  // TODO: Query from HealthKit
            source: "SPACE_APP",
            deviceModel: WorkoutSessionData.currentDeviceModel,
            osVersion: WorkoutSessionData.currentOSVersion
        )
    }

    // MARK: - Daily Sleep Upload

    private func scheduleDailySleepUpload() {
        let calendar = Calendar.current
        let now = Date()

        // Schedule for 9:00 AM daily
        var components = calendar.dateComponents([.year, .month, .day], from: now)
        components.hour = 9
        components.minute = 0

        guard var nextUploadTime = calendar.date(from: components) else { return }

        // If it's already past 9 AM today, schedule for tomorrow
        if nextUploadTime <= now {
            nextUploadTime = calendar.date(byAdding: .day, value: 1, to: nextUploadTime)!
        }

        let timeUntilNextUpload = nextUploadTime.timeIntervalSince(now)

        sleepCheckTimer = Timer.scheduledTimer(withTimeInterval: timeUntilNextUpload, repeats: false) { [weak self] _ in
            self?.setupRecurringSleepTimer()
        }

        print("⏰ [AutoTracking] Sleep upload scheduled for \(nextUploadTime)")
    }

    private func setupRecurringSleepTimer() {
        // Upload sleep data
        Task {
            await uploadYesterdaySleepData()
        }

        // Schedule next daily upload (every 24 hours)
        sleepCheckTimer = Timer.scheduledTimer(withTimeInterval: 86400, repeats: true) { [weak self] _ in
            Task {
                await self?.uploadYesterdaySleepData()
            }
        }
    }

    private func uploadYesterdaySleepData() async {
        print("😴 [AutoTracking] Uploading yesterday's sleep data...")

        let calendar = Calendar.current
        let now = Date()

        // Get yesterday's date range (from noon yesterday to noon today)
        let startOfToday = calendar.startOfDay(for: now)
        guard let yesterdayNoon = calendar.date(byAdding: .day, value: -1, to: startOfToday)?.addingTimeInterval(12 * 3600) else {
            return
        }
        let todayNoon = startOfToday.addingTimeInterval(12 * 3600)

        // Query HealthKit for sleep data
        guard let sleepData = await collectSleepData(from: yesterdayNoon, to: todayNoon) else {
            print("⚠️ [AutoTracking] No sleep data available for yesterday")
            return
        }

        // Get user ID
        guard let userId = UserDefaults.standard.string(forKey: "fastapi_user_id") else {
            print("❌ [AutoTracking] No FastAPI user ID found")
            offlineQueue.addSleepSession(sleepData)
            return
        }

        // Upload to FastAPI
        let success = await FastAPIService.shared.uploadSleepSession(userId: userId, session: sleepData)

        if success {
            lastSleepUploadTime = Date()
            saveSettings()
            print("✅ [AutoTracking] Sleep data uploaded successfully")
        } else {
            print("❌ [AutoTracking] Failed to upload sleep data, adding to offline queue")
            offlineQueue.addSleepSession(sleepData)
        }
    }

    private func collectSleepData(from startTime: Date, to endTime: Date) async -> SleepSessionData? {
        let formatter = ISO8601DateFormatter()

        // TODO: Query actual sleep data from HealthKit
        // For now, return nil if no data available

        // This is a placeholder - implement actual HealthKit sleep query
        return nil

        /* Example implementation:
        guard let sleepType = HKObjectType.categoryType(forIdentifier: .sleepAnalysis) else {
            return nil
        }

        let predicate = HKQuery.predicateForSamples(withStart: startTime, end: endTime, options: .strictStartDate)

        // Query sleep samples and aggregate data
        // Return SleepSessionData with actual values
        */
    }

    // MARK: - Place Creation

    /// Create a place from a tagged location
    func createPlaceFromLocation(label: String, category: String?, coordinate: CLLocationCoordinate2D, radiusMeters: Double = 100) async -> String? {
        let formatter = ISO8601DateFormatter()

        let placeData = PlaceData(
            label: label,
            category: category,
            centerLat: coordinate.latitude,
            centerLon: coordinate.longitude,
            radiusM: radiusMeters,
            visitsCount: 1,
            firstSeen: formatter.string(from: Date()),
            lastSeen: formatter.string(from: Date())
        )

        // Get user ID
        guard let userId = UserDefaults.standard.string(forKey: "fastapi_user_id") else {
            print("❌ [AutoTracking] No FastAPI user ID found")
            offlineQueue.addPlace(placeData)
            return nil
        }

        // Upload to FastAPI
        let placeId = await FastAPIService.shared.createPlace(userId: userId, place: placeData)

        if let placeId = placeId {
            print("✅ [AutoTracking] Place created: \(label) (\(placeId))")
            return placeId
        } else {
            print("❌ [AutoTracking] Failed to create place, adding to offline queue")
            offlineQueue.addPlace(placeData)
            return nil
        }
    }

    // MARK: - Offline Queue Processing

    private func setupNetworkMonitoring() {
        // Monitor network connectivity
        NotificationCenter.default.addObserver(
            self,
            selector: #selector(networkStatusChanged),
            name: NSNotification.Name("NetworkStatusChanged"),
            object: nil
        )
    }

    @objc private func networkStatusChanged() {
        // When network becomes available, process offline queue
        processOfflineQueue()
    }

    private func processOfflineQueue() {
        Task {
            await offlineQueue.processQueue()

            await MainActor.run {
                self.pendingUploads = offlineQueue.queueCount
            }
        }
    }

    // MARK: - Settings Persistence

    private func loadSettings() {
        isAutoTrackingEnabled = UserDefaults.standard.bool(forKey: "auto_tracking_enabled")
        lastHourlyUploadTime = UserDefaults.standard.object(forKey: "last_hourly_upload") as? Date
        lastSleepUploadTime = UserDefaults.standard.object(forKey: "last_sleep_upload") as? Date
    }

    private func saveSettings() {
        UserDefaults.standard.set(isAutoTrackingEnabled, forKey: "auto_tracking_enabled")
        if let lastHourly = lastHourlyUploadTime {
            UserDefaults.standard.set(lastHourly, forKey: "last_hourly_upload")
        }
        if let lastSleep = lastSleepUploadTime {
            UserDefaults.standard.set(lastSleep, forKey: "last_sleep_upload")
        }
    }
}

// MARK: - Offline Upload Queue

/// Manages offline queue for failed uploads
class OfflineUploadQueue {
    private let queueKey = "offline_upload_queue"

    private var queue: [QueueItem] = []

    init() {
        loadQueue()
    }

    var queueCount: Int {
        return queue.count
    }

    // MARK: - Add to Queue

    func addHealthHourly(_ data: HealthHourlyData) {
        queue.append(.healthHourly(data))
        saveQueue()
        print("📥 [OfflineQueue] Added health hourly data to queue (\(queue.count) items)")
    }

    func addSleepSession(_ data: SleepSessionData) {
        queue.append(.sleepSession(data))
        saveQueue()
        print("📥 [OfflineQueue] Added sleep session to queue (\(queue.count) items)")
    }

    func addPlace(_ data: PlaceData) {
        queue.append(.place(data))
        saveQueue()
        print("📥 [OfflineQueue] Added place to queue (\(queue.count) items)")
    }

    func addWorkoutSession(_ data: WorkoutSessionData) {
        queue.append(.workoutSession(data))
        saveQueue()
        print("📥 [OfflineQueue] Added workout session to queue (\(queue.count) items)")
    }

    // MARK: - Process Queue

    func processQueue() async {
        guard !queue.isEmpty else { return }

        print("🔄 [OfflineQueue] Processing queue (\(queue.count) items)...")

        guard let userId = UserDefaults.standard.string(forKey: "fastapi_user_id") else {
            print("❌ [OfflineQueue] No FastAPI user ID found, skipping queue processing")
            return
        }

        var successfulUploads: [Int] = []

        for (index, item) in queue.enumerated() {
            let success = await uploadQueueItem(item, userId: userId)
            if success {
                successfulUploads.append(index)
            }
        }

        // Remove successful uploads from queue (in reverse order to maintain indices)
        for index in successfulUploads.reversed() {
            queue.remove(at: index)
        }

        saveQueue()

        print("✅ [OfflineQueue] Processed \(successfulUploads.count)/\(queue.count + successfulUploads.count) items")
    }

    private func uploadQueueItem(_ item: QueueItem, userId: String) async -> Bool {
        switch item {
        case .healthHourly(let data):
            return await FastAPIService.shared.uploadHealthHourly(userId: userId, hourlyData: data)
        case .sleepSession(let data):
            return await FastAPIService.shared.uploadSleepSession(userId: userId, session: data)
        case .workoutSession(let data):
            return await FastAPIService.shared.uploadWorkoutSession(userId: userId, session: data)
        case .place(let data):
            let result = await FastAPIService.shared.createPlace(userId: userId, place: data)
            return result != nil
        }
    }

    // MARK: - Persistence

    private func loadQueue() {
        if let data = UserDefaults.standard.data(forKey: queueKey),
           let decoded = try? JSONDecoder().decode([QueueItem].self, from: data) {
            queue = decoded
            print("📂 [OfflineQueue] Loaded \(queue.count) items from disk")
        }
    }

    private func saveQueue() {
        if let encoded = try? JSONEncoder().encode(queue) {
            UserDefaults.standard.set(encoded, forKey: queueKey)
        }
    }

    // MARK: - Queue Item

    enum QueueItem: Codable {
        case healthHourly(HealthHourlyData)
        case sleepSession(SleepSessionData)
        case workoutSession(WorkoutSessionData)
        case place(PlaceData)

        enum CodingKeys: String, CodingKey {
            case type
            case data
        }

        enum ItemType: String, Codable {
            case healthHourly
            case sleepSession
            case workoutSession
            case place
        }

        init(from decoder: Decoder) throws {
            let container = try decoder.container(keyedBy: CodingKeys.self)
            let type = try container.decode(ItemType.self, forKey: .type)

            switch type {
            case .healthHourly:
                let data = try container.decode(HealthHourlyData.self, forKey: .data)
                self = .healthHourly(data)
            case .sleepSession:
                let data = try container.decode(SleepSessionData.self, forKey: .data)
                self = .sleepSession(data)
            case .workoutSession:
                let data = try container.decode(WorkoutSessionData.self, forKey: .data)
                self = .workoutSession(data)
            case .place:
                let data = try container.decode(PlaceData.self, forKey: .data)
                self = .place(data)
            }
        }

        func encode(to encoder: Encoder) throws {
            var container = encoder.container(keyedBy: CodingKeys.self)

            switch self {
            case .healthHourly(let data):
                try container.encode(ItemType.healthHourly, forKey: .type)
                try container.encode(data, forKey: .data)
            case .sleepSession(let data):
                try container.encode(ItemType.sleepSession, forKey: .type)
                try container.encode(data, forKey: .data)
            case .workoutSession(let data):
                try container.encode(ItemType.workoutSession, forKey: .type)
                try container.encode(data, forKey: .data)
            case .place(let data):
                try container.encode(ItemType.place, forKey: .type)
                try container.encode(data, forKey: .data)
            }
        }
    }
}
