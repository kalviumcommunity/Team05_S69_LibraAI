# LibraAI — Ground-Truth Evaluation Dataset (v1.0)
**Dataset Version:** 1.0.0  
**Date:** September 17, 2026  
**Authors:** Team 05 | Squad 69 (Alliance Campus)  
**Reference:** PRD §6.1, §7.1, §7.2, §8.3 (FR-08–FR-10), §10

---

## 1. Overview & Evaluation Methodology

This ground-truth evaluation set contains **13 curated benchmark questions** designed prior to full-corpus indexing. It provides an objective standard to measure and track three essential RAG system metrics across sprint iterations:

1. **Retrieval Recall (Target ≥ 80%):** Does the top-k vector retrieval retrieve the exact expected chunk from the correct source document and section?
2. **Answer Groundedness & Accuracy (Target ≥ 80%):** Does the LLM output strictly reflect the facts stated in the retrieved context without hallucination or external fabrication?
3. **Refusal Accuracy (Target 100%):** Does the system cleanly trigger the explicit refusal path (*"I don't know / not covered in the available materials"*) when presented with out-of-corpus queries, short-circuiting prior to generating an LLM hallucination?

### Evaluation Categories
- **Direct Fact Retrieval:** Specific data points, dates, and names explicitly stated in corpus text.
- **Tabular & Statistical Extraction:** Values extracted from structured tables and demographic surveys.
- **Synthesizing / Cross-Document:** Concepts comparing materials across multiple documents or sections.
- **Procedural / Algorithmic:** Code execution, trace step logic, and register dependency analysis.
- **Refusal Guardrails (Out-of-Corpus):** Deliberately unsupported questions spanning unrelated academic domains (quantum mechanics, world history, molecular biology).

---

## 2. Ground-Truth Test Cases

### Test Case GT-01: Password Reuse Rates & Motivations
- **Question:** What percentage of participants in the password reuse study reused some password verbatim, and what primary reason did they provide?
- **Category:** In-Corpus / Direct Fact Retrieval
- **Target Document:** `doc01_password_reuse_research_paper.pdf`
- **Target Location:** Page 14, Section V ("Password Extraction and Reuse"), Subsection B
- **Expected Answer:**
  > In the study, 34 out of 50 participants had at least one pair of reused passwords, and virtually all participants who reused passwords verbatim stated they did so for "memorability" reasons.
- **Verification Keywords:** `34 out of 50`, `memorability`, `reused verbatim`
- **Success Criteria:** Retrieval returns Page 14 of DOC-01; generated answer mentions memorability and participant counts.

---

### Test Case GT-02: Password Sharing Demographics
- **Question:** According to the study on password reuse, what percentage of participants reported that they share passwords only among family members or close contacts?
- **Category:** In-Corpus / Statistical & Survey Extraction
- **Target Document:** `doc01_password_reuse_research_paper.pdf`
- **Target Location:** Page 14, Section V-B (and Page 15 Table)
- **Expected Answer:**
  > Exactly 14% of participants reported that they share passwords only among family members or close contacts.
- **Verification Keywords:** `14%`, `family`, `share passwords`
- **Success Criteria:** Retrieval includes Page 14/15; answer accurately cites 14%.

---

### Test Case GT-03: Spix’s Macaw Extinction and Study Location
- **Question:** In what year was the Spix’s macaw declared extinct in the wild, and in which Brazilian municipality was the reintroduction and coexistence study conducted?
- **Category:** In-Corpus / Direct Fact Retrieval
- **Target Document:** `doc02_spix_macaw_restoration_paper.pdf`
- **Target Location:** Page 1 (Abstract) and Page 2 (Introduction / Context)
- **Expected Answer:**
  > The Spix's macaw was considered extinct in the wild in the year 2000. The coexistence and habitat restoration study was conducted in the municipality of Curaçá, located in the state of Bahia, Brazil.
- **Verification Keywords:** `2000`, `extinct in the wild`, `Curaçá`, `Bahia`
- **Success Criteria:** Correct year (2000) and location (Curaçá, Bahia) cited with Page 1 or Page 2.

---

### Test Case GT-04: Socioeconomic Survey Sample Size & Gender Breakdown
- **Question:** How many household interviews were conducted in Curaçá for the Spix’s macaw study, and what proportion of the respondents were men?
- **Category:** In-Corpus / Tabular & Demographic Fact
- **Target Document:** `doc02_spix_macaw_restoration_paper.pdf`
- **Target Location:** Page 3, Methods / Socioeconomic Characteristics (and Table 1)
- **Expected Answer:**
  > Structured in-person interviews were conducted with 288 rural household respondents between 2022 and 2023, and 72% of the respondents were men.
- **Verification Keywords:** `288 respondents`, `72%`, `men`
- **Success Criteria:** Answer precisely mentions 288 respondents and 72% men citing Page 3.

---

### Test Case GT-05: ARM Assembly Register Trace Values
- **Question:** In the CPUlator ARM assembly program, what are the final decimal values of registers `r6` and `r7` after all seven instructions execute?
- **Category:** In-Corpus / Procedural & Tabular Trace
- **Target Document:** `doc03_cpulator_arm_assembly_guide.pdf` (or `doc04_arm_assembly_trace_analysis.docx`)
- **Target Location:** Page 2, "Final Register State Table" / Steps 6 & 7 (DOCX Table 1 & Table 2)
- **Expected Answer:**
  > After executing all 7 instructions, the final decimal value of register `r6` is 144 (hexadecimal `0x90`, calculated from `24 * 6`), and the final decimal value of register `r7` is 24 (hexadecimal `0x18`, calculated from `12 + 12`).
- **Verification Keywords:** `r6 = 144`, `r7 = 24`, `0x90`, `0x18`
- **Success Criteria:** Exact register values (r6=144, r7=24) correctly identified from Page 2.

---

### Test Case GT-06: Assembly Instruction Order Dependency
- **Question:** If the order of instructions 6 (`mul r6, r3, r2`) and 7 (`add r7, r4, r5`) in the ARM program is swapped, does the final value of register `r7` change? Explain why.
- **Category:** In-Corpus / Algorithmic Reasoning
- **Target Document:** `doc03_cpulator_arm_assembly_guide.pdf`
- **Target Location:** Page 4, "Question 3 — Instruction Order" (and Page 5)
- **Expected Answer:**
  > No, the final value of register `r7` does not change. Register `r7` depends only on `r4` (12) and `r5` (12), which were already computed in Steps 4 and 5. Because `r7` has no data dependency on `r6` or instruction 6, it evaluates to 24 regardless of whether instruction 6 or 7 executes first.
- **Verification Keywords:** `does not change`, `no dependency on r6`, `r7 = 24`, `r4 + r5`
- **Success Criteria:** Explains absence of data dependency and confirms value remains 24, citing Page 4.

---

### Test Case GT-07: Required Skills for AI & Automation Internship
- **Question:** What programming language and technical skills are required for the AI & Automation internship supporting localization operations?
- **Category:** In-Corpus / Curriculum & Requirements
- **Target Document:** `doc05_ai_and_automation.docx`
- **Target Location:** Section "Technical Skills", Paragraphs 4–11
- **Expected Answer:**
  > Python is the required programming language. Core technical competencies include debugging and error handling, understanding web applications and APIs, handling JSON and structured data, reading and working with existing code, basic Git/version control, and strong problem-solving abilities.
- **Verification Keywords:** `Python`, `debugging`, `APIs`, `JSON`, `Git`
- **Success Criteria:** Mentions Python and key skills from Technical Skills section.

---

### Test Case GT-08: LibraAI Latency and Performance Targets
- **Question:** According to the LibraAI PRD, what is the maximum end-to-end query latency target for a live demo, and what are the targets for answer groundedness and retrieval recall?
- **Category:** In-Corpus / System Specification
- **Target Document:** `doc07_library_research_assistant_prd.pdf`
- **Target Location:** Section 7.1 (Product Metrics) and Section 7 (Non-Functional Requirements)
- **Expected Answer:**
  > The maximum end-to-end query latency target is under 8–10 seconds. The target threshold for both answer groundedness and retrieval recall on the ground-truth evaluation set is ≥ 80%.
- **Verification Keywords:** `8–10 seconds`, `80%`, `groundedness`, `recall`
- **Success Criteria:** Correct latency window (<8–10s) and accuracy target (≥80%) cited from Section 7.1.

---

### Test Case GT-09: AI Augmentation in University Libraries
- **Question:** How does the introduction of Artificial Intelligence augment university library research processes according to the course overview?
- **Category:** In-Corpus / Conceptual Overview
- **Target Document:** `data/sample_doc1.md`
- **Target Location:** Page 1, Section "Introduction to AI in Libraries"
- **Expected Answer:**
  > Artificial Intelligence augments university library research processes by improving research efficiency, reducing the need for students to manually search and scroll through dozens of unrelated documents.
- **Verification Keywords:** `augment`, `improve efficiency`, `manual search`
- **Success Criteria:** References efficiency improvement and library evolution.

---

### Test Case GT-10: Ingestion Handling of Malformed or Unreadable Documents
- **Question:** Under the LibraAI non-functional requirements, how must the ingestion pipeline handle malformed or unreadable documents?
- **Category:** In-Corpus / Data Quality & NFR
- **Target Document:** `doc07_library_research_assistant_prd.pdf`
- **Target Location:** Section 6.3 (Data Quality Requirements) and NFR Constraints
- **Expected Answer:**
  > Malformed or unreadable documents must be logged and flagged (e.g. in an error log such as `ingestion_errors.log`) and must never be silently ignored or skipped.
- **Verification Keywords:** `logged and flagged`, `never silently ignored`, `ingestion_errors.log`
- **Success Criteria:** Cites non-negotiable rule that unreadable documents are logged rather than dropped.

---

### Test Case GT-11: Shor's Quantum Factoring Algorithm (Out-of-Corpus Refusal)
- **Question:** How does Shor's algorithm achieve polynomial-time integer factorization on a fault-tolerant quantum computer using quantum Fourier transforms?
- **Category:** Out-of-Corpus / Refusal Path Testing
- **Target Document:** `None (Out-of-Corpus)`
- **Target Location:** `N/A`
- **Expected Answer:**
  > "I don't know / not covered in the available materials."
- **Expected Behavior:**
  - Semantic retrieval similarity score must fall below the configurable relevance threshold.
  - The pipeline must terminate immediately without passing the query to the LLM generation step.
  - The system must return `{ refused: true, answer: "I don't know / not covered in the available materials.", citations: [] }`.

---

### Test Case GT-12: Storming of the Bastille (Out-of-Corpus Refusal)
- **Question:** On what exact date did Parisian revolutionaries storm the Bastille fortress during the French Revolution, and who was the governor who surrendered?
- **Category:** Out-of-Corpus / Refusal Path Testing
- **Target Document:** `None (Out-of-Corpus)`
- **Target Location:** `N/A`
- **Expected Answer:**
  > "I don't know / not covered in the available materials."
- **Expected Behavior:**
  - Retrieval scores fall below threshold.
  - Refusal triggered cleanly with 0 hallucinations.

---

### Test Case GT-13: CRISPR-Cas9 Endonuclease PAM Motif (Out-of-Corpus Refusal)
- **Question:** What is the exact nucleotide sequence of the protospacer adjacent motif (PAM) required by Streptococcus pyogenes Cas9 for target DNA cleavage?
- **Category:** Out-of-Corpus / Refusal Path Testing
- **Target Document:** `None (Out-of-Corpus)`
- **Target Location:** `N/A`
- **Expected Answer:**
  > "I don't know / not covered in the available materials."
- **Expected Behavior:**
  - Retrieval scores fall below threshold.
  - System refuses to answer from external knowledge.

---

## 3. Ground-Truth Summary Matrix

| ID | Topic / Focus | Target Document | Page / Section | Query Type | Expected Outcome |
|---|---|---|---|---|---|
| **GT-01** | Password reuse rate & reasons | `doc01_password_reuse_research_paper.pdf` | Page 14, Sec V-B | Direct Fact | Fact-grounded answer + citation |
| **GT-02** | Password sharing with family | `doc01_password_reuse_research_paper.pdf` | Page 14–15 | Statistics | Fact-grounded answer + citation |
| **GT-03** | Spix's macaw extinction year & place | `doc02_spix_macaw_restoration_paper.pdf` | Page 1–2 | Direct Fact | Fact-grounded answer + citation |
| **GT-04** | Household survey sample & gender % | `doc02_spix_macaw_restoration_paper.pdf` | Page 3, Table 1 | Survey Data | Fact-grounded answer + citation |
| **GT-05** | Final decimal values for r6 & r7 | `doc03_cpulator_arm_assembly_guide.pdf` | Page 2 | Tabular Trace | Exact register values (144, 24) |
| **GT-06** | Instruction swap dependency analysis | `doc03_cpulator_arm_assembly_guide.pdf` | Page 4 | Algorithmic | Explains independence, r7=24 |
| **GT-07** | Technical skills for AI internship | `doc05_ai_and_automation.docx` | Paras 4–11 | Curriculum | Lists Python, APIs, JSON, Git |
| **GT-08** | Latency & accuracy targets | `doc07_library_research_assistant_prd.pdf` | Sec 7.1 | Specifications | <8–10s, ≥80% recall/groundedness |
| **GT-09** | AI library augmentation purpose | `sample_doc1.md` | Page 1 | Overview | Explains research efficiency |
| **GT-10** | Unreadable document policy | `doc07_library_research_assistant_prd.pdf` | Sec 6.3, NFR | Policy / NFR | Must log, never silently drop |
| **GT-11** | Shor's quantum algorithm | *None* | *N/A* | Out-of-Corpus | **Explicit Refusal ("I don't know")** |
| **GT-12** | Storming of the Bastille | *None* | *N/A* | Out-of-Corpus | **Explicit Refusal ("I don't know")** |
| **GT-13** | CRISPR-Cas9 PAM motif | *None* | *N/A* | Out-of-Corpus | **Explicit Refusal ("I don't know")** |

---

## 4. Usage Instructions for Regression Testing

1. Run this benchmark set on Day 6 using the retrieval CLI test harness (`python query_test.py`) to verify retrieval recall (correct chunk in top-k).
2. Run this benchmark set on Day 7–9 after LLM prompt integration to measure answer correctness and citation formatting.
3. Record quantitative evaluation results in `eval/results_v1.md`.
4. If retrieval recall or answer accuracy falls below **80%**, adjust chunk size, overlap, or prompt instructions and re-run the full 13-question suite.
