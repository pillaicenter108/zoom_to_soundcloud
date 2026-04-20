// API endpoint
const API_URL = "http://127.0.0.1:8000/sync";

// DOM references
const executeBtn = document.getElementById("executeBtn");
const btnContent = document.getElementById("btnContent");
const resultBox  = document.getElementById("resultBox");
const errorBox   = document.getElementById("errorBox");
const errorMsg   = document.getElementById("errorMsg");

/**
 * Reads form values and returns the request payload.
 */
function getFormData() {
  const zoom_account = document.querySelector('input[name="zoom_account"]:checked').value;
  const from_date    = document.getElementById("from_date").value;
  const to_date      = document.getElementById("to_date").value;
  return { zoom_account, from_date, to_date };
}

/**
 * Validates that both date fields are filled in and from <= to.
 * Returns an error string, or null if valid.
 */
function validate(data) {
  if (!data.from_date) return "Please select a From Date.";
  if (!data.to_date)   return "Please select a To Date.";
  if (data.from_date > data.to_date) return "From Date must be on or before To Date.";
  return null;
}

/**
 * Switches the button to a loading state.
 */
function setLoading(isLoading) {
  executeBtn.disabled = isLoading;

  if (isLoading) {
    btnContent.innerHTML = `
      <div class="spinner"></div>
      Running Sync...
    `;
  } else {
    btnContent.innerHTML = `
      <svg class="btn-icon" width="16" height="16" viewBox="0 0 24 24" fill="none">
        <path d="M5 12H19M19 12L12 5M19 12L12 19"
          stroke="white" stroke-width="2.5"
          stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      Execute Sync
    `;
  }
}

/**
 * Hides both result and error boxes.
 */
function clearFeedback() {
  resultBox.classList.add("hidden");
  errorBox.classList.add("hidden");
}

/**
 * Renders a successful API response.
 */
function showResult(data) {
  const badge = document.getElementById("resultBadge");
  const statusText = document.getElementById("resultStatusText");

  // Update status badge
  statusText.textContent = data.status || "success";

  // Color badge based on status
  const isSuccess = (data.status === "success");
  badge.style.background     = isSuccess ? "#dcfce7" : "#fef9c3";
  badge.style.borderColor    = isSuccess ? "#86efac" : "#fde047";
  badge.style.color          = isSuccess ? "#15803d" : "#a16207";

  // Populate stats
  document.getElementById("meetingsFetched").textContent = data.meetings_fetched ?? "—";
  document.getElementById("newUploads").textContent      = data.new_uploads      ?? "—";

  // Populate scrollable logs
  const logsBox   = document.getElementById("logs");
  const logsCount = document.getElementById("logsCount");
  const logs      = Array.isArray(data.logs) ? data.logs : [];

  logsCount.textContent = `${logs.length} ${logs.length === 1 ? "entry" : "entries"}`;

  if (logs.length === 0) {
    logsBox.innerHTML = `<span class="logs-empty">No logs returned.</span>`;
  } else {
    logsBox.innerHTML = logs.map((log, i) => {
      // Auto-color log lines by keyword
      let cls = "log-text";
      const lower = log.toLowerCase();
      if (lower.includes("error") || lower.includes("fail") || lower.includes("❌")) cls += " log-error";
      else if (lower.includes("warn") || lower.includes("skip"))                      cls += " log-warn";
      else if (lower.includes("upload") || lower.includes("success") || lower.includes("✅")) cls += " log-success";
      else if (lower.includes("fetch") || lower.includes("found") || lower.includes("info")) cls += " log-info";

      const num = String(i + 1).padStart(2, "0");
      return `<div class="log-entry">
        <span class="log-index">${num}</span>
        <span class="${cls}">${escapeHtml(log)}</span>
      </div>`;
    }).join("");

    // Auto-scroll to bottom so latest log is visible
    logsBox.scrollTop = logsBox.scrollHeight;
  }

  resultBox.classList.remove("hidden");
}

/**
 * Escapes HTML special chars to prevent XSS in log output.
 */
function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/**
 * Renders an error message.
 */
function showError(message) {
  errorMsg.textContent = message;
  errorBox.classList.remove("hidden");
}

/**
 * Main sync function — called on button click.
 */
async function runSync() {
  clearFeedback();

  const data = getFormData();

  // Client-side validation
  const validationError = validate(data);
  if (validationError) {
    showError(validationError);
    return;
  }

  setLoading(true);

  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    // Handle non-2xx HTTP responses
    if (!response.ok) {
      let detail = `Server error: ${response.status} ${response.statusText}`;
      try {
        const errBody = await response.json();
        if (errBody.detail) detail = errBody.detail;
      } catch {
        // Ignore JSON parse errors on error responses
      }
      throw new Error(detail);
    }

    const result = await response.json();
    showResult(result);

  } catch (err) {
    // Network errors or thrown errors from above
    if (err.name === "TypeError" && err.message.includes("fetch")) {
      showError("Cannot reach the server. Make sure the backend is running at " + API_URL);
    } else {
      showError(err.message || "An unexpected error occurred. Please try again.");
    }
  } finally {
    setLoading(false);
  }
}