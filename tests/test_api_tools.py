"""
Quick test to verify Clinical Trials API tools work after migration
"""
import sys
sys.path.append('..')

from tools.clinical_trials_api import search_clinical_trials_targeted

def test_basic_search():
    """Test basic API connectivity"""
    print("Testing Clinical Trials API...")
    
    result = search_clinical_trials_targeted(
        conditions=["lung cancer"],
        max_studies=3
    )
    
    if result.get("status") == "success":
        trials = result.get("data", [])
        print(f"✅ Success! Found {len(trials)} trials")
        if trials:
            print(f"   First trial: {trials[0]['nct_id']} - {trials[0]['title'][:60]}...")
        return True
    else:
        print(f"❌ Error: {result.get('title', 'Unknown error')}")
        return False

if __name__ == "__main__":
    test_basic_search()