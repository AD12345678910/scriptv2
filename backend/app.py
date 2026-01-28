import os
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

# ✅ CORS so GitHub Pages can call Render
# You can tighten this later, but start permissive to unblock.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ad12345678910.github.io",
        "https://ad12345678910.github.io/scriptv2",
        "https://ad12345678910.github.io/scriptv2/",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/api/parse-pdf")
async def parse_pdf(file: UploadFile = File(...)):
    """
    NOTE:
    If your old version used Gemini/OpenAI/etc, put that parsing logic here.
    This stub makes the service run and returns a clear error until you add parsing.
    """
    return JSONResponse(
        status_code=501,
        content={"ok": False, "message": "PDF parsing not implemented on server yet. Upload JSON for now."},
    )
