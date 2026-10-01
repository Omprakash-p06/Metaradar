import subprocess
import sys
from pathlib import Path

base_dir = Path(__file__).resolve().parents[1]


def test_setup_py_help():
    setup_script = base_dir / "setup.py"
    assert setup_script.exists(), "setup.py does not exist"

    res = subprocess.run(
        [sys.executable, str(setup_script), "--help"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "MetaRadar" in res.stdout
    assert "--skip-docker" in res.stdout
    assert "--skip-models" in res.stdout
    assert "--download-model" in res.stdout
    assert "--api-key" in res.stdout
    assert "--no-interactive" in res.stdout
    assert "--skip-frontend" in res.stdout
    assert "--skip-db-seed" in res.stdout


def test_start_py_help():
    start_script = base_dir / "start.py"
    assert start_script.exists(), "start.py does not exist"

    res = subprocess.run(
        [sys.executable, str(start_script), "--help"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "MetaRadar" in res.stdout
    assert "--no-frontend" in res.stdout
    assert "--no-backend" in res.stdout
    assert "--port-backend" in res.stdout
    assert "--port-frontend" in res.stdout
    assert "--daemon" in res.stdout


def test_start_py_module_imports():
    sys.path.insert(0, str(base_dir))
    import start
    assert hasattr(start, "cleanup_processes")
    assert hasattr(start, "check_endpoint_health")
    assert hasattr(start, "start_backend")
    assert hasattr(start, "start_frontend")
    assert hasattr(start, "free_port_if_in_use")
    assert hasattr(start, "print_recent_logs")
    assert hasattr(start, "check_socket_ready")


def test_free_port_on_unused_port():
    import start
    # Port 59999 should not be in use, function should return cleanly without error
    start.free_port_if_in_use(59999, "Test Unused Port")


def test_print_recent_logs(tmp_path):
    import start
    log_file = tmp_path / "test.log"
    log_file.write_text("line 1\nline 2\nline 3\n", encoding="utf-8")
    # Should execute without error
    start.print_recent_logs(log_file, "TestService", max_lines=2)
    start.print_recent_logs(tmp_path / "nonexistent.log", "TestService")


def test_start_frontend_cmd_construction(monkeypatch):
    import start
    captured = {}

    def mock_popen(cmd, cwd=None, env=None, stdout=None, stderr=None):
        captured["cmd"] = cmd
        captured["env"] = env
        captured["cwd"] = cwd
        class MockProc:
            pass
        return MockProc()

    monkeypatch.setattr(start.subprocess, "Popen", mock_popen)

    # 1. When pnpm is detected
    monkeypatch.setattr(start.shutil, "which", lambda binary: "/bin/pnpm" if binary == "pnpm" else None)
    start.start_frontend(port=3000, backend_port=8000)
    assert captured["cmd"] == ["/bin/pnpm", "run", "dev", "-p", "3000"]
    assert "--" not in captured["cmd"]
    assert captured["env"]["PORT"] == "3000"

    # 2. When only npm is detected
    monkeypatch.setattr(start.shutil, "which", lambda binary: None if binary == "pnpm" else "/bin/npm")
    start.start_frontend(port=3000, backend_port=8000)
    assert captured["cmd"] == ["/bin/npm", "run", "dev", "--", "-p", "3000"]
    assert captured["env"]["PORT"] == "3000"


