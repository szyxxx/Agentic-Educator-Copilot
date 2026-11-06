"""Kegagalan LLM saat menilai esai.

Bagian pertama merekam perilaku SEKARANG dan lolos. Bagian kedua menuliskan
perilaku yang seharusnya dan ditandai `xfail(strict=True)`, sehingga saat
bugnya diperbaiki (A20) tes akan gagal sebagai XPASS dan penandanya harus
dibuang bersama tes perekam yang bertentangan.

Skenario ini sama dengan G1 di `docs/analisis-gap-ganai.md` bagian 5.16.
"""

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


# --- Perilaku sekarang (rekaman) --------------------------------------------


@MODE_GAGAL
def test_rekam_node_esai_memberi_nol_dengan_catatan(soal, llm, gagalkan):
    gagalkan(llm)
    hasil = grade_essay_node({"questions": [soal.esai1], "student_answers": {}})
    assert hasil["essay_scores"] == [
        {"id": "Q003", "score": 0.0, "feedback": CATATAN_GAGAL, "max_score": 30.0}
    ]


@MODE_GAGAL
def test_rekam_nilai_akhir_tersimpan_sebagai_graded(
    client, llm, kuis_campuran, kiriman, gagalkan
):
    gagalkan(llm)

    body = client.post(f"/api/grading/run/{kuis_campuran}").json()

    # MCQ benar 20 dari 50, esai dihitung 0, respons tetap sukses.
    assert body["status"] == "success"
    assert body["data"]["graded_count"] == 1
    assert body["data"]["average_score"] == 40.0
    [sub] = kiriman(kuis_campuran)
    assert sub["score"] == 40.0
    assert sub["status"] == "graded"


def test_rekam_catatan_gagal_tidak_tersimpan(client, llm, kuis_campuran, kiriman):
    llm.fail()
    client.post(f"/api/grading/run/{kuis_campuran}")
    [sub] = kiriman(kuis_campuran)
    assert CATATAN_GAGAL not in sub["feedback"]
    assert sub["feedback"] == (
        "Skor total 40.0 dari 100. MCQ benar 2/2. "
        "Soal esai yang perlu diperdalam: Q003."
    )


def test_rekam_llm_pulih_tidak_menilai_ulang(client, llm, kuis_campuran, kiriman):
    llm.fail()
    client.post(f"/api/grading/run/{kuis_campuran}")
    jumlah_panggilan = len(llm.prompts)

    llm.reply(json.dumps([{"id": "Q003", "score": 30}]))
    res = client.post(f"/api/grading/run/{kuis_campuran}")

    assert res.json()["data"]["graded_count"] == 0
    assert len(llm.prompts) == jumlah_panggilan
    assert kiriman(kuis_campuran)[0]["score"] == 40.0


def test_rekam_kuis_ditandai_perlu_remedial_karena_nol_palsu(
    client, llm, kuis_campuran
):
    llm.fail()
    client.post(f"/api/grading/run/{kuis_campuran}")
    assert client.get(f"/api/quiz/{kuis_campuran}").json()["status"] == "attention"


def test_rekam_mcq_tetap_dinilai_saat_llm_mati(client, llm, kuis_campuran):
    llm.fail()
    body = client.post(f"/api/grading/run/{kuis_campuran}").json()
    assert body["data"]["weak_topics"] == ["Jelaskan konsep regresi."]


def test_rekam_skor_bukan_angka_membatalkan_seluruh_submission(
    client, llm, kuis_campuran, kiriman
):
    # Berbeda dari JSON rusak: `float("tinggi")` berada di luar blok try, jadi
    # submission tetap belum dinilai dan bisa diulang.
    llm.reply(json.dumps([{"id": "Q003", "score": "tinggi"}]))

    body = client.post(f"/api/grading/run/{kuis_campuran}").json()

    assert body["status"] == "error"
    [sub] = kiriman(kuis_campuran)
    assert sub["score"] is None
    assert sub["status"] == "submitted"


def test_rekam_kegagalan_materi_otomatis_tidak_menggagalkan_penilaian(
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


# --- Perilaku yang seharusnya (xfail) ---------------------------------------


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=(
        "BUG: esai yang gagal dinilai menjadi 0 final berstatus 'graded'. "
        "Mahasiswa dengan MCQ sempurna mendapat 40, bukan status perlu "
        "dinilai manusia (grading_agent.py:122-130, grading.py:73-75). FK2/G1."
    ),
)
def test_esai_gagal_tidak_menjadi_nilai_final(client, llm, kuis_campuran, kiriman):
    llm.fail()
    client.post(f"/api/grading/run/{kuis_campuran}")
    [sub] = kiriman(kuis_campuran)
    assert sub["status"] != "graded" or sub["score"] is None


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=(
        "BUG: catatan 'Gagal menilai otomatis' dibuat lalu dibuang. feedback_node "
        "tidak membacanya, sehingga dosen melihat 'perlu diperdalam', seolah "
        "jawaban mahasiswa lemah (grading_agent.py:169-186)."
    ),
)
def test_catatan_gagal_terlihat_oleh_dosen(client, llm, kuis_campuran, kiriman):
    llm.fail()
    client.post(f"/api/grading/run/{kuis_campuran}")
    assert "Gagal menilai" in kiriman(kuis_campuran)[0]["feedback"]


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=(
        "BUG: API melapor sukses saat seluruh esai gagal dinilai "
        "(grading.py:128), dan UI menampilkan 'submission dinilai'."
    ),
)
def test_respons_api_melaporkan_kegagalan_esai(client, llm, kuis_campuran):
    llm.fail()
    body = client.post(f"/api/grading/run/{kuis_campuran}").json()
    assert body["status"] != "success" or body["data"].get("failed_count")


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=(
        "BUG: skor 0 tidak bisa dinilai ulang setelah LLM pulih, karena filter "
        "hanya `score IS NULL` (grading.py:27)."
    ),
)
def test_esai_gagal_bisa_dinilai_ulang_setelah_llm_pulih(
    client, llm, kuis_campuran, kiriman
):
    llm.fail()
    client.post(f"/api/grading/run/{kuis_campuran}")
    llm.reply(json.dumps([{"id": "Q003", "score": 30}]))
    client.post(f"/api/grading/run/{kuis_campuran}")
    assert kiriman(kuis_campuran)[0]["score"] == 100.0


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=(
        "BUG: bila LLM hanya mengembalikan sebagian soal, soal yang hilang "
        "diam-diam bernilai 0 tanpa catatan apa pun (grading_agent.py:132-147)."
    ),
)
def test_jawaban_llm_parsial_tidak_diam_diam_nol(soal, llm):
    llm.reply(json.dumps([{"id": "Q003", "score": 25, "feedback": "Baik."}]))
    hasil = grade_essay_node(
        {"questions": [soal.esai1, soal.esai2], "student_answers": {}}
    )
    hilang = next(e for e in hasil["essay_scores"] if e["id"] == "Q004")
    assert hilang["feedback"], "soal yang tidak dinilai harus ditandai"


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=(
        "BUG: array kosong dari LLM lolos pemeriksaan bentuk, semua esai 0 "
        "tanpa catatan gagal (grading_agent.py:115-119)."
    ),
)
def test_array_kosong_dari_llm_dianggap_gagal(soal, llm):
    llm.reply("[]")
    hasil = grade_essay_node({"questions": [soal.esai1], "student_answers": {}})
    assert hasil["essay_scores"][0]["feedback"] == CATATAN_GAGAL
