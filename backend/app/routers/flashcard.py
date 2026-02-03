import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.resource import Resource as ResourceModel
from app.schemas.flashcard import FlashcardSetOut, FlashcardItem

router = APIRouter(prefix="/flashcards", tags=["Flashcards"])


@router.get("/module/{module_id}", response_model=list[FlashcardSetOut])
def get_flashcards_for_module(module_id: int, db: Session = Depends(get_db)):
    sets = (
        db.query(ResourceModel)
        .filter(ResourceModel.deleted == False)  # noqa
        .filter(ResourceModel.module_id == module_id)
        .filter(ResourceModel.type == "flashcard")
        .order_by(ResourceModel.id.desc())
        .all()
    )

    out = []
    for s in sets:
        if not s.content:
            continue

        try:
            payload = json.loads(s.content)
        except Exception:
            continue

        cards_raw = payload.get("flashcards", [])
        cards = []
        for c in cards_raw:
            if isinstance(c, dict) and c.get("front") and c.get("back"):
                cards.append(FlashcardItem(front=str(c["front"]), back=str(c["back"])))

        out.append(
            FlashcardSetOut(
                resource_id=s.id,
                module_id=s.module_id,
                title=s.title,
                flashcards=cards,
            )
        )

    return out
