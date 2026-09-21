"""
Tests for LibraAI citation formatting utilities.

Reference: PRD §8.5, FR-15, FR-16, FR-18
"""

from types import SimpleNamespace

from config.schema import ChunkMetadata
from generation.citations import format_citation, format_citations_list


def make_chunk(
    title="How Users Choose and Reuse Passwords",
    section="V. Password Extraction",
    page_number=14,
    chunk_id="passwords_p14_c0",
):
    """Create fake ChunkMetadata for citation tests."""
    return ChunkMetadata(
        chunk_id=chunk_id,
        doc_title=title,
        doc_type="research_paper",
        section=section,
        page_number=page_number,
        source_path="data/example.pdf",
    )


def test_single_source_citation():
    chunk = make_chunk()

    result = format_citation(chunk)

    assert result == (
        "📄 **How Users Choose and Reuse Passwords** — "
        "Page 14 *(Section: V. Password Extraction)*"
    )


def test_multiple_document_sources():
    chunks = [
        make_chunk(
            title="Research Paper One",
            section="Introduction",
            page_number=3,
            chunk_id="doc1_p3_c0",
        ),
        make_chunk(
            title="Research Paper Two",
            section="Results",
            page_number=8,
            chunk_id="doc2_p8_c0",
        ),
    ]

    result = format_citations_list(chunks)

    expected = (
        "📄 **Research Paper One** — Page 3 *(Section: Introduction)*\n"
        "📄 **Research Paper Two** — Page 8 *(Section: Results)*"
    )

    assert result == expected


def test_missing_page_number():
    chunk = SimpleNamespace(
        doc_title="Example Research Paper",
        page_number=None,
        section="Introduction",
    )

    result = format_citation(chunk)

    assert "page not available" in result
    assert "Introduction" in result


def test_missing_section():
    chunk = SimpleNamespace(
        doc_title="Example Research Paper",
        page_number=7,
        section=None,
    )

    result = format_citation(chunk)

    assert "Page 7" in result
    assert "section not available" in result


def test_empty_chunk_list():
    result = format_citations_list([])

    assert result == ""