from sqlalchemy.orm import Session
from ..models import Segment, TranslationMemoryEntry, AuditLog
from .tm_search import TMSearchService

class LearningLoop:
    def __init__(self):
        self.tm_service = TMSearchService()

    def process_approval(self, db: Session, segment_id: int, approved_translation: str, reviewer_name: str = "Linguist"):
        """
        Triggered when a segment is approved or corrected.
        1. Logs audit trail.
        2. Adds to vector store (ChromaDB) and DB translation memory.
        3. Sets status to 'accepted'.
        """
        # Fetch segment from DB
        segment = db.query(Segment).filter(Segment.id == segment_id).first()
        if not segment:
            return
        
        project = segment.project
        previous_translation = segment.translated_text
        
        # 1. Update segment state
        segment.translated_text = approved_translation
        segment.status = "accepted"
        
        # 2. Add Audit Log
        audit = AuditLog(
            segment_id=segment.id,
            action="approve" if previous_translation == approved_translation else "edit",
            previous_translation=previous_translation,
            final_translation=approved_translation,
            user_name=reviewer_name
        )
        db.add(audit)
        
        # 3. Add to Translation Memory (if it isn't an exact match already)
        if segment.match_type != "exact":
            # Add to SQLite DB
            tm_entry = TranslationMemoryEntry(
                source_text=segment.source_text,
                target_text=approved_translation,
                source_lang=project.source_lang,
                target_lang=project.target_lang,
                approved_by=reviewer_name
            )
            db.add(tm_entry)
            db.flush() # Generate ID
            
            # Add to ChromaDB vector store
            self.tm_service.add_to_tm(
                source_text=segment.source_text,
                target_text=approved_translation,
                source_lang=project.source_lang,
                target_lang=project.target_lang,
                entry_id=str(tm_entry.id)
            )
            
        db.commit()
