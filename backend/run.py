"""
MetaRadar Production Entrypoint for Render / Cloud Containers
- Runs database migrations (alembic upgrade head) before launching web server.
- Starts Uvicorn on 0.0.0.0 and dynamic port $PORT.
- Always binds to $PORT even if database migrations encounter a transient error,
  ensuring Render does not crash-loop with "No open ports detected" and allowing health
  and diagnostics endpoints to report status honestly.
"""
import os
import sys
import subprocess
import uvicorn


def run_database_migrations():
    print("[METARADAR DEPLOY] Checking database connection and running Alembic migrations...")
    try:
        res = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            check=False,
        )
        if res.returncode == 0:
            print("[METARADAR DEPLOY] Database migrations successfully applied.")
        else:
            print(
                f"[METARADAR DEPLOY WARNING] Alembic migrations returned non-zero exit code ({res.returncode}).\n"
                "Please verify your DATABASE_URL credentials in the Render dashboard.\n"
                "Starting web server on $PORT so health check and diagnostics endpoints remain accessible.",
                file=sys.stderr,
            )
    except Exception as exc:
        print(f"[METARADAR DEPLOY WARNING] Failed to execute alembic migrations: {exc}", file=sys.stderr)


def main():
    run_database_migrations()
    port = int(os.environ.get("PORT", "8000"))
    print(f"[METARADAR DEPLOY] Starting FastAPI application on 0.0.0.0:{port}...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()
