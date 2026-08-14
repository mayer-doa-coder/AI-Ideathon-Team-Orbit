from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.rag.qa import answer_question
from app.schemas.rag import (
    RagAskRequest,
    RagAskResponse,
    RagSearchRequest,
    RagSearchResponse,
)
from app.tools.rag import retrieve_agri_knowledge

router = APIRouter(prefix="/api/rag", tags=["rag"])


@router.post("/search", response_model=RagSearchResponse)
def search(payload: RagSearchRequest, db: Session = Depends(get_db)):
    results = retrieve_agri_knowledge(
        db, payload.query, k=payload.k, crop=payload.crop, topic=payload.topic
    )
    return RagSearchResponse(query=payload.query, results=results)


@router.post("/ask", response_model=RagAskResponse)
def ask(payload: RagAskRequest, db: Session = Depends(get_db)):
    result = answer_question(db, payload.query, k=payload.k)
    return RagAskResponse(query=payload.query, **result)
