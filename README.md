# Round 1B Solution – Adobe Hackathon 2025

## Approach
- Implements **Persona-Driven Document Intelligence** as described in the challenge.
- Accepts multiple related PDFs (3–10) and processes them to identify the **most relevant sections** based on:
  - **Persona** (role description).
  - **Job-to-be-done** (task/goal of the persona).
- Extracted sections are ranked by importance and outputted in a structured JSON format.
- Includes sub-section analysis with refined text summaries.
- Designed to be **generic and domain-agnostic** (works across research papers, reports, educational content, etc.).

### Key Steps
1. Parse input PDFs using **PyMuPDF** and/or **pdfplumber**.
2. Identify headings, sub-headings, and text blocks.
3. Use **keyword matching + scoring algorithms** to rank sections relevant to persona and job.
4. Generate an **output JSON** containing:
   - Metadata (documents, persona, job-to-be-done, timestamp).
   - Extracted sections (document name, page number, section title, importance rank).
   - Sub-section analysis (document name, refined text, page number).

---




## How to Build and Run
### 1. Build Docker Image
docker build --platform linux/amd64 -t round1b_solution:latest .



### 2. Run the Container
If you are inside challenge_1b folder:

docker run --rm -v "${PWD}\app\input:/app/input" -v "${PWD}\app\output:/app/output" --network none round1b_solution:latest

For Windows (if running outside the folder):

docker run --rm -v "C:\Users\Admin\OneDrive\Desktop\adobe problem solution\challenge_1b\app\input:/app/input" -v "C:\Users\Admin\OneDrive\Desktop\adobe problem solution\challenge_1b\app\output:/app/output" --network none round1b_solution:latest



## Dependencies
- PyMuPDF
- pdfplumber
- numpy


## Output
## Input/Output Mapping

- Place all input PDF files inside `/app/input/PDF/`.
Output folder: /output

A output.json file will be generated 