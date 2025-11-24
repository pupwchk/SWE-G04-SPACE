//
//  CallHistoryManager.swift
//  space
//
//  Created by 임동현 on 11/24/25.
//

import Foundation

enum CallType: String, Codable {
    case text = "문자"
    case voice = "음성통화"
    case video = "영상통화"
}

struct CallRecord: Identifiable, Codable {
    let id: UUID
    let contactName: String
    let callType: CallType
    let timestamp: Date
    let duration: TimeInterval
    let summary: String

    init(id: UUID = UUID(), contactName: String, callType: CallType, timestamp: Date = Date(), duration: TimeInterval, summary: String) {
        self.id = id
        self.contactName = contactName
        self.callType = callType
        self.timestamp = timestamp
        self.duration = duration
        self.summary = summary
    }

    var formattedTimestamp: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy년 MM월 dd일 : HH:mm"
        formatter.locale = Locale(identifier: "ko_KR")
        return formatter.string(from: timestamp)
    }

    var formattedDuration: String {
        let minutes = Int(duration) / 60
        let seconds = Int(duration) % 60
        return String(format: "%d분 %02d초", minutes, seconds)
    }
}

class CallHistoryManager: ObservableObject {
    static let shared = CallHistoryManager()

    @Published var callRecords: [CallRecord] = []

    private let userDefaultsKey = "callHistoryRecords"

    private init() {
        loadCallRecords()
        if callRecords.isEmpty {
            loadDummyData()
        }
    }

    func addCallRecord(_ record: CallRecord) {
        callRecords.insert(record, at: 0)
        saveCallRecords()
    }

    func deleteCallRecord(_ record: CallRecord) {
        callRecords.removeAll { $0.id == record.id }
        saveCallRecords()
    }

    func clearAllRecords() {
        callRecords.removeAll()
        saveCallRecords()
    }

    private func saveCallRecords() {
        if let encoded = try? JSONEncoder().encode(callRecords) {
            UserDefaults.standard.set(encoded, forKey: userDefaultsKey)
        }
    }

    private func loadCallRecords() {
        if let data = UserDefaults.standard.data(forKey: userDefaultsKey),
           let decoded = try? JSONDecoder().decode([CallRecord].self, from: data) {
            callRecords = decoded
        }
    }

    private func loadDummyData() {
        let dummyRecords = [
            CallRecord(
                contactName: "My home",
                callType: .voice,
                timestamp: Date().addingTimeInterval(-86400),
                duration: 125,
                summary: "무슨 내용으로 전화를 했을까? 집에 할일이 생겼다거나 아떠구저떠구아떠구 저떠구\n무슨 내용으로 전화를 했을까? 집에 할일이 생겼다거나 아떠구저떠구아떠구 저떠구"
            ),
            CallRecord(
                contactName: "My home",
                callType: .voice,
                timestamp: Date().addingTimeInterval(-172800),
                duration: 234,
                summary: "집에 도착했어요. 오늘 저녁 뭐 먹을까요?"
            ),
            CallRecord(
                contactName: "My home",
                callType: .voice,
                timestamp: Date().addingTimeInterval(-259200),
                duration: 89,
                summary: "조금 늦을 것 같아요. 먼저 드세요!"
            ),
            CallRecord(
                contactName: "My home",
                callType: .voice,
                timestamp: Date().addingTimeInterval(-345600),
                duration: 156,
                summary: "장 봐올게요. 필요한 거 있으면 말해주세요."
            )
        ]

        callRecords = dummyRecords
        saveCallRecords()
    }
}
