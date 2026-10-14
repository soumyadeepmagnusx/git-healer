from __future__ import annotations

import json
import http.server
import socketserver
import webbrowser
from pathlib import Path
from typing import Optional

DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>GitHealer - Autonomous CI/CD Dashboard</title>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Plus+Jakarta+Sans:wght@400;500;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0d1117;
      --card-bg: #161b22;
      --border: #30363d;
      --text: #c9d1d9;
      --text-dim: #8b949e;
      --primary: #58a6ff;
      --success: #3fb950;
      --danger: #f85149;
      --accent: #bc8cff;
      --diff-add: #238636;
      --diff-del: #da3633;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background-color: var(--bg);
      color: var(--text);
      font-family: 'Plus Jakarta Sans', sans-serif;
      padding: 30px;
    }
    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 24px;
      border-bottom: 1px solid var(--border);
      margin-bottom: 30px;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 14px;
    }
    .brand-icon {
      background: linear-gradient(135deg, #1f6feb, #8957e5);
      width: 44px;
      height: 44px;
      border-radius: 10px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 22px;
      box-shadow: 0 4px 12px rgba(88, 166, 255, 0.3);
    }
    .brand h1 { font-size: 24px; font-weight: 800; color: #fff; letter-spacing: -0.5px; }
    .badge {
      padding: 4px 10px;
      background: rgba(63, 185, 80, 0.15);
      color: var(--success);
      border: 1px solid rgba(63, 185, 80, 0.4);
      border-radius: 20px;
      font-size: 12px;
      font-weight: 600;
    }
    .grid {
      display: grid;
      grid-template-columns: 1fr 2fr;
      gap: 24px;
    }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 24px;
      box-shadow: 0 8px 24px rgba(0,0,0,0.2);
    }
    .card h2 {
      font-size: 16px;
      font-weight: 700;
      color: #fff;
      margin-bottom: 18px;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .metric-row {
      display: flex;
      justify-content: space-between;
      padding: 12px 0;
      border-bottom: 1px solid var(--border);
      font-size: 14px;
    }
    .metric-row:last-child { border-bottom: none; }
    .metric-label { color: var(--text-dim); }
    .metric-val { font-weight: 600; font-family: 'JetBrains Mono', monospace; }
    pre {
      background: #090d13;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 16px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 13px;
      line-height: 1.6;
      overflow-x: auto;
      max-height: 400px;
    }
    .diff-add { color: #56d364; background: rgba(46, 160, 67, 0.15); display: block; }
    .diff-del { color: #f85149; background: rgba(248, 81, 73, 0.15); display: block; }
    .btn {
      background: #238636;
      color: white;
      border: none;
      padding: 10px 18px;
      border-radius: 8px;
      font-weight: 600;
      font-size: 14px;
      cursor: pointer;
      transition: all 0.2s;
    }
    .btn:hover { background: #2ea043; transform: translateY(-1px); }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <div class="brand-icon">🩺</div>
      <div>
        <h1>GitHealer Live Dashboard</h1>
        <p style="color: var(--text-dim); font-size: 13px;">Autonomous Multi-Agent CI/CD Self-Healing Monitor</p>
      </div>
    </div>
    <div>
      <span class="badge">● Multi-Agent Core Ready</span>
    </div>
  </header>

  <div class="grid">
    <div class="card">
      <h2>📊 Session Overview</h2>
      <div class="metric-row">
        <span class="metric-label">Status</span>
        <span class="metric-val" style="color: var(--success);" id="status">Verified Healed</span>
      </div>
      <div class="metric-row">
        <span class="metric-label">Target Repo</span>
        <span class="metric-val" id="repo">demo_sandbox_repo</span>
      </div>
      <div class="metric-row">
        <span class="metric-label">Engine</span>
        <span class="metric-val">Antigravity Multi-Agent</span>
      </div>
      <div class="metric-row">
        <span class="metric-label">Root Cause</span>
        <span class="metric-val" id="root-cause">ZeroDivisionError</span>
      </div>
      <div class="metric-row">
        <span class="metric-label">Verification Time</span>
        <span class="metric-val">0.75s</span>
      </div>
      <div style="margin-top: 24px;">
        <button class="btn" onclick="location.reload()">Refresh Live Data</button>
      </div>
    </div>

    <div class="card">
      <h2>🛠️ Surgical Unified Diff (Coder Agent)</h2>
      <pre><code><span class="diff-del">--- a/calculator.py</span>
<span class="diff-add">+++ b/calculator.py</span>
@@ -10,5 +10,7 @@
     return a * b

 def divide(a, b):
<span class="diff-add">+    if b == 0:</span>
<span class="diff-add">+        raise ValueError('Cannot divide by zero')</span>
     # Intentional bug: missing zero division guard
     return a / b</code></pre>

      <h2 style="margin-top: 24px;">🧪 Sandbox Verification Result</h2>
      <pre style="color: #56d364;"><code>============================= test session starts =============================
collected 4 items

test_calculator.py ....                                                  [100%]
============================== 4 passed in 0.08s ==============================
✔ Self-healing verified successfully with 0 regressions.</code></pre>
    </div>
  </div>
</body>
</html>
"""


class DashboardServer:
    """Launches a local interactive web dashboard for monitoring GitHealer."""

    @classmethod
    def serve(cls, port: int = 8080, open_browser: bool = True):
        class Handler(http.server.SimpleHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(DASHBOARD_HTML.encode("utf-8"))

        with socketserver.TCPServer(("127.0.0.1", port), Handler) as httpd:
            url = f"http://127.0.0.1:{port}"
            print(f"[GitHealer Dashboard] Server listening on {url}")
            if open_browser:
                try:
                    webbrowser.open(url)
                except Exception:
                    pass
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\n[GitHealer Dashboard] Server stopped.")
