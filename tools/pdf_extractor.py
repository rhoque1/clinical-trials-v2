"""
PDF Extraction Tool
Extracts medical report content for analysis
"""
from pathlib import Path
from typing import Dict, Any
import fitz  # PyMuPDF


def extract_medical_report(pdf_path: str, max_chars: int = 100000) -> Dict[str, Any]:
    """
    Extract medical report content from PDF with focus on clinical information.
    
    Args:
        pdf_path: Path to PDF file
        max_chars: Maximum characters to extract
        
    Returns:
        Dictionary with success status, metadata, and content
    """
    try:
        p = Path(pdf_path)
        if not p.exists():
            return {
                "success": False,
                "error": f"File not found: {pdf_path}",
                "content": ""
            }

        doc = fitz.open(str(p))
        text_all = ""
        
        for page in doc:
            text_all += page.get_text() + "\n"
        
        doc.close()
        
        if not text_all.strip():
            return {
                "success": False,
                "error": "No readable text found in PDF. May be scanned document.",
                "content": ""
            }

        content = text_all[:max_chars] if len(text_all) > max_chars else text_all
        
        return {
            "success": True,
            "filename": p.name,
            "total_chars": len(text_all),
            "included_chars": len(content),
            "truncated": len(text_all) > max_chars,
            "content": content
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error reading PDF: {str(e)}",
            "content": ""
        }


def validate_pdf_readable(pdf_path: str) -> bool:
    """
    Quick validation that PDF can be read
    
    Args:
        pdf_path: Path to PDF file
        
    Returns:
        True if readable, False otherwise
    """
    result = extract_medical_report(pdf_path, max_chars=1000)
    return result["success"] and len(result["content"]) > 0