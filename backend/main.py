from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from app.database import engine, Base
from app.routers import documents, translation, glossary, review

# Load environment variables
load_dotenv()

# Create SQLite/Postgres database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Translation Studio", version="1.0.0")

# Allow React frontend to talk to backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(documents.router)
app.include_router(translation.router)
app.include_router(glossary.router)
app.include_router(review.router)

# ✅ Test route — just to confirm backend is running
@app.get("/")
def root():
    return {
        "status": "✅ Translation Studio backend is running!",
        "groq_key_loaded": bool(os.getenv("GROQ_API_KEY")),
        "db_host": os.getenv("DB_HOST"),
    }

# ✅ Test Groq translation route
@app.get("/test-translation")
def test_translation():
    from groq import Groq
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "user", "content": "Translate to Spanish: Hello, how are you?"}
        ]
    )
    return {"translation": response.choices[0].message.content}