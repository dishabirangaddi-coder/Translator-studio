import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Project, Segment
from ..schemas import ProjectResponse
from ..services.parser import DocumentParser

router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = "../data/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", response_model=ProjectResponse)
def upload_document(
    name: str,
    source_lang: str,
    target_lang: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # 1. Save uploaded file locally
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # 2. Create Project in DB
    project = Project(
        name=name,
        source_lang=source_lang,
        target_lang=target_lang,
        status="uploaded"
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # 3. Parse segments
    try:
        extracted_segments = DocumentParser.parse_document(file_path)
        
        # Save parsed segments to database
        for seg in extracted_segments:
            db_segment = Segment(
                project_id=project.id,
                position=seg["position"],
                segment_type=seg["type"],
                source_text=seg["text"],
                match_score=0.0,
                status="pending"
            )
            db.add(db_segment)
        
        db.commit()
    except Exception as e:
        # Rollback project if parsing fails
        db.delete(project)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to parse document: {str(e)}")

    return project
