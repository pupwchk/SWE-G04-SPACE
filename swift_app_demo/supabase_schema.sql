-- ========================================
-- Supabase Database Schema for SPACE App
-- ========================================
-- Run this SQL in your Supabase SQL Editor
-- ========================================

-- 1. User Profiles Table
-- Stores extended user information
CREATE TABLE IF NOT EXISTS public.user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    name TEXT,
    birthday TEXT,
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Enable Row Level Security (RLS)
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

-- RLS Policies for user_profiles
CREATE POLICY "Users can view their own profile"
    ON public.user_profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can insert their own profile"
    ON public.user_profiles FOR INSERT
    WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
    ON public.user_profiles FOR UPDATE
    USING (auth.uid() = id);

CREATE POLICY "Users can delete their own profile"
    ON public.user_profiles FOR DELETE
    USING (auth.uid() = id);

-- ========================================

-- 2. User Settings Table
-- Stores user preferences and settings
CREATE TABLE IF NOT EXISTS public.user_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    notification_method TEXT DEFAULT 'push',
    do_not_disturb_start TIME,
    do_not_disturb_end TIME,
    haru_notification_enabled BOOLEAN DEFAULT true,
    font_size TEXT DEFAULT 'medium',
    emergency_call_enabled BOOLEAN DEFAULT true,
    call_summary_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(user_id)
);

ALTER TABLE public.user_settings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own settings"
    ON public.user_settings FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own settings"
    ON public.user_settings FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own settings"
    ON public.user_settings FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own settings"
    ON public.user_settings FOR DELETE
    USING (auth.uid() = user_id);

-- ========================================

-- 3. User Tones Table
-- Stores selected speaking tones for chat and phone
CREATE TABLE IF NOT EXISTS public.user_tones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    tone_name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    UNIQUE(user_id, tone_name)
);

ALTER TABLE public.user_tones ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own tones"
    ON public.user_tones FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own tones"
    ON public.user_tones FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own tones"
    ON public.user_tones FOR DELETE
    USING (auth.uid() = user_id);

-- ========================================

-- 4. Timeline Records Table (Optional - for future use)
-- Stores user's timeline/exercise tracking data
CREATE TABLE IF NOT EXISTS public.timeline_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    total_distance NUMERIC(10, 2),
    average_speed NUMERIC(10, 2),
    max_speed NUMERIC(10, 2),
    duration INTEGER,
    coordinates JSONB,
    checkpoints JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

ALTER TABLE public.timeline_records ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own timeline records"
    ON public.timeline_records FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own timeline records"
    ON public.timeline_records FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own timeline records"
    ON public.timeline_records FOR DELETE
    USING (auth.uid() = user_id);

-- ========================================

-- 5. Call History Table (Optional - for future use)
-- Stores phone call records
CREATE TABLE IF NOT EXISTS public.call_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    contact_name TEXT NOT NULL,
    call_type TEXT NOT NULL,
    duration NUMERIC(10, 2),
    summary TEXT,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

ALTER TABLE public.call_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own call history"
    ON public.call_history FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own call history"
    ON public.call_history FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own call history"
    ON public.call_history FOR DELETE
    USING (auth.uid() = user_id);

-- ========================================

-- 6. Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_user_settings_user_id ON public.user_settings(user_id);
CREATE INDEX IF NOT EXISTS idx_user_tones_user_id ON public.user_tones(user_id);
CREATE INDEX IF NOT EXISTS idx_timeline_records_user_id ON public.timeline_records(user_id);
CREATE INDEX IF NOT EXISTS idx_call_history_user_id ON public.call_history(user_id);

-- ========================================

-- 7. Create function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = timezone('utc'::text, now());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON public.user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

CREATE TRIGGER update_user_settings_updated_at
    BEFORE UPDATE ON public.user_settings
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

-- ========================================
-- End of Schema
-- ========================================

-- Optional: Create a function to initialize user data after signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    -- Create user profile
    INSERT INTO public.user_profiles (id, email, name)
    VALUES (NEW.id, NEW.email, NULL);

    -- Create default settings
    INSERT INTO public.user_settings (user_id)
    VALUES (NEW.id);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger to run after user signup
-- Note: This trigger should be created on auth.users table
-- You may need to run this with proper permissions
-- DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
-- CREATE TRIGGER on_auth_user_created
--     AFTER INSERT ON auth.users
--     FOR EACH ROW
--     EXECUTE FUNCTION public.handle_new_user();
