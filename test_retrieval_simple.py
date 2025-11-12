"""
Test RAG retrieval quality after removing trial corpus
"""
import sys
import os
sys.path.insert(0, '.')

# Suppress console output to avoid encoding errors
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Set up API key (using the variable name from .env)
api_key = os.getenv("open_ai")
if not api_key:
    print("Error: open_ai not found in .env file")
    sys.exit(1)
os.environ["OPENAI_API_KEY"] = api_key

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from pathlib import Path

print("="*70)
print("RAG RETRIEVAL QUALITY TEST")
print("="*70)

# Load vectorstore directly
vectorstore_path = Path("vectorstore")
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

try:
    vectorstore = FAISS.load_local(
        str(vectorstore_path),
        embeddings,
        index_name="clinical_guidelines",
        allow_dangerous_deserialization=True
    )
    print("\nVectorstore loaded successfully")
except Exception as e:
    print(f"\nError loading vectorstore: {e}")
    sys.exit(1)

# Test query
query = "cervical cancer PD-L1 positive treatment guidelines"
print(f"\nQuery: {query}")
print("\nTop 5 retrieved chunks:\n")

# Retrieve
docs = vectorstore.similarity_search(query, k=5)

for i, doc in enumerate(docs, 1):
    category = doc.metadata.get('category', 'unknown')
    source = doc.metadata.get('source', 'unknown')
    content = doc.page_content[:300].replace('\n', ' ')

    print(f"{i}. [{category}] {source}")
    print(f"   {content}...")
    print()

print("="*70)
print("ANALYSIS")
print("="*70)

# Count categories
from collections import Counter
categories = Counter([doc.metadata.get('category', 'unknown') for doc in docs])

print("\nCategory distribution:")
for cat, count in categories.items():
    print(f"  {cat}: {count}/5")

if 'trial_pattern' in categories:
    print("\n[WARNING] Trial patterns still appearing")
elif 'treatment_guideline' in categories or 'drug_label' in categories:
    print("\n[SUCCESS] High-quality sources being retrieved")
else:
    print(f"\n[INFO] Categories: {list(categories.keys())}")
