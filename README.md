# FinSight — Personal Finance Dashboard with AI Insights

> Full-stack finance tracker with ML auto-categorization, spending charts, budget alerts, and Groq-powered weekly AI money reports.

**Tech stack:** React · Recharts · Python Flask · scikit-learn · Groq API (Llama 3.3) · PostgreSQL

---

## Project Structure

```
finance-dashboard/
├── backend/
│   ├── app.py                  # Flask app factory
│   ├── requirements.txt
│   ├── .env.example
│   ├── models/
│   │   └── models.py           # SQLAlchemy models
│   ├── routes/
│   │   ├── transactions.py     # CRUD + CSV upload + summary
│   │   ├── budgets.py          # Budget goals + alerts
│   │   └── insights.py         # AI weekly reports (Groq)
│   └── ml/
│       └── classifier.py       # scikit-learn Naive Bayes classifier
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── index.css           # CSS variables (dark/light theme)
│   │   ├── components/
│   │   │   ├── Sidebar.jsx
│   │   │   └── StatCard.jsx
│   │   ├── pages/
│   │   │   ├── Dashboard.jsx   # Overview, charts, tips
│   │   │   ├── Transactions.jsx # Add/upload/filter transactions
│   │   │   ├── Budgets.jsx     # Budget tracker with progress bars
│   │   │   └── Insights.jsx    # AI weekly money reports
│   │   ├── hooks/
│   │   │   └── useTheme.jsx    # Dark/light toggle with persistence
│   │   └── utils/
│   │       ├── api.js          # Axios API client
│   │       └── categories.js   # Category colors, icons, formatters
│   ├── package.json
│   ├── vite.config.js
│   └── vercel.json
├── render.yaml                 # Render deployment config
├── .gitignore
└── README.md
```

---

## Prerequisites

- **Python 3.11+** — [python.org](https://python.org)
- **Node.js 18+** — [nodejs.org](https://nodejs.org)
- **PostgreSQL** — [postgresql.org](https://postgresql.org) or use [Neon](https://neon.tech) (free cloud)
- **Groq API key** — Free at [console.groq.com](https://console.groq.com)

---

## Local Setup

### Step 1 — Clone and enter the project

```bash
git clone https://github.com/YOUR_USERNAME/finance-dashboard.git
cd finance-dashboard
```

---

### Step 2 — Backend setup

```bash
cd backend
```

**Create and activate virtual environment (Git Bash on Windows):**

```bash
python -m venv venv
source venv/Scripts/activate
```

You should see `(venv)` in your terminal prompt.

**Install dependencies:**

```bash
pip install -r requirements.txt
```

**Create your `.env` file:**

```bash
cp .env.example .env
```

Open `backend/.env` and fill in your values:

```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxx        # from console.groq.com
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/finance_dashboard
SECRET_KEY=any-random-string-here-like-abc123xyz
FLASK_ENV=development
```

**Create the PostgreSQL database:**

Open a new terminal and run:

```bash
psql -U postgres
```

Then inside psql:

```sql
CREATE DATABASE finance_dashboard;
\q
```

**Run the backend:**

```bash
python app.py
```

You should see:
```
* Running on http://127.0.0.1:5000
```

Test it: open `http://localhost:5000/api/health` in your browser — should show `{"status": "ok"}`.

---

### Step 3 — Frontend setup

Open a **new Git Bash terminal** and run:

```bash
cd finance-dashboard/frontend
npm install
```

**Create your `.env` file:**

```bash
cp .env.example .env
```

The default `frontend/.env` works for local dev:
```env
VITE_API_URL=http://localhost:5000/api
```

**Run the frontend:**

```bash
npm run dev
```

Open `http://localhost:5173` in your browser. Done!

---

## Features Walkthrough

### Dashboard
- Total spent, income, net savings for the current month
- 6-month area chart (income vs expenses)
- Spending breakdown pie chart by category
- Budget alerts (yellow = 80%, red = 100%+)
- AI spending tips from Groq
- 5 most recent transactions

### Transactions
- **Manual entry** — date, description, amount, type, category
- **CSV upload** — drag and drop any bank export CSV; auto-detects date/description/amount columns
- ML auto-categorizes every transaction using a trained Naive Bayes classifier
- Click any category tag to manually override it
- Filter by category or type (income/expense)
- Paginated table

### Budgets
- Set monthly limits per category
- Progress bars that turn amber at 80%, red at 100%
- "Over by ₹X" alerts shown per card
- Summary totals across all budgets

### AI Insights
- Click "Generate report" to get a Groq/Llama-powered weekly money analysis
- Covers: weekly summary, where money went, budget check, one actionable tip
- Stores all past weekly reports for history

---

## CSV Format

Your bank CSV needs (in any column order, any capitalization):
- A **date** column (any common date format works)
- A **description/narration/merchant** column  
- An **amount/debit/credit** column (handles ₹ and $ symbols, commas)

**Example:**
```csv
Date,Description,Amount
2024-01-15,Swiggy Food Order,-450
2024-01-16,Salary Credit,50000
2024-01-17,Uber Ride,-120
```

---

## Deployment

### Backend → Render (Free tier)

1. Push your code to GitHub (see GitHub section below)
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Settings:
   - **Root directory:** `backend`
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn "app:create_app()" --bind 0.0.0.0:$PORT`
5. Add environment variables in Render dashboard:
   - `GROQ_API_KEY` → your Groq key
   - `DATABASE_URL` → your PostgreSQL URL (Render PostgreSQL or Neon)
   - `SECRET_KEY` → any random string
   - `FLASK_ENV` → `production`
6. Add a **PostgreSQL** database in Render (free tier available) or use [Neon.tech](https://neon.tech)
7. Copy the database connection string into `DATABASE_URL`

> Render free tier spins down after 15 min inactivity — first request may take ~30 seconds to wake up.

---

### Frontend → Vercel (Free tier)

1. Go to [vercel.com](https://vercel.com) → New Project
2. Import your GitHub repo
3. Settings:
   - **Root directory:** `frontend`
   - **Framework preset:** Vite
4. Add environment variable:
   - `VITE_API_URL` → your Render backend URL, e.g. `https://finsight-backend.onrender.com/api`
5. Deploy!

Your app will be live at `https://your-project.vercel.app`

---

## Push to GitHub

```bash
# In the root finance-dashboard/ folder
cd finance-dashboard

git init
git add .
git commit -m "feat: initial finance dashboard with AI insights"

# Create a new repo on github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/finance-dashboard.git
git branch -M main
git push -u origin main
```

### Recommended commit conventions (same as your mock interview project):
```
feat: add CSV upload with auto-categorization
fix: budget percentage calculation edge case
chore: add render.yaml deployment config
docs: update README with Neon DB setup
```

---

## Resume Description

> **Personal Finance Dashboard with AI Insights** | React, Python Flask, scikit-learn, Groq API, PostgreSQL
>
> Built a full-stack finance tracker where users upload bank CSV statements or manually log transactions. Implemented a Naive Bayes ML classifier (scikit-learn) that auto-categorizes transactions into 11 spending categories. Integrated Groq's Llama 3.3-70b model for weekly AI-generated money reports in plain language. Features include interactive Recharts visualizations, budget goal tracking with real-time alerts, dark/light theme toggle, and paginated transaction history. Deployed backend on Render with PostgreSQL and frontend on Vercel.

---

## Troubleshooting

**`psycopg2` install error on Windows:**
```bash
pip install psycopg2-binary --break-system-packages
```

**Flask not found after venv activation:**
```bash
# Make sure you're in the backend folder with venv active
which python  # should show .../venv/Scripts/python
```

**CORS error in browser:**
Check that `VITE_API_URL` in frontend `.env` matches your backend URL exactly.

**CSV not parsing:**
Make sure your CSV has clear column names. The parser looks for keywords like "date", "desc", "narration", "amount", "debit" in column names.

**Groq API error:**
Get a free key at [console.groq.com](https://console.groq.com) — no credit card required, unlike OpenAI.
