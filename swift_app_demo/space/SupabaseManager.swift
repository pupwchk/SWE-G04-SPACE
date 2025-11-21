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

    @Published var currentUser: User?
    @Published var isAuthenticated = false

    private init() {
        // Check if user session exists
        checkSession()
    }

    // MARK: - Authentication Methods

    /// Sign up a new user with email and password
    func signUp(email: String, password: String, name: String) async throws -> User {
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
                print("❌ Error JSON: \(json)")
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

                let user = User(
                    id: userObj.id,
                    email: userObj.email,
                    name: name
                )

                // Create user profile in database
                try await createUserProfile(userId: userObj.id, email: userObj.email, name: name, accessToken: session.accessToken)

                await MainActor.run {
                    self.currentUser = user
                    self.isAuthenticated = true
                }

                return user
            } else if let userId = authResponse.id, let userEmail = authResponse.email {
                // Email confirmation required - no session yet
                print("✉️ Signup successful but email confirmation is required")
                print("✉️ User ID: \(userId), Email: \(userEmail)")

                // For development: just show success message without requiring confirmation
                let user = User(
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
            print("❌ JSON Decoding Error: \(error)")
            if let decodingError = error as? DecodingError {
                print("❌ Decoding Error Details: \(decodingError)")
            }
            throw AuthError.serverError("Failed to parse server response: \(error.localizedDescription)")
        }
    }

    /// Sign in with email and password
    func signIn(email: String, password: String) async throws -> User {
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
                print("❌ Error JSON: \(json)")
                if let message = json["error_description"] as? String ?? json["msg"] as? String ?? json["message"] as? String {
                    throw AuthError.serverError(message)
                }
            }
            throw AuthError.invalidCredentials
        }

        do {
            let authResponse = try JSONDecoder().decode(AuthResponse.self, from: data)

            print("✅ Auth response decoded successfully")

            // Try to get session from either nested or top-level fields
            guard let session = authResponse.getSession() else {
                print("❌ No session found in response")
                throw AuthError.serverError("Login failed - no session returned")
            }

            print("✅ Session retrieved: \(session.accessToken.prefix(20))...")

            // Get user object
            guard let userObj = authResponse.user else {
                print("❌ No user object in response")
                throw AuthError.serverError("Login failed - no user data")
            }

            print("✅ User object validated: \(userObj.email)")

            // Save session
            saveSession(session)

            let userName = userObj.userMetadata?.name ?? ""
            let user = User(
                id: userObj.id,
                email: userObj.email,
                name: userName
            )

            print("✅ About to set authenticated state")

            await MainActor.run {
                self.currentUser = user
                self.isAuthenticated = true
                print("✅ isAuthenticated set to true")
            }

            print("✅ Returning user: \(user.email)")
            return user
        } catch let error as AuthError {
            throw error
        } catch {
            print("❌ JSON Decoding Error: \(error)")
            if let decodingError = error as? DecodingError {
                print("❌ Decoding Error Details: \(decodingError)")
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
    }

    // MARK: - Database Operations

    /// Create user profile in database
    private func createUserProfile(userId: String, email: String, name: String, accessToken: String) async throws {
        guard let url = URL(string: "\(supabaseURL)/rest/v1/user_profiles") else {
            throw AuthError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue(supabaseAnonKey, forHTTPHeaderField: "apikey")
        request.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("return=minimal", forHTTPHeaderField: "Prefer")

        let body: [String: String] = [
            "id": userId,
            "email": email,
            "name": name
        ]

        request.httpBody = try JSONSerialization.data(withJSONObject: body)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw AuthError.invalidResponse
        }

        if httpResponse.statusCode != 201 {
            if let responseString = String(data: data, encoding: .utf8) {
                print("❌ Profile creation failed: \(responseString)")
            }
            // Don't throw error - profile creation is optional
            print("⚠️ Warning: Could not create user profile")
        } else {
            print("✅ User profile created successfully")
        }
    }

    // MARK: - Session Management

    private func saveSession(_ session: Session) {
        UserDefaults.standard.set(session.accessToken, forKey: "access_token")
        UserDefaults.standard.set(session.refreshToken, forKey: "refresh_token")
        UserDefaults.standard.set(session.expiresIn, forKey: "expires_in")
        UserDefaults.standard.set(Date().timeIntervalSince1970, forKey: "token_created_at")
    }

    private func getAccessToken() -> String? {
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
            // TODO: Validate token and fetch user profile
            isAuthenticated = true
        } else {
            isAuthenticated = false
        }
    }
}

// MARK: - Models

struct User: Codable, Identifiable {
    let id: String
    let email: String
    let name: String
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

struct SupabaseUser: Codable {
    let id: String
    let email: String
    let userMetadata: UserMetadata?

    enum CodingKeys: String, CodingKey {
        case id
        case email
        case userMetadata = "user_metadata"
    }
}

struct UserMetadata: Codable {
    let name: String?

    // Custom decoder to handle any additional fields
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
