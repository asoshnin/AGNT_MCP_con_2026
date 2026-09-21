"""Pytest configuration and fixtures for AGNTCon + MCPCon Hub."""

import os
import sys

import pytest

# Ensure 02_public_hub is in sys.path
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
HUB_DIR = os.path.dirname(TEST_DIR)
if HUB_DIR not in sys.path:
    sys.path.insert(0, HUB_DIR)

import analytics_db
import crm_db


@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Ensure test environment does not write to production files or leak secrets."""
    os.environ["PROJECT_NAME"] = "AGNTCon Test Suite"
    os.environ["PUBLIC_URL"] = "http://127.0.0.1:8088"
    yield

@pytest.fixture
def temp_crm_db(monkeypatch, tmp_path):
    """Provides an isolated SQLite CRM database for testing."""
    test_db = str(tmp_path / "test_crm.sqlite")
    monkeypatch.setattr(crm_db, "DB_PATH", test_db)
    crm_db.init_crm_db()
    return test_db

@pytest.fixture
def temp_analytics_db(monkeypatch, tmp_path):
    """Provides an isolated SQLite Analytics database for testing."""
    test_db = str(tmp_path / "test_analytics.sqlite")
    monkeypatch.setattr(analytics_db, "DB_PATH", test_db)
    monkeypatch.setenv("ANALYTICS_DB_PATH", test_db)
    analytics_db.init_analytics_db(test_db)
    return test_db
