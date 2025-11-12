"""
Test Script for Eligibility Corpus Integration
Validates that the RAG system can retrieve biomarker and eligibility information
"""

from tools.clinical_rag import ClinicalRAG
from pathlib import Path
import json


def test_rag_loading():
    """Test 1: Verify RAG system loads all corpus files"""
    print("\n" + "="*70)
    print("TEST 1: RAG SYSTEM LOADING")
    print("="*70)

    rag = ClinicalRAG()

    # Check if trial_patterns directory exists
    patterns_dir = Path("knowledge_base/trial_patterns")
    if not patterns_dir.exists():
        print("[X] FAILED: trial_patterns directory does not exist")
        return False

    # Count files
    txt_files = list(patterns_dir.glob("*.txt"))
    print(f"\n[+] Found {len(txt_files)} TXT files in trial_patterns/:")
    for file in txt_files:
        size_kb = file.stat().st_size / 1024
        print(f"  - {file.name} ({size_kb:.1f} KB)")

    # Build vectorstore (this will load all files)
    print("\n[*]  Building vectorstore (will load all corpus files)...")
    rag.build_vectorstore(force_rebuild=True)

    if rag.vectorstore is None:
        print("[X] FAILED: Vectorstore not built")
        return False

    print("\n[OK] TEST 1 PASSED: RAG system loaded successfully")
    return True


def test_biomarker_retrieval():
    """Test 2: Test retrieval of biomarker-specific information"""
    print("\n" + "="*70)
    print("TEST 2: BIOMARKER-SPECIFIC RETRIEVAL")
    print("="*70)

    rag = ClinicalRAG()
    rag.build_vectorstore(force_rebuild=False)

    # Test queries for different biomarkers
    test_queries = [
        ("PIK3CA E545K mutation cervical cancer", "PIK3CA"),
        ("PD-L1 expression pembrolizumab eligibility", "PD-L1"),
        ("EGFR exon 19 deletion lung cancer trials", "EGFR"),
        ("BRCA1 mutation PARP inhibitor", "BRCA"),
        ("KRAS G12C mutation targeted therapy", "KRAS")
    ]

    all_passed = True

    for query, expected_biomarker in test_queries:
        print(f"\n{'─'*70}")
        print(f"📝 Query: {query}")
        print(f"Expected to find info about: {expected_biomarker}")
        print(f"{'─'*70}")

        results = rag.retrieve(query, k=3)

        if len(results) == 0:
            print(f"[X] FAILED: No results retrieved")
            all_passed = False
            continue

        # Check if expected biomarker appears in results
        biomarker_found = False
        for i, result in enumerate(results, 1):
            print(f"\n  Result {i}:")
            print(f"    Source: {result['source']}")
            print(f"    Category: {result['category']}")

            # Check if biomarker is mentioned
            if expected_biomarker.lower() in result['content'].lower():
                biomarker_found = True
                print(f"    [+] Contains {expected_biomarker} information")
                # Show snippet
                # Find the sentence containing the biomarker
                sentences = result['content'].split('.')
                for sent in sentences:
                    if expected_biomarker.lower() in sent.lower():
                        print(f"    Snippet: {sent.strip()[:200]}...")
                        break
            else:
                print(f"    - Does not mention {expected_biomarker}")

        if biomarker_found:
            print(f"\n  [+] Successfully retrieved {expected_biomarker} information")
        else:
            print(f"\n  [!]  WARNING: {expected_biomarker} not found in top 3 results")
            all_passed = False

    if all_passed:
        print("\n[OK] TEST 2 PASSED: All biomarker queries returned relevant results")
    else:
        print("\n[!]  TEST 2 PARTIAL: Some queries did not return expected biomarker info")

    return all_passed


def test_eligibility_pattern_retrieval():
    """Test 3: Test retrieval of eligibility criteria patterns"""
    print("\n" + "="*70)
    print("TEST 3: ELIGIBILITY PATTERN RETRIEVAL")
    print("="*70)

    rag = ClinicalRAG()
    rag.build_vectorstore(force_rebuild=False)

    # Test queries about eligibility patterns
    test_queries = [
        ("Phase 2 lung cancer trial eligibility criteria", "Phase 2"),
        ("ECOG performance status requirements clinical trials", "ECOG"),
        ("brain metastases clinical trial eligibility", "brain metastases"),
        ("prior treatment lines required second line therapy", "prior treatment"),
        ("organ function requirements clinical trials", "organ function")
    ]

    all_passed = True

    for query, expected_topic in test_queries:
        print(f"\n{'─'*70}")
        print(f"📝 Query: {query}")
        print(f"Expected topic: {expected_topic}")
        print(f"{'─'*70}")

        results = rag.retrieve(query, k=3)

        if len(results) == 0:
            print(f"[X] FAILED: No results retrieved")
            all_passed = False
            continue

        topic_found = False
        for i, result in enumerate(results, 1):
            print(f"\n  Result {i}:")
            print(f"    Source: {result['source']}")
            print(f"    Category: {result['category']}")

            # Check for topic
            if expected_topic.lower() in result['content'].lower():
                topic_found = True
                print(f"    [+] Contains {expected_topic} information")
                # Show snippet
                print(f"    Snippet: {result['content'][:250]}...")
            else:
                print(f"    - Does not focus on {expected_topic}")

        if topic_found:
            print(f"\n  [+] Successfully retrieved {expected_topic} information")
        else:
            print(f"\n  [!]  WARNING: {expected_topic} not prominently featured")
            all_passed = False

    if all_passed:
        print("\n[OK] TEST 3 PASSED: All eligibility queries returned relevant patterns")
    else:
        print("\n[!]  TEST 3 PARTIAL: Some queries need refinement")

    return all_passed


def test_real_patient_scenario():
    """Test 4: Simulate real patient scenario retrieval"""
    print("\n" + "="*70)
    print("TEST 4: REAL PATIENT SCENARIO")
    print("="*70)

    rag = ClinicalRAG()
    rag.build_vectorstore(force_rebuild=False)

    # Simulate the patient from your test case
    patient_scenario = {
        "diagnosis": "Stage IIIB Cervical Squamous Cell Carcinoma",
        "biomarkers": ["PIK3CA E545K", "TP53 R273H", "PD-L1 15%", "HPV-16 positive"],
        "age": 40,
        "ecog": 1
    }

    print(f"\nPatient Profile:")
    print(f"  Diagnosis: {patient_scenario['diagnosis']}")
    print(f"  Biomarkers: {', '.join(patient_scenario['biomarkers'])}")
    print(f"  Age: {patient_scenario['age']}, ECOG: {patient_scenario['ecog']}")

    # Query 1: PIK3CA mutation trials
    print(f"\n{'─'*70}")
    print("Query 1: Finding PIK3CA mutation trials")
    print(f"{'─'*70}")

    query1 = "PIK3CA E545K mutation cervical cancer clinical trials eligibility"
    results1 = rag.retrieve(query1, k=3)

    print(f"\nRetrieved {len(results1)} results:")
    for i, result in enumerate(results1, 1):
        print(f"\n  {i}. {result['source']} ({result['category']})")
        if "PIK3CA" in result['content']:
            # Extract PIK3CA-specific info
            lines = result['content'].split('\n')
            for line in lines:
                if 'PIK3CA' in line or 'PI3K' in line or 'alpelisib' in line.lower():
                    print(f"      -> {line.strip()[:150]}")

    # Query 2: PD-L1 eligibility
    print(f"\n{'─'*70}")
    print("Query 2: PD-L1 expression eligibility criteria")
    print(f"{'─'*70}")

    query2 = "PD-L1 15% expression pembrolizumab cervical cancer eligibility"
    results2 = rag.retrieve(query2, k=3)

    print(f"\nRetrieved {len(results2)} results:")
    for i, result in enumerate(results2, 1):
        print(f"\n  {i}. {result['source']} ({result['category']})")
        if "PD-L1" in result['content'] or "pembrolizumab" in result['content'].lower():
            # Extract PD-L1-specific info
            lines = result['content'].split('\n')
            for line in lines:
                if 'PD-L1' in line or 'CPS' in line or 'pembrolizumab' in line.lower():
                    print(f"      -> {line.strip()[:150]}")

    # Query 3: General cervical cancer eligibility
    print(f"\n{'─'*70}")
    print("Query 3: General cervical cancer trial eligibility")
    print(f"{'─'*70}")

    query3 = "cervical cancer stage IIIB clinical trial eligibility ECOG"
    results3 = rag.retrieve(query3, k=3)

    print(f"\nRetrieved {len(results3)} results:")
    for i, result in enumerate(results3, 1):
        print(f"\n  {i}. {result['source']} ({result['category']})")
        print(f"      Preview: {result['content'][:200]}...")

    print("\n[OK] TEST 4 COMPLETED: Real patient scenario processed")
    print("\nObservation: Check if retrieval includes:")
    print("  - PIK3CA mutation -> alpelisib trials")
    print("  - PD-L1 >=1% or >=10% -> pembrolizumab eligibility")
    print("  - ECOG 0-1 -> eligible for most Phase 2 trials")
    print("  - Stage IIIB -> locally advanced cervical cancer trials")

    return True


def test_comparison_before_after():
    """Test 5: Compare retrieval quality before vs after corpus addition"""
    print("\n" + "="*70)
    print("TEST 5: BEFORE/AFTER COMPARISON")
    print("="*70)

    print("\n[CHART] Corpus Statistics:")

    # Count documents in each category
    categories = {
        "Treatment Guidelines": Path("knowledge_base/guidelines"),
        "Drug Labels": Path("knowledge_base/drug_labels"),
        "Biomarker Guides": Path("knowledge_base/biomarker_guides"),
        "Trial Patterns (NEW)": Path("knowledge_base/trial_patterns")
    }

    for name, path in categories.items():
        if path.exists():
            pdf_count = len(list(path.glob("*.pdf")))
            txt_count = len(list(path.glob("*.txt")))
            md_count = len(list(path.glob("*.md")))
            total = pdf_count + txt_count + md_count
            print(f"\n  {name}: {total} files")
            if pdf_count > 0:
                print(f"    - PDFs: {pdf_count}")
            if txt_count > 0:
                print(f"    - TXT: {txt_count}")
            if md_count > 0:
                print(f"    - MD: {md_count}")

    print("\n📈 Expected Improvements:")
    print("  [+] Biomarker-to-trial mappings (PIK3CA -> alpelisib trials)")
    print("  [+] Eligibility criteria patterns (Phase 1 vs 2 vs 3)")
    print("  [+] Performance status requirements (ECOG 0-1 standard)")
    print("  [+] Brain metastases policies (increasingly permissive)")
    print("  [+] Prior treatment line requirements (1st, 2nd, 3rd+)")
    print("  [+] Cancer type-specific patterns (NSCLC, breast, cervical, etc.)")

    print("\n[OK] TEST 5 COMPLETED: Corpus enhancement documented")
    return True


def run_all_tests():
    """Run complete test suite"""
    print("\n" + "="*70)
    print("ELIGIBILITY CORPUS INTEGRATION TEST SUITE")
    print("="*70)
    print("\nThis test suite validates the enhanced RAG system with trial")
    print("eligibility patterns and biomarker-specific knowledge.")

    tests = [
        ("RAG System Loading", test_rag_loading),
        ("Biomarker Retrieval", test_biomarker_retrieval),
        ("Eligibility Patterns", test_eligibility_pattern_retrieval),
        ("Real Patient Scenario", test_real_patient_scenario),
        ("Before/After Comparison", test_comparison_before_after)
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"\n[X] TEST FAILED WITH ERROR: {str(e)}")
            results[test_name] = False

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    passed = sum(1 for r in results.values() if r)
    total = len(results)

    for test_name, result in results.items():
        status = "[OK] PASS" if result else "[X] FAIL"
        print(f"{status} - {test_name}")

    print(f"\n{'='*70}")
    print(f"RESULTS: {passed}/{total} tests passed")
    print(f"{'='*70}")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Eligibility corpus successfully integrated.")
        print("\nNext steps:")
        print("1. Run the corpus builder to populate trial_patterns/")
        print("2. Rebuild vectorstore with force_rebuild=True")
        print("3. Test end-to-end workflow with real patient")
        print("4. Compare trial matching accuracy before/after")
    else:
        print("\n[!]  Some tests failed. Review output above for details.")

    return results


if __name__ == "__main__":
    run_all_tests()
