# import os
# import json
# import time
# from pathlib import Path
# from typing import List, Dict
# from PyPDF2 import PdfReader
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.metrics.pairwise import cosine_similarity

# def extract_sections(pdf_path: str) -> List[Dict]:
#     """
#     Extract headings or page text from PDF pages.
#     """
#     sections = []
#     reader = PdfReader(pdf_path)
#     for page_num, page in enumerate(reader.pages, start=1):
#         text = page.extract_text()
#         if not text:
#             continue
#         for line in text.split("\n"):
#             if len(line.split()) <= 10 or line.strip().endswith(":"):
#                 sections.append({"page": page_num, "title": line.strip(), "content": text})
#     if not sections:  # fallback: use full page text
#         for page_num, page in enumerate(reader.pages, start=1):
#             text = page.extract_text()
#             if text:
#                 sections.append({"page": page_num, "title": f"Page {page_num}", "content": text})
#     return sections

# def rank_sections(sections, persona, job):
#     """
#     Rank sections by similarity to persona and job-to-be-done.
#     """
#     query = f"{persona} {job}"
#     docs = [sec["content"] for sec in sections]
#     vectorizer = TfidfVectorizer(stop_words="english")
#     tfidf_matrix = vectorizer.fit_transform([query] + docs)
#     scores = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1:])[0]
#     for i, sec in enumerate(sections):
#         sec["score"] = float(scores[i])
#     return sorted(sections, key=lambda x: x["score"], reverse=True)

# def main():
#     input_dir = "/app/input"
#     output_dir = "/app/output"
#     json_file = os.path.join(input_dir, "challenge1b_input.json")

#     if not os.path.exists(json_file):
#         raise FileNotFoundError(f"Expected {json_file} not found in /app/input")

#     # Parse JSON
#     data = json.loads(Path(json_file).read_text(encoding="utf-8"))
#     persona_data = data.get("persona", {})
#     job_data = data.get("job_to_be_done", {})

#     # Extract persona & job as strings
#     persona = " ".join([f"{k}: {v}" for k, v in persona_data.items()]) if isinstance(persona_data, dict) else str(persona_data)
#     job = " ".join([f"{k}: {v}" for k, v in job_data.items()]) if isinstance(job_data, dict) else str(job_data)

#     pdf_dir = os.path.join(input_dir, "PDF")
#     if not os.path.exists(pdf_dir):
#         pdf_dir = os.path.join(input_dir, "PDFs")
#     if not os.path.exists(pdf_dir):
#         raise FileNotFoundError("No 'PDF' or 'PDFs' folder found in /app/input")

#     # Process all PDFs
#     all_results = []
#     pdfs = [f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf")]
#     for pdf_file in pdfs:
#         sections = extract_sections(os.path.join(pdf_dir, pdf_file))
#         ranked = rank_sections(sections, persona, job)
#         for rank, sec in enumerate(ranked, 1):
#             all_results.append({
#                 "document": pdf_file,
#                 "page_number": sec["page"],
#                 "section_title": sec["title"],
#                 "importance_rank": rank,
#                 "score": sec["score"]
#             })

#     # Create output JSON
#     output = {
#         "metadata": {
#             "documents": pdfs,
#             "persona": persona,
#             "job_to_be_done": job,
#             "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
#             "challenge_info": data.get("challenge_info", {})
#         },
#         "extracted_sections": all_results
#     }

#     os.makedirs(output_dir, exist_ok=True)
#     with open(os.path.join(output_dir, "output.json"), "w", encoding="utf-8") as f:
#         json.dump(output, f, indent=2, ensure_ascii=False)

# if __name__ == "__main__":
#     main()











import os
import re
import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Tuple

from PyPDF2 import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# -------------------------- #
# -------- UTILITIES ------- #
# -------------------------- #

def iso_now() -> str:
    return datetime.utcnow().isoformat()

def dict_to_flat_string(d) -> str:
    if isinstance(d, dict):
        return " ".join(f"{k}: {v}" for k, v in d.items())
    return str(d)

def read_persona_job(input_dir: Path) -> Tuple[str, str]:
    """
    Priority:
    1) challenge1b_input.json { persona: <str|dict>, job_to_be_done: <str|dict> }
    2) persona.txt + job.txt
    3) fallback: empty strings
    """
    json_path = input_dir / "challenge1b_input.json"
    if json_path.exists():
        data = json.loads(json_path.read_text(encoding="utf-8"))
        persona = dict_to_flat_string(data.get("persona", ""))
        job = dict_to_flat_string(data.get("job_to_be_done", "")) or dict_to_flat_string(data.get("job", ""))
        return persona, job

    # Fallback txt files
    persona_txt = input_dir / "persona.txt"
    job_txt = input_dir / "job.txt"
    persona = persona_txt.read_text(encoding="utf-8").strip() if persona_txt.exists() else ""
    job = job_txt.read_text(encoding="utf-8").strip() if job_txt.exists() else ""
    return persona, job

def read_input_documents(input_dir: Path) -> List[str]:
    """
    If challenge1b_input.json exists and has "documents" list, use that order;
    else scan PDFs inside /app/input (root or PDF/PDFs dir).
    """
    json_path = input_dir / "challenge1b_input.json"
    if json_path.exists():
        data = json.loads(json_path.read_text(encoding="utf-8"))
        docs = data.get("documents", [])
        if isinstance(docs, list) and docs and isinstance(docs[0], dict) and "filename" in docs[0]:
            return [d["filename"] for d in docs]
        # if it's a list of strings
        if isinstance(docs, list) and docs and isinstance(docs[0], str):
            return docs

    # otherwise discover PDFs
    pdf_paths = list(find_pdf_files(input_dir))
    return [p.name for p in pdf_paths]

def find_pdf_root(input_dir: Path) -> Path:
    """
    Resolve where PDFs are:
    - /app/input/PDF
    - /app/input/PDFs
    - /app/input (root)
    """
    for name in ("PDF", "PDFs"):
        p = input_dir / name
        if p.exists() and p.is_dir():
            return p
    return input_dir

def find_pdf_files(input_dir: Path):
    pdf_root = find_pdf_root(input_dir)
    for p in pdf_root.glob("*.pdf"):
        yield p

def split_into_paragraphs(text: str) -> List[str]:
    """
    Split text into reasonably-sized paragraphs.
    """
    if not text:
        return []
    # First split on double newlines
    parts = re.split(r"\n\s*\n+", text)
    # If still very long lines, fallback to sentence-ish chunking
    paras: List[str] = []
    for part in parts:
        part = part.strip()
        if not part:
            continue
        if len(part) < 400:
            paras.append(part)
        else:
            # Rough sentence splitting
            chunks = re.split(r"(?<=[.!?])\s+", part)
            buf = []
            cur = ""
            for sent in chunks:
                if len(cur) + len(sent) < 500:
                    cur += (" " if cur else "") + sent
                else:
                    if cur:
                        buf.append(cur.strip())
                    cur = sent
            if cur:
                buf.append(cur.strip())
            paras.extend(buf)
    # filter short garbage
    return [p for p in paras if len(p.strip()) > 50]

# -------------------------- #
# ---- SECTION EXTRACTION ---#
# -------------------------- #

def is_heading_candidate(line: str) -> bool:
    line_s = line.strip()
    if not line_s:
        return False
    words = line_s.split()
    # Heuristics
    if len(words) <= 10:
        return True
    if line_s.endswith(":"):
        return True
    # Numbered headings like 1., 1.2.3, I., A), etc.
    if re.match(r"^(\d+(\.\d+)*\.?\)?|[IVXLCM]+\)|[A-Z]\))\s", line_s):
        return True
    # All caps
    if line_s.isupper() and len(words) <= 15:
        return True
    return False

def extract_sections(pdf_path: Path) -> List[Dict]:
    """
    Returns a list of {page, title, content}
    - If we find heading-like lines on a page, we register them.
    - Fallback: page as one section.
    """
    sections = []
    try:
        reader = PdfReader(str(pdf_path))
    except Exception:
        return sections

    had_any = False
    for page_num, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        if not text.strip():
            continue

        page_has_heading = False
        for line in text.split("\n"):
            if is_heading_candidate(line):
                sections.append({"page": page_num, "title": line.strip(), "content": text})
                page_has_heading = True
                had_any = True
        if not page_has_heading:
            # maybe keep for fallback
            pass

    # If no headings detected at all, fallback to full-page sections
    if not had_any:
        for page_num, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text() or ""
            except Exception:
                text = ""
            if text.strip():
                sections.append({"page": page_num, "title": f"Page {page_num}", "content": text})

    return sections

# -------------------------- #
# ------- RANKING ---------- #
# -------------------------- #

def rank_texts(query: str, docs: List[str]) -> List[float]:
    if not docs:
        return []
    vectorizer = TfidfVectorizer(stop_words="english")
    matrix = vectorizer.fit_transform([query] + docs)
    scores = cosine_similarity(matrix[0], matrix[1:])[0]
    return scores.tolist()

def rank_sections(sections: List[Dict], persona: str, job: str) -> List[Dict]:
    if not sections:
        return []
    query = f"{persona} {job}".strip()
    docs = [s["content"] for s in sections]
    scores = rank_texts(query, docs)
    for s, sc in zip(sections, scores):
        s["score"] = float(sc)
    return sorted(sections, key=lambda x: x["score"], reverse=True)

def rank_paragraphs(paragraphs: List[str], persona: str, job: str) -> List[Tuple[str, float]]:
    if not paragraphs:
        return []
    query = f"{persona} {job}".strip()
    scores = rank_texts(query, paragraphs)
    ranked = list(zip(paragraphs, scores))
    ranked.sort(key=lambda x: x[1], reverse=True)
    return ranked

# -------------------------- #
# --------- MAIN ----------- #
# -------------------------- #

def build_output(
    input_documents: List[str],
    persona: str,
    job: str,
    best_sections: List[Dict],
    best_paras: List[Tuple[str, str, int]]
) -> Dict:
    return {
        "metadata": {
            "input_documents": input_documents,
            "persona": persona,
            "job_to_be_done": job,
            "processing_timestamp": iso_now()
        },
        "extracted_sections": [
            {
                "document": doc,
                "section_title": title,
                "importance_rank": rank,
                "page_number": page
            }
            for rank, (doc, title, page) in enumerate(
                [(bs["document"], bs["title"], bs["page"]) for bs in best_sections],
                start=1
            )
        ],
        "subsection_analysis": [
            {
                "document": doc,
                "refined_text": txt,
                "page_number": page
            }
            for (doc, txt, page) in best_paras
        ]
    }

def main():
    input_dir = Path("/app/input")
    output_dir = Path("/app/output")
    output_dir.mkdir(parents=True, exist_ok=True)

    persona, job = read_persona_job(input_dir)
    input_documents = read_input_documents(input_dir)

    pdf_map = {p.name: p for p in find_pdf_files(input_dir)}
    # If input_documents has names not in pdf_map, still process whatever PDFs exist
    pdf_paths = [pdf_map[name] for name in input_documents if name in pdf_map]
    # plus anything else
    for p in find_pdf_files(input_dir):
        if p not in pdf_paths:
            pdf_paths.append(p)

    all_ranked_sections: List[Dict] = []
    for pdf_path in pdf_paths:
        sections = extract_sections(pdf_path)
        ranked = rank_sections(sections, persona, job)
        for r in ranked:
            r["document"] = pdf_path.name
        all_ranked_sections.extend(ranked)

    # pick top 5 sections (or fewer if not enough)
    top_k = 5
    best_sections = sorted(all_ranked_sections, key=lambda x: x["score"], reverse=True)[:top_k]

    # Build top paragraphs list (subsection_analysis)
    # Take paragraphs from the top N sections (here N = 3), then rank them and keep top M = 5
    subsection_paras_from = 3
    max_subsection = 5
    paras_all = []
    for sec in best_sections[:subsection_paras_from]:
        for para in split_into_paragraphs(sec["content"]):
            paras_all.append((sec["document"], sec["page"], para))

    ranked_paras = []
    if paras_all:
        ranked = rank_paragraphs([p[2] for p in paras_all], persona, job)
        # ranked is list of (paragraph_text, score)
        # map back to document/page
        # create a mapping for first occurrence only (best score should come first anyway)
        used = 0
        for (text, score) in ranked:
            for (doc, page, para_text) in paras_all:
                if para_text == text:
                    ranked_paras.append((doc, text, page))
                    used += 1
                    break
            if used >= max_subsection:
                break

    final_out = build_output(
        input_documents=[p.name for p in pdf_paths],
        persona=persona,
        job=job,
        best_sections=best_sections,
        best_paras=ranked_paras
    )

    (output_dir / "output.json").write_text(
        json.dumps(final_out, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )


if __name__ == "__main__":
    main()
