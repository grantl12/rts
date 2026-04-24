-- Red Tape & Renegades: Core Schema

-- 1. PLAYER PROFILES
-- Tracks meta-progression and "Legacy Points"
CREATE TABLE profiles (
    id UUID PRIMARY KEY REFERENCES auth.users ON DELETE CASCADE,
    username TEXT UNIQUE,
    legacy_points INTEGER DEFAULT 0,
    faction_preference TEXT CHECK (faction_preference IN ('Regency', 'Sovereign', 'Frontline', 'Oligarchy')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. THE HALL OF HEROES (Persistent Units)
-- Units that hit the "Map Cap" and were retired/promoted.
CREATE TABLE hero_units (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    unit_type TEXT NOT NULL, -- e.g., 'Gravy Seal', 'Park Ranger', 'Conscript'
    nick_name TEXT,
    veterancy_rank INTEGER DEFAULT 1,
    kills_total INTEGER DEFAULT 0,
    missions_survived INTEGER DEFAULT 0,
    death_count INTEGER DEFAULT 0, -- For the "Soul" system - maybe they can be resurrected?
    assigned_to_board BOOLEAN DEFAULT FALSE, -- If true, provides global buffs
    metadata JSONB, -- For specific gear like 'Tactical Scooter' or 'Thermal Scopes'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. THE GLOBAL CONFLICT (World State)
-- Aggregated stats from all players to shift the "Neon Grid" colors.
CREATE TABLE global_conflict_stats (
    id INTEGER PRIMARY KEY CHECK (id = 1), -- Singleton row
    regency_control_percent NUMERIC(5,2) DEFAULT 25.0,
    sovereign_control_percent NUMERIC(5,2) DEFAULT 25.0,
    frontline_control_percent NUMERIC(5,2) DEFAULT 25.0,
    oligarchy_control_percent NUMERIC(5,2) DEFAULT 25.0,
    total_martyrs_created BIGINT DEFAULT 0,
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

-- 4. THE AUDIT TRAIL (Match History)
-- For the "Post-Mission" screen logic.
CREATE TABLE match_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    player_id UUID REFERENCES profiles(id),
    map_name TEXT,
    faction_played TEXT,
    outcome TEXT CHECK (outcome IN ('Success', 'Redacted', 'Total Panic')),
    units_lost INTEGER,
    legacy_earned INTEGER,
    match_date TIMESTAMPTZ DEFAULT NOW()
);
