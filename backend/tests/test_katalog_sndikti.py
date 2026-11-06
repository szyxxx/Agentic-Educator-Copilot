"""Katalog SN-Dikti: deterministik, tanpa LLM dan tanpa DB."""

from dataclasses import replace
from types import SimpleNamespace

import pytest

from app.core.sndikti_catalog import REGULATION_SUMMARY, SNDIKTI_CATALOG, run_catalog


def _course(**over):
    base = dict(name="MK", code="UJ1", sks=3, semester=2, program_study="S2")
    return SimpleNamespace(**{**base, **over})


def _rps(**over):
    base = dict(
        cpl_list=["CPL 1"],
        cpmk_list=["a", "b", "c"],
        references_list=["r1", "r2", "r3", "r4", "r5"],
        bahan_kajian=["Dasar", "Lanjutan", "Terapan"],
        learning_modality="Luring",
    )
    return SimpleNamespace(**{**base, **over})


def _meeting(week, **over):
    if week == 8:
        base = dict(sub_topic_title="Ujian Tengah Semester (UTS)")
    elif week == 16:
        base = dict(sub_topic_title="Ujian Akhir Semester (UAS)")
    else:
        base = dict(
            sub_topic_title=f"Topik {week}",
            sub_topic_description="Deskripsi",
            bahan_kajian_topik=["Dasar", "Lanjutan", "Terapan"][week % 3],
            cpmk_number=week % 3 + 1,
            reference_indices=[1],
            references="Ref",
            learning_method=["Ceramah", "Diskusi", "Studi Kasus"][week % 3],
            evaluation_method=["Kuis", "Tugas"][week % 2],
        )
    empty = dict(
        week_number=week,
        topic="",
        cpmk="",
        references="",
        sub_topic_title="",
        sub_topic_description="",
        bahan_kajian_topik="",
        cpmk_number=None,
        reference_indices=[],
        learning_method="",
        evaluation_method="",
    )
    return SimpleNamespace(**{**empty, **base, **over})


def _meetings():
    return [_meeting(w) for w in range(1, 17)]


def _gagal(report):
    return {row.id for row in report.criteria if not row.passed}


def test_ada_24_kriteria_dengan_id_unik():
    ids = [c.id for c in SNDIKTI_CATALOG]
    assert len(ids) == 24
    assert len(set(ids)) == 24


def test_setiap_kriteria_terdefinisi_lengkap():
    for crit in SNDIKTI_CATALOG:
        assert crit.weight > 0, crit.id
        assert crit.severity in ("critical", "warning", "info"), crit.id
        assert crit.scope in ("rps_level", "per_week"), crit.id
        assert crit.regulation_ref.strip(), crit.id
        assert crit.group.strip(), crit.id


def test_rps_lengkap_bernilai_100():
    report = run_catalog(_rps(), _meetings(), course=_course())
    assert _gagal(report) == set()
    assert report.score == 100
    assert report.earned_weight == report.total_weight
    assert report.regulation_summary == REGULATION_SUMMARY


def test_rps_lengkap_menghasilkan_bobot_dan_baris_tetap():
    # 16 kriteria RPS, 2 kriteria ujian, 6 kriteria x 14 minggu non-ujian.
    # Angka 102 dan 250 sama dengan hasil pada RPS di DB (bagian 3.2).
    report = run_catalog(_rps(), _meetings(), course=_course())
    assert len(report.criteria) == 102
    assert report.total_weight == 250


def test_tanpa_data_skor_rendah_dan_tanpa_exception():
    kosong = _rps(
        cpl_list=None,
        cpmk_list=None,
        references_list=None,
        bahan_kajian=None,
        learning_modality=None,
    )
    report = run_catalog(kosong, [])
    assert report.score == 0
    assert "SND-001" in _gagal(report)
    assert "SND-030" in _gagal(report)


def test_skor_mengikuti_rumus_bobot():
    report = run_catalog(_rps(learning_modality=""), _meetings(), course=_course())
    assert report.earned_weight == report.total_weight - 3
    assert report.score == round(report.earned_weight / report.total_weight * 100)


def test_ringkasan_kelompok_sama_dengan_baris():
    report = run_catalog(_rps(learning_modality=""), _meetings(), course=_course())
    assert sum(g.total for g in report.groups) == len(report.criteria)
    assert sum(g.total_weight for g in report.groups) == report.total_weight
    assert sum(g.earned_weight for g in report.groups) == report.earned_weight


@pytest.mark.parametrize(
    "course_over, rps_over",
    [
        ({"name": "  "}, {}),
        ({"code": ""}, {}),
        ({"sks": 7}, {}),
        ({"sks": 0}, {}),
        ({"semester": 15}, {}),
        ({"program_study": ""}, {}),
        ({}, {"cpl_list": []}),
        ({}, {"cpmk_list": ["a", "b"]}),
        ({}, {"bahan_kajian": ["Dasar", "Lanjutan"]}),
        ({}, {"references_list": ["r1", "r2", "r3", "r4"]}),
        ({}, {"learning_modality": " "}),
    ],
)
def test_pelanggaran_tingkat_rps_menurunkan_skor(course_over, rps_over):
    report = run_catalog(_rps(**rps_over), _meetings(), course=_course(**course_over))
    assert _gagal(report)
    assert report.score < 100


def test_jumlah_pertemuan_wajib_16():
    meetings = _meetings()[:-1]
    report = run_catalog(_rps(), meetings, course=_course())
    assert "SND-030" in _gagal(report)


def test_minggu_8_dan_16_harus_berlabel_ujian():
    meetings = _meetings()
    meetings[7].sub_topic_title = "Pertemuan biasa"
    meetings[15].sub_topic_title = "Pertemuan biasa"
    report = run_catalog(_rps(), meetings, course=_course())
    weeks = {r.target_week for r in report.criteria if not r.passed}
    assert weeks == {8, 16}
    assert {r.suggested_value for r in report.criteria if not r.passed} == {
        "Ujian Tengah Semester (UTS)",
        "Ujian Akhir Semester (UAS)",
    }


def test_kriteria_mingguan_mengabaikan_minggu_ujian():
    report = run_catalog(_rps(), _meetings(), course=_course())
    mingguan = [r for r in report.criteria if r.id == "SND-033"]
    assert len(mingguan) == 14
    assert {r.target_week for r in mingguan}.isdisjoint({8, 16})


def test_kesalahan_satu_minggu_hanya_menggagalkan_minggu_itu():
    meetings = _meetings()
    meetings[2].cpmk_number = 9
    report = run_catalog(_rps(), meetings, course=_course())
    baris = [r for r in report.criteria if not r.passed and r.target_week == 3]
    assert baris
    assert all("CPMK" in r.detail for r in baris)


def test_bahan_kajian_di_luar_daftar_ditolak():
    meetings = _meetings()
    meetings[0].bahan_kajian_topik = "Topik Asing"
    report = run_catalog(_rps(), meetings, course=_course())
    assert any(
        "tidak ada di daftar" in r.detail for r in report.criteria if not r.passed
    )


def test_cpmk_yang_tidak_dipakai_terdeteksi():
    meetings = [replace_cpmk(m) for m in _meetings()]
    report = run_catalog(_rps(), meetings, course=_course())
    assert any("belum dipakai" in r.detail for r in report.criteria if not r.passed)


def replace_cpmk(meeting):
    if meeting.cpmk_number is not None:
        meeting.cpmk_number = 1
    return meeting


def test_keluaran_stabil_antar_pemanggilan():
    pertama = run_catalog(_rps(), _meetings(), course=_course())
    kedua = run_catalog(_rps(), _meetings(), course=_course())
    assert pertama == kedua
    assert replace(pertama) == kedua


def test_katalog_tidak_memanggil_llm(llm):
    run_catalog(_rps(), _meetings(), course=_course())
    assert llm.prompts == []
