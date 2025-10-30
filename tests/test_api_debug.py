import requests

print("Testing ClinicalTrials.gov API v2...")
print("="*60)

# Test 1: Basic cervical cancer search
params = {
    "query.cond": "cervical cancer",
    "filter.overallStatus": "RECRUITING",
    "pageSize": 5,
    "format": "json"
}

try:
    response = requests.get("https://clinicaltrials.gov/api/v2/studies", params=params, timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        studies = data.get('studies', [])
        print(f"Total RECRUITING trials found: {len(studies)}")
        print("="*60)
        
        if studies:
            print("\nFirst 3 trials:\n")
            for i, study in enumerate(studies[:3], 1):
                try:
                    protocol = study.get('protocolSection', {})
                    identification = protocol.get('identificationModule', {})
                    status_module = protocol.get('statusModule', {})
                    
                    nct = identification.get('nctId', 'N/A')
                    title = identification.get('briefTitle', 'N/A')
                    status = status_module.get('overallStatus', 'N/A')
                    
                    print(f"{i}. NCT ID: {nct}")
                    print(f"   Title: {title[:80]}...")
                    print(f"   Status: {status}")
                    print(f"   URL: https://clinicaltrials.gov/study/{nct}")
                    print()
                except Exception as e:
                    print(f"   Error parsing study {i}: {e}")
        else:
            print("No trials found!")
    else:
        print(f"API returned error: {response.status_code}")
        print(response.text[:500])

except Exception as e:
    print(f"Error: {e}")

print("="*60)
print("\nNow checking if those NCT IDs exist on the website...")
print("Copy any NCT ID above and search it at: https://clinicaltrials.gov")