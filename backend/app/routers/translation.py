from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Project, Segment, StyleProfile
from ..services.translator import TranslationService
from ..services.tm_search import TMSearchService
import os

router = APIRouter(prefix="/translation", tags=["translation"])
tm_service = TMSearchService()
translation_service = TranslationService()

def run_translation_pipeline(project_id: int, db: Session):
    """
    Background worker task to iterate through segments, search TM, and call translator.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return
        
    style_profile = db.query(StyleProfile).filter(StyleProfile.id == project.style_profile_id).first()
    
    segments = db.query(Segment).filter(Segment.project_id == project_id).order_by(Segment.position).all()
    
    for segment in segments:
        # 1. Search Translation Memory (TM) using RAG (passing the db session)
        match_type, matched_target, score = tm_service.search_tm(
            db_session=db,
            source_text=segment.source_text,
            source_lang=project.source_lang,
            target_lang=project.target_lang
        )
        
        segment.match_type = match_type
        segment.match_score = score
        
        if match_type == "exact":
            # Auto-fill exact matches
            segment.translated_text = matched_target
            segment.status = "pending_review"
        else:
            # Let LLM translate new & fuzzy segments (injecting glossary + style)
            try:
                result = translation_service.translate_segment(
                    db=db,
                    text=segment.source_text,
                    source_lang=project.source_lang,
                    target_lang=project.target_lang,
                    style_profile=style_profile
                )
                segment.translated_text = result["translated_text"]
                segment.back_translated_text = result["back_translated_text"]
                segment.confidence_score = result["confidence_score"]
                segment.status = "pending_review"
            except Exception as e:
                # Log error
                print(f"Failed to translate segment {segment.id}: {e}")
                
        db.commit()
        
    project.status = "in_review"
    db.commit()

@router.post("/{project_id}/translate")
def trigger_translation(project_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    project.status = "translating"
    db.commit()
    
    # Run pipeline asynchronously to prevent API timeout
    background_tasks.add_task(run_translation_pipeline, project_id, db)
    
    return {"message": "Translation pipeline started in background", "project_id": project_id}
