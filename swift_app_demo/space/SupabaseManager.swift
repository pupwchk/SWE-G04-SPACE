//
//  SupabaseManager.swift
//  space
//
//  Supabase authentication and database manager
//

import Foundation

/// Manages Supabase authentication and API calls
class SupabaseManager: ObservableObject {
    static let shared = SupabaseManager()

    // Supabase project configuration
    private let supabaseURL = "https://aghsjspkzivcpibwwzvu.supabase.co"
    private let supabaseAnonKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFnaHNqc3Breml2Y3BpYnd3enZ1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI0OTI0OTMsImV4cCI6MjA3ODA2ODQ5M30.vtas9X3hNPoJaepihOc2C3Yxx5l38U3_-bTkKnYLAew"

    @Published var currentUser: SupabaseUser?
    @Published var isAuthenticated = false

    private init() {
        // Check if user session exists
        checkSession()
    }

    // MARK: - Authentication Methods

    /// Sign up a new user with email and password
    func signUp(email: String, password: String, name: String) async throws -> SupabaseUser {
        guard let url = URL(string: "\(supabaseURL)/auth/v1/signup") else {
            throw AuthError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue(supabaseAnonKey, forHTTPHeaderField: "apikey")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: Any] = [
            "email": email,
            "password": password,
            "options": [
                "data": [
                    "name": name
                ],
                "email_redirect_to": "\(supabaseURL)/auth/v1/verify"
            ]
        ]

        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (data, response) = try await URLSession.shared.data(for: request)

        // Debug: Print raw response
        if let responseString = String(data: data, encoding: .utf8) {
            print("📝 Sign Up Response: \(responseString)")
        }

        guard let httpResponse = response as? HTTPURLResponse else {
            throw AuthError.invalidResponse
        }

        print("📊 Status Code: \(httpResponse.statusCode)")

        if httpResponse.statusCode != 200 {
            // Parse error response
            if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                print("  Error JSON: \(json)")
                if let message = json["msg"] as? String ?? json["error_description"] as? String ?? json["message"] as? String {
                    throw AuthError.serverError(message)
                }
            }
            throw AuthError.serverError("Sign up failed with status code \(httpResponse.statusCode)")
        }

        do {
            let authResponse = try JSONDecoder().decode(AuthResponse.self, from: data)

            // Check if response contains session (instant login) or just user (email confirmation required)
            if let session = authResponse.getSession(), let userObj = authResponse.user {
                // Normal flow with session - save it
                saveSession(session)

                let user = SupabaseUser(
                    id: userObj.id,
                    email: userObj.email,
                    name: name
                )

                // Create user profile in database
                try await createUserProfile(userId: userObj.id, email: userObj.email, name: name, accessToken: session.accessToken)

                // Register user with FastAPI backend
                Task {
                    if let fastAPIUserId = await FastAPIService.shared.registerUser(email: userObj.email) {
                        UserDefaults.standard.set(fastAPIUserId, forKey: "fastapi_user_id")
                        print("✅ [FastAPI] User registered with ID: \(fastAPIUserId)")
                    }
                }

                await MainActor.run {
                    self.currentUser = user
                    self.isAuthenticated = true
                }

                // Send authentication status to Watch
                WatchConnectivityManager.shared.sendAuthenticationStatus(
                    isAuthenticated: true,
                    userId: user.id,
                    userEmail: user.email
                )

                // Load tagged locations for proximity detection
                Task {
                    await TaggedLocationManager.shared.loadTaggedLocations()
                }

                return user
            } else if let userId = authResponse.id, let userEmail = authResponse.email {
                // Email confirmation required - no session yet
                print("✉️ Signup successful but email confirmation is required")
                print("✉️ User ID: \(userId), Email: \(userEmail)")

                // For development: just show success message without requiring confirmation
                _ = SupabaseUser(
                    id: userId,
                    email: userEmail,
                    name: authResponse.userMetadata?.name ?? name
                )

                throw AuthError.emailConfirmationRequired(userEmail)
            } else {
                throw AuthError.serverError("Invalid response format")
            }
        } catch let error as AuthError {
            throw error
        } catch {
            print("  JSON Decoding Error: \(error)")
            if let decodingError = error as? DecodingError {
                print("  Decoding Error Details: \(decodingError)")
            }
            throw AuthError.serverError("Failed to parse server response: \(error.localizedDescription)")
        }
    }

    /// Sign in with email and password
    func signIn(email: String, password: String) async throws -> SupabaseUser {
        guard let url = URL(string: "\(supabaseURL)/auth/v1/token?grant_type=password") else {
            throw AuthError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue(supabaseAnonKey, forHTTPHeaderField: "apikey")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: String] = [
            "email": email,
            "password": password
        ]

        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (data, response) = try await URLSession.shared.data(for: request)

        // Debug: Print raw response
        if let responseString = String(data: data, encoding: .utf8) {
            print("📝 Sign In Response: \(responseString)")
        }

        guard let httpResponse = response as? HTTPURLResponse else {
            throw AuthError.invalidResponse
        }

        print("📊 Status Code: \(httpResponse.statusCode)")

        if httpResponse.statusCode != 200 {
            // Parse error response
            if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any] {
                print("  Error JSON: \(json)")
                if let message = json["error_description"] as? String ?? json["msg"] as? String ?? json["message"] as? String {
                    throw AuthError.serverError(message)
                }
            }
            throw AuthError.invalidCredentials
        }

        do {
            let authResponse = try JSONDecoder().decode(AuthResponse.self, from: data)

            print(" Auth response decoded successfully")

            // Try to get session from either nested or top-level fields
            guard let session = authResponse.getSession() else {
                print("  No session found in response")
                throw AuthError.serverError("Login failed - no session returned")
            }

            print(" Session retrieved: \(session.accessToken.prefix(20))...")

            // Get user object
            guard let userObj = authResponse.user else {
                print("  No user object in response")
                throw AuthError.serverError("Login failed - no user data")
            }

            print(" User object validated: \(userObj.email)")

            // Save session
            saveSession(session)

            let userName = userObj.userMetadata?.name ?? ""
            let user = SupabaseUser(
                id: userObj.id,
                email: userObj.email,
                name: userName
            )

            print(" About to set authenticated state")

            // Register user with FastAPI backend (or ensure they exist)
            // Then connect to Sendbird with the FastAPI user ID
            Task {
                if let fastAPIUserId = await FastAPIService.shared.registerUser(email: userObj.email) {
                    UserDefaults.standard.set(fastAPIUserId, forKey: "fastapi_user_id")
                    print("✅ [FastAPI] User registered with ID: \(fastAPIUserId)")

                    // Connect to Sendbird Chat using FastAPI DB UUID
                    do {
                        try await SendbirdManager.shared.connect(userId: fastAPIUserId)
                        print("✅ [Sendbird] Connected after login with FastAPI user ID: \(fastAPIUserId)")
                    } catch {
                        print("⚠️ [Sendbird] Failed to connect: \(error)")
                    }
                } else {
                    print("❌ [FastAPI] Failed to register user, cannot connect to Sendbird")
                }
            }

            await MainActor.run {
                self.currentUser = user
                self.isAuthenticated = true
                print(" isAuthenticated set to true")
            }

            // Send authentication status to Watch
            WatchConnectivityManager.shared.sendAuthenticationStatus(
                isAuthenticated: true,
                userId: user.id,
                userEmail: user.email
            )

            // Load tagged locations for proximity detection
            Task {
                await TaggedLocationManager.shared.loadTaggedLocations()
            }

            print(" Returning user: \(user.email)")
            return user
        } catch let error as AuthError {
            throw error
        } catch {
            print("  JSON Decoding Error: \(error)")
            if let decodingError = error as? DecodingError {
                print("  Decoding Error Details: \(decodingError)")
            }
            throw AuthError.serverError("Failed to parse server response: \(error.localizedDescription)")
        }
    }

    /// Sign out the current user
    func signOut() async throws {
        guard let accessToken = getAccessToken() else {
            throw AuthError.notAuthenticated
        }

        guard let url = URL(string: "\(supabaseURL)/auth/v1/logout") else {
            throw AuthError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue(supabaseAnonKey, forHTTPHeaderField: "apikey")
        request.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")

        let (_, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse,
              httpResponse.statusCode == 204 else {
            throw AuthError.serverError("Sign out failed")
        }

        // Clear session
        clearSession()

        await MainActor.run {
            self.currentUser = nil
            self.isAuthenticated = false
        }

        // Send authentication status to Watch
        WatchConnectivityManager.shared.sendAuthenticationStatus(
            isAuthenticated: false,
            userId: nil,
            userEmail: nil
        )
    }

    // MARK: - Database Operations

    // MARK: - Profile Management

    /// Fetch user profile from database
    func fetchUserProfile() async throws -> UserProfile {
        guard let accessToken = getAccessToken() else {
            throw AuthError.notAuthenticated
        }

        guard let userId = currentUser?.id else {
            throw AuthError.notAuthenticated
        }

        guard let url = URL(string: "\(supabaseURL)/rest/v1/user_profiles?id=eq.\(userId)&select=*") else {
            throw AuthError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue(supabaseAnonKey, forHTTPHeaderField: "apikey")
        request.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw AuthError.invalidResponse
        }

        if httpResponse.statusCode != 200 {
            if let responseString = String(data: data, encoding: .utf8) {
                print("  Fetch profile failed: \(responseString)")
            }
            throw AuthError.serverError("Failed to fetch profile")
        }

        let profiles = try JSONDecoder().decode([UserProfile].self, from: data)
        guard let profile = profiles.first else {
            throw AuthError.serverError("Profile not found")
        }

        return profile
    }

    /// Update user profile
    func updateUserProfile(name: String?, birthday: String?, avatarUrl: String?) async throws {
        guard let accessToken = getAccessToken() else {
            throw AuthError.notAuthenticated
        }

        guard let userId = currentUser?.id else {
            throw AuthError.notAuthenticated
        }

        guard let url = URL(string: "\(supabaseURL)/rest/v1/user_profiles?id=eq.\(userId)") else {
            throw AuthError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "PATCH"
        request.setValue(supabaseAnonKey, forHTTPHeaderField: "apikey")
        request.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        var body: [String: Any] = [:]
        if let name = name {
            body["name"] = name
        }
        if let birthday = birthday {
            body["birthday"] = birthday
        }
        if let avatarUrl = avatarUrl {
            body["avatar_url"] = avatarUrl
        }

        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw AuthError.invalidResponse
        }

        if httpResponse.statusCode != 200 && httpResponse.statusCode != 204 {
            if let responseString = String(data: data, encoding: .utf8) {
                print("  Update profile failed: \(responseString)")
            }
            throw AuthError.serverError("Failed to update profile")
        }

        print(" Profile updated successfully")
    }

    // MARK: - Settings Management

    /// Fetch user settings
    func fetchUserSettings() async throws -> UserSettings {
        guard let accessToken = getAccessToken() else {
            throw AuthError.notAuthenticated
        }

        guard let userId = currentUser?.id else {
            throw AuthError.notAuthenticated
        }

        guard let url = URL(string: "\(supabaseURL)/rest/v1/user_settings?user_id=eq.\(userId)&select=*") else {
            throw AuthError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue(supabaseAnonKey, forHTTPHeaderField: "apikey")
        request.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw AuthError.invalidResponse
        }

        if httpResponse.statusCode != 200 {
            if let responseString = String(data: data, encoding: .utf8) {
                print("  Fetch settings failed: \(responseString)")
            }
            throw AuthError.serverError("Failed to fetch settings")
        }

        let settings = try JSONDecoder().decode([UserSettings].self, from: data)
        guard let userSettings = settings.first else {
            // Return default settings if not found
            return UserSettings.default(userId: userId)
        }

        return userSettings
    }

    /// Update user settings
    func updateUserSettings(_ settings: UserSettings) async throws {
        guard let accessToken = getAccessToken() else {
            throw AuthError.notAuthenticated
        }

        guard let userId = currentUser?.id else {
            throw AuthError.notAuthenticated
        }

        guard let url = URL(string: "\(supabaseURL)/rest/v1/user_settings?user_id=eq.\(userId)") else {
            throw AuthError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "PATCH"
        request.setValue(supabaseAnonKey, forHTTPHeaderField: "apikey")
        request.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let encoder = JSONEncoder()
        encoder.keyEncodingStrategy = .convertToSnakeCase
        request.httpBody = try encoder.encode(settings)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw AuthError.invalidResponse
        }

        if httpResponse.statusCode != 200 && httpResponse.statusCode != 204 {
            if let responseString = String(data: data, encoding: .utf8) {
                print("  Update settings failed: \(responseString)")
            }
            throw AuthError.serverError("Failed to update settings")
        }

        print(" Settings updated successfully")
    }

    // MARK: - Persona Management

    /// Lazy initialization of Persona Repository
    private lazy var personaRepository: PersonaRepository = {
        let service = SupabaseService(
            baseURL: supabaseURL,
            apiKey: supabaseAnonKey,
            tokenProvider: { [weak self] in
                return self?.getAccessToken()
            }
        )
        return PersonaRepository(service: service)
    }()

    /// Fetch all adjectives
    func fetchAdjectives() async throws -> [Adjective] {
        return try await personaRepository.fetchAdjectives()
    }

    /// Fetch user personas
    func fetchPersonas() async throws -> [Persona] {
        guard let userId = currentUser?.id else {
            throw AuthError.notAuthenticated
        }

        return try await personaRepository.fetchPersonas(userId: userId)
    }

    /// Create a new persona
    func createPersona(nickname: String, adjectiveIds: [String], customInstructions: String?) async throws -> Persona {
        guard let userId = currentUser?.id else {
            throw AuthError.notAuthenticated
        }

        // Fetch adjectives to generate final prompt
        let adjectives = try await fetchAdjectives()
        let finalPrompt = personaRepository.generateFinalPrompt(
            adjectiveIds: adjectiveIds,
            customInstructions: customInstructions,
            adjectives: adjectives
        )

        let request = CreatePersonaRequest(
            userId: userId,
            nickname: nickname,
            adjectiveIds: adjectiveIds,
            customInstructions: customInstructions,
            finalPrompt: finalPrompt
        )

        let persona = try await personaRepository.createPersona(request)
        print(" Persona created successfully")
        return persona
    }

    /// Update a persona
    func updatePersona(personaId: String, nickname: String, adjectiveIds: [String], customInstructions: String?) async throws {
        // Fetch adjectives to generate final prompt
        let adjectives = try await fetchAdjectives()
        let finalPrompt = personaRepository.generateFinalPrompt(
            adjectiveIds: adjectiveIds,
            customInstructions: customInstructions,
            adjectives: adjectives
        )

        let request = UpdatePersonaRequest(
            nickname: nickname,
            adjectiveIds: adjectiveIds,
            customInstructions: customInstructions,
            finalPrompt: finalPrompt
        )

        try await personaRepository.updatePersona(id: personaId, request)
        print(" Persona updated successfully")
    }

    /// Delete a persona
    func deletePersona(personaId: String) async throws {
        try await personaRepository.deletePersona(id: personaId)
        print(" Persona deleted successfully")
    }

    /// Fetch active persona
    func fetchActivePersona() async throws -> String? {
        guard let userId = currentUser?.id else {
            throw AuthError.notAuthenticated
        }

        return try await personaRepository.fetchActivePersona(userId: userId)
    }

    /// Set active persona
    func setActivePersona(personaId: String?) async throws {
        guard let userId = currentUser?.id else {
            throw AuthError.notAuthenticated
        }

        try await personaRepository.setActivePersona(userId: userId, personaId: personaId)
        print(" Active persona set successfully")
    }

    // MARK: - Multi-Persona Selection

    /// Fetch selected personas (up to 5)
    func fetchSelectedPersonas() async throws -> [Persona] {
        guard let userId = currentUser?.id else {
            throw AuthError.notAuthenticated
        }

        return try await personaRepository.fetchSelectedPersonas(userId: userId)
    }

    /// Add a selected persona
    func addSelectedPersona(personaId: String, order: Int) async throws {
        guard let userId = currentUser?.id else {
            throw AuthError.notAuthenticated
        }

        try await personaRepository.addSelectedPersona(userId: userId, personaId: personaId, order: order)
        print(" Persona selected successfully")
    }

    /// Remove a selected persona
    func removeSelectedPersona(personaId: String) async throws {
        guard let userId = currentUser?.id else {
            throw AuthError.notAuthenticated
        }

        try await personaRepository.removeSelectedPersona(userId: userId, personaId: personaId)
        print(" Persona unselected successfully")
    }

    /// Set selected personas (replaces all existing selections, max 5)
    func setSelectedPersonas(personaIds: [String]) async throws {
        guard let userId = currentUser?.id else {
            throw AuthError.notAuthenticated
        }

        try await personaRepository.setSelectedPersonas(userId: userId, personaIds: personaIds)
        print(" Selected personas updated successfully")
    }

    // MARK: - Persona Channel Management

    /// Get Sendbird channel URL for a persona
    /// - Parameter personaId: Persona ID
    /// - Returns: Sendbird channel URL if exists, nil otherwise
    func getPersonaChannelUrl(personaId: String) async throws -> String? {
        guard let accessToken = getAccessToken() else {
            throw AuthError.notAuthenticated
        }

        guard let userId = currentUser?.id else {
            throw AuthError.notAuthenticated
        }

        guard let url = URL(string: "\(supabaseURL)/rest/v1/persona_channels?user_id=eq.\(userId)&persona_id=eq.\(personaId)&select=channel_url") else {
            throw AuthError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue(supabaseAnonKey, forHTTPHeaderField: "apikey")
        request.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw AuthError.invalidResponse
        }

        if httpResponse.statusCode != 200 {
            if let responseString = String(data: data, encoding: .utf8) {
                print("  Fetch persona channel failed: \(responseString)")
            }
            throw AuthError.serverError("Failed to fetch persona channel")
        }

        struct ChannelResponse: Codable {
            let channelUrl: String

            enum CodingKeys: String, CodingKey {
                case channelUrl = "channel_url"
            }
        }

        let channels = try JSONDecoder().decode([ChannelResponse].self, from: data)
        return channels.first?.channelUrl
    }

    /// Save Sendbird channel URL for a persona
    /// - Parameters:
    ///   - personaId: Persona ID
    ///   - channelUrl: Sendbird channel URL
    func savePersonaChannelUrl(personaId: String, channelUrl: String) async throws {
        guard let accessToken = getAccessToken() else {
            throw AuthError.notAuthenticated
        }

        guard let userId = currentUser?.id else {
            throw AuthError.notAuthenticated
        }

        guard let url = URL(string: "\(supabaseURL)/rest/v1/persona_channels") else {
            throw AuthError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue(supabaseAnonKey, forHTTPHeaderField: "apikey")
        request.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("return=minimal", forHTTPHeaderField: "Prefer")
        // Use upsert to handle duplicate key conflicts
        request.setValue("resolution=merge-duplicates", forHTTPHeaderField: "Prefer")

        let body: [String: String] = [
            "user_id": userId,
            "persona_id": personaId,
            "channel_url": channelUrl
        ]

        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (responseData, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw AuthError.invalidResponse
        }

        // Handle success (201) or conflict (409)
        if httpResponse.statusCode == 201 {
            print(" Persona channel URL saved successfully")
            return
        }

        // If conflict (409), the row already exists - update it instead
        if httpResponse.statusCode == 409 {
            print("ℹ️ [SupabaseManager] Channel already exists (409), updating instead")
            try await updatePersonaChannelUrl(personaId: personaId, channelUrl: channelUrl)
            return
        }

        // Any other status code is an error
        if let responseString = String(data: responseData, encoding: .utf8) {
            print("  Save persona channel failed: \(responseString)")
        }
        throw AuthError.serverError("Failed to save persona channel (status \(httpResponse.statusCode))")
    }

    /// Update Sendbird channel URL for a persona
    /// - Parameters:
    ///   - personaId: Persona ID
    ///   - channelUrl: Sendbird channel URL
    private func updatePersonaChannelUrl(personaId: String, channelUrl: String) async throws {
        guard let accessToken = getAccessToken() else {
            throw AuthError.notAuthenticated
        }

        guard let userId = currentUser?.id else {
            throw AuthError.notAuthenticated
        }

        guard let url = URL(string: "\(supabaseURL)/rest/v1/persona_channels?user_id=eq.\(userId)&persona_id=eq.\(personaId)") else {
            throw AuthError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "PATCH"
        request.setValue(supabaseAnonKey, forHTTPHeaderField: "apikey")
        request.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: String] = [
            "channel_url": channelUrl
        ]

        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (responseData, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw AuthError.invalidResponse
        }

        if httpResponse.statusCode != 200 && httpResponse.statusCode != 204 {
            if let responseString = String(data: responseData, encoding: .utf8) {
                print("  Update persona channel failed: \(responseString)")
            }
            throw AuthError.serverError("Failed to update persona channel")
        }

        print(" Persona channel URL updated successfully")
    }

    /// Create user profile in database
    private func createUserProfile(userId: String, email: String, name: String, accessToken: String) async throws {
        // Create user profile
        guard let profileUrl = URL(string: "\(supabaseURL)/rest/v1/user_profiles") else {
            throw AuthError.invalidURL
        }

        var profileRequest = URLRequest(url: profileUrl)
        profileRequest.httpMethod = "POST"
        profileRequest.setValue(supabaseAnonKey, forHTTPHeaderField: "apikey")
        profileRequest.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")
        profileRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        profileRequest.setValue("return=minimal", forHTTPHeaderField: "Prefer")

        let profileBody: [String: String] = [
            "id": userId,
            "email": email,
            "name": name
        ]

        profileRequest.httpBody = try JSONSerialization.data(withJSONObject: profileBody)

        let (profileData, profileResponse) = try await URLSession.shared.data(for: profileRequest)

        guard let httpProfileResponse = profileResponse as? HTTPURLResponse else {
            throw AuthError.invalidResponse
        }

        if httpProfileResponse.statusCode != 201 {
            if let responseString = String(data: profileData, encoding: .utf8) {
                print("  Profile creation failed: \(responseString)")
            }
            print("⚠️ Warning: Could not create user profile")
        } else {
            print(" User profile created successfully")
        }

        // Create default user settings
        guard let settingsUrl = URL(string: "\(supabaseURL)/rest/v1/user_settings") else {
            return
        }

        var settingsRequest = URLRequest(url: settingsUrl)
        settingsRequest.httpMethod = "POST"
        settingsRequest.setValue(supabaseAnonKey, forHTTPHeaderField: "apikey")
        settingsRequest.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")
        settingsRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        settingsRequest.setValue("return=minimal", forHTTPHeaderField: "Prefer")

        let settingsBody: [String: Any] = [
            "user_id": userId,
            "notification_method": "push",
            "haru_notification_enabled": true,
            "font_size": "medium",
            "emergency_call_enabled": true,
            "call_summary_enabled": true
        ]

        settingsRequest.httpBody = try JSONSerialization.data(withJSONObject: settingsBody)

        let (settingsData, settingsResponse) = try await URLSession.shared.data(for: settingsRequest)

        guard let httpSettingsResponse = settingsResponse as? HTTPURLResponse else {
            return
        }

        if httpSettingsResponse.statusCode != 201 {
            if let responseString = String(data: settingsData, encoding: .utf8) {
                print("  Settings creation failed: \(responseString)")
            }
            print("⚠️ Warning: Could not create user settings")
        } else {
            print(" User settings created successfully")
        }
    }

    // MARK: - Session Management

    private func saveSession(_ session: Session) {
        UserDefaults.standard.set(session.accessToken, forKey: "access_token")
        UserDefaults.standard.set(session.refreshToken, forKey: "refresh_token")
        UserDefaults.standard.set(session.expiresIn, forKey: "expires_in")
        UserDefaults.standard.set(Date().timeIntervalSince1970, forKey: "token_created_at")
    }

    func getAccessToken() -> String? {
        return UserDefaults.standard.string(forKey: "access_token")
    }

    private func clearSession() {
        UserDefaults.standard.removeObject(forKey: "access_token")
        UserDefaults.standard.removeObject(forKey: "refresh_token")
        UserDefaults.standard.removeObject(forKey: "expires_in")
        UserDefaults.standard.removeObject(forKey: "token_created_at")
    }

    private func checkSession() {
        if let accessToken = getAccessToken(),
           !accessToken.isEmpty {
            // Set authenticated to true
            isAuthenticated = true

            // Try to fetch user info from token
            Task {
                await validateSessionAndFetchUser(accessToken: accessToken)
            }
        } else {
            isAuthenticated = false
        }
    }

    private func validateSessionAndFetchUser(accessToken: String) async {
        guard let url = URL(string: "\(supabaseURL)/auth/v1/user") else {
            return
        }

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue(supabaseAnonKey, forHTTPHeaderField: "apikey")
        request.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")

        do {
            let (data, response) = try await URLSession.shared.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse,
                  httpResponse.statusCode == 200 else {
                // Token is invalid, clear session
                await MainActor.run {
                    clearSession()
                    isAuthenticated = false
                }
                return
            }

            let userObj = try JSONDecoder().decode(SupabaseUser.self, from: data)

            let user = SupabaseUser(
                id: userObj.id,
                email: userObj.email,
                name: userObj.name
            )

            // Ensure user exists in FastAPI backend
            // Then connect to Sendbird with the FastAPI user ID
            Task {
                if let fastAPIUserId = await FastAPIService.shared.registerUser(email: userObj.email) {
                    UserDefaults.standard.set(fastAPIUserId, forKey: "fastapi_user_id")
                    print("✅ [FastAPI] User registered with ID: \(fastAPIUserId)")

                    // Connect to Sendbird Chat using FastAPI DB UUID (session restore)
                    do {
                        try await SendbirdManager.shared.connect(userId: fastAPIUserId)
                        print("✅ [Sendbird] Connected on session restore with FastAPI user ID: \(fastAPIUserId)")
                    } catch {
                        print("⚠️ [Sendbird] Failed to connect: \(error)")
                    }
                } else {
                    print("❌ [FastAPI] Failed to register user, cannot connect to Sendbird")
                }
            }

            await MainActor.run {
                currentUser = user
                isAuthenticated = true
            }

            // Send authentication status to Watch
            WatchConnectivityManager.shared.sendAuthenticationStatus(
                isAuthenticated: true,
                userId: user.id,
                userEmail: user.email
            )

            // Load tagged locations for proximity detection
            Task {
                await TaggedLocationManager.shared.loadTaggedLocations()
            }

            print(" Session validated, user: \(user.email)")
        } catch {
            print("  Session validation failed: \(error.localizedDescription)")
            // Keep authentication state but log the error
        }
    }
}

// MARK: - Models

struct SupabaseUser: Codable, Identifiable {
    let id: String
    let email: String
    let userMetadata: UserMetadata?

    // Computed property for name (from user_metadata or empty string)
    var name: String {
        return userMetadata?.name ?? ""
    }

    init(id: String, email: String, name: String, userMetadata: UserMetadata? = nil) {
        self.id = id
        self.email = email
        // If userMetadata is nil but name is provided, create UserMetadata
        if let metadata = userMetadata {
            self.userMetadata = metadata
        } else if !name.isEmpty {
            // Create a simple UserMetadata with just the name
            self.userMetadata = try? UserMetadata(name: name)
        } else {
            self.userMetadata = nil
        }
    }

    enum CodingKeys: String, CodingKey {
        case id
        case email
        case userMetadata = "user_metadata"
    }
}

struct UserProfile: Codable {
    let id: String
    let email: String
    let name: String?
    let birthday: String?
    let avatarUrl: String?

    enum CodingKeys: String, CodingKey {
        case id
        case email
        case name
        case birthday
        case avatarUrl = "avatar_url"
    }
}

struct UserSettings: Codable {
    let userId: String
    let notificationMethod: String?
    let doNotDisturbStart: String?
    let doNotDisturbEnd: String?
    let haruNotificationEnabled: Bool?
    let fontSize: String?
    let emergencyCallEnabled: Bool?
    let callSummaryEnabled: Bool?

    enum CodingKeys: String, CodingKey {
        case userId = "user_id"
        case notificationMethod = "notification_method"
        case doNotDisturbStart = "do_not_disturb_start"
        case doNotDisturbEnd = "do_not_disturb_end"
        case haruNotificationEnabled = "haru_notification_enabled"
        case fontSize = "font_size"
        case emergencyCallEnabled = "emergency_call_enabled"
        case callSummaryEnabled = "call_summary_enabled"
    }

    static func `default`(userId: String) -> UserSettings {
        return UserSettings(
            userId: userId,
            notificationMethod: "push",
            doNotDisturbStart: nil,
            doNotDisturbEnd: nil,
            haruNotificationEnabled: true,
            fontSize: "medium",
            emergencyCallEnabled: true,
            callSummaryEnabled: true
        )
    }
}

struct AuthResponse: Codable {
    let user: SupabaseUser?
    let session: Session?

    // For direct user response (when email confirmation is required)
    let id: String?
    let email: String?
    let userMetadata: UserMetadata?
    let confirmationSentAt: String?

    // For login response (session fields at top level)
    let accessToken: String?
    let refreshToken: String?
    let expiresIn: Int?
    let expiresAt: Int?

    enum CodingKeys: String, CodingKey {
        case user
        case session
        case id
        case email
        case userMetadata = "user_metadata"
        case confirmationSentAt = "confirmation_sent_at"
        case accessToken = "access_token"
        case refreshToken = "refresh_token"
        case expiresIn = "expires_in"
        case expiresAt = "expires_at"
    }

    // Helper to get session from either nested or top-level fields
    func getSession() -> Session? {
        if let session = session {
            return session
        } else if let accessToken = accessToken,
                  let refreshToken = refreshToken,
                  let expiresIn = expiresIn {
            return Session(accessToken: accessToken, refreshToken: refreshToken, expiresIn: expiresIn)
        }
        return nil
    }
}

struct UserMetadata: Codable {
    let name: String?

    // Simple initializer for creating UserMetadata with name
    init(name: String?) {
        self.name = name
    }

    // Custom decoder to handle any additional fields from API
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: DynamicCodingKeys.self)
        var nameValue: String?

        for key in container.allKeys {
            if key.stringValue == "name" {
                nameValue = try? container.decode(String.self, forKey: key)
            }
        }

        self.name = nameValue
    }

    struct DynamicCodingKeys: CodingKey {
        var stringValue: String
        var intValue: Int?

        init?(stringValue: String) {
            self.stringValue = stringValue
            self.intValue = nil
        }

        init?(intValue: Int) {
            self.stringValue = "\(intValue)"
            self.intValue = intValue
        }
    }
}

struct Session: Codable {
    let accessToken: String
    let refreshToken: String
    let expiresIn: Int

    enum CodingKeys: String, CodingKey {
        case accessToken = "access_token"
        case refreshToken = "refresh_token"
        case expiresIn = "expires_in"
    }
}

// MARK: - Errors

enum AuthError: LocalizedError {
    case invalidURL
    case invalidResponse
    case invalidCredentials
    case serverError(String)
    case notAuthenticated
    case emailConfirmationRequired(String)

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .invalidResponse:
            return "Invalid response from server"
        case .invalidCredentials:
            return "Invalid email or password"
        case .serverError(let message):
            return message
        case .notAuthenticated:
            return "Not authenticated"
        case .emailConfirmationRequired(let email):
            return "계정이 생성되었습니다! \(email)로 전송된 인증 이메일을 확인해주세요."
        }
    }
}
