"""
Test what RAG retrieves after removing trial corpus
"""
import sys
sys.path.insert(0, '.')

from tools.clinical_rag import ClinicalRAG

print("\n" + "="*70)
print("RAG RETRIEVAL QUALITY TEST")
print("="*70)

rag = ClinicalRAG()
rag.build_vectorstore()  # Load the vectorstore

# Test query: cervical cancer PD-L1 positive
query = "cervical cancer PD-L1 positive treatment guidelines"
print(f"\nQuery: {query}")
print("\nTop 5 retrieved chunks:\n")

results = rag.retrieve(query, k=5)

for i, r in enumerate(results, 1):
    category = r.get('category', 'unknown')
    source = r.get('source', 'unknown')
    content = r.get('content', '')[:300].replace('\n', ' ')

    print(f"{i}. [{category}] {source}")
    print(f"   Content: {content}...")
    print()

print("="*70)
print("ANALYSIS")
print("="*70)

# Count categories
from collections import Counter
categories = Counter([r.get('category', 'unknown') for r in results])

print("\nCategory distribution:")
for cat, count in categories.items():
    print(f"  {cat}: {count}/5")

if 'trial_pattern' in categories:
    print("\n[WARNING] Trial patterns still appearing - corpus may not be fully removed")
elif 'treatment_guideline' in categories or 'drug_label' in categories:
    print("\n[SUCCESS] High-quality sources (guidelines/labels) are being retrieved")
else:
    print("\n[INFO] Categories:", list(categories.keys()))
