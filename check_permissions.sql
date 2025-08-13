-- Check current permissions and table status
-- Run this in Supabase SQL Editor

-- 1. Check if tables exist
SELECT table_name, table_schema 
FROM information_schema.tables 
WHERE table_name IN ('fast_symptoms', 'fast_diseases', 'fast_probabilities');

-- 2. Check RLS status
SELECT schemaname, tablename, rowsecurity, hasrls
FROM pg_tables 
WHERE tablename IN ('fast_symptoms', 'fast_diseases', 'fast_probabilities');

-- 3. Check policies
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual
FROM pg_policies 
WHERE tablename IN ('fast_symptoms', 'fast_diseases', 'fast_probabilities');

-- 4. Check grants for anon role
SELECT table_name, privilege_type, grantee
FROM information_schema.role_table_grants 
WHERE table_name IN ('fast_symptoms', 'fast_diseases', 'fast_probabilities')
AND grantee = 'anon';

-- 5. Try a simple insert test (this should work if permissions are correct)
-- INSERT INTO fast_symptoms (symptom_name, symptom_count) VALUES ('test_permission', 1);
-- SELECT * FROM fast_symptoms WHERE symptom_name = 'test_permission';
-- DELETE FROM fast_symptoms WHERE symptom_name = 'test_permission';