import json
import pytest


def test_usulan_llm_bukan_nilai_final(client, llm, kuis_campuran, kiriman):
    llm.reply('[{"id":"Q003","score":24,"feedback":"Baik."}]')
    body = client.post(f"/api/grading/run/{kuis_campuran}").json()
    [sub] = kiriman(kuis_campuran)
    assert sub["score"] is None
    assert sub["proposed_score"] == 88
    assert sub["status"] == "needs_review"
    assert sub["question_scores"][2]["score"] == 24
    assert body["data"]["proposed_count"] == 1
    assert (
        client.get("/api/dashboard/analytics?course_id=c1").json()["per_student"] == []
    )


def test_dosen_mengubah_esai_lalu_menyetujui_dengan_versi(
    client, llm, kuis_campuran, kiriman
):
    llm.reply('[{"id":"Q003","score":24,"feedback":"Baik."}]')
    client.post(f"/api/grading/run/{kuis_campuran}")
    [sub] = kiriman(kuis_campuran)
    edit = client.patch(
        f"/api/grading/submissions/{sub['id']}/review",
        json={
            "version": sub["version"],
            "essay_scores": [
                {"id": "Q003", "score": 30, "feedback": "Diperiksa dosen."}
            ],
        },
    )
    assert edit.status_code == 200, edit.text
    updated = kiriman(kuis_campuran)[0]
    assert updated["score"] is None and updated["proposed_score"] == 100
    assert (
        client.post(
            f"/api/grading/submissions/{sub['id']}/approve",
            json={"version": sub["version"]},
        ).status_code
        == 409
    )
    res = client.post(
        f"/api/grading/submissions/{sub['id']}/approve",
        json={"version": updated["version"]},
    )
    assert res.status_code == 200, res.text
    final = kiriman(kuis_campuran)[0]
    assert (
        final["score"] == 100 and final["status"] == "graded" and final["reviewed_by"]
    )
    assert final["question_scores"][2]["source"] == "human"


@pytest.mark.parametrize("score", [-1, 31, "tinggi", True])
def test_edit_esai_invalid_ditolak(client, llm, kuis_campuran, kiriman, score):
    llm.reply('[{"id":"Q003","score":24,"feedback":"Baik."}]')
    client.post(f"/api/grading/run/{kuis_campuran}")
    sub = kiriman(kuis_campuran)[0]
    res = client.patch(
        f"/api/grading/submissions/{sub['id']}/review",
        json={
            "version": sub["version"],
            "essay_scores": [{"id": "Q003", "score": score}],
        },
    )
    assert res.status_code in (400, 422)
    assert kiriman(kuis_campuran)[0]["score"] is None


def test_esai_gagal_bisa_dinilai_manual_dan_disetujui(
    client, llm, kuis_campuran, kiriman
):
    llm.fail()
    client.post(f"/api/grading/run/{kuis_campuran}")
    sub = kiriman(kuis_campuran)[0]
    assert sub["status"] == "manual_review"
    assert (
        client.post(
            f"/api/grading/submissions/{sub['id']}/approve",
            json={"version": sub["version"]},
        ).status_code
        == 400
    )
    edit = client.patch(
        f"/api/grading/submissions/{sub['id']}/review",
        json={"version": sub["version"], "essay_scores": [{"id": "Q003", "score": 15}]},
    )
    assert edit.status_code == 200, edit.text
    assert (
        client.post(
            f"/api/grading/submissions/{sub['id']}/approve",
            json={"version": edit.json()["version"]},
        ).status_code
        == 200
    )
    assert kiriman(kuis_campuran)[0]["score"] == 70


def test_auto_menunggu_persetujuan_dan_belum_diindeks(
    client, llm, rag_palsu, rps_lengkap, buat_kuis, unggah_jawaban, soal
):
    rid = client.post("/api/rps/", json=rps_lengkap).json()["rps_id"]
    cid = client.get(f"/api/dashboard/rps/{rid}").json()["course_id"]
    qid = buat_kuis([soal.mcq1], course_id=cid, week_number=3)
    unggah_jawaban(qid, "NIM,PG-1\n123,B\n")
    llm.reply("# Penguatan\nIsi diperiksa.")
    client.post(f"/api/grading/run/{qid}")
    [material] = client.get("/api/materials/", params={"rps_id": rid}).json()
    assert material["status"] == "pending_review"
    assert rag_palsu.indexed == []
    res = client.post(
        f"/api/materials/{material['id']}/approve",
        json={"version": material["version"]},
    )
    assert res.status_code == 200, res.text
    [approved] = client.get("/api/materials/", params={"rps_id": rid}).json()
    assert approved["status"] == "ready" and approved["approved_by"]
    assert approved["index_status"] == "indexed" and len(rag_palsu.indexed) == 1


def test_inferensi_lama_tidak_menimpa_keputusan_manusia(
    client, llm, kuis_campuran, kiriman, monkeypatch
):
    from app.api.v1 import grading
    from app.core.database import SessionLocal
    from app.models.submission import Submission
    from types import SimpleNamespace

    sid = kiriman(kuis_campuran)[0]["id"]

    def infer(_):
        with SessionLocal() as other:
            sub = other.get(Submission, sid)
            sub.score = 100
            sub.proposed_score = 100
            sub.status = "graded"
            sub.version = 3
            sub.reviewed_by = "human-concurrent"
            sub.question_scores = [
                {
                    "id": "Q003",
                    "type": "essay",
                    "score": 30,
                    "max_score": 30,
                    "source": "human",
                    "feedback": "Sudah diperiksa.",
                }
            ]
            other.commit()
        return {
            "total_score": 70,
            "essay_scores": [{"id": "Q003", "score": 15}],
            "grading_model": "slow-fake",
        }

    monkeypatch.setattr(
        grading, "build_grading_graph", lambda: SimpleNamespace(invoke=infer)
    )
    res = client.post(f"/api/grading/run/{kuis_campuran}")
    assert res.status_code == 409, res.text
    sub = kiriman(kuis_campuran)[0]
    assert sub["score"] == 100 and sub["status"] == "graded" and sub["version"] == 3
    assert sub["question_scores"][0]["source"] == "human"


def test_pending_auto_tidak_dipakai_pencarian_meski_ada_di_chroma(client, monkeypatch):
    from app.core import rag
    from types import SimpleNamespace

    mid = client.post(
        "/api/materials/",
        json={
            "course_id": "c1",
            "title": "Draft",
            "material_type": "AUTO",
            "content_text": "Belum disetujui",
        },
    ).json()["id"]
    client.post(
        "/api/materials/",
        json={"course_id": "c1", "title": "Materi manual", "content_text": "Siap"},
    )
    seen = []

    def retrieve(*args, **kwargs):
        seen.extend(kwargs["material_ids"])
        return [
            SimpleNamespace(
                page_content="Draft", metadata={"material_id": mid, "course_id": "c1"}
            )
        ]

    monkeypatch.setattr(rag, "retrieve_materials", retrieve)
    assert (
        client.post("/api/knowledge/query", json={"query": "Draft"}).json()["results"]
        == []
    )
    assert mid not in seen


def test_kuis_perlu_tinjauan_tetap_terlihat(client, llm, kuis_campuran):
    llm.reply('[{"id":"Q003","score":24}]')
    client.post(f"/api/grading/run/{kuis_campuran}")
    data = client.get("/api/dashboard/quizzes").json()
    assert kuis_campuran in [q["id"] for q in data["needs_attention"]]
