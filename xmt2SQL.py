import xml.etree.ElementTree as ET
import csv
import os
from pathlib import Path
import psycopg2
from psycopg2.extras import execute_batch
import logging

class XMLToPostgresLoader:
    def __init__(self, connection_string):
        self.conn = psycopg2.connect(connection_string)
        self.cursor = self.conn.cursor()

    def parse_clinical_signs_xml(self, xml_file):
        """Parse Clinical signs and symptoms XML"""
        tree = ET.parse(xml_file)
        root = tree.getroot()

        disorders = []
        hpo_terms = []
        associations = []

        for disorder_elem in root.findall('.//Disorder'):
            # Extract disorder info
            disorder_id = disorder_elem.get('id')
            orpha_code = disorder_elem.find('OrphaCode').text if disorder_elem.find('OrphaCode') is not None else None
            name = disorder_elem.find('Name').text if disorder_elem.find('Name') is not None else None

            disorders.append({
                'orpha_code': orpha_code,
                'name': name,
                'external_id': disorder_id
            })

            # Extract HPO associations
            hpo_list = disorder_elem.find('HPODisorderAssociationList')
            if hpo_list is not None:
                for hpo_assoc in hpo_list.findall('HPODisorderAssociation'):
                    hpo_elem = hpo_assoc.find('HPO')
                    if hpo_elem is not None:
                        hpo_id = hpo_elem.find('HPOId').text if hpo_elem.find('HPOId') is not None else None
                        hpo_term = hpo_elem.find('HPOTerm').text if hpo_elem.find('HPOTerm') is not None else None
                        frequency = hpo_elem.find('HPOFrequency').text if hpo_elem.find('HPOFrequency') is not None else None

                        hpo_terms.append({
                            'hpo_id': hpo_id,
                            'term': hpo_term
                        })

                        associations.append({
                            'disorder_orpha_code': orpha_code,
                            'hpo_id': hpo_id,
                            'frequency': frequency
                        })

        return disorders, hpo_terms, associations

    def parse_epidemiology_xml(self, xml_file):
        """Parse Epidemiology XML"""
        tree = ET.parse(xml_file)
        root = tree.getroot()

        prevalences = []

        for disorder_elem in root.findall('.//Disorder'):
            orpha_code = disorder_elem.find('OrphaCode').text if disorder_elem.find('OrphaCode') is not None else None

            prev_list = disorder_elem.find('PrevalenceList')
            if prev_list is not None:
                for prev_elem in prev_list.findall('Prevalence'):
                    prevalence_data = {
                        'disorder_orpha_code': orpha_code,
                        'prevalence_type': prev_elem.find('PrevalenceType').text if prev_elem.find('PrevalenceType') is not None else None,
                        'prevalence_class': prev_elem.find('PrevalenceClass').text if prev_elem.find('PrevalenceClass') is not None else None,
                        'val_moy': prev_elem.find('ValMoy').text if prev_elem.find('ValMoy') is not None else None,
                        'geographic_area': prev_elem.find('PrevalenceGeographic').text if prev_elem.find('PrevalenceGeographic') is not None else None,
                        'source': prev_elem.find('Source').text if prev_elem.find('Source') is not None else None
                    }
                    prevalences.append(prevalence_data)

        return prevalences

    def parse_genes_xml(self, xml_file):
        """Parse Genes XML"""
        tree = ET.parse(xml_file)
        root = tree.getroot()

        genes = []
        gene_associations = []

        for disorder_elem in root.findall('.//Disorder'):
            orpha_code = disorder_elem.find('OrphaCode').text if disorder_elem.find('OrphaCode') is not None else None

            gene_assoc_list = disorder_elem.find('DisorderGeneAssociationList')
            if gene_assoc_list is not None:
                for gene_assoc in gene_assoc_list.findall('DisorderGeneAssociation'):
                    gene_elem = gene_assoc.find('Gene')
                    if gene_elem is not None:
                        symbol = gene_elem.find('Symbol').text if gene_elem.find('Symbol') is not None else None
                        name = gene_elem.find('Name').text if gene_elem.find('Name') is not None else None
                        gene_type = gene_elem.find('GeneType').text if gene_elem.find('GeneType') is not None else None

                        locus_elem = gene_elem.find('LocusList/Locus')
                        locus = locus_elem.find('GeneLocus').text if locus_elem and locus_elem.find('GeneLocus') is not None else None

                        genes.append({
                            'symbol': symbol,
                            'name': name,
                            'gene_type': gene_type,
                            'locus': locus
                        })

                        assoc_type = gene_assoc.find('DisorderGeneAssociationType').text if gene_assoc.find('DisorderGeneAssociationType') is not None else None
                        assoc_status = gene_assoc.find('DisorderGeneAssociationStatus').text if gene_assoc.find('DisorderGeneAssociationStatus') is not None else None

                        gene_associations.append({
                            'disorder_orpha_code': orpha_code,
                            'gene_symbol': symbol,
                            'association_type': assoc_type,
                            'association_status': assoc_status
                        })

        return genes, gene_associations

    def insert_data(self, data_dict):
        """Insert all data into database"""
        try:
            # Insert disorder types and groups first (if any)
            # ... (simplified for brevity)

            # Insert disorders
            if 'disorders' in data_dict:
                disorders_sql = """
                INSERT INTO disorders (orpha_code, name)
                VALUES (%s, %s)
                ON CONFLICT (orpha_code) DO UPDATE SET name = EXCLUDED.name
                """
                disorder_data = [(d['orpha_code'], d['name']) for d in data_dict['disorders']]
                execute_batch(self.cursor, disorders_sql, disorder_data)

            # Insert HPO terms
            if 'hpo_terms' in data_dict:
                hpo_sql = """
                INSERT INTO hpo_terms (hpo_id, term)
                VALUES (%s, %s)
                ON CONFLICT (hpo_id) DO UPDATE SET term = EXCLUDED.term
                """
                hpo_data = [(h['hpo_id'], h['term']) for h in data_dict['hpo_terms']]
                execute_batch(self.cursor, hpo_sql, hpo_data)

            # Insert genes
            if 'genes' in data_dict:
                genes_sql = """
                INSERT INTO genes (symbol, name, gene_type, locus)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (symbol) DO UPDATE SET
                name = EXCLUDED.name, gene_type = EXCLUDED.gene_type, locus = EXCLUDED.locus
                """
                gene_data = [(g['symbol'], g['name'], g['gene_type'], g['locus']) for g in data_dict['genes']]
                execute_batch(self.cursor, genes_sql, gene_data)

            # Insert associations (requires JOIN to get IDs)
            if 'hpo_associations' in data_dict:
                hpo_assoc_sql = """
                INSERT INTO disorder_hpo_associations (disorder_id, hpo_term_id, frequency)
                SELECT d.id, h.id, %s
                FROM disorders d, hpo_terms h
                WHERE d.orpha_code = %s AND h.hpo_id = %s
                ON CONFLICT (disorder_id, hpo_term_id) DO UPDATE SET frequency = EXCLUDED.frequency
                """
                hpo_assoc_data = [(a['frequency'], a['disorder_orpha_code'], a['hpo_id'])
                                 for a in data_dict['hpo_associations']]
                execute_batch(self.cursor, hpo_assoc_sql, hpo_assoc_data)

            self.conn.commit()
            print("Data inserted successfully!")

        except Exception as e:
            self.conn.rollback()
            print(f"Error inserting data: {e}")
            raise

# Usage example
def main():
    # Your Supabase connection string
    conn_string = "postgresql://postgres:N^o!VQNJW44NPyF*zA$j@ecrcdeztnbciybqkwkpf.supabase.co:5432/postgres"

    loader = XMLToPostgresLoader(conn_string)

    # Parse each XML file
    xml_files = {
        'clinical_signs': 'file/Clinical signs and symptoms in rare diseases.xml.xml',
        'epidemiology': 'file/Epidiemology of rare diseases.xml',
        'genes': 'file/Genes associated with Rare diseases.xml',
        # Add other files...
    }

    all_data = {
        'disorders': [],
        'hpo_terms': [],
        'hpo_associations': [],
        'genes': [],
        'gene_associations': [],
        'prevalences': []
    }

    # Parse clinical signs
    if os.path.exists(xml_files['clinical_signs']):
        disorders, hpo_terms, associations = loader.parse_clinical_signs_xml(xml_files['clinical_signs'])
        all_data['disorders'].extend(disorders)
        all_data['hpo_terms'].extend(hpo_terms)
        all_data['hpo_associations'].extend(associations)

    # Parse epidemiology
    if os.path.exists(xml_files['epidemiology']):
        prevalences = loader.parse_epidemiology_xml(xml_files['epidemiology'])
        all_data['prevalences'].extend(prevalences)

    # Parse genes
    if os.path.exists(xml_files['genes']):
        genes, gene_associations = loader.parse_genes_xml(xml_files['genes'])
        all_data['genes'].extend(genes)
        all_data['gene_associations'].extend(gene_associations)

    # Insert all data
    loader.insert_data(all_data)

if __name__ == "__main__":
    main()
