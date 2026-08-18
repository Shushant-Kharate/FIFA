from fastapi import APIRouter, Depends, HTTPException

from auth import (
    CurrentUser, authenticate, create_access_token, get_current_user
)
from schemas import AuthUserSchema, LoginRequest, LoginResponse


router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest):
    user = authenticate(body.username, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return LoginResponse(
        access_token=create_access_token(user),
        user=AuthUserSchema(username=user.username, role=user.role, room_id=user.room_id),
    )


@router.get("/me", response_model=AuthUserSchema)
def me(user: CurrentUser = Depends(get_current_user)):
    return AuthUserSchema(username=user.username, role=user.role, room_id=user.room_id)
