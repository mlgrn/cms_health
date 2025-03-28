# scripts/test_db.py
import sqlite3
import pandas as pd
import os

db_path = os.path.join('data', 'cms_healthcare.db')
conn = sqlite3.connect(db_path)

tables = [
    "benefits_and_cost_sharing",
    "business_rules",
    "network-puf",
    "plan-attributes-puf",
    "plan-id-crosswalk-puf",
    "rate-puf",
    "service-area-puf",
    "Transparency-2025-Ind-SADP",
    "Transparency-2025-SHOP",
    "transparency-in-coverage-puf-indQHP",
    "Quality_PUF_October-2024",
    "NJBenefits06262024",
    "NJBusinessRules06262024",
    "NJNetworks06262024",
    "NJPlans06262024",
    "NJServiceAreas06262024"
]

for table in tables:
    try:
        # Wrap table names in quotes to handle special characters like hyphens
        df = pd.read_sql_query(f"SELECT * FROM \"{table}\" LIMIT 3;", conn)
        print(f"\nTable: {table}")
        print(df.head())
    except Exception as e:
        print(f"\nError querying table '{table}': {e}")

conn.close()
