"""Routes d'authentification."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from database import get_session
from dependencies import get_current_user
from models import User
from schemas import LoginRequest, TokenResponse, UserResponse
from security import create_access_token, verify_password

router = APIRouter(tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, session: Session = Depends(get_session)) -> TokenResponse:
    """Vérifie les identifiants et retourne un token JWT."""
    email = body.email.strip().lower()
    user = session.exec(select(User).where(User.email == email)).first()

    # Même message que l'email soit inconnu ou le mot de passe faux :
    # on ne révèle pas à un attaquant quels emails existent en base.
    if user is None or not verify_password(body.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect.",
        )

    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Retourne l'utilisateur connecté (permet au frontend de vérifier son token)."""
    return UserResponse(id=current_user.id, email=current_user.email)
