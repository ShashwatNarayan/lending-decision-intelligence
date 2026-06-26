/* NL query page — vanilla JS, no external libraries (Phase 4).
 *
 * Reads the question, POSTs it to /api/query, and renders the plain-English
 * answer, the generated SQL (toggle), a results table (when >1 row), and a
 * BLOCKED badge when the security layer rejects the query.
 */
(function () {
  "use strict";

  var input = document.getElementById("question-input");
  var submitBtn = document.getElementById("submit-btn");
  var spinner = document.getElementById("spinner");
  var responseSection = document.getElementById("response-section");
  var answerBox = document.getElementById("answer-box");
  var showSqlBtn = document.getElementById("show-sql-btn");
  var sqlBox = document.getElementById("sql-box");
  var resultsTable = document.getElementById("results-table");
  var blockedBadge = document.getElementById("blocked-badge");

  function resetResponse() {
    responseSection.classList.remove("hidden");
    answerBox.textContent = "";
    sqlBox.textContent = "";
    sqlBox.classList.add("hidden");
    showSqlBtn.style.display = "none";
    showSqlBtn.textContent = "Show SQL";
    resultsTable.innerHTML = "";
    blockedBadge.classList.add("hidden");
  }

  function escapeHtml(value) {
    var div = document.createElement("div");
    div.textContent = value === null || value === undefined ? "" : String(value);
    return div.innerHTML;
  }

  function buildTable(rows) {
    if (!Array.isArray(rows) || rows.length === 0) {
      return;
    }
    var columns = Object.keys(rows[0]);
    var html = '<table class="nlq-table"><thead><tr>';
    columns.forEach(function (col) {
      html += "<th>" + escapeHtml(col) + "</th>";
    });
    html += "</tr></thead><tbody>";
    rows.forEach(function (row) {
      html += "<tr>";
      columns.forEach(function (col) {
        html += "<td>" + escapeHtml(row[col]) + "</td>";
      });
      html += "</tr>";
    });
    html += "</tbody></table>";
    resultsTable.innerHTML = html;
  }

  function setLoading(loading) {
    if (loading) {
      spinner.classList.remove("hidden");
      submitBtn.disabled = true;
    } else {
      spinner.classList.add("hidden");
      submitBtn.disabled = false;
    }
  }

  function submitQuestion() {
    var question = input.value.trim();
    resetResponse();

    if (!question) {
      answerBox.textContent = "Please enter a question.";
      return;
    }

    setLoading(true);

    fetch("/api/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: question })
    })
      .then(function (resp) { return resp.json(); })
      .then(function (data) {
        answerBox.textContent = data.answer || "No answer returned.";

        if (data.sql) {
          showSqlBtn.style.display = "inline-block";
          sqlBox.textContent = data.sql;
        }

        if (Array.isArray(data.result) && data.row_count > 1) {
          buildTable(data.result);
        }

        if (data.was_blocked) {
          blockedBadge.classList.remove("hidden");
        }
      })
      .catch(function () {
        answerBox.textContent = "Network error. Please try again.";
      })
      .finally(function () {
        setLoading(false);
      });
  }

  // Toggle SQL visibility.
  showSqlBtn.addEventListener("click", function () {
    var hidden = sqlBox.classList.toggle("hidden");
    showSqlBtn.textContent = hidden ? "Show SQL" : "Hide SQL";
  });

  // Submit handlers.
  submitBtn.addEventListener("click", submitQuestion);
  input.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      submitQuestion();
    }
  });

  // Example pills populate the textarea (no auto-submit).
  document.getElementById("example-pills").addEventListener("click", function (e) {
    if (e.target && e.target.classList.contains("nlq-pill")) {
      input.value = e.target.textContent.trim();
      input.focus();
    }
  });
})();
