//
//  AppDelegate.swift
//  space
//
//  Created for handling push notifications and device token registration
//

import UIKit
import UserNotifications
@preconcurrency import SendbirdChatSDK

class AppDelegate: NSObject, UIApplicationDelegate, UNUserNotificationCenterDelegate {

    func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil
    ) -> Bool {
        // Register for push notifications
        UNUserNotificationCenter.current().delegate = self

        let authOptions: UNAuthorizationOptions = [.alert, .badge, .sound]
        UNUserNotificationCenter.current().requestAuthorization(options: authOptions) { granted, error in
            if granted {
                print("✅ [AppDelegate] Push notification permission granted")
                DispatchQueue.main.async {
                    application.registerForRemoteNotifications()
                }
            } else if let error = error {
                print("❌ [AppDelegate] Push notification permission error: \(error)")
            } else {
                print("⚠️ [AppDelegate] Push notification permission denied")
            }
        }

        return true
    }

    // MARK: - Push Notification Registration

    func application(
        _ application: UIApplication,
        didRegisterForRemoteNotificationsWithDeviceToken deviceToken: Data
    ) {
        let tokenString = deviceToken.map { String(format: "%02.2hhx", $0) }.joined()
        print("📱 [AppDelegate] Device token registered: \(tokenString)")

        // Register device token with Sendbird
        SendbirdChat.registerDevicePushToken(deviceToken, unique: true) { status, error in
            if let error = error {
                print("❌ [AppDelegate] Failed to register push token with Sendbird: \(error)")
            } else {
                print("✅ [AppDelegate] Push token registered with Sendbird")
                print("   Status: \(status)")
            }
        }
    }

    func application(
        _ application: UIApplication,
        didFailToRegisterForRemoteNotificationsWithError error: Error
    ) {
        print("❌ [AppDelegate] Failed to register for remote notifications: \(error)")
    }

    // MARK: - Notification Handling

    // Called when app is in foreground
    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification,
        withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void
    ) {
        let userInfo = notification.request.content.userInfo
        print("📬 [AppDelegate] Received notification in foreground: \(userInfo)")

        // Show notification even when app is in foreground
        completionHandler([.banner, .sound, .badge])
    }

    // Called when user taps on notification
    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse,
        withCompletionHandler completionHandler: @escaping () -> Void
    ) {
        let userInfo = response.notification.request.content.userInfo
        print("👆 [AppDelegate] User tapped notification: \(userInfo)")

        // Check if it's a Sendbird notification
        if let sendbird = userInfo["sendbird"] as? [String: Any] {
            print("📨 [AppDelegate] Sendbird notification data: \(sendbird)")

            // Extract channel URL if available
            if let channelUrl = sendbird["channel"] as? [String: Any],
               let url = channelUrl["channel_url"] as? String {
                print("   Channel URL: \(url)")
                // TODO: Navigate to chat view with this channel URL
            }
        }

        completionHandler()
    }
}
