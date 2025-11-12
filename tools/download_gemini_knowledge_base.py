"""
Download clinical guidelines identified by Gemini Deep Research
Based on curated corpus from oncology guideline ecosystem analysis
"""
import requests
import time
from pathlib import Path
from typing import List, Dict, Tuple
import hashlib


class GeminiKnowledgeBaseDownloader:
    """Downloads the 54 clinical documents identified by Gemini"""
    
    def __init__(self, base_dir: str = "knowledge_base"):
        self.base_dir = Path(base_dir)
        self.guidelines_dir = self.base_dir / "guidelines"
        self.drug_labels_dir = self.base_dir / "drug_labels"
        self.biomarker_dir = self.base_dir / "biomarker_guides"
        
        # Ensure directories exist
        for directory in [self.guidelines_dir, self.drug_labels_dir, self.biomarker_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def download_file(self, url: str, filename: Path, max_retries: int = 3) -> Tuple[bool, str]:
        """
        Download a single PDF file with retry logic
        Returns: (success: bool, message: str)
        """
        for attempt in range(max_retries):
            try:
                # Set headers to mimic browser
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                response = requests.get(url, headers=headers, timeout=30, stream=True)
                
                if response.status_code == 200:
                    # Check if it's actually a PDF
                    content_type = response.headers.get('Content-Type', '')
                    if 'pdf' not in content_type.lower() and not url.endswith('.pdf'):
                        return False, f"Not a PDF (Content-Type: {content_type})"
                    
                    # Write file
                    with open(filename, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    # Verify file size
                    file_size = filename.stat().st_size
                    if file_size < 10000:  # Less than 10KB is suspicious
                        filename.unlink()  # Delete
                        return False, f"File too small ({file_size} bytes)"
                    
                    return True, f"Downloaded ({file_size // 1024} KB)"
                
                elif response.status_code == 404:
                    return False, "404 Not Found"
                
                else:
                    if attempt < max_retries - 1:
                        time.sleep(2)  # Wait before retry
                        continue
                    return False, f"HTTP {response.status_code}"
                    
            except requests.Timeout:
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return False, "Timeout"
            
            except Exception as e:
                return False, f"Error: {str(e)[:50]}"
        
        return False, "Max retries exceeded"
    
    def download_treatment_guidelines(self) -> Dict[str, any]:
        """Download major cancer treatment guidelines from Table 1"""
        print("\n" + "="*70)
        print("📥 DOWNLOADING TREATMENT GUIDELINES (Table 1)")
        print("="*70)
        
        guidelines = [
            ("https://www.nccn.org/patients/guidelines/content/PDF/lung-early-stage-patient.pdf", 
             "nccn_nsclc_early_stage.pdf", "NCCN NSCLC Early Stage"),
            
            ("https://www.nccn.org/patients/guidelines/content/PDF/lung-metastatic-patient.pdf", 
             "nccn_nsclc_metastatic.pdf", "NCCN NSCLC Metastatic"),
            
            ("https://icapem.es/wp-content/uploads/2023/02/GUIA-ESMO-NO-DRIVER-2023.pdf", 
             "esmo_nsclc_no_driver_2023.pdf", "ESMO NSCLC Non-Driver"),
            
            ("https://www.annalsofoncology.org/article/S0923-7534(21)01116-5/pdf", 
             "esmo_sclc_2021.pdf", "ESMO SCLC"),
            
            ("https://digitalcommons.library.tmc.edu/cgi/viewcontent.cgi?article=1189&context=uthgsbs_docs", 
             "asco_metastatic_breast_2024.pdf", "ASCO Metastatic Breast Cancer"),
            
            ("https://ascopubs.org/doi/pdf/10.1200/OP.24.00663", 
             "asco_breast_cdk46_update_2024.pdf", "ASCO Breast CDK4/6 Update"),
            
            ("https://www.nccn.org/patients/guidelines/content/PDF/stage_iv_breast-patient.pdf", 
             "nccn_metastatic_breast.pdf", "NCCN Metastatic Breast"),
            
            ("https://www.nccn.org/patients/guidelines/content/PDF/breastcancerscreening-patient.pdf", 
             "nccn_breast_screening.pdf", "NCCN Breast Screening"),
            
            ("https://ascopubs.org/doi/pdf/10.1200/JCO.21.02538", 
             "asco_stage_ii_colon_2022.pdf", "ASCO Stage II Colon"),
            
            ("https://www.nccn.org/patients/guidelines/content/PDF/colon-patient.pdf", 
             "nccn_colon_cancer.pdf", "NCCN Colon Cancer"),
            
            ("https://daytonphysicians.com/wp-content/uploads/2022/10/prostate-advanced-patient.pdf", 
             "nccn_prostate_advanced.pdf", "NCCN Advanced Prostate"),
            
            ("https://www.nccn.org/patients/guidelines/content/PDF/prostate-early-patient.pdf", 
             "nccn_prostate_early.pdf", "NCCN Early Prostate"),
            
            ("https://www.annalsofoncology.org/article/S0923-7534(20)39995-3/pdf", 
             "esmo_prostate_2020.pdf", "ESMO Prostate"),
            
            ("https://www.nccn.org/patients/guidelines/content/PDF/melanoma-patient.pdf", 
             "nccn_melanoma.pdf", "NCCN Melanoma"),
            
            ("https://www.esgo.org/media/2025/08/Pocket-Guidelines_Ovarian-cancer-consensus.pdfNCCN", 
             "esgo_esmo_ovarian_2024.pdf", "ESGO/ESMO Ovarian"),
            
            ("https://www.nccn.org/patients/guidelines/content/PDF/ovarian-patient.pdf", 
             "nccn_ovarian.pdf", "NCCN Ovarian"),
            
            ("https://www.nccn.org/patients/guidelines/content/PDF/cervical-patient-guideline.pdf", 
             "nccn_cervical.pdf", "NCCN Cervical"),
            
            ("https://www.mdanderson.org/documents/for-physicians/algorithms/cancer-treatment/ca-treatment-pancreatic-web-algorithm.pdf", 
             "mdacc_pancreatic_algorithm.pdf", "MD Anderson Pancreatic"),
            
            ("https://www.annalsofoncology.org/article/S0923-7534(21)04558-8/pdf", 
             "esmo_pancreatic_2021.pdf", "ESMO Pancreatic"),
            
            ("https://www.nccn.org/patients/guidelines/content/PDF/hn-nasopharynx-patient.pdf", 
             "nccn_nasopharynx.pdf", "NCCN Nasopharyngeal"),
            
            ("https://www.annalsofoncology.org/article/S0923-7534(20)42442-8/pdf", 
             "ehns_esmo_head_neck_2020.pdf", "EHNS/ESMO Head & Neck"),
        ]
        
        results = {"success": [], "failed": []}
        
        for url, filename, description in guidelines:
            filepath = self.guidelines_dir / filename
            print(f"\n  Downloading: {description}")
            print(f"    URL: {url[:60]}...")
            
            success, message = self.download_file(url, filepath)
            
            if success:
                results["success"].append(description)
                print(f"    [OK] {message}")
            else:
                results["failed"].append((description, message))
                print(f"    [X] {message}")
            
            time.sleep(1)  # Be respectful to servers
        
        return results
    
    def download_biomarker_guidelines(self) -> Dict[str, any]:
        """Download biomarker testing guidelines from Table 2"""
        print("\n" + "="*70)
        print("📥 DOWNLOADING BIOMARKER TESTING GUIDELINES (Table 2)")
        print("="*70)
        
        biomarkers = [
            ("https://ascopubs.org/doi/pdf/10.1200/JOP.18.00035", 
             "cap_asco_lung_molecular_2020.pdf", "CAP/ASCO Lung Molecular Testing"),
            
            ("https://www.captodayonline.com/wp-content/uploads/2024/07/PD-L1-and-TMB-Testing-of-Patients-With-Lung-Cancer-for-Selection-of-Immune-Checkpoint-Inhibitor-Therapies-Guideline-From-the-College-of-American-Pathologists-Association-for-Molecular-Pathology-International-Association-for-the-Study-of-Lung-Cancer-Pulmonary-Pathology-Society-and-LUNGevity-Foundation.pdf", 
             "cap_pdl1_tmb_lung_2024.pdf", "CAP PD-L1/TMB Testing"),
            
            ("https://ascopubs.org/doi/pdf/10.1200/JCO.22.02864", 
             "asco_cap_her2_breast_2023.pdf", "ASCO/CAP HER2 Breast 2023"),
            
            ("https://ascopubs.org/doi/pdf/10.1200/OP.22.00518", 
             "asco_cap_mmr_msi_2023.pdf", "ASCO/CAP MMR/MSI 2023"),
        ]
        
        results = {"success": [], "failed": []}
        
        for url, filename, description in biomarkers:
            filepath = self.biomarker_dir / filename
            print(f"\n  Downloading: {description}")
            print(f"    URL: {url[:60]}...")
            
            success, message = self.download_file(url, filepath)
            
            if success:
                results["success"].append(description)
                print(f"    [OK] {message}")
            else:
                results["failed"].append((description, message))
                print(f"    [X] {message}")
            
            time.sleep(1)
        
        return results
    
    def download_fda_drug_labels(self) -> Dict[str, any]:
        """Download FDA oncology drug labels from Table 3"""
        print("\n" + "="*70)
        print("📥 DOWNLOADING FDA DRUG LABELS (Table 3)")
        print("="*70)
        
        drugs = [
            ("https://www.accessdata.fda.gov/drugsatfda_docs/label/2024/208065s033lbl.pdf", 
             "fda_tagrisso_osimertinib_2024_v33.pdf", "Tagrisso (Osimertinib) 2024"),
            
            ("https://www.accessdata.fda.gov/drugsatfda_docs/label/2024/125514s128lbl.pdf", 
             "fda_opdivo_nivolumab_2024.pdf", "Opdivo (Nivolumab) 2024"),
            
            ("https://www.accessdata.fda.gov/drugsatfda_docs/label/2024/125514s124lbl.pdf", 
             "fda_keytruda_pembrolizumab_2024.pdf", "Keytruda (Pembrolizumab) 2024"),
            
            ("https://www.accessdata.fda.gov/drugsatfda_docs/label/2025/125377s133lbl.pdf", 
             "fda_yervoy_ipilimumab_2025.pdf", "Yervoy (Ipilimumab) 2025"),
            
            ("https://www.accessdata.fda.gov/drugsatfda_docs/label/2025/207103s021,212436s009lbl.pdf", 
             "fda_ibrance_palbociclib_2025.pdf", "Ibrance (Palbociclib) 2025"),
            
            ("https://www.accessdata.fda.gov/drugsatfda_docs/label/2025/203415s024,213674s012lbl.pdf", 
             "fda_xtandi_enzalutamide_2025.pdf", "Xtandi (Enzalutamide) 2025"),
            
            ("https://www.accessdata.fda.gov/drugsatfda_docs/label/2024/209604s011lbl.pdf", 
             "fda_gemcitabine_2024.pdf", "Gemcitabine 2024"),
        ]
        
        results = {"success": [], "failed": []}
        
        for url, filename, description in drugs:
            filepath = self.drug_labels_dir / filename
            print(f"\n  Downloading: {description}")
            print(f"    URL: {url[:60]}...")
            
            success, message = self.download_file(url, filepath)
            
            if success:
                results["success"].append(description)
                print(f"    [OK] {message}")
            else:
                results["failed"].append((description, message))
                print(f"    [X] {message}")
            
            time.sleep(1)
        
        return results
    
    def download_all(self) -> Dict[str, any]:
        """Download complete Gemini-curated knowledge base"""
        print("\n" + "="*70)
        print("🚀 DOWNLOADING GEMINI-CURATED CLINICAL KNOWLEDGE BASE")
        print("   Source: Gemini Deep Research Analysis")
        print("   Total Expected: ~32 documents")
        print("="*70)
        
        all_results = {
            "treatment_guidelines": self.download_treatment_guidelines(),
            "biomarker_guidelines": self.download_biomarker_guidelines(),
            "fda_drug_labels": self.download_fda_drug_labels()
        }
        
        # Calculate totals
        total_success = (
            len(all_results["treatment_guidelines"]["success"]) +
            len(all_results["biomarker_guidelines"]["success"]) +
            len(all_results["fda_drug_labels"]["success"])
        )
        
        total_failed = (
            len(all_results["treatment_guidelines"]["failed"]) +
            len(all_results["biomarker_guidelines"]["failed"]) +
            len(all_results["fda_drug_labels"]["failed"])
        )
        
        # Print summary
        print("\n" + "="*70)
        print("[CHART] DOWNLOAD SUMMARY")
        print("="*70)
        print(f"[OK] Successfully Downloaded: {total_success}")
        print(f"   - Treatment Guidelines: {len(all_results['treatment_guidelines']['success'])}")
        print(f"   - Biomarker Guidelines: {len(all_results['biomarker_guidelines']['success'])}")
        print(f"   - FDA Drug Labels: {len(all_results['fda_drug_labels']['success'])}")
        
        if total_failed > 0:
            print(f"\n[X] Failed Downloads: {total_failed}")
            for category in all_results.values():
                for doc, reason in category["failed"]:
                    print(f"   - {doc}: {reason}")
        
        print("\n" + "="*70)
        if total_success >= 20:
            print("[OK] KNOWLEDGE BASE DOWNLOAD COMPLETE!")
            print(f"   {total_success} documents ready for RAG system")
        else:
            print("[!]  PARTIAL SUCCESS")
            print(f"   Only {total_success} documents downloaded (expected ~32)")
            print("   This may still be sufficient for proof-of-concept")
        print("="*70)
        
        return all_results


if __name__ == "__main__":
    downloader = GeminiKnowledgeBaseDownloader()
    downloader.download_all()