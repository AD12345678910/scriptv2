from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import os, json, tempfile
from dotenv import load_dotenv
import PyPDF2
import google.generativeai as genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("Missing GEMINI_API_KEY in environment. Add it to a .env file.")
genai.configure(api_key=api_key)

app = FastAPI()

# Allow local dev where frontend and backend are on different ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for dev; lock down in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_NAME = "gemini-2.5-flash"

def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract text from a PDF using PyPDF2. Returns concatenated text (may be short for scanned PDFs)."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp:
        tmp.write(pdf_bytes)
        tmp.flush()

        with open(tmp.name, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n"
    return text

def parse_script_with_gemini(text: str) -> dict:
    """Ask Gemini to convert script text into structured scene/line JSON."""
    model = genai.GenerativeModel(MODEL_NAME)

    prompt = f"""
Analyze this script and extract all the dialogue organized by scenes. For each line of dialogue, identify:
1. The scene it belongs to (scene number and brief description)
2. The character name who speaks it
3. The exact dialogue text

Return ONLY a JSON object in this format (no extra commentary):
{{
  "scenes": [
    {{
      "scene_number": "1",
      "scene_title": "Brief scene description",
      "lines": [
        {{"character": "CHARACTER_NAME", "line": "dialogue text here"}},
        {{"character": "CHARACTER_NAME", "line": "dialogue text here"}}
      ]
    }}
  ]
}}

Rules:
- Only include spoken dialogue (no stage directions).
- Character names should be consistent and uppercase if possible.

SCRIPT:
{text}
"""
    resp = model.generate_content(prompt)
    raw = (resp.text or "").strip()

    # Strip markdown fences if the model returns ```json ... ```
    cleaned = raw
    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()

    data = json.loads(cleaned)

    # Basic validation / sanity checks
    if "scenes" not in data or not isinstance(data["scenes"], list) or len(data["scenes"]) == 0:
        raise ValueError("No scenes found in parsed JSON.")

    for s in data["scenes"]:
        if "scene_number" not in s or "scene_title" not in s or "lines" not in s:
            raise ValueError("Scene missing required keys.")
        if not isinstance(s["lines"], list):
            raise ValueError("Scene lines must be a list.")
        for ln in s["lines"]:
            if "character" not in ln or "line" not in ln:
                raise ValueError("Line missing character or line.")

    return data

def extract_characters(script_data: dict) -> list[str]:
    chars = set()
    for scene in script_data.get("scenes", []):
        for line in scene.get("lines", []):
            c = (line.get("character") or "").strip()
            if c:
                chars.add(c)
    return sorted(chars)

@app.post("/api/parse-pdf")
async def parse_pdf(file: UploadFile = File(...)):
    pdf_bytes = await file.read()
    text = extract_pdf_text(pdf_bytes)

    extracted_len = len(text.strip())

    # Heuristic threshold: scanned PDFs often yield near-empty extraction
    if extracted_len < 500:
        return {
            "ok": False,
            "error_code": "LOW_TEXT",
            "message": (
                "We couldn’t extract enough text from this PDF (it may be scanned/image-based). "
                "Please upload a text-based PDF, a different version of the script, or run OCR first."
            ),
            "extracted_chars": extracted_len,
        }

    try:
        script_data = parse_script_with_gemini(text)
        characters = extract_characters(script_data)

        total_lines = sum(len(s.get("lines", [])) for s in script_data.get("scenes", []))
        if total_lines < 5:
            return {
                "ok": False,
                "error_code": "TOO_FEW_LINES",
                "message": (
                    "We parsed the PDF but found too little dialogue. "
                    "Please upload a clearer text-based script PDF."
                ),
                "total_lines": total_lines,
            }

        return {
            "ok": True,
            "script_data": script_data,
            "characters": characters,
            "total_lines": total_lines,
        }

    except Exception as e:
        return {
            "ok": False,
            "error_code": "PARSE_FAILED",
            "message": (
                "Parsing failed. Please upload a different version of the script. "
                f"(Error: {str(e)})"
            ),
        }
