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
from app.connectors.newsapi import NewsAPIConnector


def test_pii_scrubber_clinical_identifiers():
    """Verify clinical trial identifiers are redacted and ordinary English does not false-positive (WR-02, WR-03, IN-02)."""
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

    # None / empty input resilience (IN-02)
    s_none, p_none, c_none = PIIPHIScrubber.scrub(None)
    assert s_none == ""
    assert p_none is False
    assert c_none == {}

    # WR-02: Ordinary English with "Chart" does NOT false-positive
    s_chart, p_chart, _ = PIIPHIScrubber.scrub("Chart review shows efficacy in 50 patients across multiple cohorts.")
    assert p_chart is False
    assert "Chart review" in s_chart

    # WR-03: Ordinary English with "Patient" does NOT false-positive
    s_patient, p_patient, _ = PIIPHIScrubber.scrub("Patient data indicate strong adherence and patient enrollment increased.")
    assert p_patient is False
    assert "Patient data indicate" in s_patient


def test_source_classification_all_connectors():
    """Verify all 8 active connectors are PUBLIC and unregistered sources are UNKNOWN (IN-01)."""
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
    ]
    for src in active_sources:
        cls = PIIPHIScrubber.classify_payload("Standard clinical news text", source_type=src)
        assert cls == DataClassification.PUBLIC, f"Failed for {src}"

    # Phantom/unregistered source -> UNKNOWN (blocked by privacy gate) (IN-01)
    assert PIIPHIScrubber.classify_payload("Standard text", source_type="congress") == DataClassification.UNKNOWN
    assert PIIPHIScrubber.classify_payload("Unverified leak", source_type="untrusted_feed") == DataClassification.UNKNOWN

    # Synthetic / demo
    assert PIIPHIScrubber.classify_payload("Demo signal", source_type="synthetic") == DataClassification.SYNTHETIC
    assert PIIPHIScrubber.classify_payload("Demo signal", source_type="demo") == DataClassification.SYNTHETIC

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

    # Production mode with wildcard CORS origin: raises RuntimeError
    monkeypatch.setattr(settings, "CORS_ORIGINS", "https://example.netlify.app,*")
    with pytest.raises(RuntimeError, match="FATAL: Wildcard CORS origin is forbidden in production"):
        validate_production_settings()


@pytest.mark.asyncio
async def test_lifespan_wires_production_boot_guard(monkeypatch):
    """Verify that FastAPI lifespan startup invokes the production boot guard (CR-01, WR-08)."""
    from app.main import lifespan, app
    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "SECRET_KEY", "dev-secret-change-in-production")
    monkeypatch.setattr(settings, "DEMO_MODE", True)

    with pytest.raises(RuntimeError, match="FATAL: Cannot run in production with default SECRET_KEY"):
        async with lifespan(app):
            pass


@pytest.mark.asyncio
async def test_newsapi_read_quota_uses_utc():
    """Verify NewsAPIConnector._read_quota defaults to and reports UTC date (WR-01, WR-07)."""
    connector = NewsAPIConnector()
    quota, window_date = await connector._read_quota(None, "haemophilia_news")
    utc_today = datetime.now(timezone.utc).date().isoformat()
    assert window_date == utc_today
    assert re.match(r"^\d{4}-\d{2}-\d{2}$", window_date)
    assert len(window_date) == 10


def test_newsapi_parse_article_scrubs_title_and_raw_article():
    """Verify NewsAPIConnector._parse_article scrubs title, content, and the nested article dict (WR-04)."""
    connector = NewsAPIConnector()
    raw_article = {
        "title": "Clinical breakthrough for Subject ID: #SUB-88123 in trial",
        "description": "Patient Name: Arthur Pendelton showed remarkable improvement",
        "content": "Contact doctor at test@hospital.org or call 555-123-4567",
        "url": "https://example.com/news/1",
        "source": {"name": "Pharma Wire"},
        "publishedAt": "2026-03-01T12:00:00Z",
    }
    payload = connector._parse_article(raw_article, datetime.now(timezone.utc))
    assert payload is not None

    # Title is scrubbed in payload
    assert "SUB-88123" not in payload.title
    assert "[CLINICAL_SUBJECT_REDACTED]" in payload.title

    # Content is scrubbed in payload
    assert "Arthur Pendelton" not in payload.content
    assert "[PATIENT_NAME_REDACTED]" in payload.content

    # Nested article dictionary in raw_payload is sanitized
    stored_art = payload.raw_payload["article"]
    assert "SUB-88123" not in stored_art["title"]
    assert "[CLINICAL_SUBJECT_REDACTED]" in stored_art["title"]
    assert "Arthur Pendelton" not in stored_art["description"]
    assert "[PATIENT_NAME_REDACTED]" in stored_art["description"]
    assert "test@hospital.org" not in stored_art["content"]
    assert "[EMAIL_REDACTED]" in stored_art["content"]


def test_synthesis_evidence_pii_classification():
    """Verify evidence containing PII is classified as CONFIDENTIAL to protect privacy gate (CR-02)."""
    clean_evidence = ["Clinical trial NCT01234567 achieved primary endpoint with p < 0.01."]
    cls_clean = PIIPHIScrubber.classify_payload("\n".join(clean_evidence), source_type="clinical_trials")
    assert cls_clean == DataClassification.PUBLIC

    pii_evidence = ["Adverse event reported for Patient Name: Arthur Pendelton at Site 101."]
    cls_pii = PIIPHIScrubber.classify_payload("\n".join(pii_evidence), source_type="clinical_trials")
    assert cls_pii == DataClassification.CONFIDENTIAL


def test_scheduler_intervals_configured():
    """Verify all 8 connectors have explicit interval configurations and exact mappings (IN-03)."""
    expected_intervals = {
        "clinical_trials": 60,
        "pubmed": 60,
        "ema": 30,
        "fda": 30,
        "newsapi": 15,
        "biopharmadive": 30,
        "fierce_pharma": 30,
        "et_pharma": 30,
    }

    assert settings.SCHEDULER_BIOPHARMA_DIVE_INTERVAL_MINUTES == 30
    assert settings.SCHEDULER_FIERCE_PHARMA_INTERVAL_MINUTES == 30
    assert settings.SCHEDULER_ET_PHARMA_INTERVAL_MINUTES == 30

    scheduler = SourceScheduler()
    for src, expected_min in expected_intervals.items():
        assert src in scheduler._jobs, f"Missing job state for {src}"
        assert scheduler._jobs[src].base_interval_minutes == expected_min, f"Interval mismatch for {src}"


def test_worm_audit_trigger_ddl_integrity():
    """Verify migration 014 defines the tamper-proof DB trigger trg_block_audit_log_update_delete."""
    migration_file = base_dir / "backend" / "alembic" / "versions" / "014_auditlog_user_correlation.py"
    assert migration_file.exists()
    content = migration_file.read_text(encoding="utf-8")

    assert "CREATE TRIGGER trg_block_audit_log_update_delete" in content
    assert "BEFORE UPDATE OR DELETE ON audit_log" in content
    assert "block_audit_log_mutation()" in content
