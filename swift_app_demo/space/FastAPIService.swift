import Foundation

class FastAPIService {
    static let shared = FastAPIService()

    private let baseURL = "http://13.125.85.158:11325"

    private init() {}

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
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: String] = ["email": email]

        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: body)

            let (data, response) = try await URLSession.shared.data(for: request)

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
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        do {
            let (data, response) = try await URLSession.shared.data(for: request)

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
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        do {
            let (data, response) = try await URLSession.shared.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                print("❌ [FastAPI] Invalid response")
                return nil
            }

            if httpResponse.statusCode == 200 {
                // Print raw response for debugging
                if let jsonString = String(data: data, encoding: .utf8) {
                    print("📦 [FastAPI] Weather API Response: \(jsonString)")
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
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        do {
            let encoder = JSONEncoder()
            request.httpBody = try encoder.encode(session)

            let (data, response) = try await URLSession.shared.data(for: request)

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
        request.httpMethod = "PUT"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        do {
            let encoder = JSONEncoder()
            request.httpBody = try encoder.encode(hourlyData)

            let (data, response) = try await URLSession.shared.data(for: request)

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
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        do {
            let encoder = JSONEncoder()
            request.httpBody = try encoder.encode(session)

            let (data, response) = try await URLSession.shared.data(for: request)

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
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        do {
            let encoder = JSONEncoder()
            request.httpBody = try encoder.encode(slot)

            let (data, response) = try await URLSession.shared.data(for: request)

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
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        do {
            let encoder = JSONEncoder()
            request.httpBody = try encoder.encode(place)

            let (data, response) = try await URLSession.shared.data(for: request)

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
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        do {
            let (data, response) = try await URLSession.shared.data(for: request)

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
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        do {
            let (data, response) = try await URLSession.shared.data(for: request)

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
}
