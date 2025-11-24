//
//  TimelineDetailView.swift
//  space
//
//  Full-screen timeline tracking and timeline map view
//

import SwiftUI
import MapKit

/// Full-screen timeline detail view with map and controls
struct TimelineDetailView: View {
    @Environment(\.dismiss) private var dismiss
    @ObservedObject var locationManager: LocationManager
    @Binding var isTracking: Bool

    var onStartTracking: () -> Void
    var onStopTracking: () -> Void

    @StateObject private var timelineManager = TimelineManager.shared
    @State private var selectedTimeline: TimelineRecord?
    @State private var cameraPosition: MapCameraPosition = .automatic
    @State private var selectedCheckpoint: Checkpoint?

    var body: some View {
        NavigationStack {
            ZStack {
                // Background color
                Color(hex: "F9F9F9")
                    .ignoresSafeArea()

                VStack(spacing: 0) {
                    // Map view
                    mapView
                        .frame(maxWidth: .infinity)
                        .frame(height: 400)
                        .cornerRadius(20)
                        .padding(.horizontal, 20)
                        .padding(.top, 20)

                    // Stats section
                    statsView
                        .padding(.horizontal, 20)
                        .padding(.top, 20)

                    Spacer()

                    // Control buttons
                    controlButtons
                        .padding(.horizontal, 20)
                        .padding(.bottom, 20)

                    // Timeline history
                    if !timelineManager.timelines.isEmpty {
                        timelineHistorySection
                    }
                }
            }
            .navigationTitle("My Timeline")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .navigationBarTrailing) {
                    Button("Close") {
                        dismiss()
                    }
                }
            }
        }
    }

    // MARK: - Map View

    private var mapView: some View {
        Map(position: $cameraPosition) {
            if let timeline = selectedTimeline {
                // Show selected timeline
                MapPolyline(coordinates: timeline.coordinates.map { $0.coordinate })
                    .stroke(Color(hex: "A50034"), lineWidth: 4)

                if let firstCoord = timeline.coordinates.first?.coordinate {
                    Annotation("Start", coordinate: firstCoord) {
                        ZStack {
                            Circle()
                                .fill(Color.green)
                                .frame(width: 20, height: 20)
                            Circle()
                                .stroke(Color.white, lineWidth: 3)
                                .frame(width: 20, height: 20)
                        }
                    }
                }

                if let lastCoord = timeline.coordinates.last?.coordinate {
                    Annotation("End", coordinate: lastCoord) {
                        ZStack {
                            Circle()
                                .fill(Color(hex: "A50034"))
                                .frame(width: 20, height: 20)
                            Circle()
                                .stroke(Color.white, lineWidth: 3)
                                .frame(width: 20, height: 20)
                        }
                    }
                }

                // Show checkpoints
                ForEach(timeline.checkpoints) { checkpoint in
                    Annotation("", coordinate: checkpoint.coordinate.coordinate) {
                        CheckpointAnnotationView(
                            checkpoint: checkpoint,
                            isSelected: selectedCheckpoint?.id == checkpoint.id,
                            onTap: {
                                withAnimation(.spring(response: 0.3)) {
                                    if selectedCheckpoint?.id == checkpoint.id {
                                        selectedCheckpoint = nil
                                    } else {
                                        selectedCheckpoint = checkpoint
                                    }
                                }
                            }
                        )
                    }
                }
            } else if isTracking && locationManager.routeCoordinates.count > 1 {
                // Show current tracking
                MapPolyline(coordinates: locationManager.routeCoordinates)
                    .stroke(Color(hex: "A50034"), lineWidth: 4)

                if let lastCoord = locationManager.routeCoordinates.last {
                    Annotation("", coordinate: lastCoord) {
                        ZStack {
                            Circle()
                                .fill(Color(hex: "A50034"))
                                .frame(width: 20, height: 20)
                            Circle()
                                .stroke(Color.white, lineWidth: 3)
                                .frame(width: 20, height: 20)

                            // Pulsing animation
                            Circle()
                                .fill(Color(hex: "A50034").opacity(0.3))
                                .frame(width: 30, height: 30)
                                .scaleEffect(1.5)
                                .animation(
                                    .easeInOut(duration: 1.5).repeatForever(autoreverses: true),
                                    value: isTracking
                                )
                        }
                    }
                }
            } else if let location = locationManager.location {
                // Show current location
                Annotation("", coordinate: location.coordinate) {
                    ZStack {
                        Circle()
                            .fill(Color.blue)
                            .frame(width: 20, height: 20)
                        Circle()
                            .stroke(Color.white, lineWidth: 3)
                            .frame(width: 20, height: 20)
                    }
                }
            }

            // User location
            UserAnnotation()
        }
        .mapStyle(.standard(elevation: .realistic))
        .mapControls {
            MapUserLocationButton()
            MapCompass()
            MapScaleView()
        }
        .onAppear {
            updateCameraPosition()
            // Load dummy data for testing
            timelineManager.loadDummyData()
        }
        .onChange(of: selectedTimeline) { _, newValue in
            // Clear checkpoint selection when timeline changes
            selectedCheckpoint = nil
        }
        .onChange(of: selectedTimeline) { _, _ in
            updateCameraPosition()
        }
        .onChange(of: locationManager.location) { _, _ in
            if isTracking && selectedTimeline == nil {
                updateCameraPosition()
            }
        }
    }

    // MARK: - Stats View

    private var statsView: some View {
        VStack(spacing: 16) {
            if let timeline = selectedTimeline {
                // Selected timeline stats
                HStack(spacing: 20) {
                    statItem(title: "Distance", value: timeline.distanceFormatted, icon: "figure.walk")
                    statItem(title: "Duration", value: timeline.durationFormatted, icon: "clock.fill")
                    statItem(title: "Avg Speed", value: String(format: "%.1f km/h", timeline.averageSpeed), icon: "speedometer")
                }
            } else if isTracking {
                // Current tracking stats
                HStack(spacing: 20) {
                    statItem(
                        title: "Distance",
                        value: String(format: "%.2f km", locationManager.totalDistance / 1000),
                        icon: "figure.walk"
                    )
                    statItem(
                        title: "Speed",
                        value: String(format: "%.1f km/h", locationManager.currentSpeed),
                        icon: "speedometer"
                    )
                    statItem(
                        title: "Altitude",
                        value: String(format: "%.0f m", locationManager.currentAltitude),
                        icon: "arrow.up.arrow.down"
                    )
                }

                // GPS accuracy info
                HStack(spacing: 8) {
                    Image(systemName: "location.fill")
                        .foregroundColor(Color(hex: "A50034"))
                        .font(.system(size: 12))

                    Text("H: ±\(String(format: "%.0f", locationManager.horizontalAccuracy))m | V: ±\(String(format: "%.0f", locationManager.verticalAccuracy))m")
                        .font(.system(size: 11))
                        .foregroundColor(.gray)
                }
                .padding(.top, 8)
            } else {
                // Not tracking
                Text("Start tracking to see your timeline")
                    .font(.system(size: 14))
                    .foregroundColor(.gray)
                    .padding(.vertical, 20)
            }
        }
        .padding(16)
        .background(Color.white)
        .cornerRadius(16)
    }

    private func statItem(title: String, value: String, icon: String) -> some View {
        VStack(spacing: 6) {
            Image(systemName: icon)
                .font(.system(size: 18))
                .foregroundColor(Color(hex: "A50034"))

            Text(value)
                .font(.system(size: 16, weight: .bold))
                .foregroundColor(.black)

            Text(title)
                .font(.system(size: 11))
                .foregroundColor(.gray)
        }
        .frame(maxWidth: .infinity)
    }

    // MARK: - Control Buttons

    private var controlButtons: some View {
        HStack(spacing: 12) {
            if selectedTimeline != nil {
                // Back to tracking
                Button(action: {
                    selectedTimeline = nil
                }) {
                    HStack {
                        Image(systemName: "arrow.left")
                        Text("Back")
                    }
                    .frame(maxWidth: .infinity)
                    .frame(height: 50)
                    .background(Color.gray.opacity(0.2))
                    .foregroundColor(.black)
                    .cornerRadius(12)
                }
            } else if isTracking {
                // Stop button
                Button(action: {
                    onStopTracking()
                }) {
                    HStack {
                        Image(systemName: "stop.fill")
                        Text("Stop")
                    }
                    .frame(maxWidth: .infinity)
                    .frame(height: 50)
                    .background(Color(hex: "A50034"))
                    .foregroundColor(.white)
                    .cornerRadius(12)
                }
            } else {
                // Start button
                Button(action: {
                    selectedTimeline = nil
                    onStartTracking()
                }) {
                    HStack {
                        Image(systemName: "play.fill")
                        Text("Start Tracking")
                    }
                    .frame(maxWidth: .infinity)
                    .frame(height: 50)
                    .background(Color(hex: "A50034"))
                    .foregroundColor(.white)
                    .cornerRadius(12)
                }
            }
        }
    }

    // MARK: - Timeline History Section

    private var timelineHistorySection: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("History")
                    .font(.system(size: 18, weight: .semibold))
                    .foregroundColor(.black)

                Spacer()

                if !timelineManager.timelines.isEmpty {
                    Button(action: {
                        timelineManager.clearAllTimelines()
                    }) {
                        Text("Clear All")
                            .font(.system(size: 13))
                            .foregroundColor(Color(hex: "A50034"))
                    }
                }
            }
            .padding(.horizontal, 20)

            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: 12) {
                    ForEach(timelineManager.timelines) { timeline in
                        timelineHistoryCard(timeline: timeline)
                    }
                }
                .padding(.horizontal, 20)
            }
        }
        .padding(.bottom, 20)
    }

    private func timelineHistoryCard(timeline: TimelineRecord) -> some View {
        Button(action: {
            selectedTimeline = timeline
        }) {
            VStack(alignment: .leading, spacing: 8) {
                // Mini map preview
                if let region = timeline.region {
                    Map(position: .constant(.region(region))) {
                        MapPolyline(coordinates: timeline.coordinates.map { $0.coordinate })
                            .stroke(Color(hex: "A50034"), lineWidth: 2)
                    }
                    .frame(width: 120, height: 80)
                    .cornerRadius(8)
                    .allowsHitTesting(false)
                }

                // Stats
                VStack(alignment: .leading, spacing: 4) {
                    Text(timeline.distanceFormatted)
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(.black)

                    Text(timeline.durationFormatted)
                        .font(.system(size: 11))
                        .foregroundColor(.gray)

                    Text(formatDate(timeline.startTime))
                        .font(.system(size: 10))
                        .foregroundColor(.gray)
                }
            }
            .padding(10)
            .background(selectedTimeline?.id == timeline.id ? Color(hex: "F3DEE5") : Color.white)
            .cornerRadius(12)
            .overlay(
                RoundedRectangle(cornerRadius: 12)
                    .stroke(selectedTimeline?.id == timeline.id ? Color(hex: "A50034") : Color.clear, lineWidth: 2)
            )
        }
        .buttonStyle(.plain)
        .contextMenu {
            Button(role: .destructive) {
                timelineManager.deleteTimeline(timeline)
                if selectedTimeline?.id == timeline.id {
                    selectedTimeline = nil
                }
            } label: {
                Label("Delete", systemImage: "trash")
            }
        }
    }

    // MARK: - Helper Methods

    private func updateCameraPosition() {
        if let timeline = selectedTimeline, let region = timeline.region {
            cameraPosition = .region(region)
        } else if isTracking, let lastLocation = locationManager.location {
            cameraPosition = .region(MKCoordinateRegion(
                center: lastLocation.coordinate,
                span: MKCoordinateSpan(latitudeDelta: 0.01, longitudeDelta: 0.01)
            ))
        } else if let location = locationManager.location {
            cameraPosition = .region(MKCoordinateRegion(
                center: location.coordinate,
                span: MKCoordinateSpan(latitudeDelta: 0.01, longitudeDelta: 0.01)
            ))
        }
    }

    private func formatDate(_ date: Date) -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "MMM d, HH:mm"
        return formatter.string(from: date)
    }
}

// MARK: - Checkpoint Annotation View

struct CheckpointAnnotationView: View {
    let checkpoint: Checkpoint
    let isSelected: Bool
    let onTap: () -> Void

    var body: some View {
        VStack(spacing: 0) {
            // Bubble popup when selected
            if isSelected {
                CheckpointBubbleView(checkpoint: checkpoint)
                    .transition(.scale.combined(with: .opacity))
            }

            // Emoji marker
            Button(action: onTap) {
                ZStack {
                    // Background circle
                    Circle()
                        .fill(Color(hex: checkpoint.mood.color).opacity(0.2))
                        .frame(width: 44, height: 44)

                    Circle()
                        .fill(Color.white)
                        .frame(width: 36, height: 36)
                        .shadow(color: .black.opacity(0.2), radius: 4, x: 0, y: 2)

                    Text(checkpoint.mood.emoji)
                        .font(.system(size: 20))
                }
            }
            .buttonStyle(.plain)
            .scaleEffect(isSelected ? 1.2 : 1.0)
            .animation(.spring(response: 0.3), value: isSelected)
        }
    }
}

// MARK: - Checkpoint Bubble View

struct CheckpointBubbleView: View {
    let checkpoint: Checkpoint

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            // Mood header
            HStack(spacing: 6) {
                Text(checkpoint.mood.emoji)
                    .font(.system(size: 16))
                Text(checkpoint.mood.label)
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(Color(hex: checkpoint.mood.color))
            }

            Divider()

            // Stay duration
            HStack(spacing: 6) {
                Image(systemName: "clock.fill")
                    .font(.system(size: 11))
                    .foregroundColor(.gray)
                Text("Stayed: \(checkpoint.stayDurationFormatted)")
                    .font(.system(size: 12))
                    .foregroundColor(.primary)
            }

            // Stress change
            HStack(spacing: 6) {
                Image(systemName: checkpoint.stressChange.icon)
                    .font(.system(size: 11))
                    .foregroundColor(Color(hex: checkpoint.stressChange.color))
                Text("Stress: \(checkpoint.stressChange.label)")
                    .font(.system(size: 12))
                    .foregroundColor(.primary)
            }

            // Note if exists
            if let note = checkpoint.note, !note.isEmpty {
                Divider()
                Text(note)
                    .font(.system(size: 11))
                    .foregroundColor(.gray)
                    .lineLimit(2)
            }
        }
        .padding(12)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(Color.white)
                .shadow(color: .black.opacity(0.15), radius: 8, x: 0, y: 4)
        )
        .frame(minWidth: 160)
        .offset(y: -8)
    }
}

#Preview {
    TimelineDetailView(
        locationManager: LocationManager(),
        isTracking: .constant(false),
        onStartTracking: {},
        onStopTracking: {}
    )
}
