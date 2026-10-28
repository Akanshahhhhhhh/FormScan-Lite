r"""Shared setup for all FormScan-Lite backend tests.

Run from the backend folder:
    ..\venv\Scripts\python.exe -m pytest          (fast tests, about seconds)
    ..\venv\Scripts\python.exe -m pytest --run-slow   (also real translate/TTS)
"""
import os
import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.chdir(BACKEND_DIR)  # app.py uses relative folders (logs, uploads)

FEEDBACK_FILE = BACKEND_DIR / "data" / "feedback.jsonl"


def pytest_addoption(parser):
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="also run slow tests (model loading, internet)",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-slow"):
        return
    skip_slow = pytest.mark.skip(reason="slow test: add --run-slow to run it")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


@pytest.fixture(scope="session")
def client():
    from app import app

    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def keep_feedback_file():
    """Put feedback.jsonl back exactly as it was after a test that saves a vote."""
    existed = FEEDBACK_FILE.exists()
    before = FEEDBACK_FILE.read_bytes() if existed else b""
    yield
    if existed:
        FEEDBACK_FILE.write_bytes(before)
    elif FEEDBACK_FILE.exists():
        FEEDBACK_FILE.unlink()
