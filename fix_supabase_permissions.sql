-- =================================================================
-- Fix Supabase Permissions for Data Loading
-- Run this in your Supabase SQL Editor
-- =================================================================

-- Temporarily disable RLS for data loading
ALTER TABLE fast_symptoms DISABLE ROW LEVEL SECURITY;
ALTER TABLE fast_diseases DISABLE ROW LEVEL SECURITY;
ALTER TABLE fast_probabilities DISABLE ROW LEVEL SECURITY;

-- OR if you prefer to keep RLS enabled, run these policies instead:
-- (Comment out the DISABLE commands above and uncomment these)

/*
-- Drop existing policies if any
DROP POLICY IF EXISTS "Enable read access for all users" ON fast_symptoms;
DROP POLICY IF EXISTS "Enable read access for all users" ON fast_diseases;
DROP POLICY IF EXISTS "Enable read access for all users" ON fast_probabilities;

-- Create permissive policies for anon access
CREATE POLICY "Allow all operations for anon" ON fast_symptoms FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations for anon" ON fast_diseases FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations for anon" ON fast_probabilities FOR ALL USING (true) WITH CHECK (true);

-- Grant all permissions to anon role
GRANT ALL ON fast_symptoms TO anon;
GRANT ALL ON fast_diseases TO anon;
GRANT ALL ON fast_probabilities TO anon;
GRANT USAGE ON SEQUENCE fast_symptoms_id_seq TO anon;
GRANT USAGE ON SEQUENCE fast_diseases_id_seq TO anon;
GRANT USAGE ON SEQUENCE fast_probabilities_id_seq TO anon;
*/