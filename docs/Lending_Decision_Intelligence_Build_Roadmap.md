# Lending Decision Intelligence — Phase-Wise Build Roadmap

> **Time budget:** ~3 weeks (21 days)
> **Hard deadline context:** FICO visits ~Jul 3, MathCo ~Jul 11, BNY/CME/Fractal late Jul
> **Principle:** ship a complete decision-engine MVP fast, then layer the NL query as a bonus. If time runs short, cut the NL phase — the core is already a full, impressive project.

---

## What you're reusing (this is why it's 3 weeks, not 8)

Before jumping into phases, here's the honest inventory of what you already own and what's genuinely new code.

### From Loan Default → reuse directly

| Asset | What it gives you | Effort to reuse |
|---|---|---|
| XGBoost model + training pipeline | The prediction engine — P(default) for every applicant. **This is the brain of the new project.** You don't retrain from scratch; you refine. | ~1 day to clean up and modularize |
| 133k-record dataset | Your entire data layer. Already cleaned, feature-engineered, validated. | Zero — it's ready |
| 10 domain-specific features | Income ratios, credit history length, debt-to-income, etc. Already built and SHAP-validated. | Zero |
| SHAP integration | Per-borrower explanations already working. You'll reformat the output, not rebuild the explainer. | ~half a day to reshape output |
| 5-fold CV + evaluation pipeline | Your backtesting foundation. You'll extend it from "AUC" to "₹ impact," but the scaffolding exists. | ~1 day to extend |

### From ArthaLens → reuse directly

| Asset | What it gives you | Effort to reuse |
|---|---|---|
| Flask app skeleton | Routes, blueprints, config, error handling — the entire web framework. Don't start a new Flask app; fork this one. | ~half a day to strip and adapt |
| PostgreSQL setup (Neon) | Database connection, migrations, config. Identical infra, different schema. | ~half a day for new schema |
| Gemini 2.5 Flash NL engine | Intent routing, prompt templates, response formatting. The "talk to your data" feature, almost plug-and-play. | ~2 days to re-point at loan schema |
| Read-only DB role + SQL sandboxing | **Your single biggest differentiator.** The security architecture — user-scoping, auto-injected IDs, injection defense. Copy wholesale. | ~half a day to adapt |
| Render deployment pipeline | Procfile, requirements.txt, env vars, Neon connection string. You've done this deployment before — it's muscle memory. | ~2-3 hours |
| Frontend patterns | Jinja2 templates, CSS patterns, page layouts you've already built. You're not designing from zero. | Continuous reuse |

### What's genuinely new code

| Component | Why it's new | Estimated effort |
|---|---|---|
| **Decision layer** (approve/reject logic, cost-sensitive thresholding) | Your current project predicts; this one *decides*. The threshold-to-₹ mapping doesn't exist yet. | ~3 days |
| **Risk-based pricing engine** (score-band → interest rate) | New business logic — mapping risk scores to rate tiers. Conceptually simple, but needs careful calibration. | ~1 day |
| **Adverse-action engine** (SHAP → human-readable rejection reasons) | You have SHAP values; you don't have the "translate top-3 SHAP features into plain English sentences" layer. | ~1.5 days |
| **Portfolio impact dashboard** (₹ metrics, threshold slider, batch view) | The frontend — charts, the interactive slider, the summary cards. New UI code. | ~3 days |
| **Backtesting framework** (₹-based evaluation, not just AUC) | Extending your existing eval from "model accuracy" to "what would this threshold have cost/earned on historical data." | ~2 days |
| **Applicant lookup screen** (single-borrower view with decision + reasons) | A new page, but structurally similar to ArthaLens transaction views. | ~1 day |

**Total genuinely new work: ~12 days of focused coding.** The rest is assembly from pieces you own.

---

## Tech Stack

No new frameworks. No new languages. No learning curve. That's deliberate — your time goes into the *decision logic and business framing*, not fighting unfamiliar tools.

| Layer | Technology | Why this, specifically |
|---|---|---|
| **ML / prediction** | XGBoost, scikit-learn, SHAP | Already built, already validated. Switching to a different model would be pure waste — the project's value is the *decision layer on top*, not a fancier model underneath. |
| **Explainability** | SHAP (shapley values) | Industry standard for model explainability. Already integrated in your Loan Default project. Regulators (RBI, US FCRA) accept SHAP-based explanations — that's a real talking point in interviews. |
| **Backend** | Python + Flask | Your entire existing codebase is Flask. Switching to FastAPI or Django would cost you days for zero placement benefit. Flask is fine. |
| **Database** | PostgreSQL (hosted on Neon) | Same as ArthaLens. Neon's free tier handles this dataset easily. You already know the connection patterns, the read-only role setup, the migration flow. |
| **NL query layer** | Gemini 2.5 Flash API | Already integrated in ArthaLens. Intent routing, SQL generation, response formatting — all existing code. The prompt templates change (loan schema instead of transaction schema), but the architecture is identical. |
| **Frontend** | Jinja2 templates + vanilla JS + Chart.js or Plotly | No React, no frontend framework. Jinja2 is what ArthaLens uses. Chart.js for the interactive threshold slider and portfolio charts — lightweight, CDN-loaded, no npm/build step. Plotly is an alternative you already have experience with. |
| **Deployment** | Render (free tier) + Neon PostgreSQL | Identical to your ArthaLens deployment. Same Procfile pattern, same environment variable setup, same CI flow. You could deploy this in your sleep. |
| **Version control** | Git + GitHub | Obviously. But worth noting: make the repo public from day one. Recruiters will look at it. Clean commit history matters — commit by feature, not "fixed stuff." |

### What you are deliberately NOT using (and why)

| Temptation | Why you skip it |
|---|---|
| FastAPI / Django | Learning curve for zero benefit. Flask does everything this project needs. |
| React / Next.js frontend | Massive overkill. Jinja2 + vanilla JS handles the dashboard. A React app would triple your frontend time. |
| Docker / Kubernetes | Impressive on paper, irrelevant for a solo portfolio project. Render handles deployment without containers. |
| AWS / GCP / Azure | Same — cloud infra complexity adds nothing to the project's value. Render + Neon is simpler and free. |
| A different ML model (LightGBM, neural net) | The model isn't the point. The *decision layer on top of the model* is the point. Swapping XGBoost for something else wastes time and confuses the narrative. |

---

## The Phases

### Phase 0 — Setup and foundation (Day 1–2)

**Goal:** a running Flask app connected to a Neon database with your loan data loaded, before you write any new logic.

**What happens:**
- Fork/copy your ArthaLens Flask skeleton into a new repo. Strip out the personal-finance-specific routes and templates, keep the core structure: app factory, blueprints, config, database connection, the read-only role setup, error handling.
- Create a new Neon database (or a new schema in your existing Neon instance). Design the schema: a `loan_applications` table (your 133k records + a few added columns: loan_amount, interest_rate_assigned, decision, decision_reasons), a `portfolio_snapshots` table (for storing threshold simulation results), and a `query_log` table (for the NL layer later).
- Write a one-time data loading script: read your existing Loan Default CSV/Parquet, add synthetic but defensible columns (loan_amount derived from income × a realistic multiplier, a margin column), load into PostgreSQL.
- Verify: Flask app starts, connects to Neon, you can query the loan table. Commit.

**Reuse:** ~80% of this phase is copy-paste from ArthaLens. The schema design and data loading script are new but straightforward.

---

### Phase 1 — The prediction layer (Day 3–4)

**Goal:** your existing XGBoost model running inside the Flask app, scoring any applicant and returning P(default) + SHAP explanations.

**What happens:**
- Take your trained XGBoost model (the `.pkl` or `.json` file). If you don't have a saved model artifact, retrain on the 133k dataset and save it. This is existing code — you're just packaging it.
- Build a `scoring` module: takes an applicant's features as input → runs through the model → returns `{ probability: 0.34, shap_values: {...} }`. This is a clean function, not a route yet.
- Build the SHAP → human-readable reasons translator. This is genuinely new. Take the top 3 SHAP contributors for a given applicant and map them to plain English. For example: if `debt_to_income_ratio` has the highest SHAP value pushing toward default, the reason becomes "High debt relative to income." You'll need a mapping dictionary — ~15-20 feature-to-English entries. Simple but important.
- Test: pick 5 applicants from your dataset, score them, verify the probabilities are reasonable and the reasons make sense. Commit.

**Reuse:** the model and SHAP code are directly from Loan Default. The English-reason mapper is new (~50 lines of code).

---

### Phase 2 — The decision layer (Day 5–8) ⭐ This is the core — the thing your current projects don't have

**Goal:** the system doesn't just *predict* default — it *decides* approve/reject, *prices* the loan, and *quantifies the ₹ impact* of that decision.

**What happens — three sub-components:**

**2A. Cost-sensitive threshold engine (~2 days)**
- Define a cost matrix: what does a false approval cost (the loan amount × loss-given-default, say 60%)? What does a false rejection cost (lost interest revenue on a good borrower)?
- Build a function that, given a threshold (e.g., "reject anyone with P(default) > 20%"), computes: how many approved, how many rejected, total expected loss in ₹, total expected revenue in ₹, net portfolio value.
- Make the threshold a parameter, not a hardcoded number. This is what powers the slider on the dashboard — the user drags it, and the ₹ numbers update.
- Run this across a range of thresholds (5% to 50% in steps of 1%) and store the results. This becomes the data behind the portfolio impact chart.

**2B. Risk-based pricing engine (~1 day)**
- Create score bands: P(default) 0-10% → 10% interest, 10-20% → 13%, 20-30% → 16%, 30%+ → reject (or 20% for high-risk-appetite mode).
- For each approved applicant, assign a rate based on their band. Calculate expected revenue = loan_amount × assigned_rate × (1 - P(default)).
- This is simple business logic — maybe 30-40 lines — but it's what transforms "a model" into "a lending business."

**2C. Adverse-action decision engine (~1 day)**
- For every rejected applicant (or every applicant, period), generate a decision record: `{ decision: "REJECT", probability: 0.34, rate_offered: null, reasons: ["High debt-to-income ratio", "Credit history under 2 years", "Loan amount large relative to income"], shap_values: {...} }`.
- For approved applicants: `{ decision: "APPROVE", probability: 0.08, rate_offered: "10%", reasons: ["Stable income", "Long credit history"], shap_values: {...} }`.
- Store these in the database. This is your audit trail — and it's a real regulatory requirement in lending.

**Test:** run the full pipeline on your 133k records. Verify: at threshold=20%, what's the approval rate? What's the total expected loss? Do the reasons make sense for a sample of rejected applicants? Commit.

**Reuse:** the model scoring is from Phase 1. The cost-matrix logic, pricing engine, and decision-record generator are new — this is the ~3 days of genuinely new thinking in the project.

---

### Phase 3 — The backtesting framework (Day 9–10)

**Goal:** prove your system works by replaying history and showing the ₹ outcome — this is your "accuracy" story, but in money, not AUC.

**What happens:**
- Split your 133k records into train (80%) and test (20%), just like your existing Loan Default setup.
- On the test set, run the full decision pipeline (Phase 2) at several thresholds.
- For each threshold, compute on the test set (where you *know* who actually defaulted): actual defaults among approved applicants, actual ₹ lost, actual ₹ earned from interest on good loans, net ₹ outcome.
- Compare your system's decisions against a naive baseline: "approve everyone" and "approve only below 10% risk." Show that your optimized threshold beats both.
- Package the results into a summary: "At the optimal threshold of X%, the system would have approved Y applicants, earned ₹A in interest, lost ₹B to defaults, for a net value of ₹C — compared to ₹D under a naive approve-all strategy." That sentence, with real numbers from your backtest, is what you say in interviews.

**Reuse:** the train/test split and evaluation scaffolding are from Loan Default. The ₹-based evaluation is new but uses the Phase 2 functions directly.

---

### Phase 4 — The dashboard frontend (Day 11–14)

**Goal:** the three screens from the mockup I showed you, fully functional.

**What happens — three pages:**

**4A. Portfolio view (the main dashboard)**
- Top: four metric cards (approval rate, applicants approved, expected loss, net portfolio value) — these update live as the threshold slider moves.
- Middle: the threshold slider. When dragged, it calls an API endpoint that re-runs the Phase 2 cost-matrix at the new threshold and returns updated ₹ numbers. Use a simple fetch() call + vanilla JS to update the cards without a page reload.
- Bottom: a chart (Chart.js bar or line) showing ₹ net value across the threshold range — so the user can visually see the "sweet spot."
- Reuse: Jinja2 page structure from ArthaLens. The chart is new but Chart.js is ~10 lines of JS to set up.

**4B. Applicant lookup**
- A dropdown or search box. Select an applicant → see their details, the decision (approve/reject badge), the assigned rate (if approved), and the plain-English reasons.
- Reuse: structurally identical to how ArthaLens shows transaction details. Different data, same page pattern.

**4C. Batch upload (optional, do only if time permits)**
- Upload a CSV of new applicants → score them all → show results in a table with downloadable output.
- This is a "nice to have." Skip it if you're running behind.

**Frontend notes:**
- Don't over-design. Clean, functional, readable. The mockup I showed you is the target — not a pixel-perfect SaaS product.
- Mobile responsiveness is not important. Recruiters will look at this on a laptop.
- A loading spinner for the NL queries (Phase 5) is worth adding — it signals the system is "thinking," which is a better UX than a frozen screen.

---

### Phase 5 — The NL query layer (Day 15–17) — your ArthaLens transplant

**Goal:** the "ask the loan book" box from the mockup, powered by your existing governed NL→SQL architecture.

**What happens:**
- Copy the NL engine module from ArthaLens wholesale: the intent router, the Gemini API call, the SQL generation, the response formatter.
- Write a **semantic layer** (a structured description of your loan schema): what each table is, what each column means in business terms, what joins are valid. This is a text file / dict that gets injected into the Gemini prompt so it knows what columns exist and what they mean. ~30 minutes of careful writing.
- Adapt the prompt templates: swap "transactions" and "categories" language for "loan applications," "default probability," "approval decisions," "rejection reasons."
- Critically: the **security architecture copies directly** — read-only DB role, auto-injected user scoping, SQL validation before execution. This is the part recruiters and interviewers will ask about. Don't skip it or simplify it.
- Build the query box UI: an input field + submit button + response area. Vanilla JS fetch to a `/query` endpoint. Display the answer (and optionally the generated SQL, behind a "show SQL" toggle — great for demos).
- Write ~15-20 test queries and verify they work: "how many applicants were rejected last month?", "what's the average loan amount for approved applicants?", "which risk band has the highest default rate?" Also test adversarial queries: "DROP TABLE loan_applications" — verify it's blocked. That blocking demo is interview gold.

**Reuse:** ~70% of this phase is direct ArthaLens code. The new work is the schema description and prompt adaptation.

**If you run out of time:** this entire phase can be deferred. The project is complete and impressive without it. The NL layer is a bonus that elevates it from "strong" to "exceptional."

---

### Phase 6 — Deployment and polish (Day 18–20)

**Goal:** live at a public URL, clean repo, recruiter-ready.

**Deployment (should take ~3 hours, not a day — you've done this before):**
- Render setup: new web service, connect GitHub repo, set environment variables (Neon connection string, Gemini API key, Flask secret key). Same pattern as ArthaLens.
- Procfile: `web: gunicorn app:create_app()` — identical structure.
- `requirements.txt`: pin versions. You know the drill.
- Neon: your database is already cloud-hosted. No migration needed — it's the same Neon instance (or a new free one; Neon allows multiple projects on free tier).
- Test the deployed version end-to-end: portfolio slider works, applicant lookup works, NL queries work, adversarial queries are blocked. Fix any environment-specific bugs (these are usually just missing env vars or path issues).
- Pick a clean URL. If you can get a custom domain, great. If not, `lending-decision-intel.onrender.com` or similar is fine.

**Polish (the remaining 2 days):**

*README (critical — recruiters read this before they read your code):*
- One paragraph: what the project does (the "simple words" explanation).
- A "try it live" link to the deployed URL.
- Architecture section: a simple diagram showing data flow (CSV → model → decision layer → dashboard / NL layer). Not a fancy diagram tool — a clean text description or a single image is fine.
- Security section: explicitly call out the read-only role, SQL sandboxing, prompt injection defense. This is your differentiator — don't bury it.
- Backtesting results: the headline numbers ("at optimal threshold, net portfolio value of ₹X vs ₹Y under naive strategy").
- Tech stack list.
- No "future work" section that's longer than the "what it does" section. That signals you didn't finish.

*Code cleanup:*
- Remove debug prints, commented-out code, hardcoded paths.
- Add docstrings to the scoring module, the decision engine, and the NL query handler — not every function, just the important ones.
- Clean commit history: if it's messy, do a squash-and-rebase before making the repo public. Commit messages should read like a changelog, not a diary.

*One demo recording (optional but high-impact):*
- A 2-minute screen recording: open the dashboard → drag the slider → show the ₹ change → look up an applicant → show the rejection reason → type a natural language question → get the answer → type a malicious query → show it being blocked.
- Embed in the README or link from it. Recruiters who don't want to visit the live URL will watch this.

---

### Phase 7 — Resume integration (Day 20–21)

Not a coding phase — a framing phase. Arguably the highest-ROI 2 hours in the whole project.

**Write 3 resume bullets in the language of money and decisions, not model metrics:**

The bullets should follow this pattern: **action → mechanism → ₹/business result.**

Here's the direction (you'll tailor the exact numbers from your backtest results):

- Bullet 1 (the decision layer): something like "Engineered a cost-sensitive lending decision engine that optimizes approve/reject thresholds by expected ₹ portfolio value, improving net returns by X% over a naive baseline across 133k historical applications."
- Bullet 2 (the explainability / compliance layer): something like "Built a regulatory-grade adverse-action system generating per-borrower rejection reasons from SHAP explanations, supporting fair-lending compliance requirements."
- Bullet 3 (the NL + security layer): something like "Deployed a governed NL→SQL query layer with read-only DB role, SQL sandboxing, and prompt-injection defense — enabling non-technical risk officers to query the loan book in plain English."

Notice: no AUC, no recall, no F1-score in any of these. Every bullet talks about a **decision**, a **business outcome**, or a **safety property**. That's the reframing the strategy document called for.

---

## Phase summary at a glance

| Phase | Days | What you ship | Reuse % |
|---|---|---|---|
| 0 — Setup | 1–2 | Running Flask app + Neon DB with loan data loaded | ~80% from ArthaLens |
| 1 — Prediction | 3–4 | XGBoost scoring + SHAP → English reasons | ~90% from Loan Default |
| 2 — Decision | 5–8 | Approve/reject + pricing + ₹ impact ⭐ | ~10% — mostly new |
| 3 — Backtest | 9–10 | ₹-based evaluation proving the system works | ~50% from Loan Default eval |
| 4 — Dashboard | 11–14 | Three working screens with live threshold slider | ~40% from ArthaLens templates |
| 5 — NL layer | 15–17 | "Ask the loan book" with full security | ~70% from ArthaLens |
| 6 — Deploy + polish | 18–20 | Live URL + clean README + demo recording | ~90% from ArthaLens deploy |
| 7 — Resume | 20–21 | 3 bullets in business language | New writing, but guided |

**The cut line:** if time pressure hits, Phase 5 (NL layer) is the one you defer. Phases 0–4 + 6 give you a complete, deployable, impressive project. Phase 5 makes it exceptional but isn't required for the core story to land.
