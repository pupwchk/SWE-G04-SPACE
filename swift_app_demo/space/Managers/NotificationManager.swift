//
//  NotificationManager.swift
//  space
//
//  채팅 메시지 수신 시 로컬 알림을 관리하는 매니저
//

import Foundation
import UserNotifications
import UIKit

/// 로컬 알림 관리 매니저
class NotificationManager: NSObject, ObservableObject {
    static let shared = NotificationManager()

    // MARK: - Properties

    @Published var isAuthorized = false

    private let notificationCenter = UNUserNotificationCenter.current()

    // MARK: - Initialization

    private override init() {
        super.init()
        notificationCenter.delegate = self
        checkAuthorizationStatus()
    }

    // MARK: - Authorization

    /// 알림 권한 요청
    func requestAuthorization(completion: @escaping (Bool) -> Void = { _ in }) {
        notificationCenter.requestAuthorization(options: [.alert, .sound, .badge]) { [weak self] granted, error in
            DispatchQueue.main.async {
                self?.isAuthorized = granted

                if let error = error {
                    print("❌ [NotificationManager] Authorization failed: \(error)")
                    completion(false)
                } else {
                    print(granted ? "✅ [NotificationManager] Authorization granted" : "⚠️ [NotificationManager] Authorization denied")
                    completion(granted)
                }
            }
        }
    }

    /// 현재 알림 권한 상태 확인
    func checkAuthorizationStatus() {
        notificationCenter.getNotificationSettings { [weak self] settings in
            DispatchQueue.main.async {
                self?.isAuthorized = settings.authorizationStatus == .authorized
                print("ℹ️ [NotificationManager] Current authorization status: \(settings.authorizationStatus.rawValue)")
            }
        }
    }

    // MARK: - Notification Sending

    /// 채팅 메시지 수신 알림 전송
    /// - Parameters:
    ///   - personaName: 메시지를 보낸 페르소나 이름
    ///   - messageText: 메시지 내용
    ///   - channelUrl: 채널 URL (탭 시 해당 채팅방으로 이동하기 위한 데이터)
    func sendChatMessageNotification(personaName: String, messageText: String, channelUrl: String) {
        print("📲 [NotificationManager] sendChatMessageNotification called")
        print("   Persona: \(personaName)")
        print("   Message: \(messageText)")
        print("   Channel: \(channelUrl)")
        print("   Is authorized: \(isAuthorized)")

        // 권한이 없으면 알림을 보내지 않음
        guard isAuthorized else {
            print("⚠️ [NotificationManager] Notification not authorized")
            return
        }

        let content = UNMutableNotificationContent()
        content.title = personaName
        content.body = messageText
        content.sound = .default

        // iOS 17+ uses UNUserNotificationCenter for badge count
        if #available(iOS 17.0, *) {
            content.badge = 1
        } else {
            content.badge = NSNumber(value: UIApplication.shared.applicationIconBadgeNumber + 1)
        }

        // 채널 URL을 userInfo에 저장 (나중에 알림 탭 시 사용 가능)
        content.userInfo = [
            "type": "chat_message",
            "channelUrl": channelUrl,
            "personaName": personaName
        ]

        // 즉시 알림 전송
        let trigger = UNTimeIntervalNotificationTrigger(timeInterval: 0.1, repeats: false)

        // 고유 ID 생성 (채널별로 알림이 쌓이도록)
        let identifier = "chat_\(channelUrl)_\(Date().timeIntervalSince1970)"

        let request = UNNotificationRequest(identifier: identifier, content: content, trigger: trigger)

        print("📤 [NotificationManager] Adding notification request...")
        notificationCenter.add(request) { error in
            if let error = error {
                print("❌ [NotificationManager] Failed to send notification: \(error)")
            } else {
                print("✅ [NotificationManager] Notification sent for \(personaName)")
            }
        }
    }

    /// 배지 카운트 초기화
    func clearBadgeCount() {
        if #available(iOS 17.0, *) {
            notificationCenter.setBadgeCount(0) { error in
                if let error = error {
                    print("❌ [NotificationManager] Failed to clear badge count: \(error)")
                } else {
                    print("✅ [NotificationManager] Badge count cleared")
                }
            }
        } else {
            DispatchQueue.main.async {
                UIApplication.shared.applicationIconBadgeNumber = 0
                print("✅ [NotificationManager] Badge count cleared")
            }
        }
    }

    /// 모든 전달된 알림 제거
    func removeAllDeliveredNotifications() {
        notificationCenter.removeAllDeliveredNotifications()
        clearBadgeCount()
        print("✅ [NotificationManager] All delivered notifications removed")
    }

    /// 특정 채널의 알림만 제거
    /// - Parameter channelUrl: 제거할 채널 URL
    func removeNotifications(for channelUrl: String) {
        notificationCenter.getDeliveredNotifications { notifications in
            let identifiersToRemove = notifications
                .filter { notification in
                    if let url = notification.request.content.userInfo["channelUrl"] as? String {
                        return url == channelUrl
                    }
                    return false
                }
                .map { $0.request.identifier }

            self.notificationCenter.removeDeliveredNotifications(withIdentifiers: identifiersToRemove)
            print("✅ [NotificationManager] Removed \(identifiersToRemove.count) notifications for channel: \(channelUrl)")
        }
    }
}

// MARK: - UNUserNotificationCenterDelegate

extension NotificationManager: UNUserNotificationCenterDelegate {
    /// 앱이 포그라운드에 있을 때 알림을 표시할지 결정
    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification,
        withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void
    ) {
        print("📱 [NotificationManager] willPresent notification called")
        print("   Notification: \(notification.request.content.title) - \(notification.request.content.body)")

        // iOS 14+: 배너, 사운드, 배지, 알림 센터 리스트 모두 표시
        if #available(iOS 14.0, *) {
            completionHandler([.banner, .sound, .badge, .list])
        } else {
            completionHandler([.alert, .sound, .badge])
        }
    }

    /// 사용자가 알림을 탭했을 때 처리
    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse,
        withCompletionHandler completionHandler: @escaping () -> Void
    ) {
        let userInfo = response.notification.request.content.userInfo

        if let type = userInfo["type"] as? String, type == "chat_message" {
            if let channelUrl = userInfo["channelUrl"] as? String {
                print("📱 [NotificationManager] User tapped notification for channel: \(channelUrl)")

                // TODO: 채팅방으로 네비게이션 처리
                // NotificationCenter를 통해 앱의 다른 부분에 알림
                NotificationCenter.default.post(
                    name: NSNotification.Name("OpenChatChannel"),
                    object: nil,
                    userInfo: ["channelUrl": channelUrl]
                )
            }
        }

        completionHandler()
    }
}
