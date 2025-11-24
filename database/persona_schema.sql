-- Persona System Database Schema
-- 맞춤형 지침 & 페르소나 시스템

-- 1. 형용사 테이블 (adjectives)
-- 기본 형용사 및 연결된 지침 프롬프트 저장
CREATE TABLE IF NOT EXISTS adjectives (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    adjective_name TEXT NOT NULL UNIQUE,
    instruction_text TEXT NOT NULL,
    category TEXT, -- 예: "톤", "역할", "도메인" 등 향후 확장용
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. 페르소나 테이블 (personas)
-- 사용자가 생성한 페르소나 저장
CREATE TABLE IF NOT EXISTS personas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    nickname TEXT NOT NULL,
    adjective_ids UUID[] DEFAULT '{}', -- 선택된 형용사 ID 배열
    custom_instructions TEXT, -- 사용자 직접 입력 지침
    final_prompt TEXT, -- 최종 병합된 프롬프트 (백엔드에서 생성)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. 활성 페르소나 테이블 (user_active_persona)
-- 각 사용자의 현재 활성화된 페르소나 저장
CREATE TABLE IF NOT EXISTS user_active_persona (
    user_id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    persona_id UUID REFERENCES personas(id) ON DELETE SET NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_personas_user_id ON personas(user_id);
CREATE INDEX IF NOT EXISTS idx_adjectives_name ON adjectives(adjective_name);

-- RLS (Row Level Security) 정책 설정
ALTER TABLE personas ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_active_persona ENABLE ROW LEVEL SECURITY;

-- personas 테이블 RLS 정책
CREATE POLICY "Users can view their own personas"
    ON personas FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own personas"
    ON personas FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own personas"
    ON personas FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own personas"
    ON personas FOR DELETE
    USING (auth.uid() = user_id);

-- user_active_persona 테이블 RLS 정책
CREATE POLICY "Users can view their own active persona"
    ON user_active_persona FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can update their own active persona"
    ON user_active_persona FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can modify their own active persona"
    ON user_active_persona FOR UPDATE
    USING (auth.uid() = user_id);

-- adjectives 테이블은 모든 사용자가 읽기 가능
ALTER TABLE adjectives ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Anyone can view adjectives"
    ON adjectives FOR SELECT
    USING (true);

-- 관리자만 형용사 추가/수정 가능 (향후 관리자 역할 추가 시)
CREATE POLICY "Only admins can manage adjectives"
    ON adjectives FOR ALL
    USING (false); -- 기본적으로 모두 거부, 관리자 역할 추가 시 수정

-- 기본 형용사 데이터 삽입
INSERT INTO adjectives (adjective_name, instruction_text, category) VALUES
    ('관습 중심', '전통적이고 일반적으로 사용되는 방식을 따르는 답변을 제공합니다. 검증된 방법과 표준을 중시합니다.', '톤'),
    ('미래지향적', '혁신적이고 최신 트렌드를 반영한 답변을 제공합니다. 새로운 기술과 방법론을 적극적으로 제안합니다.', '톤'),
    ('문학적', '풍부한 표현과 비유를 사용하여 감성적이고 서정적인 답변을 제공합니다.', '톤'),
    ('자기주장', '명확하고 확신에 찬 답변을 제공합니다. 주저하지 않고 직접적으로 의견을 표현합니다.', '톤'),
    ('간결하게', '핵심만 간단명료하게 전달합니다. 불필요한 설명을 최소화합니다.', '스타일'),
    ('자세하게', '상세한 설명과 예시를 포함하여 깊이 있는 답변을 제공합니다.', '스타일'),
    ('친근한', '친구처럼 편안하고 따뜻한 어조로 답변합니다.', '스타일'),
    ('전문적인', '공식적이고 전문가적인 어조로 답변합니다.', '스타일')
ON CONFLICT (adjective_name) DO NOTHING;

-- 업데이트 트리거 함수
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 업데이트 트리거 적용
CREATE TRIGGER update_adjectives_updated_at BEFORE UPDATE ON adjectives
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_personas_updated_at BEFORE UPDATE ON personas
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_active_persona_updated_at BEFORE UPDATE ON user_active_persona
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
