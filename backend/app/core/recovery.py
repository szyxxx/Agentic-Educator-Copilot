"""Managed SQLite snapshots. Backup/restore outputs always live outside the repository."""

from __future__ import annotations

import base64
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
from datetime import datetime, timezone
from uuid import uuid4

REPO_ROOT = Path(__file__).resolve().parents[3]


def external_path(path: str | Path) -> Path:
    path = Path(path).expanduser().resolve()
    if path.is_relative_to(REPO_ROOT):
        raise ValueError("Hasil backup/restore wajib di luar repo.")
    return path


def connect_readonly(path: Path):
    return sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)


class DatabaseLease:
    """Application holds a shared lease; offline restore requires an exclusive lease."""

    def __init__(self, path, exclusive=False):
        self.path = Path(str(Path(path).resolve()) + ".lock")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.fd = os.open(self.path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            fcntl.flock(
                self.fd, (fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH) | fcntl.LOCK_NB
            )
        except BlockingIOError:
            os.close(self.fd)
            raise RuntimeError(
                "Database masih aktif. Hentikan backend/penulis sebelum restore."
            )

    def close(self):
        if self.fd is not None:
            fcntl.flock(self.fd, fcntl.LOCK_UN)
            os.close(self.fd)
            self.fd = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def _quoted(name):
    return '"' + name.replace('"', '""') + '"'


def database_manifest(path: Path) -> dict:
    tables = {}
    with connect_readonly(path) as db:
        if db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
            raise ValueError("Integritas SQLite gagal.")
        schema = db.execute(
            "SELECT type,name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"
        ).fetchall()
        for (name,) in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ):
            columns = db.execute(f"PRAGMA table_info({_quoted(name)})").fetchall()
            order = [c[1] for c in sorted(columns, key=lambda c: c[5]) if c[5]] or [
                c[1] for c in columns
            ]
            rows = db.execute(
                f"SELECT * FROM {_quoted(name)} ORDER BY "
                + ",".join(_quoted(c) for c in order)
            ).fetchall()

            def encode(v):
                return (
                    {"bytes": base64.b64encode(v).decode()}
                    if isinstance(v, bytes)
                    else v
                )

            canonical = json.dumps(
                [[encode(v) for v in row] for row in rows],
                ensure_ascii=False,
                separators=(",", ":"),
            )
            tables[name] = {
                "count": len(rows),
                "sha256": hashlib.sha256(canonical.encode()).hexdigest(),
            }
        return {
            "schema_sha256": hashlib.sha256(
                json.dumps(schema, separators=(",", ":")).encode()
            ).hexdigest(),
            "tables": tables,
        }


def backup_database(source: str | Path, output_dir: str | Path) -> Path:
    source = Path(source).resolve()
    if not source.is_file():
        raise ValueError("Database sumber tidak ditemukan.")
    output_dir = external_path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    backup = (
        output_dir
        / f"backup-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}.db"
    )
    fd = os.open(backup, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    try:
        with connect_readonly(source) as src, sqlite3.connect(backup) as dst:
            src.backup(dst)
        manifest = database_manifest(backup)
        manifest.update(
            format=1,
            created_at=datetime.now(timezone.utc).isoformat(),
            sha256=hashlib.sha256(backup.read_bytes()).hexdigest(),
        )
        manifest_path = Path(str(backup) + ".json")
        with os.fdopen(
            os.open(manifest_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), "w"
        ) as f:
            json.dump(manifest, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        with backup.open("rb") as f:
            os.fsync(f.fileno())
        verify_backup(backup)
        return backup
    except Exception:
        backup.unlink(missing_ok=True)
        Path(str(backup) + ".json").unlink(missing_ok=True)
        raise


def verify_backup(backup: str | Path) -> dict:
    backup = Path(backup).resolve()
    manifest = json.loads(Path(str(backup) + ".json").read_text())
    if manifest.get("format") != 1 or hashlib.sha256(
        backup.read_bytes()
    ).hexdigest() != manifest.get("sha256"):
        raise ValueError("Checksum backup tidak cocok.")
    current = database_manifest(backup)
    if any(current[key] != manifest.get(key) for key in ["schema_sha256", "tables"]):
        raise ValueError("Manifest isi/schema backup tidak cocok.")
    return manifest


def restore_database(backup: str | Path, target: str | Path, *, replace=False) -> dict:
    backup = Path(backup).resolve()
    target = external_path(target)
    if target == backup:
        raise ValueError("Target restore harus berbeda dari backup.")
    manifest = verify_backup(backup)
    target.parent.mkdir(parents=True, exist_ok=True)
    with DatabaseLease(target, exclusive=True):
        if target.exists() and not replace:
            raise ValueError(
                "Target sudah ada; gunakan --replace setelah backend dihentikan."
            )
        fd, name = tempfile.mkstemp(prefix=".restore-", suffix=".db", dir=target.parent)
        os.close(fd)
        temporary = Path(name)
        try:
            shutil.copyfile(backup, temporary)
            os.chmod(temporary, 0o600)
            if database_manifest(temporary) != {
                k: manifest[k] for k in ["schema_sha256", "tables"]
            }:
                raise ValueError("Verifikasi target restore gagal.")
            # A restored snapshot must not resurrect sessions revoked after its creation.
            with sqlite3.connect(temporary) as db:
                has_sessions = db.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='auth_sessions'"
                ).fetchone()
                revoked = (
                    db.execute("SELECT COUNT(*) FROM auth_sessions").fetchone()[0]
                    if has_sessions
                    else 0
                )
                if has_sessions:
                    db.execute("DELETE FROM auth_sessions")
            expected_restored = database_manifest(temporary)
            with temporary.open("rb") as f:
                os.fsync(f.fileno())
            for suffix in ["-wal", "-shm", "-journal"]:
                Path(str(target) + suffix).unlink(missing_ok=True)
            os.replace(temporary, target)
            if database_manifest(target) != expected_restored:
                raise ValueError(
                    "Verifikasi sesudah restore gagal. Jangan mulai backend."
                )
            directory = os.open(target.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            temporary.unlink(missing_ok=True)
    return {
        "restored": str(target),
        "backup_sha256": manifest["sha256"],
        "verified_tables": manifest["tables"],
        "revoked_sessions": revoked,
    }
