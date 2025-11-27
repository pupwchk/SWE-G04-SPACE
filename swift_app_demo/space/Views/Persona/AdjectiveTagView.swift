//
//  AdjectiveTagView.swift
//  space
//
//  형용사 선택 태그 컴포넌트

import SwiftUI

/// 형용사 태그 버튼 컴포넌트
struct AdjectiveTag: View {
    let adjective: Adjective
    let isSelected: Bool
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Text(adjective.adjectiveName)
                .font(.system(size: 15, weight: .medium))
                .foregroundColor(isSelected ? .white : Color(hex: "A50034"))
                .padding(.horizontal, 16)
                .padding(.vertical, 10)
                .background(
                    isSelected ? Color(hex: "A50034") : Color.white
                )
                .cornerRadius(20)
                .overlay(
                    RoundedRectangle(cornerRadius: 20)
                        .stroke(Color(hex: "A50034"), lineWidth: 1.5)
                )
        }
        .buttonStyle(.plain)
    }
}

/// 선택된 형용사를 표시하는 읽기 전용 태그
struct SelectedAdjectiveTag: View {
    let text: String

    var body: some View {
        Text(text)
            .font(.system(size: 14, weight: .medium))
            .foregroundColor(.white)
            .padding(.horizontal, 14)
            .padding(.vertical, 8)
            .background(Color(hex: "A50034"))
            .cornerRadius(16)
    }
}

#Preview {
    VStack(spacing: 12) {
        AdjectiveTag(
            adjective: Adjective(
                id: "1",
                adjectiveName: "미래지향적",
                instructionText: "혁신적이고 최신 트렌드를 반영한 답변을 제공합니다.",
                category: "톤",
                createdAt: nil,
                updatedAt: nil
            ),
            isSelected: false,
            action: {}
        )

        AdjectiveTag(
            adjective: Adjective(
                id: "2",
                adjectiveName: "문학적",
                instructionText: "풍부한 표현과 비유를 사용하여 감성적이고 서정적인 답변을 제공합니다.",
                category: "톤",
                createdAt: nil,
                updatedAt: nil
            ),
            isSelected: true,
            action: {}
        )

        SelectedAdjectiveTag(text: "자기주장")
    }
    .padding()
}
