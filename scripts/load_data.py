import sqlite3
import pandas as pd
import os

data_folder = os.path.join(os.path.dirname(__file__), '..', 'data')

# Database connection (creates if doesn't exist)
db_path = os.path.join(data_folder, 'cms_healthcare.db')
conn = sqlite3.connect(db_path)

datasets = {
    "benefits-and-cost-sharing-puf.csv": "benefits_and_cost_sharing",
    "business-rules-puf.csv": "business_rules",
    "network-puf.csv": "network-puf",
    "plan-attributes-puf.csv": "plan-attributes-puf",
    "plan-id-crosswalk-puf.csv": "plan-id-crosswalk-puf",
    "rate-puf.csv": "rate-puf",
    "service-area-puf.csv": "service-area-puf",
    "Transparency-2025-Ind-SADP.csv": "Transparency-2025-Ind-SADP",
    "Transparency-2025-SHOP.csv": "Transparency-2025-SHOP",
    "transparency-in-coverage-puf-indQHP.csv": "transparency-in-coverage-puf-indQHP",
    "Quality_PUF_October-2024.csv": "Quality_PUF_October-2024",
    "NJBenefits06262024.csv": "NJBenefits06262024",
    "NJBusinessRules06262024.csv": "NJBusinessRules06262024",
    "NJNetworks06262024.csv": "NJNetworks06262024",
    "NJPlans06262024.csv": "NJPlans06262024",
    "NJServiceAreas06262024.csv": "NJServiceAreas06262024",
}

# Load each CSV into a table
for csv_file, table_name in datasets.items():
    print(f"Loading {csv_file} into {table_name} table...")
    df = pd.read_csv(os.path.join(data_folder, csv_file), low_memory=False)
    df.to_sql(table_name, conn, if_exists="replace", index=False)

# Verify by printing table names
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("\nLoaded tables:")
for table in tables:
    print(table[0])

# Close the connection
conn.close()