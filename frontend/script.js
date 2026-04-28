const API_URL = "http://127.0.0.1:8000/sync";

const executeBtn = document.getElementById("executeBtn");
const btnContent = document.getElementById("btnContent");
const resultBox  = document.getElementById("resultBox");
const errorBox   = document.getElementById("errorBox");
const errorMsg   = document.getElementById("errorMsg");

function getFormData() {
  return {
    zoom_account: document.querySelector('input[name="zoom_account"]:checked').value,
    from_date:    document.getElementById("from_date").value,
    to_date:      document.getElementById("to_date").value,
  };
}

function validate(data) {
  if (!data.from_date) return "Please select a From Date.";
  if (!data.to_date)   return "Please select a To Date.";
  if (data.from_date > data.to_date) return "From Date must be on or before To Date.";
  return null;
}

function setLoading(isLoading) {
  executeBtn.disabled = isLoading;
  btnContent.innerHTML = isLoading
    ? `<div class="spinner"></div> Running Sync...`
    : `<svg class="btn-icon" width="16" height="16" viewBox="0 0 24 24" fill="none">
         <path d="M5 12H19M19 12L12 5M19 12L12 19" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
       </svg> Execute Sync`;
}

function clearFeedback() {
  resultBox.classList.add("hidden");
  errorBox.classList.add("hidden");
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function logColorClass(log) {
  const l = log.toLowerCase();
  if (l.includes("error") || l.includes("fail") || l.includes("❌")) return "log-error";
  if (l.includes("warn")  || l.includes("skip"))                       return "log-warn";
  if (l.includes("upload") || l.includes("success") || l.includes("✅")) return "log-success";
  if (l.includes("fetch") || l.includes("found") || l.includes("info")) return "log-info";
  return "";
}


function showResult(data) {
  const badge      = document.getElementById("resultBadge");
  const statusText = document.getElementById("resultStatusText");
  const logsBox    = document.getElementById("logs");
  const logsCount  = document.getElementById("logsCount");

  // Status badge
  statusText.textContent = data.status || "success";
  const ok = data.status === "success";
  badge.style.background  = ok ? "#dcfce7" : "#fef9c3";
  badge.style.borderColor = ok ? "#86efac" : "#fde047";
  badge.style.color       = ok ? "#15803d" : "#a16207";

  // Stats
  document.getElementById("meetingsFetched").textContent = data.meetings_fetched ?? "—";
  document.getElementById("newUploads").textContent      = data.new_uploads      ?? "—";

  // Logs
  const logs = Array.isArray(data.logs) ? data.logs : [];
  logsCount.textContent = `${logs.length} ${logs.length === 1 ? "entry" : "entries"}`;

  if (logs.length === 0) {
    logsBox.innerHTML = `<span class="logs-empty">No logs returned.</span>`;
  } else {
    logsBox.innerHTML = logs.map((log, i) => {
      const cls = logColorClass(log);
      const num = String(i + 1).padStart(2, "0");
      return `<div class="log-entry">
        <span class="log-index">${num}</span>
        <span class="log-text ${cls}">${escapeHtml(log)}</span>
      </div>`;
    }).join("");
    logsBox.scrollTop = logsBox.scrollHeight;
  }

  resultBox.classList.remove("hidden");
}

function showError(message) {
  errorMsg.textContent = message;
  errorBox.classList.remove("hidden");
}

async function runSync() {
  clearFeedback();

  const data = getFormData();
  const err  = validate(data);
  if (err) { showError(err); return; }

  setLoading(true);

  try {
    const response = await fetch(API_URL, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(data),
    });

    if (!response.ok) {
      let detail = `Server error: ${response.status} ${response.statusText}`;
      try {
        const errBody = await response.json();
        if (errBody.detail) detail = errBody.detail;
      } catch {}
      throw new Error(detail);
    }

    const result = await response.json();
    showResult(result);

  } catch (err) {
    const msg = (err.name === "TypeError" && err.message.includes("fetch"))
      ? "Cannot reach the server. Make sure the backend is running at " + API_URL
      : (err.message || "An unexpected error occurred. Please try again.");
    showError(msg);
  } finally {
    setLoading(false);
  }
}