from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import logging
import os

import extractor
import llm_client

# --------------------------------------------------
# Logging Configuration (Centralized)
# --------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --------------------------------------------------
# FastAPI App
# --------------------------------------------------
app = FastAPI(title="DocChat AI - Local Document Q&A")

# Static folder path
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# --------------------------------------------------
# Request Models
# --------------------------------------------------
class AskRequest(BaseModel):
    document_text: str
    question: str
    model: str = "llama3"


# --------------------------------------------------
# Routes
# --------------------------------------------------
@app.get("/")
async def read_index():
    """
    Serve the main frontend page.
    """
    index_path = os.path.join(STATIC_DIR, "index.html")
    return FileResponse(index_path)


@app.post("/api/extract")
async def extract_text_endpoint(file: UploadFile = File(...)):
    """
    Extract text from uploaded file (PDF or TXT).
    """
    try:
        content = await file.read()

        if not content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        text = extractor.extract_text(content, file.filename)

        logger.info(f"Extracted text from file: {file.filename}")

        return {
            "filename": file.filename,
            "text": text
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error during text extraction.")
        raise HTTPException(status_code=500, detail="Failed to extract document text.")


@app.post("/api/ask")
async def ask_llm_endpoint(request: AskRequest):
    """
    Ask a question to the local LLM using extracted document text.
    """
    try:
        if not request.document_text.strip():
            raise HTTPException(status_code=400, detail="No document text provided.")

        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty.")

        answer = llm_client.query_llm(
            request.document_text,
            request.question,
            request.model,
        )

        logger.info("LLM query completed successfully.")

        return {"answer": answer}

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error during LLM query.")
        raise HTTPException(status_code=500, detail="Failed to query local LLM.")


# --------------------------------------------------
# Local Development Entry Point
# --------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    logger.info("Starting DocChat AI server at http://localhost:8006")

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8006,
        reload=False,
    )