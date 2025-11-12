"""
Build Enhanced Clinical Trial Corpus for RAG Enhancement v2.0

This version extracts comprehensive trial information including:
- Study design details (enrollment, randomization, masking)
- Primary/secondary outcomes with timeframes
- Geographic locations (sites, cities, states)
- Sponsors and collaborators
- Study arms/cohorts with detailed descriptions
- Timeline information (start/completion dates)
- Detailed descriptions (background, rationale)
"""

import requests
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class EnhancedCorpusBuilder:
    """Builds comprehensive trial corpus from ClinicalTrials.gov API v2"""

    def __init__(self, output_dir: str = "knowledge_base/trial_patterns_v2"):
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
        """Fetch trials from ClinicalTrials.gov API v2.0 - ALL FIELDS"""

        print(f"\n[SEARCH] Fetching trials for: {condition}")

        params = {
            "query.cond": condition,
            "filter.overallStatus": "RECRUITING,NOT_YET_RECRUITING,ACTIVE_NOT_RECRUITING,COMPLETED",
            "pageSize": min(max_studies, 1000),
            "format": "json"
            # NO fields parameter - get EVERYTHING
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

    def parse_study_comprehensive(self, study: Dict) -> Optional[Dict]:
        """Extract COMPREHENSIVE trial information"""

        try:
            protocol = study.get("protocolSection", {})

            # === IDENTIFICATION ===
            identification = protocol.get("identificationModule", {})
            nct_id = identification.get("nctId", "")
            title = identification.get("briefTitle", "")
            official_title = identification.get("officialTitle", "")
            org_study_id = identification.get("orgStudyIdInfo", {}).get("id", "")

            # === STATUS ===
            status_module = protocol.get("statusModule", {})
            status = status_module.get("overallStatus", "")
            start_date = status_module.get("startDateStruct", {})
            completion_date = status_module.get("completionDateStruct", {})
            primary_completion_date = status_module.get("primaryCompletionDateStruct", {})

            # === DESIGN ===
            design_module = protocol.get("designModule", {})
            phases = design_module.get("phases", [])
            phase = phases[0] if phases else "Not specified"

            design_info = design_module.get("designInfo", {})
            study_type = design_module.get("studyType", "")
            allocation = design_info.get("allocation", "")
            intervention_model = design_info.get("interventionModel", "")
            primary_purpose = design_info.get("primaryPurpose", "")
            masking = design_info.get("maskingInfo", {}).get("masking", "")

            enrollment_info = design_module.get("enrollmentInfo", {})
            enrollment_count = enrollment_info.get("count", 0)
            enrollment_type = enrollment_info.get("type", "")

            # === DESCRIPTION ===
            description_module = protocol.get("descriptionModule", {})
            brief_summary = description_module.get("briefSummary", "")
            detailed_description = description_module.get("detailedDescription", "")

            # === CONDITIONS ===
            conditions_module = protocol.get("conditionsModule", {})
            conditions = conditions_module.get("conditions", [])

            # === ARMS & INTERVENTIONS ===
            arms_module = protocol.get("armsInterventionsModule", {})

            # Study arms
            arm_groups = []
            for arm in arms_module.get("armGroups", []):
                arm_groups.append({
                    "label": arm.get("label", ""),
                    "type": arm.get("type", ""),
                    "description": arm.get("description", ""),
                    "interventions": arm.get("interventionNames", [])
                })

            # Interventions
            interventions = []
            for intervention in arms_module.get("interventions", []):
                interventions.append({
                    "type": intervention.get("type", ""),
                    "name": intervention.get("name", ""),
                    "description": intervention.get("description", "")
                })

            # === OUTCOMES ===
            outcomes_module = protocol.get("outcomesModule", {})

            primary_outcomes = []
            for outcome in outcomes_module.get("primaryOutcomes", []):
                primary_outcomes.append({
                    "measure": outcome.get("measure", ""),
                    "description": outcome.get("description", ""),
                    "timeFrame": outcome.get("timeFrame", "")
                })

            secondary_outcomes = []
            for outcome in outcomes_module.get("secondaryOutcomes", []):
                secondary_outcomes.append({
                    "measure": outcome.get("measure", ""),
                    "description": outcome.get("description", ""),
                    "timeFrame": outcome.get("timeFrame", "")
                })

            # === ELIGIBILITY ===
            eligibility_module = protocol.get("eligibilityModule", {})
            eligibility_text = eligibility_module.get("eligibilityCriteria", "")

            # Skip if no eligibility criteria
            if not eligibility_text or len(eligibility_text) < 50:
                return None

            min_age = eligibility_module.get("minimumAge", "")
            max_age = eligibility_module.get("maximumAge", "")
            sex = eligibility_module.get("sex", "")
            healthy_volunteers = eligibility_module.get("healthyVolunteers", False)

            # === LOCATIONS ===
            locations_module = protocol.get("contactsLocationsModule", {})
            locations = []
            for loc in locations_module.get("locations", []):
                locations.append({
                    "facility": loc.get("facility", ""),
                    "city": loc.get("city", ""),
                    "state": loc.get("state", ""),
                    "country": loc.get("country", ""),
                    "zip": loc.get("zip", "")
                })

            # === SPONSORS ===
            sponsors_module = protocol.get("sponsorCollaboratorsModule", {})
            lead_sponsor = sponsors_module.get("leadSponsor", {})
            sponsor_name = lead_sponsor.get("name", "")
            sponsor_class = lead_sponsor.get("class", "")

            collaborators = []
            for collab in sponsors_module.get("collaborators", []):
                collaborators.append({
                    "name": collab.get("name", ""),
                    "class": collab.get("class", "")
                })

            # === BIOMARKER DETECTION ===
            mentioned_biomarkers = []
            search_text = (eligibility_text + " " + brief_summary + " " + detailed_description).lower()
            for biomarker in self.biomarkers:
                if biomarker.lower() in search_text:
                    mentioned_biomarkers.append(biomarker)

            return {
                # Identification
                "nct_id": nct_id,
                "title": title,
                "official_title": official_title,
                "org_study_id": org_study_id,

                # Status & Timeline
                "status": status,
                "phase": phase,
                "start_date": start_date.get("date", ""),
                "start_date_type": start_date.get("type", ""),
                "completion_date": completion_date.get("date", ""),
                "completion_date_type": completion_date.get("type", ""),
                "primary_completion_date": primary_completion_date.get("date", ""),

                # Design
                "study_type": study_type,
                "allocation": allocation,
                "intervention_model": intervention_model,
                "primary_purpose": primary_purpose,
                "masking": masking,
                "enrollment_count": enrollment_count,
                "enrollment_type": enrollment_type,

                # Descriptions
                "brief_summary": brief_summary,
                "detailed_description": detailed_description,

                # Conditions
                "conditions": conditions,

                # Arms & Interventions
                "arm_groups": arm_groups,
                "interventions": interventions,

                # Outcomes
                "primary_outcomes": primary_outcomes,
                "secondary_outcomes": secondary_outcomes,

                # Eligibility
                "eligibility_criteria": eligibility_text,
                "min_age": min_age,
                "max_age": max_age,
                "sex": sex,
                "healthy_volunteers": healthy_volunteers,

                # Locations
                "locations": locations,
                "location_count": len(locations),

                # Sponsors
                "sponsor_name": sponsor_name,
                "sponsor_class": sponsor_class,
                "collaborators": collaborators,

                # Biomarkers
                "biomarkers_mentioned": mentioned_biomarkers
            }

        except Exception as e:
            print(f"    [-] Parse error: {str(e)[:100]}")
            return None

    def build_cancer_type_corpus(self, cancer_type: str, max_trials: int = 200):
        """Build enhanced corpus for a specific cancer type"""

        print(f"\n{'='*70}")
        print(f"Building ENHANCED corpus for: {cancer_type.upper()}")
        print(f"{'='*70}")

        # Fetch trials
        studies = self.fetch_trials_for_condition(cancer_type, max_studies=max_trials)

        if not studies:
            print(f"[!]  No studies found for {cancer_type}")
            return

        # Parse trials
        print(f"\n[LIST] Parsing comprehensive trial data...")
        parsed_trials = []

        for study in studies:
            parsed = self.parse_study_comprehensive(study)
            if parsed:
                parsed_trials.append(parsed)

        print(f"  [+] Parsed {len(parsed_trials)} trials with complete data")

        if len(parsed_trials) == 0:
            return

        # Write enhanced documents
        self._write_enhanced_corpus(cancer_type, parsed_trials)
        self._write_biomarker_document(cancer_type, parsed_trials)

    def _write_enhanced_corpus(self, cancer_type: str, trials: List[Dict]):
        """Write ENHANCED corpus document with all fields"""

        filename = cancer_type.replace(" ", "_").lower() + "_enhanced_corpus.txt"
        filepath = self.output_dir / filename

        print(f"\n[DISK] Writing enhanced corpus: {filename}")

        with open(filepath, 'w', encoding='utf-8') as f:
            # Header
            f.write(f"# Enhanced Clinical Trial Corpus: {cancer_type.title()}\n")
            f.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# Total Trials: {len(trials)}\n")
            f.write(f"# Version: 2.0 (Comprehensive Extraction)\n\n")

            f.write(f"This enhanced corpus contains comprehensive information from {len(trials)} ")
            f.write(f"clinical trials for {cancer_type}, including study design, outcomes, ")
            f.write(f"locations, sponsors, and detailed eligibility criteria.\n\n")

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

                for trial in phase_trials[:50]:  # Top 50 per phase
                    f.write(f"### Trial: {trial['nct_id']}\n\n")

                    # Basic Info
                    f.write(f"**Title:** {trial['title']}\n")
                    if trial['official_title'] and trial['official_title'] != trial['title']:
                        f.write(f"**Official Title:** {trial['official_title'][:200]}...\n")

                    f.write(f"**Status:** {trial['status']}\n")
                    f.write(f"**Phase:** {trial['phase']}\n\n")

                    # Study Design
                    f.write(f"**STUDY DESIGN:**\n")
                    f.write(f"- Type: {trial['study_type']}\n")
                    f.write(f"- Allocation: {trial['allocation']}\n")
                    f.write(f"- Intervention Model: {trial['intervention_model']}\n")
                    f.write(f"- Primary Purpose: {trial['primary_purpose']}\n")
                    f.write(f"- Masking: {trial['masking']}\n")
                    f.write(f"- Enrollment: {trial['enrollment_count']} ({trial['enrollment_type']})\n\n")

                    # Brief Summary
                    if trial['brief_summary']:
                        f.write(f"**BRIEF SUMMARY:**\n")
                        f.write(f"{trial['brief_summary'][:500]}\n\n")

                    # Study Arms
                    if trial['arm_groups']:
                        f.write(f"**STUDY ARMS:** ({len(trial['arm_groups'])} arms)\n")
                        for i, arm in enumerate(trial['arm_groups'][:5], 1):
                            f.write(f"{i}. {arm['label']} ({arm['type']})\n")
                            if arm['description']:
                                f.write(f"   {arm['description'][:200]}\n")
                        f.write("\n")

                    # Interventions
                    if trial['interventions']:
                        f.write(f"**INTERVENTIONS:**\n")
                        for interv in trial['interventions'][:5]:
                            f.write(f"- {interv['type']}: {interv['name']}\n")
                        f.write("\n")

                    # Primary Outcomes
                    if trial['primary_outcomes']:
                        f.write(f"**PRIMARY OUTCOMES:**\n")
                        for outcome in trial['primary_outcomes'][:3]:
                            f.write(f"- Measure: {outcome['measure']}\n")
                            f.write(f"  Timeframe: {outcome['timeFrame']}\n")
                            if outcome['description']:
                                f.write(f"  Description: {outcome['description'][:200]}\n")
                        f.write("\n")

                    # Secondary Outcomes
                    if trial['secondary_outcomes']:
                        f.write(f"**SECONDARY OUTCOMES:** ({len(trial['secondary_outcomes'])} total)\n")
                        for outcome in trial['secondary_outcomes'][:2]:
                            f.write(f"- {outcome['measure']}\n")
                        f.write("\n")

                    # Locations
                    if trial['locations']:
                        f.write(f"**LOCATIONS:** ({trial['location_count']} sites)\n")
                        # Group by state/country
                        us_locations = [loc for loc in trial['locations'] if loc['country'] == 'United States']
                        if us_locations:
                            states = list(set([loc['state'] for loc in us_locations if loc['state']]))
                            f.write(f"- United States: {', '.join(sorted(states)[:10])}\n")

                        other_countries = list(set([loc['country'] for loc in trial['locations'] if loc['country'] != 'United States']))
                        if other_countries:
                            f.write(f"- International: {', '.join(sorted(other_countries)[:5])}\n")
                        f.write("\n")

                    # Sponsor
                    f.write(f"**SPONSOR:** {trial['sponsor_name']} ({trial['sponsor_class']})\n")
                    if trial['collaborators']:
                        collab_names = [c['name'] for c in trial['collaborators'][:3]]
                        f.write(f"**COLLABORATORS:** {', '.join(collab_names)}\n")
                    f.write("\n")

                    # Biomarkers
                    if trial['biomarkers_mentioned']:
                        f.write(f"**BIOMARKERS MENTIONED:** {', '.join(trial['biomarkers_mentioned'])}\n\n")

                    # Eligibility
                    f.write(f"**ELIGIBILITY:**\n")
                    f.write(f"- Age: {trial['min_age']} to {trial['max_age']}\n")
                    f.write(f"- Sex: {trial['sex']}\n")
                    f.write(f"- Healthy Volunteers: {'Yes' if trial['healthy_volunteers'] else 'No'}\n\n")

                    f.write(f"**ELIGIBILITY CRITERIA:**\n")
                    f.write(f"{trial['eligibility_criteria']}\n\n")

                    # Timeline
                    f.write(f"**TIMELINE:**\n")
                    f.write(f"- Start: {trial['start_date']} ({trial['start_date_type']})\n")
                    f.write(f"- Primary Completion: {trial['primary_completion_date']}\n")
                    f.write(f"- Study Completion: {trial['completion_date']} ({trial['completion_date_type']})\n")

                    f.write("\n" + "-" * 70 + "\n\n")

        print(f"  [+] Wrote {filepath}")
        size_mb = filepath.stat().st_size / (1024 * 1024)
        print(f"  [CHART] File size: {size_mb:.2f} MB")

    def _write_biomarker_document(self, cancer_type: str, trials: List[Dict]):
        """Write biomarker-specific trial document"""

        biomarker_trials = [t for t in trials if t['biomarkers_mentioned']]

        if len(biomarker_trials) == 0:
            return

        filename = cancer_type.replace(" ", "_").lower() + "_biomarker_enhanced.txt"
        filepath = self.output_dir / filename

        print(f"[DISK] Writing enhanced biomarker doc: {filename}")

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# Enhanced Biomarker-Specific Trials: {cancer_type.title()}\n")
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

                for trial in marker_trials[:20]:
                    f.write(f"**{trial['nct_id']}** - {trial['title'][:120]}\n")
                    f.write(f"Phase: {trial['phase']} | Status: {trial['status']}\n")
                    f.write(f"Purpose: {trial['primary_purpose']} | Enrollment: {trial['enrollment_count']}\n")

                    if trial['interventions']:
                        interv_names = [i['name'] for i in trial['interventions'][:2]]
                        f.write(f"Interventions: {', '.join(interv_names)}\n")

                    if trial['locations']:
                        f.write(f"Locations: {trial['location_count']} sites\n")

                    # Primary outcome
                    if trial['primary_outcomes']:
                        f.write(f"Primary Outcome: {trial['primary_outcomes'][0]['measure'][:100]}\n")

                    f.write("\n" + "-" * 70 + "\n\n")

        print(f"  [+] Wrote {filepath}")

    def build_complete_corpus(self, trials_per_cancer: int = 200):
        """Build complete ENHANCED corpus across all cancer types"""

        print("\n" + "="*70)
        print("BUILDING ENHANCED CLINICAL TRIAL CORPUS v2.0")
        print("="*70)
        print(f"\nCancer types: {len(self.cancer_types)}")
        print(f"Max trials per type: {trials_per_cancer}")
        print(f"Output directory: {self.output_dir}")
        print("\nEnhancements:")
        print("  [+] Study design (enrollment, randomization, masking)")
        print("  [+] Primary/secondary outcomes")
        print("  [+] Geographic locations")
        print("  [+] Sponsors & collaborators")
        print("  [+] Study arms/cohorts")
        print("  [+] Timeline information")

        start_time = time.time()

        for i, cancer_type in enumerate(self.cancer_types, 1):
            print(f"\n[{i}/{len(self.cancer_types)}] Processing {cancer_type}...")

            self.build_cancer_type_corpus(cancer_type, max_trials=trials_per_cancer)

            # Rate limiting
            if i < len(self.cancer_types):
                print(f"\n[~] Waiting 3 seconds...")
                time.sleep(3)

        elapsed = time.time() - start_time

        print("\n" + "="*70)
        print("[OK] ENHANCED CORPUS BUILD COMPLETE")
        print("="*70)
        print(f"Time elapsed: {elapsed:.1f} seconds")
        print(f"Output location: {self.output_dir}")

        # Stats
        files = list(self.output_dir.glob("*.txt"))
        total_size = sum(f.stat().st_size for f in files) / (1024 * 1024)

        print(f"\nGenerated {len(files)} enhanced corpus files:")
        print(f"Total size: {total_size:.2f} MB")

        for file in sorted(files):
            size_mb = file.stat().st_size / (1024 * 1024)
            print(f"  - {file.name} ({size_mb:.2f} MB)")


def main():
    """Run enhanced corpus builder"""
    builder = EnhancedCorpusBuilder()

    print("\n" + "="*70)
    print("ENHANCED CLINICAL TRIAL CORPUS BUILDER v2.0")
    print("="*70)
    print("\nThis will extract COMPREHENSIVE trial information including:")
    print("  • Study design details (enrollment, randomization, masking)")
    print("  • Primary/secondary outcomes with timeframes")
    print("  • Geographic locations (cities, states, countries)")
    print("  • Sponsors and collaborators")
    print("  • Study arms/cohorts with descriptions")
    print("  • Timeline information (start, completion dates)")
    print("  • Detailed descriptions and summaries")
    print("\nExpected output: ~15-25 MB (vs 5 MB in v1)")
    print("="*70)

    # Build corpus with 200 trials per cancer type
    builder.build_complete_corpus(trials_per_cancer=200)

    print("\n[OK] Enhanced corpus ready for RAG ingestion!")
    print("\nNext steps:")
    print("1. Review generated files in knowledge_base/trial_patterns_v2/")
    print("2. Update clinical_rag.py to point to trial_patterns_v2/")
    print("3. Rebuild vectorstore with force_rebuild=True")
    print("4. Test improved retrieval quality")


if __name__ == "__main__":
    main()
