//
//  SignUpView.swift
//  space
//
//  Created by 임동현 on 11/3/25.
//

import SwiftUI

/// Sign up screen with form fields for user registration
struct SignUpView: View {
    @Binding var isLoggedIn: Bool
    @Environment(\.dismiss) var dismiss

    @State private var name: String = ""
    @State private var email: String = ""
    @State private var password: String = ""
    @State private var confirmPassword: String = ""
    @State private var showPassword: Bool = false
    @State private var showConfirmPassword: Bool = false
    @State private var agreedToTerms: Bool = false
    @State private var isLoading: Bool = false
    @State private var errorMessage: String?
    @State private var showSuccess: Bool = false

    @StateObject private var supabaseManager = SupabaseManager.shared

    var body: some View {
        ZStack {
            // Background color
            Color(hex: "F9F9F9")
                .ignoresSafeArea()

            ScrollView(showsIndicators: false) {
                VStack(spacing: 32) {
                    // 상단 여백 (SafeArea 아래)
                    Spacer()
                        .frame(height: 40)

                    signUpCard
                }
                .padding(.horizontal, 20)
                .padding(.bottom, 40)
            }
        }
    }

    // MARK: - Sign Up Card Component
    private var signUpCard: some View {
        VStack(alignment: .leading, spacing: 18) {
            // Title and subtitle
            VStack(alignment: .leading, spacing: 4) {
                Text("회원가입")
                    .font(.system(size: 26, weight: .bold, design: .default))
                    .foregroundColor(.black)

                Text("시작하기 위해 계정을 만드세요")
                    .font(.system(size: 14, weight: .regular))
                    .foregroundColor(Color.gray.opacity(0.8))
            }
            .padding(.bottom, 4)

            // Name field
            VStack(alignment: .leading, spacing: 6) {
                Text("이름")
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(Color(hex: "A50034"))

                TextField("이름을 입력하세요", text: $name)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 14)
                    .background(Color.white)
                    .cornerRadius(10)
                    .overlay(
                        RoundedRectangle(cornerRadius: 10)
                            .stroke(name.isEmpty ? Color.gray.opacity(0.25) : Color(hex: "A50034"), lineWidth: name.isEmpty ? 1 : 1.5)
                    )
                    .autocapitalization(.words)
                    .disableAutocorrection(true)
                    .textContentType(.name)
            }

            // Email field
            VStack(alignment: .leading, spacing: 6) {
                Text("이메일 주소")
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(Color(hex: "A50034"))

                TextField("name@email.com", text: $email)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 14)
                    .background(Color.white)
                    .cornerRadius(10)
                    .overlay(
                        RoundedRectangle(cornerRadius: 10)
                            .stroke(Color.gray.opacity(0.25), lineWidth: 1)
                    )
                    .autocapitalization(.none)
                    .disableAutocorrection(true)
                    .keyboardType(.emailAddress)
                    .textContentType(.emailAddress)
            }

            // Password field
            VStack(alignment: .leading, spacing: 6) {
                Text("비밀번호")
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(Color(hex: "A50034"))

                HStack {
                    if showPassword {
                        TextField("비밀번호를 만드세요", text: $password)
                            .autocapitalization(.none)
                            .disableAutocorrection(true)
                            .textContentType(.newPassword)
                    } else {
                        SecureField("비밀번호를 만드세요", text: $password)
                            .autocapitalization(.none)
                            .textContentType(.newPassword)
                    }

                    Button(action: {
                        showPassword.toggle()
                    }) {
                        Image(systemName: showPassword ? "eye.slash.fill" : "eye.fill")
                            .foregroundColor(Color.gray.opacity(0.5))
                            .frame(width: 20, height: 20)
                    }
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 14)
                .background(Color.white)
                .cornerRadius(10)
                .overlay(
                    RoundedRectangle(cornerRadius: 10)
                        .stroke(Color.gray.opacity(0.25), lineWidth: 1)
                )
            }

            // Confirm Password field
            VStack(alignment: .leading, spacing: 6) {
                Text("비밀번호 확인")
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(Color(hex: "A50034"))

                HStack {
                    if showConfirmPassword {
                        TextField("비밀번호를 확인하세요", text: $confirmPassword)
                            .autocapitalization(.none)
                            .disableAutocorrection(true)
                            .textContentType(.newPassword)
                    } else {
                        SecureField("비밀번호를 확인하세요", text: $confirmPassword)
                            .autocapitalization(.none)
                            .textContentType(.newPassword)
                    }

                    Button(action: {
                        showConfirmPassword.toggle()
                    }) {
                        Image(systemName: showConfirmPassword ? "eye.slash.fill" : "eye.fill")
                            .foregroundColor(Color.gray.opacity(0.5))
                            .frame(width: 20, height: 20)
                    }
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 14)
                .background(Color.white)
                .cornerRadius(10)
                .overlay(
                    RoundedRectangle(cornerRadius: 10)
                        .stroke(Color.gray.opacity(0.25), lineWidth: 1)
                )
            }

            // Password validation hints
            if !password.isEmpty && password.count < 6 {
                Text("비밀번호는 최소 6자 이상이어야 합니다")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(.orange)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(Color.orange.opacity(0.1))
                    .cornerRadius(6)
            }

            // Password match validation
            if !confirmPassword.isEmpty && password != confirmPassword {
                Text("비밀번호가 일치하지 않습니다")
                    .font(.system(size: 12, weight: .medium))
                    .foregroundColor(.red)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 4)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(Color.red.opacity(0.1))
                    .cornerRadius(6)
            }

            // Error message
            if let errorMessage = errorMessage {
                Text(errorMessage)
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(.red)
                    .padding(.horizontal, 8)
                    .padding(.vertical, 6)
                    .frame(maxWidth: .infinity, alignment: .leading)
                    .background(Color.red.opacity(0.1))
                    .cornerRadius(8)
            }

            // Success message
            if showSuccess {
                HStack(spacing: 8) {
                    Image(systemName: "checkmark.circle.fill")
                        .foregroundColor(.green)
                    Text("계정이 성공적으로 생성되었습니다!")
                        .font(.system(size: 13, weight: .medium))
                        .foregroundColor(.green)
                }
                .padding(.horizontal, 8)
                .padding(.vertical, 6)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(Color.green.opacity(0.1))
                .cornerRadius(8)
            }

            // Terms and conditions checkbox
            HStack(alignment: .top, spacing: 10) {
                Button(action: {
                    agreedToTerms.toggle()
                }) {
                    Image(systemName: agreedToTerms ? "checkmark.square.fill" : "square")
                        .foregroundColor(agreedToTerms ? Color(hex: "A50034") : Color.gray.opacity(0.4))
                        .font(.system(size: 20))
                }

                VStack(alignment: .leading, spacing: 2) {
                    HStack(spacing: 3) {
                        Text("다음을 읽고 동의합니다:")
                            .font(.system(size: 12))
                            .foregroundColor(Color.gray.opacity(0.8))

                        Button(action: {
                            // Handle terms and conditions
                        }) {
                            Text("이용약관")
                                .font(.system(size: 12, weight: .medium))
                                .foregroundColor(Color(hex: "A50034"))
                        }
                    }

                    HStack(spacing: 3) {
                        Text("및")
                            .font(.system(size: 12))
                            .foregroundColor(Color.gray.opacity(0.8))

                        Button(action: {
                            // Handle privacy policy
                        }) {
                            Text("개인정보 처리방침")
                                .font(.system(size: 12, weight: .medium))
                                .foregroundColor(Color(hex: "A50034"))
                        }
                    }
                }
            }
            .padding(.top, 4)

            // Sign up button
            Button(action: {
                // Handle sign up
                handleSignUp()
            }) {
                HStack(spacing: 8) {
                    if isLoading {
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: .white))
                            .scaleEffect(0.8)
                    }
                    Text(isLoading ? "계정 생성 중..." : "회원가입")
                        .font(.system(size: 17, weight: .bold))
                        .foregroundColor(.white)
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 15)
                .background(isFormValid && !isLoading ? Color(hex: "A50034") : Color.gray.opacity(0.4))
                .cornerRadius(10)
            }
            .disabled(!isFormValid || isLoading)
            .padding(.top, 8)

            // Already have account link
            HStack(spacing: 4) {
                Text("이미 계정이 있으신가요?")
                    .font(.system(size: 13))
                    .foregroundColor(.gray)

                Button(action: {
                    dismiss()
                }) {
                    Text("로그인")
                        .font(.system(size: 13, weight: .semibold))
                        .foregroundColor(Color(hex: "A50034"))
                }
            }
            .frame(maxWidth: .infinity)
            .padding(.top, 2)
        }
        .padding(.horizontal, 24)
        .padding(.vertical, 28)
        .background(Color.white)
        .cornerRadius(20)
        .shadow(color: Color.black.opacity(0.06), radius: 12, x: 0, y: 2)
    }

    // MARK: - Form Validation
    private var isFormValid: Bool {
        !name.isEmpty &&
        !email.isEmpty &&
        email.contains("@") &&
        !password.isEmpty &&
        password.count >= 6 &&
        password == confirmPassword &&
        agreedToTerms
    }

    // MARK: - Sign Up Handler
    private func handleSignUp() {
        // Reset messages
        errorMessage = nil
        showSuccess = false
        isLoading = true

        Task {
            do {
                let user = try await supabaseManager.signUp(email: email, password: password, name: name)
                print("Sign up successful: \(user.email)")

                await MainActor.run {
                    isLoading = false
                    showSuccess = true

                    // Set logged in and close the view after a short delay
                    DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
                        isLoggedIn = true
                        dismiss()
                    }
                }
            } catch {
                await MainActor.run {
                    isLoading = false
                    errorMessage = error.localizedDescription

                    // Clear error message after 5 seconds
                    DispatchQueue.main.asyncAfter(deadline: .now() + 5) {
                        errorMessage = nil
                    }
                }
            }
        }
    }
}

#Preview {
    SignUpView(isLoggedIn: .constant(false))
}
