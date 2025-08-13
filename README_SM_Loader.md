# Orphanet SM Files Loader

This loader is designed to efficiently load Orphanet XML subset files (`*_SM.txt`) into a Supabase database using the anonymous key.

## Features

- **Fast Loading**: Uses SM (subset) files for quick data loading
- **Supabase Integration**: Uses anonymous key for secure client-side operations
- **Batch Processing**: Processes data in batches for optimal performance
- **Error Handling**: Robust error handling with detailed logging
- **Caching**: Intelligent caching to avoid duplicate lookups
- **Statistics**: Provides loading statistics and progress tracking

## Quick Start

### 1. Setup Environment Variables

Run the setup script to configure your Supabase credentials:

```bash
python setup_env.py
```

This will create `system/.env` with your Supabase URL and anonymous key.

### 2. Test Connection

Test that everything is working:

```bash
python test_sm_loader.py
```

### 3. Load All SM Files

Load all SM files from the `file/` directory:

```bash
python orphanet_supabase_loader.py -d file --stats
```

## Command Line Options

```bash
python orphanet_supabase_loader.py [options]

Options:
  -d, --directory DIR    Directory containing SM files (required)
  -u, --url URL         Supabase URL (or use SUPABASE_URL env var)
  -k, --key KEY         Supabase anonymous key (or use SUPABASE_KEY env var)
  -s, --stats           Show statistics after loading
  -h, --help           Show help message
```

## Supported File Types

The loader automatically detects and processes these SM file types:

- `natural_history_*_SM.txt` - Age of onset and inheritance patterns
- `genes_associated_*_SM.txt` - Gene associations and external references
- `clinical_signs_*_SM.txt` - HPO terms and clinical manifestations
- `epidemiology_*_SM.txt` - Prevalence and epidemiological data
- `linearisation_*_SM.txt` - Disease classifications and hierarchies
- `alignment_with_terminology_*_SM.txt` - External references and mappings
- `functional_consequences_*_SM.txt` - Disabilities and functional impacts

## Database Tables

The loader populates these Supabase tables:

### Core Tables
- `disorders` - Main disorder information
- `disorder_synonyms` - Alternative names for disorders

### Natural History
- `age_of_onset` - Age of onset information
- `inheritance_types` - Inheritance patterns

### Genetics
- `genes` - Gene information
- `gene_external_refs` - External gene references
- `disorder_gene_associations` - Gene-disorder relationships

### Clinical Signs
- `hpo_terms` - HPO (Human Phenotype Ontology) terms
- `disorder_hpo_associations` - Clinical sign associations

### Epidemiology
- `prevalence_data` - Prevalence and epidemiological information

### Classifications
- `disorder_classifications` - Disease hierarchies and classifications
- `external_references` - External database mappings
- `disorder_texts` - Disorder descriptions and definitions

### Functional Impact
- `disabilities` - Disability types
- `disorder_disability_associations` - Disability associations

### Metadata
- `import_metadata` - Import tracking and statistics

## Performance Features

### Batch Processing
- Processes data in configurable batches (50-100 records)
- Reduces API calls and improves performance
- Handles large datasets efficiently

### Intelligent Caching
- Caches disorder, gene, HPO term, and disability UUIDs
- Prevents duplicate lookups within a session
- Significantly speeds up processing

### Error Recovery
- Continues processing even if individual records fail
- Logs detailed error information
- Records import status in metadata table

## Environment Variables

Create `system/.env` with these variables:

```env
# Required
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anonymous-key

# Optional (alternative names)
SUPABASE_ANON_KEY=your-anonymous-key
ANTHROPIC_API_KEY=your-anthropic-key
```

## Dependencies

Install required packages:

```bash
pip install supabase python-dotenv tqdm
```

## Logging

The loader provides detailed logging:
- INFO: Progress updates and statistics
- WARNING: Non-critical issues (duplicate data, etc.)
- ERROR: Critical failures that stop processing

## Example Usage

```python
from orphanet_supabase_loader import OrphanetSMLoader, SupabaseConfig
import os

# Create configuration
config = SupabaseConfig(
    supabase_url=os.getenv('SUPABASE_URL'),
    supabase_key=os.getenv('SUPABASE_KEY')
)

# Create and use loader
loader = OrphanetSMLoader(config)
loader.connect_supabase()
loader.load_all_sm_files('file/')

# Get statistics
stats = loader.get_statistics()
print(f"Loaded {stats['disorders']} disorders")
```

## Troubleshooting

### Connection Issues
- Verify your Supabase URL and key are correct
- Check that your Supabase project is active
- Ensure network connectivity

### Permission Issues
- Make sure you're using the correct anonymous key
- Verify your Supabase RLS (Row Level Security) policies
- Check table permissions in your Supabase dashboard

### File Issues
- Ensure SM files are in the specified directory
- Check that files are valid XML format
- Verify file permissions are readable

### Performance Issues
- Consider processing files individually for very large datasets
- Monitor your Supabase usage limits
- Adjust batch sizes if needed

## Database Schema

The loader expects tables to already exist in your Supabase database. If you need to create the schema, use the appropriate SQL scripts or Supabase migrations.

## Contributing

This loader follows Python best practices:
- Type hints for all functions
- Comprehensive error handling
- Detailed logging
- Modular design
- Google-style docstrings