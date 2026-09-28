"""
LibraAI - Canonical Metadata Schema & API Data Contracts
Reference: PRD Appendix B, §6.3, §8.2, FR-19
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class DocType(str, Enum):
    """Enumeration of recognized academic and library document genres."""
    RESEARCH_PAPER = "research_paper"
    COURSE_MATERIAL = "course_material"
    CURRICULUM = "curriculum"
    THESIS = "thesis"
    SPECIFICATION = "specification"
    NOTES = "notes"
    OTHER = "other"


class DocumentMetadata(BaseModel):
    """Metadata representing an entire ingested document."""
    doc_id: str = Field(..., description="Unique slug or identifier for the document")
    doc_title: str = Field(..., description="Canonical title of the document")
    doc_type: DocType = Field(..., description="Category of the document")
    author: str = Field(default="Unknown", description="Author(s) or publishing institution")
    course_code: Optional[str] = Field(default=None, description="Course identifier (e.g. COA-2026)")
    source_path: str = Field(..., description="Relative file path in repository")
    total_pages: int = Field(default=1, description="Total number of pages in the source document")


class ChunkMetadata(BaseModel):
    """
    Locked metadata schema attached to every indexed text chunk.
    Stored directly in ChromaDB along with the chunk vector embedding.
    """
    chunk_id: str = Field(..., description="Deterministic unique identifier: {doc_slug}_p{page}_c{index}")
    doc_title: str = Field(..., description="Canonical title of the document")
    doc_type: str = Field(..., description="Category of the document as a string for ChromaDB compatibility")
    author: str = Field(default="Unknown", description="Author(s) or publishing department")
    course_code: Optional[str] = Field(default=None, description="Course identifier (e.g. COA-2026)")
    section: str = Field(default="General", description="Section heading or topic name")
    page_number: int = Field(default=1, description="1-indexed page number")
    source_path: str = Field(..., description="Relative file path in repository")
    is_reference: bool = Field(default=False, description="Whether this chunk belongs to a bibliography/reference section")
    token_count: int = Field(default=0, description="Estimated token count of the chunk")

    def to_chroma_metadata(self) -> Dict[str, Any]:
        """Convert to ChromaDB-safe dictionary (Chroma requires primitive types int, float, str, bool)."""
        return {
            "chunk_id": self.chunk_id,
            "doc_title": self.doc_title,
            "doc_type": str(self.doc_type),
            "author": self.author,
            "course_code": self.course_code or "",
            "section": self.section,
            "page_number": int(self.page_number),
            "source_path": self.source_path,
            "is_reference": bool(self.is_reference),
            "token_count": int(self.token_count),
        }

    @classmethod
    def from_chroma_metadata(cls, meta: Dict[str, Any]) -> "ChunkMetadata":
        """Reconstruct ChunkMetadata from ChromaDB primitive dictionary."""
        course = meta.get("course_code")
        return cls(
            chunk_id=meta["chunk_id"],
            doc_title=meta["doc_title"],
            doc_type=meta.get("doc_type", "other"),
            author=meta.get("author", "Unknown"),
            course_code=course if course else None,
            section=meta.get("section", "General"),
            page_number=int(meta.get("page_number", 1)),
            source_path=meta.get("source_path", ""),
            is_reference=bool(meta.get("is_reference", False)),
            token_count=int(meta.get("token_count", 0)),
        )


class Citation(BaseModel):
    """
    Source citation attached to generated answers.
    Constructed exclusively from stored chunk metadata (NFR-03).
    """
    doc_title: str = Field(..., description="Document title")
    section: str = Field(default="General", description="Section or subsection name")
    page_number: int = Field(..., description="1-indexed page number")
    source_path: str = Field(..., description="Relative source path")
    chunk_id: Optional[str] = Field(default=None, description="Identifier of the supporting chunk")


class QueryRequest(BaseModel):
    """Input payload for POST /query endpoint."""
    query: str = Field(..., min_length=2, description="Student question or research query")
    course_code: Optional[str] = Field(default=None, description="Optional filter to scope search to a course")
    doc_type: Optional[str] = Field(default=None, description="Optional filter to scope to a document type")
    top_k: int = Field(default=4, ge=1, le=20, description="Number of top chunks to retrieve")


class QueryResponse(BaseModel):
    """Output payload from POST /query endpoint."""
    answer: str = Field(..., description="Concise answer grounded strictly in retrieved chunks, or refusal text")
    citations: List[Citation] = Field(default_factory=list, description="Citations from stored metadata only")
    refused: bool = Field(default=False, description="True if query fell below relevance threshold and was refused")
    confidence_score: Optional[float] = Field(default=None, description="Top retrieval similarity score")
