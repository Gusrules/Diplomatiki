import secrets
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.auth import LoginIn, LoginOut, MeOut
from app.core.security import verify_password

from app.models.student import Student
from app.models.teacher import Teacher
from app.models.session import Session as SessionModel

from app.core.deps import get_session
from app.schemas.auth import LoginIn, LoginOut, MeOut, RegisterStudentIn, RegisterStudentOut
from app.core.security import verify_password, hash_password
from app.core.security import verify_password, hash_password
from app.core.deps import get_session
from app.schemas.auth import ChangePasswordIn, ChangePasswordOut


router = APIRouter(prefix="/auth", tags=["Auth"])

bearer_scheme = HTTPBearer(auto_error=False)


@router.post("/register", response_model=RegisterStudentOut)
def register_student(payload: RegisterStudentIn, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    name = payload.name.strip()

    # check existing
    exists = db.query(Student).filter(Student.email == email).first()
    if exists and not getattr(exists, "deleted", False):
        raise HTTPException(status_code=400, detail="Email already registered")

    # If you have soft-delete and want to block reuse:
    if exists and getattr(exists, "deleted", False):
        raise HTTPException(status_code=400, detail="Email already registered (deleted account)")

    u = Student(
        name=name,
        email=email,
        password_hash=hash_password(payload.password),
        deleted=False,
    )
    db.add(u)
    db.commit()
    db.refresh(u)

    return RegisterStudentOut(user_id=u.id, role="student", name=u.name)

@router.post("/login", response_model=LoginOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()

    # 1️⃣ ψάξε πρώτα student
    u = db.query(Student).filter(Student.email == email).first()
    role = "student"

    # 2️⃣ αν δεν βρέθηκε, ψάξε teacher
    if not u:
        u = db.query(Teacher).filter(Teacher.email == email).first()
        role = "teacher"

    if not u:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(payload.password, u.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = secrets.token_hex(32)

    s = SessionModel(
        token=token,
        user_id=u.id,
        role=role,
        name=u.name
    )
    db.add(s)
    db.commit()

    return LoginOut(
        user_id=u.id,
        role=role,
        name=u.name,
        token=token
    )


@router.get("/me", response_model=MeOut)
def me(s: SessionModel = Depends(get_session)):
    return MeOut(user_id=s.user_id, role=s.role, name=s.name)

@router.post("/change-password", response_model=ChangePasswordOut)
def change_password(
    payload: ChangePasswordIn,
    s: SessionModel = Depends(get_session),
    db: Session = Depends(get_db),
):
    # Βρες user ανά role
    if s.role == "student":
        u = db.query(Student).filter(Student.id == s.user_id).first()
    else:
        u = db.query(Teacher).filter(Teacher.id == s.user_id).first()

    if not u:
        raise HTTPException(status_code=404, detail="User not found")

    # verify current
    if not verify_password(payload.current_password, u.password_hash):
        raise HTTPException(status_code=400, detail="Current password is wrong")

    new_pw = (payload.new_password or "").strip()
    if len(new_pw) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters")

    u.password_hash = hash_password(new_pw)
    db.add(u)
    db.commit()

    # Optional: σβήσε όλα τα sessions του ίδιου user ώστε να ξανακάνει login
    db.query(SessionModel).filter(SessionModel.user_id == s.user_id, SessionModel.role == s.role).delete()
    db.commit()

    return ChangePasswordOut(ok=True)

@router.post("/logout", response_model=dict)
def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    # logout is "best effort"
    if credentials is None or (credentials.scheme or "").lower() != "bearer":
        return {"ok": True}

    token = (credentials.credentials or "").strip()
    if not token:
        return {"ok": True}

    s = db.query(SessionModel).filter(SessionModel.token == token).first()
    if not s:
        return {"ok": True}

    db.delete(s)
    db.commit()
    return {"ok": True}

