"""
Expand test set from 5 to 20 cases
Add 15 diverse oncology cases with ground truth trials
"""
import json
from pathlib import Path

# New test cases to add (15 cases)
NEW_TEST_CASES = [
    {
        "case_id": "breast_tnbc_first_line",
        "patient_summary": "38F with metastatic triple-negative breast cancer (ER-, PR-, HER2-), PD-L1 positive (CPS 15%), no brain metastases, treatment-naive",
        "pdf_path": "test_data/sample_reports/breast_tnbc.pdf",
        "ground_truth_trials": [
            {
                "nct_id": "NCT03036488",
                "trial_name": "KEYNOTE-355",
                "rationale": "Pembrolizumab + chemotherapy for PD-L1+ TNBC first-line, FDA approved",
                "expected_rank": "top3",
                "confidence": "very_high"
            },
            {
                "nct_id": "NCT02425891",
                "trial_name": "IMpassion130",
                "rationale": "Atezolizumab + nab-paclitaxel for PD-L1+ TNBC",
                "expected_rank": "top5",
                "confidence": "high"
            }
        ],
        "should_not_recommend": [],
        "key_biomarkers": ["Triple negative", "PD-L1 positive"],
        "treatment_line": "first_line",
        "nccn_recommendation": "Pembrolizumab + chemotherapy (Category 1 for PD-L1 CPS >=10)"
    },
    {
        "case_id": "lung_alk_positive",
        "patient_summary": "47M with metastatic NSCLC adenocarcinoma, ALK rearrangement (EML4-ALK fusion), brain metastases present, treatment-naive",
        "pdf_path": "test_data/sample_reports/lung_alk.pdf",
        "ground_truth_trials": [
            {
                "nct_id": "NCT02075840",
                "trial_name": "ALEX",
                "rationale": "Alectinib for ALK+ NSCLC first-line, superior CNS activity",
                "expected_rank": "top3",
                "confidence": "very_high"
            },
            {
                "nct_id": "NCT02737501",
                "trial_name": "ALTA-1L",
                "rationale": "Brigatinib for ALK+ NSCLC, strong CNS penetration",
                "expected_rank": "top5",
                "confidence": "high"
            }
        ],
        "should_not_recommend": [],
        "key_biomarkers": ["ALK rearrangement", "EML4-ALK fusion"],
        "treatment_line": "first_line",
        "nccn_recommendation": "Alectinib or brigatinib (Category 1 for ALK+ with brain mets)"
    },
    {
        "case_id": "prostate_brca2_crpc",
        "patient_summary": "67M with metastatic castration-resistant prostate cancer (mCRPC), germline BRCA2 mutation, progressed on abiraterone",
        "pdf_path": "test_data/sample_reports/prostate_brca2.pdf",
        "ground_truth_trials": [
            {
                "nct_id": "NCT01972217",
                "trial_name": "PROfound",
                "rationale": "Olaparib for BRCA2+ mCRPC, FDA approved",
                "expected_rank": "top3",
                "confidence": "very_high"
            },
            {
                "nct_id": "NCT02987543",
                "trial_name": "TRITON2",
                "rationale": "Rucaparib for BRCA-mutated mCRPC",
                "expected_rank": "top5",
                "confidence": "high"
            }
        ],
        "should_not_recommend": [],
        "key_biomarkers": ["BRCA2 mutation", "Castration-resistant"],
        "treatment_line": "second_line",
        "nccn_recommendation": "PARP inhibitor (olaparib Category 1 for BRCA2 mutation)"
    },
    {
        "case_id": "pancreatic_kras_g12c",
        "patient_summary": "61F with metastatic pancreatic adenocarcinoma, KRAS G12C mutation, progressed on FOLFIRINOX",
        "pdf_path": "test_data/sample_reports/pancreatic_kras.pdf",
        "ground_truth_trials": [
            {
                "nct_id": "NCT04185883",
                "trial_name": "CodeBreaK 100/101",
                "rationale": "Sotorasib for KRAS G12C mutated solid tumors including pancreatic",
                "expected_rank": "top3",
                "confidence": "high"
            },
            {
                "nct_id": "NCT03600883",
                "trial_name": "KRYSTAL-1",
                "rationale": "Adagrasib for KRAS G12C pancreatic cancer",
                "expected_rank": "top5",
                "confidence": "high"
            }
        ],
        "should_not_recommend": [],
        "key_biomarkers": ["KRAS G12C mutation"],
        "treatment_line": "second_line",
        "nccn_recommendation": "KRAS G12C inhibitor (emerging evidence) or chemotherapy"
    },
    {
        "case_id": "ovarian_brca1_platinum_sensitive",
        "patient_summary": "55F with high-grade serous ovarian cancer, germline BRCA1 mutation, platinum-sensitive recurrence (>6 months), second-line",
        "pdf_path": "test_data/sample_reports/ovarian_brca1.pdf",
        "ground_truth_trials": [
            {
                "nct_id": "NCT01874353",
                "trial_name": "SOLO2",
                "rationale": "Olaparib maintenance for BRCA+ platinum-sensitive ovarian cancer, FDA approved",
                "expected_rank": "top3",
                "confidence": "very_high"
            },
            {
                "nct_id": "NCT01847274",
                "trial_name": "NOVA",
                "rationale": "Niraparib maintenance for platinum-sensitive ovarian cancer",
                "expected_rank": "top5",
                "confidence": "high"
            }
        ],
        "should_not_recommend": [],
        "key_biomarkers": ["BRCA1 mutation", "Platinum-sensitive"],
        "treatment_line": "second_line",
        "nccn_recommendation": "PARP inhibitor maintenance (Category 1 for BRCA+ platinum-sensitive)"
    },
    {
        "case_id": "gastric_her2_positive",
        "patient_summary": "59M with metastatic gastric adenocarcinoma, HER2 positive (IHC 3+), no prior systemic therapy",
        "pdf_path": "test_data/sample_reports/gastric_her2.pdf",
        "ground_truth_trials": [
            {
                "nct_id": "NCT01041404",
                "trial_name": "ToGA",
                "rationale": "Trastuzumab + chemotherapy for HER2+ gastric cancer, FDA approved",
                "expected_rank": "top3",
                "confidence": "very_high"
            },
            {
                "nct_id": "NCT03615326",
                "trial_name": "DESTINY-Gastric01",
                "rationale": "Trastuzumab deruxtecan for HER2+ gastric cancer",
                "expected_rank": "top5",
                "confidence": "high"
            }
        ],
        "should_not_recommend": [],
        "key_biomarkers": ["HER2 positive"],
        "treatment_line": "first_line",
        "nccn_recommendation": "Trastuzumab + chemotherapy (Category 1)"
    },
    {
        "case_id": "hnscc_pdl1_high",
        "patient_summary": "64M with recurrent/metastatic head and neck squamous cell carcinoma (HPV-negative), PD-L1 CPS 30%, treatment-naive",
        "pdf_path": "test_data/sample_reports/hnscc_pdl1.pdf",
        "ground_truth_trials": [
            {
                "nct_id": "NCT02358031",
                "trial_name": "KEYNOTE-048",
                "rationale": "Pembrolizumab ± chemotherapy for PD-L1+ HNSCC, FDA approved",
                "expected_rank": "top3",
                "confidence": "very_high"
            },
            {
                "nct_id": "NCT02105636",
                "trial_name": "CheckMate 141",
                "rationale": "Nivolumab for recurrent HNSCC",
                "expected_rank": "top5",
                "confidence": "high"
            }
        ],
        "should_not_recommend": [],
        "key_biomarkers": ["PD-L1 high (CPS 30%)", "HPV-negative"],
        "treatment_line": "first_line",
        "nccn_recommendation": "Pembrolizumab monotherapy (Category 1 for CPS >=20) or pembrolizumab + chemo"
    },
    {
        "case_id": "rcc_clear_cell",
        "patient_summary": "58M with metastatic clear cell renal cell carcinoma, IMDC intermediate risk, no brain metastases, treatment-naive",
        "pdf_path": "test_data/sample_reports/rcc_clear_cell.pdf",
        "ground_truth_trials": [
            {
                "nct_id": "NCT02684006",
                "trial_name": "CheckMate 9ER",
                "rationale": "Nivolumab + cabozantinib for advanced RCC, FDA approved",
                "expected_rank": "top3",
                "confidence": "very_high"
            },
            {
                "nct_id": "NCT02853331",
                "trial_name": "KEYNOTE-426",
                "rationale": "Pembrolizumab + axitinib for advanced RCC",
                "expected_rank": "top5",
                "confidence": "high"
            }
        ],
        "should_not_recommend": [],
        "key_biomarkers": ["Clear cell histology", "IMDC intermediate risk"],
        "treatment_line": "first_line",
        "nccn_recommendation": "IO + TKI combination (Category 1: nivolumab + cabozantinib or pembrolizumab + axitinib)"
    },
    {
        "case_id": "hcc_sorafenib_progression",
        "patient_summary": "63M with unresectable hepatocellular carcinoma, Child-Pugh A, progressed on sorafenib",
        "pdf_path": "test_data/sample_reports/hcc_sorafenib.pdf",
        "ground_truth_trials": [
            {
                "nct_id": "NCT01004003",
                "trial_name": "RESORCE",
                "rationale": "Regorafenib for HCC after sorafenib progression, FDA approved",
                "expected_rank": "top3",
                "confidence": "very_high"
            },
            {
                "nct_id": "NCT01853618",
                "trial_name": "CELESTIAL",
                "rationale": "Cabozantinib for advanced HCC after prior systemic therapy",
                "expected_rank": "top5",
                "confidence": "high"
            }
        ],
        "should_not_recommend": [],
        "key_biomarkers": ["Child-Pugh A", "Sorafenib progression"],
        "treatment_line": "second_line",
        "nccn_recommendation": "Regorafenib (Category 1) or cabozantinib after sorafenib"
    },
    {
        "case_id": "bladder_fgfr3",
        "patient_summary": "66F with metastatic urothelial carcinoma, FGFR3 mutation/fusion, progressed on platinum-based chemotherapy",
        "pdf_path": "test_data/sample_reports/bladder_fgfr3.pdf",
        "ground_truth_trials": [
            {
                "nct_id": "NCT02365597",
                "trial_name": "BLC2001",
                "rationale": "Erdafitinib for FGFR-altered urothelial cancer, FDA approved",
                "expected_rank": "top3",
                "confidence": "very_high"
            },
            {
                "nct_id": "NCT02657486",
                "trial_name": "FIGHT-201",
                "rationale": "Pemigatinib for FGFR3-altered solid tumors",
                "expected_rank": "top5",
                "confidence": "high"
            }
        ],
        "should_not_recommend": [],
        "key_biomarkers": ["FGFR3 mutation"],
        "treatment_line": "second_line",
        "nccn_recommendation": "Erdafitinib (Category 1 for FGFR2/3 alterations)"
    },
    {
        "case_id": "lung_ros1_fusion",
        "patient_summary": "50F with metastatic NSCLC adenocarcinoma, ROS1 fusion (CD74-ROS1), no brain metastases, treatment-naive",
        "pdf_path": "test_data/sample_reports/lung_ros1.pdf",
        "ground_truth_trials": [
            {
                "nct_id": "NCT01970865",
                "trial_name": "PROFILE 1001",
                "rationale": "Crizotinib for ROS1+ NSCLC, FDA approved",
                "expected_rank": "top3",
                "confidence": "very_high"
            },
            {
                "nct_id": "NCT02568267",
                "trial_name": "TRIDENT-1",
                "rationale": "Repotrectinib for ROS1+ NSCLC",
                "expected_rank": "top5",
                "confidence": "high"
            }
        ],
        "should_not_recommend": [],
        "key_biomarkers": ["ROS1 fusion"],
        "treatment_line": "first_line",
        "nccn_recommendation": "Crizotinib or entrectinib (Category 1 for ROS1+)"
    },
    {
        "case_id": "melanoma_checkpoint_resistant",
        "patient_summary": "49M with metastatic melanoma (BRAF wild-type), progressed on pembrolizumab + ipilimumab combination",
        "pdf_path": "test_data/sample_reports/melanoma_resistant.pdf",
        "ground_truth_trials": [
            {
                "nct_id": "NCT03068455",
                "trial_name": "RELATIVITY-047",
                "rationale": "Relatlimab + nivolumab for checkpoint-naive melanoma (limited options post-resistance)",
                "expected_rank": "top5",
                "confidence": "medium"
            },
            {
                "nct_id": "NCT02631447",
                "trial_name": "Adoptive cell therapy trials",
                "rationale": "TIL therapy or other novel approaches for checkpoint-resistant melanoma",
                "expected_rank": "top5",
                "confidence": "medium"
            }
        ],
        "should_not_recommend": [],
        "key_biomarkers": ["BRAF wild-type", "Checkpoint inhibitor resistant"],
        "treatment_line": "third_line",
        "nccn_recommendation": "Clinical trial, adoptive cell therapy, or targeted therapy if actionable mutation"
    },
    {
        "case_id": "endometrial_msi_high",
        "patient_summary": "62F with recurrent endometrial carcinoma, MSI-H/dMMR, stage IV, progressed on carboplatin/paclitaxel",
        "pdf_path": "test_data/sample_reports/endometrial_msi.pdf",
        "ground_truth_trials": [
            {
                "nct_id": "NCT02628067",
                "trial_name": "KEYNOTE-158",
                "rationale": "Pembrolizumab for MSI-H/dMMR solid tumors, tissue-agnostic FDA approval",
                "expected_rank": "top3",
                "confidence": "very_high"
            },
            {
                "nct_id": "NCT03015129",
                "trial_name": "Dostarlimab trials",
                "rationale": "Dostarlimab for dMMR endometrial cancer, FDA approved",
                "expected_rank": "top5",
                "confidence": "high"
            }
        ],
        "should_not_recommend": [],
        "key_biomarkers": ["MSI-H", "dMMR"],
        "treatment_line": "second_line",
        "nccn_recommendation": "Pembrolizumab or dostarlimab (Category 1 for MSI-H/dMMR)"
    },
    {
        "case_id": "cholangiocarcinoma_idh1",
        "patient_summary": "57M with unresectable intrahepatic cholangiocarcinoma, IDH1 R132C mutation, progressed on gemcitabine/cisplatin",
        "pdf_path": "test_data/sample_reports/cholangiocarcinoma_idh1.pdf",
        "ground_truth_trials": [
            {
                "nct_id": "NCT02073994",
                "trial_name": "ClarIDHy",
                "rationale": "Ivosidenib for IDH1-mutated cholangiocarcinoma, FDA approved",
                "expected_rank": "top3",
                "confidence": "very_high"
            }
        ],
        "should_not_recommend": [],
        "key_biomarkers": ["IDH1 R132C mutation"],
        "treatment_line": "second_line",
        "nccn_recommendation": "Ivosidenib (Category 2A for IDH1-mutated cholangiocarcinoma)"
    },
    {
        "case_id": "glioblastoma_mgmt_methylated",
        "patient_summary": "54F with newly diagnosed glioblastoma, MGMT promoter methylated, IDH wild-type, status post-resection",
        "pdf_path": "test_data/sample_reports/glioblastoma_mgmt.pdf",
        "ground_truth_trials": [
            {
                "nct_id": "NCT00006353",
                "trial_name": "Stupp Protocol",
                "rationale": "Temozolomide + radiation for MGMT-methylated GBM, standard of care",
                "expected_rank": "top3",
                "confidence": "very_high"
            },
            {
                "nct_id": "NCT00943826",
                "trial_name": "TTFields (OPTUNE)",
                "rationale": "Tumor treating fields + temozolomide for newly diagnosed GBM",
                "expected_rank": "top5",
                "confidence": "high"
            }
        ],
        "should_not_recommend": [],
        "key_biomarkers": ["MGMT methylated", "IDH wild-type"],
        "treatment_line": "first_line",
        "nccn_recommendation": "Radiation + temozolomide (Category 1)"
    }
]

# Corresponding sample profiles
NEW_PROFILES = {
    "breast_tnbc_first_line": {
        "success": True,
        "demographics": {"age": 38, "sex": "Female", "location": "United States"},
        "diagnoses": "Stage IV triple-negative breast cancer. ER negative, PR negative, HER2 negative. Infiltrating ductal carcinoma. No visceral crisis.",
        "biomarkers": "PD-L1 positive (CPS 15% by IHC 22C3), ER/PR/HER2 negative (triple negative phenotype)",
        "treatment_history": {"prior_therapies": [], "treatment_line": "first_line", "progression_on": None},
        "search_terms": ["triple negative breast cancer", "PD-L1 positive", "metastatic breast cancer", "TNBC"]
    },
    "lung_alk_positive": {
        "success": True,
        "demographics": {"age": 47, "sex": "Male", "location": "United States"},
        "diagnoses": "Stage IV NSCLC adenocarcinoma with brain metastases. ALK rearrangement detected by FISH and NGS (EML4-ALK variant 1).",
        "biomarkers": "ALK rearrangement positive (EML4-ALK fusion), EGFR wild-type, PD-L1 <1%",
        "treatment_history": {"prior_therapies": [], "treatment_line": "first_line", "progression_on": None},
        "search_terms": ["NSCLC ALK positive", "ALK rearrangement", "brain metastases", "lung adenocarcinoma"]
    },
    "prostate_brca2_crpc": {
        "success": True,
        "demographics": {"age": 67, "sex": "Male", "location": "United States"},
        "diagnoses": "Metastatic castration-resistant prostate cancer (mCRPC) with bone metastases. Germline BRCA2 mutation detected.",
        "biomarkers": "Germline BRCA2 pathogenic variant, PSA rising on ADT, castrate testosterone levels",
        "treatment_history": {"prior_therapies": ["Abiraterone acetate + prednisone"], "treatment_line": "second_line", "progression_on": "Abiraterone"},
        "search_terms": ["mCRPC", "BRCA2 mutation", "prostate cancer", "castration resistant"]
    },
    "pancreatic_kras_g12c": {
        "success": True,
        "demographics": {"age": 61, "sex": "Female", "location": "United States"},
        "diagnoses": "Stage IV pancreatic adenocarcinoma with liver metastases. KRAS G12C mutation detected by NGS.",
        "biomarkers": "KRAS G12C mutation, TP53 mutated, microsatellite stable (MSS)",
        "treatment_history": {"prior_therapies": ["FOLFIRINOX"], "treatment_line": "second_line", "progression_on": "FOLFIRINOX"},
        "search_terms": ["pancreatic cancer", "KRAS G12C", "metastatic pancreatic", "KRAS mutation"]
    },
    "ovarian_brca1_platinum_sensitive": {
        "success": True,
        "demographics": {"age": 55, "sex": "Female", "location": "United States"},
        "diagnoses": "High-grade serous ovarian carcinoma, platinum-sensitive recurrence (8 months after completion of platinum therapy). Germline BRCA1 mutation.",
        "biomarkers": "Germline BRCA1 pathogenic variant, CA-125 elevated, platinum-sensitive recurrence",
        "treatment_history": {"prior_therapies": ["Carboplatin/paclitaxel"], "treatment_line": "second_line", "progression_on": None},
        "search_terms": ["ovarian cancer", "BRCA1 mutation", "platinum sensitive", "recurrent ovarian"]
    },
    "gastric_her2_positive": {
        "success": True,
        "demographics": {"age": 59, "sex": "Male", "location": "United States"},
        "diagnoses": "Stage IV gastric adenocarcinoma with peritoneal metastases. HER2 positive by IHC (3+) and FISH.",
        "biomarkers": "HER2 positive (IHC 3+, FISH amplified), MSS",
        "treatment_history": {"prior_therapies": [], "treatment_line": "first_line", "progression_on": None},
        "search_terms": ["gastric cancer", "HER2 positive", "metastatic gastric adenocarcinoma"]
    },
    "hnscc_pdl1_high": {
        "success": True,
        "demographics": {"age": 64, "sex": "Male", "location": "United States"},
        "diagnoses": "Recurrent/metastatic head and neck squamous cell carcinoma (oropharyngeal primary). HPV-negative, p16-negative.",
        "biomarkers": "PD-L1 CPS 30% by IHC 22C3, HPV-negative, p16-negative",
        "treatment_history": {"prior_therapies": [], "treatment_line": "first_line", "progression_on": None},
        "search_terms": ["head and neck cancer", "HNSCC", "PD-L1 high", "oropharyngeal cancer"]
    },
    "rcc_clear_cell": {
        "success": True,
        "demographics": {"age": 58, "sex": "Male", "location": "United States"},
        "diagnoses": "Metastatic clear cell renal cell carcinoma with lung metastases. IMDC intermediate risk (1 risk factor).",
        "biomarkers": "Clear cell histology, VHL mutation, IMDC intermediate risk",
        "treatment_history": {"prior_therapies": [], "treatment_line": "first_line", "progression_on": None},
        "search_terms": ["renal cell carcinoma", "clear cell RCC", "metastatic kidney cancer"]
    },
    "hcc_sorafenib_progression": {
        "success": True,
        "demographics": {"age": 63, "sex": "Male", "location": "United States"},
        "diagnoses": "Unresectable hepatocellular carcinoma, Child-Pugh A cirrhosis, progressed on sorafenib after 6 months.",
        "biomarkers": "Child-Pugh A, AFP elevated, Barcelona Clinic Liver Cancer (BCLC) stage C",
        "treatment_history": {"prior_therapies": ["Sorafenib"], "treatment_line": "second_line", "progression_on": "Sorafenib"},
        "search_terms": ["hepatocellular carcinoma", "HCC", "sorafenib progression", "liver cancer"]
    },
    "bladder_fgfr3": {
        "success": True,
        "demographics": {"age": 66, "sex": "Female", "location": "United States"},
        "diagnoses": "Metastatic urothelial carcinoma with FGFR3 S249C mutation. Progressed on cisplatin-based chemotherapy.",
        "biomarkers": "FGFR3 S249C mutation detected by NGS",
        "treatment_history": {"prior_therapies": ["Cisplatin + gemcitabine"], "treatment_line": "second_line", "progression_on": "Cisplatin-based chemotherapy"},
        "search_terms": ["urothelial carcinoma", "bladder cancer", "FGFR3 mutation", "metastatic bladder"]
    },
    "lung_ros1_fusion": {
        "success": True,
        "demographics": {"age": 50, "sex": "Female", "location": "United States"},
        "diagnoses": "Stage IV NSCLC adenocarcinoma with ROS1 fusion (CD74-ROS1). No brain metastases. Never smoker.",
        "biomarkers": "ROS1 fusion positive (CD74-ROS1), EGFR/ALK/BRAF wild-type, PD-L1 <1%",
        "treatment_history": {"prior_therapies": [], "treatment_line": "first_line", "progression_on": None},
        "search_terms": ["NSCLC ROS1 positive", "ROS1 fusion", "lung adenocarcinoma"]
    },
    "melanoma_checkpoint_resistant": {
        "success": True,
        "demographics": {"age": 49, "sex": "Male", "location": "United States"},
        "diagnoses": "Metastatic melanoma with visceral metastases. BRAF wild-type, NRAS wild-type. Progressed on pembrolizumab + ipilimumab.",
        "biomarkers": "BRAF wild-type, NRAS wild-type, checkpoint inhibitor resistant",
        "treatment_history": {"prior_therapies": ["Pembrolizumab + ipilimumab"], "treatment_line": "third_line", "progression_on": "Pembrolizumab + ipilimumab"},
        "search_terms": ["melanoma", "checkpoint inhibitor resistant", "metastatic melanoma"]
    },
    "endometrial_msi_high": {
        "success": True,
        "demographics": {"age": 62, "sex": "Female", "location": "United States"},
        "diagnoses": "Recurrent endometrial carcinoma, stage IV. MSI-H/dMMR by IHC. Endometrioid histology.",
        "biomarkers": "MSI-H (MSI-high), dMMR (MLH1/PMS2 loss by IHC), TP53 wild-type",
        "treatment_history": {"prior_therapies": ["Carboplatin + paclitaxel"], "treatment_line": "second_line", "progression_on": "Carboplatin/paclitaxel"},
        "search_terms": ["endometrial cancer", "MSI-H", "dMMR", "recurrent endometrial"]
    },
    "cholangiocarcinoma_idh1": {
        "success": True,
        "demographics": {"age": 57, "sex": "Male", "location": "United States"},
        "diagnoses": "Unresectable intrahepatic cholangiocarcinoma with IDH1 R132C mutation. Progressed on gemcitabine/cisplatin.",
        "biomarkers": "IDH1 R132C mutation detected by NGS, microsatellite stable",
        "treatment_history": {"prior_therapies": ["Gemcitabine + cisplatin"], "treatment_line": "second_line", "progression_on": "Gemcitabine/cisplatin"},
        "search_terms": ["cholangiocarcinoma", "IDH1 mutation", "intrahepatic cholangiocarcinoma"]
    },
    "glioblastoma_mgmt_methylated": {
        "success": True,
        "demographics": {"age": 54, "sex": "Female", "location": "United States"},
        "diagnoses": "Newly diagnosed glioblastoma multiforme (GBM), IDH wild-type, MGMT promoter methylated. Status post-gross total resection.",
        "biomarkers": "MGMT promoter methylated, IDH wild-type, 1p/19q non-codeleted",
        "treatment_history": {"prior_therapies": ["Surgical resection"], "treatment_line": "first_line", "progression_on": None},
        "search_terms": ["glioblastoma", "GBM", "MGMT methylated", "newly diagnosed GBM"]
    }
}

def expand_test_set():
    """Add 15 new test cases and create corresponding sample profiles"""

    # Get the project root
    import os
    script_dir = Path(__file__).parent
    project_root = script_dir.parent if script_dir.name == "evaluation" else script_dir

    # Load existing test_cases.json
    test_cases_path = project_root / "evaluation" / "test_cases.json"
    with open(test_cases_path, 'r') as f:
        data = json.load(f)

    # Add new test cases
    data["test_cases"].extend(NEW_TEST_CASES)
    data["version"] = "2.0"
    data["last_updated"] = "2024-11-07"

    # Save updated test_cases.json
    with open(test_cases_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"[OK] Updated test_cases.json: {len(data['test_cases'])} total cases")

    # Create sample profiles for new cases
    profiles_dir = project_root / "evaluation" / "sample_profiles"
    profiles_dir.mkdir(exist_ok=True, parents=True)

    for case_id, profile_data in NEW_PROFILES.items():
        profile_path = profiles_dir / f"{case_id}.json"
        with open(profile_path, 'w') as f:
            json.dump(profile_data, f, indent=2)
        print(f"[OK] Created profile: {profile_path}")

    print(f"\n{'='*70}")
    print(f"TEST SET EXPANSION COMPLETE")
    print(f"{'='*70}")
    print(f"Total test cases: {len(data['test_cases'])}")
    print(f"New cases added: {len(NEW_TEST_CASES)}")
    print(f"Sample profiles created: {len(NEW_PROFILES)}")

    # Summary by cancer type
    cancer_types = {}
    for case in data["test_cases"]:
        cancer_type = case["case_id"].split("_")[0]
        cancer_types[cancer_type] = cancer_types.get(cancer_type, 0) + 1

    print(f"\nCancer type distribution:")
    for cancer, count in sorted(cancer_types.items()):
        print(f"  {cancer}: {count}")

if __name__ == "__main__":
    expand_test_set()
