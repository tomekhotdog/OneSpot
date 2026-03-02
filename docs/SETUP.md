# OneSpot Setup Guide

This guide covers everything needed to deploy OneSpot to production on Railway with Resend email integration.

---

## 1. Resend Email API Setup

OneSpot uses the Resend API to send OTP codes and booking notifications via email.

### 1.1 Create a Resend Account

1. Go to [resend.com](https://resend.com) and sign up.
2. Complete email verification for your account.

### 1.2 Add and Verify a Domain

1. In the Resend dashboard, go to **Domains**.
2. Click **Add Domain** and enter your sending domain (e.g. `onespot-maidenhead.com`).
3. Resend will provide DNS records (SPF, DKIM, DMARC) to add to your domain.
4. Add the DNS records at your domain registrar and click **Verify**.
5. Verification typically takes a few minutes to a few hours.

### 1.3 Create an API Key

1. In the Resend dashboard, go to **API Keys**.
2. Click **Create API Key**.
3. Give it a name (e.g. "OneSpot Production") and select **Sending access** for your verified domain.
4. Copy the generated key -- this is your `RESEND_API_KEY`.

### 1.4 Cost

The Resend free tier includes:
- **3,000 emails per month**
- **100 emails per day**

This is more than sufficient for a ~250-resident community. No credit card required for the free tier.

---

## 2. Railway Setup

### 2.1 Create the Project

1. Sign up at [railway.com](https://railway.com) (GitHub login recommended).
2. Click **New Project** -> **Deploy from GitHub repo**.
3. Select the OneSpot repository.
4. Railway will detect the project and begin setup.

### 2.2 Add a Persistent Volume

The application stores all state in a JSON file. This file must persist across deploys:

1. In your Railway service, go to **Settings** -> **Volumes**.
2. Click **Add Volume**.
3. Set the mount path to `/data`.
4. Railway will provision persistent storage that survives redeploys.

Update `STATE_FILE_PATH` to `/data/state.json` in your environment variables (see below).

### 2.3 Set Environment Variables

In your Railway service, go to **Variables** and set all required environment variables (see the reference table in Section 3 below).

### 2.4 Deploy

Once variables are set, trigger a deploy. Railway will:
1. Install Python dependencies from `requirements.txt`.
2. Build the frontend (`cd frontend && npm install && npm run build`).
3. Start the server (`uvicorn backend.main:app --host 0.0.0.0 --port $PORT`).

---

## 3. Environment Variables Reference

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `BASE_URL` | Public URL of the deployed app (used in email links) | Yes (production) | `http://localhost:8000` |
| `PORT` | Port the server listens on | No | `8000` |
| `OTP_SECRET` | Random secret used for HMAC-based OTP generation. Generate with `openssl rand -hex 32`. | Yes | `dev-secret-change-me` |
| `SESSION_SECRET` | Random secret used for session cookie signing. Generate with `openssl rand -hex 32`. | Yes | `dev-session-secret-change-me` |
| `RESEND_API_KEY` | Resend API key for sending emails | Yes (production) | `""` |
| `EMAIL_FROM` | Sender email address (must match verified Resend domain) | No | `OneSpot <noreply@onespot-maidenhead.com>` |
| `EMAIL_MOCK` | When `true`, OTPs are logged to the console instead of sent via email | No | `true` |
| `ADMIN_API_KEY` | Static API key for admin endpoints. Generate with `openssl rand -hex 32`. | Yes | `dev-admin-key` |
| `STATE_FILE_PATH` | Path to the state.json file. Use `/data/state.json` on Railway (persistent volume). | No | `./backend/data/state.json` |

**Generating secrets:**
```bash
# Generate a secure random key
openssl rand -hex 32
```

---

## 4. Optional: Custom Domain

To use a custom domain (e.g. `onespot-maidenhead.com`) instead of Railway's default subdomain:

1. **Register the domain** with any registrar (Cloudflare, Namecheap, etc.).
2. In Railway, go to your service -> **Settings** -> **Networking** -> **Custom Domain**.
3. Enter your domain name.
4. Railway will provide a **CNAME target** (e.g. `your-service.up.railway.app`).
5. In your DNS registrar, add a **CNAME record** pointing your domain to the Railway target.
6. Wait for DNS propagation (usually 5-30 minutes).
7. Update the `BASE_URL` environment variable to `https://onespot-maidenhead.com`.
8. Railway handles SSL certificates automatically.
