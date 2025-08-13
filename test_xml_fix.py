#!/usr/bin/env python3
"""
Test script to verify XML fixing functionality for truncated SM files
"""

import xml.etree.ElementTree as ET
from orphanet_supabase_loader import OrphanetSMLoader, SupabaseConfig
import os
from pathlib import Path

def test_xml_fix():
    """Test the XML fixing functionality"""
    
    # Create a dummy loader just for the XML fixing function
    config = SupabaseConfig(
        supabase_url="dummy",
        supabase_key="dummy"
    )
    loader = OrphanetSMLoader(config)
    
    # Test with one of the SM files
    file_dir = Path(__file__).parent / "file"
    test_file = file_dir / "natural_history_of_rare_diseases_SM.txt"
    
    if not test_file.exists():
        print(f"Test file not found: {test_file}")
        return
    
    print(f"Testing XML fix with: {test_file.name}")
    
    # Read original content
    with open(test_file, 'r', encoding='iso-8859-1') as f:
        original_content = f.read()
    
    print(f"Original file length: {len(original_content)} characters")
    print(f"Original file ends with: ...{repr(original_content[-50:])}")
    
    # Try to fix it
    try:
        fixed_content = loader.fix_truncated_xml(str(test_file))
        print(f"Fixed file length: {len(fixed_content)} characters")
        print(f"Fixed file ends with: ...{repr(fixed_content[-100:])}")
        
        # Try to parse the fixed XML
        root = ET.fromstring(fixed_content)
        print(f"✓ Successfully parsed fixed XML!")
        
        # Count elements
        disorders = root.findall('.//Disorder')
        print(f"Found {len(disorders)} disorders in fixed XML")
        
        # Show first disorder info
        if disorders:
            first_disorder = disorders[0]
            orpha_code = first_disorder.findtext('.//OrphaCode', '')
            name = first_disorder.findtext('.//Name[@lang="en"]', '')
            print(f"First disorder: {orpha_code} - {name}")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to fix/parse XML: {e}")
        return False

def test_all_sm_files():
    """Test XML fixing with all SM files"""
    
    config = SupabaseConfig(
        supabase_url="dummy", 
        supabase_key="dummy"
    )
    loader = OrphanetSMLoader(config)
    
    file_dir = Path(__file__).parent / "file"
    sm_files = list(file_dir.glob("*_SM.txt"))
    
    print(f"\nTesting XML fixing with all {len(sm_files)} SM files:")
    print("=" * 60)
    
    results = {}
    
    for sm_file in sm_files:
        print(f"\nTesting: {sm_file.name}")
        try:
            fixed_content = loader.fix_truncated_xml(str(sm_file))
            root = ET.fromstring(fixed_content)
            
            # Count different types of elements
            disorders = root.findall('.//Disorder')
            hpo_disorders = root.findall('.//HPODisorderSetStatus')
            disabilities = root.findall('.//DisorderDisabilityRelevance')
            
            results[sm_file.name] = {
                'success': True,
                'disorders': len(disorders),
                'hpo_disorders': len(hpo_disorders),
                'disabilities': len(disabilities)
            }
            
            print(f"  ✓ Success - Disorders: {len(disorders)}, HPO: {len(hpo_disorders)}, Disabilities: {len(disabilities)}")
            
        except Exception as e:
            results[sm_file.name] = {
                'success': False,
                'error': str(e)
            }
            print(f"  ✗ Failed: {e}")
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY:")
    successful = sum(1 for r in results.values() if r['success'])
    print(f"Successfully fixed: {successful}/{len(sm_files)} files")
    
    for filename, result in results.items():
        if result['success']:
            print(f"  ✓ {filename}")
        else:
            print(f"  ✗ {filename}: {result['error']}")

if __name__ == "__main__":
    print("Testing XML fixing functionality for truncated SM files")
    print("=" * 60)
    
    # Test single file first
    if test_xml_fix():
        # Test all files
        test_all_sm_files()
    else:
        print("Single file test failed, skipping bulk test")