"""Endpoint utama: dashboard, courses, students, materials, rps, quiz.

Tes `xfail` merekam bug yang terlihat saat uji jalan A3. Penandanya strict, jadi
perbaikan bug akan memaksa penanda dibuang.
"""

import io

import pytest


def _unggah_csv(client, url, teks, params=None):
    return client.post(
        url,
        params=params,
        files={"file": ("data.csv", io.BytesIO(teks.encode()), "text/csv")},
    )


# --- Awal aplikasi ----------------------------------------------------------


def test_db_baru_berisi_seed(client):
    [course] = client.get("/api/courses/").json()
    assert course["id"] == "c1"
    assert len(client.get("/api/students/", params={"course_id": "c1"}).json()) == 3


def test_setiap_tes_mulai_dari_db_bersih_a(client):
    client.post("/api/courses/", json={"name": "Sisa", "code": "SISA"})
    assert len(client.get("/api/courses/").json()) == 2


def test_setiap_tes_mulai_dari_db_bersih_b(client):
    assert len(client.get("/api/courses/").json()) == 1


# --- Dashboard --------------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    [
        "/api/dashboard/overview",
        "/api/dashboard/courses",
        "/api/dashboard/rps",
        "/api/dashboard/quizzes",
        "/api/dashboard/analytics",
        "/api/dashboard/knowledge-base",
        "/api/dashboard/settings",
        "/api/knowledge/graph",
    ],
)
def test_halaman_baca_merespons_200_pada_db_seed(client, path):
    assert client.get(path).status_code == 200


def test_overview_menghitung_dari_data(client, llm, kuis_campuran):
    def nilai(label):
        blocks = client.get("/api/dashboard/overview").json()["stats_blocks"]
        return next(b["value"] for b in blocks if b["label"] == label)

    assert nilai("Mata Kuliah Aktif") == "1"
    assert nilai("Perlu Dinilai") == "1"

    llm.reply('[{"id": "Q003", "score": 30}]')
    client.post(f"/api/grading/run/{kuis_campuran}")

    assert nilai("Perlu Dinilai") == "0"
    assert nilai("Rata-rata Nilai") == "100.0"


def test_overview_memberi_alert_kelas_di_bawah_batas(client, buat_kuis, unggah_jawaban, soal):
    quiz_id = buat_kuis([soal.mcq1])
    unggah_jawaban(quiz_id, "NIM Mahasiswa,PG-1\n00000001,A\n00000002,A\n00000003,B\n")
    client.post(f"/api/grading/run/{quiz_id}")
    alerts = client.get("/api/dashboard/overview").json()["alerts"]
    assert any("di bawah batas lulus" in a["title"] for a in alerts)


def test_analitik_dan_ekspor_pdf(client, llm, buat_kuis, unggah_jawaban, soal):
    quiz_id = buat_kuis([soal.mcq1])
    unggah_jawaban(quiz_id, "NIM Mahasiswa,PG-1\n00000001,B\n00000002,A\n")
    client.post(f"/api/grading/run/{quiz_id}")

    data = client.get("/api/dashboard/analytics", params={"course_id": "c1"}).json()
    assert data["course_overview"]["avg_score"] == 50.0
    assert data["course_overview"]["pass_rate"] == 50.0
    assert data["course_overview"]["remedial_students"] == 1
    assert [s["status"] for s in data["per_student"]] == ["pass", "fail"]

    pdf = client.get("/api/dashboard/analytics/export", params={"course_id": "c1"})
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content.startswith(b"%PDF")


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=(
        "BUG: course_id tak dikenal diam-diam memakai mata kuliah pertama, "
        "bukan 404, sehingga data kelas lain tampil (dashboard.py:369-370)."
    ),
)
def test_analitik_course_tak_dikenal_404(client):
    res = client.get("/api/dashboard/analytics", params={"course_id": "tidak-ada"})
    assert res.status_code == 404


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=(
        "BUG: /api/dashboard/quizzes hanya mengembalikan active, attention, dan "
        "draft. Kuis berstatus completed hilang dari halaman daftar kuis "
        "(dashboard.py:321-323). Di DB sumber, kuis II5005 tidak terlihat."
    ),
)
def test_kuis_selesai_tetap_terdaftar(client, buat_kuis, unggah_jawaban, soal):
    quiz_id = buat_kuis([soal.mcq1])
    unggah_jawaban(quiz_id, "NIM Mahasiswa,PG-1\n00000001,B\n")
    client.post(f"/api/grading/run/{quiz_id}")
    assert quiz_id in str(client.get("/api/dashboard/quizzes").json())


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=(
        "BUG: courses.status tidak pernah dihitung ulang, jadi kelas rata-rata "
        "0 tetap 'On Track' (stats.py:269-285)."
    ),
)
def test_status_mata_kuliah_mengikuti_nilai(client, buat_kuis, unggah_jawaban, soal):
    quiz_id = buat_kuis([soal.mcq1])
    unggah_jawaban(quiz_id, "NIM Mahasiswa,PG-1\n00000001,A\n")
    client.post(f"/api/grading/run/{quiz_id}")
    [item] = client.get("/api/dashboard/courses").json()["items"]
    assert item["status_text"] != "On Track"


# --- Pengaturan -------------------------------------------------------------


def test_profil_dan_notifikasi_tersimpan(client):
    client.put("/api/settings/profile", json={"name": "  Dosen Uji  "})
    client.put(
        "/api/settings/notifications", json={"id": "notif.rps_review", "enabled": True}
    )
    data = client.get("/api/dashboard/settings").json()
    assert data["profile"]["name"] == "Dosen Uji"
    assert next(n for n in data["notifications"] if n["id"] == "notif.rps_review")[
        "enabled"
    ]


def test_kunci_notifikasi_asing_ditolak(client):
    res = client.put(
        "/api/settings/notifications", json={"id": "profile.name", "enabled": True}
    )
    assert res.status_code == 400


# --- Courses ----------------------------------------------------------------


def test_buat_daftar_hapus_mata_kuliah(client):
    baru = client.post(
        "/api/courses/", json={"name": "Baru", "code": "BR1", "sks": 2}
    ).json()
    assert baru["sks"] == 2
    assert baru["id"] in [c["id"] for c in client.get("/api/courses/").json()]
    assert client.delete(f"/api/courses/{baru['id']}").status_code == 200
    assert baru["id"] not in [c["id"] for c in client.get("/api/courses/").json()]


def test_kode_ganda_ditolak(client):
    assert (
        client.post("/api/courses/", json={"name": "X", "code": "II5003"}).status_code
        == 400
    )


def test_hapus_course_tak_dikenal_404(client):
    assert client.delete("/api/courses/tidak-ada").status_code == 404


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=(
        "BUG: hapus mata kuliah tidak menghapus submissions. Jawaban dan nilai "
        "mahasiswa tertinggal tanpa kuis, dan tetap terhitung di 'Perlu Dinilai' "
        "(courses.py:80-86)."
    ),
)
def test_hapus_course_tidak_meninggalkan_submission(
    client, db, buat_kuis, unggah_jawaban, soal
):
    from app.models.submission import Submission

    course = client.post("/api/courses/", json={"name": "H", "code": "H1"}).json()
    quiz_id = buat_kuis([soal.mcq1], course_id=course["id"])
    unggah_jawaban(quiz_id, "NIM Mahasiswa,PG-1\n1,B\n")

    client.delete(f"/api/courses/{course['id']}")

    assert db.query(Submission).filter(Submission.quiz_id == quiz_id).count() == 0


# --- Students ---------------------------------------------------------------


def test_tambah_dan_hapus_mahasiswa(client):
    baru = client.post(
        "/api/students/",
        json={"course_id": "c1", "nim": " 123 ", "name": " Uji ", "email": " "},
    ).json()
    assert (baru["nim"], baru["name"]) == ("123", "Uji")
    daftar = client.get("/api/students/", params={"course_id": "c1"}).json()
    assert len(daftar) == 4
    assert next(s for s in daftar if s["nim"] == "123")["email"] is None
    assert client.delete(f"/api/students/{baru['id']}").status_code == 200
    assert len(client.get("/api/students/", params={"course_id": "c1"}).json()) == 3


@pytest.mark.parametrize(
    "payload, status",
    [
        ({"course_id": "c1", "nim": "00000001", "name": "Ganda"}, 400),
        ({"course_id": "c1", "nim": "  ", "name": "X"}, 400),
        ({"course_id": "c1", "nim": "9", "name": " "}, 400),
        ({"course_id": "tidak-ada", "nim": "9", "name": "X"}, 404),
    ],
)
def test_data_mahasiswa_tidak_valid_ditolak(client, payload, status):
    assert client.post("/api/students/", json=payload).status_code == status


def test_impor_csv_titik_koma_dan_baris_buruk(client):
    res = _unggah_csv(
        client,
        "/api/students/import",
        "NIM;Nama Mahasiswa;Email\n100;Satu;a@contoh.test\n100;Ganda;\n;Tanpa NIM;\n",
        params={"course_id": "c1"},
    )
    body = res.json()
    assert body["added"] == 1
    assert [s["row"] for s in body["skipped"]] == [3, 4]
    assert client.get("/api/dashboard/courses").json()["items"][0]["students"] == 4


def test_hapus_semua_mahasiswa(client):
    client.delete("/api/students/", params={"course_id": "c1"})
    assert client.get("/api/students/", params={"course_id": "c1"}).json() == []


# --- Materials --------------------------------------------------------------


def test_buat_materi_teks_terindeks(client, rag_palsu):
    res = client.post(
        "/api/materials/",
        json={"course_id": "c1", "title": "M", "content_text": "Isi", "week": 2},
    ).json()
    assert res["indexed_chunks"] == 2
    assert rag_palsu.indexed[0][1]["material_id"] == res["id"]
    [materi] = client.get("/api/materials/", params={"course_id": "c1"}).json()
    assert materi["status_text"] == "Terindeks"
    assert materi["has_content"] is True


def test_materi_url_tanpa_teks_tidak_diindeks(client, rag_palsu):
    res = client.post(
        "/api/materials/",
        json={"course_id": "c1", "title": "M", "url": "https://contoh.test"},
    ).json()
    assert res["indexed_chunks"] == 0
    assert rag_palsu.indexed == []
    [materi] = client.get("/api/materials/").json()
    assert materi["status_text"] == "Ready"


def test_unggah_txt_mengambil_isi_dan_konten_bisa_dibaca(client):
    res = client.post(
        "/api/materials/upload",
        data={"course_id": "c1", "title": "Catatan", "week": "3"},
        files={"file": ("catatan.txt", io.BytesIO("Isi materi".encode()), "text/plain")},
    ).json()
    assert res["extracted_chars"] == 10
    isi = client.get(f"/api/materials/{res['id']}/content").json()
    assert isi["content_text"] == "Isi materi"
    assert isi["type"] == "TXT"


def test_pdf_rusak_gagal_lunak(client):
    res = client.post(
        "/api/materials/upload",
        data={"course_id": "c1", "title": "Rusak"},
        files={"file": ("rusak.pdf", io.BytesIO(b"bukan pdf"), "application/pdf")},
    )
    assert res.status_code == 200
    assert res.json()["extracted_chars"] == 0
    assert client.get("/api/materials/").json()[0]["status_text"] == "Ready"


def test_ubah_dan_hapus_materi(client):
    mid = client.post("/api/materials/", json={"course_id": "c1", "title": "M"}).json()[
        "id"
    ]
    assert client.patch(f"/api/materials/{mid}", json={"week": 5}).json()["week"] == 5
    assert client.delete(f"/api/materials/{mid}").status_code == 200
    assert client.get(f"/api/materials/{mid}/content").status_code == 404


def test_rekam_indeks_gagal_tetap_tersimpan(client, rag_palsu):
    rag_palsu.error = OSError("Chroma tidak tersedia")
    res = client.post(
        "/api/materials/",
        json={"course_id": "c1", "title": "M", "content_text": "Isi"},
    )
    assert res.status_code == 200
    assert res.json()["indexed_chunks"] == 0


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=(
        "BUG: status 'Terindeks' ditulis sebelum indeks dicoba dan tidak "
        "dikoreksi saat gagal (materials.py:106, 111). Knowledge Hub menampilkan "
        "'Terindeks 4' padahal folder chroma_db tidak ada."
    ),
)
def test_status_materi_jujur_saat_indeks_gagal(client, rag_palsu):
    rag_palsu.error = OSError("Chroma tidak tersedia")
    client.post(
        "/api/materials/",
        json={"course_id": "c1", "title": "M", "content_text": "Isi"},
    )
    assert client.get("/api/materials/").json()[0]["status_text"] != "Terindeks"


def test_rekam_pencarian_rag_gagal_jadi_500(client, rag_palsu):
    rag_palsu.error = OSError("Chroma tidak tersedia")
    res = client.post("/api/knowledge/query", json={"query": "regresi"})
    assert res.status_code == 500
    assert "RAG retrieval gagal" in res.json()["detail"]


def test_query_kosong_ditolak(client):
    assert client.post("/api/knowledge/query", json={"query": " "}).status_code == 400


# --- RPS --------------------------------------------------------------------


def test_rps_manual_lengkap_mendapat_skor_100(client, llm, rps_lengkap):
    rps_id = client.post("/api/rps/", json=rps_lengkap).json()["rps_id"]

    detail = client.get(f"/api/dashboard/rps/{rps_id}").json()
    assert detail["status"] == "draft"
    assert len(detail["meetings"]) == 16
    assert detail["summary"][0]["value"] == "100%"
    assert detail["meetings"][7]["sub_topic_title"] == "Ujian Tengah Semester (UTS)"
    assert detail["meetings"][15]["sub_topic_title"] == "Ujian Akhir Semester (UAS)"

    report = client.get(f"/api/rps/{rps_id}/compliance").json()
    assert report["score"] == 100
    assert report["total_weight"] == report["earned_weight"] == 250
    assert llm.prompts == []


def test_rps_kosong_mendapat_skor_rendah_dan_daftar_isu(client):
    rps_id = client.post(
        "/api/rps/", json={"course_name": "K", "course_code": "K1"}
    ).json()["rps_id"]
    report = client.get(f"/api/rps/{rps_id}/compliance").json()
    assert report["score"] < 50
    assert any(not c["passed"] for c in report["criteria"])


def test_ubah_rps_memperbarui_skor(client, rps_lengkap):
    rps_id = client.post("/api/rps/", json=rps_lengkap).json()["rps_id"]
    rps_lengkap["learning_modality"] = ""
    assert client.put(f"/api/rps/{rps_id}", json=rps_lengkap).status_code == 200
    item = next(
        i for i in client.get("/api/dashboard/rps").json()["items"] if i["id"] == rps_id
    )
    assert item["compliance_score"] == 99


@pytest.mark.parametrize(
    "ubah, pesan",
    [
        ({"cpmk_number": 9}, "CPMK 9 di luar rentang"),
        ({"bahan_kajian_topik": "Asing"}, "tidak ada di daftar RPS"),
        ({"reference_indices": [99]}, "Referensi 99 di luar rentang"),
    ],
)
def test_pertemuan_tidak_valid_ditolak(client, rps_lengkap, ubah, pesan):
    rps_lengkap["meetings"][0].update(ubah)
    res = client.post("/api/rps/", json=rps_lengkap)
    assert res.status_code == 400
    assert pesan in res.json()["detail"]


def test_setujui_dan_hapus_rps(client, rps_lengkap):
    rps_id = client.post("/api/rps/", json=rps_lengkap).json()["rps_id"]
    assert client.post(f"/api/rps/{rps_id}/approve").status_code == 200
    assert client.get(f"/api/dashboard/rps/{rps_id}").json()["status"] == "validated"
    assert client.delete(f"/api/rps/{rps_id}").status_code == 200
    assert client.get(f"/api/dashboard/rps/{rps_id}").status_code == 404


def test_rps_disetujui_tidak_bisa_diregenerasi(client, llm, rps_lengkap):
    rps_id = client.post("/api/rps/", json=rps_lengkap).json()["rps_id"]
    client.post(f"/api/rps/{rps_id}/approve")
    assert (
        client.post(f"/api/rps/{rps_id}/regenerate", json={"feedback": "x"}).status_code
        == 400
    )
    assert llm.prompts == []


def test_regenerate_llm_gagal_mempertahankan_pertemuan(client, llm, rps_lengkap):
    rps_id = client.post("/api/rps/", json=rps_lengkap).json()["rps_id"]
    llm.fail()
    client.post(f"/api/rps/{rps_id}/regenerate", json={"feedback": "x"})
    assert len(client.get(f"/api/dashboard/rps/{rps_id}").json()["meetings"]) == 16


def test_rekam_regenerasi_minggu_llm_gagal_jadi_500_mentah(client, llm, rps_lengkap):
    rps_id = client.post("/api/rps/", json=rps_lengkap).json()["rps_id"]
    llm.fail()
    res = client.post(f"/api/rps/{rps_id}/meetings/3/regenerate", json={"feedback": "x"})
    assert res.status_code == 500
    assert "Connection refused" in res.json()["detail"]


def _generate(client, kode="UJ1001"):
    return client.post(
        "/api/rps/generate",
        data={"course_name": "Mata Kuliah Uji", "course_code": kode, "sks": "3"},
    )


def test_rekam_generate_llm_gagal_melapor_sukses_dengan_rps_kosong(client, llm):
    llm.fail()
    res = _generate(client, kode="BARU1")
    assert res.status_code == 200
    assert res.json()["status"] == "success"
    detail = client.get(f"/api/dashboard/rps/{res.json()['data']['rps_id']}").json()
    assert detail["meetings"] == []


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=(
        "BUG KRITIS: /generate saat LLM gagal mengosongkan RPS yang ada, termasuk "
        "yang sudah disetujui: pertemuan, CPL, CPMK, dan referensi hilang, status "
        "kembali draft, respons tetap sukses (rps.py:434-438, 81). Guard "
        "'sudah disetujui' hanya ada di /regenerate. G2."
    ),
)
def test_generate_llm_gagal_tidak_merusak_rps_disetujui(client, llm, rps_lengkap):
    rps_id = client.post("/api/rps/", json=rps_lengkap).json()["rps_id"]
    client.post(f"/api/rps/{rps_id}/approve")
    llm.fail()

    _generate(client)

    detail = client.get(f"/api/dashboard/rps/{rps_id}").json()
    assert detail["status"] == "validated"
    assert len(detail["meetings"]) == 16
    assert len(detail["cpmk_list"]) == 3


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=(
        "BUG: approve menulis skor 100 tanpa memeriksa katalog. Daftar RPS "
        "menampilkan 'Compliant SN-Dikti' 100 untuk RPS kosong (rps.py:623-625)."
    ),
)
def test_approve_tidak_memalsukan_skor(client):
    rps_id = client.post(
        "/api/rps/", json={"course_name": "K", "course_code": "K1"}
    ).json()["rps_id"]
    client.post(f"/api/rps/{rps_id}/approve")
    item = next(
        i for i in client.get("/api/dashboard/rps").json()["items"] if i["id"] == rps_id
    )
    assert item["compliance_score"] < 100


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=(
        "BUG: _get_or_create_course commit sebelum validasi, jadi POST RPS yang "
        "ditolak 400 tetap meninggalkan mata kuliah baru (rps.py:517-530)."
    ),
)
def test_rps_ditolak_tidak_meninggalkan_mata_kuliah(client, rps_lengkap):
    rps_lengkap["meetings"][0]["cpmk_number"] = 9
    assert client.post("/api/rps/", json=rps_lengkap).status_code == 400
    assert "UJ1001" not in [c["code"] for c in client.get("/api/courses/").json()]


# --- Quiz -------------------------------------------------------------------


def test_siklus_kuis_manual(client, buat_kuis, soal):
    quiz_id = buat_kuis([soal.mcq1, soal.esai1])

    kuis = client.get(f"/api/quiz/{quiz_id}").json()
    assert kuis["status"] == "draft"
    assert kuis["details"] == "2 soal | MCQ + Esai"
    assert kuis["answer_key"] == [
        {"id": "Q001", "answer": "B"},
        {"id": "Q003", "answer": soal.esai1["rubric"]},
    ]

    client.post(f"/api/quiz/publish/{quiz_id}")
    kuis = client.get(f"/api/quiz/{quiz_id}").json()
    assert kuis["status"] == "active"
    assert kuis["total_students"] == 3

    client.post(f"/api/quiz/close/{quiz_id}")
    assert client.get(f"/api/quiz/{quiz_id}").json()["status"] == "completed"

    assert client.delete(f"/api/quiz/{quiz_id}").status_code == 200
    assert client.get(f"/api/quiz/{quiz_id}").status_code == 404


def test_hanya_draft_yang_bisa_diedit(client, buat_kuis, soal):
    quiz_id = buat_kuis([soal.mcq1])
    payload = {"course_id": "c1", "title": "Baru", "questions": [soal.mcq2]}
    assert client.put(f"/api/quiz/{quiz_id}", json=payload).status_code == 200
    assert client.get(f"/api/quiz/{quiz_id}").json()["title"] == "Baru"
    client.post(f"/api/quiz/publish/{quiz_id}")
    assert client.put(f"/api/quiz/{quiz_id}", json=payload).status_code == 400


def test_templat_csv_mengikuti_soal_dan_roster(client, buat_kuis, soal):
    quiz_id = buat_kuis([soal.mcq1, soal.esai1, soal.mcq2])
    baris = client.get(f"/api/quiz/{quiz_id}/template.csv").text.splitlines()
    assert baris[0] == "NIM Mahasiswa,Nama Mahasiswa,PG-1,ESSAY-1,PG-2"
    assert baris[1] == "00000001,Mahasiswa 01,,,"
    assert len(baris) == 4


def test_unggah_jawaban_memilah_baris(client, buat_kuis, unggah_jawaban, soal, kiriman):
    quiz_id = buat_kuis([soal.mcq1, soal.esai1])
    body = unggah_jawaban(
        quiz_id,
        "Jawaban Mahasiswa,,\n"
        "NIM Mahasiswa,PG-1,ESSAY-1\n"
        "00000001,b,Isi esai\n"
        "99999999,A,Asing\n"
        "00000001,A,Ganda\n"
        ",A,Tanpa NIM\n",
    ).json()

    assert body["added"] == 2
    assert body["matched"] == 1
    assert [u["nim"] for u in body["unmatched"]] == ["99999999"]
    assert len(body["skipped"]) == 2

    subs = {s["nim"]: s for s in kiriman(quiz_id)}
    assert subs["00000001"]["name"] == "Mahasiswa 01"
    assert subs["00000001"]["answers"] == {"Q001": "B", "Q003": "Isi esai"}
    assert subs["99999999"]["status"] == "unmatched"


@pytest.mark.parametrize(
    "csv_teks, pesan",
    [
        ("", "CSV kosong"),
        ("Nama,PG-1\nA,B\n", "Kolom NIM"),
        ("NIM,Catatan\n1,x\n", "kolom jawaban"),
    ],
)
def test_csv_jawaban_rusak_ditolak(buat_kuis, unggah_jawaban, soal, csv_teks, pesan):
    res = unggah_jawaban(buat_kuis([soal.mcq1]), csv_teks)
    assert res.status_code == 400
    assert pesan in res.json()["detail"]


def test_unggah_ke_kuis_tanpa_soal_ditolak(buat_kuis, unggah_jawaban):
    assert unggah_jawaban(buat_kuis([]), "NIM,PG-1\n1,A\n").status_code == 400


def test_hapus_submission_tunggal_dan_semua(
    client, buat_kuis, unggah_jawaban, soal, kiriman
):
    quiz_id = buat_kuis([soal.mcq1])
    unggah_jawaban(quiz_id, "NIM,PG-1\n1,A\n2,B\n")
    pertama = kiriman(quiz_id)[0]["id"]
    client.delete(f"/api/quiz/{quiz_id}/submissions/{pertama}")
    assert len(kiriman(quiz_id)) == 1
    client.delete(f"/api/quiz/{quiz_id}/submissions")
    assert kiriman(quiz_id) == []


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=(
        "BUG: jumlah submission dihitung sebelum flush dan SessionLocal memakai "
        "autoflush=False, jadi unggahan pertama selalu mencatat 0 (quiz.py:518-520). "
        "Halaman kuis menampilkan 'Submission 0/3'."
    ),
)
def test_jumlah_submission_tercatat_setelah_unggah(client, buat_kuis, unggah_jawaban, soal):
    quiz_id = buat_kuis([soal.mcq1])
    body = unggah_jawaban(quiz_id, "NIM,PG-1\n00000001,A\n00000002,B\n").json()
    assert body["total_submissions"] == 2
    assert client.get(f"/api/quiz/{quiz_id}").json()["submissions"] == 2


def test_generate_kuis_dengan_llm_tiruan(client, llm):
    mcq = (
        '[{"id": "Q001", "question": "Apa itu A?\\nA. satu\\nB. dua", '
        '"options": {"A": "1", "B": "2", "C": "3", "D": "4"}, "correct_answer": "B"}]'
    )
    esai = '[{"id": "Q002", "question": "Jelaskan.", "rubric": {"excellent": "x"}}]'
    llm.reply(lambda prompt: esai if "soal esai" in prompt else mcq)

    res = client.post(
        "/api/quiz/generate",
        json={"course_id": "c1", "num_questions": 2, "material_content": "Materi"},
    )

    assert res.status_code == 200
    data = res.json()["data"]
    assert [q["type"] for q in data["questions"]] == ["multiple_choice", "essay"]
    assert data["questions"][1]["max_score"] == 30
    assert data["answer_key"][0] == {"id": "Q001", "answer": "B"}
    assert client.get(f"/api/quiz/{data['quiz_id']}").json()["status"] == "draft"
    assert set(llm.tasks) == {"simple", "complex"}


def test_rekam_generate_kuis_llm_gagal_menyimpan_draft_kosong(client, llm):
    llm.fail()
    res = client.post(
        "/api/quiz/generate",
        json={"course_id": "c1", "num_questions": 2, "material_content": "Materi"},
    )
    assert res.status_code == 200
    assert res.json()["data"]["questions"] == []
    kuis = client.get(f"/api/quiz/{res.json()['data']['quiz_id']}").json()
    assert kuis["details"] == "0 soal | MCQ + Esai"


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=(
        "BUG: LLM gagal tetap menghasilkan 200 'success' dan draft 0 soal "
        "(quiz.py:71-100). UI menampilkan 'Kuis Berhasil Dibuat'."
    ),
)
def test_generate_kuis_llm_gagal_melapor_gagal(client, llm):
    llm.fail()
    res = client.post(
        "/api/quiz/generate",
        json={"course_id": "c1", "num_questions": 2, "material_content": "Materi"},
    )
    assert res.status_code >= 400
