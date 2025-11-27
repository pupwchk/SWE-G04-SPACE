//
//  MapView.swift
//  space Watch App
//
//  Map view for Apple Watch with GPS tracking
//

import SwiftUI
import MapKit

/// Map view for Apple Watch showing current location and route
struct WatchMapView: View {
    @StateObject private var locationManager = WatchLocationManager.shared
    @StateObject private var healthManager = WatchHealthKitManager.shared
    @StateObject private var connectivityManager = WatchConnectivityManager.shared

    @State private var region = MKCoordinateRegion(
        center: CLLocationCoordinate2D(latitude: 37.5665, longitude: 126.9780), // Seoul
        span: MKCoordinateSpan(latitudeDelta: 0.01, longitudeDelta: 0.01)
    )

    @State private var showingStats = false

    var body: some View {
        ZStack {
            // Map
            Map(coordinateRegion: $region, showsUserLocation: true, annotationItems: routeAnnotations) { annotation in
                MapMarker(coordinate: annotation.coordinate, tint: .red)
            }
            .edgesIgnoringSafeArea(.all)
            .onAppear {
                updateRegion()
            }
            .onChange(of: locationManager.location) { _ in
                updateRegion()
            }

            // Overlay UI
            VStack {
                Spacer()

                // Stats card
                if locationManager.isTracking {
                    VStack(spacing: 8) {
                        // GPS Stats
                        HStack(spacing: 12) {
                            // Distance
                            VStack(alignment: .leading, spacing: 2) {
                                Text(distanceText)
                                    .font(.system(size: 18, weight: .bold))
                                    .foregroundColor(.white)
                                Text("거리")
                                    .font(.system(size: 9))
                                    .foregroundColor(.white.opacity(0.8))
                            }

                            Divider()
                                .background(Color.white.opacity(0.3))
                                .frame(height: 30)

                            // Speed
                            VStack(alignment: .leading, spacing: 2) {
                                Text(speedText)
                                    .font(.system(size: 18, weight: .bold))
                                    .foregroundColor(.white)
                                Text("속도")
                                    .font(.system(size: 9))
                                    .foregroundColor(.white.opacity(0.8))
                            }
                        }

                        // Health Stats
                        HStack(spacing: 12) {
                            // Heart Rate
                            VStack(alignment: .leading, spacing: 2) {
                                HStack(spacing: 4) {
                                    Text("\(Int(healthManager.currentHeartRate))")
                                        .font(.system(size: 16, weight: .bold))
                                        .foregroundColor(.red)
                                    Text("bpm")
                                        .font(.system(size: 9))
                                        .foregroundColor(.white.opacity(0.8))
                                }
                                Text("심박수")
                                    .font(.system(size: 9))
                                    .foregroundColor(.white.opacity(0.8))
                            }

                            Divider()
                                .background(Color.white.opacity(0.3))
                                .frame(height: 30)

                            // Calories
                            VStack(alignment: .leading, spacing: 2) {
                                HStack(spacing: 4) {
                                    Text("\(Int(healthManager.totalCalories))")
                                        .font(.system(size: 16, weight: .bold))
                                        .foregroundColor(.orange)
                                    Text("kcal")
                                        .font(.system(size: 9))
                                        .foregroundColor(.white.opacity(0.8))
                                }
                                Text("칼로리")
                                    .font(.system(size: 9))
                                    .foregroundColor(.white.opacity(0.8))
                            }
                        }
                    }
                    .padding(12)
                    .background(Color.black.opacity(0.7))
                    .cornerRadius(12)
                    .padding(.bottom, 8)
                }

                // Control buttons
                HStack(spacing: 16) {
                    if locationManager.isTracking {
                        Button(action: {
                            locationManager.stopTracking()
                            healthManager.stopWorkout()
                        }) {
                            Image(systemName: "stop.fill")
                                .font(.system(size: 20))
                                .foregroundColor(.white)
                                .frame(width: 50, height: 50)
                                .background(Color.red)
                                .clipShape(Circle())
                        }
                        .buttonStyle(.plain)
                    } else {
                        Button(action: {
                            startTracking()
                        }) {
                            Image(systemName: "play.fill")
                                .font(.system(size: 20))
                                .foregroundColor(.white)
                                .frame(width: 50, height: 50)
                                .background(Color.green)
                                .clipShape(Circle())
                        }
                        .buttonStyle(.plain)
                    }

                    // Location center button
                    Button(action: {
                        updateRegion()
                    }) {
                        Image(systemName: "location.fill")
                            .font(.system(size: 16))
                            .foregroundColor(.white)
                            .frame(width: 40, height: 40)
                            .background(Color.blue)
                            .clipShape(Circle())
                    }
                    .buttonStyle(.plain)
                }
                .padding(.bottom, 12)
            }

            // Connection status indicator
            VStack {
                HStack {
                    Spacer()
                    Image(systemName: connectivityManager.isPhoneReachable ? "iphone.and.arrow.forward" : "iphone.slash")
                        .font(.system(size: 14))
                        .foregroundColor(connectivityManager.isPhoneReachable ? .green : .gray)
                        .padding(8)
                        .background(Color.black.opacity(0.6))
                        .clipShape(Circle())
                        .padding(.trailing, 8)
                        .padding(.top, 8)
                }
                Spacer()
            }
        }
        .navigationTitle("지도")
        .navigationBarTitleDisplayMode(.inline)
    }

    // MARK: - Computed Properties

    private var distanceText: String {
        let km = locationManager.totalDistance / 1000.0
        if km >= 1.0 {
            return String(format: "%.2f km", km)
        } else {
            return String(format: "%.0f m", locationManager.totalDistance)
        }
    }

    private var speedText: String {
        return String(format: "%.1f", locationManager.currentSpeed) + " km/h"
    }

    private var routeAnnotations: [RoutePoint] {
        locationManager.coordinates.enumerated().map { index, coordinate in
            RoutePoint(id: index, coordinate: coordinate)
        }
    }

    // MARK: - Methods

    private func updateRegion() {
        if let location = locationManager.location {
            withAnimation {
                region.center = location.coordinate
            }
        }
    }

    private func startTracking() {
        // Request location authorization if needed
        if locationManager.authorizationStatus == .notDetermined {
            locationManager.requestAuthorization()
        }

        // Request HealthKit authorization if needed
        if healthManager.authorizationStatus == .notDetermined {
            healthManager.requestAuthorization()
        }

        // Start GPS tracking
        locationManager.startTracking()

        // Start HealthKit workout session
        healthManager.startWorkout()
    }
}

// MARK: - Route Point Model

struct RoutePoint: Identifiable {
    let id: Int
    let coordinate: CLLocationCoordinate2D
}

// MARK: - Preview

#Preview {
    WatchMapView()
}
