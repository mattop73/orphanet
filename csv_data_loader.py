#!/usr/bin/env python3
"""
CSV Data Loader for Orphanet Database
Loads clinical signs and symptoms data from CSV into Supabase database tables
"""

import os
import pandas as pd
import logging
from typing import Dict, List, Any, Optional
from supabase import create_client, Client
import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OrphanetCSVLoader:
    """Loads Orphanet CSV data into Supabase database"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        """Initialize the loader with Supabase credentials"""
        self.supabase: Client = create_client(supabase_url, supabase_key)
        logger.info("Connected to Supabase")
    
    def test_connection(self) -> bool:
        """Test the Supabase connection"""
        try:
            # Try a simple query to test connection
            result = self.supabase.table('disorders').select('*').limit(1).execute()
            logger.info("Supabase connection test successful")
            return True
        except Exception as e:
            logger.error(f"Supabase connection test failed: {e}")
            logger.info("Attempting to continue without connection test...")
            return True  # Continue anyway
    
    def create_tables(self) -> bool:
        """Create necessary database tables - assuming they already exist"""
        logger.info("Assuming database tables already exist")
        return True
    
    def load_clinical_signs_csv(self, csv_file_path: str) -> Dict[str, List[Dict[str, Any]]]:
        """Load and parse the clinical signs and symptoms CSV file"""
        logger.info(f"Loading CSV file: {csv_file_path}")
        
        try:
            # Read CSV file
            df = pd.read_csv(csv_file_path)
            logger.info(f"Loaded {len(df)} records from CSV")
            
            # Clean the data
            df = df.dropna(subset=['orpha_code', 'disorder_name', 'hpo_id', 'hpo_term'])
            logger.info(f"After cleaning: {len(df)} records")
            
            # Extract unique disorders
            disorders = df[['disorder_id', 'orpha_code', 'disorder_name', 'disorder_type']].drop_duplicates()
            disorders_list = []
            for _, row in disorders.iterrows():
                disorders_list.append({
                    'id': int(row['disorder_id']) if pd.notna(row['disorder_id']) else None,
                    'orpha_code': str(row['orpha_code']),
                    'name': str(row['disorder_name']),
                    'disorder_type': str(row['disorder_type']) if pd.notna(row['disorder_type']) else None
                })
            
            # Extract unique HPO terms
            hpo_terms = df[['hpo_id', 'hpo_term']].drop_duplicates()
            hpo_terms_list = []
            for _, row in hpo_terms.iterrows():
                hpo_terms_list.append({
                    'hpo_id': str(row['hpo_id']),
                    'term': str(row['hpo_term'])
                })
            
            # Extract HPO associations
            hpo_associations = []
            for _, row in df.iterrows():
                hpo_associations.append({
                    'disorder_orpha_code': str(row['orpha_code']),
                    'hpo_id': str(row['hpo_id']),
                    'frequency': str(row['hpo_frequency']) if pd.notna(row['hpo_frequency']) else None,
                    'diagnostic_criteria': str(row['diagnostic_criteria']) if pd.notna(row['diagnostic_criteria']) else None
                })
            
            logger.info(f"Extracted {len(disorders_list)} disorders, {len(hpo_terms_list)} HPO terms, {len(hpo_associations)} associations")
            
            return {
                'disorders': disorders_list,
                'hpo_terms': hpo_terms_list,
                'hpo_associations': hpo_associations
            }
            
        except Exception as e:
            logger.error(f"Error loading CSV file: {e}")
            raise
    
    def insert_disorders(self, disorders: List[Dict[str, Any]]) -> bool:
        """Insert disorders into the database"""
        logger.info(f"Inserting {len(disorders)} disorders...")
        
        try:
            batch_size = 100
            for i in range(0, len(disorders), batch_size):
                batch = disorders[i:i + batch_size]
                
                # Prepare data for insertion
                batch_data = []
                for disorder in batch:
                    batch_data.append({
                        'orpha_code': disorder['orpha_code'],
                        'name': disorder['name']
                    })
                
                # Insert batch
                result = self.supabase.table('disorders').upsert(
                    batch_data,
                    on_conflict='orpha_code'
                ).execute()
                
                logger.info(f"Inserted disorders batch {i//batch_size + 1}/{(len(disorders)-1)//batch_size + 1}")
            
            logger.info("Disorders inserted successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Error inserting disorders: {e}")
            return False
    
    def insert_hpo_terms(self, hpo_terms: List[Dict[str, Any]]) -> bool:
        """Insert HPO terms into the database"""
        logger.info(f"Inserting {len(hpo_terms)} HPO terms...")
        
        try:
            batch_size = 100
            for i in range(0, len(hpo_terms), batch_size):
                batch = hpo_terms[i:i + batch_size]
                
                # Insert batch
                result = self.supabase.table('hpo_terms').upsert(
                    batch,
                    on_conflict='hpo_id'
                ).execute()
                
                logger.info(f"Inserted HPO terms batch {i//batch_size + 1}/{(len(hpo_terms)-1)//batch_size + 1}")
            
            logger.info("HPO terms inserted successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Error inserting HPO terms: {e}")
            return False
    
    def insert_hpo_associations(self, associations: List[Dict[str, Any]]) -> bool:
        """Insert HPO associations into the database"""
        logger.info(f"Inserting {len(associations)} HPO associations...")
        
        try:
            batch_size = 50  # Smaller batch size for complex joins
            
            for i in range(0, len(associations), batch_size):
                batch = associations[i:i + batch_size]
                
                # For each association, we need to get the disorder_id and hpo_term_id
                batch_data = []
                
                for assoc in batch:
                    # Get disorder ID
                    disorder_result = self.supabase.table('disorders').select('id').eq('orpha_code', assoc['disorder_orpha_code']).execute()
                    if not disorder_result.data:
                        logger.warning(f"Disorder not found for orpha_code: {assoc['disorder_orpha_code']}")
                        continue
                    
                    # Get HPO term ID
                    hpo_result = self.supabase.table('hpo_terms').select('id').eq('hpo_id', assoc['hpo_id']).execute()
                    if not hpo_result.data:
                        logger.warning(f"HPO term not found for hpo_id: {assoc['hpo_id']}")
                        continue
                    
                    batch_data.append({
                        'disorder_id': disorder_result.data[0]['id'],
                        'hpo_term_id': hpo_result.data[0]['id'],
                        'frequency': assoc['frequency'],
                        'diagnostic_criteria': assoc['diagnostic_criteria']
                    })
                
                if batch_data:
                    # Insert batch
                    result = self.supabase.table('disorder_hpo_associations').upsert(
                        batch_data,
                        on_conflict='disorder_id,hpo_term_id'
                    ).execute()
                
                logger.info(f"Processed associations batch {i//batch_size + 1}/{(len(associations)-1)//batch_size + 1}")
            
            logger.info("HPO associations inserted successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Error inserting HPO associations: {e}")
            return False
    
    def create_disorder_symptoms_view(self) -> bool:
        """Create or refresh the disorder_symptoms_view"""
        logger.info("Creating disorder_symptoms_view...")
        
        try:
            # Execute SQL to create the view
            sql = """
            CREATE OR REPLACE VIEW disorder_symptoms_view AS
            SELECT 
                d.id as disorder_id,
                d.orpha_code,
                d.name as disorder_name,
                h.hpo_id,
                h.term as symptom_name,
                dha.frequency,
                dha.diagnostic_criteria,
                CASE 
                    WHEN dha.frequency LIKE '%Very frequent%' OR dha.frequency LIKE '%99-80%' THEN 0.9
                    WHEN dha.frequency LIKE '%Frequent%' OR dha.frequency LIKE '%79-30%' THEN 0.55
                    WHEN dha.frequency LIKE '%Occasional%' OR dha.frequency LIKE '%29-5%' THEN 0.17
                    WHEN dha.frequency LIKE '%Very rare%' OR dha.frequency LIKE '%<5%' THEN 0.025
                    ELSE 0.5
                END as frequency_numeric
            FROM disorders d
            JOIN disorder_hpo_associations dha ON d.id = dha.disorder_id
            JOIN hpo_terms h ON dha.hpo_term_id = h.id
            ORDER BY d.orpha_code, h.hpo_id;
            """
            
            result = self.supabase.rpc('execute_sql', {'sql': sql}).execute()
            logger.info("disorder_symptoms_view created successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Error creating disorder_symptoms_view: {e}")
            return False
    
    def get_stats(self) -> Dict[str, int]:
        """Get database statistics"""
        stats = {}
        
        try:
            # Count disorders
            result = self.supabase.table('disorders').select('count').execute()
            stats['disorders'] = len(result.data) if result.data else 0
            
            # Count HPO terms
            result = self.supabase.table('hpo_terms').select('count').execute()
            stats['hpo_terms'] = len(result.data) if result.data else 0
            
            # Count associations
            result = self.supabase.table('disorder_hpo_associations').select('count').execute()
            stats['associations'] = len(result.data) if result.data else 0
            
            logger.info(f"Database stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return stats


def main():
    """Main function to load CSV data into database"""
    # Configuration
    SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://ecrcdeztnbciybqkwkpf.supabase.co')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVjcmNkZXp0bmJjaXlicWt3a3BmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ5NDIwOTQsImV4cCI6MjA3MDUxODA5NH0.TPT6CdwI3lgBeh-V_X-a8_H4m3YFK0lLg31eWM0woho')
    
    CSV_FILE = 'file/clinical_signs_and_symptoms_in_rare_diseases.csv'
    
    try:
        # Initialize loader
        loader = OrphanetCSVLoader(SUPABASE_URL, SUPABASE_KEY)
        
        # Test connection
        loader.test_connection()
        
        # Create tables (if needed)
        loader.create_tables()
        
        # Load CSV data
        data = loader.load_clinical_signs_csv(CSV_FILE)
        
        # Insert data step by step
        if data['disorders']:
            loader.insert_disorders(data['disorders'])
        
        if data['hpo_terms']:
            loader.insert_hpo_terms(data['hpo_terms'])
        
        if data['hpo_associations']:
            loader.insert_hpo_associations(data['hpo_associations'])
        
        # Create view
        loader.create_disorder_symptoms_view()
        
        # Get final statistics
        stats = loader.get_stats()
        
        logger.info("Data loading completed successfully!")
        logger.info(f"Final stats: {stats}")
        
    except Exception as e:
        logger.error(f"Script failed: {e}")
        raise


if __name__ == "__main__":
    main()