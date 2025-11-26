//
//  TimelineWidget.swift
//  space
//
//  Created by 임동현 on 11/6/25.
//

import SwiftUI
import MapKit

/// Timeline tracking widget with GPS functionality
struct TimelineWidget: View {
    @StateObject private var locationManager = LocationManager.shared
    @StateObject private var timelineManager = TimelineManager.shared

    @State private var showDetailView = false

    var body: some View {
        Button(action: handleTap) {
            ZStack {
                Color(hex: "F3DEE5")

                if let latestTimeline = timelineManager.timelines.first {
                    // Show latest timeline as mini map
                    timelineMiniMapView(timeline: latestTimeline)
                } else if locationManager.isTracking {
                    // Show tracking in progress
                    trackingView
                } else {
                    // Show empty state
                    emptyStateView
                }
            }
            .frame(width: 160, height: 160)
            .cornerRadius(20)
        }
        .buttonStyle(.plain)
        .sheet(isPresented: $showDetailView) {
            TimelineDetailView(
                locationManager: locationManager,
                isTracking: $locationManager.isTracking,
                onStartTracking: startTracking,
                onStopTracking: stopTracking
            )
        }
    }

    // MARK: - Empty State View

    private var emptyStateView: some View {
        VStack(spacing: 8) {
            Image(systemName: "plus.circle.fill")
                .font(.system(size: 36))
                .foregroundColor(Color(hex: "A50034"))

            Text("타임라인 기록하기")
                .font(.system(size: 14, weight: .medium))
                .foregroundColor(.black)
        }
    }

    // MARK: - Tracking View

    private var trackingView: some View {
        VStack(spacing: 8) {
            // Mini map or tracking indicator
            if locationManager.routeCoordinates.count > 1 {
                Map(position: .constant(.region(currentRegion))) {
                    MapPolyline(coordinates: locationManager.routeCoordinates)
                        .stroke(Color(hex: "A50034"), lineWidth: 3)

                    if let lastCoord = locationManager.routeCoordinates.last {
                        Annotation("", coordinate: lastCoord) {
                            Circle()
                                .fill(Color(hex: "A50034"))
                                .frame(width: 12, height: 12)
                                .overlay(
                                    Circle()
                                        .stroke(Color.white, lineWidth: 2)
                                )
                        }
                    }
                }
                .frame(height: 100)
                .cornerRadius(12)
                .padding(8)
            } else {
                ProgressView()
                    .scaleEffect(1.5)
                    .padding(.top, 20)
            }

            // Tracking stats
            VStack(spacing: 4) {
                Text(String(format: "%.2f km/h", locationManager.currentSpeed))
                    .font(.system(size: 16, weight: .bold))
                    .foregroundColor(Color(hex: "A50034"))

                Text(String(format: "%.2f km", locationManager.totalDistance / 1000))
                    .font(.system(size: 12, weight: .regular))
                    .foregroundColor(.gray)
            }
            .padding(.bottom, 8)
        }
    }

    // MARK: - Timeline Mini Map View

    private func timelineMiniMapView(timeline: TimelineRecord) -> some View {
        VStack(spacing: 0) {
            // Mini map
            if let region = timeline.region {
                Map(position: .constant(.region(region))) {
                    MapPolyline(coordinates: timeline.coordinates.map { $0.coordinate })
                        .stroke(Color(hex: "A50034"), lineWidth: 3)

                    if let firstCoord = timeline.coordinates.first?.coordinate {
                        Annotation("", coordinate: firstCoord) {
                            Circle()
                                .fill(Color.green)
                                .frame(width: 10, height: 10)
                                .overlay(Circle().stroke(Color.white, lineWidth: 2))
                        }
                    }

                    if let lastCoord = timeline.coordinates.last?.coordinate {
                        Annotation("", coordinate: lastCoord) {
                            Circle()
                                .fill(Color(hex: "A50034"))
                                .frame(width: 10, height: 10)
                                .overlay(Circle().stroke(Color.white, lineWidth: 2))
                        }
                    }
                }
                .frame(height: 110)
                .allowsHitTesting(false)
            }

            // Stats overlay
            VStack(spacing: 2) {
                Text(timeline.distanceFormatted)
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundColor(.black)

                Text(timeline.durationFormatted)
                    .font(.system(size: 11, weight: .regular))
                    .foregroundColor(.gray)
            }
            .frame(maxWidth: .infinity)
            .padding(.vertical, 8)
            .background(Color(hex: "F3DEE5").opacity(0.95))
        }
    }

    // MARK: - Computed Properties

    private var currentRegion: MKCoordinateRegion {
        if let lastLocation = locationManager.location {
            return MKCoordinateRegion(
                center: lastLocation.coordinate,
                span: MKCoordinateSpan(latitudeDelta: 0.01, longitudeDelta: 0.01)
            )
        }
        return MKCoordinateRegion(
            center: CLLocationCoordinate2D(latitude: 37.5, longitude: 127.0),
            span: MKCoordinateSpan(latitudeDelta: 0.01, longitudeDelta: 0.01)
        )
    }

    // MARK: - Actions

    private func handleTap() {
        if locationManager.isTracking {
            // If tracking, show detail view
            showDetailView = true
        } else if timelineManager.timelines.isEmpty {
            // If no timelines, start tracking
            startTracking()
        } else {
            // If has timelines, show detail view
            showDetailView = true
        }
    }

    private func startTracking() {
        locationManager.startTracking()
    }

    private func stopTracking() {
        guard let startTime = locationManager.timelineStartTime else {
            print("⚠️ No timeline start time recorded")
            return
        }

        locationManager.stopTracking()

        // Generate checkpoints automatically
        let checkpoints = timelineManager.generateCheckpoints(
            coordinates: locationManager.routeCoordinates,
            timestamps: locationManager.timestampHistory,
            healthData: locationManager.healthDataHistory
        )

        // Create timeline record using LocationManager's history
        if let timeline = timelineManager.createTimeline(
            startTime: startTime,
            endTime: Date(),
            coordinates: locationManager.routeCoordinates,
            timestamps: locationManager.timestampHistory,
            speeds: locationManager.speedHistory,
            checkpoints: checkpoints
        ) {
            timelineManager.saveTimeline(timeline)
            print("✅ Timeline saved with \(checkpoints.count) checkpoint(s)")
        }

        locationManager.resetTracking()
    }
}

#Preview {
    TimelineWidget()
        .background(Color(hex: "F9F9F9"))
}
