import Foundation
import SwiftUI

class FastAPIService {
    static let shared = FastAPIService()

    private let baseURL = "http://13.125.85.158:11325"
    private let apiSession: URLSession

    private init() {
        // Disable URL cache so backend updates show up immediately without rebuilds
        let config = URLSessionConfiguration.default
        config.requestCachePolicy = .reloadIgnoringLocalCacheData
        config.urlCache = nil
        apiSession = URLSession(configuration: config)
    }

    // MARK: - User Registration

    /// FastAPI 백엔드에 사용자 이메일 등록
    /// - Parameter email: 등록할 이메일 주소
    /// - Returns: 성공 시 백엔드 user_id (UUID), 실패 시 nil
    func registerUser(email: String) async -> String? {
        guard let url = URL(string: "\(baseURL)/api/users/") else {
            print("  [FastAPI] Invalid URL")
            return nil
        }

        var request = URLRequest(url: url)
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: String] = ["email": email]

        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: body)

            let (data, response) = try await apiSession.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                print("  [FastAPI] Invalid response")
                return nil
            }

            // 성공 응답 (201 Created)
            if httpResponse.statusCode == 201 {
                if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                   let userId = json["id"] as? String {
                    print(" [FastAPI] User registered successfully: \(userId)")
                    return userId
                }
            }

            // 이미 등록된 이메일 (400 Bad Request)
            if httpResponse.statusCode == 400 {
                print("⚠️ [FastAPI] Email already registered (400) - fetching existing user")
                // 이미 등록된 사용자의 ID를 가져오기
                return await getUserIdByEmail(email: email)
            }

            // 기타 에러
            print("  [FastAPI] Registration failed with status: \(httpResponse.statusCode)")
            if let errorString = String(data: data, encoding: .utf8) {
                print("  [FastAPI] Error details: \(errorString)")
            }
            return nil

        } catch {
            print("  [FastAPI] Network error: \(error.localizedDescription)")
            return nil
        }
    }

    /// 이메일로 사용자 ID 조회
    /// - Parameter email: 조회할 이메일
    /// - Returns: 사용자 ID (UUID)
    private func getUserIdByEmail(email: String) async -> String? {
        guard let url = URL(string: "\(baseURL)/api/users/") else {
            print("❌ [FastAPI] Invalid URL for user lookup")
            return nil
        }

        var request = URLRequest(url: url)
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        do {
            let (data, response) = try await apiSession.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                print("❌ [FastAPI] Invalid response")
                return nil
            }

            if httpResponse.statusCode == 200 {
                if let users = try? JSONSerialization.jsonObject(with: data) as? [[String: Any]] {
                    // Find user with matching email
                    if let user = users.first(where: { ($0["email"] as? String) == email }),
                       let userId = user["id"] as? String {
                        print("✅ [FastAPI] Found existing user: \(userId)")
                        return userId
                    }
                }
            }

            print("❌ [FastAPI] User lookup failed with status: \(httpResponse.statusCode)")
            return nil

        } catch {
            print("❌ [FastAPI] Network error: \(error.localizedDescription)")
            return nil
        }
    }

    /// 이메일로 사용자 정보 조회 (향후 확장용)
    /// - Parameter email: 조회할 이메일
    /// - Returns: 사용자 정보 딕셔너리
    func getUser(email: String) async -> [String: Any]? {
        // TODO: GET /api/users/ 엔드포인트로 필터링 또는
        // GET /api/users/{user_id} 엔드포인트 사용
        return nil
    }

    // MARK: - Weather API

    /// 현재 날씨 정보 조회
    /// - Parameters:
    ///   - latitude: 위도
    ///   - longitude: 경도
    ///   - sido: 시도 이름 (미세먼지 조회용, 기본값: "서울")
    /// - Returns: 날씨 정보 WeatherInfo 객체
    func getCurrentWeather(latitude: Double, longitude: Double, sido: String = "서울") async -> WeatherInfo? {
        guard let url = URL(string: "\(baseURL)/api/weather/current?latitude=\(latitude)&longitude=\(longitude)&sido=\(sido)") else {
            print("❌ [FastAPI] Invalid weather URL")
            return nil
        }

        var request = URLRequest(url: url)
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        do {
            let (data, response) = try await apiSession.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                print("❌ [FastAPI] Invalid response")
                return nil
            }

            if httpResponse.statusCode == 200 {
                // Print raw response for debugging
                if let jsonString = String(data: data, encoding: .utf8) {
                    print(" [FastAPI] Weather API Response: \(jsonString)")
                }

                if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                    print("✅ [FastAPI] Weather fetched successfully")
                    print("   - Temperature: \(json["temperature"] ?? "nil")")
                    print("   - Humidity: \(json["humidity"] ?? "nil")")
                    print("   - PM10: \(json["pm10"] ?? "nil")")
                    print("   - PM2.5: \(json["pm2_5"] ?? "nil")")

                    // Parse fetched_at string to Date
                    let dateFormatter = ISO8601DateFormatter()
                    var fetchedAt = Date()
                    if let fetchedAtStr = json["fetched_at"] as? String {
                        fetchedAt = dateFormatter.date(from: fetchedAtStr) ?? Date()
                    }

                    let weatherInfo = WeatherInfo(
                        temperature: json["temperature"] as? Double,
                        humidity: json["humidity"] as? Double,
                        precipitation: json["precipitation"] as? Double,
                        windSpeed: json["wind_speed"] as? Double,
                        pm10: json["pm10"] as? Double,
                        pm2_5: json["pm2_5"] as? Double,
                        fetchedAt: fetchedAt
                    )

                    print("🌤️ [FastAPI] WeatherInfo created: \(weatherInfo.weatherSummary)")
                    return weatherInfo
                }
            }

            print("❌ [FastAPI] Weather fetch failed with status: \(httpResponse.statusCode)")
            if let errorString = String(data: data, encoding: .utf8) {
                print("❌ [FastAPI] Error details: \(errorString)")
            }
            return nil

        } catch {
            print("❌ [FastAPI] Network error: \(error.localizedDescription)")
            return nil
        }
    }

    // MARK: - Tracking API

    /// Upload workout session data
    /// - Parameters:
    ///   - userId: FastAPI user ID (UUID)
    ///   - session: Workout session data
    /// - Returns: Success boolean
    func uploadWorkoutSession(userId: String, session: WorkoutSessionData) async -> Bool {
        guard let url = URL(string: "\(baseURL)/api/users/\(userId)/workout-sessions") else {
            print("❌ [FastAPI] Invalid workout session URL")
            return false
        }

        var request = URLRequest(url: url)
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        do {
            let encoder = JSONEncoder()
            request.httpBody = try encoder.encode(session)

            let (data, response) = try await apiSession.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                print("❌ [FastAPI] Invalid response")
                return false
            }

            if httpResponse.statusCode == 201 {
                print("✅ [FastAPI] Workout session uploaded successfully")
                return true
            } else {
                if let errorString = String(data: data, encoding: .utf8) {
                    print("❌ [FastAPI] Upload failed (\(httpResponse.statusCode)): \(errorString)")
                }
                return false
            }

        } catch {
            print("❌ [FastAPI] Network error: \(error.localizedDescription)")
            return false
        }
    }

    /// Upload hourly health data (upsert)
    /// - Parameters:
    ///   - userId: FastAPI user ID (UUID)
    ///   - hourlyData: Hourly health data
    /// - Returns: Success boolean
    func uploadHealthHourly(userId: String, hourlyData: HealthHourlyData) async -> Bool {
        guard let url = URL(string: "\(baseURL)/api/users/\(userId)/health-hourly") else {
            print("❌ [FastAPI] Invalid health hourly URL")
            return false
        }

        var request = URLRequest(url: url)
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.httpMethod = "PUT"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        do {
            let encoder = JSONEncoder()
            request.httpBody = try encoder.encode(hourlyData)

            let (data, response) = try await apiSession.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                print("❌ [FastAPI] Invalid response")
                return false
            }

            if httpResponse.statusCode == 200 {
                print("✅ [FastAPI] Health hourly data uploaded successfully")
                return true
            } else {
                if let errorString = String(data: data, encoding: .utf8) {
                    print("❌ [FastAPI] Upload failed (\(httpResponse.statusCode)): \(errorString)")
                }
                return false
            }

        } catch {
            print("❌ [FastAPI] Network error: \(error.localizedDescription)")
            return false
        }
    }

    /// Upload sleep session data
    /// - Parameters:
    ///   - userId: FastAPI user ID (UUID)
    ///   - session: Sleep session data
    /// - Returns: Success boolean
    func uploadSleepSession(userId: String, session: SleepSessionData) async -> Bool {
        guard let url = URL(string: "\(baseURL)/api/users/\(userId)/sleep-sessions") else {
            print("❌ [FastAPI] Invalid sleep session URL")
            return false
        }

        var request = URLRequest(url: url)
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        do {
            let encoder = JSONEncoder()
            request.httpBody = try encoder.encode(session)

            let (data, response) = try await apiSession.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                print("❌ [FastAPI] Invalid response")
                return false
            }

            if httpResponse.statusCode == 201 {
                print("✅ [FastAPI] Sleep session uploaded successfully")
                return true
            } else {
                if let errorString = String(data: data, encoding: .utf8) {
                    print("❌ [FastAPI] Upload failed (\(httpResponse.statusCode)): \(errorString)")
                }
                return false
            }

        } catch {
            print("❌ [FastAPI] Network error: \(error.localizedDescription)")
            return false
        }
    }

    /// Create time slot
    /// - Parameters:
    ///   - userId: FastAPI user ID (UUID)
    ///   - slot: Time slot data
    /// - Returns: Created time slot ID or nil
    func createTimeSlot(userId: String, slot: TimeSlotData) async -> String? {
        guard let url = URL(string: "\(baseURL)/api/users/\(userId)/time-slots") else {
            print("❌ [FastAPI] Invalid time slot URL")
            return nil
        }

        var request = URLRequest(url: url)
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        do {
            let encoder = JSONEncoder()
            request.httpBody = try encoder.encode(slot)

            let (data, response) = try await apiSession.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                print("❌ [FastAPI] Invalid response")
                return nil
            }

            if httpResponse.statusCode == 201 {
                if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                   let slotId = json["id"] as? String {
                    print("✅ [FastAPI] Time slot created: \(slotId)")
                    return slotId
                }
            } else {
                if let errorString = String(data: data, encoding: .utf8) {
                    print("❌ [FastAPI] Creation failed (\(httpResponse.statusCode)): \(errorString)")
                }
            }

            return nil

        } catch {
            print("❌ [FastAPI] Network error: \(error.localizedDescription)")
            return nil
        }
    }

    /// Create place
    /// - Parameters:
    ///   - userId: FastAPI user ID (UUID)
    ///   - place: Place data
    /// - Returns: Created place ID or nil
    func createPlace(userId: String, place: PlaceData) async -> String? {
        guard let url = URL(string: "\(baseURL)/api/users/\(userId)/places") else {
            print("❌ [FastAPI] Invalid place URL")
            return nil
        }

        var request = URLRequest(url: url)
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        do {
            let encoder = JSONEncoder()
            request.httpBody = try encoder.encode(place)

            let (data, response) = try await apiSession.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                print("❌ [FastAPI] Invalid response")
                return nil
            }

            if httpResponse.statusCode == 201 {
                if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                   let placeId = json["id"] as? String {
                    print("✅ [FastAPI] Place created: \(placeId)")
                    return placeId
                }
            } else {
                if let errorString = String(data: data, encoding: .utf8) {
                    print("❌ [FastAPI] Creation failed (\(httpResponse.statusCode)): \(errorString)")
                }
            }

            return nil

        } catch {
            print("❌ [FastAPI] Network error: \(error.localizedDescription)")
            return nil
        }
    }

    /// Get time slots for a date range
    /// - Parameters:
    ///   - userId: FastAPI user ID (UUID)
    ///   - start: Start date
    ///   - end: End date
    /// - Returns: Array of time slot data or nil
    func getTimeSlots(userId: String, start: Date, end: Date) async -> [TimeSlotRead]? {
        let formatter = ISO8601DateFormatter()
        let startStr = formatter.string(from: start)
        let endStr = formatter.string(from: end)

        guard let url = URL(string: "\(baseURL)/api/users/\(userId)/time-slots?start=\(startStr)&end=\(endStr)") else {
            print("❌ [FastAPI] Invalid time slots URL")
            return nil
        }

        var request = URLRequest(url: url)
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        do {
            let (data, response) = try await apiSession.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                print("❌ [FastAPI] Invalid response")
                return nil
            }

            if httpResponse.statusCode == 200 {
                let decoder = JSONDecoder()
                let slots = try decoder.decode([TimeSlotRead].self, from: data)
                print("✅ [FastAPI] Retrieved \(slots.count) time slots")
                return slots
            } else {
                if let errorString = String(data: data, encoding: .utf8) {
                    print("❌ [FastAPI] Fetch failed (\(httpResponse.statusCode)): \(errorString)")
                }
                return nil
            }

        } catch {
            print("❌ [FastAPI] Network error: \(error.localizedDescription)")
            return nil
        }
    }

    /// Get workout sessions for a date range
    /// - Parameters:
    ///   - userId: FastAPI user ID (UUID)
    ///   - start: Start date
    ///   - end: End date
    /// - Returns: Array of workout session data or nil
    func getWorkoutSessions(userId: String, start: Date, end: Date) async -> [WorkoutSessionRead]? {
        let formatter = ISO8601DateFormatter()
        let startStr = formatter.string(from: start)
        let endStr = formatter.string(from: end)

        guard let url = URL(string: "\(baseURL)/api/users/\(userId)/workout-sessions?start=\(startStr)&end=\(endStr)") else {
            print("❌ [FastAPI] Invalid workout sessions URL")
            return nil
        }

        var request = URLRequest(url: url)
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        do {
            let (data, response) = try await apiSession.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                print("❌ [FastAPI] Invalid response")
                return nil
            }

            if httpResponse.statusCode == 200 {
                let decoder = JSONDecoder()
                let sessions = try decoder.decode([WorkoutSessionRead].self, from: data)
                print("✅ [FastAPI] Retrieved \(sessions.count) workout sessions")
                return sessions
            } else {
                if let errorString = String(data: data, encoding: .utf8) {
                    print("❌ [FastAPI] Fetch failed (\(httpResponse.statusCode)): \(errorString)")
                }
                return nil
            }

        } catch {
            print("❌ [FastAPI] Network error: \(error.localizedDescription)")
            return nil
        }
    }

    /// Upload complete timeline with workout session and time slots
    /// - Parameters:
    ///   - userId: FastAPI user ID (UUID)
    ///   - timeline: Timeline record to upload
    /// - Returns: Success boolean
    func uploadTimelineComplete(userId: String, timeline: TimelineRecord) async -> Bool {
        // 1. Upload workout session
        let workoutData = timeline.toWorkoutSessionData()
        let workoutSuccess = await uploadWorkoutSession(userId: userId, session: workoutData)

        guard workoutSuccess else {
            print("❌ [FastAPI] Failed to upload workout session for timeline")
            return false
        }

        // 2. Upload time slots from checkpoints
        var allSlotsSuccess = true
        for checkpoint in timeline.checkpoints {
            let slotData = checkpoint.toTimeSlotData()
            let slotId = await createTimeSlot(userId: userId, slot: slotData)
            if slotId == nil {
                print("⚠️ [FastAPI] Failed to upload time slot for checkpoint")
                allSlotsSuccess = false
            }
        }

        return workoutSuccess && allSlotsSuccess
    }

    // MARK: - Appliance API

    /// Fetch appliances and their smart-status from backend and convert to UI models
    /// - Parameter userId: FastAPI user ID
    /// - Returns: Array of appliances mapped to UI state
    func fetchApplianceItems(userId: String) async -> [ApplianceItem] {
        async let applianceListTask = getApplianceList(userId: userId)
        async let smartStatusTask = getSmartStatus(userId: userId)

        let appliances = await applianceListTask ?? []
        let smartStatus = await smartStatusTask

        // Debug raw payloads to spot missing codes/fields that cause drops
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]

        if let data = try? encoder.encode(appliances),
           let jsonString = String(data: data, encoding: .utf8) {
            print("🧾 [FastAPI][Debug] Appliance list (\(appliances.count)):\n\(jsonString)")
        } else {
            print("⚠️ [FastAPI][Debug] Failed to encode appliance list (\(appliances.count))")
        }

        if let statusArray = smartStatus?.appliances {
            if let data = try? encoder.encode(statusArray),
               let jsonString = String(data: data, encoding: .utf8) {
                print("🧾 [FastAPI][Debug] Smart status (\(statusArray.count)):\n\(jsonString)")
            } else {
                print("⚠️ [FastAPI][Debug] Failed to encode smart status (\(statusArray.count))")
            }

            let summary = statusArray.map { status in
                let keys = status.currentSettings?.keys.sorted().joined(separator: ",") ?? "none"
                return "\(status.applianceType) isOn=\(status.isOn) keys=[\(keys)]"
            }.joined(separator: " | ")
            print("📊 [FastAPI][Debug] Smart status summary: \(summary)")
        } else {
            print("⚠️ [FastAPI][Debug] No smart status data")
        }

        let statusByType: [ApplianceType: BackendApplianceStatus] = Dictionary(
            (smartStatus?.appliances ?? []).compactMap { status in
                guard let type = ApplianceType.resolve(
                    backendCode: nil,
                    backendLabel: status.applianceType
                ) else {
                    return nil
                }
                return (type, status)
            },
            uniquingKeysWith: { first, _ in first }
        )

        var mapped: [ApplianceItem] = []

        for appliance in appliances {
            guard let resolvedType = ApplianceType.resolve(backendCode: appliance.applianceCode) else {
                print("⚠️ [FastAPI][Debug] Unknown appliance_code \(appliance.applianceCode) for id=\(appliance.id), dropping")
                continue
            }

            let matchedStatus = statusByType[resolvedType]
            if matchedStatus == nil {
                print("⚠️ [FastAPI][Debug] No smart status for id=\(appliance.id) type=\(resolvedType.displayName)")
            }

            if let item = ApplianceItem(backend: appliance, status: matchedStatus) {
                mapped.append(item)
            } else {
                let keys = matchedStatus?.currentSettings?.keys.sorted().joined(separator: ",") ?? "none"
                print("⚠️ [FastAPI][Debug] Failed to build ApplianceItem id=\(appliance.id) type=\(resolvedType.displayName) settingsKeys=[\(keys)]")
            }
        }

        return mapped
    }

    private func getApplianceList(userId: String) async -> [BackendAppliance]? {
        let urlString = "\(baseURL)/api/appliances/user/\(userId)"
        guard let url = URL(string: urlString) else {
            print("❌ [FastAPI] Invalid appliances URL")
            return nil
        }

        var request = URLRequest(url: url)
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        do {
            let (data, response) = try await apiSession.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                print("❌ [FastAPI] Invalid response for appliance list")
                return nil
            }

            if httpResponse.statusCode == 200 {
                let decoder = JSONDecoder()
                let appliances = try decoder.decode([BackendAppliance].self, from: data)
                print("✅ [FastAPI] Retrieved \(appliances.count) appliances")
                return appliances
            } else {
                if let errorString = String(data: data, encoding: .utf8) {
                    print("❌ [FastAPI] Get appliances failed (\(httpResponse.statusCode)): \(errorString)")
                }
                return nil
            }

        } catch {
            print("❌ [FastAPI] Network error fetching appliances: \(error.localizedDescription)")
            return nil
        }
    }

    private func getSmartStatus(userId: String) async -> SmartStatusResponse? {
        guard let url = URL(string: "\(baseURL)/api/appliances/smart-status/\(userId)") else {
            print("❌ [FastAPI] Invalid URL for smart status")
            return nil
        }

        var request = URLRequest(url: url)
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.httpMethod = "GET"

        do {
            let (data, response) = try await apiSession.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                print("❌ [FastAPI] Invalid response for smart status")
                return nil
            }

            if httpResponse.statusCode == 200 {
                let decoder = JSONDecoder()
                let status = try decoder.decode(SmartStatusResponse.self, from: data)
                print("✅ [FastAPI] Retrieved smart status for \(status.appliances.count) appliances")
                return status
            } else {
                if let errorString = String(data: data, encoding: .utf8) {
                    print("❌ [FastAPI] Get smart status failed (\(httpResponse.statusCode)): \(errorString)")
                }
                return nil
            }

        } catch {
            print("❌ [FastAPI] Network error fetching smart status: \(error.localizedDescription)")
            return nil
        }
    }

    /// Smart-control an appliance (on/off/set) via `/api/appliances/smart-control/{user_id}`
    /// - Parameters:
    ///   - userId: FastAPI user ID
    ///   - applianceType: Appliance type label expected by backend (예: "에어컨", "조명")
    ///   - action: "on", "off", "set"
    ///   - settings: Optional settings payload (numeric fan speeds, etc.)
    /// - Returns: Success boolean
    func controlAppliance(
        userId: String,
        applianceType: String,
        action: String,
        settings: [String: Any]?
    ) async -> Bool {
        guard let url = URL(string: "\(baseURL)/api/appliances/smart-control/\(userId)") else {
            print("❌ [FastAPI] Invalid URL for smart-control")
            return false
        }

        var request = URLRequest(url: url)
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        var body: [String: Any] = [
            "appliance_type": applianceType,
            "action": action
        ]

        if let settings, !settings.isEmpty {
            body["settings"] = settings
        }

        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: body)

            let (data, response) = try await apiSession.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                print("❌ [FastAPI] Invalid response for smart-control")
                return false
            }

            if httpResponse.statusCode == 200 {
                print("✅ [FastAPI] Smart-control success (\(applianceType), action: \(action))")
                return true
            } else {
                if let errorString = String(data: data, encoding: .utf8) {
                    print("❌ [FastAPI] Smart-control failed (\(httpResponse.statusCode)): \(errorString)")
                }
                return false
            }

        } catch {
            print("❌ [FastAPI] Network error for smart-control: \(error.localizedDescription)")
            return false
        }
    }

    /// Update appliance configuration
    /// - Parameters:
    ///   - applianceId: Appliance ID
    ///   - applianceType: Type of appliance (ac, tv, light, etc.)
    ///   - config: Configuration dictionary to update
    /// - Returns: Success boolean
    func updateApplianceConfig(applianceId: String, applianceType: ApplianceType, config: [String: Any]) async -> Bool {
        let endpoint: String
        switch applianceType {
        case .airConditioner:
            endpoint = "ac"
        case .tv:
            endpoint = "tv"
        case .lighting:
            endpoint = "light"
        case .airPurifier:
            endpoint = "air_purifier"
        case .humidifier:
            endpoint = "humidifier"
        case .dehumidifier:
            endpoint = "dehumidifier"
        }

        guard let url = URL(string: "\(baseURL)/api/appliances/config/\(endpoint)") else {
            print("❌ [FastAPI] Invalid URL for update config")
            return false
        }

        var request = URLRequest(url: url)
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        var body = config
        body["appliance_id"] = applianceId

        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: body)

            let (data, response) = try await apiSession.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                print("❌ [FastAPI] Invalid response for update config")
                return false
            }

            if httpResponse.statusCode == 200 || httpResponse.statusCode == 201 {
                print("✅ [FastAPI] Appliance config updated successfully")
                return true
            } else {
                if let errorString = String(data: data, encoding: .utf8) {
                    print("❌ [FastAPI] Update config failed (\(httpResponse.statusCode)): \(errorString)")
                }
                return false
            }

        } catch {
            print("❌ [FastAPI] Network error updating config: \(error.localizedDescription)")
            return false
        }
    }

    // MARK: - Chat API

    /// Send chat message and get AI response with appliance suggestions
    /// - Parameters:
    ///   - userId: User ID
    ///   - message: User's message text
    ///   - personaContext: Optional persona context (final prompt)
    ///   - characterId: Optional character/persona ID
    /// - Returns: Chat response with AI message and suggestions
    func sendChatMessage(
        userId: String,
        message: String,
        personaContext: String? = nil,
        characterId: String? = nil
    ) async -> ChatMessageResponse? {
        guard let url = URL(string: "\(baseURL)/api/chat/\(userId)/message") else {
            print("❌ [FastAPI] Invalid URL for send chat message")
            return nil
        }

        var request = URLRequest(url: url)
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        var body: [String: Any] = ["message": message]

        if let context = personaContext {
            body["context"] = context
        }

        if let charId = characterId {
            body["character_id"] = charId
        }

        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: body)

            let (data, response) = try await apiSession.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                print("❌ [FastAPI] Invalid response for chat message")
                return nil
            }

            if httpResponse.statusCode == 200 {
                let decoder = JSONDecoder()
                let chatResponse = try decoder.decode(ChatMessageResponse.self, from: data)
                print("✅ [FastAPI] Chat message sent successfully")
                return chatResponse
            } else {
                if let errorString = String(data: data, encoding: .utf8) {
                    print("❌ [FastAPI] Chat message failed (\(httpResponse.statusCode)): \(errorString)")
                }
                return nil
            }

        } catch {
            print("❌ [FastAPI] Network error sending chat message: \(error.localizedDescription)")
            return nil
        }
    }

    /// Approve/modify appliance changes from chat suggestion
    /// - Parameters:
    ///   - userId: User ID
    ///   - userResponse: User's approval response text (e.g., "좋아", "에어컨은 24도로")
    ///   - originalPlan: Original appliance control plan from suggestions
    /// - Returns: ApplianceApprovalResponse
    func approveChatChanges(userId: String, userResponse: String, originalPlan: [String: Any]) async -> ApplianceApprovalResponse? {
        guard let url = URL(string: "\(baseURL)/api/chat/\(userId)/approve") else {
            print("❌ [FastAPI] Invalid URL for approve chat changes")
            return nil
        }

        var request = URLRequest(url: url)
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: Any] = [
            "user_response": userResponse,
            "original_plan": originalPlan
        ]

        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: body)

            let (data, response) = try await apiSession.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                print("❌ [FastAPI] Invalid response for approve changes")
                return nil
            }

            if httpResponse.statusCode == 200 {
                let decoder = JSONDecoder()
                let approvalResponse = try decoder.decode(ApplianceApprovalResponse.self, from: data)
                print("✅ [FastAPI] Appliance changes approved successfully")
                return approvalResponse
            } else {
                if let errorString = String(data: data, encoding: .utf8) {
                    print("❌ [FastAPI] Approve changes failed (\(httpResponse.statusCode)): \(errorString)")
                }
                return nil
            }

        } catch {
            print("❌ [FastAPI] Network error approving changes: \(error.localizedDescription)")
            return nil
        }
    }

    /// Get chat conversation history
    /// - Parameters:
    ///   - userId: User ID
    ///   - personaId: Optional persona ID to filter history
    ///   - limit: Maximum number of messages to retrieve (default 50)
    /// - Returns: Array of chat history items
    func getChatHistory(userId: String, personaId: String? = nil, limit: Int = 50) async -> [ChatHistoryItem]? {
        var urlString = "\(baseURL)/api/chat/\(userId)/history?limit=\(limit)"
        if let personaId = personaId {
            urlString += "&persona_id=\(personaId)"
        }

        guard let url = URL(string: urlString) else {
            print("❌ [FastAPI] Invalid URL for chat history")
            return nil
        }

        var request = URLRequest(url: url)
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.httpMethod = "GET"

        do {
            let (data, response) = try await apiSession.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                print("❌ [FastAPI] Invalid response for chat history")
                return nil
            }

            if httpResponse.statusCode == 200 {
                let decoder = JSONDecoder()
                let historyResponse = try decoder.decode(ChatHistoryResponse.self, from: data)
                print("✅ [FastAPI] Retrieved \(historyResponse.conversationHistory.count) chat messages")
                return historyResponse.conversationHistory
            } else {
                if let errorString = String(data: data, encoding: .utf8) {
                    print("❌ [FastAPI] Get chat history failed (\(httpResponse.statusCode)): \(errorString)")
                }
                return nil
            }

        } catch {
            print("❌ [FastAPI] Network error getting chat history: \(error.localizedDescription)")
            return nil
        }
    }

    /// Clear chat session
    /// - Parameter userId: User ID
    /// - Returns: Success boolean
    func clearChatSession(userId: String) async -> Bool {
        guard let url = URL(string: "\(baseURL)/api/chat/\(userId)/session") else {
            print("❌ [FastAPI] Invalid URL for clear session")
            return false
        }

        var request = URLRequest(url: url)
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.httpMethod = "DELETE"

        do {
            let (data, response) = try await apiSession.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                print("❌ [FastAPI] Invalid response for clear session")
                return false
            }

            if httpResponse.statusCode == 200 {
                print("✅ [FastAPI] Chat session cleared successfully")
                return true
            } else {
                if let errorString = String(data: data, encoding: .utf8) {
                    print("❌ [FastAPI] Clear session failed (\(httpResponse.statusCode)): \(errorString)")
                }
                return false
            }

        } catch {
            print("❌ [FastAPI] Network error clearing session: \(error.localizedDescription)")
            return false
        }
    }

    // MARK: - Sendbird Auth API

    /// Get Sendbird authentication token for user
    /// - Parameter userId: User ID (email or UUID)
    /// - Returns: Sendbird auth response with user_id and access_token
    func getSendbirdUserToken(userId: String, nickname: String? = nil) async -> (userId: String, accessToken: String)? {
        guard let url = URL(string: "\(baseURL)/api/sendbird/auth/token") else {
            print("❌ [FastAPI] Invalid URL for Sendbird user token")
            return nil
        }

        var request = URLRequest(url: url)
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        var body: [String: Any] = ["user_id": userId]
        if let nickname = nickname {
            body["nickname"] = nickname
        }

        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: body)

            let (data, response) = try await apiSession.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                print("❌ [FastAPI] Invalid response for Sendbird user token")
                return nil
            }

            if httpResponse.statusCode == 200 {
                if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                   let userId = json["user_id"] as? String,
                   let accessToken = json["access_token"] as? String {
                    print("✅ [FastAPI] Sendbird user token retrieved for: \(userId)")
                    return (userId, accessToken)
                }
            } else {
                if let errorString = String(data: data, encoding: .utf8) {
                    print("❌ [FastAPI] Get Sendbird user token failed (\(httpResponse.statusCode)): \(errorString)")
                }
                return nil
            }

            return nil

        } catch {
            print("❌ [FastAPI] Network error getting Sendbird user token: \(error.localizedDescription)")
            return nil
        }
    }

    /// Get Sendbird AI assistant token
    /// - Returns: AI assistant user_id and access_token
    func getSendbirdAIToken() async -> (userId: String, accessToken: String)? {
        guard let url = URL(string: "\(baseURL)/api/sendbird/auth/ai-token") else {
            print("❌ [FastAPI] Invalid URL for Sendbird AI token")
            return nil
        }

        var request = URLRequest(url: url)
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        do {
            let (data, response) = try await apiSession.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                print("❌ [FastAPI] Invalid response for Sendbird AI token")
                return nil
            }

            if httpResponse.statusCode == 200 {
                if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                   let userId = json["user_id"] as? String,
                   let accessToken = json["access_token"] as? String {
                    print("✅ [FastAPI] Sendbird AI token retrieved: \(userId)")
                    return (userId, accessToken)
                }
            } else {
                if let errorString = String(data: data, encoding: .utf8) {
                    print("❌ [FastAPI] Get Sendbird AI token failed (\(httpResponse.statusCode)): \(errorString)")
                }
                return nil
            }

            return nil

        } catch {
            print("❌ [FastAPI] Network error getting Sendbird AI token: \(error.localizedDescription)")
            return nil
        }
    }

    // MARK: - HRV (Heart Rate Variability) API

    /// Sync HRV data from HealthKit to backend
    /// - Parameters:
    ///   - userId: User ID (email or UUID)
    ///   - hrvValue: HRV value in milliseconds
    ///   - measuredAt: When the HRV was measured
    /// - Returns: Sync response with fatigue level
    func syncHRV(userId: String, hrvValue: Double, measuredAt: Date) async -> HRVSyncResponse? {
        guard let url = URL(string: "\(baseURL)/api/health/hrv") else {
            print("❌ [FastAPI] Invalid URL for HRV sync")
            return nil
        }

        var request = URLRequest(url: url)
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let encoder = JSONEncoder()
        encoder.dateEncodingStrategy = .iso8601

        let requestBody = HRVSyncRequest(
            userId: userId,
            hrvValue: hrvValue,
            measuredAt: measuredAt
        )

        do {
            request.httpBody = try encoder.encode(requestBody)

            let (data, response) = try await apiSession.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                print("❌ [FastAPI] Invalid response for HRV sync")
                return nil
            }

            if httpResponse.statusCode == 200 {
                let decoder = JSONDecoder()
                decoder.dateDecodingStrategy = .iso8601

                let syncResponse = try decoder.decode(HRVSyncResponse.self, from: data)
                print("✅ [FastAPI] HRV synced successfully")
                return syncResponse
            } else {
                if let errorString = String(data: data, encoding: .utf8) {
                    print("❌ [FastAPI] HRV sync failed (\(httpResponse.statusCode)): \(errorString)")
                }
                return nil
            }

        } catch {
            print("❌ [FastAPI] Network error syncing HRV: \(error.localizedDescription)")
            return nil
        }
    }

    // MARK: - Calls API

    /// Trigger auto-call when user approaches home (GPS-based)
    /// - Parameter userId: User ID
    /// - Returns: Success boolean
    func triggerAutoCall(userId: String) async -> Bool {
        guard let url = URL(string: "\(baseURL)/api/calls/trigger/\(userId)") else {
            print("❌ [FastAPI] Invalid URL for trigger auto-call")
            return false
        }

        var request = URLRequest(url: url)
        request.cachePolicy = .reloadIgnoringLocalCacheData
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        do {
            let (data, response) = try await apiSession.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                print("❌ [FastAPI] Invalid response for trigger auto-call")
                return false
            }

            if httpResponse.statusCode == 200 {
                print("✅ [FastAPI] Auto-call triggered successfully")
                return true
            } else {
                if let errorString = String(data: data, encoding: .utf8) {
                    print("❌ [FastAPI] Trigger auto-call failed (\(httpResponse.statusCode)): \(errorString)")
                }
                return false
            }

        } catch {
            print("❌ [FastAPI] Network error triggering auto-call: \(error.localizedDescription)")
            return false
        }
    }
}

// MARK: - Models are now imported from separate files
// See: ChatModels.swift, UserModels.swift, CharacterModels.swift, FatigueModels.swift, etc.
