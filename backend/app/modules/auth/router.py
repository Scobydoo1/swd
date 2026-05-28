from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.auth.schemas import RegisterRequest, TokenResponse
from app.modules.auth.service import AuthService
from app.modules.users.schemas import UserOut
from app.shared.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    return AuthService(db).register(req)


@router.post("/login", response_model=TokenResponse)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    # OAuth2 form uses `username` field; we treat it as email.
    return AuthService(db).login(form.username, form.password)


@router.get("/me", response_model=UserOut)
def me(user=Depends(get_current_user)):
    return user
