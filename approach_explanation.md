# Approach Explanation (Round 1B)

## 1. Overview
This solution extracts and prioritizes document sections based on a given persona and job-to-be-done.

## 2. Pipeline
1. **PDF Parsing**: Using `PyPDF2` to extract page-wise text.
2. **Section Detection**: Heuristic-based detection of potential headings (short lines, colons, uppercase).
3. **Relevance Ranking**: Using TF-IDF vectorization and cosine similarity with `persona + job-to-be-done` as the query.
4. **JSON Output**: Generates a structured `output.json` with metadata and ranked sections.

## 3. Performance
- Works fully offline (no API calls).
- Processes 3–10 PDFs within the 60s limit on CPU.
- Uses TF-IDF (lightweight, <1GB image size).

## 4. Future Enhancements
- Swap TF-IDF with a compact embedding model (<=1GB total image).
- Add more robust heading detection (font size, bold, numbering patterns).
- Add granular paragraph-level subsection ranking for the "subsection_analysis" block.

---
