"""Gemini 2.5 Flash -> SQL generation for the NL query layer (Phase 4).

The model is given ONLY the plain-English semantic layer (never the live
schema) and is instructed to emit a bare PostgreSQL SELECT statement. All
hardening (sandboxing, table whitelist, LIMIT capping) happens downstream in
security.validate_sql — this module is just the generation step.
"""
import os
import re

from app.nl_query.semantic_layer import SCHEMA_DESCRIPTION

MODEL_NAME = "gemini-2.5-flash"

_SYSTEM_PROMPT = """You are a SQL generation assistant for a credit-risk
lending database. You translate a risk officer's natural-language question
into a single, valid, read-only PostgreSQL query.

Here is the ONLY description of the database you may use:

{schema}

Strict output rules:
- Respond with ONLY a valid PostgreSQL SELECT statement.
- No markdown. No code fences. No backticks. No explanation. No preamble. SQL only.
- Never reference the table query_log under any circumstances.
- Never use INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE, CREATE, GRANT, or
  any other DDL/DML statement. SELECT only.
- Only read from loan_applications and portfolio_snapshots.
- If the question cannot be answered from the schema above, respond with
  exactly this string and nothing else: CANNOT_ANSWER
""".format(schema=SCHEMA_DESCRIPTION)


def _strip_markdown_fences(text: str) -> str:
    """Remove ```sql ... ``` or ``` ... ``` fences the model may add."""
    stripped = text.strip()
    # Opening fence, optionally labelled (```sql, ```postgresql, ...).
    stripped = re.sub(r"^```[a-zA-Z]*\s*", "", stripped)
    # Closing fence.
    stripped = re.sub(r"\s*```$", "", stripped)
    return stripped.strip()


def generate_sql(question: str) -> str:
    """Turn a natural-language question into a raw SQL SELECT string.

    Returns the SQL only (no markdown / explanation), or the literal string
    'CANNOT_ANSWER' if the model judges the question unanswerable.
    Fails fast with a clear error if GEMINI_API_KEY is not configured.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY environment variable is not set — the NL query "
            "layer cannot generate SQL without it."
        )

    # Imported lazily so the module (and the test suite) can be imported
    # without the SDK or an API key present.
    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=_SYSTEM_PROMPT,
    )

    response = model.generate_content(question)
    return _strip_markdown_fences(response.text or "")
