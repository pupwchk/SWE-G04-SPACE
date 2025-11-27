//
//  PersonalTestView.swift
//  space
//
//  Created by 임동현 on 11/6/25.
//

import SwiftUI

/// Personal test questionnaire view with burgundy gradient background
struct PersonalTestView: View {
    @Environment(\.dismiss) var dismiss
    @Binding var selectedPersonas: Set<String>

    @State private var q1Answer: Int? = nil // 명황/성격 파악
    @State private var q2Answer: Int? = nil // 혼자 vs 함께
    @State private var q3Answer: Int? = nil // 계획 변경
    @State private var q4Answer: Int? = nil // 아침형 vs 밤형
    @State private var q5Answer: Int? = nil // 수면 시간
    @State private var q6Answer: Int? = nil // 루틴
    @State private var q7Answer: Int? = nil // 디지털 기기
    @State private var q8Answer: Int? = nil // 취미/관심사

    @State private var selectedBottomTab = 1 // 0: 답안 재조, 1: 다른 문제 생성, 2: 추가 문제

    var isAllQuestionsAnswered: Bool {
        q1Answer != nil && q2Answer != nil && q3Answer != nil &&
        q4Answer != nil && q5Answer != nil && q6Answer != nil &&
        q7Answer != nil && q8Answer != nil
    }

    var body: some View {
        ZStack {
            // Burgundy gradient background
            LinearGradient(
                gradient: Gradient(colors: [
                    Color(hex: "8B1538"),
                    Color(hex: "A50034")
                ]),
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()

            ScrollView(showsIndicators: false) {
                VStack(alignment: .leading, spacing: 24) {
                    // Title
                    Text("성향 테스트")
                        .font(.system(size: 40, weight: .bold))
                        .foregroundColor(.white)
                        .padding(.top, 20)
                        .padding(.horizontal, 20)

                    // Question 1: 명황/성격 파악
                    QuestionSection(
                        icon: "sun.max.fill",
                        title: "명황 / 성격 파악",
                        question: "하루 중 가장 에너지가 높을 때는 언제인가요?",
                        options: ["아침", "점심", "저녁"],
                        selectedIndex: $q1Answer
                    )

                    // Question 2: 혼자 vs 함께
                    QuestionSection(
                        icon: "person.2.fill",
                        title: nil,
                        question: "혼자 있을 때와 사람들과 함께 있을 때, 어떤 상황이 더 편한가요?",
                        options: ["혼자", "함께", "상황마다 다름"],
                        selectedIndex: $q2Answer
                    )

                    // Question 3: 계획 변경
                    QuestionSection(
                        icon: "calendar",
                        title: nil,
                        question: "계획이 바뀌면 기분이 어떤가요?",
                        options: ["상관없음", "조금 스트레스", "매우 불편함"],
                        selectedIndex: $q3Answer
                    )

                    // Question 4: 습관/루틴 관련
                    QuestionSection(
                        icon: "moon.stars.fill",
                        title: "습관 / 루틴 관련",
                        question: "아침형인가요, 밤형인가요?",
                        options: ["아침", "둘다 아님", "밤"],
                        selectedIndex: $q4Answer
                    )

                    // Question 5: 수면 시간
                    QuestionSection(
                        icon: "bed.double.fill",
                        title: nil,
                        question: "하루 평균 수면 시간은?",
                        options: ["4-6", "6-8", "8이상"],
                        selectedIndex: $q5Answer
                    )

                    // Question 6: 루틴
                    QuestionSection(
                        icon: "figure.walk",
                        title: nil,
                        question: "자주 하는 루틴은?",
                        options: ["헬스", "산책", "카페 가기", "명상", "스트레칭", "자전거"],
                        selectedIndex: $q6Answer,
                        columns: 2
                    )

                    // Question 7: 디지털 기기
                    QuestionSection(
                        icon: "iphone",
                        title: "디지털 가기를 가장 자주 쓰는 시간대는?",
                        question: nil,
                        options: ["아침", "저녁", "하루 종일"],
                        selectedIndex: $q7Answer
                    )

                    // Question 8: 취미/관심사
                    QuestionSection(
                        icon: "gamecontroller.fill",
                        title: "취미 / 관심사",
                        question: "여가 시간에 가장 자주 하는 것은?",
                        options: ["음악", "영화·드라마", "웹툰", "게임", "카페", "운동"],
                        selectedIndex: $q8Answer,
                        columns: 2
                    )

                    // Submit button
                    Button(action: {
                        handleSubmit()
                    }) {
                        Text("제출하기")
                            .font(.system(size: 18, weight: .semibold))
                            .foregroundColor(isAllQuestionsAnswered ? Color(hex: "A50034") : .white.opacity(0.5))
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 16)
                            .background(
                                isAllQuestionsAnswered ? Color.white : Color.white.opacity(0.2)
                            )
                            .cornerRadius(25)
                    }
                    .disabled(!isAllQuestionsAnswered)
                    .padding(.horizontal, 20)
                    .padding(.top, 12)

                    Spacer(minLength: 120)
                }
            }

            // Bottom navigation bar
            VStack {
                Spacer()

                HStack(spacing: 0) {
                    // 답안 재조
                    BottomTabButton(
                        icon: "arrow.counterclockwise",
                        label: "답안 재조",
                        isSelected: selectedBottomTab == 0,
                        action: { selectedBottomTab = 0 }
                    )

                    // 다른 문제 생성
                    BottomTabButton(
                        icon: "circle.fill",
                        label: "다른 문제 생성",
                        isSelected: selectedBottomTab == 1,
                        action: { selectedBottomTab = 1 }
                    )

                    // 추가 문제
                    BottomTabButton(
                        icon: "triangle.fill",
                        label: "추가 문제",
                        isSelected: selectedBottomTab == 2,
                        action: { selectedBottomTab = 2 }
                    )
                }
                .frame(height: 80)
                .background(Color(hex: "E8C0CD"))
                .clipShape(RoundedRectangle(cornerRadius: 40))
                .padding(.horizontal, 40)
                .padding(.bottom, 30)
            }
        }
        .navigationBarTitleDisplayMode(.inline)
        .navigationBarBackButtonHidden(true)
        .toolbar {
            ToolbarItem(placement: .navigationBarLeading) {
                Button(action: { dismiss() }) {
                    Image(systemName: "chevron.left")
                        .foregroundColor(.white)
                        .font(.system(size: 18, weight: .semibold))
                }
            }
        }
    }

    // MARK: - Actions

    private func handleSubmit() {
        // Collect all answers
        let answers = [q1Answer, q2Answer, q3Answer, q4Answer, q5Answer, q6Answer, q7Answer, q8Answer]

        // TODO: Integrate with PersonaRepository to generate and save persona
        print("Persona test answers: \(answers)")

        // Navigate back to home
        dismiss()
    }
}

// MARK: - Question Section Component

struct QuestionSection: View {
    let icon: String?
    let title: String?
    let question: String?
    let options: [String]
    @Binding var selectedIndex: Int?
    var columns: Int = 3

    init(icon: String? = nil, title: String? = nil, question: String? = nil, options: [String], selectedIndex: Binding<Int?>, columns: Int = 3) {
        self.icon = icon
        self.title = title
        self.question = question
        self.options = options
        self._selectedIndex = selectedIndex
        self.columns = columns
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            // Title with icon
            if let title = title {
                HStack(spacing: 8) {
                    if let icon = icon {
                        Image(systemName: icon)
                            .font(.system(size: 18))
                    }
                    Text(title)
                        .font(.system(size: 17, weight: .semibold))
                }
                .foregroundColor(.white)
            }

            // Question text
            if let question = question {
                Text(question)
                    .font(.system(size: 16, weight: .medium))
                    .foregroundColor(.white)
                    .lineSpacing(4)
            }

            // Options
            if columns == 3 {
                HStack(spacing: 12) {
                    ForEach(0..<options.count, id: \.self) { index in
                        OptionButton(
                            text: options[index],
                            isSelected: selectedIndex == index,
                            action: { selectedIndex = index }
                        )
                    }
                }
            } else {
                let rows = stride(from: 0, to: options.count, by: columns).map {
                    Array(options[$0..<min($0 + columns, options.count)])
                }
                VStack(spacing: 12) {
                    ForEach(0..<rows.count, id: \.self) { rowIndex in
                        HStack(spacing: 12) {
                            ForEach(0..<rows[rowIndex].count, id: \.self) { colIndex in
                                let index = rowIndex * columns + colIndex
                                OptionButton(
                                    text: rows[rowIndex][colIndex],
                                    isSelected: selectedIndex == index,
                                    action: { selectedIndex = index }
                                )
                            }
                        }
                    }
                }
            }
        }
        .padding(.horizontal, 20)
    }
}

// MARK: - Option Button Component

struct OptionButton: View {
    let text: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(text)
                .font(.system(size: 15, weight: .medium))
                .foregroundColor(isSelected ? Color(hex: "A50034") : .white)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 12)
                .background(
                    isSelected ? Color.white : Color.clear
                )
                .cornerRadius(20)
                .overlay(
                    RoundedRectangle(cornerRadius: 20)
                        .stroke(Color.white, lineWidth: 1.5)
                )
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Bottom Tab Button Component

struct BottomTabButton: View {
    let icon: String
    let label: String
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            VStack(spacing: 6) {
                Image(systemName: icon)
                    .font(.system(size: 24))
                    .foregroundColor(isSelected ? Color(hex: "A50034") : .black)

                Text(label)
                    .font(.system(size: 11, weight: .medium))
                    .foregroundColor(isSelected ? Color(hex: "A50034") : .black)
                    .lineLimit(1)
                    .minimumScaleFactor(0.8)
            }
            .frame(maxWidth: .infinity)
        }
        .buttonStyle(.plain)
    }
}

#Preview {
    NavigationStack {
        PersonalTestView(selectedPersonas: .constant([]))
    }
}
