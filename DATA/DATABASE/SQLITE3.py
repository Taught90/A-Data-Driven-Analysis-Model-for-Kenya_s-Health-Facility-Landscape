import pandas as pd
import sqlite3
import os

# First, ensure the database connection is established
def setup_database():
    db_path = 'DATA/DATABASE/SOCIAL HEALTH LICENSED HEALTH FACILITIES AND FUNDS.db'
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    try:
        connection = sqlite3.connect(db_path)
        print(f"Successfully connected to database: {db_path}")
        return connection
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

# Connect to database
connection = setup_database()

if connection is None:
    print("Failed to establish database connection. Exiting.")
    exit()

# CSV files mapping
csv_files = {
    "CONTRACTED-FACILITES-REHABILITATION.csv": 'CONTRACTED-FACILITES-REHABILITATION',
    'CONTRACTED-FACILITIES-COUNTY-GOVT.csv': 'CONTRACTED-FACILITIES-COUNTY-GOVT.csv',
    'CONTRACTED-FACILITIES-GOVERNMENT-OF-KENYA.csv': 'CONTRACTED-FACILITIES-GOVERNMENT-OF-KENYA',
    'CONTRACTED-FACILITIES-INSTITUTIONAL.csv': 'CONTRACTED-FACILITIES-INSTITUTIONAL',
    'CONTRACTED-FACILITIES-NGOs.csv': 'CONTRACTED-FACILITIES-NGOs',
    'CONTRACTED-FACILITIES-PRIVATE.csv': 'CONTRACTED-FACILITIES-PRIVATE',
    'CONTRACTED-FACILITIES-COMMUNITY-HOSP.csv': "CONTRACTED-FACILITIES-COMMUNITY-HOSP",
    'CONTRACTED-FACILITIES-FBOs.csv' : 'CONTRACTED-FACILITIES-FBOs',
    'SHA-FACILITIES-PAYMENT-ANALYSIS.csv' : 'SHA-FACILITIES-PAYMENT-ANALYSIS'
}

# Read and add each CSV file to the database
for file, table_name in csv_files.items():
    csv_file_path = 'DATA/CLEANED DATA (CSV)/' + file
    try:
        # Read CSV file
        df = pd.read_csv(csv_file_path)
        print(f"Successfully read {file} with {len(df)} rows and {len(df.columns)} columns")
        
        # Display basic info about the dataframe
        print(f"Columns: {df.columns.tolist()}")
        print(f"First few rows:")
        print(df.head(2))  # Show just 2 rows for preview
        print("-" * 50)
        
        # Add to SQLite database
        df.to_sql(table_name, connection, if_exists='replace', index=False)
        print(f"Successfully added {table_name} to database with {len(df)} rows")
        
    except FileNotFoundError:
        print(f"Error: File not found - {csv_file_path}")
    except pd.errors.EmptyDataError:
        print(f"Error: File is empty - {csv_file_path}")
    except Exception as e:
        print(f"Error processing {file}: {e}")

# Verify the tables were created
try:
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("\nTables in database:")
    for table in tables:
        print(f" - {table[0]}")
except Exception as e:
    print(f"Error listing tables: {e}")

# Close connection
connection.close()
print("\nDatabase connection closed.")