-- Create tagged_locations table
CREATE TABLE IF NOT EXISTS tagged_locations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    tag VARCHAR(50) NOT NULL,
    custom_name VARCHAR(100),
    is_home BOOLEAN DEFAULT FALSE,
    notification_enabled BOOLEAN DEFAULT TRUE,
    notification_radius INTEGER DEFAULT 1000,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_tagged_locations_user_id ON tagged_locations(user_id);
CREATE INDEX IF NOT EXISTS idx_tagged_locations_is_home ON tagged_locations(is_home);
CREATE INDEX IF NOT EXISTS idx_tagged_locations_user_home ON tagged_locations(user_id, is_home);

-- Enable RLS
ALTER TABLE tagged_locations ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Users can view their own tagged locations"
    ON tagged_locations FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own tagged locations"
    ON tagged_locations FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own tagged locations"
    ON tagged_locations FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own tagged locations"
    ON tagged_locations FOR DELETE
    USING (auth.uid() = user_id);

-- Create location_notifications table
CREATE TABLE IF NOT EXISTS location_notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    tagged_location_id UUID NOT NULL REFERENCES tagged_locations(id) ON DELETE CASCADE,
    triggered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    distance_meters INTEGER NOT NULL,
    acknowledged BOOLEAN DEFAULT FALSE
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_location_notifications_user_id ON location_notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_location_notifications_triggered_at ON location_notifications(triggered_at);
CREATE INDEX IF NOT EXISTS idx_location_notifications_tagged_location_id ON location_notifications(tagged_location_id);

-- Enable RLS
ALTER TABLE location_notifications ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Users can view their own location notifications"
    ON location_notifications FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own location notifications"
    ON location_notifications FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own location notifications"
    ON location_notifications FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own location notifications"
    ON location_notifications FOR DELETE
    USING (auth.uid() = user_id);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for tagged_locations
CREATE TRIGGER update_tagged_locations_updated_at
    BEFORE UPDATE ON tagged_locations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE tagged_locations IS 'Stores user-defined location tags (home, dormitory, etc.)';
COMMENT ON COLUMN tagged_locations.notification_radius IS 'Notification radius in meters (default: 1000m = 1km)';
COMMENT ON TABLE location_notifications IS 'Stores history of location-based notifications sent to users';
COMMENT ON COLUMN location_notifications.distance_meters IS 'Distance from tagged location when notification was triggered';
