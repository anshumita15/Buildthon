from flask import Flask, render_template_string, jsonify
import json
import os
 
app = Flask(__name__)
 
DATA_FILE   = "/tmp/seizureguard_data.json"
EVENTS_FILE = "/tmp/seizureguard_events.json"
 
# ── HTML template ─────────────────────────────────────────────────────────────
TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>SeizureGuard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Segoe UI', sans-serif;
      background: #0d1117;
      color: #e6edf3;
      padding: 2em;
    }
    h1  { font-size: 1.6em; margin-bottom: 0.25em; }
    h2  { font-size: 1.1em; margin: 1.5em 0 0.5em; color: #8b949e; }
 
    /* status badge */
    #status-badge {
      display: inline-block;
      padding: 0.35em 1em;
      border-radius: 999px;
      font-weight: bold;
      font-size: 0.95em;
      margin-bottom: 1.5em;
      transition: background 0.3s, color 0.3s;
    }
    .status-ARMED   { background: #1f6feb33; color: #58a6ff; border: 1px solid #1f6feb; }
    .status-WARNING { background: #9e6a0333; color: #d29922; border: 1px solid #9e6a03; }
    .status-SEIZURE { background: #da363333; color: #f85149; border: 1px solid #da3633;
                      animation: pulse 0.6s infinite alternate; }
    @keyframes pulse { from { opacity: 1; } to { opacity: 0.5; } }
 
    /* stats row */
    .stats {
      display: flex;
      gap: 1.5em;
      margin-bottom: 1.5em;
    }
    .stat-card {
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 8px;
      padding: 0.75em 1.25em;
      min-width: 140px;
    }
    .stat-label { font-size: 0.75em; color: #8b949e; text-transform: uppercase; }
    .stat-value { font-size: 1.4em; font-weight: bold; margin-top: 0.1em; }
 
    /* chart */
    #chart-wrap {
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 8px;
      padding: 1em;
      margin-bottom: 1.5em;
    }
 
    /* event log */
    #event-log {
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 8px;
      padding: 1em;
      max-height: 240px;
      overflow-y: auto;
    }
    .event-row {
      display: flex;
      gap: 1em;
      padding: 0.4em 0;
      border-bottom: 1px solid #21262d;
      font-size: 0.88em;
    }
    .event-row:last-child { border-bottom: none; }
    .event-time   { color: #8b949e; white-space: nowrap; }
    .event-type   { color: #f85149; font-weight: bold; }
    .event-detail { color: #8b949e; }
    .no-events    { color: #8b949e; font-size: 0.9em; }
  </style>
</head>
<body>
  <h1>🌙 SeizureGuard Monitor</h1>
 
  <span id="status-badge" class="status-ARMED">● ARMED</span>
 
  <div class="stats">
    <div class="stat-card">
      <div class="stat-label">Magnitude (m/s²)</div>
      <div class="stat-value" id="val-mag">—</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Band Ratio</div>
      <div class="stat-value" id="val-ratio">—</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Amplitude</div>
      <div class="stat-value" id="val-amp">—</div>
    </div>
  </div>
 
  <div id="chart-wrap">
    <canvas id="chart" height="100"></canvas>
  </div>
 
  <h2>Event Log (seizure confirmations)</h2>
  <div id="event-log">
    <p class="no-events">No events yet.</p>
  </div>
 
  <script>
    // ── rolling chart (last 60 data points = ~60 seconds) ──────────────────
    const MAX_POINTS = 60;
    const labels = Array(MAX_POINTS).fill("");
    const magData = Array(MAX_POINTS).fill(null);
 
    const ctx = document.getElementById("chart").getContext("2d");
    const chart = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [{
          label: "Acceleration magnitude (m/s²)",
          data: magData,
          borderColor: "#58a6ff",
          backgroundColor: "rgba(88,166,255,0.08)",
          borderWidth: 1.5,
          pointRadius: 0,
          tension: 0.3,
          fill: true,
        }]
      },
      options: {
        animation: false,
        scales: {
          x: { display: false },
          y: {
            min: 8,
            max: 16,
            ticks: { color: "#8b949e" },
            grid:  { color: "#21262d" },
          }
        },
        plugins: {
          legend: { labels: { color: "#8b949e" } }
        }
      }
    });
 
    // ── poll /data every second ─────────────────────────────────────────────
    async function fetchData() {
      try {
        const res  = await fetch("/data");
        const json = await res.json();
 
        // update status badge
        const badge = document.getElementById("status-badge");
        badge.textContent = "● " + json.status;
        badge.className   = "status-" + json.status;
 
        // update stat cards
        document.getElementById("val-mag").textContent   = json.magnitude.toFixed(3);
        document.getElementById("val-ratio").textContent = json.ratio.toFixed(3);
        document.getElementById("val-amp").textContent   = json.amplitude.toFixed(3);
 
        // push to chart
        magData.push(json.magnitude);
        labels.push("");
        if (magData.length > MAX_POINTS) { magData.shift(); labels.shift(); }
        chart.update();
 
      } catch (e) {
        console.warn("Data fetch failed:", e);
      }
    }
 
    // ── poll /events every 3 seconds ────────────────────────────────────────
    async function fetchEvents() {
      try {
        const res    = await fetch("/events");
        const events = await res.json();
        const log    = document.getElementById("event-log");
 
        if (!events.length) {
          log.innerHTML = '<p class="no-events">No events yet.</p>';
          return;
        }
 
        // most recent first
        const rows = [...events].reverse().map(e => `
          <div class="event-row">
            <span class="event-time">${e.time}</span>
            <span class="event-type">${e.type}</span>
            <span class="event-detail">${e.detail}</span>
          </div>`).join("");
        log.innerHTML = rows;
 
      } catch (e) {
        console.warn("Events fetch failed:", e);
      }
    }
 
    fetchData();
    fetchEvents();
    setInterval(fetchData,   1000);
    setInterval(fetchEvents, 3000);
  </script>
</body>
</html>
"""
 
# ── routes ────────────────────────────────────────────────────────────────────
@app.route("/")
def home():
    return render_template_string(TEMPLATE)
 
 
@app.route("/data")
def data():
    if not os.path.exists(DATA_FILE):
        return jsonify({"magnitude": 9.8, "ratio": 0.0,
                        "amplitude": 0.0, "status": "ARMED"})
    try:
        with open(DATA_FILE) as f:
            return jsonify(json.load(f))
    except (json.JSONDecodeError, OSError):
        return jsonify({"magnitude": 9.8, "ratio": 0.0,
                        "amplitude": 0.0, "status": "ARMED"})
 
 
@app.route("/events")
def events():
    if not os.path.exists(EVENTS_FILE):
        return jsonify([])
    try:
        with open(EVENTS_FILE) as f:
            return jsonify(json.load(f))
    except (json.JSONDecodeError, OSError):
        return jsonify([])
 
 
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)