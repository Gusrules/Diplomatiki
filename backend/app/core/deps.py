from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.session import Session as SessionModel

def get_session(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> SessionModel:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.replace("Bearer ", "").strip()
    s = db.query(SessionModel).filter(SessionModel.token == token).first()
    if not s:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return s

def require_teacher(s: SessionModel = Depends(get_session)) -> SessionModel:
    if s.role != "teacher":
        raise HTTPException(status_code=403, detail="Teacher only")
    return s
