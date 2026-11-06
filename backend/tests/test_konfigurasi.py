"""Konfigurasi instalasi dan lokasi indeks."""
import importlib
from pathlib import Path
import tomllib


def test_chroma_persist_dir_dari_environment(monkeypatch, tmp_path):
    from app.core import rag

    target = str(tmp_path / "indeks")
    try:
        with monkeypatch.context() as env:
            env.setenv("CHROMA_PERSIST_DIR", target)
            importlib.reload(rag)
            assert rag.CHROMA_PERSIST_DIR == target
    finally:
        importlib.reload(rag)


def test_requirements_sama_dengan_dependensi_runtime():
    root = Path(__file__).resolve().parents[1]
    project = tomllib.loads((root / "pyproject.toml").read_text())
    requirements = {line.strip() for line in (root / "requirements.txt").read_text().splitlines() if line.strip() and not line.startswith("#")}
    assert requirements == set(project["project"]["dependencies"])
    assert not any(item.startswith("pytest") for item in requirements)
    assert any(item.startswith("pytest") for item in project["dependency-groups"]["dev"])
