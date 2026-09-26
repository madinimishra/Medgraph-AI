from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import FileResponse
import shutil
import os
import uuid
import mimetypes

from app.core.config import settings
from app.core.dependencies import get_current_user
from app.services.document_service import DocumentService
from app.vectorstore.chroma_manager import ChromaManager

router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    deidentify: bool = Form(False),
    current_user=Depends(get_current_user)
):

    document_id = str(uuid.uuid4())

    # Each document gets its own folder, keyed by its document_id, so two
    # uploads with the same original filename never collide and the file
    # can always be found again later from its document_id alone.
    document_dir = os.path.join(settings.UPLOAD_DIR, document_id)
    os.makedirs(document_dir, exist_ok=True)

    file_path = os.path.join(document_dir, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    result = DocumentService.process_document(
        file_path, document_id=document_id, deidentify=deidentify
    )

    return {
        "filename": file.filename,
        **result
    }


@router.get("/")
def list_documents(
    current_user=Depends(get_current_user)
):
    """All previously uploaded documents (one entry per document, not
    per chunk), newest first - backs the Documents page's list view."""

    return ChromaManager.list_documents()


@router.get("/{document_id}/file")
def get_document_file(
    document_id: str,
    current_user=Depends(get_current_user)
):
    """Serves the original uploaded file so the frontend can view or
    download it. Requires authentication like every other document
    route - the frontend fetches this with its bearer token and turns
    the response into a blob URL rather than linking to it directly."""

    metadata = ChromaManager.get_document(document_id)

    if metadata is None:
        raise HTTPException(status_code=404, detail="Document not found")

    filename = metadata["filename"]
    file_path = os.path.join(settings.UPLOAD_DIR, document_id, filename)

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Original file is no longer available")

    media_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

    return FileResponse(
        file_path,
        media_type=media_type,
        filename=filename,
        content_disposition_type="inline"
    )
