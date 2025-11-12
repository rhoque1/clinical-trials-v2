"""
Download free clinical knowledge base for RAG system
Uses publicly available resources from NCI, FDA, and academic sources
"""
import requests
import time
from pathlib import Path
from typing import List, Dict


class KnowledgeBaseDownloader:
    """Downloads public clinical guidelines and drug information"""
    
    def __init__(self, base_dir: str = "knowledge_base"):
        self.base_dir = Path(base_dir)
        self.guidelines_dir = self.base_dir / "guidelines"
        self.drug_labels_dir = self.base_dir / "drug_labels"
        self.biomarker_dir = self.base_dir / "biomarker_guides"
        
    def download_nci_pdq_summaries(self) -> List[str]:
        """
        Download NCI PDQ treatment summaries (HTML format)
        These are comprehensive, evidence-based cancer treatment guidelines
        """
        print("\n📥 Downloading NCI PDQ Treatment Summaries...")
        
        # Key cancer types for proof-of-concept
        cancer_types = [
            "non-small-cell-lung-cancer",
            "breast-cancer", 
            "colorectal-cancer",
            "prostate-cancer",
            "melanoma",
            "ovarian-epithelial-fallopian-tube-peritoneal-cancer",
            "cervical-cancer",
            "pancreatic-cancer"
        ]
        
        downloaded = []
        base_url = "https://www.cancer.gov/types/{}/hp"
        
        for cancer in cancer_types:
            try:
                url = base_url.format(cancer)
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    filename = self.guidelines_dir / f"nci_pdq_{cancer}.html"
                    filename.write_text(response.text, encoding='utf-8')
                    downloaded.append(str(filename))
                    print(f"  [+] Downloaded: {cancer}")
                else:
                    print(f"  [-] Failed: {cancer} (status {response.status_code})")
                
                time.sleep(1)  # Be respectful of NCI servers
                
            except Exception as e:
                print(f"  [-] Error downloading {cancer}: {str(e)}")
        
        print(f"\n[OK] Downloaded {len(downloaded)} NCI PDQ summaries")
        return downloaded
    
    def create_biomarker_guide(self) -> str:
        """
        Create a comprehensive biomarker interpretation guide
        Based on public knowledge - NCCN, ASCO, CAP guidelines
        """
        print("\n📝 Creating biomarker interpretation guide...")
        
        biomarker_content = """
# Clinical Biomarker Interpretation Guide
*Compiled from NCCN, ASCO, CAP public guidelines*

## EGFR Mutations (Non-Small Cell Lung Cancer)

### Actionable Mutations:
- **Exon 19 deletions** (45% of EGFR mutations)
  - First-line: Osimertinib, Erlotinib, Gefitinib, Afatinib
  - Prognosis: Favorable response to TKIs
  
- **L858R (Exon 21)** (40% of EGFR mutations)
  - First-line: Same as exon 19 deletions
  - Slightly less responsive than exon 19 deletions
  
- **T790M** (resistance mutation)
  - Acquired resistance to 1st/2nd gen TKIs
  - Treatment: Osimertinib (3rd gen TKI)

### Uncommon Mutations:
- Exon 20 insertions (5%): Poor TKI response
- G719X, L861Q, S768I: Respond to 2nd gen TKIs

### Clinical Trial Considerations:
- EGFR+ patients should preferentially enroll in EGFR-targeted trials
- Combination trials: EGFR TKI + chemotherapy/immunotherapy
- Resistance mechanism trials if progression on TKI

---

## KRAS Mutations

### G12C Mutation:
- **Actionable**: Sotorasib, Adagrasib approved
- Prevalence: 13% of NSCLC, 3-4% of CRC
- Clinical trials: KRAS G12C-specific inhibitors

### Other KRAS Mutations (G12D, G12V, G13D):
- **Not directly targetable** (as of 2024)
- Clinical significance: Poor response to EGFR TKIs
- Trial consideration: Combination strategies, MEK inhibitors

---

## PD-L1 Expression (Immunotherapy Biomarker)

### Tumor Proportion Score (TPS):
- **>=50%**: High expression
  - First-line pembrolizumab monotherapy approved (NSCLC)
  - Strong predictor of response
  
- **1-49%**: Intermediate expression
  - Consider combination: chemo + immunotherapy
  
- **<1%**: Low/negative
  - Immunotherapy less likely to benefit
  - Consider other biomarkers (TMB, MSI)

### Combined Positive Score (CPS):
- Used in gastric, cervical, HNSCC
- CPS >=10: Pembrolizumab approved
- CPS >=1: Consider combination therapy

---

## Microsatellite Instability (MSI) / Mismatch Repair (MMR)

### MSI-High / dMMR:
- **Universal immunotherapy responders**
- Pembrolizumab approved (tumor-agnostic)
- Prevalence: 15% CRC, 30% endometrial, <5% most others
- Clinical trials: All immunotherapy trials

### MSS / pMMR:
- Standard microsatellite stable tumors
- Immunotherapy less effective (except PD-L1 high)

---

## HER2 (ERBB2)

### Breast Cancer:
- **IHC 3+ or FISH amplified**: HER2-positive
  - Trastuzumab, Pertuzumab, T-DM1, T-DXd
  - Excellent prognosis with targeted therapy

### Gastric Cancer:
- HER2+ (10-20% of cases)
- Trastuzumab + chemotherapy

### Emerging: HER2 in Other Cancers
- CRC, NSCLC, Bladder: HER2 amplifications
- Clinical trials: HER2-directed ADCs (T-DXd, T-DM1)

---

## BRAF V600E

### Melanoma:
- **50% of melanomas**
- First-line: Dabrafenib + Trametinib
- Excellent response rates

### Colorectal Cancer:
- **~10% of CRC**
- Poor prognosis marker
- Treatment: BRAF + EGFR inhibitor + chemo
- Clinical trials: Novel BRAF combinations

### NSCLC, Thyroid:
- BRAF inhibitors effective
- Consider combination strategies

---

## ALK Rearrangements

### NSCLC (3-5%):
- First-line: Alectinib, Brigatinib, Lorlatinib
- Excellent long-term outcomes
- Brain metastases: CNS-penetrant ALK inhibitors

---

## ROS1 Rearrangements

### NSCLC (1-2%):
- Crizotinib, Entrectinib approved
- Similar biology to ALK
- Clinical trials: Next-gen ROS1 inhibitors

---

## NTRK Fusions (Tumor-Agnostic)

### Pan-cancer biomarker:
- Larotrectinib, Entrectinib (FDA approved)
- Rare: <1% most cancers, enriched in some pediatric
- Clinical trials: Next-gen TRK inhibitors

---

## PIK3CA Mutations

### Breast Cancer (HR+/HER2-):
- **Alpelisib + Fulvestrant** (FDA approved)
- ~40% of HR+ breast cancers
- Clinical trials: Next-gen PI3K inhibitors

### Other Cancers:
- Emerging target in cervical, head/neck, endometrial
- Clinical trials available

---

## Tumor Mutational Burden (TMB)

### TMB-High (>=10 mutations/Mb):
- Pembrolizumab approved (tumor-agnostic)
- Predictor of immunotherapy response
- Independent of PD-L1

---

## Clinical Trial Matching Logic:

1. **Tier 1 (Highest Priority)**:
   - Actionable mutations with FDA-approved drugs
   - Examples: EGFR exon 19 del, ALK+, BRAF V600E, MSI-H

2. **Tier 2 (Clinical Trial Recommended)**:
   - Emerging targets: KRAS G12C, HER2 amplifications, NTRK fusions
   - Resistance mutations: EGFR T790M

3. **Tier 3 (Prognostic/Research)**:
   - TP53, ARID1A, STK11 (no direct therapy)
   - Useful for stratification, clinical trial eligibility

---

**Last Updated**: January 2025
**Sources**: NCCN Guidelines, ASCO, CAP, FDA Drug Labels
"""
        
        filename = self.biomarker_dir / "biomarker_interpretation_guide.md"
        filename.write_text(biomarker_content, encoding='utf-8')
        print(f"[OK] Created biomarker guide: {filename}")
        
        return str(filename)
    
    def create_fda_drug_reference(self) -> str:
        """
        Create a reference guide for common oncology drugs
        Based on FDA-approved indications
        """
        print("\n📝 Creating FDA drug reference...")
        
        drug_content = """
# FDA-Approved Oncology Drugs Reference
*Common cancer therapeutics and their indications*

## Targeted Therapies

### EGFR Inhibitors (NSCLC):
- **Osimertinib** (Tagrisso): 1st line EGFR+, T790M resistance
- **Erlotinib** (Tarceva): 1st line EGFR+
- **Gefitinib** (Iressa): 1st line EGFR+
- **Afatinib** (Gilotrif): 1st line EGFR+ (exon 19 del, L858R)
- **Amivantamab**: EGFR exon 20 insertions

### ALK Inhibitors:
- **Alectinib** (Alecensa): 1st line ALK+
- **Brigatinib** (Alunbrig): 1st/2nd line ALK+
- **Lorlatinib** (Lorbrena): ALK+ (any line, brain mets)
- **Crizotinib** (Xalkori): ALK+, ROS1+

### KRAS G12C Inhibitors:
- **Sotorasib** (Lumakras): KRAS G12C+ NSCLC (post 1 line)
- **Adagrasib** (Krazati): KRAS G12C+ NSCLC

### HER2-Directed:
- **Trastuzumab** (Herceptin): HER2+ breast, gastric
- **Pertuzumab** (Perjeta): HER2+ breast (combo with trastuzumab)
- **T-DM1** (Kadcyla): HER2+ breast (ADC)
- **T-DXd** (Enhertu): HER2+ breast, gastric, NSCLC (ADC)

### BRAF/MEK Inhibitors:
- **Dabrafenib + Trametinib**: BRAF V600E/K melanoma, NSCLC, thyroid
- **Vemurafenib** (Zelboraf): BRAF V600E melanoma
- **Encorafenib + Binimetinib**: BRAF V600E melanoma, CRC

---

## Immunotherapy (Checkpoint Inhibitors)

### PD-1 Inhibitors:
- **Pembrolizumab** (Keytruda):
  - NSCLC (PD-L1 >=1%), melanoma, HNSCC
  - MSI-H/dMMR (tumor-agnostic)
  - TMB-H >=10 mut/Mb (tumor-agnostic)
  
- **Nivolumab** (Opdivo):
  - Melanoma, NSCLC, RCC, Hodgkin, HNSCC
  - MSI-H/dMMR CRC

### PD-L1 Inhibitors:
- **Atezolizumab** (Tecentriq): NSCLC, SCLC, urothelial
- **Durvalumab** (Imfinzi): Stage III NSCLC (consolidation)

### CTLA-4 Inhibitors:
- **Ipilimumab** (Yervoy): Melanoma (mono or + nivolumab)

---

## Chemotherapy (Key Regimens)

### Platinum-Based:
- **Cisplatin/Carboplatin**: NSCLC, ovarian, cervical, bladder
- **Oxaliplatin**: Colorectal (FOLFOX)

### Taxanes:
- **Paclitaxel**: Breast, ovarian, NSCLC
- **Docetaxel**: Breast, NSCLC, prostate

### Antimetabolites:
- **Pemetrexed**: Non-squamous NSCLC
- **Gemcitabine**: Pancreatic, bladder, NSCLC
- **5-FU**: Colorectal (FOLFOX, FOLFIRI)

---

## Hormone Therapies

### Breast Cancer (HR+):
- **CDK4/6 Inhibitors**: Palbociclib, Ribociclib, Abemaciclib
  - + Aromatase inhibitor or Fulvestrant
- **Fulvestrant**: ER+ breast (2nd line)
- **Tamoxifen**: ER+ breast (pre/post-menopausal)

### Prostate Cancer:
- **Enzalutamide** (Xtandi): Castration-resistant prostate
- **Abiraterone** (Zytiga): Castration-resistant prostate

---

**Last Updated**: January 2025
**Source**: FDA Drug Labels, NCCN Compendia
"""
        
        filename = self.drug_labels_dir / "fda_oncology_drugs.md"
        filename.write_text(drug_content, encoding='utf-8')
        print(f"[OK] Created drug reference: {filename}")
        
        return str(filename)
    
    def download_all(self) -> Dict[str, List[str]]:
        """Download complete knowledge base"""
        print("\n" + "="*60)
        print("🚀 DOWNLOADING CLINICAL KNOWLEDGE BASE")
        print("="*60)
        
        results = {
            "nci_pdq": [],
            "biomarker_guide": None,
            "drug_reference": None
        }
        
        # Download NCI PDQ summaries
        results["nci_pdq"] = self.download_nci_pdq_summaries()
        
        # Create reference guides
        results["biomarker_guide"] = self.create_biomarker_guide()
        results["drug_reference"] = self.create_fda_drug_reference()
        
        print("\n" + "="*60)
        print("[OK] KNOWLEDGE BASE DOWNLOAD COMPLETE!")
        print("="*60)
        print(f"Total files: {len(results['nci_pdq']) + 2}")
        print(f"  - NCI PDQ Summaries: {len(results['nci_pdq'])}")
        print(f"  - Biomarker Guide: 1")
        print(f"  - Drug Reference: 1")
        print("="*60)
        
        return results


if __name__ == "__main__":
    downloader = KnowledgeBaseDownloader()
    downloader.download_all()