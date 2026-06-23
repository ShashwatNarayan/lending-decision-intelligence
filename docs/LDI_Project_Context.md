# PROJECT CONTEXT — Lending Decision Intelligence Platform

> **Purpose of this file:** This is the master context document for a Claude Project dedicated to building the Lending Decision Intelligence platform. It carries forward every architectural decision, business rule, reuse mapping, and constraint from the planning conversations so the building Claude has full context from message one. Read this before answering any question about the project.

---

## 1. What this project IS (and is NOT)

**IS:** A B2B decision-support tool for credit risk professionals (loan officers, risk analysts at banks/NBFCs). Given a loan applicant's financial profile, the system:
1. Predicts probability of default (existing XGBoost model)
2. Makes an approve/reject **decision** based on a cost-sensitive threshold
3. Assigns a **risk-based interest rate** for approved applicants
4. Generates **plain-English rejection/approval reasons** from SHAP values (regulatory-grade adverse-action explanations)
5. Shows the **₹ portfolio impact** of any threshold choice via an interactive dashboard
6. (Bonus) Lets a non-technical user **ask the loan book questions in plain English** via a governed NL→SQL layer

**IS NOT:**
- A consumer-facing tool (borrowers never visit it; the bank's staff does)
- An AI/ML-powered categorization system (the model is XGBoost, not deep learning — never misrepresent this)
- A production credit bureau (it's a portfolio project using public data, designed to demonstrate decision-science thinking)
- A chatbot or agent

---

## 2. The builder's profile and constraints

**Builder:** Shashwat Narayan, B.Tech CSE student at KIIT (Class of 2027, CGPA 8.26)

**Hard constraints:**
- **FICO visits campus ~July 3, 2026** — this is the highest-priority target company and the project must be at minimum demo-ready by then
- **CAT 2026 in November** — project time is capped; no scope creep allowed
- **Honesty as a hard rule:** never describe ArthaLens or this project as "AI/ML-driven" unless referring specifically to the XGBoost model or the Gemini NL layer. The categorization pipeline in ArthaLens is rule-based. The decision layer in this project is cost-sensitive thresholding on model outputs — call it what it is.
- **Stack conservatism:** no new frameworks. Reuse the Python/Flask/PostgreSQL/Render stack the builder already knows.

**What the builder already knows well:** Python, Flask, PostgreSQL, XGBoost, SHAP, scikit-learn, Gemini API, Jinja2, vanilla JS, Chart.js, Git, Render deployment, Neon PostgreSQL.

**What the builder does NOT know (don't assume):** React, Docker, Kubernetes, AWS/GCP services, FastAPI (limited exposure), frontend frameworks, CI/CD pipelines beyond Render's auto-deploy.

---

## 3. Existing codebases to reuse

### 3A. Loan Default Risk Prediction System
**Repo:** https://github.com/ShashwatNarayan/LoanDefaultRiskPredictionSystem

**What exists and should be reused:**
- Trained XGBoost model on 133k records
- 10 domain-specific engineered features (income ratios, debt-to-income, credit history length, etc.)
- SHAP integration — per-borrower SHAP value computation already working
- 5-fold cross-validation pipeline (AUC 0.7375)
- SMOTE-based class imbalance handling
- Feature engineering pipeline (can be extracted into a reusable module)
- Data loading and preprocessing code

**What to extract specifically:**
- The model training + saving code → refactor into a `model/` module
- The SHAP explanation code → refactor into an `explainability/` module
- The feature engineering functions → refactor into a `features/` module
- The evaluation pipeline → extend from AUC-based to ₹-based in a `backtest/` module

**Key model details:**
- Algorithm: XGBoost classifier
- Target: binary (default / no default)
- Dataset: 133k records, ~10 engineered features
- Performance: 5-fold CV AUC of 0.7375; default recall improved from 17.8% to 62.8% via threshold tuning + SMOTE
- Output: P(default) per applicant + per-feature SHAP values

### 3B. ArthaLens (Personal Financial Intelligence System)
**Live at:** arthalens.onrender.com
**What it is:** A personal finance tool with rule-based transaction categorization, anomaly detection, and a governed NL→SQL query layer.

**What exists and should be reused:**
- **Flask application skeleton:** app factory pattern, blueprints, config management, error handling
- **PostgreSQL (Neon) connection:** connection pooling, migration patterns, environment variable config
- **The governed NL→SQL engine (this is the crown jewel for reuse):**
  - Intent routing: classifies user query → subscription lookup (zero LLM calls) vs SQL generation
  - Gemini 2.5 Flash integration: prompt templates, API call patterns, response parsing
  - **Security architecture (THE differentiator):**
    - Read-only database role for all LLM-generated queries
    - Automatic user_id injection (queries are scoped to the authenticated user)
    - SQL sandboxing (whitelist of allowed operations)
    - Prompt injection defense
  - Response formatting
- **Jinja2 template patterns:** page layouts, component structure, CSS patterns
- **Render deployment config:** Procfile, requirements.txt, env var patterns
- **z-score anomaly detection** (may be useful as a pattern but not directly relevant)
- **SHA-256/MD5 idempotent ingestion** (not needed for this project)

**What to extract specifically:**
- The entire NL query engine module (intent router + Gemini caller + SQL generator + security layer + response formatter)
- The Flask app skeleton (strip personal-finance routes, keep structure)
- The Neon database connection setup
- The read-only role creation SQL scripts
- The Jinja2 base templates and CSS
- The Render deployment files (Procfile, requirements.txt)

---

## 4. Architecture

```
┌─────────────────────────────────────────────────────┐
│                   FLASK WEB APP                      │
│                                                      │
│  ┌──────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ Portfolio │  │  Applicant   │  │   NL Query    │  │
│  │   View    │  │   Lookup     │  │     Box       │  │
│  │ (slider)  │  │  (single)    │  │  (Phase 5)    │  │
│  └─────┬─────┘  └──────┬───────┘  └───────┬───────┘  │
│        │               │                  │          │
│  ┌─────▼───────────────▼──────────────────▼───────┐  │
│  │              API / ROUTE LAYER                  │  │
│  └─────────────────────┬──────────────────────────┘  │
│                        │                             │
│  ┌─────────────────────▼──────────────────────────┐  │
│  │            DECISION ENGINE                      │  │
│  │  ┌────────────┐ ┌──────────┐ ┌──────────────┐  │  │
│  │  │ Cost-Sens. │ │ Risk-    │ │  Adverse     │  │  │
│  │  │ Threshold  │ │ Based    │ │  Action      │  │  │
│  │  │ Engine     │ │ Pricing  │ │  Reasons     │  │  │
│  │  └─────┬──────┘ └────┬─────┘ └──────┬───────┘  │  │
│  └────────┼─────────────┼──────────────┼──────────┘  │
│           │             │              │             │
│  ┌────────▼─────────────▼──────────────▼──────────┐  │
│  │           SCORING MODULE                        │  │
│  │     XGBoost model + SHAP explainer              │  │
│  │     (reused from Loan Default)                  │  │
│  └─────────────────────┬──────────────────────────┘  │
│                        │                             │
│  ┌─────────────────────▼──────────────────────────┐  │
│  │         POSTGRESQL (Neon)                       │  │
│  │  loan_applications │ decisions │ query_log      │  │
│  │  [read-only role for NL queries]                │  │
│  └────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## 5. Business logic rules (these are design decisions, not suggestions — follow them)

### 5A. Cost-sensitive threshold
- **False approval cost** = loan_amount × loss_given_default (use 0.6 as LGD — industry standard assumption meaning 60% of the loan is lost if the borrower defaults)
- **False rejection cost** = loan_amount × interest_rate × loan_term_fraction (lost revenue from turning away a good borrower)
- The threshold slider ranges from 5% to 50% P(default)
- At each threshold value, compute: total approved, total rejected, expected ₹ loss, expected ₹ revenue, net portfolio value
- **Optimal threshold** = the one that maximizes net portfolio value (expected revenue minus expected loss)
- Display this as a clear recommendation: "Optimal threshold: X% — maximizes net portfolio value at ₹Y"

### 5B. Risk-based pricing (score-band → interest rate)
| P(default) range | Risk band | Interest rate | Decision |
|---|---|---|---|
| 0% – 10% | Low risk | 10.0% | Approve |
| 10% – 20% | Medium risk | 13.0% | Approve |
| 20% – 30% | High risk | 16.0% | Approve (at institution's discretion) |
| 30%+ | Very high risk | — | Reject |

These bands are configurable, not hardcoded. Store them in a config dict or DB table so they can be adjusted without code changes.

### 5C. Adverse-action reason generation
- For each applicant, take the top 3 SHAP features (by absolute value) pushing toward default
- Map each feature name to a human-readable reason using a lookup dictionary
- Example mappings (expand this to cover all ~10-15 features):
  - `debt_to_income_ratio` → "High debt relative to income"
  - `credit_history_months` → "Short credit history"
  - `loan_to_income_ratio` → "Loan amount large relative to income"
  - `num_existing_loans` → "Multiple existing loan obligations"
  - `months_employed` → "Limited employment history"
  - `delinquency_count` → "Previous missed or late payments"
  - `annual_income` → "Income below threshold for requested amount"
- For approved applicants, flip the framing to positive: "Stable income," "Long credit history," etc.
- Always return exactly 3 reasons, ordered by SHAP magnitude

### 5D. Backtesting
- Train/test split: 80/20 (consistent with existing Loan Default setup)
- Evaluate at thresholds from 5% to 50% in 1% steps
- For each threshold, on the TEST SET ONLY (where true outcomes are known), compute:
  - Actual defaults among approved applicants
  - Actual ₹ lost (actual defaults × loan_amount × LGD)
  - Actual ₹ earned (non-defaulting approved × loan_amount × assigned_rate)
  - Net ₹ outcome
- Compare against baselines: "approve all" and "approve only <10% risk"
- Report the headline sentence: "At optimal threshold X%, the system earned ₹A net vs ₹B under naive approval — a Y% improvement"

---

## 6. Database schema

```sql
-- The main loan applications table (loaded from the existing 133k dataset)
CREATE TABLE loan_applications (
    id SERIAL PRIMARY KEY,
    -- Original features from the dataset (adjust column names to match your actual CSV)
    annual_income NUMERIC,
    loan_amount NUMERIC,
    debt_to_income_ratio NUMERIC,
    credit_history_months INTEGER,
    num_existing_loans INTEGER,
    months_employed INTEGER,
    delinquency_count INTEGER,
    -- ... (include all features your model uses)
    
    -- Synthetic additions for business context
    loan_term_months INTEGER DEFAULT 36,
    
    -- True outcome (known from historical data)
    actually_defaulted BOOLEAN,
    
    -- Model outputs (populated by scoring pipeline)
    default_probability NUMERIC,
    risk_band VARCHAR(20),
    
    -- Decision outputs (populated by decision engine)
    decision VARCHAR(10), -- 'APPROVE' or 'REJECT'
    assigned_interest_rate NUMERIC,
    expected_revenue NUMERIC,
    expected_loss NUMERIC,
    
    -- Explanation (populated by adverse-action engine)
    rejection_reasons JSONB, -- ["High debt relative to income", "Short credit history", "..."]
    shap_values JSONB,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Portfolio simulation snapshots (one row per threshold evaluated)
CREATE TABLE portfolio_snapshots (
    id SERIAL PRIMARY KEY,
    threshold_pct NUMERIC,
    total_approved INTEGER,
    total_rejected INTEGER,
    approval_rate NUMERIC,
    expected_total_revenue NUMERIC,
    expected_total_loss NUMERIC,
    net_portfolio_value NUMERIC,
    -- Backtest actuals (only for test-set evaluations)
    actual_defaults_in_approved INTEGER,
    actual_loss NUMERIC,
    actual_revenue NUMERIC,
    actual_net NUMERIC,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Query audit log (for the NL layer)
CREATE TABLE query_log (
    id SERIAL PRIMARY KEY,
    natural_language_query TEXT,
    generated_sql TEXT,
    was_executed BOOLEAN,
    was_blocked BOOLEAN DEFAULT FALSE,
    block_reason TEXT,
    result_row_count INTEGER,
    execution_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Read-only role for NL-generated queries (CRITICAL SECURITY)
-- This is copied from ArthaLens's security architecture
CREATE ROLE readonly_query_role WITH LOGIN PASSWORD 'xxx';
GRANT CONNECT ON DATABASE lending_intel TO readonly_query_role;
GRANT USAGE ON SCHEMA public TO readonly_query_role;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly_query_role;
-- NO INSERT, UPDATE, DELETE, DROP, or DDL permissions
```

---

## 7. Tech stack (locked — do not suggest alternatives)

| Layer | Technology | Notes |
|---|---|---|
| ML model | XGBoost + scikit-learn | Existing model, not to be swapped |
| Explainability | SHAP | Existing integration |
| Backend | Python 3.11+ + Flask | From ArthaLens |
| Database | PostgreSQL on Neon | From ArthaLens |
| NL engine | Gemini 2.5 Flash API | From ArthaLens |
| Frontend | Jinja2 + vanilla JS + Chart.js | No React, no frontend frameworks |
| Deployment | Render (free tier) | From ArthaLens |
| Version control | Git + GitHub (public repo) | Clean commit history matters |

**Do not suggest:** React, Next.js, FastAPI, Django, Docker, AWS/GCP/Azure, LangChain, any CSS framework beyond basic custom CSS. The builder's time goes into business logic, not tooling.

---

## 8. File/folder structure (target)

```
lending-decision-intelligence/
├── app/
│   ├── __init__.py              # Flask app factory (from ArthaLens)
│   ├── config.py                # Config management (from ArthaLens)
│   ├── models/
│   │   ├── scoring.py           # XGBoost loading + prediction (from Loan Default)
│   │   └── explainer.py         # SHAP computation + reason generation
│   ├── decision/
│   │   ├── engine.py            # Cost-sensitive threshold + approve/reject logic
│   │   ├── pricing.py           # Risk-band → interest rate mapping
│   │   └── adverse_action.py    # SHAP → human-readable reasons
│   ├── backtest/
│   │   └── evaluator.py         # ₹-based backtesting framework
│   ├── nl_query/
│   │   ├── router.py            # Intent classification (from ArthaLens)
│   │   ├── sql_generator.py     # Gemini → SQL generation (from ArthaLens)
│   │   ├── security.py          # Read-only role, sandboxing, injection defense (from ArthaLens)
│   │   └── semantic_layer.py    # Schema description for the LLM
│   ├── routes/
│   │   ├── portfolio.py         # Portfolio dashboard routes
│   │   ├── applicant.py         # Single applicant lookup routes
│   │   └── query.py             # NL query endpoint
│   ├── templates/
│   │   ├── base.html            # Base layout (from ArthaLens)
│   │   ├── portfolio.html       # Dashboard with slider + charts
│   │   ├── applicant.html       # Applicant detail view
│   │   └── components/
│   │       ├── metric_card.html
│   │       └── reason_list.html
│   └── static/
│       ├── css/
│       │   └── main.css
│       └── js/
│           ├── threshold_slider.js
│           └── nl_query.js
├── data/
│   ├── load_data.py             # One-time script to load CSV → PostgreSQL
│   └── raw/                     # The 133k-record dataset
├── model/
│   ├── train.py                 # Model training script (from Loan Default)
│   └── artifacts/
│       └── xgboost_model.json   # Saved model artifact
├── tests/
│   ├── test_scoring.py
│   ├── test_decision.py
│   ├── test_backtest.py
│   └── test_nl_queries.py       # Including adversarial query tests
├── Procfile                     # web: gunicorn app:create_app()
├── requirements.txt
├── .env.example                 # Template for env vars (no real secrets)
├── README.md
└── .gitignore
```

---

## 9. Key interview talking points this project enables

When helping the builder prepare for interviews, emphasize these conversations (not generic ML Q&A):

1. **"Why not just maximize recall/AUC?"** → Because in lending, a false approval costs real money (loan_amount × 0.6 LGD) while a false rejection costs lost revenue. The right metric is net ₹ portfolio value, not a statistical score. This is cost-sensitive decision-making.

2. **"How do you explain rejections?"** → SHAP values identify the top contributing features per applicant. These are mapped to plain-English reasons that comply with fair-lending disclosure requirements (US: FCRA/ECOA adverse action notices; India: RBI fair practices code). This isn't just good UX — it's a legal requirement.

3. **"How do you prevent the NL layer from being exploited?"** → Four layers: (a) read-only database role — even if the LLM generates malicious SQL, it physically cannot modify data; (b) SQL sandboxing — only SELECT statements pass validation; (c) prompt injection defense in the Gemini prompt template; (d) query audit logging for forensic review. Walk through each layer.

4. **"What would you do differently in production?"** → (a) The model would be retrained on fresh data periodically with monitoring for distribution drift; (b) the cost matrix and risk bands would be calibrated by the institution's risk appetite, not hardcoded; (c) A/B testing of threshold changes before full rollout; (d) regulatory review of the SHAP-to-reason mappings.

5. **"What's the business impact?"** → Quote the backtest headline: "At optimal threshold X%, net portfolio value was ₹Y — a Z% improvement over naive approval." Always lead with the ₹ number, not the AUC.

---

## 10. What NOT to do (hard rules)

- **Never describe the project as "AI-powered" or "ML-driven" in a blanket sense.** The XGBoost model is ML. The decision layer is business logic. The NL layer uses an LLM. Be precise about which component uses what.
- **Never fabricate metrics.** All numbers on the resume and in interviews must come from actual backtest results on the held-out test set. If you haven't run the backtest yet, say "pending evaluation," not a made-up number.
- **Never suggest swapping XGBoost for a deep learning model.** The model isn't the point of this project. The decision layer on top is. Suggesting a model swap wastes time and misses the thesis.
- **Never suggest adding React, Docker, or cloud infrastructure.** The builder's time budget doesn't support learning new tooling, and none of it adds interview value for the target companies.
- **Never suggest a consumer-facing version.** This is B2B by design. A consumer version ("check your loan eligibility!") targets a different market, different users, and different companies — and it would confuse the project's narrative.
- **Keep scope tight.** If the builder asks about adding features beyond what's in this document (e.g., "should I add a chatbot?", "should I add user authentication?"), the default answer is no unless it directly serves the FICO/Tier-C/Tier-A interview narrative.
