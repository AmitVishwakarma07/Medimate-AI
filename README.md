# MediMate AI - Smart Healthcare Assistant with Personal Health Dashboard

> **Status: hardened for real-world use (Stage 4A of 3 stages - deployment files come next).** Originally an educational mini-project. MediMate AI does **not** diagnose diseases, prescribe medicines, or replace a
> qualified healthcare professional. It uses user-entered or clearly labelled sample data only. It is **not**
> production-ready and makes **no** claim of compliance with medical privacy regulations.

## 1. Abstract
MediMate AI is a responsive web application that combines a personal health-record tracker, trend charts, a general
health-education chatbot, rule-based wellness suggestions, and a demo appointment manager. A React frontend talks to a
Python FastAPI backend that stores data in SQLite. The chatbot works fully offline with a transparent rule-based
fallback and can optionally use an external LLM, only with the user's explicit consent and without ever sending health
records. The project shows how a small full-stack system can be built with safety, privacy and simplicity in mind.

## 2. Problem Statement
People often track health numbers (heart rate, sleep, water intake) in scattered notes or apps, find it hard to see
trends, and search the internet for health information of mixed quality. There is a need for a single, simple tool to
record measurements, view them visually, and read safe, general educational information, while making it very clear
that it is not a substitute for professional care.

## 3. Objectives
1. Let users securely register, log in, and keep their own health records.
2. Visualise measurements over time with charts that update when records change.
3. Provide a chatbot for general health education with built-in safety rules (emergencies, medicines).
4. Offer gentle, explainable wellness suggestions based on user-chosen goals and logged data.
5. Provide a demo appointment manager (clearly not connected to real hospitals).
6. Follow privacy-by-design: minimal data, password hashing, consent before any external AI use.

## 4. Existing System vs Proposed System
| | Existing (typical) | Proposed (MediMate AI) |
|---|---|---|
| Record keeping | Paper notes, phone notes, spreadsheets | One place with validation, filters, edit/delete, CSV export |
| Trends | Manual graphs, or none | Automatic charts from saved records |
| Health information | General web search, mixed reliability | Chatbot with emergency and medicine safeguards and clear disclaimers |
| Advice | Generic articles | Explained suggestions ("why you see this") tied to chosen goals |
| Privacy | Data often sent to third parties | Local SQLite; external AI is optional, opt-in, question text only |

## 5. Technology Stack and Why
| Layer | Technology | Reason |
|---|---|---|
| Frontend | React + Vite (JavaScript) | Component-based UI, very fast dev server, beginner friendly |
| Styling | Plain responsive CSS | No extra build setup; easy to read and explain |
| Icons / charts | Lucide React, Recharts | Free, React-native libraries; Recharts gives responsive line/bar charts |
| Backend | Python FastAPI | Simple, fast, automatic validation and interactive API docs at `/docs` |
| Validation | Pydantic | Declares allowed input shapes and rejects bad data with clear errors |
| Database | SQLite via SQLAlchemy | Zero-install file database; SQLAlchemy protects against SQL injection and keeps code readable |
| Passwords / login | bcrypt, JWT (PyJWT) | bcrypt is a slow, salted hash; JWT is a signed token proving who is logged in |
| AI | Optional OpenAI-compatible LLM + rule-based fallback | Works free and offline; LLM optional, configured only through backend env vars |
| API calls | Browser Fetch API | Built into browsers; no extra library |
| Version control | Git | Standard history and collaboration |

## 6. System Architecture
```
 Browser (React + Vite, http://localhost:5173)
   pages -> services/api.js (fetch + Bearer token)
        |   /api/*  (Vite dev proxy)
        v
 FastAPI backend (http://127.0.0.1:8000)
   routers (auth, health_records, appointments, chatbot, recommendations)
     -> auth.py (bcrypt + JWT, "who is this user?")
     -> schemas.py (Pydantic validation)
     -> services/ (ai_service.py, recommendation_service.py)
     -> models.py + database.py (SQLAlchemy)
        v
 SQLite file (medimate.db)            (optional) external LLM API <- question text only, with consent
```
**Request flow example (add a record):** the form calls `api.createRecord()` -> `POST /api/health-records` with the
token -> FastAPI checks the token (`get_current_user`) -> Pydantic validates the body -> a `HealthRecord` row is saved
with the logged-in user's id -> JSON is returned -> the page reloads its data and the charts redraw.

## 7. Database Schema (SQLite)
**users**: `id` PK, `name`, `email` (unique), `password_hash` (bcrypt), `created_at`, `goals` (comma-separated keys),
`activity_level`, `has_restrictions` (bool), `ai_consent` (bool)

**health_records**: `id` PK, `user_id` FK -> users, `record_type`, `value`, `value2` (diastolic for blood pressure),
`unit`, `recorded_date`, `notes`, `is_sample` (bool, true only for demo sample rows), `created_at`

**appointments**: `id` PK, `user_id` FK -> users, `title`, `provider`, `appt_date`, `appt_time` ("HH:MM"), `notes`,
`status` (scheduled / completed / cancelled), `created_at`

**recommendation_progress**: `id` PK, `user_id` FK -> users, `rec_key`, `completed` (bool); unique (`user_id`, `rec_key`)

Relationships: one user has many health records, appointments, and recommendation-progress rows.

## 8. Implemented Features
- Registration, login, logout; passwords hashed with bcrypt; protected endpoints; demo-auth limitations explained in the UI.
- Dashboard: welcome, total entries, latest heart rate / blood pressure / water / sleep, recent records, upcoming
  appointments, wellness cards, heart-rate chart, quick-add form. Sample data is labelled **SAMPLE**.
- Health records: add, view, edit, delete; filters by type and date range; empty states; CSV export of own records;
  optional demo-mode sample data (loadable and removable). Types: heart rate, blood pressure, sleep, water, weight, activity.
- Trends: heart rate, blood pressure (systolic and diastolic), sleep, water charts with a time-range filter; they use
  saved records and carry an "informational, not a diagnosis" note.
- Chatbot: suggested questions, timestamps, typing indicator, disclaimer; emergency-keyword detection; refuses medicine
  and dosage advice; rule-based topics (headache, fever, cough/cold, stomach upset, sleep, hydration, blood pressure,
  heart rate, stress, exercise, diet, when to seek help); optional external LLM with consent.
- Recommendations: goal- and data-based, with a "why", mark-as-done, asks for more info when data is insufficient,
  and suppresses diet/exercise tips if the user flags restrictions.
- Appointments: create, view, edit, cancel, delete; date/time validation; clearly marked demo only.
- Settings: profile, goals, activity level, restrictions flag, external-AI consent.
- Backend: structured JSON errors, suitable status codes, CORS for local development, interactive docs at `/docs`.

## 9. Installation and Running (Windows PowerShell)
**Prerequisites:** Python 3.10+ and Node.js 18+ (LTS) installed.

**Backend** (terminal 1):
```powershell
cd medimate-ai\backend
python -m venv venv
venv\Scripts\Activate.ps1          # if blocked: Set-ExecutionPolicy -Scope Process Bypass
pip install -r requirements-dev.txt     # includes the test tools
copy .env.example .env             # then edit SECRET_KEY (see below)
uvicorn app.main:app --reload
```
Open http://127.0.0.1:8000/docs for the API docs and http://127.0.0.1:8000/api/health (returns `{"status":"ok"}`) to check it is running.
Generate a secret for `SECRET_KEY` in `.env` with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`.

**Frontend** (terminal 2):
```powershell
cd medimate-ai\frontend
npm install
npm run dev
```
Open http://localhost:5173. Register an account using made-up details, then try **Health Records -> Load sample data**.

**Optional external AI:** in `backend\.env` set `LLM_API_KEY`, `LLM_MODEL` and (if needed) `LLM_BASE_URL` for any
OpenAI-compatible service, restart the backend, and tick the consent box in the app's Settings. Without a key the
rule-based helper is used. The key stays on the backend and is never sent to the browser.

## 10. API Documentation
Interactive docs: `/docs` (development only; hidden when `ENV=production`). The browser app authenticates with an httpOnly session cookie plus the header `X-Requested-With: MediMate` on state-changing requests (CSRF defence). API clients may use `Authorization: Bearer <token>` instead. All endpoints except register, login, logout and `/api/health` need a session.
Errors use one shape: `{"error": {"status": 422, "message": "...", "details": [...]}}`.

| Method | Path | Purpose | Success |
|---|---|---|---|
| POST | /api/auth/register | Create account, returns token | 201 |
| POST | /api/auth/login | Log in, returns token | 200 |
| POST | /api/auth/logout | End the session (clears the cookie) | 204 |
| GET / PUT | /api/profile | Read / update profile, goals, consent | 200 |
| GET | /api/health-records | List own records (`record_type`, `start_date`, `end_date`, `limit`) | 200 |
| POST | /api/health-records | Create record | 201 |
| PUT | /api/health-records/{id} | Update own record | 200 |
| DELETE | /api/health-records/{id} | Delete own record | 204 |
| GET | /api/health-records/summary | Total count and latest of each type | 200 |
| GET | /api/health-records/export.csv | Download own records as CSV | 200 |
| POST / DELETE | /api/health-records/demo-data | Load / remove labelled sample data (demo mode) | 201 / 200 |
| GET / POST | /api/appointments | List / create demo appointments | 200 / 201 |
| PUT / DELETE | /api/appointments/{id} | Edit (including cancel) / delete | 200 / 204 |
| POST | /api/chat | Ask the chatbot `{ "message": "..." }` | 200 |
| GET | /api/chat/status | Chatbot mode (rule-based or external AI) | 200 |
| GET | /api/recommendations | Personalised suggestions plus "needs more info" | 200 |
| PUT | /api/recommendations/{key} | Mark done / not done `{ "completed": true }` | 200 |
| GET | /api/account/export | Download all my data as JSON | 200 |
| PUT | /api/account/password | Change password (needs current password) | 200 |
| DELETE | /api/account | Delete my account and ALL my data (needs password) | 204 |
| GET | /api/health | Server check | 200 |

Common error codes: 401 not logged in or bad credentials, 403 missing security header or wrong password confirmation, 429 too many attempts (rate limit), 404 record not found (also used for other users' records),
409 email already registered, 422 invalid input.

## 11. Testing
Automated backend tests are in `backend/tests/test_api.py` (pytest, in-memory database, never touches real data).
```powershell
cd medimate-ai\backend
venv\Scripts\Activate.ps1
pytest -v
```
They cover: registration and login, authentication failures, record create/read/update/delete, invalid inputs, filters,
users being unable to read/edit/delete each other's records, CSV export and formula escaping, demo data, appointment
validation and isolation, the chatbot working without an API key, emergency and medicine safeguards, and
recommendation logic. **Record your own pytest result in your report** (for example the final "N passed" line).

The frontend has no automated tests. Use this manual checklist: register, log in, load sample data, add / edit /
delete a record, check dashboard cards and charts update, filter records, export CSV, ask the chatbot each suggested
question plus "I have chest pain", complete a recommendation, create / edit / cancel an appointment, change settings,
log out and confirm pages are no longer reachable.

## 12. Limitations
- Authentication is hardened but still basic: httpOnly session cookie, rate limiting and account lock-out, password rules - but **no email verification, no password reset by email, no multi-factor login, and sessions cannot be revoked before they expire**. Rate limits are in memory (one server process only).
- SQLite is a single local file; there are no database migrations or backups.
- The rule-based chatbot only knows a fixed set of topics and uses keyword matching; it is not a language model and can
  misunderstand questions. Emergency detection is also keyword-based and cannot catch every phrasing.
- Recommendation thresholds only choose which gentle suggestion to show; they are not medical judgements.
- Appointments are not connected to real hospitals or doctors.
- Not reviewed for medical-privacy compliance and not suitable for real patient data.
- A rate-limit lock-out can be triggered against someone's account by repeated wrong guesses (it lasts about 15 minutes).
- Security measures here are not a substitute for a professional security review or legal review of the privacy notice before real users sign up.
- No automated frontend tests; the frontend is designed for modern desktop and mobile browsers but was not tested on every device.

## 13. Future Enhancements (NOT implemented)
Email verification and password reset; multi-factor login; session revocation; shared (Redis) rate limiting; stored consent records; HTTPS deployment (see the deployment stage); PostgreSQL
with migrations; reminders and notifications; import from wearable devices; multi-language support; richer
recommendation logic reviewed by clinicians; a retrieval-based chatbot using vetted sources; accessibility audit;
automated frontend and end-to-end tests; Docker packaging.

## 14. Safety and Privacy Considerations
- No diagnosis, prescriptions, doses, or advice to stop treatment. Emergency keywords trigger a message to contact local
  emergency services; medicine questions get a polite refusal.
- The fallback chatbot says it is rule-based, not a real LLM, and never invents references.
- External AI is off unless a server key exists **and** the user opts in. Only the typed question is sent, never health
  records. Emergency and medicine questions are always handled locally.
- Sessions use an httpOnly, SameSite=Lax cookie (Secure in production) with a CSRF header check; login and sign-up are rate limited; passwords need 10+ characters and are checked against common ones.
- Users can download all their data, change their password, and delete their account and all data from Settings. A plain-language privacy notice is shown at sign-up and in Settings (the operator must fill in the contact line and have it reviewed).
- The server refuses to start in production mode without a strong `SECRET_KEY` and HTTPS cookies; API docs are hidden in production; unexpected errors return a generic message while details go to the server log.
- Passwords are stored only as bcrypt hashes. Secrets live in `.env` (ignored by Git); `.env.example` has placeholders only.
- Every record query is filtered by the logged-in user's id; other users' ids return 404.
- CSV export escapes spreadsheet formulas. Minimal data is collected (name, email, optional goals).
- Sample data is created only on request in demo mode and is labelled SAMPLE. Use made-up data only for testing.

## 15. Free deployment
A complete step-by-step guide is in `docs/DEPLOY_FREE.md` (GitHub + Render free web service + Neon free Postgres). The repository includes a `Dockerfile` that builds the React site and serves it together with the API from one container, and a `render.yaml` blueprint.

## 16. Project Structure
```
medimate-ai/
  backend/app/ (main.py, config.py, database.py, models.py, schemas.py, auth.py, routers/, services/)
  backend/tests/test_api.py   backend/requirements.txt   backend/.env.example
  frontend/src/ (App.jsx, main.jsx, index.css, pages/, components/, services/, hooks/)
  docs/REPORT_OUTLINE_AND_VIVA.md   docs/DEPLOY_FREE.md
  Dockerfile   render.yaml   .dockerignore
  README.md   .gitignore
```
