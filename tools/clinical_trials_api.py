import requests
from typing import List, Dict, Any, Optional
import functools

def handle_api_errors(func):
    """
    Decorator to wrap tool functions with structured error handling
    that makes failures visible to AI agents.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            return {"status": "success", "data": result}
       
        except requests.exceptions.HTTPError as e:
            return {
                "status": "error",
                "error_type": "API_HTTP_ERROR",
                "http_status": e.response.status_code,
                "title": f"HTTP Error: {e.response.reason}",
                "detail": e.response.text[:500],
                "request_url": str(e.request.url)
            }
           
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "error_type": "API_CONNECTION_ERROR",
                "title": "API Connection Failed",
                "detail": str(e)
            }
           
        except Exception as e:
            return {
                "status": "error",
                "error_type": "TOOL_EXECUTION_ERROR",
                "title": "Unexpected error in search function",
                "detail": str(e)
            }
    return wrapper


@handle_api_errors
def search_clinical_trials_targeted(conditions: List[str], age: Optional[str] = None,
                                    location: Optional[str] = None, max_studies: int = 15) -> List[Dict[str, Any]]:
    """Search clinical trials using ClinicalTrials.gov API v2.0 with proper error handling."""
   
    base_url = "https://clinicaltrials.gov/api/v2/studies"
    condition_query = " OR ".join(conditions) if len(conditions) > 1 else conditions[0]
   
    params = {
        "query.cond": condition_query,
        "filter.overallStatus": "RECRUITING,NOT_YET_RECRUITING,ACTIVE_NOT_RECRUITING",
        "pageSize": min(max_studies, 100),
        "format": "json"
    }

    if location:
        params["query.locn"] = location
   
    response = requests.get(base_url, params=params, timeout=30)
    response.raise_for_status()
   
    data = response.json()
    studies_data = data.get("studies", [])
   
    if len(studies_data) == 0:
        return []
   
    parsed_studies = []
    for study in studies_data:
        parsed_study = parse_v2_study_data(study)
        if parsed_study:
            parsed_studies.append(parsed_study)
   
    return parsed_studies


def parse_v2_study_data(study: dict) -> Optional[dict]:
    """Parse study data from ClinicalTrials.gov API v2.0 response"""
    try:
        protocol = study.get("protocolSection", {})
        identification = protocol.get("identificationModule", {})
        nct_id = identification.get("nctId", "Not specified")
        title = identification.get("briefTitle", "Not specified")
        official_title = identification.get("officialTitle", "Not specified")
        
        status_module = protocol.get("statusModule", {})
        overall_status = status_module.get("overallStatus", "Not specified")
        
        description_module = protocol.get("descriptionModule", {})
        brief_summary = description_module.get("briefSummary", "Not specified")
        if len(brief_summary) > 400:
            brief_summary = brief_summary[:400] + "..."
        
        conditions_module = protocol.get("conditionsModule", {})
        conditions = conditions_module.get("conditions", ["Not specified"])
        
        design_module = protocol.get("designModule", {})
        phases = design_module.get("phases", ["Not specified"])
        study_type = design_module.get("studyType", "Not specified")
        
        sponsors_module = protocol.get("sponsorCollaboratorsModule", {})
        lead_sponsor = sponsors_module.get("leadSponsor", {})
        sponsor_name = lead_sponsor.get("name", "Not specified")
        
        contacts_locations = protocol.get("contactsLocationsModule", {})
        locations = contacts_locations.get("locations", [])
        
        facilities = []
        cities = []
        for loc in locations[:5]:
            facility = loc.get("facility", "")
            city = loc.get("city", "")
            state = loc.get("state", "")
            country = loc.get("country", "")
            
            if facility:
                facilities.append(facility)
            if city:
                city_state = city
                if state:
                    city_state += f", {state}"
                if country and country != "United States":
                    city_state += f", {country}"
                cities.append(city_state)
        
        arms_interventions = protocol.get("armsInterventionsModule", {})
        interventions = []
        for intervention in arms_interventions.get("interventions", []):
            intervention_name = intervention.get("name", "")
            if intervention_name:
                interventions.append(intervention_name)
        
        eligibility_module = protocol.get("eligibilityModule", {})
        min_age = eligibility_module.get("minimumAge", "Not specified")
        max_age = eligibility_module.get("maximumAge", "Not specified")
        gender = eligibility_module.get("gender", "Not specified")
        
        return {
            "nct_id": nct_id,
            "title": title,
            "official_title": official_title,
            "status": overall_status,
            "brief_summary": brief_summary,
            "conditions": conditions,
            "phase": phases,
            "study_type": study_type,
            "sponsor": sponsor_name,
            "locations": {
                "facilities": facilities[:3] if facilities else ["Not specified"],
                "cities": list(set(cities))[:5] if cities else ["Not specified"]
            },
            "interventions": interventions[:3] if interventions else ["Not specified"],
            "eligibility": {
                "min_age": min_age,
                "max_age": max_age,
                "gender": gender
            },
            "url": f"https://clinicaltrials.gov/study/{nct_id}"
        }
       
    except Exception as e:
        return None