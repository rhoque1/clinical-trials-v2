"""
Helper script to create sample patient profiles for testing

Since we may not have actual PDF files for all test cases,
this script generates mock patient profiles that can be used
directly by the evaluator.
"""

import json
from pathlib import Path


def create_sample_profiles():
    """
    Create sample patient profiles matching test cases
    """

    profiles = {
        "cervical_pdl1_standard": {
            "success": True,
            "demographics": {
                "age": 40,
                "sex": "Female",
                "location": "United States"
            },
            "diagnoses": "Stage IIIB cervical squamous cell carcinoma. Patient presents with locally advanced disease. Tumor shows squamous cell histology. HPV-16 positive by PCR testing.",
            "biomarkers": "PD-L1 positive (CPS 50% by IHC 22C3), HPV-16 positive, TP53 wild-type",
            "treatment_history": {
                "prior_therapies": [],
                "treatment_line": "first_line",
                "progression_on": None
            },
            "search_terms": ["cervical cancer", "PD-L1 positive", "HPV positive", "locally advanced"]
        },

        "lung_egfr_exon19": {
            "success": True,
            "demographics": {
                "age": 62,
                "sex": "Male",
                "location": "United States"
            },
            "diagnoses": "Metastatic non-small cell lung cancer (NSCLC), adenocarcinoma histology, stage IV. No brain metastases on MRI.",
            "biomarkers": "EGFR exon 19 deletion (p.E746_A750del) by NGS. ALK negative by IHC. ROS1 negative by FISH. PD-L1 TPS 10%.",
            "treatment_history": {
                "prior_therapies": [],
                "treatment_line": "first_line",
                "progression_on": None
            },
            "search_terms": ["lung cancer", "NSCLC", "EGFR positive", "metastatic", "adenocarcinoma"]
        },

        "breast_her2_brca": {
            "success": True,
            "demographics": {
                "age": 45,
                "sex": "Female",
                "location": "United States"
            },
            "diagnoses": "Metastatic HER2-positive breast cancer, stage IV. ER negative, PR negative, HER2 positive (IHC 3+). Bone and liver metastases.",
            "biomarkers": "HER2 positive (IHC 3+, FISH amplified with ratio 5.2). Germline BRCA1 mutation (c.5266dupC). ER negative, PR negative.",
            "treatment_history": {
                "prior_therapies": ["trastuzumab", "pertuzumab", "docetaxel"],
                "treatment_line": "second_line",
                "progression_on": "trastuzumab + pertuzumab + docetaxel"
            },
            "search_terms": ["breast cancer", "HER2 positive", "BRCA1 mutation", "metastatic", "second-line"]
        },

        "colorectal_msi_high": {
            "success": True,
            "demographics": {
                "age": 58,
                "sex": "Female",
                "location": "United States"
            },
            "diagnoses": "Stage IV colorectal adenocarcinoma. Primary tumor in right (ascending) colon. Liver metastases. MSI-H/dMMR confirmed.",
            "biomarkers": "MSI-H (microsatellite instability-high) by PCR. dMMR (deficient mismatch repair) by IHC (loss of MLH1/PMS2). BRAF V600E mutation detected. KRAS/NRAS wild-type.",
            "treatment_history": {
                "prior_therapies": [],
                "treatment_line": "first_line",
                "progression_on": None
            },
            "search_terms": ["colorectal cancer", "MSI-H", "dMMR", "BRAF mutation", "immunotherapy"]
        },

        "melanoma_braf_v600e": {
            "success": True,
            "demographics": {
                "age": 52,
                "sex": "Male",
                "location": "United States"
            },
            "diagnoses": "Unresectable stage III melanoma. Multiple in-transit metastases. No distant organ metastases. No brain metastases on MRI.",
            "biomarkers": "BRAF V600E mutation confirmed by NGS. NRAS wild-type. PD-L1 expression 5%.",
            "treatment_history": {
                "prior_therapies": [],
                "treatment_line": "first_line",
                "progression_on": None
            },
            "search_terms": ["melanoma", "BRAF V600E", "unresectable", "stage III"]
        }
    }

    # Save profiles
    output_dir = Path("evaluation/sample_profiles")
    output_dir.mkdir(parents=True, exist_ok=True)

    for case_id, profile in profiles.items():
        output_file = output_dir / f"{case_id}.json"
        with open(output_file, 'w') as f:
            json.dump(profile, f, indent=2)
        print(f"[OK] Created: {output_file}")

    print(f"\n[SUCCESS] Created {len(profiles)} sample patient profiles")
    print(f"   Location: {output_dir}")


if __name__ == "__main__":
    create_sample_profiles()
