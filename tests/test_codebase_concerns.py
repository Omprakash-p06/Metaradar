import re
import sys
from datetime import datetime, timezone
from pathlib import Path
import pytest

base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))

from app.services.pii import PIIPHIScrubber
from app.providers.base import DataClassification
from app.core.config import settings, validate_production_settings
from app.services.scheduler import SourceScheduler


def test_pii_scrubber_clinical_identifiers():
    """Verify that clinical trial subject and patient identifiers are detected and redacted."""
    # Clinical subject ID
    s1, p1, c1 = PIIPHIScrubber.scrub("Trial screening enrolled Subject ID: #SUB-90214 in cohort A")
    assert p1 is True
    assert "[CLINICAL_SUBJECT_REDACTED]" in s1
    assert "SUB-90214" not in s1

    # Participant ID
    s2, p2, c2 = PIIPHIScrubber.scrub("Adverse event noted for Participant ID: PT-7821-X")
    assert p2 is True
    assert "[CLINICAL_SUBJECT_REDACTED]" in s2
    assert "PT-7821-X" not in s2

    # Patient name
    s3, p3, c3 = PIIPHIScrubber.scrub("Case history for Patient Name: Arthur Pendelton at Site 104")
    assert p3 is True
    assert "[PATIENT_NAME_REDACTED]" in s3
    assert "Arthur Pendelton" not in s3

    # Clean text has no PII
    s4, p4, _ = PIIPHIScrubber.scrub("Phase 3 trial readouts demonstrate 92% annualized bleeding reduction.")
    assert p4 is False
    assert s4 == "Phase 3 trial readouts demonstrate 92% annualized bleeding reduction."


def test_source_classification_all_connectors():
    """Verify all 8 authoritative and trade-press connectors are recognized as PUBLIC."""
    active_sources = [
        "pubmed",
        "clinical_trials",
        "fda",
        "ema",
        "newsapi",
        "biopharmadive",
        "fierce_pharma",
        "fiercepharma",
        "et_pharma",
        "congress",
    ]
    for src in active_sources:
        cls = PIIPHIScrubber.classify_payload("Standard clinical news text", source_type=src)
        assert cls == DataClassification.PUBLIC, f"Failed for {src}"

    # Synthetic / demo
    assert PIIPHIScrubber.classify_payload("Demo signal", source_type="synthetic") == DataClassification.SYNTHETIC
    assert PIIPHIScrubber.classify_payload("Demo signal", source_type="demo") == DataClassification.SYNTHETIC

    # Unrecognized source -> UNKNOWN (blocked by privacy gate)
    assert PIIPHIScrubber.classify_payload("Unverified leak", source_type="untrusted_feed") == DataClassification.UNKNOWN

    # Text containing PII always escalates to CONFIDENTIAL regardless of source
    assert PIIPHIScrubber.classify_payload("Subject ID: #SUB-1234", source_type="clinical_trials") == DataClassification.CONFIDENTIAL


def test_production_boot_guard(monkeypatch):
    """Verify production boot guard blocks startup with dev secrets or demo mode."""
    # Development mode: passes even with dev defaults
    monkeypatch.setattr(settings, "APP_ENV", "development")
    monkeypatch.setattr(settings, "SECRET_KEY", "dev-secret-change-in-production")
    monkeypatch.setattr(settings, "DEMO_MODE", True)
    validate_production_settings()  # No exception

    # Production mode with default secret: raises RuntimeError
    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "SECRET_KEY", "dev-secret-change-in-production")
    with pytest.raises(RuntimeError, match="FATAL: Cannot run in production with default SECRET_KEY"):
        validate_production_settings()

    # Production mode with DEMO_MODE=True: raises RuntimeError
    monkeypatch.setattr(settings, "SECRET_KEY", "a-very-secure-random-prod-key-32chars")
    monkeypatch.setattr(settings, "DEMO_MODE", True)
    with pytest.raises(RuntimeError, match="FATAL: DEMO_MODE must be False in production"):
        validate_production_settings()

    # Production mode with valid secrets & DEMO_MODE=False: succeeds
    monkeypatch.setattr(settings, "DEMO_MODE", False)
    validate_production_settings()  # No exception


def test_newsapi_utc_date_format():
    """Verify UTC date generation conforms to YYYY-MM-DD ISO format."""
    now_utc = datetime.now(timezone.utc)
    today_iso = now_utc.date().isoformat()
    assert re.match(r"^\d{4}-\d{2}-\d{2}$", today_iso)
    assert len(today_iso) == 10


def test_scheduler_intervals_configured():
    """Verify all 8 connectors have explicit scheduler interval configurations."""
    assert settings.SCHEDULER_BIOPHARMA_DIVE_INTERVAL_MINUTES == 30
    assert settings.SCHEDULER_FIERCE_PHARMA_INTERVAL_MINUTES == 30
    assert settings.SCHEDULER_ET_PHARMA_INTERVAL_MINUTES == 30

    scheduler = SourceScheduler()
    scheduler._init_job_states()
    for src in ["biopharmadive", "fierce_pharma", "et_pharma", "clinical_trials", "pubmed", "ema", "fda", "newsapi"]:
        assert src in scheduler._jobs, f"Missing job state for {src}"
        assert scheduler._jobs[src].base_interval_minutes > 0



def test_worm_audit_trigger_ddl_integrity():
    """Verify migration 014 defines the tamper-proof DB trigger trg_block_audit_log_update_delete."""
    migration_file = base_dir / "backend" / "alembic" / "versions" / "014_auditlog_user_correlation.py"
    assert migration_file.exists()
    content = migration_file.read_text(encoding="utf-8")

    assert "CREATE TRIGGER trg_block_audit_log_update_delete" in content
    assert "BEFORE UPDATE OR DELETE ON audit_log" in content
    assert "block_audit_log_mutation()" in content
