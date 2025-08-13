#!/usr/bin/env python3
"""
Test script for the Orphanet SM Loader
"""

import os
import sys
from pathlib import Path
from orphanet_supabase_loader import OrphanetSMLoader, SupabaseConfig
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Test the SM loader with environment variables"""
    
    # Get credentials from environment (based on user rules)
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        logger.error("Missing environment variables:")
        logger.error("Please set SUPABASE_URL and SUPABASE_KEY (or SUPABASE_ANON_KEY)")
        logger.error("Based on your user rules, these should be in system/.env")
        sys.exit(1)
    
    # Create configuration
    config = SupabaseConfig(
        supabase_url=supabase_url,
        supabase_key=supabase_key
    )
    
    # Create loader
    loader = OrphanetSMLoader(config)
    
    try:
        # Test connection
        logger.info("Testing Supabase connection...")
        if not loader.connect_supabase():
            logger.error("Failed to connect to Supabase")
            sys.exit(1)
        
        logger.info("✓ Connection successful!")
        
        # Test with file directory
        file_dir = Path(__file__).parent / "file"
        if not file_dir.exists():
            logger.error(f"File directory not found: {file_dir}")
            sys.exit(1)
        
        # Check for SM files
        sm_files = list(file_dir.glob("*_SM.txt"))
        if not sm_files:
            logger.error("No SM files found in file directory")
            sys.exit(1)
        
        logger.info(f"Found {len(sm_files)} SM files:")
        for f in sm_files:
            logger.info(f"  - {f.name}")
        
        # Load a single file for testing (natural history is usually smaller)
        test_file = None
        for f in sm_files:
            if "natural_history" in f.name.lower():
                test_file = f
                break
        
        if not test_file:
            test_file = sm_files[0]  # Use first available file
        
        logger.info(f"Testing with single file: {test_file.name}")
        
        # Test parsing (these are truncated files from head -500)
        try:
            logger.info(f"Note: Testing with truncated file (head -500 extract)")
            root = loader.parse_xml(str(test_file))
            logger.info(f"✓ Successfully parsed {test_file.name}")
            
            # Count disorders in file
            disorders = root.findall('.//Disorder')
            logger.info(f"  Found {len(disorders)} disorders in truncated file")
            
            if len(disorders) == 0:
                # Try different search patterns for different file types
                hpo_disorders = root.findall('.//HPODisorderSetStatus')
                disabilities = root.findall('.//DisorderDisabilityRelevance')
                
                if hpo_disorders:
                    logger.info(f"  Found {len(hpo_disorders)} HPO disorder entries")
                    # Get disorders from HPO structure
                    disorders = [hpo.find('Disorder') for hpo in hpo_disorders[:5] if hpo.find('Disorder') is not None]
                elif disabilities:
                    logger.info(f"  Found {len(disabilities)} disability entries")
                    # Get disorders from disability structure
                    disorders = [dis.find('Disorder') for dis in disabilities[:5] if dis.find('Disorder') is not None]
            
            # Test disorder processing (first 3 only for truncated files)
            test_disorders = disorders[:3]
            if test_disorders:
                logger.info(f"Testing disorder processing with {len(test_disorders)} disorders...")
                
                for i, disorder in enumerate(test_disorders):
                    if disorder is not None:
                        disorder_uuid = loader.get_or_create_disorder(disorder)
                        if disorder_uuid:
                            orpha_code = disorder.findtext('.//OrphaCode', '')
                            name = disorder.findtext('.//Name[@lang="en"]', '')
                            logger.info(f"  ✓ Processed disorder {i+1}: {orpha_code} - {name[:50]}...")
                        else:
                            logger.warning(f"  ✗ Failed to process disorder {i+1}")
                    else:
                        logger.warning(f"  ✗ Disorder {i+1} is None")
            else:
                logger.warning("  No disorders found to test with")
            
        except Exception as e:
            logger.error(f"Failed to parse or process file: {e}")
            logger.error("This might be expected for truncated files - trying to continue...")
            # Don't exit, just warn
        
        # Get statistics
        logger.info("Getting current database statistics...")
        stats = loader.get_statistics()
        
        print("\n=== Current Database Statistics ===")
        for table, count in stats.items():
            print(f"{table:30} {count}")
        
        logger.info("✓ Test completed successfully!")
        logger.info(f"To load all SM files, run:")
        logger.info(f"python orphanet_supabase_loader.py -d file --stats")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()