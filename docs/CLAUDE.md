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

**Phase 2 — Decision engine (Days 5–8)**

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

*Last updated: Phase 1 complete*
