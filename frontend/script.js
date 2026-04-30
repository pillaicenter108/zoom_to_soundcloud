const BASE_URL   = "http://127.0.0.1:8000";
const SYNC_URL   = `${BASE_URL}/sync`;
const STATUS_URL = (jobId) => `${BASE_URL}/status/${jobId}`;

// ── Exponential backoff schedule (well under 100 req/hr CF limit) ─────────
// Poll 1-3  →  5s   Poll 4-6  → 15s   Poll 7+  → 60s
const POLL_SCHEDULE = [5000, 5000, 5000, 15000, 15000, 15000];
const POLL_MAX_MS   = 60000;

let pollTimer = null;
let pollCount = 0;

// ── DOM refs ──────────────────────────────────────────────────────────────
const executeBtn = document.getElementById("executeBtn");
const resultBox  = document.getElementById("resultBox");
const errorBox   = document.getElementById("errorBox");
const errorMsg   = document.getElementById("errorMsg");

// ── Helpers ───────────────────────────────────────────────────────────────
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

function setLoading(isLoading, label = "Running Sync...") {
  executeBtn.disabled = isLoading;
  document.getElementById("btnContent").innerHTML = isLoading
    ? `<div class="spinner"></div> ${label}`
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
  if (l.includes("upload")|| l.includes("success")|| l.includes("✅")) return "log-success";
  if (l.includes("fetch") || l.includes("found")  || l.includes("info")) return "log-info";
  return "";
}

function nextDelay() {
  return POLL_SCHEDULE[pollCount] !== undefined ? POLL_SCHEDULE[pollCount] : POLL_MAX_MS;
}

// ── Smart activity message from latest log ────────────────────────────────
function latestActivityMsg(logs, nextSec) {
  if (!logs || logs.length === 0) return "Starting sync…";
  const last = logs[logs.length - 1].toLowerCase();
  if (last.includes("zoom auth"))       return "Authenticating with Zoom…";
  if (last.includes("soundcloud auth")) return "Authenticating with SoundCloud…";
  if (last.includes("meetings fetched"))return "Fetching recordings list…";
  if (last.includes("⬇️") || last.includes("downloaded")) return "Downloading recording…";
  if (last.includes("🎧") || last.includes("uploaded"))   return "Uploading to SoundCloud…";
  if (last.includes("⏭") || last.includes("already"))    return "Checking recordings…";
  if (last.includes("❌"))              return "Handling an error…";
  return `Next check in ${nextSec}s…`;
}

// ── Render logs (works for both live/partial and final) ───────────────────
function renderLogs(logs, isRunning) {
  const logsBox   = document.getElementById("logs");
  const logsCount = document.getElementById("logsCount");
  const nextSec   = Math.round(nextDelay() / 1000);

  logsCount.textContent = isRunning
    ? `${logs.length} so far — next check in ${nextSec}s`
    : `${logs.length} ${logs.length === 1 ? "entry" : "entries"}`;

  const actMsg = document.getElementById("activityMsg");
  if (actMsg) actMsg.textContent = isRunning ? latestActivityMsg(logs, nextSec) : "";

  if (logs.length === 0) {
    logsBox.innerHTML = `<span class="logs-empty" style="color:#2563eb;">
      <div class="spinner" style="border-top-color:#2563eb;border-color:rgba(37,99,235,0.25);margin:0 auto 6px;"></div>
      Waiting for first log…
    </span>`;
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
}

// ── Show card during polling (status badge only, logs rendered separately) ─
function showRunningCard() {
  const badge = document.getElementById("resultBadge");
  document.getElementById("resultStatusText").textContent = "running";
  badge.style.background  = "#dbeafe";
  badge.style.borderColor = "#93c5fd";
  badge.style.color       = "#1d4ed8";
  document.getElementById("meetingsFetched").textContent = "…";
  document.getElementById("newUploads").textContent      = "…";
  resultBox.classList.remove("hidden");
  errorBox.classList.add("hidden");
}

// ── Final result card ────────────────────────────────────────────────────
function showResult(data) {
  const badge = document.getElementById("resultBadge");
  const ok    = data.status === "success";
  document.getElementById("resultStatusText").textContent = data.status || "success";
  badge.style.background  = ok ? "#dcfce7" : "#fef9c3";
  badge.style.borderColor = ok ? "#86efac" : "#fde047";
  badge.style.color       = ok ? "#15803d" : "#a16207";

  document.getElementById("meetingsFetched").textContent = data.meetings_fetched ?? "—";
  document.getElementById("newUploads").textContent      = data.new_uploads      ?? "—";

  renderLogs(Array.isArray(data.logs) ? data.logs : [], false);

  resultBox.classList.remove("hidden");
  errorBox.classList.add("hidden");
}

function showError(message) {
  errorMsg.textContent = message;
  errorBox.classList.remove("hidden");
  resultBox.classList.add("hidden");
}

// ── Polling ───────────────────────────────────────────────────────────────
function stopPolling() {
  if (pollTimer !== null) { clearTimeout(pollTimer); pollTimer = null; }
}

function schedulePoll(jobId) {
  const delay = nextDelay();

  pollTimer = setTimeout(async () => {
    pollCount++;
    try {
      const res = await fetch(STATUS_URL(jobId));
      if (!res.ok) throw new Error(`Status check failed: ${res.status}`);
      const data = await res.json();
      const logs = Array.isArray(data.logs) ? data.logs : [];

      if (data.status === "success" || data.status === "error") {
        stopPolling();
        setLoading(false);
        if (data.status === "error") {
          showError(data.error || "Sync failed with an unknown error.");
        } else {
          showResult(data);
        }
      } else {
        // Still running — render partial logs NOW, then schedule next poll
        renderLogs(logs, true);
        schedulePoll(jobId);
      }
    } catch (err) {
      stopPolling();
      setLoading(false);
      showError("Lost contact with the server while polling. " + err.message);
    }
  }, delay);
}

function startPolling(jobId) {
  stopPolling();
  pollCount = 0;
  showRunningCard();
  renderLogs([], true);   // show empty log panel immediately
  schedulePoll(jobId);
}

// ── Main entry point ──────────────────────────────────────────────────────
async function runSync() {
  clearFeedback();
  stopPolling();

  const data = getFormData();
  const err  = validate(data);
  if (err) { showError(err); return; }

  setLoading(true, "Starting Sync…");

  try {
    const response = await fetch(SYNC_URL, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(data),
    });

    if (!response.ok) {
      let detail = `Server error: ${response.status} ${response.statusText}`;
      try { const eb = await response.json(); if (eb.detail) detail = eb.detail; } catch {}
      throw new Error(detail);
    }

    const { job_id } = await response.json();
    setLoading(true, "Sync Running…");
    startPolling(job_id);

  } catch (err) {
    setLoading(false);
    const msg = (err.name === "TypeError" && err.message.includes("fetch"))
      ? "Cannot reach the server. Make sure the backend is running at " + BASE_URL
      : (err.message || "An unexpected error occurred. Please try again.");
    showError(msg);
  }
}