import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture()
def client(tmp_path, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setattr(settings, "photo_root", tmp_path / "photos")
    monkeypatch.setattr(settings, "thumb_dir", tmp_path / "thumbs")
    monkeypatch.setattr(settings, "auth_enabled", False)
    monkeypatch.setattr(settings, "require_2fa", True)
    from app.auth import ip_limiter
    ip_limiter.reset()
    (tmp_path / "photos").mkdir()
    from fastapi.testclient import TestClient
    from app.main import create_app
    app = create_app(f"sqlite:///{tmp_path / 'test.db'}")
    with TestClient(app) as c:
        yield c
