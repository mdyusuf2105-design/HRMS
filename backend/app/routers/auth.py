
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import TokenResponse, UserCreate, UserResponse
import jwt

router = APIRouter(prefix="/auth", tags=["Authentication"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@router.post("/register", response_model=UserResponse,
             status_code=status.HTTP_201_CREATED)
def register_user(data: UserCreate, db: Session = Depends(get_db)):
    # Public registration must never grant elevated roles.
    if data.role != "employee":
        raise HTTPException(
            status_code=403,
            detail="Only employees can self-register",
        )

    existing_user = db.query(User).filter(
        User.email == str(data.email).lower()
    ).first()

    if existing_user:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        full_name=data.full_name,
        email=str(data.email).lower(),
        hashed_password=hash_password(data.password),
        role="employee",
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login_user(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    email = form.username.lower()

    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")

    token = create_access_token(user.id, user.role)
    return TokenResponse(access_token=token)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_error = HTTPException(
        status_code=401,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        subject = payload.get("sub")
        if not subject:
            raise credentials_error
        user_id = int(subject)
    except (InvalidTokenError, ValueError, TypeError):
        raise credentials_error

    user = db.query(User).filter(User.id == user_id).first()

    if not user or not user.is_active:
        raise credentials_error

    return user


@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user


def require_roles(*roles: str):
    def role_checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user

    return role_checker
