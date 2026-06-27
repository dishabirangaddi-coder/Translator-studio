from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import Segment, AuditLog, Project
from ..schemas import SegmentResponse, SegmentApproveRequest
from ..services.learning_loop import LearningLoop

router = APIRouter(prefix="/review", tags=["review"])
learning_loop = LearningLoop()

@router.get("/project/{project_id}/segments", response_model=List[SegmentResponse])
def get_segments_for_review(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    return db.query(Segment).filter(
        Segment.project_id == project_id
    ).order_by(Segment.position).all()

@router.post("/segments/{segment_id}/approve")
def approve_segment(
    segment_id: int,
    request: SegmentApproveRequest,
    db: Session = Depends(get_db)
):
    segment = db.query(Segment).filter(Segment.id == segment_id).first()
    if not segment:
        raise HTTPException(status_code=404, detail="Segment not found")
        
    try:
        # Pass approval to continuous learning loop (adds to TM and logs audit)
        learning_loop.process_approval(
            db=db,
            segment_id=segment_id,
            approved_translation=request.approved_translation,
            reviewer_name=request.reviewer_name
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process approval: {str(e)}")
        
    return {"message": "Segment approved and saved to TM"}

@router.get("/project/{project_id}/audit-trail")
def get_audit_trail(project_id: int, db: Session = Depends(get_db)):
    segments = db.query(Segment).filter(Segment.project_id == project_id).all()
    segment_ids = [s.id for s in segments]
    
    logs = db.query(AuditLog).filter(
        AuditLog.segment_id.in_(segment_ids)
    ).order_by(AuditLog.timestamp.desc()).all()
    
    return logs
