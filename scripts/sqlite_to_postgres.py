import sqlite3
import pandas as pd
from sqlalchemy import create_engine, text
import time

# SQLite connection
sqlite_conn = sqlite3.connect('data/cms_healthcare.db')

# PostgreSQL connection (replace with your Railway URL)
postgres_url = 'postgresql://postgres:QIUoRaKKKGlWTUwUmGhBFZbsHgibIKru@interchange.proxy.rlwy.net:42600/railway'
postgres_engine = create_engine(postgres_url)

# First check if the PostgreSQL database is accessible
try:
    with postgres_engine.connect() as conn:
        print("PostgreSQL connection successful!")
        
        # Check for existing tables
        result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'"))
        existing_tables = [row[0] for row in result]
        
        if existing_tables:
            print(f"Found existing tables: {', '.join(existing_tables)}")
            
            # Optional: check row counts for each table
            for table in existing_tables:
                count = conn.execute(text(f"SELECT COUNT(*) FROM \"{table}\"")).scalar()
                print(f"Table '{table}' has {count} rows")
        else:
            print("No tables found in the PostgreSQL database")
except Exception as e:
    print(f"Error connecting to PostgreSQL: {str(e)}")
    print("Please check if your Railway PostgreSQL instance is running and accessible")
    exit(1)

# List all tables from SQLite
tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", sqlite_conn)
print(f"Found {len(tables)} tables in SQLite database")

# Function to migrate a single table with retries
def migrate_table(table_name, max_retries=3, retry_delay=5):
    for attempt in range(max_retries):
        try:
            print(f"Migrating table: {table_name} (Attempt {attempt+1}/{max_retries})")
            df = pd.read_sql_query(f"SELECT * FROM `{table_name}`", sqlite_conn)
            print(f"  - Read {len(df)} rows from SQLite")
            
            # For larger tables, use chunking to avoid memory issues
            if len(df) > 10000:
                print(f"  - Large table detected ({len(df)} rows), using chunks")
                df.to_sql(table_name, postgres_engine, if_exists='replace', index=False, 
                          method='multi', chunksize=1000)
            else:
                df.to_sql(table_name, postgres_engine, if_exists='replace', index=False)
                
            # Verify migration
            with postgres_engine.connect() as conn:
                pg_count = conn.execute(text(f"SELECT COUNT(*) FROM \"{table_name}\"")).scalar()
                
            print(f"  - Successfully migrated table: {table_name} ({pg_count} rows)")
            return True
            
        except Exception as e:
            print(f"  - Error migrating table {table_name}: {str(e)}")
            if attempt < max_retries - 1:
                print(f"  - Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                # Refresh connection
                postgres_engine.dispose()
            else:
                print(f"  - Failed to migrate {table_name} after {max_retries} attempts")
                return False

# Try to migrate each table
successful_migrations = 0
for table in tables['name']:
    if migrate_table(table):
        successful_migrations += 1

sqlite_conn.close()
postgres_engine.dispose()

print(f"Migration completed. Successfully migrated {successful_migrations} out of {len(tables)} tables.")
