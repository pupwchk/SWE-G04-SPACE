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
        // 권한이 없으면 알림을 보내지 않음
        guard isAuthorized else {
            print("⚠️ [NotificationManager] Notification not authorized")
            return
        }

        // 앱이 활성화 상태일 때는 알림을 보내지 않음 (이미 화면에 표시되므로)
        if UIApplication.shared.applicationState == .active {
            print("ℹ️ [NotificationManager] App is active, skipping notification")
            return
        }

        let content = UNMutableNotificationContent()
        content.title = personaName
        content.body = messageText
        content.sound = .default
        content.badge = NSNumber(value: UIApplication.shared.applicationIconBadgeNumber + 1)

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
        DispatchQueue.main.async {
            UIApplication.shared.applicationIconBadgeNumber = 0
            print("✅ [NotificationManager] Badge count cleared")
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
        // 앱이 활성화 상태일 때도 배너와 사운드 표시 (선택사항)
        // 원하지 않으면 빈 배열 [] 반환
        completionHandler([.banner, .sound, .badge])
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
