# Web dashboard

The current local dashboard is dependency-free and reads the API health, repositories, runs, approvals, and event timelines.

Run it from the repository root with:

```powershell
python -m http.server 5173 --directory apps/web
```

Then open `http://localhost:5173`. The API is expected at `http://localhost:8000`; set `localStorage.repopilot-api` if it is hosted elsewhere.
