"""
LibraAI - Corpus Catalog & Document Metadata Registry
Reference: PRD §6.1, §6.3, Appendix B
"""

from typing import Dict, Any, Optional

CORPUS_CATALOG: Dict[str, Dict[str, Any]] = {
    "doc01_password_reuse_research_paper.pdf": {
        "doc_slug": "doc01_password_reuse",
        "doc_title": "How Users Choose and Reuse Passwords",
        "doc_type": "research_paper",
        "author": "Ameya Hanamsagar, Simon S. Woo, Christopher Kanich, Jelena Mirkovic",
        "course_code": "CS-SEC",
        "description": "Lab study on password reuse, structure, and user risk perceptions.",
    },
    "doc02_spix_macaw_restoration_paper.pdf": {
        "doc_slug": "doc02_spix_macaw",
        "doc_title": "Coexistence and Habitat Restoration Planning for the Reintroduction of Spix's Macaw",
        "doc_type": "research_paper",
        "author": "Ugo Eichler Vercillo et al.",
        "course_code": "BIO-101",
        "description": "Conservation biology study on Spix's macaw reintroduction in Curaçá, Bahia, Brazil.",
    },
    "doc03_cpulator_arm_assembly_guide.pdf": {
        "doc_slug": "doc03_cpulator_arm",
        "doc_title": "CPUlator ARM Assembly Program Trace and Analysis",
        "doc_type": "course_material",
        "author": "Computer Systems Faculty",
        "course_code": "COA-2026",
        "description": "Step-by-step ARM assembly trace and register state analysis in CPUlator.",
    },
    "doc04_arm_assembly_trace_analysis.docx": {
        "doc_slug": "doc04_arm_trace",
        "doc_title": "CPUlator ARM Assembly Program Trace and Analysis Report",
        "doc_type": "course_material",
        "author": "Computer Systems Faculty",
        "course_code": "COA-2026",
        "description": "Structured trace tables and register dependency synthesis.",
    },
    "doc05_ai_and_automation.docx": {
        "doc_slug": "doc05_ai_automation",
        "doc_title": "AI & Automation / Technology Support for Localization Operations",
        "doc_type": "curriculum",
        "author": "Localization Operations Faculty",
        "course_code": "AI-AUTO",
        "description": "Competency guide detailing core skills (Python, APIs, JSON, Git) for AI interns.",
    },
    "sample_doc1.md": {
        "doc_slug": "sample_doc1_ai_libraries",
        "doc_title": "Introduction to AI in Libraries",
        "doc_type": "notes",
        "author": "Library Information Systems",
        "course_code": "LIS-101",
        "description": "Overview of AI augmentation and research efficiency in university libraries.",
    },
    "doc07_library_research_assistant_prd.pdf": {
        "doc_slug": "doc07_library_prd",
        "doc_title": "Product Requirements Document (PRD) — LibraAI",
        "doc_type": "specification",
        "author": "Team 05 | Squad 69",
        "course_code": "SE-RAG",
        "description": "Technical specification, functional requirements, and architecture for LibraAI.",
    },
    "sample_doc2.txt": {
        "doc_slug": "sample_doc2",
        "doc_title": "University Library Guidelines",
        "doc_type": "notes",
        "author": "Library Administration",
        "course_code": "LIS-101",
        "description": "Sample guidelines document for extraction testing.",
    },
    "sample_doc3.txt": {
        "doc_slug": "sample_doc3",
        "doc_title": "Research Ethics and Academic Integrity",
        "doc_type": "notes",
        "author": "Academic Ethics Committee",
        "course_code": "ETH-100",
        "description": "Sample notes on ethical research practices.",
    },
}


def get_document_catalog_entry(filename: str) -> Dict[str, Any]:
    """Retrieve catalog metadata for a given file or return fallback values."""
    base = filename.replace(".json", "")
    if base in CORPUS_CATALOG:
        return CORPUS_CATALOG[base]
    # Fallback heuristic
    slug = base.split(".")[0].replace(" ", "_").lower()
    return {
        "doc_slug": slug,
        "doc_title": base,
        "doc_type": "other",
        "author": "Unknown",
        "course_code": None,
        "description": "",
    }
