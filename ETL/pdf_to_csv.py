import os
import re
import pandas as pd
from typing import List, Tuple, Dict, Optional

# =====================================================
# CONFIGURATION
# =====================================================

# Constants
INPUT_DIR = "DATA/SOURCE DATA/TXT/"
OUTPUT_DIR = "DATA/CLEANED DATA (CSV)/"

# File mappings
INPUT_FILES = {
    "CONTRACTED-FACILITES-REHABILITATION": "CONTRACTED-FACILITES-REHABILITATION.pdf.txt",
    "CONTRACTED-FACILITIES-CLINICAL-FACILITIES": "CONTRACTED-FACILITIES-CLINICAL-FACILITIES.pdf.txt",
    "CONTRACTED-FACILITIES-GOVERNMENT-OF-KENYA": "CONTRACTED-FACILITIES-GOVERNMENT-OF-KENYA.pdf.txt",
    "CONTRACTED-FACILITIES-INSTITUTIONAL": "CONTRACTED-FACILITIES-INSTITUTIONAL.pdf.txt",
    "CONTRACTED-FACILITIES-NGOs": "CONTRACTED-FACILITIES-NGOs.pdf.txt",
    "CONTRACTED-FACILITIES-PRIVATE": "CONTRACTED-FACILITIES-PRIVATE.pdf.txt",
    "CONTRACTED-FACILITIES-COMMUNITY-HOSP": "CONTRACTED-FACILITIES-COMMUNITY-HOSP.pdf.txt",
    "CONTRACTED-FACILITIES-FBOs": "CONTRACTED-FACILITIES-FBOs.pdf.txt",
    "CONTRACTED-FACILITIES-COUNTY-GOVT": "CONTRACTED-FACILITIES-COUNTY-GOVT.pdf.txt",
    "SHA-FACILITIES-PAYMENT-ANALYSIS": "SHA-FACILITIES-PAYMENT-ANALYSIS.pdf.txt"
}

# County list with standardized names and common variations
COUNTY_STANDARDIZATION = {
    "BARINGO": ["BARINGO"],
    "BOMET": ["BOMET"],
    "BUNGOMA": ["BUNGOMA"],
    "BUSIA": ["BUSIA"],
    "ELGEYO-MARAKWET": ["ELGEYO-MARAKWET", "ELGEYO MARAKWET"],
    "EMBU": ["EMBU"],
    "GARISSA": ["GARISSA"],
    "HOMA BAY": ["HOMA BAY", "HOMA-BAY"],
    "ISIOLO": ["ISIOLO"],
    "KAJIADO": ["KAJIADO"],
    "KAKAMEGA": ["KAKAMEGA"],
    "KERICHO": ["KERICHO"],
    "KIAMBU": ["KIAMBU"],
    "KILIFI": ["KILIFI"],
    "KIRINYAGA": ["KIRINYAGA"],
    "KISII": ["KISII"],
    "KISUMU": ["KISUMU"],
    "KITUI": ["KITUI"],
    "KWALE": ["KWALE"],
    "LAIKIPIA": ["LAIKIPIA"],
    "LAMU": ["LAMU"],
    "MACHAKOS": ["MACHAKOS"],
    "MAKUENI": ["MAKUENI"],
    "MANDERA": ["MANDERA"],
    "MARSABIT": ["MARSABIT"],
    "MERU": ["MERU"],
    "MIGORI": ["MIGORI"],
    "MOMBASA": ["MOMBASA"],
    "MURANGA": ["MURANG'A", "MURANGA"],
    "NAIROBI": ["NAIROBI"],
    "NAKURU": ["NAKURU"],
    "NANDI": ["NANDI"],
    "NAROK": ["NAROK"],
    "NYAMIRA": ["NYAMIRA"],
    "NYANDARUA": ["NYANDARUA"],
    "NYERI": ["NYERI"],
    "SAMBURU": ["SAMBURU"],
    "SIAYA": ["SIAYA"],
    "TANA RIVER": ["TANA RIVER", "TANA-RIVER"],
    "TAITA-TAVETA": ["TAITA-TAVETA", "TAITA TAVETA"],
    "THARAKA-NITHI": ["THARAKA-NITHI", "THARAKA NITHI"],
    "TRANS-NZOIA": ["TRANS-NZOIA", "TRANS NZOIA"],
    "TURKANA": ["TURKANA"],
    "UASIN GISHU": ["UASIN GISHU", "UASIN-GISHU"],
    "VIHIGA": ["VIHIGA"],
    "WAJIR": ["WAJIR"],
    "WEST POKOT": ["WEST POKOT", "WEST-POKOT"]
}

# Create mapping from variation to standardized name
ALL_COUNTY_VARIATIONS = []
VARIATION_TO_STANDARD = {}
for standard_name, variations in COUNTY_STANDARDIZATION.items():
    ALL_COUNTY_VARIATIONS.extend(variations)
    for variation in variations:
        VARIATION_TO_STANDARD[variation.upper()] = standard_name

# Pre-compiled regex patterns
PATTERN_UNIVERSAL = re.compile(
    r"(CN-\d+)\s+(.+?)\s+"
    r"(COUNTY GOVERNMENT|GOVERNMENT OF KENYA \(GOK\)|REHABILITATION|FAITH BASED ORGANIZATION \(FBO\)|Private|Community|NGO - \(Non Government Organization\)|Institutional)"
    r"\s+(LEVEL\s*\d+[A-Z]?)",
    re.IGNORECASE
)

PATTERN_SIMPLE = re.compile(
    r"(CN-\d+)\s+(.+?)\s+(LEVEL\s*\d+[A-Z]?)",
    re.IGNORECASE
)

PATTERN_PAYMENT = re.compile(
    r'^(\d+)\s+'                           # No
    r'(.+?)\s+'                            # Vendor Name
    r'(\d+)\s+'                            # No2
    r'([A-Z]\s*\d+[A-Z]?)\s+'              # Level
    r'([A-Z][A-Z\s\-]*?)\s+'               # County
    r'((?:[\d,]+\s+){7})'                  # 7 date amounts
    r'([\d,]+)\s+'                         # Grand Total
    r'([\d,]+%)\s*$',                      # Percentage
    re.MULTILINE
)

FACILITY_TYPE_MAP = {
    "CLINICAL": "CLINICAL",
    "REHABILITATION": "REHABILITATION", 
    "NGO": "NGO",
    "INSTITUTIONAL": "INSTITUTIONAL"
}

# =====================================================
# UTILITY FUNCTIONS
# =====================================================

def read_file_safely(filepath: str) -> Optional[str]:
    """Read file with error handling."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as file:
            return file.read()
    except:
        return None

def preprocess_text(text: str) -> str:
    """Clean and preprocess text data."""
    text = re.sub(r"\n(?!CN-)", " ", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()

def standardize_county_name(county_variation: str) -> str:
    """Convert county variation to standardized name."""
    standardized = VARIATION_TO_STANDARD.get(county_variation.upper())
    return standardized if standardized else "UNKNOWN"

def split_facility_and_county(text: str) -> Tuple[str, str]:
    """Split facility name and county."""
    words = text.split()
    
    # Try from the end
    for i in range(len(words), 0, -1):
        for j in range(1, min(4, i + 1)):
            possible_county = " ".join(words[i-j:i])
            if possible_county.upper() in ALL_COUNTY_VARIATIONS:
                facility_name = " ".join(words[:i-j])
                return facility_name, standardize_county_name(possible_county)
    
    # Try from beginning
    for i in range(len(words)):
        for j in range(1, min(4, len(words) - i + 1)):
            possible_county = " ".join(words[i:i+j])
            if possible_county.upper() in ALL_COUNTY_VARIATIONS:
                facility_name = " ".join(words[:i])
                return facility_name, standardize_county_name(possible_county)
    
    return text, "UNKNOWN"

def detect_facility_type(filename: str) -> str:
    """Detect facility type from filename."""
    filename_upper = filename.upper()
    for key in FACILITY_TYPE_MAP:
        if key in filename_upper:
            return FACILITY_TYPE_MAP[key]
    return "UNKNOWN"

# =====================================================
# MAIN PROCESSING FUNCTIONS
# =====================================================

def process_facility_file(file_key: str, filepath: str) -> bool:
    """Process a single facility file."""
    print(f"Processing: {file_key}")
    
    text_content = read_file_safely(filepath)
    if text_content is None:
        return False
        
    processed_text = preprocess_text(text_content)
    
    # Try universal pattern first
    universal_matches = PATTERN_UNIVERSAL.findall(processed_text)
    cleaned_data = []
    
    if universal_matches:
        print(f"  Found {len(universal_matches)} matches using universal pattern")
        for app_no, facility_blob, ftype, level in universal_matches:
            facility_name, county = split_facility_and_county(facility_blob)
            cleaned_data.append([
                app_no.strip(), 
                facility_name.strip(), 
                county, 
                ftype.upper().strip(), 
                level.upper().strip()
            ])
    else:
        print("  Using simple pattern")
        simple_matches = PATTERN_SIMPLE.findall(processed_text)
        print(f"  Found {len(simple_matches)} matches using simple pattern")
        
        default_type = detect_facility_type(file_key)
        for app_no, facility_blob, level in simple_matches:
            facility_name, county = split_facility_and_county(facility_blob)
            cleaned_data.append([
                app_no.strip(),
                facility_name.strip(), 
                county,
                default_type,
                level.upper().strip()
            ])
    
    if cleaned_data:
        df = pd.DataFrame(cleaned_data, columns=[
            "Application Number", "Facility Name", "County", "Facility Type", "Keph Level"
        ])
        
        output_path = os.path.join(OUTPUT_DIR, f"{file_key}.csv")
        df.to_csv(output_path, index=False)
        print(f"  Saved {len(df)} records -> {file_key}.csv")
        return True
    else:
        print(f"  No data extracted from {file_key}")
        return False

def process_payment_analysis() -> bool:
    """Process payment analysis file."""
    print("Processing PAYMENT ANALYSIS...")
    
    pay_file_key = "SHA-FACILITIES-PAYMENT-ANALYSIS"
    pay_filepath = os.path.join(INPUT_DIR, INPUT_FILES[pay_file_key])
    
    text_content = read_file_safely(pay_filepath)
    if text_content is None:
        return False
    
    rows = []
    date_columns = ['03-Dec', '05-Dec', '11-Dec', '18-Dec', '23-Dec', '09-Jan', '30-Jan', '03-Feb']
    
    for line in text_content.split("\n"):
        line = line.strip()
        if not line or ('No' in line and 'Vendor' in line and 'Level' in line):
            continue
        
        line = re.sub(r'\s{2,}', ' ', line)
        match = PATTERN_PAYMENT.match(line)
        
        if match:
            amounts_text = match.group(6).strip()
            amount_list = amounts_text.split()
            
            # Handle case where amounts aren't properly split
            if len(amount_list) != 8:
                amount_list = re.findall(r'[\d,]+', amounts_text)
            
            row_data = {
                'No': match.group(1),
                'Vendor': match.group(2).strip(),
                'No2': match.group(3),
                'Level': match.group(4).strip(),
                'County': standardize_county_name(match.group(5).strip()),
                'Grand_Total': match.group(7).replace(',', ''),
                'Percentage': match.group(8).replace('%', '')
            }
            
            # Add date columns
            for i, date_col in enumerate(date_columns):
                if i < len(amount_list):
                    row_data[date_col] = amount_list[i].replace(',', '')
                else:
                    row_data[date_col] = ''
            
            rows.append(row_data)
    
    if rows:
        df_pay = pd.DataFrame(rows)
        
        # Reorder columns
        column_order = ['No', 'Vendor', 'No2', 'Level', 'County'] + date_columns + ['Grand_Total', 'Percentage']
        column_order = [col for col in column_order if col in df_pay.columns]
        df_pay = df_pay.reindex(columns=column_order)
        
        # Convert numeric columns
        for col in date_columns + ['Grand_Total', 'Percentage']:
            if col in df_pay.columns:
                df_pay[col] = df_pay[col].replace('', '0')
                df_pay[col] = df_pay[col].astype(str).str.replace(',', '')
                df_pay[col] = pd.to_numeric(df_pay[col], errors='coerce')
        
        output_path = os.path.join(OUTPUT_DIR, f"{pay_file_key}.csv")
        df_pay.to_csv(output_path, index=False)
        print(f"  Saved {len(df_pay)} payment rows -> {pay_file_key}.csv")
        return True
    else:
        print("  No payment data extracted")
        return False

def main():
    """Main execution function."""
    print("Starting data processing pipeline...")
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Process facility files
    success_count = 0
    total_files = len(INPUT_FILES)
    
    for file_key, filename in INPUT_FILES.items():
        filepath = os.path.join(INPUT_DIR, filename)
        if process_facility_file(file_key, filepath):
            success_count += 1
    
    # Process payment analysis separately
    if process_payment_analysis():
        success_count += 1
    
    print(f"\nProcessing complete: {success_count}/{total_files} files successful")
    print(f"Output directory: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()