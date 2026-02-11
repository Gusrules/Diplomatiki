from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.session import Session as SessionModel

bearer_scheme = HTTPBearer(auto_error=False)

def get_session(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> SessionModel:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Swagger/clients should send: Authorization: Bearer <token>
    if (credentials.scheme or "").lower() != "bearer":
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = (credentials.credentials or "").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    s = db.query(SessionModel).filter(SessionModel.token == token).first()
    if not s:
        raise HTTPException(status_code=401, detail="Not authenticated")

    return s


def require_teacher(s: SessionModel = Depends(get_session)) -> SessionModel:
    if s.role != "teacher":
        raise HTTPException(status_code=403, detail="Teacher only")
    return s
