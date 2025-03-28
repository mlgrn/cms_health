import os
import pandas as pd
from sqlalchemy import create_engine

# Your local PostgreSQL URL
DATABASE_URL = 'postgresql://localhost:5432/cms_healthcare_data'

# Path to your CSV files
data_folder = os.path.join(os.path.dirname(__file__), '..', 'data')

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)

datasets = {
    "benefits-and-cost-sharing-puf.csv": "benefits_and_cost_sharing",
    "business-rules-puf.csv": "business_rules",
    "network-puf.csv": "network_puf",
    "plan-attributes-puf.csv": "plan_attributes_puf",
    "plan-id-crosswalk-puf.csv": "plan_id_crosswalk_puf",
    "rate-puf.csv": "rate_puf",
    "service-area-puf.csv": "service_area_puf",
    "Transparency-2025-Ind-SADP.csv": "transparency_2025_ind_sadp",
    "Transparency-2025-SHOP.csv": "transparency_2025_shop",
    "transparency-in-coverage-puf-indQHP.csv": "transparency_in_coverage_puf_indqhp",
    "Quality_PUF_October-2024.csv": "quality_puf_october_2024",
    "NJBenefits06262024.csv": "nj_benefits_06262024",
    "NJBusinessRules06262024.csv": "nj_business_rules_06262024",
    "NJNetworks06262024.csv": "nj_networks_06262024",
    "NJPlans06262024.csv": "nj_plans_06262024",
    "NJServiceAreas06262024.csv": "nj_service_areas_06262024",
}

# Load each CSV into PostgreSQL
for csv_file, table_name in datasets.items():
    print(f"Loading {csv_file} into table {table_name}...")
    df = pd.read_csv(os.path.join(data_folder, csv_file), low_memory=False)
    df.to_sql(table_name, engine, if_exists='replace', index=False, chunksize=50000)
    print(f"Table {table_name} loaded successfully.")

engine.dispose()
print("All CSVs loaded into PostgreSQL.")