"""Real sessions and course isolation; no dependency overrides or network."""

import time
import json
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.auth import COOKIE, hash_token
from app.models.security import User, AuthSession, CourseAccess

PASSWORD = "Unit-test-password-012345"


def account(client, username, role, course_ids=None):
    res = client.post(
        "/api/auth/users",
        json={
            "username": username,
            "password": PASSWORD,
            "role": role,
            "course_ids": course_ids or [],
        },
    )
    assert res.status_code == 201, res.text
    return res.json()["id"]


def login_as(username):
    c = TestClient(app, headers={"Origin": "http://localhost:3000"})
    res = c.post("/api/auth/login", json={"username": username, "password": PASSWORD})
    assert res.status_code == 200, res.text
    return c


@pytest.mark.parametrize(
    "method,path",
    [
        ("get", "/api/dashboard/overview"),
        ("get", "/openapi.json"),
        ("get", "/docs"),
        ("post", "/api/rps/nope/approve"),
        ("delete", "/api/quiz/nope"),
        ("post", "/api/knowledge/query"),
        ("get", "/api/audit/"),
    ],
)
def test_tanpa_login_ditolak(anonymous_client, method, path):
    assert getattr(anonymous_client, method)(path).status_code == 401
    assert anonymous_client.get("/health").status_code == 200


def test_password_sesi_cookie_dan_logout(client, db):
    u = db.query(User).filter_by(username="unitadmin").one()
    assert u.password_hash.startswith("$argon2id$") and PASSWORD not in u.password_hash
    raw = client.cookies.get(COOKIE)
    assert db.get(AuthSession, hash_token(raw)) and not db.get(AuthSession, raw)
    login = client.post(
        "/api/auth/login", json={"username": "unitadmin", "password": PASSWORD}
    )
    cookie = login.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=strict" in cookie
    assert client.post("/api/auth/logout").status_code == 200
    assert client.get("/api/auth/me").status_code == 401


def test_sesi_kedaluwarsa_ditolak(client, db):
    row = db.get(AuthSession, hash_token(client.cookies.get(COOKIE)))
    row.expires_at = time.time() - 1
    db.commit()
    assert client.get("/api/auth/me").status_code == 401


def test_login_salah_dan_pembatasan(anonymous_client):
    for _ in range(10):
        assert (
            anonymous_client.post(
                "/api/auth/login", json={"username": "unitadmin", "password": "salah"}
            ).status_code
            == 401
        )
    assert (
        anonymous_client.post(
            "/api/auth/login", json={"username": "unitadmin", "password": PASSWORD}
        ).status_code
        == 429
    )


def test_csrf_dan_cors_ditolak(client):
    assert (
        client.post(
            "/api/auth/logout", headers={"Origin": "http://jahat.test"}
        ).status_code
        == 403
    )
    assert client.post("/api/auth/logout", headers={"Origin": ""}).status_code == 403
    preflight = client.options(
        "/api/auth/login",
        headers={
            "Origin": "http://jahat.test",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert "access-control-allow-origin" not in preflight.headers


def test_dosen_hanya_mata_kuliahnya(client, buat_kuis, soal, db):
    q1 = buat_kuis([soal.mcq1], course_id="c1")
    other = client.post(
        "/api/courses/",
        json={
            "name": "Lain",
            "code": "ZZ001",
            "sks": 3,
            "semester": 1,
            "program_study": "Uji",
        },
    ).json()["id"]
    q2 = buat_kuis([soal.mcq1], course_id=other)
    account(client, "dosensatu", "dosen", ["c1"])
    with login_as("dosensatu") as dosen:
        assert dosen.get(f"/api/quiz/{q1}").status_code == 200
        assert dosen.get(f"/api/quiz/{q2}").status_code == 404
        assert dosen.delete(f"/api/quiz/{q2}").status_code == 404
        assert dosen.post(f"/api/quiz/publish/{q2}").status_code == 404
        ids = {c["id"] for c in dosen.get("/api/courses/").json()}
        assert ids == {"c1"}
        assert dosen.post(
            "/api/quiz/", json={"course_id": other, "questions": [soal.mcq1]}
        ).status_code in (403, 422)
        assert (
            dosen.post(
                "/api/materials/",
                json={"course_id": other, "title": "X", "content_text": "X"},
            ).status_code
            == 403
        )
        assert dosen.get("/api/auth/users").status_code == 403
        assert dosen.get("/api/audit/").status_code == 403
        assert dosen.get("/api/dashboard/settings").status_code in (403, 404)
    assert client.get(f"/api/quiz/{q2}").status_code == 200


@pytest.mark.parametrize(
    "method,path",
    [
        ("delete", "/api/courses/c1"),
        ("post", "/api/quiz/publish/nope"),
        ("post", "/api/grading/run/nope"),
        ("post", "/api/grading/submissions/nope/approve"),
        ("patch", "/api/grading/submissions/nope/review"),
        ("put", "/api/settings/profile"),
        ("post", "/api/auth/users"),
    ],
)
def test_penjamin_mutu_tidak_mengubah_pengajaran(client, method, path):
    account(client, "mutu", "penjamin_mutu")
    with login_as("mutu") as qm:
        assert getattr(qm, method)(path).status_code == 403


def test_penjamin_mutu_boleh_review_rps_bukan_ubah_nilai(
    client, rps_lengkap, llm, kuis_campuran, kiriman
):
    rid = client.post("/api/rps/", json=rps_lengkap).json()["rps_id"]
    account(client, "mutu", "penjamin_mutu")
    with login_as("mutu") as qm:
        assert qm.get(f"/api/dashboard/rps/{rid}").status_code == 200
        assert qm.post(f"/api/rps/{rid}/approve").status_code == 200
    account(client, "dosenlain", "dosen", [])
    with login_as("dosenlain") as dosen:
        assert dosen.post(f"/api/rps/{rid}/approve").status_code == 404


def test_perubahan_akun_mencabut_sesi(client):
    uid = account(client, "dosen", "dosen", ["c1"])
    with login_as("dosen") as dosen:
        assert dosen.get("/api/auth/me").status_code == 200
        assert (
            client.patch(f"/api/auth/users/{uid}", json={"active": False}).status_code
            == 200
        )
        assert dosen.get("/api/auth/me").status_code == 401


def test_dosen_membuat_kursus_mendapat_penugasan(client):
    account(client, "dosen", "dosen", [])
    with login_as("dosen") as dosen:
        res = dosen.post(
            "/api/courses/",
            json={
                "name": "Baru",
                "code": "NEW1",
                "sks": 3,
                "semester": 1,
                "program_study": "Uji",
            },
        )
        assert res.status_code == 200, res.text
        assert res.json()["id"] in dosen.get("/api/auth/me").json()["course_ids"]


def test_isolasi_rps_mahasiswa_analitik_dan_rag(
    client, db, rps_lengkap, llm, monkeypatch
):
    from app.models import Course, Material, Student
    from app.core import rag
    from types import SimpleNamespace

    rid = client.post("/api/rps/", json=rps_lengkap).json()["rps_id"]
    detail = client.get(f"/api/dashboard/rps/{rid}").json()
    foreign = detail["course_id"]
    db.add(
        Material(
            id="foreign-material",
            course_id=foreign,
            title="Rahasia MK lain",
            status="ready",
            content_text="Private",
        )
    )
    db.add(
        Student(id="foreign-student", course_id=foreign, nim="PRIVATE", name="Private")
    )
    db.commit()
    mid = client.post(
        "/api/materials/",
        json={"course_id": "c1", "title": "Sendiri", "content_text": "Own"},
    ).json()["id"]
    account(client, "dosen", "dosen", ["c1"])
    with login_as("dosen") as dosen:
        assert dosen.get(f"/api/dashboard/rps/{rid}").status_code == 404
        assert dosen.post(f"/api/rps/{rid}/approve").status_code == 404
        assert dosen.post(f"/api/rps/{rid}/review").status_code == 404
        assert dosen.delete(f"/api/rps/{rid}").status_code == 404
        assert dosen.get(f"/api/materials/foreign-material/content").status_code == 404
        assert dosen.delete("/api/students/foreign-student").status_code == 404
        assert dosen.get("/api/students/", params={"course_id": foreign}).json() == []
        assert (
            dosen.get(
                "/api/dashboard/analytics", params={"course_id": foreign}
            ).status_code
            == 404
        )
        assert dosen.get(
            "/api/dashboard/analytics/pdf", params={"course_id": foreign}
        ).status_code in (404, 422)
        assert dosen.get("/api/materials/").json()[0]["id"] == mid
        form = {
            k: json.dumps(rps_lengkap[k])
            for k in [
                "cpl_list",
                "cpmk_list",
                "references_list",
                "bahan_kajian",
                "learning_methods",
            ]
        }
        form.update(course_name="Hijack", course_code=rps_lengkap["course_code"])
        assert dosen.post("/api/rps/generate", data=form).status_code == 403
        seen = []

        def search(*args, **kwargs):
            seen.extend(kwargs["material_ids"])
            return [
                SimpleNamespace(
                    page_content="Secret",
                    metadata={"material_id": "foreign-material", "course_id": foreign},
                )
            ]

        monkeypatch.setattr(rag, "retrieve_materials", search)
        assert (
            dosen.post("/api/knowledge/query", json={"query": "Secret"}).json()[
                "results"
            ]
            == []
        )
        assert seen == [mid]


@pytest.mark.parametrize(
    "endpoint,payload",
    [
        ("/api/quiz/", {"questions": []}),
        ("/api/materials/", {"title": "Tidak sah", "content_text": "Rahasia"}),
    ],
)
def test_extra_config_tidak_menyamarkan_course_id(client, endpoint, payload):
    other = client.post(
        "/api/courses/",
        json={
            "name": "Lain",
            "code": "PRIVATE1",
            "sks": 3,
            "semester": 1,
            "program_study": "Uji",
        },
    ).json()["id"]
    account(client, "dosen", "dosen", ["c1"])
    with login_as("dosen") as dosen:
        response = dosen.post(
            endpoint,
            json={**payload, "course_id": other, "config": {"course_id": "c1"}},
        )
        assert response.status_code == 403, response.text


def test_cookie_secure_bawaan_untuk_https(client, monkeypatch):
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "true")
    res = client.post(
        "/api/auth/login", json={"username": "unitadmin", "password": PASSWORD}
    )
    assert "; Secure" in res.headers["set-cookie"]


def test_dosen_meninjau_dan_menyetujui_nilai_sendiri(
    client, llm, kuis_campuran, kiriman
):
    account(client, "dosen", "dosen", ["c1"])
    llm.reply('[{"id":"Q003","score":24}]')
    with login_as("dosen") as dosen:
        assert dosen.post(f"/api/grading/run/{kuis_campuran}").status_code == 200
        sub = dosen.get(f"/api/quiz/{kuis_campuran}/submissions").json()[0]
        result = dosen.patch(
            f"/api/grading/submissions/{sub['id']}/review",
            json={
                "version": sub["version"],
                "essay_scores": [{"id": "Q003", "score": 27}],
            },
        )
        assert result.status_code == 200, result.text
        approved = dosen.post(
            f"/api/grading/submissions/{sub['id']}/approve",
            json={"version": result.json()["version"]},
        )
        assert approved.status_code == 200 and approved.json()["score"] == 94


def test_bootstrap_env_hanya_eksplisit_dan_tidak_mereset_password(db, monkeypatch):
    from app.core.auth import bootstrap_from_env, check_password

    db.query(User).delete()
    db.commit()
    monkeypatch.setenv("EDUCOPILOT_ADMIN_USERNAME", "")
    monkeypatch.setenv("EDUCOPILOT_ADMIN_PASSWORD", "")
    bootstrap_from_env()
    assert db.query(User).count() == 0
    monkeypatch.setenv("EDUCOPILOT_ADMIN_USERNAME", "operator")
    with pytest.raises(RuntimeError):
        bootstrap_from_env()
    monkeypatch.setenv("EDUCOPILOT_ADMIN_PASSWORD", PASSWORD)
    bootstrap_from_env()
    db.expire_all()
    user = db.query(User).one()
    assert user.role == "admin" and check_password(user.password_hash, PASSWORD)
    monkeypatch.setenv("EDUCOPILOT_ADMIN_PASSWORD", "Password-lain-0123456")
    bootstrap_from_env()
    db.expire_all()
    assert check_password(db.query(User).one().password_hash, PASSWORD)
