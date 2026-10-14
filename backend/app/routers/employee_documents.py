from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.employee import Employee
from app.models.employee_document import EmployeeDocument
from app.models.user import User
from app.routers.auth import get_current_user, require_roles

router = APIRouter(prefix="/employees", tags=["Employee Documents"])

UPLOAD_DIR = (
    Path(__file__).resolve().parents[2]
    / "private_uploads"
    / "employee_documents"
)
MAX_FILE_SIZE = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}


def document_payload(document):
    return {
        "id": document.id,
        "employee_id": document.employee_id,
        "original_filename": document.original_filename,
        "content_type": document.content_type,
        "size_bytes": document.size_bytes,
        "uploaded_by_user_id": document.uploaded_by_user_id,
        "uploaded_at": document.uploaded_at,
    }


def get_employee_or_404(db, employee_id):
    employee = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


def can_access_documents(current_user, employee):
    return (
        current_user.role in {"admin", "hr"}
        or employee.user_id == current_user.id
    )


def valid_signature(extension, content):
    if extension == ".pdf":
        return content.startswith(b"%PDF-")
    if extension in {".jpg", ".jpeg"}:
        return content.startswith(b"\xff\xd8\xff")
    if extension == ".png":
        return content.startswith(b"\x89PNG\r\n\x1a\n")
    return False


@router.post(
    "/{employee_id}/documents",
    status_code=status.HTTP_201_CREATED,
)
async def upload_employee_document(
    employee_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("admin", "hr")),
):
    try:
        employee = get_employee_or_404(db, employee_id)
        original_filename = Path(file.filename or "").name.strip()
        extension = Path(original_filename).suffix.lower()

        if not original_filename or extension not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail="Only PDF, JPG, JPEG, and PNG files are allowed",
            )

        content = await file.read(MAX_FILE_SIZE + 1)

        if not content:
            raise HTTPException(status_code=400, detail="File is empty")

        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="Maximum file size is 5 MB",
            )

        if not valid_signature(extension, content):
            raise HTTPException(
                status_code=400,
                detail="File content does not match its extension",
            )

        content_types = {
            ".pdf": "application/pdf",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
        }

        stored_filename = f"{uuid4().hex}{extension}"
        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        destination = UPLOAD_DIR / stored_filename

        document = EmployeeDocument(
            employee_id=employee.id,
            uploaded_by_user_id=current_user.id,
            original_filename=original_filename[:255],
            stored_filename=stored_filename,
            content_type=content_types[extension],
            size_bytes=len(content),
        )

        try:
            destination.write_bytes(content)
            db.add(document)
            db.commit()
            db.refresh(document)
        except Exception:
            db.rollback()
            destination.unlink(missing_ok=True)
            raise

        return document_payload(document)
    finally:
        await file.close()


@router.get("/{employee_id}/documents")
def list_employee_documents(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    employee = get_employee_or_404(db, employee_id)

    if not can_access_documents(current_user, employee):
        raise HTTPException(status_code=403, detail="Access denied")

    documents = (
        db.query(EmployeeDocument)
        .filter(EmployeeDocument.employee_id == employee_id)
        .order_by(EmployeeDocument.uploaded_at.desc())
        .all()
    )
    return [document_payload(document) for document in documents]


@router.get("/{employee_id}/documents/{document_id}/download")
def download_employee_document(
    employee_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    employee = get_employee_or_404(db, employee_id)

    if not can_access_documents(current_user, employee):
        raise HTTPException(status_code=403, detail="Access denied")

    document = (
        db.query(EmployeeDocument)
        .filter(
            EmployeeDocument.id == document_id,
            EmployeeDocument.employee_id == employee_id,
        )
        .first()
    )

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    path = UPLOAD_DIR / document.stored_filename

    if not path.is_file():
        raise HTTPException(status_code=404, detail="Stored file not found")

    return FileResponse(
        path=path,
        media_type=document.content_type,
        filename=document.original_filename,
        content_disposition_type="attachment",
        headers={"X-Content-Type-Options": "nosniff"},
    )
