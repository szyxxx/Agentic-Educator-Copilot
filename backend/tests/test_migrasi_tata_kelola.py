import shutil
from pathlib import Path
from sqlalchemy import text
from app.core.database import init_db, make_engine
from app.core.recovery import database_manifest


def test_migrasi_salinan_db_repo_idempoten_dan_id_tetap(tmp_path):
    original = Path(__file__).resolve().parents[1] / "educopilot.db"
    copied = tmp_path / "legacy.db"
    shutil.copyfile(original, copied)
    target = make_engine(f"sqlite:///{copied}")
    before = database_manifest(copied)
    with target.connect() as c:
        old_ids = {
            table: set(c.execute(text(f"SELECT id FROM {table}")).scalars())
            for table in (
                "courses",
                "rps",
                "quizzes",
                "submissions",
                "materials",
                "students",
            )
        }
    init_db(target_engine=target)
    first = database_manifest(copied)
    init_db(target_engine=target)
    assert database_manifest(copied) == first
    with target.connect() as c:
        for table, ids in old_ids.items():
            assert set(c.execute(text(f"SELECT id FROM {table}")).scalars()) == ids
        assert (
            c.execute(
                text(
                    "SELECT COUNT(*) FROM materials WHERE material_type='AUTO' AND status='ready'"
                )
            ).scalar()
            == 0
        )
        assert c.execute(text("SELECT COUNT(*) FROM users")).scalar() == 0
        assert c.execute(text("SELECT COUNT(*) FROM auth_sessions")).scalar() == 0
        assert (
            c.execute(
                text(
                    "SELECT COUNT(*) FROM submissions s JOIN quizzes q ON s.quiz_id=q.id, json_each(q.questions) j WHERE json_extract(j.value,'$.type')='essay' AND s.score IS NOT NULL"
                )
            ).scalar()
            == 0
        )
    target.dispose()
