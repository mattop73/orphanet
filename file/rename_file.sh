#!/bin/bash

# Script to rename XML files by removing spaces and replacing with underscores
# Usage: ./rename_xml_files.sh

echo "🔄 Renaming XML files to remove spaces..."

# Function to rename file if it exists
rename_if_exists() {
    local old_name="$1"
    local new_name="$2"

    if [ -f "$old_name" ]; then
        mv "$old_name" "$new_name"
        echo "✅ Renamed: '$old_name' → '$new_name'"
    else
        echo "⚠️  File not found: '$old_name'"
    fi
}

# Rename each file
rename_if_exists "Clinical signs and symptoms in rare diseases.xml" "clinical_signs_and_symptoms_in_rare_diseases.xml"
rename_if_exists "Epidiemology of rare diseases.xml" "epidemiology_of_rare_diseases.xml"
rename_if_exists "Genes associated with Rare diseases.xml" "genes_associated_with_rare_diseases.xml"
rename_if_exists "Linearisation of rare diseases.xml" "linearisation_of_rare_diseases.xml"
rename_if_exists "natural history of rare diseases.xml" "natural_history_of_rare_diseases.xml"
rename_if_exists "Rare disease alignment with terminology.xml" "rare_disease_alignment_with_terminology.xml"
rename_if_exists "Rare diseases and functional consequences.xml" "rare_diseases_and_functional_consequences.xml"

echo ""
echo "🎉 Renaming complete!"
echo ""
echo "📋 New file names:"
ls -la *.xml | grep -E "(clinical_signs|epidemiology|genes_associated|linearisation|natural_history|rare_disease)" | awk '{print "  " $9}'

echo ""
echo "💡 You can now use these file paths in your Python scripts:"
echo ""
echo "xml_files = ["
echo "    'clinical_signs_and_symptoms_in_rare_diseases.xml',"
echo "    'epidemiology_of_rare_diseases.xml',"
echo "    'genes_associated_with_rare_diseases.xml',"
echo "    'linearisation_of_rare_diseases.xml',"
echo "    'natural_history_of_rare_diseases.xml',"
echo "    'rare_disease_alignment_with_terminology.xml',"
echo "    'rare_diseases_and_functional_consequences.xml'"
echo "]"
