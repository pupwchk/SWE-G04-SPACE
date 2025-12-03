//
//  LoginView.swift
//  space
//
//  Created by 임동현 on 11/3/25.
//

import SwiftUI

/// Main login screen with liquid glass effect top banner
struct LoginView: View {
    @Binding var isLoggedIn: Bool

    @State private var email: String = ""
    @State private var password: String = ""
    @State private var showSignUp: Bool = false
    @State private var isLoading: Bool = false
    @State private var errorMessage: String?
    @State private var showError: Bool = false

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

                    loginCard
                    socialLoginSection
                }
                .padding(.horizontal, 20)
                .padding(.bottom, 40)
            }
        }
        .sheet(isPresented: $showSignUp) {
            SignUpView(isLoggedIn: $isLoggedIn)
        }
    }

    // MARK: - Login Card Component
    private var loginCard: some View {
        VStack(alignment: .leading, spacing: 18) {
            // Title
            Text("HARU에 오신 것을 환영합니다")
                .font(.system(size: 26, weight: .bold, design: .default))
                .foregroundColor(.black)
                .padding(.bottom, 4)

            // Email field
            VStack(alignment: .leading, spacing: 6) {
                Text("이메일 주소")
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(Color(hex: "A50034"))

                TextField("your@email.com", text: $email)
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

                SecureField("비밀번호를 입력하세요", text: $password)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 14)
                    .background(Color.white)
                    .cornerRadius(10)
                    .overlay(
                        RoundedRectangle(cornerRadius: 10)
                            .stroke(Color.gray.opacity(0.25), lineWidth: 1)
                    )
                    .textContentType(.password)
            }

            // Forgot password link
            HStack {
                Spacer()
                Button(action: {
                    // Handle forgot password
                }) {
                    Text("비밀번호를 잊으셨나요?")
                        .font(.system(size: 13, weight: .medium))
                        .foregroundColor(Color(hex: "A50034"))
                }
            }
            .padding(.top, -4)

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

            // Login button
            Button(action: {
                handleLogin()
            }) {
                HStack(spacing: 8) {
                    if isLoading {
                        ProgressView()
                            .progressViewStyle(CircularProgressViewStyle(tint: .white))
                            .scaleEffect(0.8)
                    }
                    Text(isLoading ? "로그인 중..." : "로그인")
                        .font(.system(size: 17, weight: .bold))
                        .foregroundColor(.white)
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 15)
                .background(isLoading ? Color(hex: "A50034").opacity(0.7) : Color(hex: "A50034"))
                .cornerRadius(10)
            }
            .disabled(isLoading || email.isEmpty || password.isEmpty)
            .buttonStyle(.plain)
            .padding(.top, 4)

            // Register link
            HStack(spacing: 4) {
                Text("계정이 없으신가요?")
                    .font(.system(size: 13))
                    .foregroundColor(.gray)

                Button(action: {
                    showSignUp = true
                }) {
                    Text("회원가입")
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

    // MARK: - Social Login Section
    private var socialLoginSection: some View {
        VStack(spacing: 20) {
            // Divider with text
            HStack(spacing: 10) {
                Rectangle()
                    .fill(Color.gray.opacity(0.25))
                    .frame(height: 1)

                Text("또는 다음으로 계속하기")
                    .font(.system(size: 13, weight: .regular))
                    .foregroundColor(Color.gray.opacity(0.7))
                    .lineLimit(1)
                    .fixedSize(horizontal: true, vertical: false)

                Rectangle()
                    .fill(Color.gray.opacity(0.25))
                    .frame(height: 1)
            }

            // Social login buttons
            HStack(spacing: 20) {
                SocialLoginButton(imageName: "btn_google") {
                    handleSocialLogin(provider: "Google")
                }

                SocialLoginButton(imageName: "btn_apple") {
                    handleSocialLogin(provider: "Apple")
                }

                SocialLoginButton(imageName: "btn_naver") {
                    handleSocialLogin(provider: "Naver")
                }

                SocialLoginButton(imageName: "btn_kakao") {
                    handleSocialLogin(provider: "Kakao")
                }
            }
        }
    }

    // MARK: - Login Handler
    private func handleLogin() {
        // Reset error message
        errorMessage = nil
        isLoading = true

        Task {
            do {
                let user = try await supabaseManager.signIn(email: email, password: password)
                print("Login successful: \(user.email)")

                // NOTE: SendBird Calls authentication is handled in SupabaseManager.signIn()
                // after FastAPI user registration completes
                await MainActor.run {
                    isLoading = false
                    withAnimation {
                        isLoggedIn = true
                    }
                }
            } catch {
                await MainActor.run {
                    isLoading = false
                    errorMessage = error.localizedDescription
                    showError = true

                    // Clear error message after 5 seconds
                    DispatchQueue.main.asyncAfter(deadline: .now() + 5) {
                        errorMessage = nil
                    }
                }
            }
        }
    }

    // MARK: - Social Login Handler
    private func handleSocialLogin(provider: String) {
        // TODO: Implement social login logic
        print("\(provider) login tapped")

        // For now, simply navigate to main tab view
        withAnimation {
            isLoggedIn = true
        }
    }
}

#Preview {
    LoginView(isLoggedIn: .constant(false))
}
