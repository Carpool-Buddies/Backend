# Google OAuth Setup

To enable real Google login (the buttons already work in code — they just need
credentials), follow these steps.

## 1. Create OAuth credentials

1. Go to <https://console.cloud.google.com>
2. Create a project (or select an existing one)
3. **APIs & Services → OAuth consent screen**
   - User type: **External**
   - Fill app name, support email, developer email — save
   - Add scopes: `openid`, `email`, `profile`
   - Add yourself as a **Test user** (while the app is in "Testing")
4. **APIs & Services → Credentials → Create Credentials → OAuth client ID**
   - Application type: **Web application**
   - Name: `CarpoolBuddies (local)`
   - **Authorized redirect URIs** — add exactly:
     ```
     http://localhost:8000/api/v1/auth/google/callback
     ```
   - Create → copy the **Client ID** and **Client Secret**

## 2. Put the keys in `.env`

In `Backend/api-server-fastapi/.env`:

```
GOOGLE_CLIENT_ID=xxxxxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=xxxxxxxx
FRONTEND_URL=http://localhost:3000
SECRET_KEY=<any long random string>
```

## 3. Restart the API

```
docker compose up -d            # Postgres + Redis
uvicorn app.main:app --reload   # or via docker
```

## 4. Test the flow

1. Open <http://localhost:3000/login>
2. Click **המשך עם Google**
3. You'll be sent to Google, then back to:
   - `/onboarding` on first login (confirm name + university)
   - `/dashboard` afterwards
4. The httpOnly `access_token` cookie is set automatically.

## How it works (code reference)

- `GET /api/v1/auth/google/login` → redirects to Google (Authlib)
- `GET /api/v1/auth/google/callback` → exchanges the code, upserts the user
  (`app/services/users.py`), detects university from the email domain
  (`app/core/universities.py`), sets JWT cookies, redirects to the frontend
- Adding more providers is a one-line registration in `app/services/oauth.py`

## Production notes

- Add your production callback URL to the Authorized redirect URIs too:
  `https://api.yourdomain.com/api/v1/auth/google/callback`
- Move the consent screen from "Testing" to "Published"
- Cookies become `Secure` automatically when `DEBUG=False`
