//
//  FontSizeManager.swift
//  space
//
//  글자 크기 관리 매니저

import SwiftUI
import Combine

/// 앱 전체의 글자 크기를 관리하는 싱글톤 매니저
class FontSizeManager: ObservableObject {
    static let shared = FontSizeManager()

    private let userDefaults = UserDefaults.standard
    private let fontSizeKey = "app_font_size"

    /// 현재 글자 크기 (12pt ~ 24pt)
    @Published var fontSize: Double {
        didSet {
            userDefaults.set(fontSize, forKey: fontSizeKey)
        }
    }

    private init() {
        // UserDefaults에서 저장된 글자 크기 불러오기 (기본값: 16pt)
        let savedSize = userDefaults.double(forKey: fontSizeKey)
        self.fontSize = savedSize > 0 ? savedSize : 16.0
    }

    /// 글자 크기 리셋
    func reset() {
        fontSize = 16.0
    }
}
