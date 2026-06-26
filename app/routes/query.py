"""NL query routes (Phase 4).

GET  /query       -> the 'Ask the Loan Book' page (static form, POSTs via JS).
POST /api/query   -> run the governed NL->SQL pipeline and return JSON.

Note: the spec names a '/query' prefix, but the JSON endpoint must live at
'/api/query' (sibling to the existing /api/* routes), so the two routes are
declared with explicit paths on a single blueprint rather than a shared prefix.
"""
import logging

from flask import Blueprint, jsonify, render_template, request

from app.nl_query.router import answer_question

query_bp = Blueprint("query", __name__)

logger = logging.getLogger(__name__)


@query_bp.route("/query")
def ask_page():
    """Render the static NL query page; all work happens via POST /api/query."""
    return render_template("query.html")


@query_bp.route("/api/query", methods=["POST"])
def api_query():
    """Accept {"question": "..."} and return the full pipeline result as JSON."""
    data = request.get_json(silent=True) or {}
    question = data.get("question", "")

    try:
        result = answer_question(question)
        result["success"] = True
        return jsonify(result)
    except ValueError as exc:
        # Security-layer rejection (too short, sandbox violation, etc.).
        return jsonify(
            success=False,
            answer=str(exc),
            was_blocked=True,
            sql=None,
            result=[],
            row_count=0,
        )
    except Exception:
        logger.error("Unexpected failure in /api/query", exc_info=True)
        return (
            jsonify(
                success=False,
                answer="An error occurred processing your query. "
                "Please try again.",
                was_blocked=False,
                sql=None,
                result=[],
                row_count=0,
            ),
            500,
        )
