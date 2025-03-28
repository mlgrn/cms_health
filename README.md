# Healthcare Transparency Data Tool

This tool helps consumers compare healthcare plans based on both premium costs and quality metrics such as claim denial rates. It uses public CMS (Centers for Medicare & Medicaid Services) data to provide insights that aren't typically available through standard marketplace comparisons.

For example, if a healthcare plan is fairly inexpensive in terms of the premium, but the denial rate or resubmission rate is historically high that plan may lead to a lot of frustration, wasted time spent of paperwork or having to pay more than expected out of pocket. Customers should be able to see this public data to make a more informed decision. 



## Features

- Retrieves plan data by state and age
- Calculates and displays key quality metrics:
  - Claim denial rates
  - Claim resubmission rates
  - Out-of-network claims percentages
- Shows monthly premium costs for each plan
- Ranks plans based on both cost and quality metrics
- Smart plan ID matching to maximize premium data availability

## Getting Started

### Prerequisites

- tested on Python 3.11.4
- PostgreSQL database with CMS data. I have temporarily hosted a database on Railway for convenience as 3-28-25 and will provide access for evaluation purposes. 
- Required Python packages (see requirements.txt)

### Installation

1. Clone this repository
```bashgits
git clone https://github.com/mlgrn/cms_health
cd cms_health
```

2. Install required packages
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the project root with the database connection string:

example
```
DATABASE_URL="postgresql://username:password@localhost:5432/database_name"
```


## Usage

### Starting the API

First, start the FastAPI backend:

```bash
cd api
uvicorn main:app --reload
```

The API should be running at http://localhost:8000.

### Running the Client

From another terminal, run the client script:

```bash
cd scripts
python be_transparent.py
```

Follow the prompts to:
1. Enter your age
2. Enter your state's two-letter code
3. View and compare healthcare plans

## How It Works

1. The client collects your age and state information
2. It queries the API for:
   - Available insurance issuers in your state
   - Premium rates for your age and state
   - Transparency data for each issuer
3. For each plan, it calculates quality metrics from transparency data
4. If premium data isn't immediately available for some plans, it makes targeted API calls to find matching premium data
5. Finally, it displays:
   - All available plans with their metrics
   - Plans ranked by denial rate (lowest to highest)
   - Plans ranked by value (premium cost divided by approval probability)

## API Endpoints

- `/` - API status check
- `/plans/{state_code}` - Get plans for a specific state
- `/rates/{state_code}/{age}` - Get premium rates by state and age
- `/issuers/{state_code}` - Get issuer IDs for a specific state
- `/transparency/{issuer_id}` - Get transparency data for a specific issuer
- `/all-transparency/{issuer_id}` - Get transparency data from all tables for an issuer
- `/rate-by-plan/{plan_id}/{age}` - Get premium rates for a specific plan ID and age

## Notes for Reviewers

- The tool uses progressive fallback logic for plan ID matching since plan IDs can vary between transparency and rate data tables
- The API includes robust error handling and diagnostics to help troubleshoot any issues
- For states or plans with limited data, the tool will display what's available with appropriate notices
- The tool currently supports data for 31 states (see the prompt when running the client) 