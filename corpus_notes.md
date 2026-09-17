# LibraAI — Corpus Inspection Notes & Data Profiling Report
**Document Version:** 1.0.0  
**Date:** September 17, 2026  
**Authors:** Team 05 | Squad 69 (Alliance Campus)  
**Reference:** PRD §6.1, §6.2, §6.3, §7.2, §10, §12 (Risk R1)

---

## 1. Executive Summary & Inventory Profile

Before developing the document ingestion, cleaning, and chunking modules for **LibraAI**, a representative sample of 8 documents spanning multiple academic genres (research papers, theses/project reports, course laboratory guides, technical curriculum documents, system specifications, and slide decks) was manually and programmatically inspected.

The primary objectives of this data inspection were:
1. Identify structural elements that introduce noise into retrieval (running headers/footers, page numbers, licensing notices).
2. Locate bibliography/reference sections to formulate exclusion or tagging rules (preventing retrieval contamination).
3. Analyze table and figure layouts to avoid splitting coherent multi-line tabular data across chunk boundaries.
4. Detect encoding issues, ligatures, zero-width spaces, and multi-column reading flows.
5. Verify page number extractability across PDF, DOCX, and Markdown formats.
6. Validate scanned vs. digital-native PDFs to identify OCR dependencies early (PRD Risk R1).

### Corpus Overview Table

| Document ID | Filename | Document Type | Format | Length | Extractable Text? | Primary Discipline |
|---|---|---|---|---|---|---|
| **DOC-01** | `doc01_password_reuse_research_paper.pdf` | Research Paper | PDF (2-column) | 16 pages | Yes (~5,500 chars/page) | Computer Science / Cybersecurity |
| **DOC-02** | `doc02_spix_macaw_restoration_paper.pdf` | Research Paper | PDF (Journal) | 9 pages | Yes (~4,500 chars/page) | Conservation Biology / Ecology |
| **DOC-03** | `doc03_cpulator_arm_assembly_guide.pdf` | Course Lab Guide | PDF (Digital) | 5 pages | Yes (~700 chars/page) | Computer Systems / Architecture |
| **DOC-04** | `doc04_arm_assembly_trace_analysis.docx` | Lab Report / Analysis | DOCX | 52 paras, 3 tables | Yes (Full XML) | Computer Architecture |
| **DOC-05** | `doc05_ai_and_automation.docx` | Curriculum Guide | DOCX | 104 paras | Yes (Full XML) | AI & Workflow Automation |
| **DOC-06** | `sample_doc1.md` | Course Overview | Markdown | 4 lines / 197 chars | Yes (Raw text) | Library & Information Science |
| **DOC-07** | `doc07_library_research_assistant_prd.pdf` | System Specification | PDF (Digital) | 13 pages | Yes (~2,200 chars/page) | Systems Engineering / RAG |
| **DOC-08** | `recurssion & backtraking bootcamp.pdf` | Lecture Slides | PDF (Scanned) | 60 pages | **No (0 chars on all pages)** | Data Structures & Algorithms |

---

## 2. Detailed Per-Document Inspection

### DOC-01: How Users Choose and Reuse Passwords
- **File:** `data/doc01_password_reuse_research_paper.pdf`
- **Type:** Peer-reviewed academic conference/journal research paper
- **Domain:** Computer Science, Human-Computer Interaction (HCI), Cybersecurity
- **Structure:** 16 pages, standard 2-column IEEE/ACM format.
- **Detailed Findings:**
  1. **Headers & Footers:**
     - Header: Alternating running headers starting from page 2. Left column heads contain subsection names (e.g., *“B. Password Extraction”*, *“Our first contribution lies in our novel study methodology”*).
     - Footer: Discrete page numbers centered at the bottom of each page (`1`, `2`, ..., `16`). The first page footer includes author affiliation footnotes and copyright/permission block.
  2. **Reference / Bibliography Section:**
     - **Location:** Begins on **Page 15** in the lower half of the right-hand column under the bold heading `REFERENCES`, spanning through the entirety of **Page 16**.
     - **Format:** 38 numbered citations in standard IEEE bracketed notation (e.g., `[1]`, `[2]`).
     - **Retrieval Implication:** Reference lines contain heavy keyword concentrations (e.g., "password", "authentication", "reuse") which can cause false-positive semantic matches if not stripped or tagged during Day 3 cleaning.
  3. **Figures & Tables:**
     - Contains multiple figures (e.g., *Fig. 1: User study flow*, *Fig. 2: Password composition*) and multi-row tables (e.g., *Table I: Demographics*, *Table IV: Password reuse patterns*).
     - Text inside tables is condensed and contains statistical percentages (`68%`, `14%`). Chunkers must maintain table context rather than splitting mid-table.
  4. **Inconsistent Formatting & Encoding Artifacts:**
     - Two-column reading order: Standard naive extraction can read across horizontal lines instead of following column 1 then column 2. PyMuPDF's block-based extraction (`get_text("blocks")`) is required.
     - Ligature characters present: `\ufb01` (`fi`) and `\ufb02` (`fl`) appear throughout the text (e.g., *“ﬁrst”*, *“ﬂow”*). Must be normalized to standard ASCII (`fi`, `fl`).
  5. **Page Number Extractability:**
     - Highly extractable. Footers contain single numeric strings matching PDF page indices 1:1.

---

### DOC-02: Coexistence and Habitat Restoration Planning for the Reintroduction of Spix’s Macaw
- **File:** `data/doc02_spix_macaw_restoration_paper.pdf`
- **Type:** Published peer-reviewed scientific journal article (*Conservation Biology*, Wiley)
- **Domain:** Environmental Science, Conservation Biology, Wildlife Management
- **Structure:** 9 pages, mixed 1-column abstract and 2-column body text.
- **Detailed Findings:**
  1. **Headers & Footers:**
     - Header: Running header on odd pages displays the journal title `CONSERVATION BIOLOGY`, while even pages display page progress indicator `2 of 9`, `4 of 9`, `8 of 9`.
     - Footer: Displays article DOI (`https://doi.org/10.1111/cobi.70105`), copyright information, and submission metadata.
  2. **Reference / Bibliography Section:**
     - **Location:** Header `REFERENCES` appears on **Page 8** (right column, mid-page) and covers all of **Page 9**.
     - **Format:** APA-style alphabetical bibliography with author names, years, titles, and DOIs.
     - **Retrieval Implication:** APA citations contain frequent domain terms (*"Spix's macaw"*, *"Curaçá"*, *"habitat"*), posing high risk of false retrieval hits.
  3. **Figures & Tables:**
     - Includes embedded map figures (*Figure 1: Study region in Bahia, Brazil*), conceptual diagrams (*Figure 3: Interaction diagram*), and survey tables (*Table 1: Socioeconomic characteristics of rural properties in Curaçá*).
     - Captions frequently span multiple lines and contain detailed methodologies.
  4. **Inconsistent Formatting & Encoding Artifacts:**
     - Contains Portuguese accents and diacritics (*Curaçá*, *Juazeiro*, *Pambu*, *Gráfica*). UTF-8 normalization is essential.
     - Cordel literature illustration callouts on Page 4 create discontinuous paragraphs.
  5. **Page Number Extractability:**
     - Very high. The header pattern `X of 9` reliably indicates physical journal page numbers.

---

### DOC-03: CPUlator ARM Assembly Program Trace and Analysis
- **File:** `data/doc03_cpulator_arm_assembly_guide.pdf`
- **Type:** University Course Material / Lab Instruction & Solution Manual
- **Domain:** Computer Systems, Computer Organization and Architecture (COA)
- **Structure:** 5 pages, digital-native PDF with code listings, register diagrams, and trace explanations.
- **Detailed Findings:**
  1. **Headers & Footers:**
     - Header: No formal running header; top of Page 1 contains course task banner (`CPUlator ARM Assembly Program / Trace and Analysis`). Subsequent pages start directly with question titles (`Step 3`, `Question 2 — Explain Step 6`, `Question 3 — Instruction Order`).
     - Footer: No running page footer; bottom lines terminate with code comments or equation results.
  2. **Reference / Bibliography Section:**
     - **Location:** None. Lab exercises and course solution guides do not have bibliographies.
  3. **Figures & Tables:**
     - Contains register equations, step-by-step arithmetic traces (`r3 = r1 + r2 = 18 + 6 = 24 = 0x18`), and tabular register dumps (`Final Register State`).
  4. **Inconsistent Formatting & Encoding Artifacts:**
     - Pervasive zero-width spaces (`\u200b`) between lines and words.
     - Assembly comment delimiters (`@`, `#`) and operator symbols (`<<`, `×`).
     - Unconventional indentation and variable line heights across steps.
  5. **Page Number Extractability:**
     - Physical page digits are absent from text. Extraction must rely strictly on PyMuPDF page object indices (`doc[i].number + 1`).

---

### DOC-04: CPUlator ARM Assembly Program Trace and Analysis (DOCX)
- **File:** `data/doc04_arm_assembly_trace_analysis.docx`
- **Type:** Course Assignment / Lab Submission Report
- **Domain:** Computer Architecture
- **Structure:** 52 paragraphs, 3 formatted Word tables.
- **Detailed Findings:**
  1. **Headers & Footers:**
     - Neither running headers nor footers are defined in document properties.
  2. **Reference / Bibliography Section:**
     - None.
  3. **Figures & Tables:**
     - Contains 3 critical structured tables:
       - *Table 1 (8 rows × 5 cols):* Trace table containing columns `Step`, `Instruction`, `Register Changed`, `Hex Value`, and `Decimal Value`.
       - *Table 2 (8 rows × 3 cols):* Final register summary (`Register`, `Hex Value`, `Decimal Value`).
       - *Table 3 (4 rows × 3 cols):* Synthesis questions and answers (`Question 1`, `Question 2`, `Question 3`).
     - Standard paragraph extractors discard table cell structures. Table cells must be explicitly parsed row-by-row with column headers preserved.
  4. **Inconsistent Formatting & Encoding Artifacts:**
     - Code snippets formatted in Courier New mixed with body Calibri text.
     - Empty paragraph elements used for vertical spacing.
  5. **Page Number Extractability:**
     - Native DOCX does not store fixed page numbers. Pages must be synthesized based on section breaks or paragraph counts.

---

### DOC-05: AI & Automation / Technology Support for Localization Operations
- **File:** `data/doc05_ai_and_automation.docx`
- **Type:** Academic Coursework / Curriculum / Competency Guide
- **Domain:** Artificial Intelligence, Software Engineering, Localization Workflows
- **Structure:** 104 paragraphs, hierarchical bullet points.
- **Detailed Findings:**
  1. **Headers & Footers:**
     - No running headers/footers in document XML.
  2. **Reference / Bibliography Section:**
     - None.
  3. **Figures & Tables:**
     - No tables or figures; consists of dense nested bulleted lists organizing skills: *Python*, *Debugging*, *Web applications & APIs*, *JSON*, *Git*.
  4. **Inconsistent Formatting & Encoding Artifacts:**
     - Inconsistent bullet character points (`•`, `-`, `o`).
     - Hanging section titles with empty paragraphs between them.
  5. **Page Number Extractability:**
     - Requires synthetic page tracking or section-level metadata (`section="Technical Skills"`).

---

### DOC-06: Introduction to AI in Libraries
- **File:** `data/sample_doc1.md`
- **Type:** Course Note / Digital-native Markdown
- **Domain:** Library Information Systems & AI
- **Structure:** 4 lines, 197 characters.
- **Detailed Findings:**
  1. **Headers & Footers:** Standard `# Introduction to AI in Libraries` markdown heading.
  2. **Reference / Bibliography Section:** None.
  3. **Figures & Tables:** None.
  4. **Inconsistent Formatting & Encoding Artifacts:** Minimalistic; risk of being under-length for token splitters (197 characters < 300 token target).
  5. **Page Number Extractability:** Single-page document (`page_number: 1`).

---

### DOC-07: Product Requirements Document (PRD) — LibraAI
- **File:** `data/doc07_library_research_assistant_prd.pdf`
- **Type:** Technical Specification / System Architecture Document
- **Domain:** Software Engineering, Natural Language Processing, Information Retrieval
- **Structure:** 13 pages, comprehensive sections 1 through 14 + Appendices A and B.
- **Detailed Findings:**
  1. **Headers & Footers:**
     - Header: Document banner on page 1, running title on subsequent pages.
     - Footer: Clean page footer format: `Page X of 13`.
  2. **Reference / Bibliography Section:**
     - Concludes with *Appendix A — Glossary* and *Appendix B — Metadata Schema Contract* on pages 12–13.
  3. **Figures & Tables:**
     - Architecture flow diagrams (ASCII/Mermaid representation).
     - 6 markdown-style requirement tables (`Functional Requirements`, `Success Metrics`, `Milestones`, `Risks`).
  4. **Inconsistent Formatting & Encoding Artifacts:**
     - Multi-line table cell wraps.
     - Unicode symbols for checkboxes and status indicators (`≥`, `—`, `▪`).
  5. **Page Number Extractability:**
     - High reliability via footer parsing or PDF page index.

---

### DOC-08: Recursion & Backtracking Bootcamp Notes (Scanned Specimen)
- **File:** `recurssion & backtraking bootcamp_260807_151623 (2).pdf` (17.5 MB)
- **Type:** Classroom Slide Deck / Handwriting & Diagram Scans
- **Domain:** Computer Science / Algorithms
- **Structure:** 60 pages.
- **Detailed Findings:**
  1. **Headers & Footers:** Embedded visually in scanned image bitmaps.
  2. **Reference / Bibliography Section:** None.
  3. **Figures & Tables:** Hand-drawn recursion trees, call stack diagrams.
  4. **Critical Risk Finding (PRD §12, Risk R1):**
     - **0 extractable characters across all 60 pages** using PyMuPDF `page.get_text()`.
     - The PDF consists entirely of embedded raster images (JPEG/PNG streams).
     - **Pipeline Action Required:** Ingestion must either employ an OCR engine (such as Tesseract / EasyOCR) or catch and log this file as unreadable (`ingestion_errors.log`) rather than crashing or silently skipping (fulfilling NFR-05).

---

## 3. Cross-Cutting Analysis & Synthesis

### 3.1 Header & Footer Patterns
| Document Category | Header Pattern | Footer Pattern | Cleaning Recommendation |
|---|---|---|---|
| **Academic Papers (DOC-01, DOC-02)** | Running paper/journal title, section name | Bare digits (`1`, `2`) or `X of Y` with DOI | Strip running lines matching regex `^\d+$` or `^\d+\s+of\s+\d+$` and journal titles during Day 3 cleaning. |
| **Lab Manuals (DOC-03)** | No formal header; task banner | None | Retain text; use PDF object page index. |
| **DOCX Files (DOC-04, DOC-05)** | None | None | Generate synthetic page numbers based on section headers. |
| **Specifications (DOC-07)** | Project Title | `Page X of Y` | Strip footer regex `^Page\s+\d+\s+of\s+\d+$`. |

### 3.2 Bibliography / Reference Section Identification
- In research papers (DOC-01, DOC-02), bibliography sections are concentrated in the final 10–15% of the document (Pages 15–16 of DOC-01; Pages 8–9 of DOC-02).
- **Strategy for Day 3 Cleaning:**
  - Detect section boundary headers matching `^(?:REFERENCES|BIBLIOGRAPHY|WORKS CITED)\s*$` (case-insensitive).
  - Do not delete references entirely; instead, tag chunks with `is_reference: true` or exclude them from the primary semantic retrieval collection so they do not hijack student concept queries.

### 3.3 Tables & Layout Complexities
- Academic tables (DOC-01 Table IV, DOC-02 Table 1) and lab trace tables (DOC-04 Table 1) contain compact multi-cell relationships.
- Naive character splitting splits rows mid-cell, destroying relational meaning.
- **Strategy for Day 4 Chunking:**
  - Treat tables as atomic blocks where possible, or split strictly on row boundaries with header rows repeated.

### 3.4 Inconsistent Formatting & Encoding Gotchas
1. **Unicode Ligatures:** Replace `\ufb01` (`fi`) and `\ufb02` (`fl`) with standard ASCII equivalents.
2. **Zero-Width Spaces:** Strip `\u200b`, `\u200c`, and non-breaking spaces (`\u00a0`) in lab PDFs.
3. **Multi-Column Text Flow:** Ensure extraction does not interleave columns horizontally.
4. **Scanned Documents:** Catch documents with `< 50` characters per page and log them to `ingestion_errors.log`.

---

## 4. Recommendations for Next Sprint Days

| Sprint Day | Module | Specific Action Grounded in Corpus Findings |
|---|---|---|
| **Day 2** | Document Loading | Implement PyMuPDF loader preserving `page_number = page.number + 1`. For DOCX, extract table text row-by-row. Log zero-text PDFs to `ingestion_errors.log`. |
| **Day 3** | Cleaning & Normalization | Implement regex-based header/footer removal. Add `tag_references(text)` function to flag bibliographies from Page 15 (DOC-01) and Page 8 (DOC-02). Normalize ligatures and zero-width spaces. |
| **Day 4** | Section-Aware Chunking | Split on markdown `#`, `##` and roman numeral headings (`I.`, `II.`, `Step 1`, `Question 1`). Enforce 300–500 token window with 15% overlap. |
| **Day 5** | Embedding & Indexing | Store locked metadata schema (`doc_title`, `doc_type`, `author`, `course_code`, `section`, `page_number`, `source_path`). Validate sample vectors in ChromaDB. |
