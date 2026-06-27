# Lending Decision Intelligence Platform

A B2B credit decisioning tool that scores loan applicants, makes approve/reject decisions using cost-sensitive thresholding, and quantifies the ₹ portfolio impact of any threshold choice.

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.1-000000?logo=flask&logoColor=white)
![XGBoost](https://img.shields.io/badge/XGBoost-2.0-EB5E28)
![SHAP](https://img.shields.io/badge/SHAP-0.44-4B8BBE)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Neon-4169E1?logo=postgresql&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash-8E75B2?logo=googlegemini&logoColor=white)
![Render](https://img.shields.io/badge/Deploy-Render-46E3B7?logo=render&logoColor=white)

---

## What it does

This is a decisioning tool for loan officers and risk analysts, not for borrowers. An XGBoost model predicts the probability of default for each applicant, and a cost-sensitive decision engine converts that probability into an approve/reject decision and a risk-based interest rate for approvals. For every rejection, SHAP values generate plain-English reasons that trace directly back to the factors that drove the outcome. A portfolio dashboard lets an analyst move the decision threshold and watch the net ₹ portfolio value shift across 133,018 historical applications, and a Gemini-powered natural-language query layer lets analysts ask plain-English questions about the loan book. It is not consumer-facing and not "AI-powered" — the model is XGBoost, the decision layer is cost-sensitive thresholding.

---

## Live demo

[https://YOUR-RENDER-URL.onrender.com](https://YOUR-RENDER-URL.onrender.com)

> Note: replace this URL after deployment.

---

## Why this is different from a standard ML project

This matters more than the model itself:

- **The model predicts. The platform decides.** A classifier outputs a probability — `0.31`. That is not a decision. The platform wraps the model in a decision layer that converts a probability into an action (approve/reject), a price (interest rate), and a justification (reasons). The cut-off is chosen by business cost, not by a default `0.5`, which is what makes the output something a risk team can act on.
- **Every rejection produces a reason traceable to a SHAP value.** No black-box "computer says no." Each adverse-action reason is generated from the SHAP contributions computed for that specific applicant, so a reason can always be tied back to a concrete number. That traceability is what makes the decisions defensible to an auditor or a rejected applicant.
- **The threshold slider turns "AUC = 0.73" into a ₹ number.** Model metrics don't move a business. The dashboard reframes the threshold choice as net portfolio value in rupees, so the trade-off between approving more loans and absorbing more defaults becomes a money decision. A risk team can own a rupee figure in a way it can never own an AUC.

---

## Backtesting results

Backtested across all 133,018 historical applications under a revenue model of `loan_amnt × rate × term × 0.5` for repaid loans and a 60% loss given default.

| Metric | Value |
|---|---|
| Optimal threshold | 0.44 |
| Net portfolio value at optimal | ₹211.3M (₹211,291,304) |
| Approval rate at optimal | 89.77% |
| vs naive 0.5 threshold | +₹3.0M |

The optimum sits at 0.44 — not a textbook 0.20–0.35 — because of the revenue model. A repaid loan earns up to ~47% of principal (e.g. 19% × 5y × 0.5) while a default loses only 60% of principal (LGD), so net ₹ value keeps rising as the threshold loosens until the break-even default probability of ≈0.44 is reached, after which losses dominate. This is a property of the cost model, not the classifier. At the model's F1-optimal threshold of 0.2282, the approval rate is 64.7%.

---

## Architecture

```
CSV (133k records)
    ↓
XGBoost Scorer  →  P(default) per applicant
    ↓
Decision Engine →  APPROVE / REJECT + risk-based rate
    ↓
SHAP Explainer  →  Plain-English rejection reasons
    ↓
┌─────────────────────────────────┐
│  Flask Web App                  │
│  ├── Portfolio Dashboard        │
│  ├── Applicant Lookup           │
│  └── NL Query (Gemini SQL)      │
└─────────────────────────────────┘
    ↓
PostgreSQL on Neon (133k rows)
```

---

## How the decision engine works

**Cost-sensitive thresholding — why 0.2282, not 0.5.** A default `0.5` cut-off implicitly assumes that approving a borrower who defaults costs the same as rejecting a borrower who would have repaid. In lending that is false: a default loses principal, while a wrongly-rejected applicant only loses the spread you would have earned. Because the two errors carry very different costs — and because the dataset is imbalanced at ~20% default — the right cut-off sits well below `0.5`. This platform uses a pre-computed threshold of **0.2282**: an applicant is approved only when their predicted probability of default falls below it. The threshold is a tunable business lever, not a model constant, which is exactly what the dashboard slider exposes.

**Pricing bands — five tiers on a base rate.** Approved applicants are priced by risk. Starting from a `BASE_RATE` of 8.0% (a placeholder for the policy rate plus a spread), the engine adds a risk premium that grows as predicted default probability rises: +2.0% for the lowest-risk tier (P < 0.05), then +4.0% (P < 0.10), +6.5% (P < 0.15), +9.0% (P < 0.20), and +11.0% for the borderline tier just under the approval threshold. Lower predicted risk earns a cheaper rate; applicants near the cut-off pay the most. Rejected applicants receive no rate.

**SHAP → adverse-action reasons.** For each applicant the platform computes SHAP values with a `TreeExplainer`, which attribute the prediction to individual features. The factors are ranked by the magnitude of their contribution, tiny contributors are dropped, and the strongest ones are mapped to plain-English statements ("Debt-to-income ratio exceeds acceptable thresholds," "Credit score is below the threshold for approval"). Rejections surface the factors pushing risk up; approvals surface the factors holding it down. The output is capped at a handful of reasons so it stays readable, and every reason is anchored to a real SHAP contribution rather than a generic template.

**₹ impact calculation.** The portfolio view turns a threshold into money. For any threshold, the engine partitions the 133k historical applications into approvals and rejections, then estimates value on the approved book: interest revenue earned on loans that repay, minus losses on loans that default, where each default is charged a loss given default (LGD) of 60% of principal (i.e. 40% is assumed recovered). Summing revenue minus expected loss across the approved set yields a single net portfolio value in rupees, letting an analyst compare thresholds on the metric that actually matters.

---

## Security architecture (NL query layer)

- **Read-only database role:** all Gemini-generated SQL runs on a separate read-only Neon connection (`AI_DB_URL`). Even if the LLM produces malicious SQL, it physically cannot modify data.
- **SQL validation:** generated SQL is checked for forbidden tokens (DROP, INSERT, UPDATE, DELETE, pg_sleep, information_schema, etc.) and table allowlisting before execution.
- **Prompt injection defense:** user input is scanned for known injection patterns before being passed to Gemini.
- **Query audit log:** every query (blocked or executed) is logged to the `query_log` table for forensic review.

---

## API reference

### JSON API

| Method | Path | Description |
|---|---|---|
| POST | `/api/score` | Score an applicant (any subset of the 30 features; missing values default to dataset medians). Returns decision, default probability, assigned rate, reasons, and top SHAP factors. |
| GET | `/api/backtest/summary` | All pre-computed threshold snapshots plus the optimal threshold. |
| GET | `/api/backtest/optimal` | Optimal threshold and the ₹ portfolio value it produces. |
| GET | `/api/backtest/threshold/<t>` | Portfolio metrics simulated at a custom threshold `t`. |
| GET | `/api/applicant/<id>` | Full stored decision + 30 features for a single application by id. |
| GET | `/api/applicant/random` | A random scored applicant (`?decision=APPROVE\|REJECT` to filter). |
| GET | `/api/applicant/<id>/shap` | Fresh top-10 SHAP attribution for one applicant (powers the bar chart). |
| POST | `/api/query` | Natural-language query endpoint (Phase 4): turns a plain-English question into SQL via Gemini and executes it on the read-only connection. |

### Web pages

| Method | Path | Description |
|---|---|---|
| GET | `/` | Portfolio dashboard — metric cards, threshold slider, ₹-impact charts. |
| GET | `/applicant/<id>` | Single-applicant detail page (decision banner, profile, SHAP chart). |
| GET | `/applicant/random` | Redirects to a random applicant (`?decision=` to filter). |
| GET | `/query` | Natural-language query page — ask plain-English questions about the loan book. |

---

## Project structure

```
lending-decision-intelligence/
├── app/                  # Flask application (factory + blueprints)
│   ├── models/           # XGBoost scoring + SHAP explainer
│   ├── decision/         # Threshold engine, pricing, adverse-action reasons
│   ├── backtest/         # ₹-based threshold backtesting
│   ├── nl_query/         # Gemini NL→SQL engine, security layer, router
│   ├── routes/           # HTTP blueprints + JSON API
│   ├── templates/        # Jinja2 server-rendered pages
│   └── static/           # CSS + vanilla JS (Chart.js dashboard)
├── data/                 # LendingClub CSV + one-time DB loader
├── model/artifacts/      # Pinned XGBoost model, scaler, feature list, threshold
├── migrations/           # Flask-Migrate / Alembic schema migrations
├── scripts/              # One-time batch scorer (score_all.py)
├── tests/                # Unit tests (scoring, decision engine, NL queries)
├── docs/                 # Project context, roadmap, build notes
├── flask_app.py          # Dev entry point (app.run)
├── wsgi.py               # Production entry point (gunicorn wsgi:app)
└── requirements.txt      # Pinned dependencies
```

---

## Tech stack

| Layer | Technology |
|---|---|
| ML model | XGBoost (scikit-learn 1.3.2, xgboost 2.0.3) |
| Explainability | SHAP (TreeExplainer) |
| Backend | Python 3.11 + Flask |
| Database | PostgreSQL on Neon |
| NL query | Gemini 2.5 Flash |
| Frontend | Jinja2 + vanilla JS + Chart.js |
| Deployment | Render |

---

## Local setup

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

## Dataset

LendingClub public dataset. 133,018 records. 30 engineered features. Default rate: 20.25%. Source: public domain.

---

## Author

**Shashwat Narayan**
Building decision systems that turn model outputs into accountable business actions.
[GitHub](https://github.com/your-username)
