"""SQL sandboxing and prompt-injection defense for the NL->SQL layer (Phase 4).

This is the second line of defense. The first is the read-only database role
(AI_DB_URL) — even a malicious query physically cannot mutate data. These
functions add a validation layer on top so we never even *send* a dangerous
statement, and so we cap result size and reject obvious prompt-injection text.

Every guard raises ValueError with a human-readable message on violation.
"""
import re

from app.nl_query.semantic_layer import ALLOWED_TABLES, MAX_RESULT_ROWS

# Symbol-style tokens that have no word boundaries — checked as substrings.
_FORBIDDEN_SYMBOLS = ["--", "/*", "*/"]

# Word-style forbidden tokens — checked with word-boundary regex so we don't
# false-positive on substrings inside legitimate column names.
_FORBIDDEN_WORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "TRUNCATE", "ALTER", "CREATE",
    "GRANT", "REVOKE", "EXECUTE", "EXEC", "INFORMATION_SCHEMA", "PG_CATALOG",
    "SLEEP", "PG_SLEEP",
]

# Pull table names out of FROM / JOIN clauses.
_TABLE_RE = re.compile(r"\b(?:FROM|JOIN)\s+([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE)

# Prompt-injection phrases (lower-cased substring match).
_INJECTION_PATTERNS = [
    "ignore previous", "ignore above", "disregard", "you are now",
    "new instructions", "system prompt", "forget everything", "act as",
]


def validate_sql(sql: str) -> str:
    """Validate and normalize an LLM-generated SQL statement.

    Returns the cleaned, safe SQL string. Raises ValueError on any violation.
    """
    if not sql or not sql.strip():
        raise ValueError("Empty SQL statement.")

    # 1. Normalize whitespace to single spaces.
    cleaned = re.sub(r"\s+", " ", sql.strip())

    # 2. Must start with SELECT.
    if not re.match(r"(?i)^SELECT\b", cleaned):
        raise ValueError("Only SELECT statements are allowed.")

    upper = cleaned.upper()

    # 3a. Symbol tokens (comments) — substring match.
    for sym in _FORBIDDEN_SYMBOLS:
        if sym in cleaned:
            raise ValueError(f"Disallowed token in query: '{sym}'.")

    # 3b. The 'XP_' extended-procedure prefix (trailing char is a word char,
    # so match the prefix only).
    if re.search(r"\bXP_", upper):
        raise ValueError("Disallowed token in query: 'XP_'.")

    # 3c. Word-boundary forbidden keywords.
    for word in _FORBIDDEN_WORDS:
        if re.search(r"\b" + re.escape(word) + r"\b", upper):
            raise ValueError(f"Disallowed keyword in query: '{word}'.")

    # 4. Only reference whitelisted tables.
    referenced = _TABLE_RE.findall(cleaned)
    for table in referenced:
        if table.lower() not in ALLOWED_TABLES:
            raise ValueError(
                f"Query references a table that is not permitted: '{table}'."
            )

    # 5. Add a LIMIT if none is present (case-insensitive).
    if not re.search(r"\bLIMIT\b", upper):
        cleaned = cleaned.rstrip(";").rstrip()
        cleaned = f"{cleaned} LIMIT {MAX_RESULT_ROWS}"

    # 6. Return the cleaned, safe SQL.
    return cleaned


def is_prompt_injection(question: str) -> bool:
    """Return True if the question contains a known prompt-injection phrase."""
    lowered = (question or "").lower()
    return any(pattern in lowered for pattern in _INJECTION_PATTERNS)


def sanitize_question(question: str) -> str:
    """Strip, truncate to 500 chars, and remove non-printable characters."""
    cleaned = (question or "").strip()
    cleaned = cleaned[:500]
    cleaned = "".join(ch for ch in cleaned if ch.isprintable())
    return cleaned


def check_question_length(question: str) -> None:
    """Raise ValueError if the question is shorter than 5 characters."""
    if len((question or "").strip()) < 5:
        raise ValueError("Question is too short. Please ask a fuller question.")
