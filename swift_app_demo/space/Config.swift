//
//  Config.swift
//  space
//
//  Configuration and environment variables
//

import Foundation

/// Application configuration
struct Config {
    // MARK: - Sendbird Configuration

    /// Sendbird Application ID
    /// From .env: SENDBIRD_APP_ID
    static let sendbirdAppId = "89419626-76B6-4551-AB9B-D7FF2B41A68D"

    /// Sendbird API Token (if needed for server-side operations)
    /// From .env: SENDBIRD_API_TOKEN
    static let sendbirdApiToken = "16af94d4dcd84dda9f92d864"

    /// AI Assistant User ID in Sendbird
    static let aiUserId = "home_ai_assistant"

    // MARK: - Backend Configuration

    /// FastAPI Backend Base URL
    static let backendBaseURL = "http://13.125.85.158:11325"

    // MARK: - Supabase Configuration

    /// Supabase Project URL
    /// From .env: SUPABASE_URL
    static let supabaseURL = "https://aghsjspkzivcpibwwzvu.supabase.co"

    /// Supabase Anonymous Key
    /// From .env: SUPABASE_ANON_KEY
    static let supabaseAnonKey = "sb_publishable_Sls_xhBveIh5Z8Qv-1E1Qw_ExCImTBQ"

    // MARK: - Feature Flags

    /// Enable/disable Sendbird Chat features
    static let sendbirdChatEnabled = true

    /// Enable/disable Sendbird Calls features
    static let sendbirdCallsEnabled = true

    /// Enable/disable GPS-based auto-call
    static let autoCallEnabled = true

    /// Enable debug logging
    static let debugLoggingEnabled = true
}
