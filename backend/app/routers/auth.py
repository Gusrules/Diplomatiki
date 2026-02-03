import secrets
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.auth import LoginIn, LoginOut, MeOut
from app.core.security import verify_password

from app.models.student import Student
from app.models.teacher import Teacher
from app.models.session import Session as SessionModel

router = APIRouter(prefix="/auth", tags=["Auth"])

def _get_session(db: Session, authorization: str | None):
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.replace("Bearer ", "").strip()
    if not token:
        return None
    return db.query(SessionModel).filter(SessionModel.token == token).first()

@router.post("/login", response_model=LoginOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    role = payload.role.strip().lower()
    if role not in ("student", "teacher"):
        raise HTTPException(status_code=400, detail="role must be student or teacher")

    if role == "student":
        u = db.query(Student).filter(Student.email == payload.email).first()
    else:
        u = db.query(Teacher).filter(Teacher.email == payload.email).first()

    if not u:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(payload.password, u.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # create session token
    token = secrets.token_hex(32)

    s = SessionModel(token=token, user_id=u.id, role=role, name=u.name)
    db.add(s)
    db.commit()

    return LoginOut(user_id=u.id, role=role, name=u.name, token=token)

@router.get("/me", response_model=MeOut)
def me(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    s = _get_session(db, authorization)
    if not s:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return MeOut(user_id=s.user_id, role=s.role, name=s.name)

@router.post("/logout", response_model=dict)
def logout(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
):
    s = _get_session(db, authorization)
    if not s:
        return {"ok": True}
    db.delete(s)
    db.commit()
    return {"ok": True}
