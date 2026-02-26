from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.features.auth.application.usecases.get_current_user_use_case import GetCurrentUser
from app.features.auth.di.dependencies import get_current_user_use_case
from app.features.users.domain.entities.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/v1/login")


def get_authenticated_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    use_case: Annotated[GetCurrentUser, Depends(get_current_user_use_case)],
) -> User:
    try:
        return use_case.execute(token)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
