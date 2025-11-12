"""
Build Clinical Trial Eligibility Corpus for RAG Enhancement

This script extracts eligibility criteria from ClinicalTrials.gov across major
cancer types and structures them into documents for RAG ingestion.
"""

import requests
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class EligibilityCorpusBuilder:
    """Builds a corpus of trial eligibility patterns from ClinicalTrials.gov"""

    def __init__(self, output_dir: str = "knowledge_base/trial_patterns"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.base_url = "https://clinicaltrials.gov/api/v2/studies"

        # Major cancer types to build corpus for
        self.cancer_types = [
            "cervical cancer",
            "lung cancer",
            "breast cancer",
            "colorectal cancer",
            "melanoma",
            "ovarian cancer",
            "prostate cancer",
            "pancreatic cancer",
            "gastric cancer",
            "head and neck cancer"
        ]

        # Biomarkers to specifically track
        self.biomarkers = [
            "EGFR", "ALK", "ROS1", "BRAF", "KRAS", "NRAS",
            "PIK3CA", "TP53", "PTEN", "HER2", "ERBB2",
            "PD-L1", "MSI-H", "dMMR", "TMB-H",
            "BRCA1", "BRCA2", "ATM", "PALB2"
        ]

    def fetch_trials_for_condition(self, condition: str, max_studies: int = 200) -> List[Dict]:
        """Fetch trials from ClinicalTrials.gov API v2.0"""

        print(f"\n[SEARCH] Fetching trials for: {condition}")

        params = {
            "query.cond": condition,
            "filter.overallStatus": "RECRUITING,NOT_YET_RECRUITING,ACTIVE_NOT_RECRUITING,COMPLETED",
            "pageSize": min(max_studies, 1000),
            "format": "json",
            "fields": "NCTId,BriefTitle,Phase,OverallStatus,EligibilityCriteria,InterventionName,Condition,BioSpecRetention,BioSpecDescription"
        }

        try:
            response = requests.get(self.base_url, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()

            studies = data.get("studies", [])
            print(f"  [+] Found {len(studies)} trials")

            return studies

        except Exception as e:
            print(f"  [-] Error: {str(e)[:100]}")
            return []

    def parse_study_eligibility(self, study: Dict) -> Optional[Dict]:
        """Extract eligibility criteria and key metadata from study"""

        try:
            protocol = study.get("protocolSection", {})

            # Identification
            identification = protocol.get("identificationModule", {})
            nct_id = identification.get("nctId", "")
            title = identification.get("briefTitle", "")

            # Status and phase
            status_module = protocol.get("statusModule", {})
            status = status_module.get("overallStatus", "")

            design_module = protocol.get("designModule", {})
            phases = design_module.get("phases", [])
            phase = phases[0] if phases else "Not specified"

            # Conditions
            conditions_module = protocol.get("conditionsModule", {})
            conditions = conditions_module.get("conditions", [])

            # Interventions
            arms_module = protocol.get("armsInterventionsModule", {})
            interventions = []
            for intervention in arms_module.get("interventions", []):
                name = intervention.get("name", "")
                if name:
                    interventions.append(name)

            # Eligibility criteria - THIS IS THE KEY DATA
            eligibility_module = protocol.get("eligibilityModule", {})
            eligibility_text = eligibility_module.get("eligibilityCriteria", "")

            # Skip if no eligibility criteria
            if not eligibility_text or len(eligibility_text) < 50:
                return None

            min_age = eligibility_module.get("minimumAge", "")
            max_age = eligibility_module.get("maximumAge", "")
            sex = eligibility_module.get("sex", "")
            healthy_volunteers = eligibility_module.get("healthyVolunteers", "No")

            # Check for biomarker mentions
            mentioned_biomarkers = []
            eligibility_lower = eligibility_text.lower()
            for biomarker in self.biomarkers:
                if biomarker.lower() in eligibility_lower:
                    mentioned_biomarkers.append(biomarker)

            return {
                "nct_id": nct_id,
                "title": title,
                "phase": phase,
                "status": status,
                "conditions": conditions,
                "interventions": interventions[:5],  # Limit to top 5
                "eligibility_criteria": eligibility_text,
                "min_age": min_age,
                "max_age": max_age,
                "sex": sex,
                "healthy_volunteers": healthy_volunteers,
                "biomarkers_mentioned": mentioned_biomarkers
            }

        except Exception as e:
            return None

    def build_cancer_type_corpus(self, cancer_type: str, max_trials: int = 200):
        """Build eligibility corpus for a specific cancer type"""

        print(f"\n{'='*70}")
        print(f"Building corpus for: {cancer_type.upper()}")
        print(f"{'='*70}")

        # Fetch trials
        studies = self.fetch_trials_for_condition(cancer_type, max_studies=max_trials)

        if not studies:
            print(f"[!]  No studies found for {cancer_type}")
            return

        # Parse eligibility criteria
        print(f"\n[LIST] Parsing eligibility criteria...")
        parsed_trials = []

        for study in studies:
            parsed = self.parse_study_eligibility(study)
            if parsed:
                parsed_trials.append(parsed)

        print(f"  [+] Parsed {len(parsed_trials)} trials with eligibility criteria")

        if len(parsed_trials) == 0:
            return

        # Build structured document
        self._write_corpus_document(cancer_type, parsed_trials)

        # Build biomarker-specific document
        self._write_biomarker_document(cancer_type, parsed_trials)

    def _write_corpus_document(self, cancer_type: str, trials: List[Dict]):
        """Write main eligibility corpus document"""

        filename = cancer_type.replace(" ", "_").lower() + "_eligibility_patterns.txt"
        filepath = self.output_dir / filename

        print(f"\n[DISK] Writing corpus document: {filename}")

        with open(filepath, 'w', encoding='utf-8') as f:
            # Header
            f.write(f"# Clinical Trial Eligibility Patterns: {cancer_type.title()}\n")
            f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d')}\n")
            f.write(f"# Total Trials: {len(trials)}\n\n")

            f.write(f"This document contains eligibility criteria patterns from {len(trials)} ")
            f.write(f"clinical trials for {cancer_type}. This data is used to enhance ")
            f.write(f"trial matching and eligibility prediction.\n\n")

            # Group by phase
            phases = {}
            for trial in trials:
                phase = trial['phase']
                if phase not in phases:
                    phases[phase] = []
                phases[phase].append(trial)

            # Write trials organized by phase
            for phase in sorted(phases.keys()):
                phase_trials = phases[phase]

                f.write(f"\n{'='*70}\n")
                f.write(f"## {phase} TRIALS ({len(phase_trials)} trials)\n")
                f.write(f"{'='*70}\n\n")

                for trial in phase_trials[:50]:  # Limit to top 50 per phase
                    f.write(f"### Trial: {trial['nct_id']}\n")
                    f.write(f"**Title:** {trial['title'][:200]}\n")
                    f.write(f"**Phase:** {trial['phase']}\n")
                    f.write(f"**Status:** {trial['status']}\n")

                    if trial['interventions']:
                        f.write(f"**Interventions:** {', '.join(trial['interventions'][:3])}\n")

                    if trial['biomarkers_mentioned']:
                        f.write(f"**Biomarkers Mentioned:** {', '.join(trial['biomarkers_mentioned'])}\n")

                    f.write(f"**Age Range:** {trial['min_age']} to {trial['max_age']}\n")
                    f.write(f"**Sex:** {trial['sex']}\n\n")

                    f.write(f"**Eligibility Criteria:**\n")
                    f.write(f"{trial['eligibility_criteria']}\n\n")
                    f.write("-" * 70 + "\n\n")

        print(f"  [+] Wrote {filepath}")

    def _write_biomarker_document(self, cancer_type: str, trials: List[Dict]):
        """Write biomarker-specific trial document"""

        # Filter trials that mention biomarkers
        biomarker_trials = [t for t in trials if t['biomarkers_mentioned']]

        if len(biomarker_trials) == 0:
            return

        filename = cancer_type.replace(" ", "_").lower() + "_biomarker_trials.txt"
        filepath = self.output_dir / filename

        print(f"[DISK] Writing biomarker document: {filename}")

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Biomarker-Specific Trials: {cancer_type.title()}\n")
            f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d')}\n")
            f.write(f"# Trials with Biomarker Requirements: {len(biomarker_trials)}\n\n")

            # Group by biomarker
            by_biomarker = {}
            for trial in biomarker_trials:
                for biomarker in trial['biomarkers_mentioned']:
                    if biomarker not in by_biomarker:
                        by_biomarker[biomarker] = []
                    by_biomarker[biomarker].append(trial)

            # Write by biomarker
            for biomarker in sorted(by_biomarker.keys()):
                marker_trials = by_biomarker[biomarker]

                f.write(f"\n{'='*70}\n")
                f.write(f"## {biomarker} ({len(marker_trials)} trials)\n")
                f.write(f"{'='*70}\n\n")

                for trial in marker_trials[:20]:  # Top 20 per biomarker
                    f.write(f"**{trial['nct_id']}** - {trial['title'][:150]}\n")
                    f.write(f"Phase: {trial['phase']} | Status: {trial['status']}\n")

                    if trial['interventions']:
                        f.write(f"Interventions: {', '.join(trial['interventions'][:2])}\n")

                    # Extract biomarker-specific criteria
                    criteria = trial['eligibility_criteria']
                    # Find sentences containing the biomarker
                    sentences = criteria.split('.')
                    relevant = [s.strip() for s in sentences if biomarker.lower() in s.lower()]

                    if relevant:
                        f.write(f"\nBiomarker Criteria:\n")
                        for sentence in relevant[:3]:
                            f.write(f"  - {sentence}\n")

                    f.write("\n" + "-" * 70 + "\n\n")

        print(f"  [+] Wrote {filepath}")

    def build_complete_corpus(self, trials_per_cancer: int = 200):
        """Build complete eligibility corpus across all cancer types"""

        print("\n" + "="*70)
        print("BUILDING CLINICAL TRIAL ELIGIBILITY CORPUS")
        print("="*70)
        print(f"\nCancer types: {len(self.cancer_types)}")
        print(f"Max trials per type: {trials_per_cancer}")
        print(f"Output directory: {self.output_dir}")

        start_time = time.time()

        for i, cancer_type in enumerate(self.cancer_types, 1):
            print(f"\n[{i}/{len(self.cancer_types)}] Processing {cancer_type}...")

            self.build_cancer_type_corpus(cancer_type, max_trials=trials_per_cancer)

            # Rate limiting - be nice to ClinicalTrials.gov API
            if i < len(self.cancer_types):
                print(f"\n[~] Waiting 3 seconds before next request...")
                time.sleep(3)

        elapsed = time.time() - start_time

        print("\n" + "="*70)
        print("[OK] CORPUS BUILD COMPLETE")
        print("="*70)
        print(f"Time elapsed: {elapsed:.1f} seconds")
        print(f"Output location: {self.output_dir}")

        # List generated files
        files = list(self.output_dir.glob("*.txt"))
        print(f"\nGenerated {len(files)} corpus files:")
        for file in sorted(files):
            size_kb = file.stat().st_size / 1024
            print(f"  - {file.name} ({size_kb:.1f} KB)")


def main():
    """Run corpus builder"""
    builder = EligibilityCorpusBuilder()

    # Build corpus with 200 trials per cancer type
    # Adjust this number based on your needs (more = more comprehensive, slower)
    builder.build_complete_corpus(trials_per_cancer=200)

    print("\n[OK] Corpus ready for RAG ingestion!")
    print("\nNext steps:")
    print("1. Review generated files in knowledge_base/trial_patterns/")
    print("2. Run the RAG rebuild to index these documents")
    print("3. Test retrieval with biomarker queries")


if __name__ == "__main__":
    main()
