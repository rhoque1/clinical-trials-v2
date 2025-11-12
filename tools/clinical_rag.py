"""
Clinical RAG System for Knowledge-Enhanced Trial Matching
Ingests NCCN guidelines and FDA drug labels for retrieval
"""
import os
from pathlib import Path
from typing import List, Dict, Optional
import json

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document


class ClinicalRAG:
    """
    Retrieval-Augmented Generation system for clinical guidelines
    Uses FAISS for vector similarity search
    """
    
    def __init__(self, knowledge_base_dir: str = "knowledge_base", vectorstore_path: str = "vectorstore"):
        # Load environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        # Verify API key is loaded
        # Verify API key is loaded (using your variable name)
        api_key = os.getenv("open_ai")
        if not api_key:
            raise ValueError("open_ai not found in .env file")
        
        # Set it as OPENAI_API_KEY for langchain
        os.environ["OPENAI_API_KEY"] = api_key
        
        self.knowledge_base_dir = Path(knowledge_base_dir)
        self.vectorstore_path = Path(vectorstore_path)
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.vectorstore = None
        
        # Ensure vectorstore directory exists
        self.vectorstore_path.mkdir(exist_ok=True)
        
    def load_and_chunk_documents(self) -> List[Document]:
        """
        Load all PDFs and TXT files from knowledge base and chunk them
        Returns list of Document objects with metadata
        """
        print("\n" + "="*70)
        print("📚 LOADING AND CHUNKING CLINICAL DOCUMENTS")
        print("="*70)

        all_documents = []

        # Define document categories
        categories = {
            "treatment_guideline": self.knowledge_base_dir / "guidelines",
            "drug_label": self.knowledge_base_dir / "drug_labels",
            "biomarker_guide": self.knowledge_base_dir / "biomarker_guides",
            "trial_pattern": self.knowledge_base_dir / "trial_patterns_v2"  # ENHANCED v2.0
        }

        for category, directory in categories.items():
            if not directory.exists():
                print(f"[!]  Directory not found: {directory}")
                continue

            # Load PDF files
            pdf_files = list(directory.glob("*.pdf"))
            # Load TXT files (NEW)
            txt_files = list(directory.glob("*.txt"))

            total_files = len(pdf_files) + len(txt_files)
            print(f"\n📂 Processing {category.replace('_', ' ').title()}: {total_files} files ({len(pdf_files)} PDFs, {len(txt_files)} TXT)")

            # Process PDF files
            for pdf_path in pdf_files:
                try:
                    print(f"  Loading: {pdf_path.name}...", end=" ")

                    # Load PDF
                    loader = PyPDFLoader(str(pdf_path))
                    pages = loader.load()

                    # Add metadata
                    for page in pages:
                        page.metadata.update({
                            "source": pdf_path.name,
                            "category": category,
                            "file_path": str(pdf_path)
                        })

                    all_documents.extend(pages)
                    print(f"[+] {len(pages)} pages")

                except Exception as e:
                    print(f"[-] Error: {str(e)[:50]}")

            # Process TXT files (NEW)
            for txt_path in txt_files:
                try:
                    print(f"  Loading: {txt_path.name}...", end=" ")

                    # Read text file
                    with open(txt_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Create Document object
                    doc = Document(
                        page_content=content,
                        metadata={
                            "source": txt_path.name,
                            "category": category,
                            "file_path": str(txt_path)
                        }
                    )

                    all_documents.append(doc)
                    print(f"[+] {len(content)} chars")

                except Exception as e:
                    print(f"[-] Error: {str(e)[:50]}")

        print(f"\n[OK] Total documents loaded: {len(all_documents)}")

        # Chunk documents
        print("\n🔪 Chunking documents...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,  # Characters per chunk
            chunk_overlap=200,  # Overlap to preserve context
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        chunks = text_splitter.split_documents(all_documents)
        print(f"[OK] Created {len(chunks)} chunks")

        return chunks
    
    def build_vectorstore(self, force_rebuild: bool = False) -> FAISS:
        """
        Build FAISS vectorstore from documents
        Saves to disk for reuse
        """
        vectorstore_file = self.vectorstore_path / "clinical_guidelines.faiss"
        
        # Check if vectorstore already exists
        if vectorstore_file.exists() and not force_rebuild:
            print("\n[BOX] Loading existing vectorstore...")
            self.vectorstore = FAISS.load_local(
                str(self.vectorstore_path),
                self.embeddings,
                index_name="clinical_guidelines",
                allow_dangerous_deserialization=True
            )
            print("[OK] Vectorstore loaded")
            return self.vectorstore
        
        # Build new vectorstore
        print("\n🔨 Building vectorstore (this may take 2-3 minutes)...")
        
        # Load and chunk documents
        chunks = self.load_and_chunk_documents()
        
        # Create embeddings and vectorstore
        print("\n🧬 Creating embeddings...")
        print("   (Using OpenAI text-embedding-3-small)")
        
        self.vectorstore = FAISS.from_documents(chunks, self.embeddings)
        
        # Save to disk
        print("\n[DISK] Saving vectorstore to disk...")
        self.vectorstore.save_local(
            str(self.vectorstore_path),
            index_name="clinical_guidelines"
        )
        print(f"[OK] Vectorstore saved to: {self.vectorstore_path}")
        
        return self.vectorstore
    
    def retrieve(self, query: str, k: int = 5) -> List[Dict]:
        """
        Retrieve top-k relevant chunks for a query
        
        Args:
            query: Search query (e.g., "EGFR exon 19 deletion treatment")
            k: Number of results to return
            
        Returns:
            List of dicts with 'content' and 'metadata'
        """
        if self.vectorstore is None:
            raise ValueError("Vectorstore not built. Call build_vectorstore() first.")
        
        # Retrieve similar documents
        results = self.vectorstore.similarity_search(query, k=k)
        
        # Format results
        formatted_results = []
        for doc in results:
            formatted_results.append({
                "content": doc.page_content,
                "source": doc.metadata.get("source", "Unknown"),
                "category": doc.metadata.get("category", "Unknown"),
                "page": doc.metadata.get("page", "Unknown")
            })
        
        return formatted_results
    
    def retrieve_with_scores(self, query: str, k: int = 5) -> List[Dict]:
        """
        Retrieve with similarity scores
        Higher score = more relevant
        """
        if self.vectorstore is None:
            raise ValueError("Vectorstore not built. Call build_vectorstore() first.")
        
        results = self.vectorstore.similarity_search_with_score(query, k=k)
        
        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "content": doc.page_content,
                "source": doc.metadata.get("source", "Unknown"),
                "category": doc.metadata.get("category", "Unknown"),
                "page": doc.metadata.get("page", "Unknown"),
                "similarity_score": float(score)
            })
        
        return formatted_results


def test_rag_system():
    """Test the RAG system with sample queries"""
    print("\n" + "="*70)
    print("🧪 TESTING CLINICAL RAG SYSTEM")
    print("="*70)
    
    # Initialize RAG
    rag = ClinicalRAG()
    
    # Build vectorstore
    rag.build_vectorstore(force_rebuild=False)
    
    # Test queries
    test_queries = [
        "EGFR exon 19 deletion treatment options",
        "PD-L1 expression and immunotherapy eligibility",
        "KRAS G12C mutation targeted therapy"
    ]
    
    print("\n" + "="*70)
    print("[SEARCH] TESTING RETRIEVAL")
    print("="*70)
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        print("-" * 70)
        
        results = rag.retrieve(query, k=3)
        
        for i, result in enumerate(results, 1):
            print(f"\n  Result {i}:")
            print(f"    Source: {result['source']}")
            print(f"    Category: {result['category']}")
            print(f"    Content preview: {result['content'][:150]}...")
    
    print("\n" + "="*70)
    print("[OK] RAG SYSTEM TEST COMPLETE")
    print("="*70)


if __name__ == "__main__":
    test_rag_system()