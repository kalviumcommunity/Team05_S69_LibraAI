"""
LibraAI - Citation Formatting Utilities

Formats citations using only stored ChunkMetadata.
Reference: PRD §8.5, FR-15, FR-16, FR-18
"""

from typing import Iterable

from config.schema import ChunkMetadata


def format_citation(chunk_metadata: ChunkMetadata) -> str:
    """
    Format a single chunk's metadata into a human-readable citation.

    Expected format:
        📄 **Document Title** — Page 14 *(Section: V. Password Extraction)*

    Missing page numbers and sections are handled gracefully.
    """

    title = getattr(chunk_metadata, "doc_title", None) or "document title not available"

    page_number = getattr(chunk_metadata, "page_number", None)
    if page_number is None or page_number == "":
        page = "page not available"
    else:
        page = f"Page {page_number}"

    section = getattr(chunk_metadata, "section", None)
    if section is None or str(section).strip() == "":
        section_text = "section not available"
    else:
        section_text = str(section)

    return f"📄 **{title}** — {page} *(Section: {section_text})*"


def format_citations_list(chunks: Iterable[ChunkMetadata]) -> str:
    """
    Format multiple chunk metadata objects as separate citation lines.

    Returns an empty string when the chunk collection is empty.
    """

    citations = [format_citation(chunk) for chunk in chunks]

    return "\n".join(citations)
