# Phase 1: Foundation — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build all shared infrastructure that Phase 2 parallel agents depend on.

**Architecture:** FastAPI backend serving a Vite-built React SPA. Single `state.json` for storage. Tailwind CSS for styling. All shared models, state management, config, and frontend shell built here.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic, filelock, React 18, Vite, Tailwind CSS, React Router v7, Vitest, pytest, httpx

---

### Task 1: Initialize Git & Project Root Files

**Files:**
- Create: `.gitignore`
- Create: `README.md`
- Create: `requirements.txt`
- Create: `railway.toml`
- Create: `Procfile`
- Create: `.env.example`

**Step 1: Create .gitignore**

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
venv/
.env

# Node
node_modules/
frontend/dist/

# State
backend/data/state.json
backend/data/state.backup.json

# IDE
.vscode/
.idea/
*.swp
```

**Step 2: Create requirements.txt**

```
fastapi>=0.115.0
uvicorn[standard]>=0.34.0
pydantic>=2.10.0
filelock>=3.16.0
apscheduler>=3.10.0
httpx>=0.28.0
python-multipart>=0.0.18
```

**Step 3: Create .env.example**

```
BASE_URL=http://localhost:8000
PORT=8000
OTP_SECRET=change-me-to-a-random-secret
SESSION_SECRET=change-me-to-a-random-secret
WHATSAPP_API_TOKEN=not-needed-in-dev
WHATSAPP_PHONE_NUMBER_ID=not-needed-in-dev
WHATSAPP_MOCK=true
ADMIN_API_KEY=dev-admin-key
STATE_FILE_PATH=./backend/data/state.json
```

**Step 4: Create railway.toml**

```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "cd frontend && npm install && npm run build && cd .. && uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3

[[volumes]]
mount = "/data"
```

**Step 5: Create Procfile**

```
web: uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

**Step 6: Create README.md**

```markdown
# OneSpot — Parking Space Sharing for One Maidenhead

A community tool for ~250 residents to share parking bays using a credit system.

> **Disclaimer:** OneSpot is an independent community tool built by a resident. Not affiliated with Get Living, Greystar, or One Maidenhead management.

## Quick Start

### Backend
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn backend.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Tests
```bash
pytest -v                    # Backend
cd frontend && npm test      # Frontend
```

## Docs
- [Setup Guide](docs/SETUP.md) — WhatsApp, Railway, env vars
- [Architecture](docs/ARCHITECTURE.md) — System overview
- [Development](docs/DEVELOPMENT.md) — Local dev workflow
- [Features](docs/features/) — Feature documentation
- [API Reference](docs/api/endpoints.md)
```

**Step 7: Commit**

```bash
git add .gitignore README.md requirements.txt railway.toml Procfile .env.example
git commit -m "feat: project root scaffolding"
```

---

### Task 2: Backend Skeleton — Config, Models, State Manager

**Files:**
- Create: `backend/__init__.py`
- Create: `backend/config.py`
- Create: `backend/models.py`
- Create: `backend/state.py`
- Create: `backend/routers/__init__.py`
- Create: `backend/services/__init__.py`
- Create: `backend/data/bays.json`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/test_models.py`
- Create: `tests/test_state.py`
- Create: `pytest.ini`

**Step 1: Create pytest.ini**

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
```

**Step 2: Create backend/__init__.py and subpackage inits**

Empty files for:
- `backend/__init__.py`
- `backend/routers/__init__.py`
- `backend/services/__init__.py`
- `tests/__init__.py`

**Step 3: Create backend/config.py**

```python
import os
from pathlib import Path


BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
PORT = int(os.getenv("PORT", "8000"))
OTP_SECRET = os.getenv("OTP_SECRET", "dev-secret-change-me")
SESSION_SECRET = os.getenv("SESSION_SECRET", "dev-session-secret-change-me")
WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_MOCK = os.getenv("WHATSAPP_MOCK", "true").lower() == "true"
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "dev-admin-key")
STATE_FILE_PATH = Path(os.getenv("STATE_FILE_PATH", "./backend/data/state.json"))

# Session
SESSION_EXPIRY_DAYS = 7

# OTP
OTP_EXPIRY_SECONDS = 300  # 5 minutes
OTP_MAX_ATTEMPTS = 3
OTP_RATE_LIMIT_WINDOW_SECONDS = 900  # 15 minutes
OTP_RATE_LIMIT_MAX_REQUESTS = 3

# Credits
INITIAL_CREDITS = 24

# Booking
MAX_ADVANCE_WEEKS = 3
```

**Step 4: Create backend/models.py**

```python
from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


def new_id() -> str:
    return str(uuid.uuid4())


def now_utc() -> datetime:
    return datetime.utcnow()


class AvailabilityPermission(str, Enum):
    ANYONE = "anyone"
    OWNERS_ONLY = "owners_only"


class User(BaseModel):
    id: str = Field(default_factory=new_id)
    name: str
    flat_number: str
    phone: str
    is_owner: bool = False
    bay_number: Optional[str] = None
    availability_permission: AvailabilityPermission = AvailabilityPermission.ANYONE
    credits: int = 24
    created_at: datetime = Field(default_factory=now_utc)
    last_login: datetime = Field(default_factory=now_utc)


class Session(BaseModel):
    user_id: str
    created_at: datetime = Field(default_factory=now_utc)
    expires_at: datetime


class OTPRequest(BaseModel):
    code: str
    created_at: datetime = Field(default_factory=now_utc)
    expires_at: datetime
    attempts: int = 0
    request_count_window: int = 1
    window_start: datetime = Field(default_factory=now_utc)


class DayHours(BaseModel):
    start: int  # 0-23
    end: int  # 1-24 (end > start)


class AvailabilityType(str, Enum):
    RECURRING = "recurring"
    ONE_OFF = "one_off"


class Availability(BaseModel):
    id: str = Field(default_factory=new_id)
    user_id: str
    bay_number: str
    type: AvailabilityType
    # Recurring fields
    pattern: Optional[dict[str, Optional[DayHours]]] = None  # day_name -> DayHours | None
    exclusions: list[str] = Field(default_factory=list)  # ISO date strings
    # One-off fields
    date: Optional[str] = None  # ISO date string
    start_hour: Optional[int] = None
    end_hour: Optional[int] = None
    # Common
    created_at: datetime = Field(default_factory=now_utc)
    paused: bool = False


class BookingStatus(str, Enum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class Booking(BaseModel):
    id: str = Field(default_factory=new_id)
    booker_user_id: str
    owner_user_id: str
    bay_number: str
    date: str  # ISO date string
    start_hour: int
    end_hour: int
    credits_charged: int
    status: BookingStatus = BookingStatus.CONFIRMED
    created_at: datetime = Field(default_factory=now_utc)
    modified_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    reminder_sent: bool = False


class CreditType(str, Enum):
    INITIAL_GRANT = "initial_grant"
    BOOKING_CHARGE = "booking_charge"
    BOOKING_EARNING = "booking_earning"
    CANCELLATION_REFUND = "cancellation_refund"
    CANCELLATION_DEBIT = "cancellation_debit"
    ADMIN_ADJUSTMENT = "admin_adjustment"


class CreditLedgerEntry(BaseModel):
    id: str = Field(default_factory=new_id)
    user_id: str
    amount: int
    type: CreditType
    related_booking_id: Optional[str] = None
    description: str
    timestamp: datetime = Field(default_factory=now_utc)


class WhatsAppLogEntry(BaseModel):
    id: str = Field(default_factory=new_id)
    recipient: str
    template: str
    params: dict = Field(default_factory=dict)
    status: str = "sent"
    timestamp: datetime = Field(default_factory=now_utc)


class AppState(BaseModel):
    users: dict[str, User] = Field(default_factory=dict)
    sessions: dict[str, Session] = Field(default_factory=dict)
    otp_requests: dict[str, OTPRequest] = Field(default_factory=dict)
    availability: dict[str, Availability] = Field(default_factory=dict)
    bookings: dict[str, Booking] = Field(default_factory=dict)
    credit_ledger: list[CreditLedgerEntry] = Field(default_factory=list)
    whatsapp_log: list[WhatsAppLogEntry] = Field(default_factory=list)
```

**Step 5: Create backend/state.py**

```python
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Callable

from filelock import FileLock

from backend.config import STATE_FILE_PATH
from backend.models import AppState


class StateManager:
    def __init__(self, path: Path | None = None):
        self.path = path or STATE_FILE_PATH
        self.lock_path = self.path.with_suffix(".lock")
        self._lock = FileLock(str(self.lock_path))

    def _ensure_dir(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def read(self) -> AppState:
        self._ensure_dir()
        if not self.path.exists():
            return AppState()
        with self._lock:
            data = json.loads(self.path.read_text())
        return AppState.model_validate(data)

    def write(self, state: AppState) -> None:
        self._ensure_dir()
        with self._lock:
            # Backup current state
            if self.path.exists():
                backup_path = self.path.with_name("state.backup.json")
                backup_path.write_text(self.path.read_text())
            # Atomic write via temp file
            fd, tmp_path = tempfile.mkstemp(
                dir=str(self.path.parent), suffix=".tmp"
            )
            try:
                with os.fdopen(fd, "w") as f:
                    json.dump(state.model_dump(mode="json"), f, indent=2, default=str)
                os.replace(tmp_path, str(self.path))
            except Exception:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                raise

    def update(self, fn: Callable[[AppState], AppState]) -> AppState:
        """Read state, apply fn, write back. Returns the new state."""
        self._ensure_dir()
        with self._lock:
            state = self._read_unlocked()
            new_state = fn(state)
            self._write_unlocked(new_state)
        return new_state

    def _read_unlocked(self) -> AppState:
        if not self.path.exists():
            return AppState()
        data = json.loads(self.path.read_text())
        return AppState.model_validate(data)

    def _write_unlocked(self, state: AppState) -> None:
        if self.path.exists():
            backup_path = self.path.with_name("state.backup.json")
            backup_path.write_text(self.path.read_text())
        fd, tmp_path = tempfile.mkstemp(
            dir=str(self.path.parent), suffix=".tmp"
        )
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(state.model_dump(mode="json"), f, indent=2, default=str)
            os.replace(tmp_path, str(self.path))
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise


# Singleton instance
state_manager = StateManager()
```

**Step 6: Write tests — test_models.py**

```python
from backend.models import (
    AppState,
    Availability,
    AvailabilityType,
    Booking,
    CreditLedgerEntry,
    CreditType,
    DayHours,
    User,
)


def test_user_defaults():
    user = User(name="Tomek", flat_number="42", phone="+447123456789")
    assert user.credits == 24
    assert user.is_owner is False
    assert user.bay_number is None
    assert user.id is not None


def test_user_owner():
    user = User(
        name="Tomek",
        flat_number="42",
        phone="+447123456789",
        is_owner=True,
        bay_number="B-07",
    )
    assert user.is_owner is True
    assert user.bay_number == "B-07"


def test_availability_recurring():
    avail = Availability(
        user_id="u1",
        bay_number="B-07",
        type=AvailabilityType.RECURRING,
        pattern={
            "monday": DayHours(start=8, end=18),
            "tuesday": None,
        },
    )
    assert avail.pattern["monday"].start == 8
    assert avail.pattern["tuesday"] is None
    assert avail.paused is False


def test_availability_one_off():
    avail = Availability(
        user_id="u1",
        bay_number="B-07",
        type=AvailabilityType.ONE_OFF,
        date="2026-03-15",
        start_hour=10,
        end_hour=16,
    )
    assert avail.date == "2026-03-15"
    assert avail.start_hour == 10


def test_booking_defaults():
    booking = Booking(
        booker_user_id="u2",
        owner_user_id="u1",
        bay_number="B-07",
        date="2026-03-05",
        start_hour=9,
        end_hour=17,
        credits_charged=8,
    )
    assert booking.status == "confirmed"
    assert booking.reminder_sent is False


def test_credit_ledger_entry():
    entry = CreditLedgerEntry(
        user_id="u1",
        amount=24,
        type=CreditType.INITIAL_GRANT,
        description="Welcome credits",
    )
    assert entry.amount == 24
    assert entry.related_booking_id is None


def test_app_state_empty():
    state = AppState()
    assert state.users == {}
    assert state.bookings == {}
    assert state.credit_ledger == []


def test_app_state_roundtrip():
    state = AppState()
    user = User(name="Tomek", flat_number="42", phone="+447123456789")
    state.users[user.id] = user
    data = state.model_dump(mode="json")
    restored = AppState.model_validate(data)
    assert restored.users[user.id].name == "Tomek"
```

**Step 7: Write tests — test_state.py**

```python
import json
from pathlib import Path

import pytest

from backend.models import AppState, User
from backend.state import StateManager


@pytest.fixture
def tmp_state(tmp_path):
    path = tmp_path / "state.json"
    return StateManager(path=path)


def test_read_empty(tmp_state):
    state = tmp_state.read()
    assert isinstance(state, AppState)
    assert state.users == {}


def test_write_and_read(tmp_state):
    state = AppState()
    user = User(name="Tomek", flat_number="42", phone="+447123456789")
    state.users[user.id] = user
    tmp_state.write(state)

    loaded = tmp_state.read()
    assert user.id in loaded.users
    assert loaded.users[user.id].name == "Tomek"


def test_write_creates_backup(tmp_state):
    state1 = AppState()
    user1 = User(name="First", flat_number="1", phone="+441111111111")
    state1.users[user1.id] = user1
    tmp_state.write(state1)

    state2 = AppState()
    user2 = User(name="Second", flat_number="2", phone="+442222222222")
    state2.users[user2.id] = user2
    tmp_state.write(state2)

    backup_path = tmp_state.path.with_name("state.backup.json")
    assert backup_path.exists()
    backup_data = json.loads(backup_path.read_text())
    backup_state = AppState.model_validate(backup_data)
    assert user1.id in backup_state.users


def test_update_atomic(tmp_state):
    state = AppState()
    user = User(name="Tomek", flat_number="42", phone="+447123456789")
    state.users[user.id] = user
    tmp_state.write(state)

    def add_credits(s: AppState) -> AppState:
        s.users[user.id].credits += 10
        return s

    new_state = tmp_state.update(add_credits)
    assert new_state.users[user.id].credits == 34

    loaded = tmp_state.read()
    assert loaded.users[user.id].credits == 34


def test_write_atomic_on_failure(tmp_state):
    state = AppState()
    tmp_state.write(state)

    def bad_fn(s: AppState) -> AppState:
        raise ValueError("intentional error")

    with pytest.raises(ValueError):
        tmp_state.update(bad_fn)

    # Original state should be intact
    loaded = tmp_state.read()
    assert loaded.users == {}
```

**Step 8: Run tests**

```bash
pytest tests/test_models.py tests/test_state.py -v
```

Expected: All PASS.

**Step 9: Commit**

```bash
git add backend/ tests/ pytest.ini
git commit -m "feat: backend skeleton — config, Pydantic models, state manager with tests"
```

---

### Task 3: Bay Configuration

**Files:**
- Create: `backend/data/bays.json`

**Step 1: Create placeholder bay layout**

Generate 150 bays: 75 on Level A (A-001 to A-075), 75 on Level B (B-001 to B-075). Arranged in a 15-column x 5-row grid per level. Each bay has: `id`, `number`, `level`, `row`, `col`.

```json
{
  "levels": [
    {
      "id": "A",
      "name": "Level A",
      "rows": 5,
      "cols": 15
    },
    {
      "id": "B",
      "name": "Level B",
      "rows": 5,
      "cols": 15
    }
  ],
  "bays": [
    {"id": "A-001", "number": "A-001", "level": "A", "row": 0, "col": 0},
    {"id": "A-002", "number": "A-002", "level": "A", "row": 0, "col": 1}
  ]
}
```

Use a script or manual generation to create all 150 entries. Pattern: `{level}-{NNN}` where NNN = (row * 15) + col + 1, zero-padded to 3 digits.

**Step 2: Commit**

```bash
git add backend/data/bays.json
git commit -m "feat: placeholder bay configuration — 150 bays across 2 levels"
```

---

### Task 4: FastAPI App Shell

**Files:**
- Create: `backend/main.py`
- Create: `backend/routers/auth.py` (stub)
- Create: `backend/routers/users.py` (stub)
- Create: `backend/routers/availability.py` (stub)
- Create: `backend/routers/bookings.py` (stub)
- Create: `backend/routers/map.py` (stub)
- Create: `backend/routers/admin.py` (stub)
- Create: `backend/dependencies.py`
- Create: `tests/test_main.py`

**Step 1: Create backend/dependencies.py**

```python
from fastapi import Cookie, HTTPException, Header, Request

from backend.models import User
from backend.state import state_manager
from backend import config


async def get_current_user(session_token: str = Cookie(None)) -> User:
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    state = state_manager.read()
    session = state.sessions.get(session_token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    from datetime import datetime
    if datetime.utcnow() > session.expires_at:
        raise HTTPException(status_code=401, detail="Session expired")
    user = state.users.get(session.user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


async def require_admin(x_admin_key: str = Header(None)) -> None:
    if x_admin_key != config.ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")
```

**Step 2: Create backend/main.py**

```python
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.routers import admin, auth, availability, bookings, map as map_router, users

app = FastAPI(title="OneSpot", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(availability.router, prefix="/api/availability", tags=["availability"])
app.include_router(bookings.router, prefix="/api/bookings", tags=["bookings"])
app.include_router(map_router.router, prefix="/api/map", tags=["map"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

# Serve frontend static files (production)
frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """SPA fallback — serve index.html for all non-API, non-asset routes."""
        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist / "index.html")
```

**Step 3: Create router stubs**

Each router file (`auth.py`, `users.py`, `availability.py`, `bookings.py`, `map.py`, `admin.py`) follows this pattern:

```python
from fastapi import APIRouter

router = APIRouter()
```

Endpoints will be implemented by Phase 2 agents. Just the empty router for now.

The `map.py` router also includes a static bay data endpoint:

```python
import json
from pathlib import Path
from fastapi import APIRouter

router = APIRouter()

BAYS_PATH = Path(__file__).parent.parent / "data" / "bays.json"

@router.get("/bays")
async def get_bays():
    data = json.loads(BAYS_PATH.read_text())
    return data
```

**Step 4: Write test_main.py**

```python
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_api_bays():
    response = client.get("/api/map/bays")
    assert response.status_code == 200
    data = response.json()
    assert "bays" in data
    assert "levels" in data
    assert len(data["bays"]) == 150


def test_unknown_api_route():
    response = client.get("/api/nonexistent")
    assert response.status_code in (404, 405)
```

**Step 5: Run tests**

```bash
pytest tests/ -v
```

Expected: All PASS.

**Step 6: Commit**

```bash
git add backend/ tests/
git commit -m "feat: FastAPI app shell with router stubs and dependencies"
```

---

### Task 5: Frontend Scaffolding

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.js`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/postcss.config.js`
- Create: `frontend/index.html`
- Create: `frontend/src/main.jsx`
- Create: `frontend/src/App.jsx`
- Create: `frontend/src/index.css`
- Create: `frontend/src/api.js`
- Create: `frontend/src/context/AuthContext.jsx`
- Create: `frontend/src/components/Layout.jsx`
- Create: `frontend/src/components/Disclaimer.jsx`
- Create: `frontend/src/styles/theme.js`
- Create: `frontend/src/pages/Home.jsx` (placeholder)
- Create: `frontend/src/pages/Login.jsx` (placeholder)
- Create: `frontend/src/pages/Signup.jsx` (placeholder)
- Create: `frontend/src/pages/MapView.jsx` (placeholder)
- Create: `frontend/src/pages/ListView.jsx` (placeholder)
- Create: `frontend/src/pages/BookingFlow.jsx` (placeholder)
- Create: `frontend/src/pages/MySpace.jsx` (placeholder)
- Create: `frontend/src/pages/MyBookings.jsx` (placeholder)
- Create: `frontend/src/pages/Profile.jsx` (placeholder)

**Step 1: Create package.json**

```json
{
  "name": "onespot-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "test": "vitest run",
    "test:watch": "vitest"
  },
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^7.0.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0",
    "tailwindcss": "^3.4.0",
    "vite": "^6.0.0",
    "vitest": "^2.1.0",
    "@testing-library/react": "^16.0.0",
    "@testing-library/jest-dom": "^6.6.0",
    "jsdom": "^25.0.0"
  }
}
```

**Step 2: Create vite.config.js**

```javascript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test-setup.js',
  },
})
```

**Step 3: Create tailwind.config.js**

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#5BA4D9',
          light: '#E8F2FA',
          dark: '#2E7AB8',
        },
        accent: {
          green: '#4CAF82',
          'green-light': '#E8F5EC',
          amber: '#E8A838',
          red: '#E8645A',
        },
        text: {
          primary: '#1A1A1A',
          secondary: '#6B6B6B',
        },
        bg: {
          page: '#F7F9FB',
          card: '#FFFFFF',
        },
        border: '#E2E8F0',
      },
      fontFamily: {
        sans: ['"DM Sans"', '"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        body: '14px',
        emphasis: '16px',
        'title-section': '20px',
        'title-page': '28px',
        hero: '40px',
      },
      borderRadius: {
        card: '12px',
        button: '8px',
        pill: '20px',
      },
      maxWidth: {
        content: '480px',
      },
    },
  },
  plugins: [],
}
```

**Step 4: Create postcss.config.js**

```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

**Step 5: Create index.html**

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap" rel="stylesheet" />
    <title>OneSpot — Parking Space Sharing</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

**Step 6: Create src/index.css**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  @apply bg-bg-page text-text-primary font-sans text-body;
  -webkit-font-smoothing: antialiased;
}
```

**Step 7: Create src/test-setup.js**

```javascript
import '@testing-library/jest-dom'
```

**Step 8: Create src/styles/theme.js**

```javascript
// Design tokens exported for JS usage (e.g. inline styles, charting)
// Primary styling uses Tailwind classes — use these only when CSS classes aren't practical.

export const colors = {
  primary: '#5BA4D9',
  primaryLight: '#E8F2FA',
  primaryDark: '#2E7AB8',
  accentGreen: '#4CAF82',
  accentGreenLight: '#E8F5EC',
  accentAmber: '#E8A838',
  accentRed: '#E8645A',
  textPrimary: '#1A1A1A',
  textSecondary: '#6B6B6B',
  bgPage: '#F7F9FB',
  bgCard: '#FFFFFF',
  border: '#E2E8F0',
}

// Bay status -> colour mapping for the parking map
export const bayStatusColors = {
  available: colors.primary,
  own: colors.accentGreen,
  unavailable: '#9CA3AF',    // grey
  booked: colors.accentAmber,
  restricted: '#D1D5DB',     // light grey / muted
}
```

**Step 9: Create src/api.js**

```javascript
const BASE = '/api'

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  })

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    const error = new Error(body.detail || `Request failed: ${res.status}`)
    error.status = res.status
    error.body = body
    throw error
  }

  if (res.status === 204) return null
  return res.json()
}

export const api = {
  auth: {
    requestOTP: (phone) => request('/auth/request-otp', { method: 'POST', body: JSON.stringify({ phone }) }),
    verifyOTP: (phone, code) => request('/auth/verify-otp', { method: 'POST', body: JSON.stringify({ phone, code }) }),
    logout: () => request('/auth/logout', { method: 'POST' }),
  },
  users: {
    register: (data) => request('/users/register', { method: 'POST', body: JSON.stringify(data) }),
    me: () => request('/users/me'),
    update: (data) => request('/users/me', { method: 'PATCH', body: JSON.stringify(data) }),
    credits: () => request('/users/me/credits'),
  },
  availability: {
    mine: () => request('/availability/mine'),
    setRecurring: (data) => request('/availability/recurring', { method: 'POST', body: JSON.stringify(data) }),
    addOneOff: (data) => request('/availability/one-off', { method: 'POST', body: JSON.stringify(data) }),
    remove: (id) => request(`/availability/${id}`, { method: 'DELETE' }),
    togglePause: (id) => request(`/availability/${id}/pause`, { method: 'PATCH' }),
    addExclusion: (date) => request('/availability/recurring/exclude', { method: 'POST', body: JSON.stringify({ date }) }),
    removeExclusion: (date) => request(`/availability/recurring/exclude/${date}`, { method: 'DELETE' }),
  },
  map: {
    bays: () => request('/map/bays'),
    status: (date, start, end) => request(`/map/status?date=${date}&start=${start}&end=${end}`),
  },
  browse: {
    available: (date, start, end) => request(`/browse/available?date=${date}&start=${start}&end=${end}`),
  },
  bookings: {
    create: (data) => request('/bookings', { method: 'POST', body: JSON.stringify(data) }),
    mine: () => request('/bookings/mine'),
    extend: (id, hours) => request(`/bookings/${id}/extend`, { method: 'PATCH', body: JSON.stringify({ hours }) }),
    reduce: (id, hours) => request(`/bookings/${id}/reduce`, { method: 'PATCH', body: JSON.stringify({ hours }) }),
    cancel: (id) => request(`/bookings/${id}`, { method: 'DELETE' }),
  },
}
```

**Step 10: Create src/context/AuthContext.jsx**

```jsx
import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { api } from '../api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  const fetchUser = useCallback(async () => {
    try {
      const data = await api.users.me()
      setUser(data)
    } catch {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchUser()
  }, [fetchUser])

  const logout = async () => {
    try {
      await api.auth.logout()
    } finally {
      setUser(null)
    }
  }

  return (
    <AuthContext.Provider value={{ user, loading, setUser, fetchUser, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
```

**Step 11: Create src/components/Disclaimer.jsx**

```jsx
export default function Disclaimer() {
  return (
    <p className="text-xs text-text-secondary leading-relaxed">
      OneSpot is an independent community tool built by a resident to help neighbours
      share parking spaces. It is not affiliated with, endorsed by, or operated by
      Get Living, Greystar, or One Maidenhead management. Use at your own discretion.
    </p>
  )
}
```

**Step 12: Create src/components/Layout.jsx**

```jsx
import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import Disclaimer from './Disclaimer'

const navItems = [
  { to: '/', label: 'Home', icon: '🏠' },
  { to: '/map', label: 'Map', icon: '🗺️' },
]

const ownerNav = { to: '/my-space', label: 'My Space', icon: '🅿️' }
const nonOwnerNav = { to: '/browse', label: 'Browse', icon: '🔍' }

export default function Layout() {
  const { user } = useAuth()

  const items = [
    ...navItems,
    user?.is_owner ? ownerNav : nonOwnerNav,
    { to: '/profile', label: 'Profile', icon: '👤' },
  ]

  return (
    <div className="min-h-screen bg-bg-page flex flex-col">
      <main className="flex-1 w-full max-w-content mx-auto px-4 pb-20 pt-4">
        <Outlet />
      </main>

      <nav className="fixed bottom-0 inset-x-0 bg-bg-card border-t border-border">
        <div className="max-w-content mx-auto flex justify-around py-2">
          {items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex flex-col items-center gap-0.5 px-3 py-1 text-xs transition-colors ${
                  isActive ? 'text-primary font-semibold' : 'text-text-secondary'
                }`
              }
            >
              <span className="text-lg">{item.icon}</span>
              <span>{item.label}</span>
            </NavLink>
          ))}
        </div>
      </nav>

      <footer className="fixed bottom-16 inset-x-0 px-4 py-2 hidden">
        <Disclaimer />
      </footer>
    </div>
  )
}
```

**Step 13: Create page placeholders**

Each page file (`Home.jsx`, `Login.jsx`, `Signup.jsx`, `MapView.jsx`, `ListView.jsx`, `BookingFlow.jsx`, `MySpace.jsx`, `MyBookings.jsx`, `Profile.jsx`) follows this pattern:

```jsx
export default function PageName() {
  return (
    <div>
      <h1 className="text-title-page font-bold">Page Name</h1>
      <p className="text-text-secondary mt-2">Coming soon.</p>
    </div>
  )
}
```

**Step 14: Create src/App.jsx**

```jsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Layout from './components/Layout'
import Home from './pages/Home'
import Login from './pages/Login'
import Signup from './pages/Signup'
import MapView from './pages/MapView'
import ListView from './pages/ListView'
import BookingFlow from './pages/BookingFlow'
import MySpace from './pages/MySpace'
import MyBookings from './pages/MyBookings'
import Profile from './pages/Profile'

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="p-8 text-center text-text-secondary">Loading...</div>
  if (!user) return <Navigate to="/login" replace />
  return children
}

function PublicRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="p-8 text-center text-text-secondary">Loading...</div>
  if (user) return <Navigate to="/" replace />
  return children
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<PublicRoute><Login /></PublicRoute>} />
          <Route path="/signup" element={<PublicRoute><Signup /></PublicRoute>} />
          <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
            <Route index element={<Home />} />
            <Route path="map" element={<MapView />} />
            <Route path="browse" element={<ListView />} />
            <Route path="book/:bayId" element={<BookingFlow />} />
            <Route path="my-space" element={<MySpace />} />
            <Route path="my-bookings" element={<MyBookings />} />
            <Route path="profile" element={<Profile />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
```

**Step 15: Create src/main.jsx**

```jsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'
import './index.css'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>
)
```

**Step 16: Install dependencies & verify build**

```bash
cd frontend && npm install && npm run build
```

Expected: Build succeeds, `frontend/dist/` created.

**Step 17: Commit**

```bash
git add frontend/
git commit -m "feat: frontend scaffolding — Vite, React, Tailwind, router, auth context, API client"
```

---

### Task 6: Documentation

**Files:**
- Create: `docs/SETUP.md`
- Create: `docs/ARCHITECTURE.md`
- Create: `docs/DEVELOPMENT.md`
- Create: `docs/api/endpoints.md`
- Create: `docs/features/auth.md` (stub)
- Create: `docs/features/availability.md` (stub)
- Create: `docs/features/booking.md` (stub)
- Create: `docs/features/map.md` (stub)
- Create: `docs/features/admin.md` (stub)

**Step 1: Create docs/SETUP.md**

Full manual setup guide covering WhatsApp Business API (step-by-step with screenshots description), Railway, environment variables, and optional domain. Content as described in the design doc Section 1 (Manual Setup Steps).

**Step 2: Create docs/ARCHITECTURE.md**

System overview: how backend serves frontend, state.json flow, auth cookie flow, credit system overview, WhatsApp mock/real toggle. Diagram of request flow.

**Step 3: Create docs/DEVELOPMENT.md**

Local development workflow: how to start backend, frontend, run tests, use mock WhatsApp, check state.json manually.

**Step 4: Create docs/api/endpoints.md**

Full API reference copied from spec Section 11, with request/response examples for each endpoint.

**Step 5: Create feature doc stubs**

Each `docs/features/*.md` gets a header and "To be filled by implementing agent" note. These will be completed by Phase 2 agents.

**Step 6: Commit**

```bash
git add docs/
git commit -m "docs: setup guide, architecture, development workflow, API reference, feature stubs"
```

---

### Task 7: Verify Everything Works Together

**Step 1: Start backend**

```bash
source venv/bin/activate
uvicorn backend.main:app --reload
```

Verify: `http://localhost:8000/api/map/bays` returns bay JSON.

**Step 2: Start frontend**

```bash
cd frontend && npm run dev
```

Verify: `http://localhost:5173` loads the React app, shows Login page (since no session).

**Step 3: Run all tests**

```bash
pytest -v
cd frontend && npm test
```

Expected: All pass.

**Step 4: Commit any fixes, tag phase 1 complete**

```bash
git tag phase-1-complete
```
