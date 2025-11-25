//
//  DeviceManager.swift
//  space
//
//  Manager for connected smart devices (Apple Watch, AirPods, etc.)
//

import Foundation
import WatchConnectivity
import Combine

/// Type of connected device
enum DeviceType: String, Codable {
    case watch = "Apple Watch"
    case airpods = "AirPods"
    case iphone = "iPhone"

    var icon: String {
        switch self {
        case .watch:
            return "applewatch"
        case .airpods:
            return "airpodspro"
        case .iphone:
            return "iphone"
        }
    }
}

/// Connected device model
struct ConnectedDevice: Identifiable {
    let id = UUID()
    let type: DeviceType
    let name: String
    let model: String?
    let batteryLevel: Int? // 0-100
    let isConnected: Bool
    let lastSeen: Date

    var batteryLevelFormatted: String {
        if let level = batteryLevel {
            return "\(level)%"
        } else {
            return "N/A"
        }
    }

    var batteryColor: String {
        guard let level = batteryLevel else { return "9E9E9E" } // Gray

        if level > 50 {
            return "4CAF50" // Green
        } else if level > 20 {
            return "FFC107" // Amber
        } else {
            return "F44336" // Red
        }
    }
}

/// Manager for tracking connected devices
class DeviceManager: ObservableObject {
    static let shared = DeviceManager()

    @Published var connectedDevices: [ConnectedDevice] = []

    private init() {
        updateDeviceList()
    }

    // MARK: - Update Device List

    func updateDeviceList() {
        var devices: [ConnectedDevice] = []

        // Add Apple Watch if paired
        if let watchDevice = getWatchDevice() {
            devices.append(watchDevice)
        }

        // Add AirPods if connected (placeholder - requires audio framework)
        // AirPods detection would require AVAudioSession and Bluetooth monitoring
        // For now, we'll just show Watch

        DispatchQueue.main.async {
            self.connectedDevices = devices
        }
    }

    // MARK: - Apple Watch Detection

    private func getWatchDevice() -> ConnectedDevice? {
        let connectivity = WatchConnectivityManager.shared

        guard WCSession.isSupported(),
              let session = WCSession.default as WCSession?,
              session.isPaired else {
            return nil
        }

        let isConnected = session.isReachable
        let isAppInstalled = session.isWatchAppInstalled

        // We can't directly get battery level from WatchConnectivity
        // The Watch would need to send it via messages
        // For now, we'll show nil for battery

        let watchName = "Apple Watch" // Session doesn't provide device name

        return ConnectedDevice(
            type: .watch,
            name: watchName,
            model: nil, // Session doesn't provide model info
            batteryLevel: nil, // Would need to be sent from Watch app
            isConnected: isConnected && isAppInstalled,
            lastSeen: Date()
        )
    }

    // MARK: - Receive Battery Update from Watch

    /// Called when Watch sends battery level update
    func updateWatchBattery(_ level: Int) {
        if let index = connectedDevices.firstIndex(where: { $0.type == .watch }) {
            let existingDevice = connectedDevices[index]

            let updatedDevice = ConnectedDevice(
                type: existingDevice.type,
                name: existingDevice.name,
                model: existingDevice.model,
                batteryLevel: level,
                isConnected: existingDevice.isConnected,
                lastSeen: Date()
            )

            connectedDevices[index] = updatedDevice
            print("🔋 Watch battery updated: \(level)%")
        }
    }

    // MARK: - Refresh

    func refresh() {
        updateDeviceList()
    }
}
