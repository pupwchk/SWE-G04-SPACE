//
//  SupabaseService.swift
//  space
//
//  MCP-style Supabase Service Layer
//  Provides a clean interface for Supabase operations

import Foundation

/// Supabase Service Protocol - MCP-style interface
protocol SupabaseServiceProtocol {
    func query<T: Decodable>(table: String, select: String, filter: String?) async throws -> [T]
    func insert<T: Encodable>(table: String, data: T) async throws -> Data
    func update<T: Encodable>(table: String, filter: String, data: T) async throws
    func delete(table: String, filter: String) async throws
}

/// Supabase Service Implementation
class SupabaseService: SupabaseServiceProtocol {
    private let baseURL: String
    private let apiKey: String
    private let tokenProvider: () -> String?

    init(baseURL: String, apiKey: String, tokenProvider: @escaping () -> String?) {
        self.baseURL = baseURL
        self.apiKey = apiKey
        self.tokenProvider = tokenProvider
    }

    // MARK: - Generic CRUD Operations

    /// Generic SELECT query
    func query<T: Decodable>(
        table: String,
        select: String = "*",
        filter: String? = nil
    ) async throws -> [T] {
        var urlString = "\(baseURL)/rest/v1/\(table)?select=\(select)"
        if let filter = filter {
            urlString += "&\(filter)"
        }

        guard let url = URL(string: urlString) else {
            throw SupabaseError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "GET"
        request.setValue(apiKey, forHTTPHeaderField: "apikey")

        if let token = tokenProvider() {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw SupabaseError.invalidResponse
        }

        guard httpResponse.statusCode == 200 else {
            if let errorString = String(data: data, encoding: .utf8) {
                print("  Query failed: \(errorString)")
            }
            throw SupabaseError.queryFailed(statusCode: httpResponse.statusCode)
        }

        // Debug: Print raw response
        if let jsonString = String(data: data, encoding: .utf8) {
            print(" Raw API Response: \(jsonString.prefix(200))...")
        }

        let decoder = JSONDecoder()
        // Note: Not using convertFromSnakeCase because models have explicit CodingKeys
        return try decoder.decode([T].self, from: data)
    }

    /// Generic INSERT operation
    func insert<T: Encodable>(
        table: String,
        data: T
    ) async throws -> Data {
        guard let url = URL(string: "\(baseURL)/rest/v1/\(table)") else {
            throw SupabaseError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue(apiKey, forHTTPHeaderField: "apikey")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("return=representation", forHTTPHeaderField: "Prefer")

        if let token = tokenProvider() {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        let encoder = JSONEncoder()
        // Note: Not using convertToSnakeCase because models have explicit CodingKeys
        request.httpBody = try encoder.encode(data)

        let (responseData, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw SupabaseError.invalidResponse
        }

        guard httpResponse.statusCode == 201 else {
            if let errorString = String(data: responseData, encoding: .utf8) {
                print("  Insert failed: \(errorString)")
            }
            throw SupabaseError.insertFailed(statusCode: httpResponse.statusCode)
        }

        return responseData
    }

    /// Generic UPDATE operation
    func update<T: Encodable>(
        table: String,
        filter: String,
        data: T
    ) async throws {
        guard let url = URL(string: "\(baseURL)/rest/v1/\(table)?\(filter)") else {
            throw SupabaseError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "PATCH"
        request.setValue(apiKey, forHTTPHeaderField: "apikey")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if let token = tokenProvider() {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        let encoder = JSONEncoder()
        // Note: Not using convertToSnakeCase because models have explicit CodingKeys
        request.httpBody = try encoder.encode(data)

        let (responseData, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw SupabaseError.invalidResponse
        }

        guard httpResponse.statusCode == 200 || httpResponse.statusCode == 204 else {
            if let errorString = String(data: responseData, encoding: .utf8) {
                print("  Update failed: \(errorString)")
            }
            throw SupabaseError.updateFailed(statusCode: httpResponse.statusCode)
        }
    }

    /// Generic DELETE operation
    func delete(
        table: String,
        filter: String
    ) async throws {
        guard let url = URL(string: "\(baseURL)/rest/v1/\(table)?\(filter)") else {
            throw SupabaseError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "DELETE"
        request.setValue(apiKey, forHTTPHeaderField: "apikey")

        if let token = tokenProvider() {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        let (responseData, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw SupabaseError.invalidResponse
        }

        guard httpResponse.statusCode == 200 || httpResponse.statusCode == 204 else {
            if let errorString = String(data: responseData, encoding: .utf8) {
                print("  Delete failed: \(errorString)")
            }
            throw SupabaseError.deleteFailed(statusCode: httpResponse.statusCode)
        }
    }

    /// RPC (Remote Procedure Call) support
    func rpc<T: Decodable>(
        function: String,
        params: [String: Any]
    ) async throws -> T {
        guard let url = URL(string: "\(baseURL)/rest/v1/rpc/\(function)") else {
            throw SupabaseError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue(apiKey, forHTTPHeaderField: "apikey")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        if let token = tokenProvider() {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }

        request.httpBody = try JSONSerialization.data(withJSONObject: params)

        let (data, response) = try await URLSession.shared.data(for: request)

        guard let httpResponse = response as? HTTPURLResponse else {
            throw SupabaseError.invalidResponse
        }

        guard httpResponse.statusCode == 200 else {
            if let errorString = String(data: data, encoding: .utf8) {
                print("  RPC failed: \(errorString)")
            }
            throw SupabaseError.rpcFailed(statusCode: httpResponse.statusCode)
        }

        return try JSONDecoder().decode(T.self, from: data)
    }
}

// MARK: - Errors

enum SupabaseError: LocalizedError {
    case invalidURL
    case invalidResponse
    case queryFailed(statusCode: Int)
    case insertFailed(statusCode: Int)
    case updateFailed(statusCode: Int)
    case deleteFailed(statusCode: Int)
    case rpcFailed(statusCode: Int)
    case decodingError(Error)

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid URL"
        case .invalidResponse:
            return "Invalid response from server"
        case .queryFailed(let code):
            return "Query failed with status code \(code)"
        case .insertFailed(let code):
            return "Insert failed with status code \(code)"
        case .updateFailed(let code):
            return "Update failed with status code \(code)"
        case .deleteFailed(let code):
            return "Delete failed with status code \(code)"
        case .rpcFailed(let code):
            return "RPC failed with status code \(code)"
        case .decodingError(let error):
            return "Decoding error: \(error.localizedDescription)"
        }
    }
}
