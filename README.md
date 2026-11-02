# FinSight

[![CI](https://github.com/Avni-06/finance-dashboard/actions/workflows/ci.yml/badge.svg)](https://github.com/Avni-06/finance-dashboard/actions/workflows/ci.yml)

A money tracker built around how people actually earn, starting with students.

Import a bank statement and FinSight sorts every UPI payment into categories, then answers
the question a student on pocket money actually has: **"Will this last until my next allowance?"**
Salaried employees and freelancers get dashboards built for their kind of income too.

![Student dashboard](docs/screenshots/student-dashboard.png)

**Try it without signing up:** open the app and click *Student demo*, *Salaried demo* or
*Freelancer demo*. Each is a read-only account with 6 months of generated sample data.

---

## What it does

### For everyone
- **Bank statement import.** Handles junk rows above the header, separate debit/credit columns,
  `Dr/Cr` flags, `₹1,234.50` / `(120.00)` amounts and mixed date formats. Tested with an HDFC-style
  layout and two generic CSV layouts. Re-uploading the same file doesn't create duplicates
  (SHA-256 row fingerprints).
- **Automatic categories that learn.** Change Swiggy to "Fun" once and every past and future
  Swiggy payment follows.
- **Budgets** with warnings at 80% and alerts at 100%, plus suggested limits from your income.
- **Recurring payment detection.** Netflix, rent, EMIs and SIPs are found automatically, with
  their next due date.
- **Unusual spending alerts.** "Food is at ₹4,190, 2.4× your usual by this day of the month."
- **Weekly report** in plain words with one concrete action, written by an LLM.
- **Savings goals** that tell you how much to save per month to hit the date.
- Dark and light themes, works on mobile.

### Built around how you earn

| | Student | Salaried | Freelancer |
|---|---|---|---|
| Headline number | Safe to spend today | Safe to spend until payday | Average month |
| Special views | Money runway, no-spend streak, semester costs kept out of daily money, income sources (allowance, stipend, scholarship) | 50/30/20 check, EMI load, emergency fund target | Income swings, tax set-aside, top clients |
| Categories | Food & Canteen, Hostel & Rent, Books & Stationery, Fees, Events & Hackathons… | Rent, Groceries, Bills, EMI & Loans, Investments… | Business Expenses, Software & Tools, Taxes… |

### Roles
| Role | How it's created | Can do |
|---|---|---|
| **User** | Sign up | Everything on their own data |
| **Demo** | "Try demo" button | Read-only tour with sample data; all writes are blocked server-side |
| **Admin** | `python manage.py create-admin` only, never via sign-up | Platform stats, user management, model metrics, retrain the model |

---

## How categorisation works

```mermaid
flowchart LR
    A["UPI/DR/4123.../SWIGGY/YESB/swiggy@ybl"] --> B[Clean narration<br/>+ merchant key]
    B --> C{User rule<br/>for merchant?}
    C -- yes --> R[Category]
    C -- no --> D{Known brand<br/>keyword?}
    D -- yes --> R
    D -- no --> E[TF-IDF + Logistic Regression<br/>masked to income/expense]
    E --> F{Confident?}
    F -- yes --> R
    F -- no --> G[Other + 'Review' flag]
```

- The model predicts one of 27 profile-independent **concepts** (food, rent, stipend…), which are
  then mapped to each profile's categories. One model serves students, employees and freelancers.
- **Training data is synthetic:** 4,431 generated bank narrations (1,476 distinct merchants), shaped
  like real UPI, NEFT, POS and ACH formats with reference numbers, IFSC codes and VPAs. It has not
  been trained or evaluated on real customer data.
- **Evaluation uses an 80/20 group split by merchant**, so the test set (888 rows) only contains
  merchants the model has never seen.

| Model | Accuracy | Macro-F1 |
|---|---|---|
| TF-IDF + Logistic Regression (unseen merchants) | **85.0%** | **0.858** |
| Keyword rules only | 69.3% | 0.732 |
| Majority class | 6.1% | 0.004 |

- The weakest classes are `shopping` and `transfer_in`, where the model confuses generic merchant
  names with other categories.
- User corrections are stored as merchant rules immediately, and an admin can retrain the model with
  all corrections included (each counts 3× a synthetic example).

## Weekly report: free LLMs with a fallback

Provider chain: **Groq (Llama 3.3 70B) → Google Gemini → built-in rules.** Both LLMs have free tiers.
If no key is set or a provider fails, the rule-based writer produces the report, so the feature never
breaks in a demo. Only aggregated spending figures, your first name and recurring merchant names are
sent to the LLM, never raw transactions or emails. Reports are cached per week and limited to 5 per
user per day to protect the free quota.

---

## Tech stack

**Frontend:** React 18, Vite, Tailwind CSS, Recharts, React Router
**Backend:** Flask, SQLAlchemy, JWT auth, pandas
**ML:** scikit-learn (TF-IDF word + char n-grams, Logistic Regression)
**Database:** SQLite locally, PostgreSQL supported through `DATABASE_URL` (Neon recommended)
**Testing/CI:** pytest (34 tests), GitHub Actions (backend tests + frontend build)

```
finance-dashboard/
├── backend/
│   ├── app/
│   │   ├── ml/            # concepts, synthetic dataset, training, hybrid classifier
│   │   ├── models/        # SQLAlchemy models
│   │   ├── routes/        # auth, transactions, budgets+goals, dashboard, insights, admin
│   │   ├── services/      # analytics, AI reports, demo seeding, import logic
│   │   └── utils/         # CSV parser, merchant cleaning, validation, security decorators
│   ├── tests/
│   ├── manage.py          # create-admin, seed-demo, train
│   └── run.py
├── frontend/
│   └── src/
│       ├── components/    # layout, charts, runway track, dialogs
│       ├── pages/         # dashboard, transactions, budgets, goals, insights, admin…
│       ├── context/       # auth
│       └── lib/           # api client, formatting, theme
└── render.yaml
```

---

## Run it locally (Windows, macOS, Linux)

Needs **Python 3.11+** and **Node 18+**. No database install needed: it uses SQLite locally.

**1. Backend** (terminal 1)
```bash
cd backend
python -m venv venv
venv\Scripts\activate            # macOS/Linux: source venv/bin/activate
pip install -r requirements-dev.txt
copy .env.example .env           # macOS/Linux: cp .env.example .env
python run.py                    # http://localhost:5000/api/health
```
The classifier trains itself on first use (about 10 seconds). Add a free `GROQ_API_KEY`
(console.groq.com) or `GEMINI_API_KEY` (aistudio.google.com) to `.env` for LLM-written reports.

**2. Frontend** (terminal 2)
```bash
cd frontend
npm install
npm run dev                      # http://localhost:5173
```

**3. Optional**
```bash
python manage.py create-admin --email admin@example.com   # then log in at /login
python manage.py seed-demo                                 # rebuild demo data
python -m pytest -q                                        # run the tests
python -m app.ml.train                                     # retrain and print accuracy
```
A sample statement to import is in `frontend/public/sample-statement.csv`.

## Deploy (free)

1. **Database:** create a free Postgres database on [Neon](https://neon.tech) and copy its connection string.
2. **API on Render:** New → Blueprint → pick this repo (uses `render.yaml`). Fill in `DATABASE_URL`,
   `CORS_ORIGINS` (your Vercel URL) and optionally `GROQ_API_KEY` / `GEMINI_API_KEY`.
3. **Frontend on Vercel:** import the repo, root directory `frontend`, framework Vite, and set
   `VITE_API_URL` to `https://<your-render-app>.onrender.com/api`.

Render's free tier sleeps after 15 minutes, so the first request can take ~30 seconds.

## Security notes
- Passwords hashed with Werkzeug (scrypt); JWTs expire after 7 days.
- Roles are checked against the database on every request, so deactivation applies immediately.
- Every query is scoped to the logged-in user; tests cover cross-user access (IDOR).
- Role can't be set at sign-up; admins are created from the command line only.
- Uploads are limited to 2 MB and 5,000 rows.

## Known limitations
- Real bank exports other than HDFC-style layouts are not yet verified.
- The classifier is trained on synthetic data, so accuracy on real statements may differ.
- No login rate limiting, and no database migrations (tables are created on first run).
- The JWT is stored in `localStorage`.

## Screenshots

| Landing | Transactions (light mode) |
|---|---|
| ![Landing](docs/screenshots/landing.png) | ![Transactions](docs/screenshots/transactions-light.png) |

![Admin](docs/screenshots/admin.png)
