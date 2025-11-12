"""
Flexible RAG System - Supports Multiple Configurations for A/B Testing

This version allows swapping knowledge sources and retrieval parameters
without rebuilding the entire vectorstore.
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


class FlexibleRAG:
    """
    RAG system that accepts configuration for knowledge sources
    """

    def __init__(self, config=None, knowledge_base_dir: str = "knowledge_base"):
        from dotenv import load_dotenv
        load_dotenv()

        # Load API key
        api_key = os.getenv("open_ai")
        if not api_key:
            raise ValueError("open_ai not found in .env file")
        os.environ["OPENAI_API_KEY"] = api_key

        self.knowledge_base_dir = Path(knowledge_base_dir)
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        self.vectorstore = None

        # Default config if none provided
        if config is None:
            from evaluation.rag_configurations import CONFIG_GUIDELINES_FDA
            config = CONFIG_GUIDELINES_FDA

        self.config = config

    def load_documents_by_config(self) -> List[Document]:
        """
        Load documents based on configuration settings
        """
        print("\n" + "="*70)
        print(f"📚 LOADING DOCUMENTS FOR: {self.config.name}")
        print("="*70)

        all_documents = []

        # Define all possible sources
        source_dirs = {
            "guidelines": ("treatment_guideline", self.knowledge_base_dir / "guidelines"),
            "drug_labels": ("drug_label", self.knowledge_base_dir / "drug_labels"),
            "biomarker_guides": ("biomarker_guide", self.knowledge_base_dir / "biomarker_guides"),
            "trial_corpus": ("trial_pattern", self.knowledge_base_dir / "trial_patterns_v2"),
            "published_results": ("published_result", self.knowledge_base_dir / "published_results"),
            "actionability_db": ("actionability", self.knowledge_base_dir / "actionability")
        }

        # Load only enabled sources
        for source_key, (category, directory) in source_dirs.items():
            config_attr = f"include_{source_key}"

            if not hasattr(self.config, config_attr):
                continue

            if not getattr(self.config, config_attr):
                print(f"⊘ Skipping: {category}")
                continue

            if not directory.exists():
                print(f"[!]  Directory not found: {directory}")
                continue

            # Load files from this source
            pdf_files = list(directory.glob("*.pdf"))
            txt_files = list(directory.glob("*.txt"))
            md_files = list(directory.glob("*.md"))

            total_files = len(pdf_files) + len(txt_files) + len(md_files)
            print(f"\n[+] Loading {category}: {total_files} files")

            # Process PDFs
            for pdf_path in pdf_files:
                try:
                    loader = PyPDFLoader(str(pdf_path))
                    pages = loader.load()

                    for page in pages:
                        page.metadata.update({
                            "source": pdf_path.name,
                            "category": category,
                            "file_path": str(pdf_path)
                        })

                    all_documents.extend(pages)
                    print(f"  [+] {pdf_path.name}: {len(pages)} pages")

                except Exception as e:
                    print(f"  [-] {pdf_path.name}: {str(e)[:50]}")

            # Process TXT files
            for txt_path in txt_files:
                try:
                    with open(txt_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    doc = Document(
                        page_content=content,
                        metadata={
                            "source": txt_path.name,
                            "category": category,
                            "file_path": str(txt_path)
                        }
                    )

                    all_documents.append(doc)
                    print(f"  [+] {txt_path.name}: {len(content)} chars")

                except Exception as e:
                    print(f"  [-] {txt_path.name}: {str(e)[:50]}")

            # Process MD files
            for md_path in md_files:
                try:
                    with open(md_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    doc = Document(
                        page_content=content,
                        metadata={
                            "source": md_path.name,
                            "category": category,
                            "file_path": str(md_path)
                        }
                    )

                    all_documents.append(doc)
                    print(f"  [+] {md_path.name}: {len(content)} chars")

                except Exception as e:
                    print(f"  [-] {md_path.name}: {str(e)[:50]}")

        print(f"\n[OK] Total documents loaded: {len(all_documents)}")
        return all_documents

    def build_vectorstore(self, force_rebuild: bool = True) -> FAISS:
        """
        Build vectorstore from configured sources

        Note: force_rebuild defaults to True for experiments
        to ensure clean comparisons between configs
        """
        print(f"\n🔨 Building vectorstore for: {self.config.config_id}")

        # Load documents according to config
        documents = self.load_documents_by_config()

        if not documents:
            raise ValueError("No documents loaded! Check configuration.")

        # Chunk documents with config parameters
        print(f"\n🔪 Chunking documents (size={self.config.chunk_size}, overlap={self.config.chunk_overlap})...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunk_size,
            chunk_overlap=self.config.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        chunks = text_splitter.split_documents(documents)
        print(f"[OK] Created {len(chunks)} chunks")

        # Create embeddings
        print(f"\n🧬 Creating embeddings...")
        self.vectorstore = FAISS.from_documents(chunks, self.embeddings)
        print(f"[OK] Vectorstore built")

        return self.vectorstore

    def retrieve(self, query: str, k: int = None) -> List[Dict]:
        """
        Retrieve top-k relevant chunks

        Args:
            query: Search query
            k: Number of results (uses config default if None)
        """
        if self.vectorstore is None:
            raise ValueError("Vectorstore not built. Call build_vectorstore() first.")

        k = k or self.config.k_retrieval

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

    def retrieve_with_scores(self, query: str, k: int = None) -> List[Dict]:
        """Retrieve with similarity scores"""
        if self.vectorstore is None:
            raise ValueError("Vectorstore not built. Call build_vectorstore() first.")

        k = k or self.config.k_retrieval

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

    def construct_query(self, patient_profile: Dict) -> str:
        """
        Construct retrieval query based on config template
        """
        # Extract fields
        diagnoses = patient_profile.get("diagnoses", "")
        biomarkers = patient_profile.get("biomarkers", "")

        # Try to extract additional fields if template needs them
        template = self.config.query_template

        query_vars = {
            "diagnoses": str(diagnoses)[:200],
            "biomarkers": str(biomarkers)[:200],
            "cancer_type": self._extract_cancer_type(diagnoses),
            "primary_biomarker": self._extract_primary_biomarker(biomarkers),
            "stage": self._extract_stage(diagnoses),
            "histology": self._extract_histology(diagnoses),
            "treatment_line": "first_line"  # TODO: Extract from treatment history
        }

        # Format query
        try:
            query = template.format(**query_vars)
        except KeyError as e:
            # Fallback to simple query if template has missing vars
            print(f"[!] Query template error: {e}. Using simple query.")
            query = f"{diagnoses} {biomarkers} treatment guidelines"

        return query

    def _extract_cancer_type(self, diagnoses: str) -> str:
        """Extract main cancer type"""
        diagnoses_lower = str(diagnoses).lower()
        cancer_types = ["cervical", "lung", "breast", "colorectal", "melanoma", "ovarian", "prostate"]

        for cancer in cancer_types:
            if cancer in diagnoses_lower:
                return f"{cancer} cancer"

        return "cancer"

    def _extract_primary_biomarker(self, biomarkers: str) -> str:
        """Extract most important biomarker"""
        biomarkers_str = str(biomarkers)

        # Priority markers
        priority = ["EGFR", "ALK", "PD-L1", "BRAF", "HER2", "KRAS", "MSI-H"]

        for marker in priority:
            if marker in biomarkers_str:
                return marker

        # Return first mentioned biomarker
        words = biomarkers_str.split()
        if words:
            return words[0]

        return "biomarker"

    def _extract_stage(self, diagnoses: str) -> str:
        """Extract cancer stage"""
        import re
        diagnoses_str = str(diagnoses)

        # Look for stage patterns
        stage_match = re.search(r'\b(stage\s+)?([IV]+|[1-4])[ABC]?\b', diagnoses_str, re.IGNORECASE)
        if stage_match:
            return stage_match.group(0)

        if "metastatic" in diagnoses_str.lower():
            return "metastatic"

        return "advanced"

    def _extract_histology(self, diagnoses: str) -> str:
        """Extract histology"""
        diagnoses_lower = str(diagnoses).lower()

        histologies = ["adenocarcinoma", "squamous cell", "small cell", "non-small cell"]

        for hist in histologies:
            if hist in diagnoses_lower:
                return hist

        return "carcinoma"
