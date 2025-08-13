#!/usr/bin/env python3
"""
Orphanet XML Files to Supabase Database Loader
Parses complete Orphanet XML files and loads data into Supabase database using the anonymous key

This version handles both complete XML files and truncated SM files (head -500 extracts)
"""

import xml.etree.ElementTree as ET
import os
import sys
import re
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union
import logging
from dataclasses import dataclass
import argparse
import json
from pathlib import Path

# Required packages (install with: pip install supabase python-dotenv tqdm)
from supabase import create_client, Client
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class SupabaseConfig:
    """Supabase configuration using anonymous key"""
    supabase_url: str
    supabase_key: str  # Anonymous key for client operations


class OrphanetXMLLoader:
    """Main class for loading Orphanet XML files to Supabase"""
    
    def __init__(self, config: SupabaseConfig):
        self.config = config
        self.supabase: Optional[Client] = None
        self.disorder_cache = {}  # Cache for disorder UUID lookups
        self.gene_cache = {}  # Cache for gene UUID lookups
        self.hpo_cache = {}  # Cache for HPO term UUID lookups
        self.disability_cache = {}  # Cache for disability UUID lookups
        
    def connect_supabase(self) -> bool:
        """Connect to Supabase using anonymous key"""
        try:
            self.supabase = create_client(self.config.supabase_url, self.config.supabase_key)
            # Test connection
            result = self.supabase.table('disorders').select('id').limit(1).execute()
            logger.info("Connected to Supabase successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            return False
    
    def fix_truncated_xml(self, xml_file: str) -> str:
        """Fix truncated XML files (head -500 extracts) by adding proper closing tags"""
        try:
            with open(xml_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with ISO-8859-1 encoding if UTF-8 fails
            with open(xml_file, 'r', encoding='iso-8859-1') as f:
                content = f.read()
        
        # If the file is already complete XML, return as is
        if content.strip().endswith('</JDBOR>'):
            return content
        
        # Track open tags using a more robust approach
        tag_stack = []
        
        # Find all tags in the content
        all_tags = re.findall(r'<[^>]+>', content)
        
        for tag_match in all_tags:
            tag = tag_match.strip('<>')
            
            # Skip XML declarations, comments, and CDATA
            if tag.startswith('?') or tag.startswith('!'):
                continue
            
            # Handle closing tags
            if tag.startswith('/'):
                tag_name = tag[1:]
                # Remove from stack if it matches
                if tag_stack and tag_stack[-1] == tag_name:
                    tag_stack.pop()
                continue
            
            # Handle self-closing tags
            if tag.endswith('/'):
                continue
            
            # Extract tag name (everything before first space or attribute)
            tag_name = tag.split()[0] if ' ' in tag else tag
            tag_stack.append(tag_name)
        
        # Add missing closing tags in reverse order
        fixed_content = content.rstrip()
        
        # Close any incomplete tags that might be cut off in the middle
        if not fixed_content.endswith('>'):
            # Find the last complete tag
            last_tag_start = fixed_content.rfind('<')
            if last_tag_start != -1:
                # Remove the incomplete tag
                fixed_content = fixed_content[:last_tag_start].rstrip()
        
        # Add missing closing tags
        while tag_stack:
            tag = tag_stack.pop()
            fixed_content += f"\n</{tag}>"
        
        return fixed_content
    
    def parse_xml(self, xml_file: str) -> ET.Element:
        """Parse XML file and return root element, handling truncated files"""
        try:
            # First try to parse as-is
            tree = ET.parse(xml_file)
            return tree.getroot()
        except ET.ParseError as e:
            logger.warning(f"XML parse error for {xml_file}: {e}. Attempting to fix truncated XML...")
            try:
                # Fix truncated XML and parse from string
                fixed_content = self.fix_truncated_xml(xml_file)
                root = ET.fromstring(fixed_content)
                logger.info(f"Successfully fixed and parsed truncated XML: {xml_file}")
                return root
            except Exception as fix_error:
                logger.error(f"Failed to fix and parse {xml_file}: {fix_error}")
                raise
        except Exception as e:
            logger.error(f"Failed to parse {xml_file}: {e}")
            raise
    
    def get_or_create_disorder(self, disorder_elem: ET.Element) -> Optional[str]:
        """Get or create disorder and return UUID"""
        orpha_code = disorder_elem.findtext('.//OrphaCode', '')
        
        if orpha_code in self.disorder_cache:
            return self.disorder_cache[orpha_code]
        
        disorder_data = {
            'disorder_id': int(disorder_elem.get('id', 0)),
            'orpha_code': orpha_code,
            'name': disorder_elem.findtext('.//Name[@lang="en"]', ''),
            'disorder_type': disorder_elem.findtext('.//DisorderType/Name[@lang="en"]', ''),
            'disorder_group': disorder_elem.findtext('.//DisorderGroup/Name[@lang="en"]', ''),
            'expert_link': disorder_elem.findtext('.//ExpertLink[@lang="en"]', ''),
            'created_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }
        
        try:
            # Try to get existing disorder
            existing = self.supabase.table('disorders').select('id').eq('orpha_code', orpha_code).execute()
            
            if existing.data:
                disorder_uuid = existing.data[0]['id']
                # Update existing disorder
                self.supabase.table('disorders').update({
                    'name': disorder_data['name'],
                    'disorder_type': disorder_data['disorder_type'],
                    'disorder_group': disorder_data['disorder_group'],
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }).eq('id', disorder_uuid).execute()
            else:
                # Create new disorder
                result = self.supabase.table('disorders').insert(disorder_data).execute()
                disorder_uuid = result.data[0]['id']
            
            self.disorder_cache[orpha_code] = disorder_uuid
            
            # Add synonyms
            for synonym in disorder_elem.findall('.//Synonym[@lang="en"]'):
                if synonym.text:
                    synonym_data = {
                        'disorder_id': disorder_uuid,
                        'synonym': synonym.text,
                        'created_at': datetime.now(timezone.utc).isoformat()
                    }
                    try:
                        self.supabase.table('disorder_synonyms').insert(synonym_data).execute()
                    except Exception as e:
                        # Ignore duplicate synonyms
                        if 'duplicate' not in str(e).lower():
                            logger.warning(f"Failed to insert synonym: {e}")
            
            return disorder_uuid
            
        except Exception as e:
            logger.error(f"Failed to get/create disorder {orpha_code}: {e}")
            return None
    
    def load_natural_history(self, xml_file: str):
        """Load natural history data from XML file"""
        logger.info(f"Loading natural history from {xml_file}")
        root = self.parse_xml(xml_file)
        
        disorders = root.findall('.//Disorder')
        batch_size = 100
        
        for i in tqdm(range(0, len(disorders), batch_size), desc="Processing natural history"):
            batch_disorders = disorders[i:i + batch_size]
            
            onset_data = []
            inheritance_data = []
            
            for disorder in batch_disorders:
                disorder_uuid = self.get_or_create_disorder(disorder)
                
                if not disorder_uuid:
                    continue
                
                # Collect age of onset data
                for onset in disorder.findall('.//AverageAgeOfOnset'):
                    onset_data.append({
                        'disorder_id': disorder_uuid,
                        'onset_name': onset.findtext('Name[@lang="en"]', ''),
                        'onset_id': int(onset.get('id', 0)),
                        'created_at': datetime.now(timezone.utc).isoformat()
                    })
                
                # Collect inheritance types
                for inheritance in disorder.findall('.//TypeOfInheritance'):
                    inheritance_data.append({
                        'disorder_id': disorder_uuid,
                        'inheritance_name': inheritance.findtext('Name[@lang="en"]', ''),
                        'inheritance_id': int(inheritance.get('id', 0)),
                        'created_at': datetime.now(timezone.utc).isoformat()
                    })
            
            # Batch insert data
            if onset_data:
                try:
                    self.supabase.table('age_of_onset').insert(onset_data).execute()
                except Exception as e:
                    logger.error(f"Failed to insert onset data batch: {e}")
            
            if inheritance_data:
                try:
                    self.supabase.table('inheritance_types').insert(inheritance_data).execute()
                except Exception as e:
                    logger.error(f"Failed to insert inheritance data batch: {e}")
        
        logger.info(f"Loaded natural history for {len(disorders)} disorders")
    
    def load_genes(self, xml_file: str):
        """Load gene association data from XML file"""
        logger.info(f"Loading genes from {xml_file}")
        root = self.parse_xml(xml_file)
        
        disorders = root.findall('.//Disorder')
        batch_size = 50
        
        for i in tqdm(range(0, len(disorders), batch_size), desc="Processing gene associations"):
            batch_disorders = disorders[i:i + batch_size]
            
            associations_data = []
            external_refs_data = []
            
            for disorder in batch_disorders:
                disorder_uuid = self.get_or_create_disorder(disorder)
                
                if not disorder_uuid:
                    continue
                
                for gene_assoc in disorder.findall('.//DisorderGeneAssociation'):
                    gene_elem = gene_assoc.find('Gene')
                    if gene_elem is None:
                        continue
                    
                    gene_symbol = gene_elem.findtext('Symbol', '')
                    
                    # Get or create gene
                    if gene_symbol not in self.gene_cache:
                        gene_data = {
                            'gene_symbol': gene_symbol,
                            'gene_name': gene_elem.findtext('Name[@lang="en"]', ''),
                            'gene_type': gene_elem.findtext('.//GeneType/Name[@lang="en"]', ''),
                            'chromosomal_location': gene_elem.findtext('.//GeneLocus', ''),
                            'created_at': datetime.now(timezone.utc).isoformat(),
                            'updated_at': datetime.now(timezone.utc).isoformat()
                        }
                        
                        try:
                            # Try to get existing gene
                            existing = self.supabase.table('genes').select('id').eq('gene_symbol', gene_symbol).execute()
                            
                            if existing.data:
                                gene_uuid = existing.data[0]['id']
                                # Update existing gene
                                self.supabase.table('genes').update({
                                    'gene_name': gene_data['gene_name'],
                                    'updated_at': gene_data['updated_at']
                                }).eq('id', gene_uuid).execute()
                            else:
                                # Create new gene
                                result = self.supabase.table('genes').insert(gene_data).execute()
                                gene_uuid = result.data[0]['id']
                            
                            self.gene_cache[gene_symbol] = gene_uuid
                            
                            # Collect external references
                            for ext_ref in gene_elem.findall('.//ExternalReference'):
                                external_refs_data.append({
                                    'gene_id': gene_uuid,
                                    'source': ext_ref.findtext('Source', ''),
                                    'reference': ext_ref.findtext('Reference', ''),
                                    'created_at': datetime.now(timezone.utc).isoformat()
                                })
                        except Exception as e:
                            logger.error(f"Failed to process gene {gene_symbol}: {e}")
                            continue
                    else:
                        gene_uuid = self.gene_cache[gene_symbol]
                    
                    # Create association
                    associations_data.append({
                        'disorder_id': disorder_uuid,
                        'gene_id': gene_uuid,
                        'association_type': gene_assoc.findtext('.//DisorderGeneAssociationType/Name[@lang="en"]', ''),
                        'association_status': gene_assoc.findtext('.//DisorderGeneAssociationStatus/Name[@lang="en"]', ''),
                        'source_of_validation': gene_assoc.findtext('SourceOfValidation', ''),
                        'created_at': datetime.now(timezone.utc).isoformat()
                    })
            
            # Batch insert associations
            if associations_data:
                try:
                    self.supabase.table('disorder_gene_associations').insert(associations_data).execute()
                except Exception as e:
                    logger.error(f"Failed to insert gene associations batch: {e}")
            
            # Batch insert external references
            if external_refs_data:
                try:
                    self.supabase.table('gene_external_refs').insert(external_refs_data).execute()
                except Exception as e:
                    logger.error(f"Failed to insert gene external refs batch: {e}")
        
        logger.info(f"Loaded gene associations for {len(disorders)} disorders")
    
    def load_clinical_signs(self, xml_file: str):
        """Load clinical signs and symptoms (HPO terms) from XML file"""
        logger.info(f"Loading clinical signs from {xml_file}")
        root = self.parse_xml(xml_file)
        
        hpo_disorders = root.findall('.//HPODisorderSetStatus')
        batch_size = 100
        
        for i in tqdm(range(0, len(hpo_disorders), batch_size), desc="Processing clinical signs"):
            batch_disorders = hpo_disorders[i:i + batch_size]
            
            associations_data = []
            
            for hpo_disorder in batch_disorders:
                disorder = hpo_disorder.find('Disorder')
                if disorder is None:
                    continue
                
                disorder_uuid = self.get_or_create_disorder(disorder)
                if not disorder_uuid:
                    continue
                
                for hpo_assoc in disorder.findall('.//HPODisorderAssociation'):
                    hpo_id = hpo_assoc.findtext('.//HPOId', '')
                    
                    # Get or create HPO term
                    if hpo_id not in self.hpo_cache:
                        hpo_data = {
                            'hpo_id': hpo_id,
                            'term': hpo_assoc.findtext('.//HPOTerm', ''),
                            'created_at': datetime.now(timezone.utc).isoformat()
                        }
                        
                        try:
                            # Try to get existing HPO term
                            existing = self.supabase.table('hpo_terms').select('id').eq('hpo_id', hpo_id).execute()
                            
                            if existing.data:
                                hpo_uuid = existing.data[0]['id']
                                # Update existing HPO term
                                self.supabase.table('hpo_terms').update({
                                    'term': hpo_data['term']
                                }).eq('id', hpo_uuid).execute()
                            else:
                                # Create new HPO term
                                result = self.supabase.table('hpo_terms').insert(hpo_data).execute()
                                hpo_uuid = result.data[0]['id']
                            
                            self.hpo_cache[hpo_id] = hpo_uuid
                        except Exception as e:
                            logger.error(f"Failed to process HPO term {hpo_id}: {e}")
                            continue
                    else:
                        hpo_uuid = self.hpo_cache[hpo_id]
                    
                    # Create association
                    frequency = hpo_assoc.findtext('.//HPOFrequency/Name[@lang="en"]', '')
                    
                    # Parse frequency category
                    frequency_category = None
                    if '99-80%' in frequency:
                        frequency_category = 'Very frequent'
                    elif '79-30%' in frequency:
                        frequency_category = 'Frequent'
                    elif '29-5%' in frequency:
                        frequency_category = 'Occasional'
                    elif '4-1%' in frequency:
                        frequency_category = 'Very rare'
                    
                    associations_data.append({
                        'disorder_id': disorder_uuid,
                        'hpo_term_id': hpo_uuid,
                        'frequency': frequency,
                        'frequency_category': frequency_category,
                        'diagnostic_criteria': bool(hpo_assoc.findtext('DiagnosticCriteria', '')),
                        'created_at': datetime.now(timezone.utc).isoformat()
                    })
            
            # Batch insert associations
            if associations_data:
                try:
                    self.supabase.table('disorder_hpo_associations').insert(associations_data).execute()
                except Exception as e:
                    logger.error(f"Failed to insert HPO associations batch: {e}")
        
        logger.info(f"Loaded clinical signs for {len(hpo_disorders)} disorders")
    
    def load_epidemiology(self, xml_file: str):
        """Load epidemiology data from XML file"""
        logger.info(f"Loading epidemiology from {xml_file}")
        root = self.parse_xml(xml_file)
        
        disorders = root.findall('.//Disorder')
        batch_size = 100
        
        for i in tqdm(range(0, len(disorders), batch_size), desc="Processing epidemiology"):
            batch_disorders = disorders[i:i + batch_size]
            
            prevalence_data = []
            
            for disorder in batch_disorders:
                disorder_uuid = self.get_or_create_disorder(disorder)
                
                if not disorder_uuid:
                    continue
                
                for prevalence in disorder.findall('.//Prevalence'):
                    val_moy = prevalence.findtext('ValMoy', '0')
                    try:
                        val_moy = float(val_moy) if val_moy else 0.0
                    except ValueError:
                        val_moy = 0.0
                    
                    prevalence_data.append({
                        'disorder_id': disorder_uuid,
                        'prevalence_type': prevalence.findtext('.//PrevalenceType/Name[@lang="en"]', ''),
                        'prevalence_qualification': prevalence.findtext('.//PrevalenceQualification/Name[@lang="en"]', ''),
                        'prevalence_class': prevalence.findtext('.//PrevalenceClass/Name[@lang="en"]', ''),
                        'val_moy': val_moy,
                        'geographic_area': prevalence.findtext('.//PrevalenceGeographic/Name[@lang="en"]', ''),
                        'validation_status': prevalence.findtext('.//PrevalenceValidationStatus/Name[@lang="en"]', ''),
                        'source': prevalence.findtext('Source', ''),
                        'created_at': datetime.now(timezone.utc).isoformat()
                    })
            
            # Batch insert data
            if prevalence_data:
                try:
                    self.supabase.table('prevalence_data').insert(prevalence_data).execute()
                except Exception as e:
                    logger.error(f"Failed to insert prevalence data batch: {e}")
        
        logger.info(f"Loaded epidemiology for {len(disorders)} disorders")
    
    def load_classifications(self, xml_file: str):
        """Load disorder classifications/linearisation from XML file"""
        logger.info(f"Loading classifications from {xml_file}")
        root = self.parse_xml(xml_file)
        
        disorders = root.findall('.//Disorder')
        batch_size = 100
        
        for i in tqdm(range(0, len(disorders), batch_size), desc="Processing classifications"):
            batch_disorders = disorders[i:i + batch_size]
            
            classification_data = []
            
            for disorder in batch_disorders:
                disorder_uuid = self.get_or_create_disorder(disorder)
                
                if not disorder_uuid:
                    continue
                
                for assoc in disorder.findall('.//DisorderDisorderAssociation'):
                    classification_data.append({
                        'disorder_id': disorder_uuid,
                        'parent_disorder_orpha_code': assoc.findtext('.//TargetDisorder/OrphaCode', ''),
                        'parent_disorder_name': assoc.findtext('.//TargetDisorder/Name[@lang="en"]', ''),
                        'association_type': assoc.findtext('.//DisorderDisorderAssociationType/Name[@lang="en"]', ''),
                        'created_at': datetime.now(timezone.utc).isoformat()
                    })
            
            # Batch insert data
            if classification_data:
                try:
                    self.supabase.table('disorder_classifications').insert(classification_data).execute()
                except Exception as e:
                    logger.error(f"Failed to insert classification data batch: {e}")
        
        logger.info(f"Loaded classifications for {len(disorders)} disorders")
    
    def load_external_references(self, xml_file: str):
        """Load external references and terminology alignments from XML file"""
        logger.info(f"Loading external references from {xml_file}")
        root = self.parse_xml(xml_file)
        
        disorders = root.findall('.//Disorder')
        batch_size = 50
        
        for i in tqdm(range(0, len(disorders), batch_size), desc="Processing external references"):
            batch_disorders = disorders[i:i + batch_size]
            
            references_data = []
            texts_data = []
            
            for disorder in batch_disorders:
                disorder_uuid = self.get_or_create_disorder(disorder)
                
                if not disorder_uuid:
                    continue
                
                # Load external references
                for ext_ref in disorder.findall('.//ExternalReference'):
                    references_data.append({
                        'disorder_id': disorder_uuid,
                        'source': ext_ref.findtext('Source', ''),
                        'reference': ext_ref.findtext('Reference', ''),
                        'mapping_relation': ext_ref.findtext('.//DisorderMappingRelation/Name[@lang="en"]', ''),
                        'mapping_validation_status': ext_ref.findtext('.//DisorderMappingValidationStatus/Name[@lang="en"]', ''),
                        'created_at': datetime.now(timezone.utc).isoformat()
                    })
                
                # Load disorder texts (definitions)
                for text_section in disorder.findall('.//TextSection[@lang="en"]'):
                    text_type = text_section.findtext('.//TextSectionType/Name[@lang="en"]', 'definition')
                    content = text_section.findtext('Contents', '')
                    
                    if content:
                        texts_data.append({
                            'disorder_id': disorder_uuid,
                            'text_type': text_type,
                            'content': content,
                            'created_at': datetime.now(timezone.utc).isoformat()
                        })
            
            # Batch insert data
            if references_data:
                try:
                    self.supabase.table('external_references').insert(references_data).execute()
                except Exception as e:
                    logger.error(f"Failed to insert external references batch: {e}")
            
            if texts_data:
                try:
                    self.supabase.table('disorder_texts').insert(texts_data).execute()
                except Exception as e:
                    logger.error(f"Failed to insert disorder texts batch: {e}")
        
        logger.info(f"Loaded external references for {len(disorders)} disorders")
    
    def load_functional_consequences(self, xml_file: str):
        """Load functional consequences and disabilities from XML file"""
        logger.info(f"Loading functional consequences from {xml_file}")
        root = self.parse_xml(xml_file)
        
        disorder_disabilities = root.findall('.//DisorderDisabilityRelevance')
        batch_size = 100
        
        for i in tqdm(range(0, len(disorder_disabilities), batch_size), desc="Processing disabilities"):
            batch_disabilities = disorder_disabilities[i:i + batch_size]
            
            associations_data = []
            
            for disorder_disability in batch_disabilities:
                disorder = disorder_disability.find('Disorder')
                if disorder is None:
                    continue
                
                disorder_uuid = self.get_or_create_disorder(disorder)
                if not disorder_uuid:
                    continue
                
                for disability_assoc in disorder_disability.findall('.//DisabilityDisorderAssociation'):
                    disability_elem = disability_assoc.find('Disability')
                    if disability_elem is None:
                        continue
                    
                    disability_id = int(disability_elem.get('id', 0))
                    disability_name = disability_elem.findtext('Name[@lang="en"]', '')
                    
                    # Get or create disability
                    if disability_id not in self.disability_cache:
                        disability_data = {
                            'disability_id': disability_id,
                            'name': disability_name,
                            'created_at': datetime.now(timezone.utc).isoformat()
                        }
                        
                        try:
                            # Try to get existing disability
                            existing = self.supabase.table('disabilities').select('id').eq('disability_id', disability_id).execute()
                            
                            if existing.data:
                                disability_uuid = existing.data[0]['id']
                                # Update existing disability
                                self.supabase.table('disabilities').update({
                                    'name': disability_data['name']
                                }).eq('id', disability_uuid).execute()
                            else:
                                # Create new disability
                                result = self.supabase.table('disabilities').insert(disability_data).execute()
                                disability_uuid = result.data[0]['id']
                            
                            self.disability_cache[disability_id] = disability_uuid
                        except Exception as e:
                            logger.error(f"Failed to process disability {disability_id}: {e}")
                            continue
                    else:
                        disability_uuid = self.disability_cache[disability_id]
                    
                    # Create association
                    associations_data.append({
                        'disorder_id': disorder_uuid,
                        'disability_id': disability_uuid,
                        'frequency': disability_assoc.findtext('.//FrequenceDisability/Name[@lang="en"]', ''),
                        'temporality': disability_assoc.findtext('.//TemporalityDisability/Name[@lang="en"]', ''),
                        'severity': disability_assoc.findtext('.//SeverityDisability/Name[@lang="en"]', ''),
                        'loss_of_ability': disability_assoc.findtext('LossOfAbility', '') == 'y',
                        'created_at': datetime.now(timezone.utc).isoformat()
                    })
            
            # Batch insert associations
            if associations_data:
                try:
                    self.supabase.table('disorder_disability_associations').insert(associations_data).execute()
                except Exception as e:
                    logger.error(f"Failed to insert disability associations batch: {e}")
        
        logger.info(f"Loaded disabilities for {len(disorder_disabilities)} disorders")
    
    def load_all_xml_files(self, file_directory: str):
        """Load all XML files from a directory"""
        file_mappings = {
            'natural_history': self.load_natural_history,
            'genes_associated': self.load_genes,
            'clinical_signs': self.load_clinical_signs,
            'epidemiology': self.load_epidemiology,
            'linearisation': self.load_classifications,
            'alignment_with_terminology': self.load_external_references,
            'functional_consequences': self.load_functional_consequences
        }
        
        # Look for XML files specifically
        xml_files = []
        for filename in os.listdir(file_directory):
            if filename.endswith('.xml'):
                xml_files.append(filename)
        
        logger.info(f"Found {len(xml_files)} XML files to process")
        
        for filename in xml_files:
            filepath = os.path.join(file_directory, filename)
            
            # Determine which loader to use
            for key, loader_func in file_mappings.items():
                if key in filename.lower():
                    try:
                        logger.info(f"Processing {filename} with {key} loader")
                        loader_func(filepath)
                        
                        # Record import metadata (ignore errors for missing columns)
                        try:
                            metadata = {
                                'file_name': filename,
                                'file_type': key,
                                'orphanet_version': 'Full_XML',
                                'status': 'completed'
                            }
                            self.supabase.table('import_metadata').insert(metadata).execute()
                        except Exception as e:
                            logger.warning(f"Failed to record metadata for {filename}: {e}")
                        
                    except Exception as e:
                        logger.error(f"Failed to load {filename}: {e}")
                        # Record failed import
                        try:
                            metadata = {
                                'file_name': filename,
                                'file_type': key,
                                'orphanet_version': 'Full_XML',
                                'status': 'failed',
                                'error_message': str(e)
                            }
                            self.supabase.table('import_metadata').insert(metadata).execute()
                        except:
                            pass
                    break
            else:
                logger.warning(f"No loader found for {filename}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get loading statistics"""
        stats = {}
        tables = [
            'disorders', 'disorder_synonyms', 'age_of_onset', 'inheritance_types',
            'genes', 'gene_external_refs', 'disorder_gene_associations',
            'hpo_terms', 'disorder_hpo_associations', 'prevalence_data',
            'disorder_classifications', 'external_references', 'disorder_texts',
            'disabilities', 'disorder_disability_associations', 'import_metadata'
        ]
        
        for table in tables:
            try:
                result = self.supabase.table(table).select('id', count='exact').execute()
                stats[table] = result.count
            except Exception as e:
                stats[table] = f"Error: {e}"
        
        return stats


def main():
    parser = argparse.ArgumentParser(description='Load Orphanet XML files to Supabase')
    parser.add_argument('--directory', '-d', required=True, help='Directory containing XML files')
    parser.add_argument('--url', '-u', help='Supabase URL (or use SUPABASE_URL env var)')
    parser.add_argument('--key', '-k', help='Supabase anonymous key (or use SUPABASE_KEY env var)')
    parser.add_argument('--stats', '-s', action='store_true', help='Show statistics after loading')
    
    args = parser.parse_args()
    
    # Get configuration from args or environment
    supabase_url = args.url or os.getenv('SUPABASE_URL')
    supabase_key = args.key or os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        logger.error("Missing Supabase URL or key. Provide via --url/--key or set SUPABASE_URL/SUPABASE_KEY environment variables")
        sys.exit(1)
    
    # Create configuration
    config = SupabaseConfig(
        supabase_url=supabase_url,
        supabase_key=supabase_key
    )
    
    # Create loader and process files
    loader = OrphanetXMLLoader(config)
    
    try:
        # Connect to Supabase
        if not loader.connect_supabase():
            logger.error("Failed to connect to Supabase")
            sys.exit(1)
        
        # Load all XML files
        loader.load_all_xml_files(args.directory)
        
        logger.info("Data loading completed successfully!")
        
        # Show statistics if requested
        if args.stats:
            logger.info("Getting statistics...")
            stats = loader.get_statistics()
            print("\n=== Loading Statistics ===")
            for table, count in stats.items():
                print(f"{table:30} {count}")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()