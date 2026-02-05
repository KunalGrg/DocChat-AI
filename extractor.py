import pypdf
import io

def extract_text(file_bytes: bytes, filename: str) -> str:
    """
    Extract text content from uploaded bytes (PDF or Text).
    """
    filename = filename.lower()
    if filename.endswith(".pdf"):
        return _extract_from_pdf(file_bytes)
    else:
        # Assume text-based file
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            # Fallback for other encodings
            return file_bytes.decode("latin-1", errors="replace")

def _extract_from_pdf(file_bytes: bytes) -> str:
    try:
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""
