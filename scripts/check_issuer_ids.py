#check if issuer ids are unique by state

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

with engine.connect() as connection:
    query = text('''
        SELECT "IssuerId", COUNT(DISTINCT "StateCode") as num_states
        FROM plan_attributes_puf
        GROUP BY "IssuerId"
        HAVING COUNT(DISTINCT "StateCode") > 1
        LIMIT 20;
    ''')
    
    df = pd.read_sql_query(query, connection)

print(df)


