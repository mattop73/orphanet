import xml.etree.ElementTree as ET
import os
import logging
import time
from supabase import create_client, Client
import json
from typing import List, Dict, Any
import requests
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SupabaseXMLLoader:
    def __init__(self, supabase_url: str, supabase_key: str):
        """Initialize Supabase client"""
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key

        try:
            self.supabase: Client = create_client(supabase_url, supabase_key)
            logger.info("Supabase client initialized successfully!")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise

    def test_connection(self):
        """Test Supabase connection"""
        try:
            # Try to read from a table (even if it doesn't exist, we'll get a proper response)
            result = self.supabase.table('disorders').select("*").limit(1).execute()
            logger.info("Supabase connection test successful!")
            return True
        except Exception as e:
            logger.error(f"Supabase connection test failed: {e}")
            return False

    def create_tables_via_sql(self):
        """Create tables using Supabase SQL function"""

        # First, let's create the basic tables we need
        sql_commands = [
            """
            CREATE TABLE IF NOT EXISTS disorders (
                id SERIAL PRIMARY KEY,
                orpha_code VARCHAR(10) UNIQUE NOT NULL,
                name VARCHAR(150) NOT NULL,
                expert_link TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS hpo_terms (
                id SERIAL PRIMARY KEY,
                hpo_id VARCHAR(15) UNIQUE NOT NULL,
                term VARCHAR(120) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS disorder_hpo_associations (
                id SERIAL PRIMARY KEY,
                disorder_id INTEGER REFERENCES disorders(id) ON DELETE CASCADE,
                hpo_term_id INTEGER REFERENCES hpo_terms(id) ON DELETE CASCADE,
                frequency VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(disorder_id, hpo_term_id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS prevalences (
                id SERIAL PRIMARY KEY,
                disorder_id INTEGER REFERENCES disorders(id) ON DELETE CASCADE,
                prevalence_type VARCHAR(50),
                prevalence_class VARCHAR(50),
                val_moy DECIMAL(10,6),
                geographic_area VARCHAR(100),
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_disorders_orpha_code ON disorders(orpha_code);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_hpo_terms_hpo_id ON hpo_terms(hpo_id);
            """
        ]

        logger.info("Creating database tables...")
        for i, sql in enumerate(sql_commands):
            try:
                # Use rpc to execute SQL
                result = self.supabase.rpc('exec_sql', {'sql_query': sql}).execute()
                logger.info(f"Executed SQL command {i+1}/{len(sql_commands)}")
            except Exception as e:
                logger.warning(f"SQL command {i+1} might have failed (this could be normal): {e}")

    def parse_clinical_signs_xml(self, xml_file: str):
        """Parse Clinical signs and symptoms XML"""
        logger.info(f"Parsing clinical signs XML: {xml_file}")

        if not os.path.exists(xml_file):
            logger.error(f"File not found: {xml_file}")
            return [], [], []

        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            disorders = []
            hpo_terms = []
            associations = []

            disorder_count = 0
            for disorder_elem in root.findall('.//Disorder'):
                disorder_count += 1
                if disorder_count % 1000 == 0:
                    logger.info(f"Processed {disorder_count} disorders...")

                # Extract disorder info
                disorder_id = disorder_elem.get('id')
                orpha_code_elem = disorder_elem.find('OrphaCode')
                name_elem = disorder_elem.find('Name')
                expert_link_elem = disorder_elem.find('ExpertLink')

                orpha_code = orpha_code_elem.text if orpha_code_elem is not None else None
                name = name_elem.text if name_elem is not None else None
                expert_link = expert_link_elem.text if expert_link_elem is not None else None

                if orpha_code and name:
                    disorders.append({
                        'orpha_code': orpha_code,
                        'name': name[:150],  # Truncate to fit database field
                        'expert_link': expert_link
                    })

                # Extract HPO associations
                hpo_list = disorder_elem.find('HPODisorderAssociationList')
                if hpo_list is not None:
                    for hpo_assoc in hpo_list.findall('HPODisorderAssociation'):
                        hpo_elem = hpo_assoc.find('HPO')
                        if hpo_elem is not None:
                            hpo_id_elem = hpo_elem.find('HPOId')
                            hpo_term_elem = hpo_elem.find('HPOTerm')
                            hpo_freq_elem = hpo_elem.find('HPOFrequency')

                            hpo_id = hpo_id_elem.text if hpo_id_elem is not None else None
                            hpo_term = hpo_term_elem.text if hpo_term_elem is not None else None
                            frequency = hpo_freq_elem.text if hpo_freq_elem is not None else None

                            if hpo_id and hpo_term:
                                hpo_terms.append({
                                    'hpo_id': hpo_id,
                                    'term': hpo_term[:120]
                                })

                                associations.append({
                                    'disorder_orpha_code': orpha_code,
                                    'hpo_id': hpo_id,
                                    'frequency': frequency
                                })

            logger.info(f"Parsed {len(disorders)} disorders, {len(hpo_terms)} HPO terms, {len(associations)} associations")
            return disorders, hpo_terms, associations

        except Exception as e:
            logger.error(f"Error parsing XML: {e}")
            return [], [], []

    def parse_epidemiology_xml(self, xml_file: str):
        """Parse Epidemiology XML"""
        logger.info(f"Parsing epidemiology XML: {xml_file}")

        if not os.path.exists(xml_file):
            logger.error(f"File not found: {xml_file}")
            return []

        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            prevalences = []

            for disorder_elem in root.findall('.//Disorder'):
                orpha_code_elem = disorder_elem.find('OrphaCode')
                orpha_code = orpha_code_elem.text if orpha_code_elem is not None else None

                if not orpha_code:
                    continue

                prev_list = disorder_elem.find('PrevalenceList')
                if prev_list is not None:
                    for prev_elem in prev_list.findall('Prevalence'):
                        prevalence_data = {
                            'disorder_orpha_code': orpha_code,
                            'prevalence_type': self.safe_get_text(prev_elem, 'PrevalenceType'),
                            'prevalence_class': self.safe_get_text(prev_elem, 'PrevalenceClass'),
                            'val_moy': self.safe_get_text(prev_elem, 'ValMoy'),
                            'geographic_area': self.safe_get_text(prev_elem, 'PrevalenceGeographic'),
                            'source': self.safe_get_text(prev_elem, 'Source')
                        }
                        prevalences.append(prevalence_data)

            logger.info(f"Parsed {len(prevalences)} prevalence records")
            return prevalences

        except Exception as e:
            logger.error(f"Error parsing epidemiology XML: {e}")
            return []

    def safe_get_text(self, parent, tag_name):
        """Safely get text from XML element"""
        elem = parent.find(tag_name)
        return elem.text if elem is not None else None

    def insert_disorders(self, disorders: List[Dict], batch_size: int = 100):
        """Insert disorders using Supabase API"""
        logger.info(f"Inserting {len(disorders)} disorders...")

        # Remove duplicates based on orpha_code
        unique_disorders = {}
        for disorder in disorders:
            unique_disorders[disorder['orpha_code']] = disorder

        disorders_list = list(unique_disorders.values())

        successful_inserts = 0
        for i in range(0, len(disorders_list), batch_size):
            batch = disorders_list[i:i + batch_size]
            try:
                result = self.supabase.table('disorders').upsert(batch).execute()
                successful_inserts += len(batch)
                logger.info(f"Inserted disorders batch {i//batch_size + 1}/{(len(disorders_list)-1)//batch_size + 1}")
                time.sleep(0.1)  # Small delay to avoid rate limits
            except Exception as e:
                logger.error(f"Error inserting disorders batch: {e}")
                # Try individual inserts for this batch
                for disorder in batch:
                    try:
                        self.supabase.table('disorders').upsert([disorder]).execute()
                        successful_inserts += 1
                    except Exception as single_error:
                        logger.error(f"Failed to insert disorder {disorder['orpha_code']}: {single_error}")

        logger.info(f"Successfully inserted {successful_inserts}/{len(disorders_list)} disorders")
        return successful_inserts

    def insert_hpo_terms(self, hpo_terms: List[Dict], batch_size: int = 100):
        """Insert HPO terms using Supabase API"""
        logger.info(f"Inserting {len(hpo_terms)} HPO terms...")

        # Remove duplicates based on hpo_id
        unique_hpo = {}
        for hpo in hpo_terms:
            unique_hpo[hpo['hpo_id']] = hpo

        hpo_list = list(unique_hpo.values())

        successful_inserts = 0
        for i in range(0, len(hpo_list), batch_size):
            batch = hpo_list[i:i + batch_size]
            try:
                result = self.supabase.table('hpo_terms').upsert(batch).execute()
                successful_inserts += len(batch)
                logger.info(f"Inserted HPO terms batch {i//batch_size + 1}/{(len(hpo_list)-1)//batch_size + 1}")
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error inserting HPO terms batch: {e}")
                # Try individual inserts
                for hpo in batch:
                    try:
                        self.supabase.table('hpo_terms').upsert([hpo]).execute()
                        successful_inserts += 1
                    except Exception as single_error:
                        logger.error(f"Failed to insert HPO term {hpo['hpo_id']}: {single_error}")

        logger.info(f"Successfully inserted {successful_inserts}/{len(hpo_list)} HPO terms")
        return successful_inserts

    def get_disorder_id_map(self):
        """Get mapping of orpha_code to disorder ID"""
        logger.info("Fetching disorder ID mappings...")
        try:
            result = self.supabase.table('disorders').select('id, orpha_code').execute()
            disorder_map = {row['orpha_code']: row['id'] for row in result.data}
            logger.info(f"Fetched {len(disorder_map)} disorder mappings")
            return disorder_map
        except Exception as e:
            logger.error(f"Error fetching disorder mappings: {e}")
            return {}

    def get_hpo_id_map(self):
        """Get mapping of hpo_id to internal ID"""
        logger.info("Fetching HPO ID mappings...")
        try:
            result = self.supabase.table('hpo_terms').select('id, hpo_id').execute()
            hpo_map = {row['hpo_id']: row['id'] for row in result.data}
            logger.info(f"Fetched {len(hpo_map)} HPO mappings")
            return hpo_map
        except Exception as e:
            logger.error(f"Error fetching HPO mappings: {e}")
            return {}

    def insert_hpo_associations(self, associations: List[Dict], batch_size: int = 50):
        """Insert HPO associations using Supabase API"""
        logger.info(f"Preparing to insert {len(associations)} HPO associations...")

        # Get ID mappings
        disorder_map = self.get_disorder_id_map()
        hpo_map = self.get_hpo_id_map()

        # Convert associations to use internal IDs
        valid_associations = []
        for assoc in associations:
            disorder_id = disorder_map.get(assoc['disorder_orpha_code'])
            hpo_term_id = hpo_map.get(assoc['hpo_id'])

            if disorder_id and hpo_term_id:
                valid_associations.append({
                    'disorder_id': disorder_id,
                    'hpo_term_id': hpo_term_id,
                    'frequency': assoc['frequency']
                })

        logger.info(f"Found {len(valid_associations)} valid associations to insert")

        successful_inserts = 0
        for i in range(0, len(valid_associations), batch_size):
            batch = valid_associations[i:i + batch_size]
            try:
                result = self.supabase.table('disorder_hpo_associations').upsert(batch).execute()
                successful_inserts += len(batch)
                logger.info(f"Inserted associations batch {i//batch_size + 1}/{(len(valid_associations)-1)//batch_size + 1}")
                time.sleep(0.2)  # Longer delay for complex inserts
            except Exception as e:
                logger.error(f"Error inserting associations batch: {e}")
                # Try individual inserts
                for association in batch:
                    try:
                        self.supabase.table('disorder_hpo_associations').upsert([association]).execute()
                        successful_inserts += 1
                    except Exception as single_error:
                        logger.error(f"Failed to insert association: {single_error}")

        logger.info(f"Successfully inserted {successful_inserts}/{len(valid_associations)} associations")
        return successful_inserts

    def get_stats(self):
        """Get database statistics"""
        try:
            tables = ['disorders', 'hpo_terms', 'disorder_hpo_associations', 'prevalences']
            logger.info("Database Statistics:")

            for table in tables:
                try:
                    result = self.supabase.table(table).select('*', count='exact').execute()
                    count = result.count if hasattr(result, 'count') else len(result.data)
                    logger.info(f"  {table}: {count:,} records")
                except Exception as e:
                    logger.warning(f"  {table}: Could not get count ({e})")

        except Exception as e:
            logger.error(f"Error getting statistics: {e}")

def main():
    # REPLACE THESE WITH YOUR ACTUAL SUPABASE CREDENTIALS
    SUPABASE_URL = "https://ecrcdeztnbciybqkwkpf.supabase.co"  # Your Supabase project URL
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVjcmNkZXp0bmJjaXlicWt3a3BmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ5NDIwOTQsImV4cCI6MjA3MDUxODA5NH0.TPT6CdwI3lgBeh-V_X-a8_H4m3YFK0lLg31eWM0woho"                    # Your Supabase anon key

    # These you can find in your Supabase dashboard under Settings > API

    try:
        loader = SupabaseXMLLoader(SUPABASE_URL, SUPABASE_KEY)

        # Test connection
        if not loader.test_connection():
            logger.error("Connection test failed. Please check your Supabase URL and API key.")
            return

        # Try to create tables (this might fail if tables already exist, which is fine)
        try:
            loader.create_tables_via_sql()
        except Exception as e:
            logger.warning(f"Table creation might have failed (could be normal): {e}")

        # Define XML files - UPDATE THESE PATHS
        xml_files = {
            'clinical_signs': 'file/Clinical signs and symptoms in rare diseases.xml.xml',
            'epidemiology': 'file/Epidiemology of rare diseases.xml',
        }

        all_data = {
            'disorders': [],
            'hpo_terms': [],
            'hpo_associations': [],
            'prevalences': []
        }

        # Parse clinical signs file
        if os.path.exists(xml_files['clinical_signs']):
            logger.info("Processing clinical signs file...")
            disorders, hpo_terms, associations = loader.parse_clinical_signs_xml(xml_files['clinical_signs'])
            all_data['disorders'].extend(disorders)
            all_data['hpo_terms'].extend(hpo_terms)
            all_data['hpo_associations'].extend(associations)
        else:
            logger.warning(f"Clinical signs file not found: {xml_files['clinical_signs']}")

        # Parse epidemiology file
        if os.path.exists(xml_files['epidemiology']):
            logger.info("Processing epidemiology file...")
            prevalences = loader.parse_epidemiology_xml(xml_files['epidemiology'])
            all_data['prevalences'].extend(prevalences)
        else:
            logger.warning(f"Epidemiology file not found: {xml_files['epidemiology']}")

        # Insert data step by step
        if all_data['disorders']:
            loader.insert_disorders(all_data['disorders'])

        if all_data['hpo_terms']:
            loader.insert_hpo_terms(all_data['hpo_terms'])

        if all_data['hpo_associations']:
            loader.insert_hpo_associations(all_data['hpo_associations'])

        # Get final statistics
        loader.get_stats()

        logger.info("Data loading completed successfully!")

    except Exception as e:
        logger.error(f"Script failed: {e}")
        raise

if __name__ == "__main__":
    main()
