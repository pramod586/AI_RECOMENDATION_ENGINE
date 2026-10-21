
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.database import get_db
from app.models import Document, DocumentChunk, User
from app.services.document_service import extract_text, split_text
from app.services.embedding_service import generate_document_embedding


router = APIRouter(
    prefix="/api/documents",
    tags=["Documents"],
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required",
        )

    original_name = Path(file.filename).name
    extension = Path(original_name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, DOCX, and TXT files are supported",
        )

    stored_name = f"{uuid4().hex}{extension}"
    file_path = UPLOAD_DIR / stored_name

    try:
        content = await file.read()

        if not content:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty",
            )

        # Save original file
        file_path.write_bytes(content)

        # Extract text
        extracted_text = extract_text(str(file_path))

        if not extracted_text.strip():
            raise HTTPException(
                status_code=400,
                detail="No readable text found in the document",
            )

        # Split extracted text into chunks
        chunks = split_text(extracted_text)

        # Save document information
        document = Document(
            user_id=current_user.id,
            filename=original_name,
            file_path=str(file_path),
            file_type=extension.lstrip("."),
            status="processed",
        )

        db.add(document)
        db.flush()

        # Generate embeddings and save document chunks
        for index, chunk in enumerate(chunks):

            # Generate Gemini embedding for each chunk
            embedding = generate_document_embedding(chunk)

            # Save chunk content and embedding in PostgreSQL
            document_chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=index,
                content=chunk,
                embedding=embedding,
            )

            db.add(document_chunk)

        # Commit document and all chunks together
        db.commit()
        db.refresh(document)

        return {
            "status": "success",
            "message": "Document uploaded, processed, and embedded successfully",
            "document_id": document.id,
            "filename": document.filename,
            "total_chunks": len(chunks),
            "embeddings_generated": len(chunks),
        }

    except HTTPException:
        db.rollback()
        file_path.unlink(missing_ok=True)
        raise

    except Exception as exc:
        db.rollback()
        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=500,
            detail=f"Document processing failed: {str(exc)}",
        )

    finally:
        await file.close()