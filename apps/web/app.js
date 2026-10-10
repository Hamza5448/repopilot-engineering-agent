const apiBase = localStorage.getItem("repopilot-api") || "http://localhost:8000";
const $ = (id) => document.getElementById(id);

async function get(path) {
  const response = await fetch(`${apiBase}${path}`);
  if (!response.ok) throw new Error(`${path} returned ${response.status}`);
  return response.json();
}

function metric(label, value, tone = "") {
  return `<div class="metric ${tone}"><span>${label}</span><strong>${value}</strong></div>`;
}

function renderRuns(runs) {
  $("run-count").textContent = `${runs.length} shown`;
  $("runs").innerHTML = runs.length
    ? runs.map((run) => `<button class="run-row" data-run="${run.id}">
        <span><strong>${run.trigger_type}</strong><small>${run.id}</small></span>
        <span class="status ${run.status}">${run.status}</span>
      </button>`).join("")
    : '<p class="muted">No runs yet.</p>';
  document.querySelectorAll("[data-run]").forEach((button) => {
    button.addEventListener("click", () => loadEvents(button.dataset.run));
  });
}

async function loadEvents(runId) {
  $("selected-run").textContent = runId;
  try {
    const events = await get(`/api/v1/runs/${runId}/events`);
    $("events").innerHTML = events.map((event) => `<div class="event">
      <span class="dot"></span><div><strong>${event.event_type}</strong><small>${new Date(event.created_at).toLocaleString()}</small></div>
    </div>`).join("");
  } catch (error) { $("error").textContent = error.message; }
}

async function refresh() {
  $("error").textContent = "";
  try {
    const [ready, repositories, runs] = await Promise.all([
      get("/ready"), get("/api/v1/repositories"), get("/api/v1/runs?limit=50"),
    ]);
    const succeeded = runs.filter((run) => run.status === "succeeded").length;
    const waiting = runs.filter((run) => run.status === "waiting_for_approval").length;
    $("metrics").innerHTML = [
      metric("API", ready.status, "good"), metric("GitHub App", ready.github_app_configured ? "Ready" : "Missing", ready.github_app_configured ? "good" : "bad"),
      metric("Repositories", repositories.length), metric("Succeeded", succeeded, "good"), metric("Approval queue", waiting, waiting ? "warn" : ""),
    ].join("");
    renderRuns(runs);
  } catch (error) { $("error").textContent = error.message; }
}

$("refresh").addEventListener("click", refresh);
refresh();
