from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ad12345678910.github.io",   # your GitHub Pages domain
        "http://localhost:5500",             # optional for local testing
        "http://127.0.0.1:5500",             # optional
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
