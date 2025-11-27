import Foundation

class FastAPIService {
    static let shared = FastAPIService()

    private let baseURL = "http://13.125.85.158:11325"

    private init() {}

    // MARK: - User Registration

    /// FastAPI 백엔드에 사용자 이메일 등록
    /// - Parameter email: 등록할 이메일 주소
    /// - Returns: 성공 시 백엔드 user_id (UUID), 실패 시 nil
    func registerUser(email: String) async -> String? {
        guard let url = URL(string: "\(baseURL)/api/users/") else {
            print("  [FastAPI] Invalid URL")
            return nil
        }

        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")

        let body: [String: String] = ["email": email]

        do {
            request.httpBody = try JSONSerialization.data(withJSONObject: body)

            let (data, response) = try await URLSession.shared.data(for: request)

            guard let httpResponse = response as? HTTPURLResponse else {
                print("  [FastAPI] Invalid response")
                return nil
            }

            // 성공 응답 (201 Created)
            if httpResponse.statusCode == 201 {
                if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
                   let userId = json["id"] as? String {
                    print(" [FastAPI] User registered successfully: \(userId)")
                    return userId
                }
            }

            // 이미 등록된 이메일 (400 Bad Request)
            if httpResponse.statusCode == 400 {
                print("⚠️ [FastAPI] Email already registered (400) - continuing")
                return nil // 이미 등록되어 있으므로 에러가 아님
            }

            // 기타 에러
            print("  [FastAPI] Registration failed with status: \(httpResponse.statusCode)")
            if let errorString = String(data: data, encoding: .utf8) {
                print("  [FastAPI] Error details: \(errorString)")
            }
            return nil

        } catch {
            print("  [FastAPI] Network error: \(error.localizedDescription)")
            return nil
        }
    }

    /// 이메일로 사용자 정보 조회 (향후 확장용)
    /// - Parameter email: 조회할 이메일
    /// - Returns: 사용자 정보 딕셔너리
    func getUser(email: String) async -> [String: Any]? {
        // TODO: GET /api/users/ 엔드포인트로 필터링 또는
        // GET /api/users/{user_id} 엔드포인트 사용
        return nil
    }
}
