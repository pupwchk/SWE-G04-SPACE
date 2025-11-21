//
//  SignUpView.swift
//  space
//
//  Created by 임동현 on 11/3/25.
//

import SwiftUI

/// Sign up screen with form fields for user registration
struct SignUpView: View {
    @Environment(\.dismiss) var dismiss

    @State private var name: String = ""
    @State private var email: String = ""
    @State private var password: String = ""
    @State private var confirmPassword: String = ""
    @State private var showPassword: Bool = false
    @State private var showConfirmPassword: Bool = false
    @State private var agreedToTerms: Bool = false

    var body: some View {
        ZStack {
            // Background color
            Color(hex: "F9F9F9")
                .ignoresSafeArea()

            VStack(spacing: 0) {
                // MARK: - Top Banner
                topBanner
                    .frame(height: 260)

                // MARK: - Sign Up Form Section
                GeometryReader { proxy in
                    ScrollView(showsIndicators: false) {
                        VStack(spacing: 24) {
                            Spacer(minLength: 0)
                            signUpCard
                        }
                        .frame(minHeight: proxy.size.height, alignment: .top)
                        .padding(.horizontal, 20)
                        .padding(.top, -12)
                        .padding(.bottom, 32)
                    }
                }
            }
        }
        .ignoresSafeArea(edges: .top)
    }

    // MARK: - Top Banner Component
    private var topBanner: some View {
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

    // MARK: - Sign Up Card Component
    private var signUpCard: some View {
        VStack(alignment: .leading, spacing: 18) {
            // Title and subtitle
            VStack(alignment: .leading, spacing: 4) {
                Text("Sign up")
                    .font(.system(size: 26, weight: .bold, design: .default))
                    .foregroundColor(.black)

                Text("Create an account to get started")
                    .font(.system(size: 14, weight: .regular))
                    .foregroundColor(Color.gray.opacity(0.8))
            }
            .padding(.bottom, 4)

            // Name field
            VStack(alignment: .leading, spacing: 6) {
                Text("Name")
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(Color.gray.opacity(0.8))

                TextField("", text: $name)
                    .padding(.horizontal, 16)
                    .padding(.vertical, 14)
                    .background(Color.white)
                    .cornerRadius(10)
                    .overlay(
                        RoundedRectangle(cornerRadius: 10)
                            .stroke(name.isEmpty ? Color.gray.opacity(0.25) : Color(hex: "A50034"), lineWidth: name.isEmpty ? 1 : 1.5)
                    )
                    .autocapitalization(.words)
            }

            // Email field
            VStack(alignment: .leading, spacing: 6) {
                Text("Email Address")
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(Color.gray.opacity(0.8))

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
                    .keyboardType(.emailAddress)
            }

            // Password field
            VStack(alignment: .leading, spacing: 6) {
                Text("Password")
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(Color.gray.opacity(0.8))

                HStack {
                    if showPassword {
                        TextField("Create a password", text: $password)
                            .autocapitalization(.none)
                    } else {
                        SecureField("Create a password", text: $password)
                            .autocapitalization(.none)
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
                Text("Confirm Password")
                    .font(.system(size: 13, weight: .medium))
                    .foregroundColor(Color.gray.opacity(0.8))

                HStack {
                    if showConfirmPassword {
                        TextField("Confirm password", text: $confirmPassword)
                            .autocapitalization(.none)
                    } else {
                        SecureField("Confirm password", text: $confirmPassword)
                            .autocapitalization(.none)
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
                        Text("I've read and agree with the")
                            .font(.system(size: 12))
                            .foregroundColor(Color.gray.opacity(0.8))

                        Button(action: {
                            // Handle terms and conditions
                        }) {
                            Text("Terms and Conditions")
                                .font(.system(size: 12, weight: .medium))
                                .foregroundColor(.blue)
                        }
                    }

                    HStack(spacing: 3) {
                        Text("and the")
                            .font(.system(size: 12))
                            .foregroundColor(Color.gray.opacity(0.8))

                        Button(action: {
                            // Handle privacy policy
                        }) {
                            Text("Privacy Policy")
                                .font(.system(size: 12, weight: .medium))
                                .foregroundColor(.blue)
                        }

                        Text(".")
                            .font(.system(size: 12))
                            .foregroundColor(Color.gray.opacity(0.8))
                    }
                }
            }
            .padding(.top, 4)

            // Sign up button
            Button(action: {
                // Handle sign up
                handleSignUp()
            }) {
                Text("Sign up")
                    .font(.system(size: 17, weight: .bold))
                    .foregroundColor(.white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 15)
                    .background(isFormValid ? Color(hex: "A50034") : Color.gray.opacity(0.4))
                    .cornerRadius(10)
            }
            .disabled(!isFormValid)
            .padding(.top, 8)

            // Already have account link
            HStack(spacing: 4) {
                Text("Already have an account?")
                    .font(.system(size: 13))
                    .foregroundColor(.gray)

                Button(action: {
                    dismiss()
                }) {
                    Text("Sign in")
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
        // TODO: Implement sign up logic
        print("Sign up with:")
        print("Name: \(name)")
        print("Email: \(email)")
        print("Password: \(password)")

        // Close the sign up view
        dismiss()
    }
}

#Preview {
    SignUpView()
}
