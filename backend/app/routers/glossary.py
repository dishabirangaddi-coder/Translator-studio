from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import GlossaryTerm
from ..schemas import GlossaryTermCreate, GlossaryTermResponse

router = APIRouter(prefix="/glossary", tags=["glossary"])

@router.post("", response_model=GlossaryTermResponse)
def create_glossary_term(term_in: GlossaryTermCreate, db: Session = Depends(get_db)):
    # Conflict Detection: check if term already exists for this language pair
    existing_term = db.query(GlossaryTerm).filter(
        GlossaryTerm.source_term == term_in.source_term,
        GlossaryTerm.source_lang == term_in.source_lang,
        GlossaryTerm.target_lang == term_in.target_lang
    ).first()
    
    if existing_term:
        if existing_term.target_term != term_in.target_term:
            raise HTTPException(
                status_code=400,
                detail=f"Conflict detected: The term '{term_in.source_term}' is already translated as '{existing_term.target_term}' for this language pair."
            )
        return existing_term
        
    term = GlossaryTerm(
        source_term=term_in.source_term,
        target_term=term_in.target_term,
        source_lang=term_in.source_lang,
        target_lang=term_in.target_lang,
        context_note=term_in.context_note
    )
    db.add(term)
    db.commit()
    db.refresh(term)
    return term

@router.get("", response_model=List[GlossaryTermResponse])
def get_glossary_terms(
    source_lang: Optional[str] = None,
    target_lang: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(GlossaryTerm)
    if source_lang:
        query = query.filter(GlossaryTerm.source_lang == source_lang)
    if target_lang:
        query = query.filter(GlossaryTerm.target_lang == target_lang)
    return query.all()

@router.delete("/{term_id}")
def delete_glossary_term(term_id: int, db: Session = Depends(get_db)):
    term = db.query(GlossaryTerm).filter(GlossaryTerm.id == term_id).first()
    if not term:
        raise HTTPException(status_code=404, detail="Term not found")
    db.delete(term)
    db.commit()
    return {"message": "Term deleted successfully"}
