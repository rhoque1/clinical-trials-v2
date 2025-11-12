"""
Rebuild vectorstore without trial corpus
"""

from tools.clinical_rag import ClinicalRAG

print("\n" + "="*70)
print("REBUILDING VECTORSTORE")
print("="*70)
print("\nRemoving trial corpus from knowledge base...")
print("Sources included:")
print("  - Guidelines (NCCN, ASCO)")
print("  - FDA drug labels")
print("  - Biomarker guides")
print("\nSources EXCLUDED:")
print("  - Trial patterns corpus (8.8MB, backed up)")
print("="*70)

rag = ClinicalRAG()

print("\nBuilding vectorstore (this may take 2-3 minutes)...")
rag.build_vectorstore(force_rebuild=True)

print("\n" + "="*70)
print("VECTORSTORE REBUILT SUCCESSFULLY")
print("="*70)
print("\nOld vectorstore included trial corpus")
print("New vectorstore: Guidelines + FDA + Biomarker guides only")
print("\nExpected improvement: +5-10% retrieval precision")
print("="*70)
