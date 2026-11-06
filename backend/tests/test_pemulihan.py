"""Startup gagal aman, snapshot terverifikasi, dan ID replay tetap."""

import json
from pathlib import Path

import pytest

from app.core import database


def test_startup_db_hilang_tidak_membuat_seed(tmp_path):
    engine = database.make_engine(f"sqlite:///{tmp_path / 'hilang.db'}")
    with pytest.raises(RuntimeError, match="tidak ditemukan"):
        database.init_db(target_engine=engine)
    assert not (tmp_path / "hilang.db").exists()
    engine.dispose()


def test_init_eksplisit_kosong_seed_harus_diminta(tmp_path):
    from sqlalchemy.orm import sessionmaker
    from app.models.course import Course

    engine = database.make_engine(f"sqlite:///{tmp_path / 'baru.db'}")
    database.init_db(target_engine=engine, allow_create=True)
    with sessionmaker(bind=engine)() as db:
        assert db.query(Course).count() == 0
    database.init_db(target_engine=engine, seed_demo=True)
    with sessionmaker(bind=engine)() as db:
        assert db.query(Course).count() == 1
    engine.dispose()


def test_backup_restore_mempertahankan_manifest_dan_id(tmp_path):
    from app.core.recovery import backup_database, restore_database, verify_backup

    source = tmp_path / "source.db"
    engine = database.make_engine(f"sqlite:///{source}")
    database.init_db(target_engine=engine, allow_create=True, seed_demo=True)
    backup = backup_database(source, tmp_path / "backup")
    manifest = verify_backup(backup)
    assert manifest["tables"]["courses"]["count"] == 1
    target = tmp_path / "restore.db"
    restore_database(backup, target)
    assert verify_backup(backup)["tables"] == manifest["tables"]
    import sqlite3

    with sqlite3.connect(target) as db:
        assert db.execute("SELECT id FROM courses").fetchall() == [("c1",)]
    engine.dispose()


def test_restore_backup_rusak_ditolak_tanpa_menyentuh_target(tmp_path):
    from app.core.recovery import backup_database, restore_database

    source = tmp_path / "source.db"
    engine = database.make_engine(f"sqlite:///{source}")
    database.init_db(target_engine=engine, allow_create=True, seed_demo=True)
    backup = backup_database(source, tmp_path / "backup")
    backup.write_bytes(backup.read_bytes() + b"rusak")
    target = tmp_path / "target.db"
    target.write_bytes(b"jangan diubah")
    with pytest.raises(ValueError):
        restore_database(backup, target, replace=True)
    assert target.read_bytes() == b"jangan diubah"
    engine.dispose()


def test_restore_menolak_database_yang_masih_dipakai(tmp_path):
    from app.core.recovery import backup_database, restore_database, DatabaseLease

    source = tmp_path / "source.db"
    engine = database.make_engine(f"sqlite:///{source}")
    database.init_db(target_engine=engine, allow_create=True, seed_demo=True)
    backup = backup_database(source, tmp_path / "backup")
    with DatabaseLease(source):
        with pytest.raises(RuntimeError, match="aktif"):
            restore_database(backup, source, replace=True)
    engine.dispose()


def test_id_csv_deterministik_dan_replay_legacy_tetap(
    client, buat_kuis, unggah_jawaban, kiriman, soal
):
    qid = buat_kuis([soal.mcq1])
    text = "NIM,PG-1\n99001,B\n"
    unggah_jawaban(qid, text)
    first = kiriman(qid)[0]["id"]
    client.delete(f"/api/quiz/{qid}/submissions")
    unggah_jawaban(qid, text)
    assert kiriman(qid)[0]["id"] == first
    legacy = "NIM,PG-1,Submission ID\n99002,A,sub-legacy123\n"
    assert unggah_jawaban(qid, legacy).status_code == 200
    assert next(s for s in kiriman(qid) if s["nim"] == "99002")["id"] == "sub-legacy123"
    assert unggah_jawaban(qid, legacy).json()["added"] == 0
    conflict = "NIM,PG-1,Submission ID\n99002,B,sub-legacy123\n"
    assert unggah_jawaban(qid, conflict).status_code == 409


def test_ekspor_replay_membawa_id_lama(
    client, buat_kuis, unggah_jawaban, kiriman, soal
):
    qid = buat_kuis([soal.mcq1, soal.esai1])
    unggah_jawaban(qid, "NIM,PG-1,ESSAY-1,Submission ID\n99001,B,Isi,sub-id-lama\n")
    exported = client.get(f"/api/quiz/{qid}/replay.csv")
    assert exported.status_code == 200
    assert "sub-id-lama" in exported.text
    client.delete(f"/api/quiz/{qid}/submissions")
    assert unggah_jawaban(qid, exported.text).json()["added"] == 1
    assert kiriman(qid)[0]["id"] == "sub-id-lama"


def test_restore_membersihkan_jurnal_crash_dan_mencabut_sesi(tmp_path):
    import sqlite3
    import subprocess
    import sys
    from app.core.recovery import backup_database, restore_database, database_manifest

    source = tmp_path / "source.db"
    target = tmp_path / "target.db"
    with sqlite3.connect(source) as db:
        db.execute("CREATE TABLE payload(id INTEGER PRIMARY KEY,value TEXT)")
        db.execute("INSERT INTO payload VALUES (1,'BACKUP')")
        db.execute("CREATE TABLE auth_sessions(token_hash TEXT PRIMARY KEY)")
        db.execute("INSERT INTO auth_sessions VALUES ('revoked-token')")
    backup = backup_database(source, tmp_path / "backups")
    script = """import sqlite3,os,sys
c=sqlite3.connect(sys.argv[1]);c.execute('PRAGMA journal_mode=DELETE');c.execute('PRAGMA cache_size=5');c.execute('CREATE TABLE payload(id INTEGER PRIMARY KEY,value TEXT)');c.executemany('INSERT INTO payload VALUES (?,?)',[(i,'OLD'*2000) for i in range(1,151)]);c.commit();c.execute('BEGIN IMMEDIATE');c.execute("UPDATE payload SET value='NEW'");os._exit(0)
"""
    subprocess.run([sys.executable, "-c", script, str(target)], check=True)
    assert Path(str(target) + "-journal").exists()
    restored = restore_database(backup, target, replace=True)
    assert restored["revoked_sessions"] == 1
    assert not Path(str(target) + "-journal").exists()
    with sqlite3.connect(target) as db:
        assert db.execute("SELECT value FROM payload").fetchall() == [("BACKUP",)]
        assert db.execute("SELECT COUNT(*) FROM auth_sessions").fetchone()[0] == 0
