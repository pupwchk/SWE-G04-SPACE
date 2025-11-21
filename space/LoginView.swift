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

            VStack(spacing: 0) {
                // MARK: - Liquid Glass Top Banner
                liquidGlassBanner
                    .frame(height: 260)

                // MARK: - Login Card Section
                GeometryReader { proxy in
                    ScrollView(showsIndicators: false) {
                        VStack(spacing: 24) {
                            Spacer(minLength: 0) // Push content down when there is extra space
                            loginCard
                            socialLoginSection
                        }
                        .frame(minHeight: proxy.size.height, alignment: .top)
                        .padding(.horizontal, 20)
                        .padding(.top, -12) // Keep slight overlap with the banner
                        .padding(.bottom, 32)
                    }
                }
            }
        }
        .ignoresSafeArea(edges: .top)
        .sheet(isPresented: $showSignUp) {
            SignUpView(isLoggedIn: $isLoggedIn)
        }
    }

    // MARK: - Liquid Glass Banner Component
    private var liquidGlassBanner: some View {
        ZStack {
            // Base burgundy background
            Color(hex: "A50034")

            // Rotated "SPACE" text
            Text("SPACE")
                .font(.system(size: 80, weight: .bold, design: .default))
                .foregroundColor(.white)
                .rotationEffect(.degrees(-15))
                .offset(x: 10, y: 30)
        }
    }

    // MARK: - Login Card Component
    private var loginCard: some View {
        VStack(alignment: .leading, spacing: 18) {
            // Title
            Text("Welcome to SPACE")
                .font(.system(size: 26, weight: .bold, design: .default))
                .foregroundColor(.black)
                .padding(.bottom, 4)

            // Email field
            VStack(alignment: .leading, spacing: 6) {
                Text("Email Address")
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(Color.gray.opacity(0.8))

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
                Text("Password")
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(Color.gray.opacity(0.8))

                SecureField("Enter your password", text: $password)
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
                    Text("Forgot password?")
                        .font(.system(size: 13, weight: .medium))
                        .foregroundColor(.blue)
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

            // Temporary bypass button for testing
            Button(action: {
                print("Bypass button tapped")
                withAnimation {
                    isLoggedIn = true
                }
            }) {
                Text("🚀 홈 화면으로 바로가기 (테스트용)")
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundColor(Color(hex: "A50034"))
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 12)
                    .background(Color(hex: "A50034").opacity(0.1))
                    .cornerRadius(10)
                    .overlay(
                        RoundedRectangle(cornerRadius: 10)
                            .stroke(Color(hex: "A50034").opacity(0.3), lineWidth: 1.5)
                    )
            }
            .buttonStyle(.plain)
            .padding(.top, 8)

            // Register link
            HStack(spacing: 4) {
                Text("Not a member?")
                    .font(.system(size: 13))
                    .foregroundColor(.gray)

                Button(action: {
                    showSignUp = true
                }) {
                    Text("Register now")
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

                Text("Or continue with")
                    .font(.system(size: 13, weight: .regular))
                    .foregroundColor(Color.gray.opacity(0.7))

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
