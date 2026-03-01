# OneSpot Development Guide

Everything you need to run OneSpot locally for development.

---

## Prerequisites

- **Python 3.11+** (`python3 --version`)
- **Node.js 18+** (`node --version`)
- **npm 9+** (`npm --version`)

---

## Backend Setup

```bash
# From the project root

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Start the backend server with hot reload
uvicorn backend.main:app --reload --port 8000
```

The backend runs at `http://localhost:8000`. The `--reload` flag watches for file changes and restarts automatically.

---

## Frontend Setup

```bash
# From the project root

cd frontend

# Install Node dependencies
npm install

# Start the Vite dev server
npm run dev
```

The frontend dev server runs at `http://localhost:5173` and proxies API requests (`/api/*`) to the backend at `http://localhost:8000`.

---

## Running Both Together

Open two terminal windows (or use tmux/split panes):

| Terminal 1 (Backend) | Terminal 2 (Frontend) |
|----------------------|-----------------------|
| `source venv/bin/activate` | `cd frontend` |
| `uvicorn backend.main:app --reload --port 8000` | `npm run dev` |

During development, open `http://localhost:5173` in your browser. The Vite dev server handles hot module replacement (HMR) for instant feedback on frontend changes. API calls are proxied to the backend.

For production-like testing (serving the built frontend from FastAPI), build the frontend first:

```bash
cd frontend && npm run build && cd ..
uvicorn backend.main:app --port 8000
# Open http://localhost:8000
```

---

## Testing

### Backend tests

```bash
# From the project root, with venv activated
pytest -v
```

Tests are located in the `tests/` directory and use pytest.

### Frontend tests

```bash
cd frontend
npm test           # Single run
npm run test:watch # Watch mode
```

Frontend tests use Vitest and Testing Library.

---

## Mock WhatsApp Mode

By default, `WHATSAPP_MOCK=true` is set in `.env.example`. In mock mode:

- OTP codes are **logged to the server console** instead of being sent via WhatsApp.
- No Meta Business Account or API credentials are needed.
- All WhatsApp notification sends are logged but not actually dispatched.

Look for log output like:
```
[MOCK WHATSAPP] OTP for +447123456789: 847291
```

To test with real WhatsApp delivery, set `WHATSAPP_MOCK=false` and provide valid `WHATSAPP_API_TOKEN` and `WHATSAPP_PHONE_NUMBER_ID` values.

---

## Environment Variables

Copy the example environment file:

```bash
cp .env.example .env
```

The defaults in `.env.example` are configured for local development. See [docs/SETUP.md](SETUP.md) for a full reference of all environment variables.

---

## Inspecting State

All application data is stored in a single JSON file. To inspect it:

```bash
# Pretty-print the current state
cat backend/data/state.json | python -m json.tool

# Or use jq if installed
cat backend/data/state.json | jq .
```

To reset state to a clean slate, delete the file (it will be recreated on next server start):

```bash
rm backend/data/state.json
```

---

## Common Commands Cheat Sheet

| Task | Command |
|------|---------|
| Start backend (dev) | `uvicorn backend.main:app --reload --port 8000` |
| Start frontend (dev) | `cd frontend && npm run dev` |
| Run backend tests | `pytest -v` |
| Run frontend tests | `cd frontend && npm test` |
| Build frontend for production | `cd frontend && npm run build` |
| Pretty-print state | `cat backend/data/state.json \| python -m json.tool` |
| Reset state | `rm backend/data/state.json` |
| Generate a secret key | `openssl rand -hex 32` |
| Check Python version | `python3 --version` |
| Check Node version | `node --version` |

---

## Project Structure

```
OneSpot/
├── backend/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Environment variables and constants
│   ├── state.py             # JSON state manager (file locking, atomic writes)
│   ├── models.py            # Pydantic models
│   ├── dependencies.py      # FastAPI dependency injection
│   ├── routers/             # API route handlers
│   ├── services/            # Business logic (WhatsApp, OTP, credits, scheduler)
│   └── data/                # state.json and bays.json
├── frontend/
│   ├── src/                 # React source code
│   ├── index.html           # Entry HTML
│   ├── vite.config.js       # Vite configuration (includes API proxy)
│   ├── tailwind.config.js   # Tailwind CSS configuration
│   └── package.json         # Node dependencies and scripts
├── tests/                   # Backend tests (pytest)
├── docs/                    # Documentation
├── requirements.txt         # Python dependencies
├── railway.toml             # Railway deployment config
├── Procfile                 # Process start command
└── .env.example             # Environment variable template
```
