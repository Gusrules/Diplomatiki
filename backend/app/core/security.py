from passlib.context import CryptContext
from passlib.exc import UnknownHashError

# No bcrypt dependency -> works reliably on Windows/Python 3.12
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    try:
        return pwd_context.verify(password, password_hash)
    except UnknownHashError:
        # Handle malformed or invalid hashes in the database
        # Try simple comparison for plain-text or fallback hashes
        return password == password_hash
