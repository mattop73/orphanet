import xml.etree.ElementTree as ET
import os
from collections import defaultdict, Counter
import argparse
import sys
from pathlib import Path

class XMLAnalyzer:
    def __init__(self):
        self.element_counts = Counter()
        self.attribute_counts = defaultdict(Counter)
        self.text_content_stats = defaultdict(list)
        self.namespace_counts = Counter()
        self.max_depth = 0
        self.total_elements = 0
        self.file_size = 0
        
    def analyze_file(self, file_path):
        """Analyze a single XML file"""
        print(f"\n{'='*60}")
        print(f"ANALYZING: {file_path}")
        print(f"{'='*60}")
        
        # Get file size
        self.file_size = os.path.getsize(file_path)
        print(f"File Size: {self.file_size:,} bytes ({self.file_size/1024/1024:.2f} MB)")
        
        try:
            # Parse XML file
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Reset counters for this file
            self.element_counts.clear()
            self.attribute_counts.clear()
            self.text_content_stats.clear()
            self.namespace_counts.clear()
            self.max_depth = 0
            self.total_elements = 0
            
            # Analyze structure
            self._analyze_element(root, depth=0)
            
            # Print analysis results
            self._print_analysis_results(root)
            
        except ET.ParseError as e:
            print(f"ERROR: Failed to parse XML file - {e}")
        except Exception as e:
            print(f"ERROR: {e}")
    
    def _analyze_element(self, element, depth=0):
        """Recursively analyze XML elements"""
        self.total_elements += 1
        self.max_depth = max(self.max_depth, depth)
        
        # Count element tags
        tag = self._clean_tag(element.tag)
        self.element_counts[tag] += 1
        
        # Count namespaces
        if '}' in element.tag:
            namespace = element.tag.split('}')[0] + '}'
            self.namespace_counts[namespace] += 1
        
        # Count attributes
        for attr_name, attr_value in element.attrib.items():
            self.attribute_counts[tag][attr_name] += 1
        
        # Analyze text content
        if element.text and element.text.strip():
            text_length = len(element.text.strip())
            self.text_content_stats[tag].append(text_length)
        
        # Recursively analyze children
        for child in element:
            self._analyze_element(child, depth + 1)
    
    def _clean_tag(self, tag):
        """Remove namespace from tag for cleaner display"""
        if '}' in tag:
            return tag.split('}')[1]
        return tag
    
    def _print_analysis_results(self, root):
        """Print comprehensive analysis results"""
        
        # Basic structure info
        print(f"\n📊 BASIC STRUCTURE:")
        print(f"Root Element: {self._clean_tag(root.tag)}")
        print(f"Total Elements: {self.total_elements:,}")
        print(f"Maximum Depth: {self.max_depth}")
        print(f"Unique Element Types: {len(self.element_counts)}")
        
        # Namespaces
        if self.namespace_counts:
            print(f"\n🔗 NAMESPACES ({len(self.namespace_counts)}):")
            for ns, count in self.namespace_counts.most_common():
                print(f"  {ns:<40} {count:,} elements")
        
        # Most common elements
        print(f"\n📋 ELEMENT FREQUENCY (Top 20):")
        for element, count in self.element_counts.most_common(20):
            percentage = (count / self.total_elements) * 100
            print(f"  {element:<25} {count:,} ({percentage:.1f}%)")
        
        # Attribute analysis
        print(f"\n🏷️  ATTRIBUTES ANALYSIS:")
        elements_with_attrs = {k: v for k, v in self.attribute_counts.items() if v}
        if elements_with_attrs:
            for element in sorted(elements_with_attrs.keys())[:10]:  # Show top 10
                attrs = self.attribute_counts[element]
                print(f"  {element}:")
                for attr, count in attrs.most_common(5):  # Top 5 attrs per element
                    print(f"    └─ {attr}: {count:,} occurrences")
        else:
            print("  No attributes found")
        
        # Text content analysis
        print(f"\n📝 TEXT CONTENT ANALYSIS:")
        elements_with_text = {k: v for k, v in self.text_content_stats.items() if v}
        if elements_with_text:
            for element in sorted(elements_with_text.keys())[:10]:  # Show top 10
                lengths = self.text_content_stats[element]
                avg_length = sum(lengths) / len(lengths)
                max_length = max(lengths)
                min_length = min(lengths)
                print(f"  {element}: {len(lengths):,} elements with text")
                print(f"    └─ Avg length: {avg_length:.1f} chars, Range: {min_length}-{max_length}")
        else:
            print("  No text content found")
        
        # Structure hierarchy (sample)
        print(f"\n🌳 STRUCTURE SAMPLE:")
        self._print_structure_sample(root, max_depth=3)
    
    def _print_structure_sample(self, element, depth=0, max_depth=3, prefix=""):
        """Print a sample of the XML structure"""
        if depth > max_depth:
            return
        
        tag = self._clean_tag(element.tag)
        attrs_info = f" [{len(element.attrib)} attrs]" if element.attrib else ""
        text_info = " [has text]" if element.text and element.text.strip() else ""
        
        print(f"{prefix}{tag}{attrs_info}{text_info}")
        
        # Show only first few children to avoid overwhelming output
        children = list(element)[:5]  # First 5 children
        for i, child in enumerate(children):
            is_last = (i == len(children) - 1)
            child_prefix = prefix + ("└── " if is_last else "├── ")
            self._print_structure_sample(child, depth + 1, max_depth, 
                                       prefix + ("    " if is_last else "│   "))
        
        if len(element) > 5:
            print(f"{prefix}    ... and {len(element) - 5} more children")

def analyze_multiple_files(file_paths):
    """Analyze multiple XML files and provide summary"""
    analyzer = XMLAnalyzer()
    
    print("🔍 XML FILE ANALYZER")
    print("=" * 60)
    
    valid_files = []
    for file_path in file_paths:
        if os.path.exists(file_path) and file_path.lower().endswith('.xml'):
            valid_files.append(file_path)
        else:
            print(f"⚠️  Skipping: {file_path} (not found or not XML)")
    
    if not valid_files:
        print("❌ No valid XML files found!")
        return
    
    print(f"📁 Found {len(valid_files)} XML file(s) to analyze")
    
    # Analyze each file
    for file_path in valid_files:
        analyzer.analyze_file(file_path)
    
    print(f"\n✅ Analysis complete!")

def main():
    parser = argparse.ArgumentParser(description='Analyze XML file structure and content')
    parser.add_argument('files', nargs='+', help='XML file paths to analyze')
    parser.add_argument('--directory', '-d', help='Analyze all XML files in directory')
    
    args = parser.parse_args()
    
    file_paths = []
    
    # Handle directory option
    if args.directory:
        directory = Path(args.directory)
        if directory.exists() and directory.is_dir():
            xml_files = list(directory.glob('*.xml'))
            file_paths.extend([str(f) for f in xml_files])
            print(f"Found {len(xml_files)} XML files in directory: {directory}")
        else:
            print(f"Directory not found: {args.directory}")
            return
    
    # Add individual files
    file_paths.extend(args.files)
    
    if not file_paths:
        print("No files specified. Usage examples:")
        print("  python xml_analyzer.py file1.xml file2.xml")
        print("  python xml_analyzer.py -d /path/to/xml/directory")
        return
    
    analyze_multiple_files(file_paths)

if __name__ == "__main__":
    # If no command line args, show usage
    if len(sys.argv) == 1:
        print("🔍 XML File Analyzer")
        print("=" * 40)
        print("Usage examples:")
        print("  python xml_analyzer.py file1.xml file2.xml")
        print("  python xml_analyzer.py -d /path/to/xml/directory")
        print("  python xml_analyzer.py *.xml")
        print("\nThis script analyzes XML files and shows:")
        print("• File structure and hierarchy")
        print("• Element frequency and distribution")
        print("• Namespace usage")
        print("• Attribute analysis")
        print("• Text content statistics")
        print("• Visual structure sample")
    else:
        main()
