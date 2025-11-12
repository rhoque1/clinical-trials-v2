"""
Rebuild vectorstore silently (suppress console output to avoid encoding issues)
"""

import sys
import io
import os

# Redirect stdout/stderr to suppress emoji encoding errors
old_stdout = sys.stdout
old_stderr = sys.stderr

# Set environment for UTF-8
os.environ['PYTHONIOENCODING'] = 'utf-8'

try:
    # Suppress output
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()

    from tools.clinical_rag import ClinicalRAG

    # Restore for our messages
    sys.stdout = old_stdout
    sys.stderr = old_stderr

    print("\n[REBUILDING VECTORSTORE]")
    print("Sources: Guidelines + FDA + Biomarker guides (NO trial corpus)")
    print("This will take 2-3 minutes...")
    print("")

    # Suppress again for build
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()

    rag = ClinicalRAG()
    rag.build_vectorstore(force_rebuild=True)

    # Restore
    sys.stdout = old_stdout
    sys.stderr = old_stderr

    print("\n[SUCCESS] Vectorstore rebuilt without trial corpus")
    print("Old size: ~112MB (with 8.8MB trial corpus)")
    print("New size: Check vectorstore/ directory")
    print("")

except Exception as e:
    sys.stdout = old_stdout
    sys.stderr = old_stderr
    print(f"\n[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()
