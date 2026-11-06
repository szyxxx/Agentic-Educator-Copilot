import json
import pytest
from app.models.audit import AuditEvent
from test_autentikasi import account, login_as


def test_audit_generate_modele_ubah_nilai_approve_publish_delete(
    client, llm, kuis_campuran, kiriman
):
    llm.reply('[{"id":"Q003","score":24,"feedback":"Baik."}]')
    assert client.post(f"/api/grading/run/{kuis_campuran}").status_code == 200
    sub = kiriman(kuis_campuran)[0]
    edited = client.patch(
        f"/api/grading/submissions/{sub['id']}/review",
        json={"version": sub["version"], "essay_scores": [{"id": "Q003", "score": 30}]},
    ).json()
    assert (
        client.post(
            f"/api/grading/submissions/{sub['id']}/approve",
            json={"version": edited["version"]},
        ).status_code
        == 200
    )
    assert client.post(f"/api/quiz/publish/{kuis_campuran}").status_code == 200
    assert client.delete(f"/api/quiz/{kuis_campuran}").status_code == 200
    data = client.get("/api/audit/?limit=500").json()
    actions = {e["action"] for e in data["events"]}
    assert {"grade_propose", "grade_edit", "approve", "publish", "delete"} <= actions
    grading = [e for e in data["events"] if e["object_id"] == sub["id"]]
    assert any(e["llm_model"] and "FakeLLM" in e["llm_model"] for e in grading)
    versions = [e["version"] for e in reversed(grading)]
    assert versions == sorted(set(versions))
    assert all(
        e["actor_name"] == "unitadmin"
        and e["occurred_at"]
        and e["application_version"]
        and e["request_id"]
        for e in grading
    )
    assert "Unit-test-password" not in json.dumps(data)


def test_login_gagal_tercatat_tanpa_password(client, anonymous_client):
    client.post(
        "/api/auth/login",
        json={"username": "unitadmin", "password": "SECRET-FOR-FAILED-LOGIN"},
    )
    data = client.get("/api/audit/?action=login_failed").json()
    assert data["total"] == 1
    event = data["events"][0]
    assert event["actor_name"] == "unitadmin" and event["action"] == "login_failed"
    assert "SECRET-FOR-FAILED-LOGIN" not in json.dumps(data)


def test_audit_hanya_admin_dan_penjamin_mutu(client):
    account(client, "mutu", "penjamin_mutu")
    account(client, "dosen", "dosen", ["c1"])
    with login_as("mutu") as qm:
        assert qm.get("/api/audit/").status_code == 200
        assert qm.delete("/api/audit/anything").status_code == 403
    with login_as("dosen") as dosen:
        assert dosen.get("/api/audit/").status_code == 403


def test_transaksi_gagal_tidak_meninggalkan_audit_sukses(
    client, llm, rps_lengkap, monkeypatch
):
    from app.api.v1 import rps as api

    llm.reply(
        lambda prompt: (
            json.dumps(rps_lengkap["meetings"]) if "16 elemen" in prompt else "Tren"
        )
    )
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
    form.update(course_name="Uji", course_code="ROLLBACK-AUDIT")
    monkeypatch.setattr(
        api,
        "_refresh_compliance",
        lambda *args: (_ for _ in ()).throw(RuntimeError("DB gagal")),
    )
    assert client.post("/api/rps/generate", data=form).status_code == 503
    events = client.get("/api/audit/?limit=500").json()["events"]
    assert not any(
        e["action"] == "generate" and e["object_type"] in ("rps", "courses")
        for e in events
    )
    assert any(e["action"] == "operation_failed" for e in events)


def test_penolakan_versi_tidak_mencatat_approve_palsu(
    client, llm, kuis_campuran, kiriman
):
    llm.reply('[{"id":"Q003","score":24}]')
    client.post(f"/api/grading/run/{kuis_campuran}")
    sub = kiriman(kuis_campuran)[0]
    assert (
        client.post(
            f"/api/grading/submissions/{sub['id']}/approve",
            json={"version": sub["version"] - 1},
        ).status_code
        == 409
    )
    assert (
        client.get(f"/api/audit/?action=approve&object_id={sub['id']}").json()["total"]
        == 0
    )


def test_auto_dibuat_saat_approve_nilai_dicatat_generate_bukan_persetujuan_materi(
    client, llm, rps_lengkap, buat_kuis, unggah_jawaban, soal, kiriman
):
    rid = client.post("/api/rps/", json=rps_lengkap).json()["rps_id"]
    cid = client.get(f"/api/dashboard/rps/{rid}").json()["course_id"]
    qid = buat_kuis([soal.esai1], course_id=cid, week_number=3)
    unggah_jawaban(qid, "NIM,ESSAY-1\n123,Jawaban\n")
    llm.reply('[{"id":"Q003","score":24}]')
    client.post(f"/api/grading/run/{qid}")
    sub = kiriman(qid)[0]
    llm.reply("# Materi penguatan\nPerlu diperiksa.")
    result = client.post(
        f"/api/grading/submissions/{sub['id']}/approve",
        json={"version": sub["version"]},
    )
    mid = result.json()["auto_material_id"]
    assert mid
    events = client.get(f"/api/audit/?object_id={mid}").json()["events"]
    assert {e["action"] for e in events} == {"generate"}
    material = next(m for m in client.get("/api/materials/").json() if m["id"] == mid)
    assert (
        client.post(
            f"/api/materials/{mid}/approve", json={"version": material["version"]}
        ).status_code
        == 200
    )
    events = client.get(f"/api/audit/?object_id={mid}").json()["events"]
    assert {e["action"] for e in events} == {"generate", "approve", "index"}
