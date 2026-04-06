import json
import os
from pathlib import Path

import httpx


def _default_tasks_path() -> Path:
    # backend/ -> ai-dashboard-generator/ -> repo root/
    return Path(__file__).resolve().parents[2] / "mission-control-tasks" / "dashboard_tasks.json"


def main():
    mc_url = os.getenv("MC_URL", "http://localhost:3000").rstrip("/")
    api_key = os.getenv("MC_API_KEY", "")
    if not api_key:
        raise SystemExit("MC_API_KEY is not set")

    tasks_path = Path(os.getenv("MC_TASKS_JSON", str(_default_tasks_path())))
    if not tasks_path.exists():
        raise SystemExit(f"Tasks JSON not found: {tasks_path}")

    data = json.loads(tasks_path.read_text(encoding="utf-8"))
    templates = data.get("templates", [])
    if not isinstance(templates, list) or not templates:
        raise SystemExit("No templates found in dashboard_tasks.json")

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    created = 0
    with httpx.Client(timeout=10) as client:
        for t in templates:
            payload = {
                "title": t.get("title"),
                "description": t.get("description"),
                "assigned_to": t.get("assigned_to", "ai-dashboard-agent"),
                "type": t.get("task_type"),
                "priority": t.get("priority", "medium"),
                "endpoint": t.get("endpoint", "http://localhost:8010/api/mc-task"),
            }
            r = client.post(f"{mc_url}/api/tasks", headers=headers, json=payload)
            if r.status_code in (200, 201):
                created += 1
            else:
                raise SystemExit(f"Failed creating task template: {r.status_code} {r.text}")

    print(f"Registered {created} task templates in Mission Control.")


if __name__ == "__main__":
    main()

