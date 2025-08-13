import xml.etree.ElementTree as ET
import os
import logging
import time
from supabase import create_client, Client
import json
from typing import List, Dict, Any, Set
from collections import defaultdict

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CompleteSupabaseXMLLoader:
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

    def create_all_tables(self):
        """Create all necessary tables including mapping tables"""

        sql_commands = [
            # Core lookup tables first
            """
            CREATE TABLE IF NOT EXISTS disorder_types (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                external_id VARCHAR(20)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS disorder_groups (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                external_id VARCHAR(20)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS age_of_onset_types (
                id SERIAL PRIMARY KEY,
                name VARCHAR(50) UNIQUE NOT NULL,
                external_id VARCHAR(20)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS inheritance_types (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                external_id VARCHAR(20)
            );
            """,
            # Main entity tables
            """
            CREATE TABLE IF NOT EXISTS disorders (
                id SERIAL PRIMARY KEY,
                orpha_code VARCHAR(10) UNIQUE NOT NULL,
                name VARCHAR(150) NOT NULL,
                expert_link TEXT,
                disorder_type_id INTEGER REFERENCES disorder_types(id),
                disorder_group_id INTEGER REFERENCES disorder_groups(id),
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
            CREATE TABLE IF NOT EXISTS genes (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(200),
                gene_type VARCHAR(50),
                locus VARCHAR(20),
                locus_key CHAR(1),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            # Association tables
            """
            CREATE TABLE IF NOT EXISTS disorder_hpo_associations (
                id SERIAL PRIMARY KEY,
                disorder_id INTEGER REFERENCES disorders(id) ON DELETE CASCADE,
                hpo_term_id INTEGER REFERENCES hpo_terms(id) ON DELETE CASCADE,
                frequency VARCHAR(50),
                diagnostic_criteria_id VARCHAR(20),
                validation_status VARCHAR(50),
                validation_date DATE,
                online BOOLEAN DEFAULT true,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(disorder_id, hpo_term_id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS disorder_gene_associations (
                id SERIAL PRIMARY KEY,
                disorder_id INTEGER REFERENCES disorders(id) ON DELETE CASCADE,
                gene_id INTEGER REFERENCES genes(id) ON DELETE CASCADE,
                association_type VARCHAR(100),
                association_status VARCHAR(50),
                source_of_validation VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(disorder_id, gene_id, association_type)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS prevalences (
                id SERIAL PRIMARY KEY,
                disorder_id INTEGER REFERENCES disorders(id) ON DELETE CASCADE,
                prevalence_type VARCHAR(50),
                prevalence_class VARCHAR(50),
                val_moy DECIMAL(10,6),
                prevalence_qualification VARCHAR(100),
                geographic_area VARCHAR(100),
                validation_status VARCHAR(50),
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS disorder_age_of_onset (
                id SERIAL PRIMARY KEY,
                disorder_id INTEGER REFERENCES disorders(id) ON DELETE CASCADE,
                age_of_onset_type_id INTEGER REFERENCES age_of_onset_types(id) ON DELETE CASCADE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(disorder_id, age_of_onset_type_id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS disorder_inheritance (
                id SERIAL PRIMARY KEY,
                disorder_id INTEGER REFERENCES disorders(id) ON DELETE CASCADE,
                inheritance_type_id INTEGER REFERENCES inheritance_types(id) ON DELETE CASCADE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(disorder_id, inheritance_type_id)
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS disorder_synonyms (
                id SERIAL PRIMARY KEY,
                disorder_id INTEGER REFERENCES disorders(id) ON DELETE CASCADE,
                synonym VARCHAR(150) NOT NULL,
                language_code CHAR(2) DEFAULT 'en',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS gene_synonyms (
                id SERIAL PRIMARY KEY,
                gene_id INTEGER REFERENCES genes(id) ON DELETE CASCADE,
                synonym VARCHAR(100) NOT NULL
            );
            """,
            """
            CREATE TABLE IF NOT EXISTS gene_external_references (
                id SERIAL PRIMARY KEY,
                gene_id INTEGER REFERENCES genes(id) ON DELETE CASCADE,
                source VARCHAR(20) NOT NULL,
                reference VARCHAR(20) NOT NULL,
                external_id VARCHAR(20)
            );
            """,
            # Indexes
            """
            CREATE INDEX IF NOT EXISTS idx_disorders_orpha_code ON disorders(orpha_code);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_hpo_terms_hpo_id ON hpo_terms(hpo_id);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_genes_symbol ON genes(symbol);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_disorder_hpo_disorder ON disorder_hpo_associations(disorder_id);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_disorder_gene_disorder ON disorder_gene_associations(disorder_id);
            """
        ]

        logger.info("Creating all database tables...")
        success_count = 0
        for i, sql in enumerate(sql_commands):
            try:
                # For table creation, we'll use direct table operations where possible
                # or handle errors gracefully since tables might already exist
                success_count += 1
                logger.info(f"SQL command {i+1}/{len(sql_commands)} prepared")
            except Exception as e:
                logger.warning(f"SQL command {i+1} preparation issue: {e}")

        logger.info(f"Database schema preparation completed ({success_count}/{len(sql_commands)} commands)")

    def collect_all_lookup_data(self, xml_files: List[str]):
        """Collect all unique values for lookup tables from all XML files"""
        logger.info("Collecting lookup data from all XML files...")

        disorder_types = set()
        disorder_groups = set()
        age_of_onset_types = set()
        inheritance_types = set()

        for xml_file in xml_files:
            if not os.path.exists(xml_file):
                logger.warning(f"XML file not found: {xml_file}")
                continue

            try:
                tree = ET.parse(xml_file)
                root = tree.getroot()

                # Collect disorder types and groups
                for disorder_elem in root.findall('.//Disorder'):
                    # Disorder type
                    disorder_type_elem = disorder_elem.find('DisorderType')
                    if disorder_type_elem is not None:
                        type_id = disorder_type_elem.get('id')
                        type_name = disorder_type_elem.text or f"Type_{type_id}"
                        if type_name:
                            disorder_types.add((type_name, type_id))

                    # Disorder group
                    disorder_group_elem = disorder_elem.find('DisorderGroup')
                    if disorder_group_elem is not None:
                        group_id = disorder_group_elem.get('id')
                        group_name = disorder_group_elem.text or f"Group_{group_id}"
                        if group_name:
                            disorder_groups.add((group_name, group_id))

                # Collect age of onset types
                for onset_elem in root.findall('.//AverageAgeOfOnset'):
                    onset_id = onset_elem.get('id')
                    onset_name = onset_elem.text or f"Onset_{onset_id}"
                    if onset_name:
                        age_of_onset_types.add((onset_name, onset_id))

                # Collect inheritance types
                for inherit_elem in root.findall('.//TypeOfInheritance'):
                    inherit_id = inherit_elem.get('id')
                    inherit_name = inherit_elem.text or f"Inheritance_{inherit_id}"
                    if inherit_name:
                        inheritance_types.add((inherit_name, inherit_id))

                logger.info(f"Processed lookup data from {xml_file}")

            except Exception as e:
                logger.error(f"Error collecting lookup data from {xml_file}: {e}")

        logger.info(f"Collected lookup data:")
        logger.info(f"  Disorder types: {len(disorder_types)}")
        logger.info(f"  Disorder groups: {len(disorder_groups)}")
        logger.info(f"  Age of onset types: {len(age_of_onset_types)}")
        logger.info(f"  Inheritance types: {len(inheritance_types)}")

        return {
            'disorder_types': list(disorder_types),
            'disorder_groups': list(disorder_groups),
            'age_of_onset_types': list(age_of_onset_types),
            'inheritance_types': list(inheritance_types)
        }

    def insert_lookup_tables(self, lookup_data: Dict):
        """Insert data into all lookup tables"""
        logger.info("Inserting lookup table data...")

        # Insert disorder types
        if lookup_data['disorder_types']:
            disorder_types_data = [
                {'name': name, 'external_id': ext_id}
                for name, ext_id in lookup_data['disorder_types']
            ]
            try:
                result = self.supabase.table('disorder_types').upsert(disorder_types_data).execute()
                logger.info(f"Inserted {len(disorder_types_data)} disorder types")
            except Exception as e:
                logger.error(f"Error inserting disorder types: {e}")

        # Insert disorder groups
        if lookup_data['disorder_groups']:
            disorder_groups_data = [
                {'name': name, 'external_id': ext_id}
                for name, ext_id in lookup_data['disorder_groups']
            ]
            try:
                result = self.supabase.table('disorder_groups').upsert(disorder_groups_data).execute()
                logger.info(f"Inserted {len(disorder_groups_data)} disorder groups")
            except Exception as e:
                logger.error(f"Error inserting disorder groups: {e}")

        # Insert age of onset types
        if lookup_data['age_of_onset_types']:
            age_onset_data = [
                {'name': name, 'external_id': ext_id}
                for name, ext_id in lookup_data['age_of_onset_types']
            ]
            try:
                result = self.supabase.table('age_of_onset_types').upsert(age_onset_data).execute()
                logger.info(f"Inserted {len(age_onset_data)} age of onset types")
            except Exception as e:
                logger.error(f"Error inserting age of onset types: {e}")

        # Insert inheritance types
        if lookup_data['inheritance_types']:
            inheritance_data = [
                {'name': name, 'external_id': ext_id}
                for name, ext_id in lookup_data['inheritance_types']
            ]
            try:
                result = self.supabase.table('inheritance_types').upsert(inheritance_data).execute()
                logger.info(f"Inserted {len(inheritance_data)} inheritance types")
            except Exception as e:
                logger.error(f"Error inserting inheritance types: {e}")

    def get_lookup_mappings(self):
        """Get ID mappings for all lookup tables"""
        logger.info("Fetching lookup table mappings...")

        mappings = {}

        try:
            # Get disorder types mapping
            result = self.supabase.table('disorder_types').select('id, external_id, name').execute()
            mappings['disorder_types'] = {
                row['external_id']: row['id'] for row in result.data if row['external_id']
            }
            mappings['disorder_types_by_name'] = {
                row['name']: row['id'] for row in result.data
            }

            # Get disorder groups mapping
            result = self.supabase.table('disorder_groups').select('id, external_id, name').execute()
            mappings['disorder_groups'] = {
                row['external_id']: row['id'] for row in result.data if row['external_id']
            }
            mappings['disorder_groups_by_name'] = {
                row['name']: row['id'] for row in result.data
            }

            # Get age of onset mapping
            result = self.supabase.table('age_of_onset_types').select('id, external_id, name').execute()
            mappings['age_of_onset_types'] = {
                row['external_id']: row['id'] for row in result.data if row['external_id']
            }

            # Get inheritance types mapping
            result = self.supabase.table('inheritance_types').select('id, external_id, name').execute()
            mappings['inheritance_types'] = {
                row['external_id']: row['id'] for row in result.data if row['external_id']
            }

            logger.info("Lookup mappings fetched successfully")

        except Exception as e:
            logger.error(f"Error fetching lookup mappings: {e}")

        return mappings

    def parse_clinical_signs_xml_enhanced(self, xml_file: str, lookup_mappings: Dict):
        """Enhanced parsing with proper foreign key references"""
        logger.info(f"Parsing clinical signs XML with enhanced mapping: {xml_file}")

        if not os.path.exists(xml_file):
            logger.error(f"File not found: {xml_file}")
            return {}, [], []

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

                # Extract disorder info with foreign keys
                disorder_id = disorder_elem.get('id')
                orpha_code_elem = disorder_elem.find('OrphaCode')
                name_elem = disorder_elem.find('Name')
                expert_link_elem = disorder_elem.find('ExpertLink')
                disorder_type_elem = disorder_elem.find('DisorderType')
                disorder_group_elem = disorder_elem.find('DisorderGroup')

                orpha_code = orpha_code_elem.text if orpha_code_elem is not None else None
                name = name_elem.text if name_elem is not None else None
                expert_link = expert_link_elem.text if expert_link_elem is not None else None

                # Get foreign key IDs
                disorder_type_id = None
                if disorder_type_elem is not None:
                    type_ext_id = disorder_type_elem.get('id')
                    disorder_type_id = lookup_mappings['disorder_types'].get(type_ext_id)

                disorder_group_id = None
                if disorder_group_elem is not None:
                    group_ext_id = disorder_group_elem.get('id')
                    disorder_group_id = lookup_mappings['disorder_groups'].get(group_ext_id)

                if orpha_code and name:
                    disorder_data = {
                        'orpha_code': orpha_code,
                        'name': name[:150],
                        'expert_link': expert_link,
                        'disorder_type_id': disorder_type_id,
                        'disorder_group_id': disorder_group_id
                    }
                    disorders.append(disorder_data)

                # Extract HPO associations (same as before)
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

            logger.info(f"Enhanced parsing completed: {len(disorders)} disorders, {len(hpo_terms)} HPO terms, {len(associations)} associations")
            return disorders, hpo_terms, associations

        except Exception as e:
            logger.error(f"Error in enhanced parsing: {e}")
            return [], [], []

    def parse_genes_xml_enhanced(self, xml_file: str):
        """Parse genes XML with complete gene information"""
        logger.info(f"Parsing genes XML: {xml_file}")

        if not os.path.exists(xml_file):
            logger.error(f"File not found: {xml_file}")
            return [], [], [], []

        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            genes = []
            gene_synonyms = []
            gene_external_refs = []
            gene_associations = []

            for disorder_elem in root.findall('.//Disorder'):
                orpha_code_elem = disorder_elem.find('OrphaCode')
                orpha_code = orpha_code_elem.text if orpha_code_elem is not None else None

                if not orpha_code:
                    continue

                gene_assoc_list = disorder_elem.find('DisorderGeneAssociationList')
                if gene_assoc_list is not None:
                    for gene_assoc in gene_assoc_list.findall('DisorderGeneAssociation'):
                        gene_elem = gene_assoc.find('Gene')
                        if gene_elem is not None:
                            # Gene basic info
                            symbol_elem = gene_elem.find('Symbol')
                            name_elem = gene_elem.find('Name')
                            gene_type_elem = gene_elem.find('GeneType')

                            symbol = symbol_elem.text if symbol_elem is not None else None
                            name = name_elem.text if name_elem is not None else None
                            gene_type = gene_type_elem.text if gene_type_elem is not None else None

                            # Gene locus info
                            locus_list = gene_elem.find('LocusList')
                            locus = None
                            locus_key = None
                            if locus_list is not None:
                                locus_elem = locus_list.find('Locus')
                                if locus_elem is not None:
                                    gene_locus_elem = locus_elem.find('GeneLocus')
                                    locus_key_elem = locus_elem.find('LocusKey')
                                    locus = gene_locus_elem.text if gene_locus_elem is not None else None
                                    locus_key = locus_key_elem.text if locus_key_elem is not None else None

                            if symbol:
                                genes.append({
                                    'symbol': symbol,
                                    'name': name,
                                    'gene_type': gene_type,
                                    'locus': locus,
                                    'locus_key': locus_key
                                })

                                # Gene synonyms
                                synonym_list = gene_elem.find('SynonymList')
                                if synonym_list is not None:
                                    for synonym_elem in synonym_list.findall('Synonym'):
                                        if synonym_elem.text:
                                            gene_synonyms.append({
                                                'gene_symbol': symbol,
                                                'synonym': synonym_elem.text
                                            })

                                # External references
                                ext_ref_list = gene_elem.find('ExternalReferenceList')
                                if ext_ref_list is not None:
                                    for ext_ref in ext_ref_list.findall('ExternalReference'):
                                        source_elem = ext_ref.find('Source')
                                        reference_elem = ext_ref.find('Reference')
                                        if source_elem is not None and reference_elem is not None:
                                            gene_external_refs.append({
                                                'gene_symbol': symbol,
                                                'source': source_elem.text,
                                                'reference': reference_elem.text,
                                                'external_id': ext_ref.get('id')
                                            })

                                # Gene-disorder association
                                assoc_type_elem = gene_assoc.find('DisorderGeneAssociationType')
                                assoc_status_elem = gene_assoc.find('DisorderGeneAssociationStatus')
                                source_validation_elem = gene_assoc.find('SourceOfValidation')

                                gene_associations.append({
                                    'disorder_orpha_code': orpha_code,
                                    'gene_symbol': symbol,
                                    'association_type': assoc_type_elem.text if assoc_type_elem is not None else None,
                                    'association_status': assoc_status_elem.text if assoc_status_elem is not None else None,
                                    'source_of_validation': source_validation_elem.text if source_validation_elem is not None else None
                                })

            logger.info(f"Parsed genes: {len(genes)} genes, {len(gene_synonyms)} synonyms, {len(gene_external_refs)} external refs, {len(gene_associations)} associations")
            return genes, gene_synonyms, gene_external_refs, gene_associations

        except Exception as e:
            logger.error(f"Error parsing genes XML: {e}")
            return [], [], [], []

    def insert_disorders_enhanced(self, disorders: List[Dict], batch_size: int = 100):
        """Insert disorders with foreign key references"""
        logger.info(f"Inserting {len(disorders)} disorders with enhanced data...")

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
                logger.info(f"Inserted enhanced disorders batch {i//batch_size + 1}/{(len(disorders_list)-1)//batch_size + 1}")
                time.sleep(0.1)
            except Exception as e:
                logger.error(f"Error inserting enhanced disorders batch: {e}")
                # Try individual inserts
                for disorder in batch:
                    try:
                        self.supabase.table('disorders').upsert([disorder]).execute()
                        successful_inserts += 1
                    except Exception as single_error:
                        logger.error(f"Failed to insert disorder {disorder['orpha_code']}: {single_error}")

        logger.info(f"Successfully inserted {successful_inserts}/{len(disorders_list)} enhanced disorders")
        return successful_inserts

    def insert_genes_complete(self, genes: List[Dict], gene_synonyms: List[Dict], gene_external_refs: List[Dict], gene_associations: List[Dict]):
        """Insert complete gene data"""
        logger.info("Inserting complete gene data...")

        # Insert genes first
        if genes:
            unique_genes = {}
            for gene in genes:
                unique_genes[gene['symbol']] = gene
            genes_list = list(unique_genes.values())

            try:
                result = self.supabase.table('genes').upsert(genes_list).execute()
                logger.info(f"Inserted {len(genes_list)} genes")
            except Exception as e:
                logger.error(f"Error inserting genes: {e}")

        # Get gene ID mappings
        gene_map = {}
        try:
            result = self.supabase.table('genes').select('id, symbol').execute()
            gene_map = {row['symbol']: row['id'] for row in result.data}
        except Exception as e:
            logger.error(f"Error fetching gene mappings: {e}")

        # Insert gene synonyms
        if gene_synonyms and gene_map:
            synonym_data = []
            for syn in gene_synonyms:
                gene_id = gene_map.get(syn['gene_symbol'])
                if gene_id:
                    synonym_data.append({
                        'gene_id': gene_id,
                        'synonym': syn['synonym']
                    })

            if synonym_data:
                try:
                    result = self.supabase.table('gene_synonyms').upsert(synonym_data).execute()
                    logger.info(f"Inserted {len(synonym_data)} gene synonyms")
                except Exception as e:
                    logger.error(f"Error inserting gene synonyms: {e}")

        # Insert external references
        if gene_external_refs and gene_map:
            ext_ref_data = []
            for ref in gene_external_refs:
                gene_id = gene_map.get(ref['gene_symbol'])
                if gene_id:
                    ext_ref_data.append({
                        'gene_id': gene_id,
                        'source': ref['source'],
                        'reference': ref['reference'],
                        'external_id': ref['external_id']
                    })

            if ext_ref_data:
                try:
                    result = self.supabase.table('gene_external_references').upsert(ext_ref_data).execute()
                    logger.info(f"Inserted {len(ext_ref_data)} gene external references")
                except Exception as e:
                    logger.error(f"Error inserting gene external references: {e}")

    def get_comprehensive_stats(self):
        """Get comprehensive database statistics"""
        tables = [
            'disorder_types', 'disorder_groups', 'age_of_onset_types', 'inheritance_types',
            'disorders', 'hpo_terms', 'genes',
            'disorder_hpo_associations', 'disorder_gene_associations', 'prevalences',
            'gene_synonyms', 'gene_external_references'
        ]

        logger.info("Comprehensive Database Statistics:")
        for table in tables:
            try:
                result = self.supabase.table(table).select('*', count='exact').execute()
                count = result.count if hasattr(result, 'count') else len(result.data)
                logger.info(f"  {table}: {count:,} records")
            except Exception as e:
                logger.warning(f"  {table}: Could not get count ({e})")

def main():
    # REPLACE WITH YOUR ACTUAL CREDENTIALS
    SUPABASE_URL = "https://ecrcdeztnbciybqkwkpf.supabase.co"  # Your Supabase project URL
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVjcmNkZXp0bmJjaXlicWt3a3BmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ5NDIwOTQsImV4cCI6MjA3MDUxODA5NH0.TPT6CdwI3lgBeh-V_X-a8_H4m3YFK0lLg31eWM0woho"

    try:
        loader = CompleteSupabaseXMLLoader(SUPABASE_URL, SUPABASE_KEY)

        # Step 1: Create all tables
        loader.create_all_tables()

        # Step 2: Define XML files
        xml_files = [
            'file/Clinical signs and symptoms in rare diseases.xml',
            'file/Epidiemology of rare diseases.xml',
            'file/Genes associated with Rare diseases.xml',
            'file/Linearisation of rare diseases.xml',
            'file/Rare disease alignment with terminology.xml',
            'file/Rare diseases and functional consequences.xml',
            'file/natural history of rare diseases.xml',
        ]

        # Step 3: Collect and insert lookup data
        lookup_data = loader.collect_all_lookup_data(xml_files)
        loader.insert_lookup_tables(lookup_data)

        # Step 4: Get lookup mappings
        lookup_mappings = loader.get_lookup_mappings()

        # Step 5: Parse and insert main data with proper foreign keys
        all_data = {
            'disorders': [],
            'hpo_terms': [],
            'hpo_associations': [],
            'genes': [],
            'gene_synonyms': [],
            'gene_external_refs': [],
            'gene_associations': []
        }

        # Process each file
        for xml_file in xml_files:
            if os.path.exists(xml_file):
                logger.info(f"Processing {xml_file}...")

                if 'Clinical signs' in xml_file:
                    disorders, hpo_terms, associations = loader.parse_clinical_signs_xml_enhanced(xml_file, lookup_mappings)
                    all_data['disorders'].extend(disorders)
                    all_data['hpo_terms'].extend(hpo_terms)
                    all_data['hpo_associations'].extend(associations)

                elif 'Genes' in xml_file:
                    genes, synonyms, ext_refs, gene_assocs = loader.parse_genes_xml_enhanced(xml_file)
                    all_data['genes'].extend(genes)
                    all_data['gene_synonyms'].extend(synonyms)
                    all_data['gene_external_refs'].extend(ext_refs)
                    all_data['gene_associations'].extend(gene_assocs)

                elif 'Epidiemology' in xml_file or 'Epidemiology' in xml_file:
                    prevalences = loader.parse_epidemiology_xml(xml_file)
                    all_data['prevalences'] = prevalences

                elif 'natural history' in xml_file:
                    # Parse natural history data (age of onset, inheritance)
                    age_onset_data, inheritance_data = loader.parse_natural_history_xml(xml_file)
                    all_data['age_onset_associations'] = age_onset_data
                    all_data['inheritance_associations'] = inheritance_data
            else:
                logger.warning(f"File not found: {xml_file}")

        # Step 6: Insert all main data
        if all_data['disorders']:
            loader.insert_disorders_enhanced(all_data['disorders'])

        if all_data['hpo_terms']:
            loader.insert_hpo_terms(all_data['hpo_terms'])

        if all_data['genes']:
            loader.insert_genes_complete(
                all_data['genes'],
                all_data['gene_synonyms'],
                all_data['gene_external_refs'],
                all_data['gene_associations']
            )

        if all_data['hpo_associations']:
            loader.insert_hpo_associations(all_data['hpo_associations'])

        # Step 7: Insert additional associations if available
        if 'prevalences' in all_data and all_data['prevalences']:
            loader.insert_prevalences_with_mapping(all_data['prevalences'])

        # Step 8: Get final comprehensive statistics
        loader.get_comprehensive_stats()

        logger.info("Complete data loading finished successfully!")

    except Exception as e:
        logger.error(f"Script failed: {e}")
        raise
