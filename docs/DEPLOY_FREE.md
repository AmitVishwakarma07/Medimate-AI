# Deploy MediMate AI for free (Render + Neon + GitHub)

**Cost: Rs 0, no credit card needed** (free tiers can change - check each site's pricing page before you start).

| Piece | Service | Free-tier facts to know |
|---|---|---|
| Source code | GitHub | Free private repositories |
| App (site + API in one Docker container) | Render "Free" web service | Sleeps after 15 minutes without visitors; the first visit after that takes about a minute. Small CPU, so login can take a second or two. HTTPS address provided. |
| Database | Neon Postgres (Free) | 0.5 GB storage; suspends when idle and wakes automatically. **Do not use Render's own free database - it is deleted after 30 days.** |

Your address will look like `https://medimate-ai-xxxx.onrender.com`.

---
## Step 0 - Before you start
1. Make sure the project folder contains `Dockerfile`, `render.yaml`, `backend/`, `frontend/` and a `.gitignore`.
2. Inside `frontend/`, `package-lock.json` should exist (it is created by `npm install`). It must be committed.
3. Run the app and tests locally one more time (`pytest -v`) so you deploy something that works.

## Step 1 - Put the code on GitHub
Create an empty **private** repository named `medimate-ai` on github.com (no README), then in PowerShell:
```powershell
cd medimate-ai
git init
git add .
git status
```
**Read the `git status` list.** It must NOT contain `.env`, `venv`, `node_modules`, or any `.db` file. If it does, stop and
fix `.gitignore` first (committing secrets is the most common beginner mistake - if it happens, change the secret).
```powershell
git commit -m "MediMate AI"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/medimate-ai.git
git push -u origin main
```

## Step 2 - Create the free database on Neon
1. Sign up at neon.com (GitHub login is fine). Create a project named `medimate`; pick the region closest to you
   (for India, Singapore is usually the nearest).
2. On the project dashboard click **Connect** and copy the connection string. It looks like
   `postgresql://user:password@ep-something.neon.tech/neondb?sslmode=require`.
3. Keep it private - it is a password. Do not paste it into chat, GitHub, or screenshots.

## Step 3 - Deploy on Render
1. Sign up at render.com with GitHub. Allow it to access your `medimate-ai` repository.
2. Click **New -> Blueprint**, choose the repository. Render reads `render.yaml` and shows one free web service.
3. It will ask for two values:
   - `DATABASE_URL` = the Neon connection string from Step 2
   - `CONTACT_EMAIL` = an email address you really read (shown to users in the privacy notice)
4. Click **Apply** (or Deploy). The first build takes roughly 5-10 minutes (it builds the React site and installs Python
   packages). Watch the **Logs** tab.
5. When it says **Live**, open the `onrender.com` address.

(`SECRET_KEY` is generated for you. `ENV=production` makes the server refuse to start with unsafe settings.)

## Step 4 - Check that it really works and is safe
- `https://YOUR-ADDRESS/api/health` shows `{"status":"ok"}`.
- `https://YOUR-ADDRESS/docs` should show **Not Found** (API docs are hidden in production).
- Register with a made-up account, add a record, check the charts, ask the chatbot, create an appointment reminder.
- Open the browser's DevTools -> Application -> Cookies: the `mm_session` cookie must show **HttpOnly** and **Secure**.
- In Settings, try **Download all my data**, then **Delete my account** (use a throw-away account).
- Open the site on your phone.

## Step 5 - Updating later
Change code, then `git add . ; git commit -m "message" ; git push`. Render rebuilds and redeploys automatically.

## Step 6 - Keeping it healthy (free-tier habits)
- **Sleeping:** the first visit after idle is slow. Warn your users, or (optional) use a free uptime pinger such as
  UptimeRobot to request `/api/health` every 10-14 minutes. One always-awake free service uses about 720 of Render's
  750 free hours per month, so do not run other free services in the same workspace.
- **Backups:** Neon free keeps only a short history window. Regularly download a copy of your database with `pg_dump`
  (install PostgreSQL client tools, then `pg_dump "YOUR_NEON_URL" > backup.sql`) and store it somewhere safe. Users can
  also download their own data from Settings.
- **Watch limits:** Neon's dashboard shows storage and compute use. If a free limit is reached, the database pauses
  until the next monthly window or you upgrade - data is not deleted.
- **Logs:** Render -> your service -> **Logs**. Login failures and account deletions are logged without raw emails.

## Troubleshooting
| Symptom | Likely cause and fix |
|---|---|
| Build fails at `npm` | Make sure `frontend/package.json` and `package-lock.json` are committed; read the build log's first red line. |
| Service crashes: "Unsafe production configuration" | A setting is missing: `DATABASE_URL` must be the Neon Postgres string (not SQLite); `SECRET_KEY` must exist. The message names the problem. |
| "could not connect to server" / database errors | Wrong or incomplete `DATABASE_URL`. It must end with `?sslmode=require`. Copy it again from Neon. |
| Everyone gets "Too many login attempts" | The app sees all visitors as one address. In Render set `TRUSTED_PROXY_HOPS=2` and redeploy. |
| Login works but you are logged out immediately | You are on `http://` or a different address. Use the HTTPS `onrender.com` address (secure cookies need HTTPS). |
| Very slow first page | Normal on the free plan after sleeping (about a minute). |

## Before you let REAL people use it (please read)
Deploying is the easy part. For other people's health information you are responsible for how it is handled:
1. Tell users the truth: it is a small free-hosted project, not a medical service. Keep the "not a medical device" wording.
2. Set a real `CONTACT_EMAIL` and have the privacy notice (`frontend/src/components/PrivacyNotice.jsx`) reviewed by someone
   qualified. India's data-protection rules (DPDP Act and Rules, notified November 2025) require a clear notice, consent,
   user rights such as access and erasure, reasonable security safeguards, and breach reporting; most duties start
   applying on 13 May 2027. This project includes data download and account deletion, but it is not legal advice.
3. Start with a small group you know. There is **no email verification, no password reset by email, and no multi-factor
   login** yet, and sessions cannot be revoked before they expire.
4. Do not store anything you would not want exposed if the free database were breached; a professional security review is
   advisable before wider use.
5. Free tiers have no uptime guarantee. Do not rely on this for anything urgent or clinical.
