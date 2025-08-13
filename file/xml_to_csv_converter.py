#!/usr/bin/env python3
"""
XML to CSV Converter for Orphanet Rare Disease Database Files
Converts various Orphanet XML files to CSV format while preserving structure
"""

import xml.etree.ElementTree as ET
import csv
import os
from typing import Dict, List, Any
import argparse


class OrphanetXMLtoCSV:
    """Base class for converting Orphanet XML files to CSV"""

    def __init__(self, xml_file: str, csv_file: str = None):
        self.xml_file = xml_file
        self.csv_file = csv_file or xml_file.replace('.xml', '.csv').replace('.txt', '.csv')
        self.tree = None
        self.root = None

    def parse_xml(self):
        """Parse the XML file"""
        self.tree = ET.parse(self.xml_file)
        self.root = self.tree.getroot()

    def get_disorder_base_info(self, disorder) -> Dict[str, str]:
        """Extract common disorder information"""
        info = {
            'disorder_id': disorder.get('id', ''),
            'orpha_code': disorder.findtext('.//OrphaCode', ''),
            'name': disorder.findtext('.//Name[@lang="en"]', ''),
            'disorder_type': disorder.findtext('.//DisorderType/Name[@lang="en"]', ''),
            'disorder_group': disorder.findtext('.//DisorderGroup/Name[@lang="en"]', ''),
            'expert_link': disorder.findtext('.//ExpertLink[@lang="en"]', '')
        }
        return info


class NaturalHistoryConverter(OrphanetXMLtoCSV):
    """Converter for natural_history_of_rare_diseases files"""

    def convert(self):
        self.parse_xml()

        with open(self.csv_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['disorder_id', 'orpha_code', 'name', 'disorder_type', 'disorder_group',
                         'expert_link', 'age_of_onset', 'type_of_inheritance']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for disorder in self.root.findall('.//Disorder'):
                base_info = self.get_disorder_base_info(disorder)

                # Get age of onset
                age_onsets = []
                for onset in disorder.findall('.//AverageAgeOfOnset'):
                    age_onsets.append(onset.findtext('Name[@lang="en"]', ''))

                # Get inheritance types
                inheritances = []
                for inheritance in disorder.findall('.//TypeOfInheritance'):
                    inheritances.append(inheritance.findtext('Name[@lang="en"]', ''))

                row = base_info.copy()
                row['age_of_onset'] = '|'.join(age_onsets)
                row['type_of_inheritance'] = '|'.join(inheritances)

                writer.writerow(row)


class LinearisationConverter(OrphanetXMLtoCSV):
    """Converter for linearisation_of_rare_diseases files"""

    def convert(self):
        self.parse_xml()

        with open(self.csv_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['disorder_id', 'orpha_code', 'name', 'target_disorder_code',
                         'target_disorder_name', 'association_type']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for disorder in self.root.findall('.//Disorder'):
                base_info = self.get_disorder_base_info(disorder)

                # Get disorder associations
                for assoc in disorder.findall('.//DisorderDisorderAssociation'):
                    row = {
                        'disorder_id': base_info['disorder_id'],
                        'orpha_code': base_info['orpha_code'],
                        'name': base_info['name'],
                        'target_disorder_code': assoc.findtext('.//TargetDisorder/OrphaCode', ''),
                        'target_disorder_name': assoc.findtext('.//TargetDisorder/Name[@lang="en"]', ''),
                        'association_type': assoc.findtext('.//DisorderDisorderAssociationType/Name[@lang="en"]', '')
                    }
                    writer.writerow(row)

                # If no associations, write basic info
                if not disorder.findall('.//DisorderDisorderAssociation'):
                    row = {
                        'disorder_id': base_info['disorder_id'],
                        'orpha_code': base_info['orpha_code'],
                        'name': base_info['name'],
                        'target_disorder_code': '',
                        'target_disorder_name': '',
                        'association_type': ''
                    }
                    writer.writerow(row)


class EpidemiologyConverter(OrphanetXMLtoCSV):
    """Converter for epidemiology_of_rare_diseases files"""

    def convert(self):
        self.parse_xml()

        with open(self.csv_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['disorder_id', 'orpha_code', 'name', 'disorder_type', 'disorder_group',
                         'prevalence_type', 'prevalence_qualification', 'prevalence_class',
                         'val_moy', 'prevalence_geographic', 'prevalence_validation_status', 'source']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for disorder in self.root.findall('.//Disorder'):
                base_info = self.get_disorder_base_info(disorder)

                # Get prevalence data
                for prev in disorder.findall('.//Prevalence'):
                    row = {
                        'disorder_id': base_info['disorder_id'],
                        'orpha_code': base_info['orpha_code'],
                        'name': base_info['name'],
                        'disorder_type': base_info['disorder_type'],
                        'disorder_group': base_info['disorder_group'],
                        'prevalence_type': prev.findtext('.//PrevalenceType/Name[@lang="en"]', ''),
                        'prevalence_qualification': prev.findtext('.//PrevalenceQualification/Name[@lang="en"]', ''),
                        'prevalence_class': prev.findtext('.//PrevalenceClass/Name[@lang="en"]', ''),
                        'val_moy': prev.findtext('ValMoy', ''),
                        'prevalence_geographic': prev.findtext('.//PrevalenceGeographic/Name[@lang="en"]', ''),
                        'prevalence_validation_status': prev.findtext('.//PrevalenceValidationStatus/Name[@lang="en"]', ''),
                        'source': prev.findtext('Source', '')
                    }
                    writer.writerow(row)

                # If no prevalence data, write basic info
                if not disorder.findall('.//Prevalence'):
                    row = {
                        'disorder_id': base_info['disorder_id'],
                        'orpha_code': base_info['orpha_code'],
                        'name': base_info['name'],
                        'disorder_type': base_info['disorder_type'],
                        'disorder_group': base_info['disorder_group']
                    }
                    writer.writerow(row)


class GenesConverter(OrphanetXMLtoCSV):
    """Converter for genes_associated_with_rare_diseases files"""

    def convert(self):
        self.parse_xml()

        with open(self.csv_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['disorder_id', 'orpha_code', 'disorder_name', 'gene_symbol',
                         'gene_name', 'gene_type', 'gene_locus', 'association_type',
                         'association_status', 'source_of_validation']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for disorder in self.root.findall('.//Disorder'):
                base_info = self.get_disorder_base_info(disorder)

                # Get gene associations
                for gene_assoc in disorder.findall('.//DisorderGeneAssociation'):
                    gene = gene_assoc.find('Gene')
                    if gene is not None:
                        row = {
                            'disorder_id': base_info['disorder_id'],
                            'orpha_code': base_info['orpha_code'],
                            'disorder_name': base_info['name'],
                            'gene_symbol': gene.findtext('Symbol', ''),
                            'gene_name': gene.findtext('Name[@lang="en"]', ''),
                            'gene_type': gene.findtext('.//GeneType/Name[@lang="en"]', ''),
                            'gene_locus': gene.findtext('.//GeneLocus', ''),
                            'association_type': gene_assoc.findtext('.//DisorderGeneAssociationType/Name[@lang="en"]', ''),
                            'association_status': gene_assoc.findtext('.//DisorderGeneAssociationStatus/Name[@lang="en"]', ''),
                            'source_of_validation': gene_assoc.findtext('SourceOfValidation', '')
                        }
                        writer.writerow(row)

                # If no gene associations, write basic info
                if not disorder.findall('.//DisorderGeneAssociation'):
                    row = {
                        'disorder_id': base_info['disorder_id'],
                        'orpha_code': base_info['orpha_code'],
                        'disorder_name': base_info['name']
                    }
                    writer.writerow(row)


class FunctionalConsequencesConverter(OrphanetXMLtoCSV):
    """Converter for rare_diseases_and_functional_consequences files"""

    def convert(self):
        self.parse_xml()

        with open(self.csv_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['disorder_id', 'orpha_code', 'disorder_name', 'disorder_type',
                         'disability_name', 'frequency', 'temporality', 'severity',
                         'loss_of_ability', 'type', 'defined']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for disorder_disability in self.root.findall('.//DisorderDisabilityRelevance'):
                disorder = disorder_disability.find('Disorder')
                if disorder is not None:
                    base_info = self.get_disorder_base_info(disorder)

                    # Get disability associations
                    for disability_assoc in disorder_disability.findall('.//DisabilityDisorderAssociation'):
                        row = {
                            'disorder_id': base_info['disorder_id'],
                            'orpha_code': base_info['orpha_code'],
                            'disorder_name': base_info['name'],
                            'disorder_type': base_info['disorder_type'],
                            'disability_name': disability_assoc.findtext('.//Disability/Name[@lang="en"]', ''),
                            'frequency': disability_assoc.findtext('.//FrequenceDisability/Name[@lang="en"]', ''),
                            'temporality': disability_assoc.findtext('.//TemporalityDisability/Name[@lang="en"]', ''),
                            'severity': disability_assoc.findtext('.//SeverityDisability/Name[@lang="en"]', ''),
                            'loss_of_ability': disability_assoc.findtext('LossOfAbility', ''),
                            'type': disability_assoc.findtext('Type', ''),
                            'defined': disability_assoc.findtext('Defined', '')
                        }
                        writer.writerow(row)


class TerminologyAlignmentConverter(OrphanetXMLtoCSV):
    """Converter for rare_disease_alignment_with_terminology files"""

    def convert(self):
        self.parse_xml()

        with open(self.csv_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['disorder_id', 'orpha_code', 'disorder_name', 'disorder_type',
                         'synonym', 'external_source', 'external_reference', 'mapping_relation',
                         'mapping_validation_status', 'definition']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for disorder in self.root.findall('.//Disorder'):
                base_info = self.get_disorder_base_info(disorder)

                # Get synonyms
                synonyms = []
                for synonym in disorder.findall('.//Synonym[@lang="en"]'):
                    synonyms.append(synonym.text)
                synonym_str = '|'.join(synonyms) if synonyms else ''

                # Get definition
                definition = disorder.findtext('.//TextSection[@lang="en"]/Contents', '')

                # Get external references
                has_refs = False
                for ext_ref in disorder.findall('.//ExternalReference'):
                    has_refs = True
                    row = {
                        'disorder_id': base_info['disorder_id'],
                        'orpha_code': base_info['orpha_code'],
                        'disorder_name': base_info['name'],
                        'disorder_type': base_info['disorder_type'],
                        'synonym': synonym_str,
                        'external_source': ext_ref.findtext('Source', ''),
                        'external_reference': ext_ref.findtext('Reference', ''),
                        'mapping_relation': ext_ref.findtext('.//DisorderMappingRelation/Name[@lang="en"]', ''),
                        'mapping_validation_status': ext_ref.findtext('.//DisorderMappingValidationStatus/Name[@lang="en"]', ''),
                        'definition': definition
                    }
                    writer.writerow(row)

                # If no external references, write basic info
                if not has_refs:
                    row = {
                        'disorder_id': base_info['disorder_id'],
                        'orpha_code': base_info['orpha_code'],
                        'disorder_name': base_info['name'],
                        'disorder_type': base_info['disorder_type'],
                        'synonym': synonym_str,
                        'definition': definition
                    }
                    writer.writerow(row)


class ClinicalSignsConverter(OrphanetXMLtoCSV):
    """Converter for clinical_signs_and_symptoms_in_rare_diseases files"""

    def convert(self):
        self.parse_xml()

        with open(self.csv_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['disorder_id', 'orpha_code', 'disorder_name', 'disorder_type',
                         'hpo_id', 'hpo_term', 'hpo_frequency', 'diagnostic_criteria']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for hpo_disorder in self.root.findall('.//HPODisorderSetStatus'):
                disorder = hpo_disorder.find('Disorder')
                if disorder is not None:
                    base_info = self.get_disorder_base_info(disorder)

                    # Get HPO associations
                    for hpo_assoc in disorder.findall('.//HPODisorderAssociation'):
                        row = {
                            'disorder_id': base_info['disorder_id'],
                            'orpha_code': base_info['orpha_code'],
                            'disorder_name': base_info['name'],
                            'disorder_type': base_info['disorder_type'],
                            'hpo_id': hpo_assoc.findtext('.//HPOId', ''),
                            'hpo_term': hpo_assoc.findtext('.//HPOTerm', ''),
                            'hpo_frequency': hpo_assoc.findtext('.//HPOFrequency/Name[@lang="en"]', ''),
                            'diagnostic_criteria': hpo_assoc.findtext('DiagnosticCriteria', '')
                        }
                        writer.writerow(row)

                    # If no HPO associations, write basic info
                    if not disorder.findall('.//HPODisorderAssociation'):
                        row = {
                            'disorder_id': base_info['disorder_id'],
                            'orpha_code': base_info['orpha_code'],
                            'disorder_name': base_info['name'],
                            'disorder_type': base_info['disorder_type']
                        }
                        writer.writerow(row)


def get_converter_for_file(filename: str) -> OrphanetXMLtoCSV:
    """Determine which converter to use based on filename"""
    filename_lower = filename.lower()

    if 'natural_history' in filename_lower:
        return NaturalHistoryConverter
    elif 'linearisation' in filename_lower:
        return LinearisationConverter
    elif 'epidemiology' in filename_lower:
        return EpidemiologyConverter
    elif 'genes_associated' in filename_lower:
        return GenesConverter
    elif 'functional_consequences' in filename_lower:
        return FunctionalConsequencesConverter
    elif 'alignment_with_terminology' in filename_lower:
        return TerminologyAlignmentConverter
    elif 'clinical_signs' in filename_lower:
        return ClinicalSignsConverter
    else:
        raise ValueError(f"Cannot determine converter type for file: {filename}")


def main():
    parser = argparse.ArgumentParser(description='Convert Orphanet XML files to CSV format')
    parser.add_argument('input_files', nargs='+', help='Input XML file(s) to convert')
    parser.add_argument('--output-dir', '-o', help='Output directory for CSV files (default: same as input)')

    args = parser.parse_args()

    for input_file in args.input_files:
        try:
            print(f"Processing: {input_file}")

            # Get appropriate converter
            converter_class = get_converter_for_file(input_file)

            # Determine output file path
            if args.output_dir:
                basename = os.path.basename(input_file)
                output_file = os.path.join(args.output_dir,
                                          basename.replace('.xml', '.csv').replace('.txt', '.csv'))
            else:
                output_file = None  # Use default (same directory as input)

            # Convert file
            converter = converter_class(input_file, output_file)
            converter.convert()

            output_name = output_file or input_file.replace('.xml', '.csv').replace('.txt', '.csv')
            print(f"  ✓ Converted to: {output_name}")

        except Exception as e:
            print(f"  ✗ Error processing {input_file}: {str(e)}")


if __name__ == "__main__":
    main()
