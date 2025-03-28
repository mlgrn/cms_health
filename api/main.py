import os 
from fastapi import FastAPI, Depends
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import pandas as pd
import numpy as np


dotenv_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

app = FastAPI()


DATABASE_URL = os.getenv("DATABASE_URL")

def get_db():
    engine = create_engine(DATABASE_URL)
    try:
        yield engine
    finally:
        engine.dispose()

@app.get("/")
def read_root():
    return {"message": "CMS Healthcare API Running!"}

#get plans and info by state code
@app.get("/plans/{state_code}")
def get_plans(state_code: str, engine=Depends(get_db)):
    query = text('SELECT * FROM plan_attributes_puf WHERE "StateCode" = :state LIMIT 20;')
    df = pd.read_sql_query(query, engine, params={"state": state_code.upper()})
    if df.empty:
        return {"error": f"State code '{state_code.upper()}' not found in the database"}
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.astype(object).where(pd.notnull(df), None)
    return df.to_dict(orient='records')


# Get insurance rate data for a specific state and age
# Returns rate information from rate_puf table including premium rates and other rate factors
@app.get("/rates/{state_code}/{age}")
def get_rates(state_code: str, age: int, engine=Depends(get_db)):
    query = text('''
        SELECT * FROM rate_puf
        WHERE "StateCode" = :state
        AND "Age" = :age
        LIMIT 20;
    ''')
    try:
        df = pd.read_sql_query(query, engine, params={"state": state_code.upper(), "age": str(age)})
        
        if df.empty:
            return {"error": f"No rate data found for state {state_code.upper()} and age {age}."}
            
        df = df.replace([np.inf, -np.inf], np.nan).astype(object).where(pd.notnull(df), None)
        return df.to_dict(orient='records')
    except Exception as e:
        return {"error": f"Database error: {str(e)}"}


#gets issuers IDs for a specific state
@app.get("/issuers/{state_code}")
def get_issuers(state_code: str, engine=Depends(get_db)):
    query = text('''
        SELECT DISTINCT "IssuerId"
        FROM plan_attributes_puf
        WHERE "StateCode" = :state;
    ''')
    try:
        df = pd.read_sql_query(query, engine, params={"state": state_code.upper()})
        
        if df.empty:
            return {"error": f"No issuers found for state {state_code.upper()}."}
            
        df = df.astype(object).where(pd.notnull(df), None)
        return df.to_dict(orient='records')
    except Exception as e:
        return {"error": f"Database error: {str(e)}"}


@app.get("/transparency/{issuer_id}")
def get_transparency(issuer_id: str, engine = Depends(get_db)):
    query = text('SELECT * FROM transparency_in_coverage_puf_indqhp WHERE "Issuer_ID" = :issuer LIMIT 20;')
    try:
        df = pd.read_sql_query(query, engine, params={"issuer": issuer_id})
        if df.empty:
            return {"error": f"No transparency data found for issuer ID {issuer_id}."}
        df = df.replace([np.inf, -np.inf], np.nan)
        df = df.astype(object).where(pd.notnull(df), None)
        return df.to_dict(orient='records')
    except Exception as e:
        return {"error": f"Database error: {str(e)}"}

@app.get("/all-transparency/{issuer_id}")
def get_all_transparency(issuer_id: str, engine = Depends(get_db)):
    """
    Get transparency data from all three transparency tables for a given issuer ID.
    """
    all_data = {}
    
    # Check transparency_in_coverage_puf_indqhp table
    try:
        query = text('SELECT * FROM transparency_in_coverage_puf_indqhp WHERE "Issuer_ID" = :issuer LIMIT 50;')
        df = pd.read_sql_query(query, engine, params={"issuer": issuer_id})
        if not df.empty:
            df = df.replace([np.inf, -np.inf], np.nan)
            df = df.astype(object).where(pd.notnull(df), None)
            all_data["indqhp"] = df.to_dict(orient='records')
    except Exception as e:
        all_data["indqhp_error"] = f"Database error: {str(e)}"
    
    # Check transparency_2025_ind_sadp table
    try:
        query = text('SELECT * FROM transparency_2025_ind_sadp WHERE "Issuer_ID" = :issuer LIMIT 50;')
        df = pd.read_sql_query(query, engine, params={"issuer": issuer_id})
        if not df.empty:
            df = df.replace([np.inf, -np.inf], np.nan)
            df = df.astype(object).where(pd.notnull(df), None)
            all_data["ind_sadp"] = df.to_dict(orient='records')
    except Exception as e:
        all_data["ind_sadp_error"] = f"Database error: {str(e)}"
    
    # Check transparency_2025_shop table
    try:
        query = text('SELECT * FROM transparency_2025_shop WHERE "Issuer_ID" = :issuer LIMIT 50;')
        df = pd.read_sql_query(query, engine, params={"issuer": issuer_id})
        if not df.empty:
            df = df.replace([np.inf, -np.inf], np.nan)
            df = df.astype(object).where(pd.notnull(df), None)
            all_data["shop"] = df.to_dict(orient='records')
    except Exception as e:
        all_data["shop_error"] = f"Database error: {str(e)}"
    
    # Check if we found any data
    if not all_data or (len(all_data) == 0 or 
                        (len(all_data) == 3 and 
                         "indqhp_error" in all_data and 
                         "ind_sadp_error" in all_data and 
                         "shop_error" in all_data)):
        return {"error": f"No transparency data found for issuer ID {issuer_id} in any table."}
    
    return all_data

@app.get("/rate-by-plan/{plan_id}/{age}")
def get_rate_by_plan(plan_id: str, age: int, engine=Depends(get_db)):
    """
    Get rate data for a specific plan ID and age.
    This endpoint helps match plan IDs from transparency data with rate information.
    
    First tries exact match, then attempts partial matching as a fallback.
    """
    # First try exact match
    exact_query = text('''
        SELECT * FROM rate_puf
        WHERE "PlanId" = :plan_id
        AND "Age" = :age
        AND ("Tobacco" = 'No' OR "Tobacco" = 'Tobacco User/Non-Tobacco User')
        LIMIT 5;
    ''')
    
    try:
        df = pd.read_sql_query(exact_query, engine, params={"plan_id": plan_id, "age": str(age)})
        
        # If exact match found, return it
        if not df.empty:
            df = df.replace([np.inf, -np.inf], np.nan).astype(object).where(pd.notnull(df), None)
            return df.to_dict(orient='records')
            
        # If no exact match, try partial match (uses first 10 characters of plan ID)
        # This is often effective as plan IDs may have variations but share a common prefix
        if len(plan_id) >= 10:
            plan_prefix = plan_id[:10]
            partial_query = text('''
                SELECT * FROM rate_puf
                WHERE "PlanId" LIKE :plan_prefix || '%'
                AND "Age" = :age
                AND ("Tobacco" = 'No' OR "Tobacco" = 'Tobacco User/Non-Tobacco User')
                LIMIT 5;
            ''')
            
            df = pd.read_sql_query(partial_query, engine, params={
                "plan_prefix": plan_prefix, 
                "age": str(age)
            })
            
            if not df.empty:
                df = df.replace([np.inf, -np.inf], np.nan).astype(object).where(pd.notnull(df), None)
                return df.to_dict(orient='records')
                
        # If still no match, try a more flexible match using issuer ID if present in the plan ID
        # Extract issuer ID from the plan ID if possible (typically first 5 digits)
        if len(plan_id) >= 5:
            issuer_id = plan_id[:5]
            issuer_query = text('''
                SELECT * FROM rate_puf
                WHERE "PlanId" LIKE :issuer_id || '%' 
                AND "Age" = :age
                AND ("Tobacco" = 'No' OR "Tobacco" = 'Tobacco User/Non-Tobacco User')
                LIMIT 10;
            ''')
            
            df = pd.read_sql_query(issuer_query, engine, params={
                "issuer_id": issuer_id, 
                "age": str(age)
            })
            
            if not df.empty:
                df = df.replace([np.inf, -np.inf], np.nan).astype(object).where(pd.notnull(df), None)
                return df.to_dict(orient='records')
        
        # No matches found
        return {"error": f"No rate data found for plan ID {plan_id} and age {age}."}
    except Exception as e:
        return {"error": f"Database error: {str(e)}"}