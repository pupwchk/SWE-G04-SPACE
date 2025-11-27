import SwiftUI

struct MyPageView: View {
    @Environment(\.dismiss) var dismiss
    @StateObject private var supabaseManager = SupabaseManager.shared
    @State private var userProfile: UserProfile?
    @State private var isLoading = true
    @State private var showEditName = false
    @State private var showEditBirthday = false
    @State private var editedName = ""
    @State private var editedBirthday = ""
    @State private var showPasswordChange = false
    @State private var showAccountDeletion = false

    var body: some View {
        VStack(spacing: 0) {
            // Navigation bar
            HStack {
                Button(action: {
                    dismiss()
                }) {
                    Image(systemName: "chevron.left")
                        .font(.system(size: 20))
                        .foregroundColor(.black)
                }
                Spacer()
            }
            .padding(.horizontal, 20)
            .padding(.vertical, 16)

            // Title
            Text("마이페이지")
                .font(.system(size: 18, weight: .semibold))
                .frame(maxWidth: .infinity)
                .padding(.bottom, 30)

            // Profile avatar
            ZStack(alignment: .bottomTrailing) {
                Circle()
                    .fill(Color(red: 0.89, green: 0.82, blue: 0.85))
                    .frame(width: 100, height: 100)
                    .overlay(
                        Image(systemName: "person.fill")
                            .font(.system(size: 45))
                            .foregroundColor(Color(red: 0.71, green: 0.47, blue: 0.56))
                    )

                Circle()
                    .fill(Color(hex: "A50034"))
                    .frame(width: 32, height: 32)
                    .overlay(
                        Image(systemName: "pencil")
                            .font(.system(size: 14, weight: .semibold))
                            .foregroundColor(.white)
                    )
                    .offset(x: 4, y: 4)
            }
            .padding(.bottom, 40)

            if isLoading {
                ProgressView()
                    .padding()
            } else {
                // Settings rows
                VStack(spacing: 0) {
                    // Nickname row
                    Button(action: {
                        editedName = userProfile?.name ?? ""
                        showEditName = true
                    }) {
                        SettingsRow(
                            label: "닉네임",
                            value: userProfile?.name ?? "닉네임 없음"
                        )
                    }
                    .buttonStyle(PlainButtonStyle())

                    Divider()
                        .padding(.horizontal, 20)

                    // Account row (read-only)
                    SettingsRow(
                        label: "계정",
                        value: userProfile?.email ?? supabaseManager.currentUser?.email ?? ""
                    )

                    Divider()
                        .padding(.horizontal, 20)

                    // Birthday row
                    Button(action: {
                        editedBirthday = userProfile?.birthday ?? ""
                        showEditBirthday = true
                    }) {
                        SettingsRow(
                            label: "생일",
                            value: userProfile?.birthday ?? "생일 없음"
                        )
                    }
                    .buttonStyle(PlainButtonStyle())
                }
                .background(Color.white)
            }

            Spacer()

            // Bottom buttons
            HStack(spacing: 40) {
                Button(action: {
                    showPasswordChange = true
                }) {
                    Text("비밀번호 변경")
                        .font(.system(size: 14))
                        .foregroundColor(Color(white: 0.7))
                }

                Button(action: {
                    showAccountDeletion = true
                }) {
                    Text("탈퇴하기")
                        .font(.system(size: 14))
                        .foregroundColor(Color(white: 0.7))
                }
            }
            .padding(.bottom, 40)
        }
        .navigationBarHidden(true)
        .background(Color.white)
        .onAppear {
            Task {
                await loadUserProfile()
            }
        }
        .sheet(isPresented: $showEditName) {
            EditNameSheet(
                name: $editedName,
                onSave: {
                    Task {
                        await updateName()
                    }
                }
            )
        }
        .sheet(isPresented: $showEditBirthday) {
            EditBirthdaySheet(
                birthday: $editedBirthday,
                onSave: {
                    Task {
                        await updateBirthday()
                    }
                }
            )
        }
        .alert("비밀번호 변경", isPresented: $showPasswordChange) {
            Button("확인", role: .cancel) { }
        } message: {
            Text("비밀번호 변경 기능은 준비 중입니다.")
        }
        .alert("계정 탈퇴", isPresented: $showAccountDeletion) {
            Button("취소", role: .cancel) { }
            Button("탈퇴", role: .destructive) {
                // TODO: Implement account deletion
            }
        } message: {
            Text("정말로 계정을 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.")
        }
    }

    // MARK: - Data Loading

    private func loadUserProfile() async {
        isLoading = true
        defer { isLoading = false }

        do {
            let profile = try await supabaseManager.fetchUserProfile()
            userProfile = profile
        } catch {
            print("  Failed to load user profile: \(error.localizedDescription)")
        }
    }

    private func updateName() async {
        guard !editedName.isEmpty else { return }

        do {
            try await supabaseManager.updateUserProfile(
                name: editedName,
                birthday: nil,
                avatarUrl: nil
            )
            await loadUserProfile()
            showEditName = false
        } catch {
            print("  Failed to update name: \(error.localizedDescription)")
        }
    }

    private func updateBirthday() async {
        guard !editedBirthday.isEmpty else { return }

        do {
            try await supabaseManager.updateUserProfile(
                name: nil,
                birthday: editedBirthday,
                avatarUrl: nil
            )
            await loadUserProfile()
            showEditBirthday = false
        } catch {
            print("  Failed to update birthday: \(error.localizedDescription)")
        }
    }
}

// MARK: - Edit Name Sheet

struct EditNameSheet: View {
    @Environment(\.dismiss) var dismiss
    @Binding var name: String
    let onSave: () -> Void

    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                TextField("닉네임", text: $name)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .padding()

                Spacer()
            }
            .navigationTitle("닉네임 변경")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("취소") {
                        dismiss()
                    }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("저장") {
                        onSave()
                        dismiss()
                    }
                    .disabled(name.isEmpty)
                }
            }
        }
    }
}

// MARK: - Edit Birthday Sheet

struct EditBirthdaySheet: View {
    @Environment(\.dismiss) var dismiss
    @Binding var birthday: String
    let onSave: () -> Void

    var body: some View {
        NavigationView {
            VStack(spacing: 20) {
                TextField("생일 (예: 01/15)", text: $birthday)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                    .padding()

                Text("형식: MM/DD")
                    .font(.caption)
                    .foregroundColor(.gray)

                Spacer()
            }
            .navigationTitle("생일 변경")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("취소") {
                        dismiss()
                    }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("저장") {
                        onSave()
                        dismiss()
                    }
                    .disabled(birthday.isEmpty)
                }
            }
        }
    }
}

struct SettingsRow: View {
    let label: String
    let value: String

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 8) {
                Text(label)
                    .font(.system(size: 12))
                    .foregroundColor(Color(white: 0.8))

                Text(value)
                    .font(.system(size: 16))
                    .foregroundColor(.black)
            }

            Spacer()

            Image(systemName: "chevron.right")
                .font(.system(size: 14))
                .foregroundColor(Color(white: 0.8))
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 20)
        .contentShape(Rectangle())
    }
}

#Preview {
    MyPageView()
}
