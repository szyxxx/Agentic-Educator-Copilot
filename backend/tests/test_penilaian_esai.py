"""Penilaian esai dengan LLM tiruan yang berhasil menjawab."""

import json

import pytest

from app.agents.grading_agent import feedback_node, grade_essay_node


def _jawaban(*items) -> str:
    return json.dumps(list(items))


def _nilai(questions, answers):
    return grade_essay_node({"questions": questions, "student_answers": answers})[
        "essay_scores"
    ]


def test_skor_llm_dipakai(soal, llm):
    llm.reply(_jawaban({"id": "Q003", "score": 24, "feedback": "Baik."}))
    assert _nilai([soal.esai1], {"Q003": "isi"}) == [
        {"id": "Q003", "score": 24.0, "feedback": "Baik.", "max_score": 30.0}
    ]


def test_memakai_model_kelas_complex_sekali_untuk_semua_esai(soal, llm):
    llm.reply(
        _jawaban({"id": "Q003", "score": 1}, {"id": "Q004", "score": 2})
    )
    _nilai([soal.esai1, soal.esai2], {"Q003": "a", "Q004": "b"})
    assert llm.tasks == ["complex"]
    assert len(llm.prompts) == 1


def test_prompt_memuat_rubrik_dan_jawaban(soal, llm):
    llm.reply(_jawaban({"id": "Q003", "score": 1}))
    _nilai([soal.esai1], {"Q003": "Jawaban khas mahasiswa"})
    assert "lengkap dan tepat" in llm.prompts[0]
    assert "Jawaban khas mahasiswa" in llm.prompts[0]


def test_prompt_tidak_memuat_identitas_mahasiswa(client, llm, kuis_campuran):
    llm.reply(_jawaban({"id": "Q003", "score": 15}))
    client.post(f"/api/grading/run/{kuis_campuran}")
    assert llm.prompts
    assert "00000001" not in llm.prompts[0]
    assert "Mahasiswa 01" not in llm.prompts[0]


def test_jawaban_dipotong_1500_karakter(soal, llm):
    llm.reply(_jawaban({"id": "Q003", "score": 1}))
    _nilai([soal.esai1], {"Q003": "x" * 2000})
    assert "x" * 1500 in llm.prompts[0]
    assert "x" * 1501 not in llm.prompts[0]


def test_esai_kosong_tetap_dikirim_sebagai_tidak_dijawab(soal, llm):
    llm.reply(_jawaban({"id": "Q003", "score": 0}))
    _nilai([soal.esai1], {})
    assert "(tidak dijawab)" in llm.prompts[0]


@pytest.mark.parametrize("mentah, harapan", [(99, 30.0), (-5, 0.0)])
def test_skor_dibatasi_ke_rentang_soal(soal, llm, mentah, harapan):
    llm.reply(_jawaban({"id": "Q003", "score": mentah}))
    assert _nilai([soal.esai1], {"Q003": "isi"})[0]["score"] == harapan


def test_pagar_markdown_dan_teks_pengantar_ditoleransi(soal, llm):
    llm.reply('Berikut hasilnya:\n```json\n[{"id": "Q003", "score": 12}]\n```')
    assert _nilai([soal.esai1], {"Q003": "isi"})[0]["score"] == 12.0


def test_kuis_tanpa_esai_tidak_memanggil_llm(soal, llm):
    assert _nilai([soal.mcq1], {}) == []
    assert llm.prompts == []


@pytest.mark.parametrize(
    "skor, kata_kunci",
    [(18, "Jawaban esai sudah memadai."), (17.9, "perlu diperdalam: Q003")],
)
def test_batas_lemah_enam_puluh_persen(skor, kata_kunci):
    hasil = feedback_node(
        {
            "total_score": 50,
            "mcq_scores": [],
            "essay_scores": [{"id": "Q003", "score": skor, "max_score": 30}],
        }
    )
    assert kata_kunci in hasil["overall_feedback"]


def test_endpoint_menggabungkan_mcq_dan_esai(client, llm, kuis_campuran, kiriman):
    llm.reply(_jawaban({"id": "Q003", "score": 24, "feedback": "Baik."}))

    res = client.post(f"/api/grading/run/{kuis_campuran}")

    assert res.json()["data"]["average_score"] == 88.0  # (10 + 10 + 24) / 50
    [sub] = kiriman(kuis_campuran)
    assert sub["score"] == 88.0
    assert sub["status"] == "graded"
    assert sub["feedback"].startswith(
        "Skor total 88.0 dari 100. MCQ benar 2/2. Jawaban esai sudah memadai."
    )


def test_feedback_esai_dari_llm_tersimpan(client, llm, kuis_campuran, kiriman):
    llm.reply(
        _jawaban({"id": "Q003", "score": 24, "feedback": "Contoh kasusnya kurang."})
    )
    client.post(f"/api/grading/run/{kuis_campuran}")
    assert "Contoh kasusnya kurang." in kiriman(kuis_campuran)[0]["feedback"]


def test_materi_otomatis_dibuat_setelah_penilaian_jika_ada_rps(
    client, llm, rag_palsu, rps_lengkap, buat_kuis, unggah_jawaban, soal
):
    rps = client.post("/api/rps/", json=rps_lengkap).json()["rps_id"]
    course_id = client.get(f"/api/dashboard/rps/{rps}").json()["course_id"]
    quiz_id = buat_kuis([soal.mcq1], course_id=course_id, week_number=3)
    unggah_jawaban(quiz_id, "NIM Mahasiswa,PG-1\n123,A\n")
    llm.reply("# Penguatan Minggu 4\nIsi materi.")

    data = client.post(f"/api/grading/run/{quiz_id}").json()["data"]

    assert data["auto_material_week"] == 4
    [materi] = client.get("/api/materials/", params={"rps_id": rps}).json()
    assert materi["id"] == data["auto_material_id"]
    assert materi["type"] == "AUTO"
    assert materi["status_text"] == "Auto-Generated"
    assert len(rag_palsu.indexed) == 1
