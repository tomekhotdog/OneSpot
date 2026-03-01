# OneSpot Setup Guide

This guide covers everything needed to deploy OneSpot to production on Railway with WhatsApp Business API integration.

---

## 1. WhatsApp Business API Setup

OneSpot uses the Meta Cloud API (free tier) to send OTP codes and booking notifications via WhatsApp.

### 1.1 Create a Meta Business Account

1. Go to [business.facebook.com](https://business.facebook.com) and sign up or log in.
2. Complete business verification if prompted (not strictly required for testing, but needed for production message volumes).

### 1.2 Create a Developer App

1. Go to [developers.facebook.com](https://developers.facebook.com) and log in with your Meta account.
2. Click **Create App**.
3. Select **Business** as the app type.
4. Give it a name (e.g. "OneSpot") and select your Meta Business Account.
5. Click **Create App**.

### 1.3 Add the WhatsApp Product

1. In your app dashboard, click **Add Products** in the left sidebar.
2. Find **WhatsApp** and click **Set Up**.
3. You will be given a **test phone number** and a **temporary API token** (valid 24 hours).
4. Note the **Phone Number ID** -- you will need this for the `WHATSAPP_PHONE_NUMBER_ID` environment variable.
5. The temporary token can be used for initial testing.

### 1.4 Create a Permanent API Token

Temporary tokens expire after 24 hours. For production, create a system user:

1. Go to [business.facebook.com](https://business.facebook.com) -> **Business Settings**.
2. Navigate to **Users** -> **System Users**.
3. Click **Add** and create a system user (e.g. "OneSpot Bot") with **Admin** role.
4. Click **Generate New Token** for this system user.
5. Select your WhatsApp app and grant the `whatsapp_business_messaging` and `whatsapp_business_management` permissions.
6. Copy the generated token -- this is your permanent `WHATSAPP_API_TOKEN`.

### 1.5 Register a Dedicated Phone Number

For production, register a real phone number instead of using the test number:

1. In the WhatsApp product settings, go to **Phone Numbers**.
2. Click **Add Phone Number**.
3. Enter a phone number you control (this will be the number users see messages from).
4. Complete the verification process (Meta will send a code via SMS or voice call).
5. Update `WHATSAPP_PHONE_NUMBER_ID` with the new phone number's ID.

### 1.6 Submit Message Templates

WhatsApp requires pre-approved templates for outbound messages. Submit the following five templates under **WhatsApp** -> **Message Templates** in your app dashboard:

#### `otp_verification` (Authentication category -- auto-approved)
- **Category:** Authentication
- **Body:** `Your OneSpot verification code is: {{1}}. It expires in 5 minutes.`

#### `booking_confirmed_booker` (Utility category)
- **Category:** Utility
- **Body:** `Booking confirmed! You've booked bay {{1}} (Level {{2}}) on {{3}} from {{4}} to {{5}}. That's {{6}} credits. The bay owner is {{7}} (Flat {{8}}). If you need to reach them: {{9}}. Manage your booking at {{10}}`

#### `booking_confirmed_owner` (Utility category)
- **Category:** Utility
- **Body:** `Your bay {{1}} has been booked by {{2}} (Flat {{3}}) on {{4}} from {{5}} to {{6}}. You've earned {{7}} credits. If you need to reach them: {{8}}. Please ensure your bay is clear.`

#### `booking_ending_reminder` (Utility category)
- **Category:** Utility
- **Body:** `Reminder: Your booking for bay {{1}} ends at {{2}} today. Please ensure you've vacated the space by then.`

#### `booking_cancelled` (Utility category)
- **Category:** Utility
- **Body:** `Booking cancelled: Bay {{1}} on {{2}} from {{3}} to {{4}} has been cancelled by {{5}}. Credits have been adjusted.`

**Approval timeline:** Authentication templates are auto-approved. Utility templates typically take 1-2 business days.

### 1.7 Cost

The WhatsApp Business API free tier includes:
- **1,000 service conversations per month** (booking notifications, reminders)
- **Unlimited authentication conversations per month** (OTP messages)

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
| `BASE_URL` | Public URL of the deployed app (used in WhatsApp message links) | Yes (production) | `http://localhost:8000` |
| `PORT` | Port the server listens on | No | `8000` |
| `OTP_SECRET` | Random secret used for HMAC-based OTP generation. Generate with `openssl rand -hex 32`. | Yes | `dev-secret-change-me` |
| `SESSION_SECRET` | Random secret used for session cookie signing. Generate with `openssl rand -hex 32`. | Yes | `dev-session-secret-change-me` |
| `WHATSAPP_API_TOKEN` | Meta Cloud API permanent access token (from system user) | Yes (production) | `""` |
| `WHATSAPP_PHONE_NUMBER_ID` | WhatsApp Business phone number ID from Meta dashboard | Yes (production) | `""` |
| `WHATSAPP_MOCK` | When `true`, OTPs are logged to the console instead of sent via WhatsApp | No | `true` |
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
