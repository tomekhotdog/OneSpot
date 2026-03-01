from datetime import datetime
from fastapi import Cookie, HTTPException, Header

from backend import config
from backend.models import User
from backend.state import state_manager


async def get_current_user(session_token: str = Cookie(None)) -> User:
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    state = state_manager.read()
    session = state.sessions.get(session_token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    if datetime.utcnow() > session.expires_at:
        raise HTTPException(status_code=401, detail="Session expired")
    user = state.users.get(session.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def require_admin(x_admin_key: str = Header(None)) -> None:
    if x_admin_key != config.ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")
