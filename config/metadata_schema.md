# LibraAI — Metadata Schema Contract
**Specification Version:** 1.0.0  
**Date:** September 18, 2026  
**Authors:** Team 05 | Squad 69 (Alliance Campus)  
**Reference:** PRD Appendix B, §6.3, §8.2, §9, FR-19

---

## 1. Purpose & Locking Strategy

Per PRD §6.3 and §9, the metadata schema must be **locked before the first embedding run**. Changing the metadata schema downstream requires an expensive full re-indexing of ChromaDB and re-processing of the entire document corpus.

This document formalizes the canonical metadata contract enforced across all pipeline stages:
1. **Document Loading (Day 2 Track A):** Ingests raw files and outputs document-level metadata.
2. **Cleaning & Tagging (Day 3 Track A):** Tags reference sections (`is_reference`).
3. **Section-Aware Chunking (Day 4 Track A):** Attaches full chunk-level metadata to each split.
4. **Vector Database Indexing (Day 5 Track A):** Persists metadata alongside embeddings in ChromaDB.
5. **Retrieval & Citation Formatting (Day 5–6 Track B):** Unpacks metadata from retrieved chunks to format citations (`doc_title + page/section`).
6. **API Response (Day 2 & Day 7 Track B):** Serializes citations into FastAPI JSON payloads.

---

## 2. Core Metadata Fields Specification

| Field Name | Type | Required? | Description | Example Value |
|---|---|---|---|---|
| **`doc_title`** | `str` | **Yes** | The canonical human-readable title of the document. | `"How Users Choose and Reuse Passwords"` |
| **`doc_type`** | `str` (Enum) | **Yes** | Academic genre of the document. | `"research_paper"`, `"course_material"`, `"thesis"`, `"specification"`, `"overview"` |
| **`author`** | `str` | **Yes** | Author(s), researcher(s), or institutional department. If unknown, defaults to `"Unknown"`. | `"Ugo Eichler Vercillo et al."` or `"Department of Computer Science"` |
| **`course_code`** | `Optional[str]` | No (Nullable) | University course identifier or curriculum code, used for scoped filtering (FR-07). | `"COA-2026"`, `"BIO-101"`, or `null` |
| **`section`** | `str` | **Yes** | Immediate heading, subsection, or topic name where the chunk text resides. | `"V. Password Extraction and Reuse"`, `"Table 1"`, or `"General"` |
| **`page_number`** | `int` | **Yes** | 1-indexed page number where the chunk originates. (Synthesized for non-paginated DOCX/MD). | `14` |
| **`chunk_id`** | `str` | **Yes** | Deterministic unique identifier: `{doc_slug}_p{page}_c{chunk_index:03d}`. | `"doc01_password_reuse_p14_c002"` |
| **`source_path`** | `str` | **Yes** | Relative file path of the source document in repository. | `"data/doc01_password_reuse_research_paper.pdf"` |
| **`text`** | `str` | **Yes** | Cleaned textual content of the chunk (~300–500 tokens). | `"34 out of our 50 participants have at least one pair of reused passwords..."` |
| **`is_reference`** | `bool` | No (Default `false`) | Flag marking bibliography or reference list chunks (from Day 1 finding) to filter from search. | `false` |
| **`token_count`** | `int` | No (Default `0`) | Approximate token count of chunk text for window validation. | `342` |

---

## 3. Allowed Document Types (`doc_type` Enum)

The `doc_type` field must strictly match one of the following enumerated strings:
- `research_paper`: Peer-reviewed conference or journal papers (e.g. DOC-01, DOC-02).
- `course_material`: Lab instruction manuals, exercise guides, homework trace sheets (e.g. DOC-03, DOC-04).
- `curriculum`: Syllabus, skills guides, job descriptions, academic requirements (e.g. DOC-05).
- `thesis`: Master's / PhD theses or capstone project dissertations.
- `specification`: Requirements specifications, software design docs (e.g. DOC-07 PRD).
- `notes`: Markdown or plaintext lecture notes, summaries (e.g. DOC-06).

---

## 4. Citation Contract (`Citation`)

When an answer is generated, citations are constructed **exclusively from stored metadata** — never hallucinated by the LLM (NFR-03).

The citation structure exposed via API:
```json
{
  "doc_title": "How Users Choose and Reuse Passwords",
  "section": "V. Password Extraction and Reuse",
  "page_number": 14,
  "source_path": "data/doc01_password_reuse_research_paper.pdf",
  "chunk_id": "doc01_password_reuse_p14_c002"
}
```

Format displayed in Streamlit UI:
> 📄 **How Users Choose and Reuse Passwords** — Page 14 *(Section: V. Password Extraction and Reuse)*

---

## 5. API Data Contract (`POST /query`)

### Request Payload (`QueryRequest`)
```json
{
  "query": "What percentage of participants reused passwords verbatim?",
  "course_code": null,
  "doc_type": "research_paper",
  "top_k": 4
}
```

### Response Payload (`QueryResponse`)
```json
{
  "answer": "In the study, 34 out of 50 participants reused some password verbatim, primarily for memorability reasons.",
  "citations": [
    {
      "doc_title": "How Users Choose and Reuse Passwords",
      "section": "V. Password Extraction and Reuse",
      "page_number": 14,
      "source_path": "data/doc01_password_reuse_research_paper.pdf",
      "chunk_id": "doc01_password_reuse_p14_c002"
    }
  ],
  "refused": false,
  "confidence_score": 0.88
}
```

### Refusal Payload (FR-05 & FR-10)
```json
{
  "answer": "I don't know / not covered in the available materials.",
  "citations": [],
  "refused": true,
  "confidence_score": 0.32
}
```
