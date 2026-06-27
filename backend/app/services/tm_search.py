import os
import difflib
from typing import List, Dict, Tuple
from dotenv import load_dotenv
from .embedder import get_embedding

load_dotenv()

CHROMA_PATH = os.getenv("CHROMA_DB_PATH", "../data/chromadb")
CHROMA_AVAILABLE = False

try:
    import chromadb
    CHROMA_AVAILABLE = True
except ImportError:
    print("Warning: chromadb not found. Falling back to SQL + difflib similarity matching.")

class TMSearchService:
    def __init__(self):
        self.use_fallback = not CHROMA_AVAILABLE
        self.collection = None
        
        if CHROMA_AVAILABLE:
            try:
                # Ensure the path directory exists
                os.makedirs(os.path.dirname(CHROMA_PATH), exist_ok=True)
                self.client = chromadb.PersistentClient(path=CHROMA_PATH)
                self.collection = self.client.get_or_create_collection(
                    name="translation_memory",
                    metadata={"hnsw:space": "cosine"}
                )
            except Exception as e:
                print(f"Error initializing ChromaDB: {e}. Switching to SQL + difflib matching.")
                self.use_fallback = True

    def add_to_tm(self, source_text: str, target_text: str, source_lang: str, target_lang: str, entry_id: str):
        """
        Adds an approved translation to the memory index.
        """
        if self.use_fallback or not self.collection:
            # Sqlite fallback handles the DB persistence; we just pass here.
            return
            
        try:
            vector = get_embedding(source_text)
            self.collection.add(
                ids=[entry_id],
                embeddings=[vector],
                metadatas=[{
                    "source_text": source_text,
                    "target_text": target_text,
                    "source_lang": source_lang,
                    "target_lang": target_lang
                }],
                documents=[source_text]
            )
        except Exception as e:
            print(f"ChromaDB insert failed: {e}")

    def search_tm(self, db_session, source_text: str, source_lang: str, target_lang: str, threshold: float = 0.75) -> Tuple[str, str, float]:
        """
        Searches the TM index for matching segments.
        Classifies matches as exact (>=0.99), fuzzy (>=threshold), or new.
        """
        # If ChromaDB is unavailable or error-prone, fall back to SQL + difflib
        if self.use_fallback or not self.collection:
            return self._fallback_sql_search(db_session, source_text, source_lang, target_lang, threshold)
            
        try:
            vector = get_embedding(source_text)
            results = self.collection.query(
                query_embeddings=[vector],
                n_results=1,
                where={
                    "$and": [
                        {"source_lang": {"$eq": source_lang}},
                        {"target_lang": {"$eq": target_lang}}
                    ]
                }
            )
            
            if not results or not results["ids"] or len(results["ids"][0]) == 0:
                return "new", "", 0.0

            distance = results["distances"][0][0]
            similarity = 1.0 - distance
            metadata = results["metadatas"][0][0]
            matched_target = metadata["target_text"]

            if similarity >= 0.99:
                return "exact", matched_target, similarity
            elif similarity >= threshold:
                return "fuzzy", matched_target, similarity
            else:
                return "new", "", similarity
                
        except Exception as e:
            print(f"ChromaDB query failed: {e}. Falling back to SQL + difflib search.")
            return self._fallback_sql_search(db_session, source_text, source_lang, target_lang, threshold)

    def _fallback_sql_search(self, db, source_text: str, source_lang: str, target_lang: str, threshold: float) -> Tuple[str, str, float]:
        """
        SQL/Python alternative when vector database is not configured.
        Uses difflib to compare string similarity against all DB records for the language pair.
        """
        from ..models import TranslationMemoryEntry
        
        # Load entries for this language pair
        entries = db.query(TranslationMemoryEntry).filter(
            TranslationMemoryEntry.source_lang == source_lang,
            TranslationMemoryEntry.target_lang == target_lang
        ).all()
        
        best_match = None
        best_ratio = 0.0
        
        for entry in entries:
            # Use SequenceMatcher for ratio comparison
            ratio = difflib.SequenceMatcher(None, source_text.strip().lower(), entry.source_text.strip().lower()).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_match = entry
                
        if best_ratio >= 0.99 and best_match:
            return "exact", best_match.target_text, best_ratio
        elif best_ratio >= threshold and best_match:
            return "fuzzy", best_match.target_text, best_ratio
        else:
            return "new", "", best_ratio
