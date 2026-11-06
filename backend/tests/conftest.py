"""Fixture bersama untuk seluruh tes backend.

Tiga jaminan yang dijaga file ini:

1. Tes tidak menyentuh `backend/educopilot.db`. `DATABASE_URL` diarahkan ke
   file di folder sementara sebelum modul `app` diimpor, dan setiap tes mulai
   dari DB baru di alamat itu. Hash file asli dicek di akhir sesi.
2. Tes tidak memakai jaringan. Upaya koneksi TCP/UDP gagal, dicatat, dan
   membuat tes yang bersangkutan gagal saat teardown.
3. Tes tidak memanggil LLM sungguhan. `get_llm` diganti `FakeLLM` di semua
   tempat pemakaiannya, dan kunci API dikosongkan.
"""

from __future__ import annotations

import hashlib
import io
import os
import shutil
import socket
import tempfile
from pathlib import Path
from types import SimpleNamespace
from typing import Callable

# --- Lingkungan harus siap SEBELUM `app` diimpor ----------------------------
# `app.core.config` membaca env saat impor, dan `load_dotenv` tidak menimpa
# nilai yang sudah ada, jadi `.env` lokal tidak bisa membocorkan kunci ke tes.

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_DB = BACKEND_DIR / "educopilot.db"

_TMP_DIR = Path(tempfile.mkdtemp(prefix="educopilot-tes-"))
_TEST_DB = _TMP_DIR / "tes.db"

os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB}"
os.environ["ENVIRONMENT"] = "test"
os.environ["CHROMA_PERSIST_DIR"] = str(_TMP_DIR / "chroma")
os.environ["OPENROUTER_API_KEY"] = ""
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["LLM_PROVIDER_ORDER"] = "ollama"
os.environ["OLLAMA_BASE_URL"] = "http://127.0.0.1:9"
os.environ["OLLAMA_NUM_CTX"] = "8192"
os.environ["OLLAMA_GRADING_SEED"] = "42"
os.environ["EMBEDDING_PROVIDER"] = "huggingface"
os.environ["OLLAMA_EMBEDDING_NUM_GPU"] = "0"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["ANONYMIZED_TELEMETRY"] = "False"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.agents import (  # noqa: E402
    auto_material_agent,
    grading_agent,
    quiz_agent,
    rps_agent,
    rps_review_agent,
)
from app.core import database  # noqa: E402
from app.core import llm as llm_module  # noqa: E402
from app.main import app  # noqa: E402


def _sha256(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


@pytest.fixture(scope="session", autouse=True)
def lindungi_db_repo():
    """Pastikan engine menunjuk DB sementara, dan DB repo tidak berubah."""
    assert str(database.engine.url) == f"sqlite:///{_TEST_DB}"
    assert Path(database.engine.url.database).resolve() != REPO_DB.resolve()
    sebelum = _sha256(REPO_DB)
    yield
    database.engine.dispose()
    shutil.rmtree(_TMP_DIR, ignore_errors=True)
    assert _sha256(REPO_DB) == sebelum, "backend/educopilot.db berubah saat tes!"


@pytest.fixture(autouse=True)
def tanpa_jaringan(monkeypatch):
    """Tolak koneksi IP. `AF_UNIX` dibiarkan karena dipakai event loop lokal."""
    upaya: list = []
    connect_asli = socket.socket.connect

    def connect_diblok(self, address):
        if self.family in (socket.AF_INET, socket.AF_INET6):
            upaya.append(address)
            raise OSError(f"Jaringan diblok saat tes: {address!r}")
        return connect_asli(self, address)

    monkeypatch.setattr(socket.socket, "connect", connect_diblok)
    yield
    assert not upaya, f"Tes mencoba koneksi jaringan: {upaya}"


@pytest.fixture(autouse=True)
def db_baru():
    """Mulai dari file DB kosong di alamat `DATABASE_URL`, lalu buat skema + seed."""
    database.engine.dispose()
    _TEST_DB.unlink(missing_ok=True)
    database.init_db()
    yield
    database.engine.dispose()


class FakeResponse:
    def __init__(self, content):
        self.content = content


class FakeLLM:
    """Pengganti model chat. Merekam prompt, tanpa jaringan.

    Tanpa konfigurasi, setiap panggilan gagal, sehingga pemanggilan LLM yang
    tidak diharapkan terlihat sebagai kegagalan, bukan keberhasilan semu.
    """

    def __init__(self) -> None:
        self.prompts: list[str] = []
        self.tasks: list[str] = []
        self._handler: Callable[[str], object] = self._belum_diatur

    @staticmethod
    def _belum_diatur(prompt: str):
        raise RuntimeError("FakeLLM: tes tidak mengharapkan panggilan LLM")

    def reply(self, content) -> "FakeLLM":
        """Balas dengan teks tetap, atau fungsi `prompt -> teks`."""
        self._handler = content if callable(content) else (lambda _prompt: content)
        return self

    def fail(self, error: Exception | None = None) -> "FakeLLM":
        """Setiap panggilan melempar galat, seperti penyedia yang mati."""
        err = error or ConnectionError("[Errno 111] Connection refused")

        def _raise(_prompt: str):
            raise err

        self._handler = _raise
        return self

    def get(self, task: str = "complex") -> "FakeLLM":
        self.tasks.append(task)
        return self

    def invoke(self, prompt, *_args, **_kwargs) -> FakeResponse:
        self.prompts.append(prompt)
        return FakeResponse(self._handler(prompt))


@pytest.fixture(autouse=True)
def llm(monkeypatch) -> FakeLLM:
    fake = FakeLLM()
    # Agen mengimpor `get_llm` dengan namanya, `api/v1/rps.py` mengimpornya di
    # dalam fungsi dari `app.core.llm`. Keduanya harus diganti.
    for module in (
        llm_module,
        grading_agent,
        quiz_agent,
        rps_agent,
        rps_review_agent,
        auto_material_agent,
    ):
        monkeypatch.setattr(module, "get_llm", fake.get)
    return fake


@pytest.fixture(autouse=True)
def rag_palsu(monkeypatch) -> SimpleNamespace:
    """Cegah pemanggilan Chroma/model embedding selama pengujian unit."""
    from app.core import rag

    state = SimpleNamespace(indexed=[], chunks=2, error=None)

    def index_material(content, metadata):
        if state.error:
            raise state.error
        state.indexed.append((content, metadata))
        return state.chunks

    def retrieve_materials(query, course_id=None, k=3):
        if state.error:
            raise state.error
        return []

    monkeypatch.setattr(rag, "index_material", index_material)
    monkeypatch.setattr(rag, "retrieve_materials", retrieve_materials)
    return state


@pytest.fixture
def client(db_baru):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db(db_baru):
    session = database.SessionLocal()
    yield session
    session.close()


# --- Pembuat data uji -------------------------------------------------------

MCQ_1 = {
    "id": "Q001",
    "type": "multiple_choice",
    "question": "Soal pilihan ganda satu?",
    "options": {"A": "a", "B": "b", "C": "c", "D": "d"},
    "correct_answer": "B",
    "weight": 10,
}
MCQ_2 = {
    "id": "Q002",
    "type": "multiple_choice",
    "question": "Soal pilihan ganda dua?",
    "options": {"A": "a", "B": "b", "C": "c", "D": "d"},
    "correct_answer": "C",
    "weight": 10,
}
ESAI_1 = {
    "id": "Q003",
    "type": "essay",
    "question": "Jelaskan konsep regresi.",
    "rubric": {"excellent": "lengkap dan tepat", "good": "cukup"},
    "max_score": 30,
}
ESAI_2 = {
    "id": "Q004",
    "type": "essay",
    "question": "Bandingkan dua metode klasifikasi.",
    "rubric": {"excellent": "lengkap"},
    "max_score": 20,
}


@pytest.fixture
def soal() -> SimpleNamespace:
    """Salinan soal baku. Kuis campuran: nilai maksimum 10 + 10 + 30 = 50."""
    return SimpleNamespace(
        mcq1=dict(MCQ_1), mcq2=dict(MCQ_2), esai1=dict(ESAI_1), esai2=dict(ESAI_2)
    )


@pytest.fixture
def buat_kuis(client):
    def _buat(questions, course_id="c1", week_number=1, title="Kuis Uji") -> str:
        res = client.post(
            "/api/quiz/",
            json={
                "course_id": course_id,
                "week_number": week_number,
                "quiz_type": "mixed",
                "num_questions": len(questions),
                "title": title,
                "questions": questions,
            },
        )
        assert res.status_code == 200, res.text
        return res.json()["data"]["quiz_id"]

    return _buat


@pytest.fixture
def unggah_jawaban(client):
    def _unggah(quiz_id: str, csv_text: str):
        return client.post(
            f"/api/quiz/{quiz_id}/submissions/upload-csv",
            files={"file": ("jawaban.csv", io.BytesIO(csv_text.encode()), "text/csv")},
        )

    return _unggah


@pytest.fixture
def kuis_campuran(buat_kuis, unggah_jawaban, soal) -> str:
    """Kuis 2 MCQ + 1 esai, satu mahasiswa roster menjawab MCQ benar semua."""
    quiz_id = buat_kuis([soal.mcq1, soal.mcq2, soal.esai1])
    res = unggah_jawaban(
        quiz_id,
        "NIM Mahasiswa,PG-1,PG-2,ESSAY-1\n00000001,B,C,Regresi memodelkan hubungan.\n",
    )
    assert res.status_code == 200, res.text
    assert res.json()["added"] == 1
    return quiz_id


@pytest.fixture
def kiriman(client):
    """Ambil daftar submission sebuah kuis lewat API."""

    def _kiriman(quiz_id: str) -> list[dict]:
        res = client.get(f"/api/quiz/{quiz_id}/submissions")
        assert res.status_code == 200, res.text
        return res.json()

    return _kiriman


def _pertemuan_lengkap(bahan_kajian: list[str]) -> list[dict]:
    meetings: list[dict] = []
    methods = ["Ceramah", "Diskusi", "Studi Kasus"]
    evaluations = ["Kuis", "Tugas"]
    for week in range(1, 17):
        if week in (8, 16):
            meetings.append({"week": week})
            continue
        meetings.append(
            {
                "week": week,
                "bahan_kajian_topik": bahan_kajian[week % 3],
                "sub_topic_title": f"Sub-topik minggu {week}",
                "sub_topic_description": "Deskripsi pertemuan yang cukup jelas.",
                "cpmk_number": week % 3 + 1,
                "reference_indices": [1, 2],
                "method": methods[week % 3],
                "evaluation": evaluations[week % 2],
            }
        )
    return meetings


@pytest.fixture
def rps_lengkap() -> dict:
    """Payload RPS manual yang memenuhi semua kriteria katalog."""
    bahan_kajian = ["Dasar", "Lanjutan", "Terapan"]
    return {
        "course_name": "Mata Kuliah Uji",
        "course_code": "UJ1001",
        "sks": 3,
        "semester": 2,
        "program_study": "S2 Uji",
        "cpl_list": ["CPL satu", "CPL dua"],
        "cpmk_list": ["CPMK satu", "CPMK dua", "CPMK tiga"],
        "references_list": ["Ref 1", "Ref 2", "Ref 3", "Ref 4", "Ref 5"],
        "bahan_kajian": bahan_kajian,
        "learning_methods": ["Ceramah", "Diskusi", "Studi Kasus"],
        "learning_modality": "Luring",
        "meetings": _pertemuan_lengkap(bahan_kajian),
    }
