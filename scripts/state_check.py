import requests
import time
from collections import defaultdict

# List of all US state codes
US_STATES = [
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
    'DC'  # Including District of Columbia
]

# Base API URL - assumes API is running locally on default port
BASE_URL = "http://localhost:8000"

def check_states():
    states_with_data = []
    states_without_data = []
    
    print(f"Checking {len(US_STATES)} states for plan data...")
    
    for state in US_STATES:
        url = f"{BASE_URL}/plans/{state}"
        try:
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    states_with_data.append(state)
                    print(f"✅ {state}: Found {len(data)} plans")
                elif isinstance(data, dict) and "error" in data:
                    states_without_data.append(state)
                    print(f"❌ {state}: No data found")
                else:
                    states_without_data.append(state)
                    print(f"❌ {state}: No data (empty list)")
            else:
                print(f"⚠️ {state}: Error - Status code {response.status_code}")
                states_without_data.append(state)
                
            # Small delay to avoid overwhelming the API
            time.sleep(0.2)
            
        except Exception as e:
            print(f"⚠️ {state}: Error - {str(e)}")
            states_without_data.append(state)
    
    return states_with_data, states_without_data

def print_summary(states_with_data, states_without_data):
    print("\n--- SUMMARY ---")
    print(f"Total states checked: {len(US_STATES)}")
    print(f"States WITH data ({len(states_with_data)}): {', '.join(sorted(states_with_data))}")
    print(f"States WITHOUT data ({len(states_without_data)}): {', '.join(sorted(states_without_data))}")

if __name__ == "__main__":
    print("CMS Healthcare Data State Availability Check")
    print("===========================================")
    
    states_with_data, states_without_data = check_states()
    print_summary(states_with_data, states_without_data)
