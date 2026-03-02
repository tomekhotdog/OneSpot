import os
from pathlib import Path


BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
PORT = int(os.getenv("PORT", "8000"))
OTP_SECRET = os.getenv("OTP_SECRET", "dev-secret-change-me")
SESSION_SECRET = os.getenv("SESSION_SECRET", "dev-session-secret-change-me")
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
EMAIL_MOCK = os.getenv("EMAIL_MOCK", "true").lower() == "true"
EMAIL_FROM = os.getenv("EMAIL_FROM", "OneSpot <onboarding@resend.dev>")
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
