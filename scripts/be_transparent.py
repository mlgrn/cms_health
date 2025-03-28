#!/usr/bin/env python3
import requests
import json
from tabulate import tabulate

# API base URL - assuming the API is running locally on default port
API_BASE_URL = "http://localhost:8000"

def get_user_input():
    """Get user age and state information."""
    # Get user's age
    while True:
        try:
            age = int(input("Please enter your age: "))
            if age <= 0 or age >= 120:
                print("Please enter a valid age between 1 and 119.")
                continue
            break
        except ValueError:
            print("Please enter a valid number for your age.")
    
    # Get user's state (two letter abbreviation)
    while True:
        print("\nStates WITH data (31): AK, AL, AR, AZ, DE, FL, HI, IA, IL, IN, KS, LA, MI, MO, MS, MT, NC, ND, NE, NH, OH, OK, OR, SC, SD, TN, TX, UT, WI, WV, WY")
        print("States without data: CA, CO, CT, DC, GA, ID, KY, MA, MD, ME, MN, NJ, NM, NV, NY, PA, RI, VA, VT, WA\n")
        state_code = input("Please enter your state's two-letter code: ").strip().upper()
        if len(state_code) != 2 or not state_code.isalpha():
            print("Please enter a valid two-letter state code.")
            continue
        break
    
    return age, state_code

def check_api_status():
    """Check if the API is running."""
    try:
        response = requests.get(f"{API_BASE_URL}/")
        if response.status_code == 200:
            return True
        return False
    except requests.exceptions.RequestException:
        return False

def get_issuers(state_code):
    """Fetch issuer IDs for a given state."""
    try:
        print(f"Fetching issuers for state: {state_code}...")
        response = requests.get(f"{API_BASE_URL}/issuers/{state_code}")
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: API returned status code {response.status_code}")
            print(f"Response: {response.text}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to API: {e}")
        return None

def get_all_transparency_data(issuer_id):
    """Fetch transparency data from all tables for a given issuer ID."""
    try:
        response = requests.get(f"{API_BASE_URL}/all-transparency/{issuer_id}")
        
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except requests.exceptions.RequestException:
        return None

def get_rates_data(state_code, age):
    """Fetch rates data for a specific state and age."""
    try:
        print(f"Fetching premium rates for state: {state_code}, age: {age}...")
        response = requests.get(f"{API_BASE_URL}/rates/{state_code}/{age}")
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and "error" in data:
                print(f"Warning: {data['error']}")
                return None
            
            # Print debugging information about the first few records
            if data and len(data) > 0:
                print(f"Successfully retrieved {len(data)} rate records.")
                for idx, rate in enumerate(data[:3]):
                    print(f"Sample rate record {idx+1}: PlanId={rate.get('PlanId', 'Not found')}, Tobacco={rate.get('Tobacco', 'Not found')}, IndividualRate=${rate.get('IndividualRate', 'Not found')}")
            else:
                print("Warning: No rate data found.")
            return data
        else:
            print(f"Warning: Could not fetch rates data. Status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Warning: Error connecting to rates API: {e}")
        return None

def get_rate_by_plan_id(plan_id, age):
    """Fetch rate data specifically for a plan ID and age."""
    try:
        print(f"Fetching premium rate for plan ID: {plan_id}, age: {age}...")
        response = requests.get(f"{API_BASE_URL}/rate-by-plan/{plan_id}/{age}")
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict) and "error" in data:
                # Silently handle errors since we may try multiple plans
                return None
            
            if data and len(data) > 0:
                # First check for exact plan ID match
                for rate in data:
                    rate_plan_id = rate.get("PlanId", "")
                    if rate_plan_id == plan_id and (
                            rate.get("Tobacco", "") == "Tobacco User/Non-Tobacco User" or 
                            rate.get("Tobacco", "") == "No" or 
                            rate.get("TobaccoUse", "") == "No Preference" or 
                            rate.get("TobaccoUse", "") == "No"):
                        return rate
                        
                # If no exact match, return the first applicable rate
                # This handles partial matches from the API's fallback search
                return data[0]
            return None
        else:
            return None
    except requests.exceptions.RequestException:
        return None

def check_all_issuers_transparency(issuers):
    """Check transparency data for all issuers and return results."""
    results = []
    
    print(f"Checking transparency data for {len(issuers)} issuers...")
    for issuer in issuers:
        issuer_id = issuer["IssuerId"]
        data = get_all_transparency_data(issuer_id)
        
        if data and "error" not in data:
            # Store issuer and what data types are available
            available_types = []
            for data_type in ["indqhp", "ind_sadp", "shop"]:
                if data_type in data and data[data_type]:
                    available_types.append(data_type)
            
            if available_types:
                # Calculate metrics for each issuer
                metrics = calculate_issuer_metrics(data, available_types)
                
                results.append({
                    "issuer_id": issuer_id,
                    "available_types": available_types,
                    "data": data,
                    "metrics": metrics
                })
    
    return results

def calculate_issuer_metrics(data, available_types):
    """Calculate important metrics for each issuer based on transparency data."""
    metrics = {}
    
    for data_type in available_types:
        type_metrics = {}
        records = data[data_type]
        issuer_level_metrics = {}
        plan_level_metrics = {}
        
        # Find a record with complete issuer-level data
        complete_issuer_record = None
        for record in records:
            if (is_numeric(record.get("Issuer_Claims_Received_In_Network")) and
                is_numeric(record.get("Issuer_Claims_Received_Out_of_Network")) and
                is_numeric(record.get("Issuer_Claims_Denied_In_Network")) and
                is_numeric(record.get("Issuer_Claims_Denied_Out_of_Network\"")) and
                is_numeric(record.get("Issuer_Claims_Resubmitted_In_Network")) and
                is_numeric(record.get("Issuer_Claims_Resubmitted_Out_of_Network"))):
                complete_issuer_record = record
                break
        
        # Calculate issuer-level metrics if data is available
        if complete_issuer_record:
            issuer_name = complete_issuer_record.get("Issuer_Name", "Unknown")
            claims_in_net = float(complete_issuer_record.get("Issuer_Claims_Received_In_Network", 0))
            claims_out_net = float(complete_issuer_record.get("Issuer_Claims_Received_Out_of_Network", 0))
            denied_in_net = float(get_numeric_value(complete_issuer_record.get("Issuer_Claims_Denied_In_Network", 0)))
            denied_out_net = float(get_numeric_value(complete_issuer_record.get("Issuer_Claims_Denied_Out_of_Network\"", 0)))
            resub_in_net = float(get_numeric_value(complete_issuer_record.get("Issuer_Claims_Resubmitted_In_Network", 0)))
            resub_out_net = float(get_numeric_value(complete_issuer_record.get("Issuer_Claims_Resubmitted_Out_of_Network", 0)))
            
            total_claims = claims_in_net + claims_out_net
            
            # Calculate metrics
            if total_claims > 0:
                issuer_level_metrics = {
                    "issuer_name": issuer_name,
                    "denial_rate": ((denied_in_net + denied_out_net) / total_claims) if total_claims > 0 else 0,
                    "resubmission_rate": ((resub_in_net + resub_out_net) / total_claims) if total_claims > 0 else 0,
                    "out_of_network_claims_pct": (claims_out_net / total_claims) if total_claims > 0 else 0
                }
        
        # Calculate metrics for each plan if available
        plans_metrics = []
        for record in records:
            plan_id = record.get("Plan_ID")
            plan_name = record.get("Plan_Name", "N/A")
            metal_level = record.get("Metal_Level", "N/A")
            
            if plan_id and all([
                is_numeric(record.get("Plan_Number_Claims_Received_In_Network")),
                is_numeric(record.get("Plan_Number_Claims_Received_Out_of_Network")),
                is_numeric(record.get("Plan_Number_Claims_Denied_In_Network")),
                is_numeric(record.get("Plan_Number_Claims_Denied_Out_of_Network")),
                is_numeric(record.get("Plan_Number_Claims_Resubmitted_In_Network")),
                is_numeric(record.get("Plan_Number_Claims_Resubmitted_Out_of_Network"))
            ]):
                claims_in_net = float(get_numeric_value(record.get("Plan_Number_Claims_Received_In_Network", 0)))
                claims_out_net = float(get_numeric_value(record.get("Plan_Number_Claims_Received_Out_of_Network", 0)))
                denied_in_net = float(get_numeric_value(record.get("Plan_Number_Claims_Denied_In_Network", 0)))
                denied_out_net = float(get_numeric_value(record.get("Plan_Number_Claims_Denied_Out_of_Network", 0)))
                resub_in_net = float(get_numeric_value(record.get("Plan_Number_Claims_Resubmitted_In_Network", 0)))
                resub_out_net = float(get_numeric_value(record.get("Plan_Number_Claims_Resubmitted_Out_of_Network", 0)))
                
                total_claims = claims_in_net + claims_out_net
                
                if total_claims > 0:
                    plans_metrics.append({
                        "Plan_ID": plan_id,
                        "Plan_Name": plan_name,
                        "Metal_Level": metal_level,
                        "denial_rate": ((denied_in_net + denied_out_net) / total_claims) if total_claims > 0 else 0,
                        "resubmission_rate": ((resub_in_net + resub_out_net) / total_claims) if total_claims > 0 else 0,
                        "out_of_network_claims_pct": (claims_out_net / total_claims) if total_claims > 0 else 0
                    })
        
        # Store metrics for this data type
        type_metrics = {
            "issuer_level": issuer_level_metrics,
            "plan_level": plans_metrics
        }
        
        metrics[data_type] = type_metrics
    
    return metrics

def is_numeric(value):
    """Check if a value can be converted to a number."""
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        if value.strip() == "**" or value.strip() == "":
            return False
        try:
            float(value.replace(",", ""))
            return True
        except ValueError:
            return False
    return False

def get_numeric_value(value):
    """Convert a value to a numeric type, handling strings with commas."""
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        return float(value.replace(",", ""))
    return 0

def find_premium_for_plan(plan_id, rates_data):
    """Find premium rate for a specific plan ID."""
    if not rates_data or not plan_id:
        return None
    
    # Try exact match first
    for rate in rates_data:
        rate_plan_id = rate.get("PlanId", "")
        if rate_plan_id and rate_plan_id == plan_id and (
                rate.get("Tobacco", "") == "Tobacco User/Non-Tobacco User" or 
                rate.get("Tobacco", "") == "No" or 
                rate.get("TobaccoUse", "") == "No Preference" or 
                rate.get("TobaccoUse", "") == "No"):
            return rate.get("IndividualRate")
    
    return None

def process_rates_data(rates_data):
    """Process rates data for easier lookup."""
    plan_id_to_premium = {}
    
    if not rates_data:
        return plan_id_to_premium
    
    for rate in rates_data:
        plan_id = rate.get("PlanId")
        if plan_id and (rate.get("Tobacco") == "Tobacco User/Non-Tobacco User" or rate.get("Tobacco") == "No"):
            if plan_id not in plan_id_to_premium:
                plan_id_to_premium[plan_id] = rate.get("IndividualRate")
    
    # Print some diagnostics
    if len(plan_id_to_premium) > 0:
        print(f"\nProcessed {len(plan_id_to_premium)} unique plans with premium data.")
        sample_keys = list(plan_id_to_premium.keys())[:3]
        print(f"Sample PlanId format: {sample_keys}")
    else:
        print("\nWarning: No premium data processed from rates data.")
    
    return plan_id_to_premium

def display_metrics_for_all_plans(results, rates_data, user_age):
    """Display calculated metrics for all plans in a concise table."""
    if not results:
        print("\nNo transparency data found for any issuers.")
        return
    
    all_plans = []
    
    # Process rates data for faster lookup
    plan_id_to_premium = process_rates_data(rates_data)
    
    # Collect sample plan IDs from transparency data for comparison
    transparency_plan_ids = []
    
    # Use the provided user_age for plan-specific rate lookup
    age = user_age
    
    # Track API calls for fetching plan-specific premium data
    api_requests_count = 0
    api_success_count = 0
    
    for result in results:
        issuer_id = result["issuer_id"]
        metrics = result["metrics"]
        
        for data_type in result["available_types"]:
            type_metrics = metrics.get(data_type, {})
            issuer_metrics = type_metrics.get("issuer_level", {})
            plan_metrics = type_metrics.get("plan_level", [])
            
            data_type_label = {
                "indqhp": "Individual QHP",
                "ind_sadp": "Individual SADP", 
                "shop": "SHOP"
            }.get(data_type, data_type)
            
            issuer_name = issuer_metrics.get("issuer_name", "Unknown")
            
            for plan in plan_metrics:
                plan_id = plan["Plan_ID"]
                if len(transparency_plan_ids) < 3:
                    transparency_plan_ids.append(plan_id)
                
                # First try existing rate data (faster)
                premium = plan_id_to_premium.get(plan_id)
                
                # If premium not found, try direct API lookup by plan ID
                if premium is None:
                    api_requests_count += 1
                    rate_data = get_rate_by_plan_id(plan_id, age)
                    if rate_data:
                        api_success_count += 1
                        premium = rate_data.get("IndividualRate")
                        # Add to our cache for faster lookups
                        plan_id_to_premium[plan_id] = premium
                
                premium_display = f"${premium:.2f}" if premium else "N/A"
                
                all_plans.append({
                    "Issuer ID": issuer_id,
                    "Issuer Name": issuer_name,
                    "Plan Type": data_type_label,
                    "Plan ID": plan_id,
                    "Metal Level": plan["Metal_Level"],
                    "Monthly Premium": premium_display,
                    "Denial Rate": f"{plan['denial_rate']:.2%}",
                    "Resubmission Rate": f"{plan['resubmission_rate']:.2%}",
                    "Out-of-Network %": f"{plan['out_of_network_claims_pct']:.2%}"
                })
    
    # Print sample plan IDs from transparency data for debugging
    if transparency_plan_ids:
        print(f"Sample Plan IDs from transparency data: {transparency_plan_ids}")
    
    # Print statistics on API requests for premium data
    if api_requests_count > 0:
        print(f"\nMade {api_requests_count} direct API requests for plan premium data, successful: {api_success_count} ({(api_success_count/api_requests_count)*100:.1f}%)")
    
    if all_plans:
        # Count plans with premium data
        plans_with_premium_count = sum(1 for p in all_plans if p["Monthly Premium"] != "N/A")
        print(f"\nFound premium data for {plans_with_premium_count} out of {len(all_plans)} plans.")
        
        print("\nAll Available Plans With Quality Metrics:")
        print(tabulate(all_plans, headers="keys", tablefmt="grid"))
        
        # Sort plans by denial rate (lowest to highest)
        print("\nPlans Ranked by Denial Rate (Lowest to Highest):")
        sorted_by_denial = sorted(
            all_plans, 
            key=lambda x: float(x["Denial Rate"].strip('%')) / 100
        )
        print(tabulate(sorted_by_denial, headers="keys", tablefmt="grid"))
        
        # Sort by value (premium divided by (1 - denial_rate))
        print("\nPlans Ranked by Value (Lower premium + lower denial rate = better value):")
        # Filter plans with valid premium data first
        plans_with_premium = [p for p in all_plans if p["Monthly Premium"] != "N/A"]
        
        if plans_with_premium:
            for plan in plans_with_premium:
                premium = float(plan["Monthly Premium"].replace("$", ""))
                denial_rate = float(plan["Denial Rate"].strip('%')) / 100
                # Value score: premium divided by probability of claim approval
                # Lower is better - represents cost per approved claim
                value_score = premium / (1 - denial_rate) if denial_rate < 1 else float('inf')
                plan["Value Score"] = f"${value_score:.2f}"
            
            sorted_by_value = sorted(
                plans_with_premium,
                key=lambda x: float(x["Value Score"].replace("$", ""))
            )
            print(tabulate(sorted_by_value, headers="keys", tablefmt="grid"))
        else:
            print("\nNo plans with premium data available for value ranking.")
    else:
        print("\nNo plan-level metrics available.")

def main():
    print("Healthcare Transparency Data Tool")
    print("--------------------------------")
    
    # Check API status
    if not check_api_status():
        print("\nError: Cannot connect to the API. Make sure it's running at", API_BASE_URL)
        return
    
    # Get user input
    age, state_code = get_user_input()
    
    print(f"\nFinding plans for age {age} in state {state_code}...")
    
    # Get rates data for the state and age
    rates_data = get_rates_data(state_code, age)
    
    # Get issuers for the state
    issuers = get_issuers(state_code)
    
    if not issuers or "error" in issuers:
        print("No issuers found for your state. Exiting.")
        return
    
    # Check transparency data for all issuers
    transparency_results = check_all_issuers_transparency(issuers)
    
    if not transparency_results:
        print("No transparency data available for any issuers in your state.")
        return
    
    # Display metrics for all plans in a concise table with premium information
    display_metrics_for_all_plans(transparency_results, rates_data, age)

if __name__ == "__main__":
    main()
