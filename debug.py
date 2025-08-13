import xml.etree.ElementTree as ET
import os
import logging
from supabase import create_client, Client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # YOUR CREDENTIALS HERE
    SUPABASE_URL = "https://ecrcdeztnbciybqkwkpf.supabase.co"  # Your Supabase project URL
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImVjcmNkZXp0bmJjaXlicWt3a3BmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ5NDIwOTQsImV4cCI6MjA3MDUxODA5NH0.TPT6CdwI3lgBeh-V_X-a8_H4m3YFK0lLg31eWM0woho"

    # Initialize Supabase
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    logger.info("Supabase client created")

    # Test with one small insert
    try:
        test_disorder = {
            'orpha_code': 'TEST123',
            'name': 'Test Disorder for Connection',
            'expert_link': 'http://test.com'
        }

        result = supabase.table('disorders').insert([test_disorder]).execute()
        logger.info(f"✅ Test insert successful: {result}")

        # Now try to read it back
        result = supabase.table('disorders').select("*").eq('orpha_code', 'TEST123').execute()
        logger.info(f"✅ Test read successful: {result.data}")

        # Clean up
        supabase.table('disorders').delete().eq('orpha_code', 'TEST123').execute()
        logger.info("✅ Test cleanup successful")

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        return

    # Find XML files
    xml_files = []
    for file in os.listdir('./file/'):
        if file.endswith('.xml'):
            xml_files.append(file)

    logger.info(f"Found XML files: {xml_files}")

    # Process first XML file found
    if xml_files:
        xml_file = xml_files[0]
        logger.info(f"Processing: {xml_file}")

        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()

            disorders = []
            count = 0

            # Parse first 10 disorders only
            for disorder_elem in root.findall('.//Disorder'):
                if count >= 10:
                    break

                orpha_code_elem = disorder_elem.find('OrphaCode')
                name_elem = disorder_elem.find('Name')

                if orpha_code_elem is not None and name_elem is not None:
                    disorders.append({
                        'orpha_code': orpha_code_elem.text,
                        'name': name_elem.text[:150],
                        'expert_link': None
                    })
                    count += 1

            logger.info(f"Parsed {len(disorders)} disorders")

            # Insert disorders
            if disorders:
                result = supabase.table('disorders').upsert(disorders).execute()
                logger.info(f"✅ Inserted {len(disorders)} disorders successfully")

                # Verify insertion
                result = supabase.table('disorders').select("*").execute()
                logger.info(f"✅ Total disorders in database: {len(result.data)}")

        except Exception as e:
            logger.error(f"❌ XML processing failed: {e}")

    else:
        logger.warning("No XML files found in current directory")

if __name__ == "__main__":
    main()
