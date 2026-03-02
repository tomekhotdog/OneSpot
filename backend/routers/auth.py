"""Authentication endpoints: OTP request/verify and logout."""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Response, Cookie
from pydantic import BaseModel

from backend.config import SESSION_EXPIRY_DAYS
from backend.models import Session
from backend.services.otp import OTPError, generate_otp, verify_otp
from backend.state import state_manager

router = APIRouter()


class RequestOTPBody(BaseModel):
    email: str


class VerifyOTPBody(BaseModel):
    email: str
    code: str


@router.post("/request-otp")
async def request_otp(body: RequestOTPBody):
    try:
        generate_otp(body.email, state_manager=state_manager)
    except OTPError as exc:
        raise HTTPException(status_code=429, detail=str(exc))
    return {"expires_in": 300}


@router.post("/verify-otp")
async def verify_otp_endpoint(body: VerifyOTPBody, response: Response):
    try:
        valid = verify_otp(body.email, body.code, state_manager=state_manager)
    except OTPError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    if not valid:
        raise HTTPException(status_code=400, detail="Invalid code. Please try again.")

    # OTP verified — check if user exists
    state = state_manager.read()
    existing_user = None
    for user in state.users.values():
        if user.email == body.email:
            existing_user = user
            break

    if existing_user is None:
        return {"is_new_user": True}

    # Existing user — create session
    token = secrets.token_urlsafe()
    now = datetime.utcnow()
    session = Session(
        user_id=existing_user.id,
        created_at=now,
        expires_at=now + timedelta(days=SESSION_EXPIRY_DAYS),
    )

    def _store_session(s):
        s.sessions[token] = session
        # Update last_login
        if existing_user.id in s.users:
            s.users[existing_user.id].last_login = now
        return s

    state_manager.update(_store_session)

    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=SESSION_EXPIRY_DAYS * 24 * 3600,
    )

    return {
        "is_new_user": False,
        "user": existing_user.model_dump(mode="json"),
    }


@router.post("/logout")
async def logout(response: Response, session_token: str = Cookie(None)):
    if session_token:
        def _remove_session(s):
            s.sessions.pop(session_token, None)
            return s

        state_manager.update(_remove_session)

    response.delete_cookie(key="session_token")
    return {"ok": True}
