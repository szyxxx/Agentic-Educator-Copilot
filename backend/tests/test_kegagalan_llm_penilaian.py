"""Kegagalan LLM tidak boleh menjadi nilai final; penilaian bisa diulang."""

import json

import pytest

from app.agents.grading_agent import grade_essay_node

CATATAN_GAGAL = "Gagal menilai otomatis. Mohon dinilai manual."


def _bukan_json(llm):
    llm.reply("Maaf, saya tidak bisa menilai jawaban ini.")


def _objek_bukan_array(llm):
    llm.reply('{"id": "Q003", "score": 30}')


def _koneksi_putus(llm):
    llm.fail()


def _kunci_tidak_ada(llm):
    llm.fail(RuntimeError("No LLM provider configured."))


def _konten_blok(llm):
    # Bentuk `content` bisa berupa list blok, `.replace` lalu gagal.
    llm.reply([{"type": "text", "text": '[{"id": "Q003", "score": 30}]'}])


MODE_GAGAL = pytest.mark.parametrize(
    "gagalkan",
    [_koneksi_putus, _kunci_tidak_ada, _bukan_json, _objek_bukan_array, _konten_blok],
)


@MODE_GAGAL
def test_node_esai_gagal_tidak_memberi_nilai_final(soal, llm, gagalkan):
    gagalkan(llm)
    hasil = grade_essay_node({"questions": [soal.esai1], "student_answers": {}})
    assert hasil["essay_scores"] == [
        {"id": "Q003", "score": None, "feedback": CATATAN_GAGAL, "max_score": 30.0}
    ]


@MODE_GAGAL
def test_esai_gagal_berstatus_manual_dengan_mcq_tetap_tercatat(client, llm, kuis_campuran, kiriman, gagalkan):
    gagalkan(llm)
    res = client.post(f"/api/grading/run/{kuis_campuran}")
    assert res.status_code == 503
    assert res.json()["data"]["failed_count"] == 1
    assert res.json()["data"]["graded_count"] == 0
    [sub] = kiriman(kuis_campuran)
    assert sub["score"] is None
    assert sub["status"] == "manual_review"
    assert "MCQ benar 2/2" in sub["feedback"]
    assert CATATAN_GAGAL in sub["feedback"]
    assert "perlu diperdalam" not in sub["feedback"]
    assert client.get(f"/api/quiz/{kuis_campuran}").json()["status"] == "active"
    analytics = client.get("/api/dashboard/analytics?course_id=c1").json()
    assert analytics["per_student"] == []


@pytest.mark.parametrize("score", ["tinggi", None, "nan", "inf", True])
def test_skor_tidak_valid_perlu_dinilai_ulang(client, llm, kuis_campuran, kiriman, score):
    llm.reply(json.dumps([{"id": "Q003", "score": score}]))
    res = client.post(f"/api/grading/run/{kuis_campuran}")
    assert res.status_code == 503
    assert kiriman(kuis_campuran)[0]["status"] == "manual_review"
    assert kiriman(kuis_campuran)[0]["score"] is None


def test_kegagalan_materi_otomatis_tidak_menggagalkan_penilaian(
    client, llm, rps_lengkap, buat_kuis, unggah_jawaban, soal
):
    rps = client.post("/api/rps/", json=rps_lengkap).json()["rps_id"]
    course_id = client.get(f"/api/dashboard/rps/{rps}").json()["course_id"]
    quiz_id = buat_kuis([soal.mcq1], course_id=course_id, week_number=3)
    unggah_jawaban(quiz_id, "NIM Mahasiswa,PG-1\n123,B\n")
    llm.fail()

    body = client.post(f"/api/grading/run/{quiz_id}").json()

    assert body["status"] == "success"
    assert body["data"]["average_score"] == 100.0
    assert body["data"]["auto_material_id"] is None
    assert client.get("/api/materials/", params={"rps_id": rps}).json() == []


# --- Perlindungan nilai dan kemampuan mengulang ----------------------------


def test_esai_gagal_tidak_menjadi_nilai_final(client, llm, kuis_campuran, kiriman):
    llm.fail()
    client.post(f"/api/grading/run/{kuis_campuran}")
    [sub] = kiriman(kuis_campuran)
    assert sub["status"] != "graded" or sub["score"] is None


def test_catatan_gagal_terlihat_oleh_dosen(client, llm, kuis_campuran, kiriman):
    llm.fail()
    client.post(f"/api/grading/run/{kuis_campuran}")
    assert "Gagal menilai" in kiriman(kuis_campuran)[0]["feedback"]


def test_respons_api_melaporkan_kegagalan_esai(client, llm, kuis_campuran):
    llm.fail()
    body = client.post(f"/api/grading/run/{kuis_campuran}").json()
    assert body["status"] != "success" or body["data"].get("failed_count")


def test_esai_gagal_bisa_dinilai_ulang_setelah_llm_pulih(
    client, llm, kuis_campuran, kiriman
):
    llm.fail()
    client.post(f"/api/grading/run/{kuis_campuran}")
    llm.reply(json.dumps([{"id": "Q003", "score": 30}]))
    client.post(f"/api/grading/run/{kuis_campuran}")
    assert kiriman(kuis_campuran)[0]["score"] == 100.0


def test_jawaban_llm_parsial_tidak_diam_diam_nol(soal, llm):
    llm.reply(json.dumps([{"id": "Q003", "score": 25, "feedback": "Baik."}]))
    hasil = grade_essay_node(
        {"questions": [soal.esai1, soal.esai2], "student_answers": {}}
    )
    hilang = next(e for e in hasil["essay_scores"] if e["id"] == "Q004")
    assert hilang["feedback"], "soal yang tidak dinilai harus ditandai"


def test_array_kosong_dari_llm_dianggap_gagal(soal, llm):
    llm.reply("[]")
    hasil = grade_essay_node({"questions": [soal.esai1], "student_answers": {}})
    assert hasil["essay_scores"][0]["feedback"] == CATATAN_GAGAL


def test_batch_parsial_menandai_gagal_dan_retry_tidak_menimpa_nilai_lama(client, llm, kuis_campuran, unggah_jawaban, kiriman):
    unggah_jawaban(kuis_campuran, "NIM,PG-1,PG-2,ESSAY-1\n00000002,B,C,JAWABAN_GAGAL\n")
    llm.reply(lambda prompt: "[]" if "JAWABAN_GAGAL" in prompt else '[{"id":"Q003","score":30,"feedback":"Tepat."}]')
    body = client.post(f"/api/grading/run/{kuis_campuran}").json()
    assert body["status"] == "partial"
    assert body["data"]["failed_count"] == body["data"]["graded_count"] == 1
    first, second = kiriman(kuis_campuran)
    assert first["score"] == 100
    assert second["score"] is None
    assert client.get(f"/api/quiz/{kuis_campuran}").json()["progress_percent"] == 67
    llm.reply('[{"id":"Q003","score":15,"feedback":"Cukup."}]')
    body = client.post(f"/api/grading/run/{kuis_campuran}").json()
    assert body["status"] == "success"
    assert body["data"]["graded_count"] == 1
    assert [s["score"] for s in kiriman(kuis_campuran)] == [100, 70]
    assert body["data"]["average_score"] == 85
    assert client.get(f"/api/quiz/{kuis_campuran}").json()["status"] == "completed"


def test_esai_parsial_api_belum_final(client, llm, buat_kuis, unggah_jawaban, kiriman, soal):
    qid = buat_kuis([soal.esai1, soal.esai2])
    unggah_jawaban(qid, "NIM,ESSAY-1,ESSAY-2\n00000001,Isi,Isi\n")
    llm.reply('[{"id":"Q003","score":25,"feedback":"Bagus."}]')
    assert client.post(f"/api/grading/run/{qid}").status_code == 503
    [sub] = kiriman(qid)
    assert sub["score"] is None
    assert "Q003: Bagus." in sub["feedback"]
    assert "Q004: Gagal menilai" in sub["feedback"]
