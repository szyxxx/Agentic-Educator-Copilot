"""Penilaian pilihan ganda: deterministik, tidak memanggil LLM."""

import pytest

from app.agents.grading_agent import (
    aggregate_node,
    build_grading_graph,
    grade_mcq_node,
)
from app.api.v1.quiz import _clean_mcq_answer


def _nilai(questions, answers):
    return grade_mcq_node({"questions": questions, "student_answers": answers})[
        "mcq_scores"
    ]


def test_jawaban_benar_mendapat_bobot_penuh(soal):
    [hasil] = _nilai([soal.mcq1], {"Q001": "B"})
    assert hasil == {"id": "Q001", "score": 10.0, "correct": True, "picked": "B"}


def test_jawaban_salah_mendapat_nol(soal):
    [hasil] = _nilai([soal.mcq1], {"Q001": "A"})
    assert hasil["score"] == 0.0
    assert hasil["correct"] is False
    assert hasil["picked"] == "A"


@pytest.mark.parametrize("jawaban", ["b", " B ", "b\n"])
def test_huruf_kecil_dan_spasi_tetap_cocok(soal, jawaban):
    [hasil] = _nilai([soal.mcq1], {"Q001": jawaban})
    assert hasil["correct"] is True


def test_jawaban_kosong_ditandai_dan_bernilai_nol(soal):
    [hasil] = _nilai([soal.mcq1], {})
    assert hasil["score"] == 0.0
    assert hasil["picked"] == "(kosong)"


def test_soal_tanpa_kunci_tidak_pernah_benar(soal):
    soal.mcq1["correct_answer"] = ""
    [hasil] = _nilai([soal.mcq1], {"Q001": ""})
    assert hasil["correct"] is False


def test_bobot_bawaan_sepuluh(soal):
    del soal.mcq1["weight"]
    [hasil] = _nilai([soal.mcq1], {"Q001": "B"})
    assert hasil["score"] == 10.0


def test_soal_esai_dilewati(soal):
    assert _nilai([soal.esai1], {"Q003": "teks"}) == []


def test_total_memakai_persentase_berbobot(soal):
    soal.mcq1["weight"] = 30
    questions = [soal.mcq1, soal.mcq2]
    scores = _nilai(questions, {"Q001": "B", "Q002": "A"})
    hasil = aggregate_node({"questions": questions, "mcq_scores": scores})
    assert hasil["total_score"] == 75.0


def test_kuis_tanpa_soal_bernilai_nol():
    assert aggregate_node({"questions": []})["total_score"] == 0.0


def test_graf_penuh_tidak_memanggil_llm(soal, llm):
    questions = [soal.mcq1, soal.mcq2]
    hasil = build_grading_graph().invoke(
        {
            "quiz_id": "q",
            "student_id": "s",
            "nim": "1",
            "questions": questions,
            "answer_key": [],
            "student_answers": {"Q001": "B", "Q002": "A"},
            "mcq_scores": [],
            "essay_scores": [],
            "total_score": 0.0,
            "feedback_per_question": [],
            "overall_feedback": "",
            "weak_topics": [],
            "messages": [],
        }
    )
    assert hasil["total_score"] == 50.0
    assert hasil["overall_feedback"] == "Skor total 50.0 dari 100. MCQ benar 1/2."
    assert hasil["weak_topics"] == [soal.mcq2["question"]]
    assert llm.prompts == []


def test_endpoint_menilai_kuis_pilihan_ganda(
    client, llm, buat_kuis, unggah_jawaban, kiriman, soal
):
    quiz_id = buat_kuis([soal.mcq1, soal.mcq2])
    unggah_jawaban(
        quiz_id,
        "NIM Mahasiswa,PG-1,PG-2\n00000001,B,C\n00000002,b,A\n00000003,A,A\n",
    )

    res = client.post(f"/api/grading/run/{quiz_id}")

    assert res.status_code == 200
    data = res.json()["data"]
    assert data["graded_count"] == 3
    assert data["average_score"] == 50.0
    skor = {s["nim"]: s["score"] for s in kiriman(quiz_id)}
    assert skor == {"00000001": 100.0, "00000002": 50.0, "00000003": 0.0}
    assert {s["status"] for s in kiriman(quiz_id)} == {"graded"}
    assert client.get(f"/api/quiz/{quiz_id}").json()["status"] == "attention"
    assert llm.prompts == []


def test_kuis_rata_rata_lulus_berstatus_completed(
    client, buat_kuis, unggah_jawaban, soal
):
    quiz_id = buat_kuis([soal.mcq1])
    unggah_jawaban(quiz_id, "NIM Mahasiswa,PG-1\n00000001,B\n")
    client.post(f"/api/grading/run/{quiz_id}")
    assert client.get(f"/api/quiz/{quiz_id}").json()["status"] == "completed"


def test_penilaian_ulang_hanya_menyentuh_yang_belum_dinilai(
    client, buat_kuis, unggah_jawaban, soal
):
    quiz_id = buat_kuis([soal.mcq1])
    unggah_jawaban(quiz_id, "NIM Mahasiswa,PG-1\n00000001,B\n")
    assert client.post(f"/api/grading/run/{quiz_id}").json()["data"]["graded_count"] == 1
    assert client.post(f"/api/grading/run/{quiz_id}").json()["data"]["graded_count"] == 0


def test_kuis_tak_dikenal_404(client):
    assert client.post("/api/grading/run/tidak-ada").status_code == 404


@pytest.mark.parametrize(
    "mentah, harapan",
    [("B", "B"), ("b", "B"), (" c ", "C"), ("", None), ("-", None), (None, None)],
)
def test_pembersih_jawaban_csv(mentah, harapan):
    assert _clean_mcq_answer(mentah) == harapan


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=(
        "BUG: _clean_mcq_answer mengambil huruf A-D pertama di mana pun, jadi "
        "'Tidak tahu' menjadi D dan 'Jawaban: D' menjadi A (quiz.py:366-374)."
    ),
)
@pytest.mark.parametrize(
    "mentah, harapan",
    [("Tidak tahu", None), ("Belum", None), ("Jawaban: D", "D")],
)
def test_teks_bebas_tidak_salah_dibaca_sebagai_pilihan(mentah, harapan):
    assert _clean_mcq_answer(mentah) == harapan
