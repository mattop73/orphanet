import xml.etree.ElementTree as ET
import os
import psycopg2
from psycopg2.extras import execute_batch
import logging
import time
from urllib.parse import quote_plus

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class XMLToPostgresLoader:
    def __init__(self, connection_string):
        """Initialize connection with retry logic"""
        self.connection_string = connection_string
        self.conn = None
        self.cursor = None
        self.connect_with_retry()

    def connect_with_retry(self, max_retries=3, delay=5):
        """Connect to database with retry logic"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to connect to database (attempt {attempt + 1}/{max_retries})")
                self.conn = psycopg2.connect(
                    self.connection_string,
                    connect_timeout=30,  # 30 second timeout
                    keepalives=1,
                    keepalives_idle=30,
                    keepalives_interval=10,
                    keepalives_count=5
                )
                self.conn.autocommit = False
                self.cursor = self.conn.cursor()
                logger.info("Successfully connected to database!")
                return
            except psycopg2.OperationalError as e:
                logger.error(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
                else:
                    logger.error("All connection attempts failed!")
                    raise

    def test_connection(self):
        """Test database connection"""
        try:
            self.cursor.execute("SELECT version();")
            result = self.cursor.fetchone()
            logger.info(f"Database version: {result[0]}")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def parse_clinical_signs_xml(self, xml_file):
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

                if orpha_code and name:  # Only add if we have essential data
                    disorders.append({
                        'orpha_code': orpha_code,
                        'name': name[:150],  # Truncate to fit database field
                        'expert_link': expert_link,
                        'external_id': disorder_id
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
                                    'term': hpo_term[:120]  # Truncate to fit database field
                                })

                                associations.append({
                                    'disorder_orpha_code': orpha_code,
                                    'hpo_id': hpo_id,
                                    'frequency': frequency
                                })

            logger.info(f"Parsed {len(disorders)} disorders, {len(hpo_terms)} HPO terms, {len(associations)} associations")
            return disorders, hpo_terms, associations

        except ET.ParseError as e:
            logger.error(f"XML parsing error: {e}")
            return [], [], []
        except Exception as e:
            logger.error(f"Unexpected error parsing XML: {e}")
            return [], [], []

    def parse_epidemiology_xml(self, xml_file):
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

    def insert_data_batch(self, data_dict, batch_size=1000):
        """Insert all data into database with batch processing"""
        try:
            logger.info("Starting data insertion...")

            # Insert disorders first
            if 'disorders' in data_dict and data_dict['disorders']:
                logger.info(f"Inserting {len(data_dict['disorders'])} disorders...")
                disorders_sql = """
                INSERT INTO disorders (orpha_code, name, expert_link)
                VALUES (%s, %s, %s)
                ON CONFLICT (orpha_code) DO UPDATE SET
                name = EXCLUDED.name, expert_link = EXCLUDED.expert_link
                """

                # Process in batches
                disorders = data_dict['disorders']
                for i in range(0, len(disorders), batch_size):
                    batch = disorders[i:i + batch_size]
                    disorder_data = [(d['orpha_code'], d['name'], d['expert_link']) for d in batch]
                    execute_batch(self.cursor, disorders_sql, disorder_data)
                    logger.info(f"Inserted disorders batch {i//batch_size + 1}/{(len(disorders)-1)//batch_size + 1}")

                self.conn.commit()
                logger.info("Disorders inserted successfully!")

            # Insert HPO terms
            if 'hpo_terms' in data_dict and data_dict['hpo_terms']:
                logger.info(f"Inserting {len(data_dict['hpo_terms'])} HPO terms...")

                # Remove duplicates
                unique_hpo = {}
                for hpo in data_dict['hpo_terms']:
                    unique_hpo[hpo['hpo_id']] = hpo

                hpo_sql = """
                INSERT INTO hpo_terms (hpo_id, term)
                VALUES (%s, %s)
                ON CONFLICT (hpo_id) DO UPDATE SET term = EXCLUDED.term
                """

                hpo_list = list(unique_hpo.values())
                for i in range(0, len(hpo_list), batch_size):
                    batch = hpo_list[i:i + batch_size]
                    hpo_data = [(h['hpo_id'], h['term']) for h in batch]
                    execute_batch(self.cursor, hpo_sql, hpo_data)
                    logger.info(f"Inserted HPO terms batch {i//batch_size + 1}/{(len(hpo_list)-1)//batch_size + 1}")

                self.conn.commit()
                logger.info("HPO terms inserted successfully!")

            # Insert HPO associations
            if 'hpo_associations' in data_dict and data_dict['hpo_associations']:
                logger.info(f"Inserting {len(data_dict['hpo_associations'])} HPO associations...")

                hpo_assoc_sql = """
                INSERT INTO disorder_hpo_associations (disorder_id, hpo_term_id, frequency)
                SELECT d.id, h.id, %s
                FROM disorders d, hpo_terms h
                WHERE d.orpha_code = %s AND h.hpo_id = %s
                ON CONFLICT (disorder_id, hpo_term_id) DO UPDATE SET frequency = EXCLUDED.frequency
                """

                associations = data_dict['hpo_associations']
                for i in range(0, len(associations), batch_size):
                    batch = associations[i:i + batch_size]
                    hpo_assoc_data = [(a['frequency'], a['disorder_orpha_code'], a['hpo_id']) for a in batch]
                    execute_batch(self.cursor, hpo_assoc_sql, hpo_assoc_data)
                    logger.info(f"Inserted associations batch {i//batch_size + 1}/{(len(associations)-1)//batch_size + 1}")

                self.conn.commit()
                logger.info("HPO associations inserted successfully!")

            # Insert prevalences
            if 'prevalences' in data_dict and data_dict['prevalences']:
                logger.info(f"Inserting {len(data_dict['prevalences'])} prevalence records...")

                prev_sql = """
                INSERT INTO prevalences (disorder_id, prevalence_type, prevalence_class, val_moy, geographic_area, source)
                SELECT d.id, %s, %s, %s, %s, %s
                FROM disorders d
                WHERE d.orpha_code = %s
                """

                prevalences = data_dict['prevalences']
                for i in range(0, len(prevalences), batch_size):
                    batch = prevalences[i:i + batch_size]
                    prev_data = [(p['prevalence_type'], p['prevalence_class'], p['val_moy'],
                                 p['geographic_area'], p['source'], p['disorder_orpha_code']) for p in batch]
                    execute_batch(self.cursor, prev_sql, prev_data)
                    logger.info(f"Inserted prevalences batch {i//batch_size + 1}/{(len(prevalences)-1)//batch_size + 1}")

                self.conn.commit()
                logger.info("Prevalences inserted successfully!")

            logger.info("All data inserted successfully!")

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error inserting data: {e}")
            raise

    def get_stats(self):
        """Get database statistics"""
        try:
            stats_sql = """
            SELECT 'disorders' as table_name, COUNT(*) as count FROM disorders
            UNION ALL
            SELECT 'hpo_terms', COUNT(*) FROM hpo_terms
            UNION ALL
            SELECT 'disorder_hpo_associations', COUNT(*) FROM disorder_hpo_associations
            UNION ALL
            SELECT 'prevalences', COUNT(*) FROM prevalences
            ORDER BY table_name;
            """

            self.cursor.execute(stats_sql)
            results = self.cursor.fetchall()

            logger.info("Database Statistics:")
            for table_name, count in results:
                logger.info(f"  {table_name}: {count:,} records")

        except Exception as e:
            logger.error(f"Error getting statistics: {e}")

    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("Database connection closed")

def main():
    # IMPORTANT: Replace these with your actual Supabase credentials
    # You can find these in your Supabase project dashboard under Settings > Database
    SUPABASE_HOST = "ecrcdeztnbciybqkwkpf.supabase.co"  # Replace with your project reference
    SUPABASE_PASSWORD = "N^o!VQNJW44NPyF*zA$j"    # Replace with your database password

    # URL encode the password to handle special characters
    encoded_password = quote_plus(SUPABASE_PASSWORD)

    # Build connection string
    conn_string = f"postgresql://postgres:{encoded_password}@{SUPABASE_HOST}:5432/postgres"

    # For testing, you can also try with sslmode parameter
    # conn_string = f"postgresql://postgres:{encoded_password}@{SUPABASE_HOST}:5432/postgres?sslmode=require"

    try:
        loader = XMLToPostgresLoader(conn_string)

        # Test connection
        if not loader.test_connection():
            logger.error("Connection test failed. Please check your credentials and network.")
            return

        # Define XML files - UPDATE THESE PATHS TO MATCH YOUR FILES
        xml_files = {
            'clinical_signs': 'file/Clinical signs and symptoms in rare diseases.xml.xml',
            'epidemiology': 'file/Epidiemology of rare diseases.xml',
            # Add other files as needed...
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

        # Insert all data
        if any(all_data.values()):
            loader.insert_data_batch(all_data)
            loader.get_stats()
        else:
            logger.warning("No data to insert!")

    except Exception as e:
        logger.error(f"Script failed: {e}")
        raise
    finally:
        if 'loader' in locals():
            loader.close()

if __name__ == "__main__":
    main()
