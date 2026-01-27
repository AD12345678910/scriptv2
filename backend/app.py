import os
import tempfile
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# GitHub Pages origin (set on Render)
GITHUB_PAGES_ORIGIN = os.getenv("GITHUB_PAGES_ORIGIN", "")

origins = [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]

if GITHUB_PAGES_ORIGIN:
    origins.append(GITHUB_PAGES_ORIGIN)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/api/parse-pdf")
async def parse_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        return {"ok": False, "message": "Please upload a PDF"}

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(await file.read())

        # 🔴 TEMP DEMO OUTPUT — replace with your real parser later
        script_data = {
            "scenes": [
                {
                    "scene_number": "1",
                    "scene_title": "Example Scene",
                    "lines": [
                        {"character": "SELBY", "line": "This came from the backend."}
                    ],
                }
            ]
        }

        return {
            "ok": True,
            "script_data": script_data,
            "characters": ["SELBY"],
            "total_lines": 1,
        }

    except Exception as e:
        return {"ok": False, "message": str(e)}
