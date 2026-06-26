# CLAUDE.md — Lending Decision Intelligence Platform
## Project Context File for Claude Code

> **READ THIS FIRST, EVERY TIME.** Before writing, editing, or running any code in this project,
> read this file completely. Then read `LDI_Project_Context.md` for architecture details and
> `Lending_Decision_Intelligence_Build_Roadmap.md` for the phase plan.
> All decisions in those two files are final unless Shashwat explicitly says otherwise in the prompt.

---

## What this project is (one paragraph)

A B2B credit decisioning tool for loan officers and risk analysts. Given a loan applicant's
financial profile, it: (1) predicts probability of default using an existing XGBoost model,
(2) makes an approve/reject decision using a cost-sensitive threshold, (3) assigns a risk-based
interest rate to approved applicants, (4) generates plain-English rejection reasons from SHAP
values, and (5) shows the ₹ portfolio impact of any threshold choice via an interactive dashboard.
It is NOT consumer-facing. It is NOT "AI-powered" — the model is XGBoost, the decision layer is
cost-sensitive thresholding. Call things what they are.

---

## Locked tech stack — never suggest alternatives

| Layer | Technology |
|---|---|
| ML model | XGBoost + scikit-learn (existing artifacts, do not retrain) |
| Explainability | SHAP |
| Backend | Python 3.11 + Flask (app factory pattern) |
| Database | PostgreSQL on Neon |
| NL engine | Gemini 2.5 Flash API (Phase 5 only) |
| Frontend | Jinja2 + vanilla JS + Chart.js or Plotly |
| Deployment | Render (free tier) |

**Never suggest:** React, Next.js, FastAPI, Django, Docker, AWS/GCP/Azure, LangChain,
any CSS framework other than custom CSS. Never suggest retraining the model.

---

## Model artifacts (already built, do not regenerate)

Located in `model/artifacts/`:

| File | Details |
|---|---|
| `xgboost_model.pkl` | XGBClassifier, 500 trees, depth 6, lr 0.05 |
| `scaler.pkl` | StandardScaler fitted on 30 features (sklearn 1.3.2) |
| `feature_columns.pkl` | List of 30 feature names in exact order |
| `optimal_threshold.pkl` | `0.2282` — optimized for max F1 on imbalanced data |

**Version pins (requirements.txt must match):**
```
xgboost==2.0.3
scikit-learn==1.3.2
```
These pins exist because the pickle files were serialized with these exact versions.
Do not upgrade them without retraining.

---

## The 30 features (exact names, exact order)

```python
['loan_amnt', 'int_rate', 'annual_inc', 'dti', 'emp_length', 'revol_bal',
 'revol_util', 'mort_acc', 'credit_history_years', 'loan_to_income',
 'fico_score', 'installment_to_income', 'int_rate_tier', 'open_acc_ratio',
 'has_delinquency', 'has_pub_rec', 'high_inq_flag', 'loan_amnt_tier',
 'is_short_term', 'grade_encoded', 'home_OTHER', 'home_OWN', 'home_RENT',
 'purpose_credit_card', 'purpose_debt_consolidation', 'purpose_home_improvement',
 'purpose_major_purchase', 'purpose_medical', 'purpose_other', 'purpose_small_business']
```

---

## Dataset

- File: `data/stage2_features.csv`
- 133,018 rows × 31 columns (30 features + `target`)
- Default rate: 20.25%
- Zero null values
- Source: LendingClub public dataset, already cleaned and feature-engineered

---

## Target folder structure

```
lending-decision-intelligence/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── config.py                # Env-driven config
│   ├── models/
│   │   ├── scoring.py           # XGBoost load + predict
│   │   └── explainer.py         # SHAP compute + reason generation
│   ├── decision/
│   │   ├── engine.py            # Cost-sensitive threshold + approve/reject
│   │   ├── pricing.py           # Risk-band → interest rate
│   │   └── adverse_action.py    # SHAP → plain-English reasons
│   ├── backtest/
│   │   └── evaluator.py         # ₹-based backtesting
│   ├── nl_query/                # Phase 5 only — do not build until Phase 4 is done
│   │   ├── router.py
│   │   ├── sql_generator.py
│   │   ├── security.py
│   │   └── semantic_layer.py
│   ├── routes/
│   │   ├── main.py              # Landing + base page routes
│   │   ├── portfolio.py         # Portfolio dashboard routes
│   │   └── applicant.py         # Single applicant lookup routes
│   ├── templates/
│   │   ├── base.html
│   │   ├── portfolio.html
│   │   └── applicant.html
│   └── static/
│       ├── css/main.css
│       └── js/
│           ├── threshold_slider.js
│           └── charts.js
├── data/
│   ├── load_data.py             # One-time CSV → PostgreSQL loader
│   └── stage2_features.csv      # The 133k dataset
├── model/
│   └── artifacts/
│       ├── xgboost_model.pkl
│       ├── scaler.pkl
│       ├── feature_columns.pkl
│       └── optimal_threshold.pkl
├── migrations/                  # Flask-Migrate / Alembic
├── tests/
│   ├── test_scoring.py
│   └── test_decision.py
├── .python-version              # Contains: 3.11.9
├── .env.example
├── config.py
├── wsgi.py                      # gunicorn wsgi:app
├── flask_app.py                 # dev only: app.run()
├── Procfile                     # web: gunicorn wsgi:app
├── render.yaml
├── requirements.txt
├── LDI_Project_Context.md
├── Lending_Decision_Intelligence_Build_Roadmap.md
├── CLAUDE.md                    # This file
└── .gitignore
```

---

## Database schema (Neon PostgreSQL)

Three tables. Do not add tables without discussing first.

### `loan_applications`
Stores all 133k records + computed decision columns.

| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| loan_amnt | NUMERIC(12,2) | |
| int_rate | NUMERIC(6,3) | |
| annual_inc | NUMERIC(14,2) | |
| dti | NUMERIC(8,3) | |
| emp_length | NUMERIC(4,1) | |
| revol_bal | NUMERIC(14,2) | |
| revol_util | NUMERIC(6,2) | |
| mort_acc | INTEGER | |
| credit_history_years | NUMERIC(6,1) | |
| loan_to_income | NUMERIC(8,4) | |
| fico_score | NUMERIC(6,1) | |
| installment_to_income | NUMERIC(8,4) | |
| int_rate_tier | INTEGER | 0–4 |
| open_acc_ratio | NUMERIC(6,4) | |
| has_delinquency | BOOLEAN | |
| has_pub_rec | BOOLEAN | |
| high_inq_flag | BOOLEAN | |
| loan_amnt_tier | INTEGER | 0–3 |
| is_short_term | BOOLEAN | |
| grade_encoded | INTEGER | 0–6 |
| home_OTHER | BOOLEAN | |
| home_OWN | BOOLEAN | |
| home_RENT | BOOLEAN | |
| purpose_credit_card | BOOLEAN | |
| purpose_debt_consolidation | BOOLEAN | |
| purpose_home_improvement | BOOLEAN | |
| purpose_major_purchase | BOOLEAN | |
| purpose_medical | BOOLEAN | |
| purpose_other | BOOLEAN | |
| purpose_small_business | BOOLEAN | |
| target | SMALLINT | 1=default, 0=no default (ground truth) |
| default_probability | NUMERIC(6,4) | Computed by scoring.py |
| decision | VARCHAR(10) | 'APPROVE' or 'REJECT' |
| assigned_rate | NUMERIC(6,3) | Interest rate assigned (approved only) |
| decision_reasons | TEXT | JSON array of plain-English reasons |
| loaded_at | TIMESTAMPTZ | default NOW() |

### `portfolio_snapshots`
Stores threshold simulation results for the dashboard slider.

| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| threshold | NUMERIC(6,4) | The threshold value simulated |
| approvals | INTEGER | Count of approved loans |
| rejections | INTEGER | Count of rejected loans |
| expected_defaults | INTEGER | Among approved |
| net_portfolio_value | NUMERIC(16,2) | ₹ value at this threshold |
| created_at | TIMESTAMPTZ | default NOW() |

### `query_log` (Phase 5 only — create the table now, use it later)
| Column | Type | Notes |
|---|---|---|
| id | SERIAL PK | |
| question | TEXT | User's natural language question |
| generated_sql | TEXT | What Gemini produced |
| was_blocked | BOOLEAN | Did the security layer reject it? |
| created_at | TIMESTAMPTZ | default NOW() |

---

## Environment variables required

```
SECRET_KEY=         # Flask sessions — fail-fast if missing
DATABASE_URL=       # Neon full-access connection string
AI_DB_URL=          # Neon read-only role (Phase 5)
GEMINI_API_KEY=     # Gemini API (Phase 5)
```

---

## Hard rules — never violate these

1. **Never describe this project as "AI-powered"** unless referring specifically to the XGBoost
   model or the Gemini NL layer. The decision layer is cost-sensitive thresholding. Say that.

2. **Never suggest React, Docker, FastAPI, or any framework not in the locked stack.**

3. **Never retrain the model.** The artifacts in `model/artifacts/` are final for this project.

4. **Never add features outside the roadmap phases** without explicit instruction. Default answer
   to "should I add X?" is no.

5. **Scope: Phases 0–4 + Phase 6 are the non-negotiable core.** Phase 5 (NL layer) is deferrable.
   Phase 7 is resume writing, not code.

6. **The `.python-version` file must contain `3.11.9`** to match the model artifact versions.

7. **`requirements.txt` must pin `xgboost==2.0.3` and `scikit-learn==1.3.2`** — do not change
   these versions.

8. **Read-only DB role for NL queries** (Phase 5): all Gemini-generated SQL runs on `AI_DB_URL`,
   never on the main `DATABASE_URL`. This is a security requirement, not optional.

---

## Current build phase

**Phase 5 — Deployment and Polish (Days 18–20)**

### Phase 0 — Setup and foundation (Days 1–2) — DONE

Goal: running Flask app + Neon DB connected + loan data loaded.

- [x] Fresh repo created
- [x] Flask skeleton scaffolded (app factory, blueprints, config)
- [x] Neon DB connected + migrations initialized
- [x] `loan_applications` table created
- [x] `portfolio_snapshots` table created
- [x] `query_log` table created
- [x] `data/load_data.py` written
- [x] 133k records loaded into Neon
- [x] Smoke test: Flask starts, DB query returns rows
- [x] `.python-version` = 3.11.9
- [x] `requirements.txt` pinned

### Phase 1 — Scoring + explanation (Days 3–4) — DONE

Goal: working scoring module (load model, score applicant, SHAP reasons) exposed via API.

- [x] `app/models/scoring.py` — `ScoringModel` class + `get_model()` singleton
- [x] `app/models/explainer.py` — `SHAPExplainer` (TreeExplainer) + `get_explainer()` singleton
- [x] `app/decision/adverse_action.py` — `generate_reasons()` (SHAP → plain English)
- [x] `app/decision/pricing.py` — `assign_rate()` risk-band → interest rate
- [x] `app/decision/engine.py` — `DecisionEngine.decide()` single entry point
- [x] `POST /api/score` endpoint in `app/routes/applicant.py` (+ `FEATURE_DEFAULTS` medians)
- [x] `scripts/score_all.py` — batch-scored all 133k rows, wrote back prob/decision/rate
- [x] End-to-end tested: median (APPROVE), high-risk (REJECT), low-risk (APPROVE)

> **IMPORTANT — model uses RAW (unscaled) features.** Despite `scaler.pkl` being a
> project artifact, the XGBoost model was trained on **raw** features. Verified
> empirically: raw scoring reproduces the ~20% dataset default rate and the
> documented median-applicant probability (~0.19); feeding `scaler.transform()`
> output yields nonsensical ~0.60 probabilities and breaks correlation with the
> ground-truth target. `scoring.py` therefore does **not** apply the scaler, and
> SHAP's `TreeExplainer` runs on raw features too, so scorer and explainer agree.
> The scaler is still loaded (`self.scaler`) per the artifact contract but is not
> used in inference. **Do not "fix" this by re-adding scaling.**

### Phase 2 — Decision engine + backtest (Days 5–8) — DONE

Goal: ₹-impact backtesting that proves the decision engine is worth deploying.

- [x] `app/backtest/evaluator.py` — `PortfolioEvaluator` (`evaluate_at_threshold`,
      `evaluate_threshold_range`, `find_optimal_threshold`) + `get_evaluator()` singleton
- [x] Revenue / loss model: revenue = loan_amnt × rate/100 × term_years × 0.5
      (3y short / 5y long); loss = loan_amnt × 0.60 (LGD); reject = 0
- [x] `scripts/run_backtest.py` — pre-computed 41 thresholds (0.10–0.50) into
      `portfolio_snapshots` via idempotent `ON CONFLICT (threshold)` upsert
- [x] Migration `a1c2e3f40512` — unique constraint on `portfolio_snapshots.threshold`
- [x] `GET /api/backtest/summary`, `/api/backtest/threshold/<float>`,
      `/api/backtest/optimal` in `app/routes/portfolio.py`
- [x] `GET /api/applicant/<int:id>`, `/api/applicant/random` (+ `?decision=` filter)
      in `app/routes/applicant.py`

> **NOTE — optimal threshold is ~0.44, not 0.20–0.35.** Under the specified
> revenue model a repaid loan earns up to `rate × term × 0.5` of principal
> (e.g. 19% × 5y × 0.5 ≈ 47.5%) while a default loses only 60% (LGD). The
> break-even default probability is therefore ≈0.44 for long-term top-tier
> loans, so net ₹ value keeps rising until ~0.44 before losses dominate. This is
> a direct consequence of the revenue formula, not a bug. Approval rate at the
> model threshold 0.2282 is 64.7%, matching Phase 1.

### Phase 3 — Dashboard UI (Days 11–14) — DONE

Goal: three working frontend screens wired to the Phase 1/2 APIs. Jinja2 +
vanilla JS + Chart.js (CDN). No React, no build step, no new backend logic.

- [x] `app/templates/base.html` — navy sidebar, top bar (live threshold /
      optimal / model), Chart.js CDN, `{% block %}` tags
- [x] `app/templates/portfolio.html` — 4 metric cards, threshold slider
      (0.10–0.50, default 0.44), two Chart.js charts; cards server-rendered at
      0.44 so the page works without JS
- [x] `app/templates/applicant.html` — decision banner (green/red), 8-feature
      profile table, decision-reason list (+ fallback), SHAP bar chart
- [x] `app/templates/404.html` — clean HTML not-found page
- [x] `app/static/css/main.css` — all custom CSS (single file)
- [x] `app/static/js/charts.js` — portfolio charts (+ vanilla vertical-line
      plugin for optimal/current threshold) and the SHAP bar chart
- [x] `app/static/js/threshold_slider.js` — initial render + fetch on slide
- [x] `GET /` and `/portfolio` → dashboard (`portfolio.py`)
- [x] `GET /applicant/<int:id>`, `GET /applicant/random` (+ `?decision=`) HTML
      pages (`applicant.py`)
- [x] `GET /api/applicant/<int:id>/shap` — fresh top-10 SHAP per request
      (`SHAPExplainer.get_shap_values`)
- [x] Smoke-tested all 7 flows (dashboard, slider @0.23/0.10, applicant
      approve/reject/random, 404)

> **NOTE — applicant routes are split into two blueprints.** Part E asked the
> applicant blueprint to mount at `url_prefix="/applicant"`, but the existing
> `/api/score` and `/api/applicant/*` JSON routes live there and must stay at
> root (hard constraint: APIs unchanged). Resolved by splitting: `applicant_bp`
> (HTML pages) mounts at `/applicant`; `applicant_api_bp` (JSON) stays at root.
> `portfolio_bp` mounts at `url_prefix="/"` and now owns `/` (the old
> `main.index` placeholder moved to `/health`). The scaler is still **not**
> applied anywhere in the inference path (Phase 1 finding preserved).

### Phase 4 — NL Query Layer (Days 15–17) — DONE

- [x] app/nl_query/__init__.py
- [x] app/nl_query/semantic_layer.py — SCHEMA_DESCRIPTION, ALLOWED_TABLES, MAX_RESULT_ROWS=500
- [x] app/nl_query/security.py — 4 guards (validate_sql, is_prompt_injection, sanitize_question, check_question_length)
- [x] app/nl_query/sql_generator.py — generate_sql() via Gemini 2.5 Flash, lazy import, fail-fast on missing key
- [x] app/nl_query/router.py — full pipeline, read-only AI_DB_URL, query_log audit via DATABASE_URL
- [x] app/routes/query.py — GET /query + POST /api/query (single bp, no shared prefix — documented)
- [x] query_bp registered in app/__init__.py
- [x] 'Ask the Loan Book' nav link added to base.html
- [x] app/templates/query.html — textarea, spinner, answer/SQL toggle, results table, BLOCKED badge, 8 example pills
- [x] app/static/js/nl_query.js — vanilla JS, Ctrl+Enter, HTML-escaped table builder, pills without auto-submit
- [x] tests/test_nl_queries.py — 14 cases, no live API/DB calls
- [x] tests/adversarial_queries.md — 10 inputs mapped to defense layer
- [x] requirements.txt — google-generativeai==0.8.5 added
- [x] All 14 tests pass; smoke check confirmed LIMIT 500 appended

> NOTE — blueprint prefix deviation: query_bp uses no shared prefix;
> /query and /api/query declared as explicit paths to keep the API
> sibling to existing /api/* routes. Matches the Phase 3 pattern.

---

## How to run locally

```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Set environment variables (copy .env.example → .env, fill values)

# Run migrations
flask db upgrade

# Start dev server
python flask_app.py
# → http://localhost:5000
```

---

## Deployment (Render + Neon)

- Start command: `gunicorn wsgi:app`
- Build command: `pip install -r requirements.txt && flask db upgrade`
- Python version: set via `.python-version` = `3.11.9`
- All env vars set in Render dashboard (never in `render.yaml` except `OWNER_EMAIL` pattern from ArthaLens)

---

*Last updated: Phase 4 complete*
