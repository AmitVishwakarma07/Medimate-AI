# MediMate AI - Mini-Project Report Outline and Viva Questions

## Part A: Report outline (suggested chapters)
**Front matter:** title page, certificate, declaration, acknowledgement, abstract, table of contents, list of figures and tables.

1. **Introduction** - background, motivation, scope, and the statement that the project is educational and not a medical device.
2. **Problem statement and objectives** - see README sections 2 and 3.
3. **Literature / existing systems survey** - health-tracking apps, symptom-checker websites, general chatbots; their
   strengths and weaknesses (privacy, reliability, safety claims). Cite only real sources you have actually read.
4. **Proposed system** - features, user roles, safety rules.
5. **System analysis** - functional and non-functional requirements; hardware/software requirements.
6. **System design** - architecture diagram, data-flow diagram, use-case diagram, ER diagram and table schema,
   API design, UI wireframes.
7. **Implementation** - modules: authentication, health records, charts, chatbot, recommendations, appointments, settings;
   short code excerpts with explanation; screenshots of every page.
8. **Testing** - test cases table (input, expected output, actual output, pass/fail), pytest summary, manual checklist.
   Report only results you actually obtained.
9. **Security, privacy and ethics** - password hashing, token auth, per-user data isolation, consent for external AI,
   disclaimers, why real patient data must not be used.
10. **Results and discussion** - what works, screenshots, observations.
11. **Limitations and future enhancements** - README sections 12 and 13; keep "implemented" and "future" clearly separate.
12. **Conclusion.**
13. **References** - libraries' official documentation (FastAPI, React, Recharts, SQLAlchemy, bcrypt) and any articles you used.
**Appendices:** API list, sample requests/responses from `/docs`, key source files, user manual.

---

## Part B: Viva questions and answers

### General
**Q1. What is your project and what problem does it solve?**
A personal health dashboard that lets users record measurements, see trends, read safe general health information from a
chatbot, get gentle wellness suggestions, and manage demo appointments. It brings scattered tracking and information into one place.

**Q2. Does it diagnose or prescribe?** No. It gives general education only, refuses medicine/dosage questions, tells users to
contact emergency services for urgent symptoms, and states clearly that it is not a doctor.

**Q3. Why did you choose this architecture?** A separate frontend and backend (client-server) keeps responsibilities clear:
the browser shows the interface, the server validates data, enforces security and talks to the database.

### Frontend
**Q4. Why React?** It builds the UI from reusable components (for example `RecordForm` is used on both the dashboard and
the records page) and re-renders automatically when state changes.

**Q5. What does Vite do?** It is the development server and build tool: fast start-up, hot reload, and a proxy that forwards
`/api` requests to the backend so the browser does not hit CORS problems in development.

**Q6. How do pages switch without a router library?** `App.jsx` reads `window.location.hash` (for example `#chat`), listens
for `hashchange`, and renders the matching page component. It is a simple approach suited to a small project.

**Q7. How do the charts update when records change?** Pages fetch records from the API, and `seriesFor()` turns them into chart
data for Recharts. After a record is added, edited or deleted the page reloads the data, so state changes and the chart redraws.

**Q8. What is `useState` / `useEffect`?** `useState` stores values that change (form fields, loaded data); `useEffect` runs
code after rendering, such as loading data from the API. I wrapped the loading pattern in a small `useAsync` hook.

### Backend
**Q9. Why FastAPI?** Concise Python code, automatic request validation through Pydantic, and automatic interactive docs at `/docs`.

**Q10. What is a router and a dependency?** A router groups related endpoints (`health_records.py`). A dependency is a function
FastAPI runs first and passes in, for example `get_current_user` (checks the token) and `get_db` (gives a database session).

**Q11. What does Pydantic do?** It defines the allowed shape of incoming data. For example a blood-pressure record must have
both numbers and the diastolic must be lower than the systolic; wrong data returns a 422 error before reaching the database.

**Q12. How do you stop one user reading another's data?** Every query filters by `user_id` of the logged-in user. If a record id
belongs to someone else the server answers 404, which also avoids revealing that the id exists. This is covered by tests.

**Q13. What HTTP status codes do you use?** 200 OK, 201 Created, 204 No Content (delete), 401 Unauthorized, 404 Not Found,
409 Conflict (duplicate email), 422 Unprocessable (invalid input).

**Q14. What is CORS?** A browser rule that blocks a page from calling a different origin unless the server allows it. The
backend allows the local frontend origins; in development the Vite proxy also avoids the problem.

### Database
**Q15. Why SQLite and SQLAlchemy?** SQLite needs no installation and stores everything in one file, ideal for a demo.
SQLAlchemy maps tables to Python classes and uses parameterised queries, which protects against SQL injection.

**Q16. Describe the tables and relationships.** `users` (one) to `health_records`, `appointments` and `recommendation_progress`
(many) through `user_id` foreign keys. See README section 7.

**Q17. Why does a blood-pressure record have `value` and `value2`?** One row stores systolic and diastolic together so they stay
paired by date; other record types use only `value`.

### Security
**Q18. How are passwords stored?** Only as bcrypt hashes - slow, salted one-way hashes. Plain passwords are never saved or logged.

**Q19. How does login work?** The server checks the password against the hash and returns a signed JWT containing the user id
and an expiry. The browser sends it as `Authorization: Bearer <token>` on each request; the server verifies the signature.

**Q20. What are the weaknesses of your authentication?** No email verification, rate limiting, token revocation or HTTPS, and the
token sits in localStorage. It is acceptable for a local demo, not for production. These are listed as limitations.

### AI integration
**Q21. How does the chatbot work?** `POST /api/chat` -> `ai_service.answer()`: (1) emergency keywords return an
emergency message; (2) medicine/dosage words return a refusal; (3) if an LLM key exists and the user consented, the question
is sent to the external LLM; otherwise (4) a rule-based keyword match returns a prepared general answer.

**Q22. Is the fallback a real AI?** No, and the app says so. It is keyword matching with hand-written, general answers.

**Q23. How do you protect privacy with the LLM?** The API key lives only in backend environment variables, the feature needs
the user's consent in Settings, only the typed question is sent (never health records), and any LLM failure falls back to
the rule-based answer.

**Q24. What are the chatbot's limits?** It can misunderstand wording, knows limited topics, and keyword emergency detection
cannot catch every phrasing. That is why every answer carries a disclaimer and advice to see a professional.

### Recommendation logic
**Q25. How are recommendations generated?** `recommendation_service.build()` looks at the user's chosen goals, activity level, the
restrictions flag and 14-day averages of logged sleep/water. Matching rules add suggestions, each with a "why".

**Q26. What if there is not enough information?** It returns a "needs more info" list (for example "choose a goal or log some
sleep") instead of guessing, and shows only the general safety reminder.

**Q27. What about medical restrictions?** If the user flags restrictions, diet and exercise tips are replaced by "check with a
professional first".

**Q28. Are the thresholds medical?** No. They only decide which gentle suggestion to show; the app never diagnoses.

### API requests
**Q29. Walk through adding a record.** Form -> `api.createRecord()` (Fetch, `POST /api/health-records`, token in header) ->
token check -> Pydantic validation -> row saved with the user's id -> 201 JSON -> page reloads and charts redraw.

**Q30. How do you handle errors?** The backend always returns `{"error": {"status", "message", "details"}}`; `api.js` turns
that into a readable message that forms and toasts display; a 401 on a logged-in request logs the user out.

**Q31. How is CSV export safe?** It only exports the logged-in user's rows, and prefixes cells beginning with `=`, `+`, `-`,
`@` so spreadsheets will not run them as formulas.

### Testing and future work
**Q32. How did you test?** pytest with a temporary in-memory database covering CRUD, invalid input, authentication failures,
user isolation, CSV, chatbot fallback and recommendations, plus a manual frontend checklist. (State your actual results.)

**Q33. What would you improve next?** Email verification, httpOnly cookies, rate limiting, HTTPS, PostgreSQL with migrations,
a retrieval-based chatbot over vetted sources, and automated frontend tests.
