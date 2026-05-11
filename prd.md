# PRODUCT REQUIREMENTS DOCUMENT (PRD) - v6.0

**Project Name:** Educator Copilot
**Status:** Final MVP Specification
**Last Updated:** Mei 2026
**Changelog v6.1:** Integrasi OpenRouter untuk model LLM (via ChatOpenAI `base_url`). Penambahan variabel lingkungan dinamis (`LLM_HEAVY_MODEL`, `LLM_LIGHT_MODEL`). Penambahan fitur AI Quiz Generator (pilihan ganda dan esai) berdasarkan teks materi.
**Changelog v6.0:** Riset perbandingan template RPS dari 10 PT (ITB, UI, UGM, ITS, UB, Unhas, UNDIP, UNAIR, UPI, UNPAD). Model input superset multi-universitas. Arsitektur I-P-O diperinci. Daftar fungsi & workflow diperjelas. Preset template per institusi.
**Changelog v5.0:** Stack diubah ke Python + LangGraph + Streamlit. Pemenuhan 5 kriteria wajib sistem agentic. Arsitektur LangGraph didefinisikan secara eksplisit.

---

## 1. Ringkasan Eksekutif

Educator Copilot adalah sistem **Agentic AI berbasis LangGraph** yang membantu dosen mengelola siklus pembelajaran semester penuh—mulai dari perancangan RPS berbasis CPL/CPMK institusi, pengelolaan materi per-minggu, hingga analisis pemahaman mahasiswa melalui kuis dan pembuatan materi remediasi adaptif.

**Deliverable utama:** Dashboard interaktif berbasis **Streamlit** yang dapat dijalankan secara lokal oleh dosen.

**Filosofi desain:**

> Otomatisasi tugas berulang dan analitik. Dosen fokus pada kualitas pedagogi, bukan administrasi.

---

## 2. Pemenuhan 5 Kriteria Wajib Sistem Agentic

### ✅ Kriteria 1 — Goal-driven Agent

Educator Copilot memiliki dua tujuan agen yang terukur dan jelas:

| Agent                    | Goal Eksplisit                                                                                                                                                                             |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Curriculum Agent**     | _"Menghasilkan draft RPS 16 minggu yang selaras dengan CPL/CPMK institusi, terdistribusi secara proporsional berdasarkan Bloom Taxonomy, dan siap untuk di-review dosen."_                 |
| **Learning Cycle Agent** | _"Menganalisis hasil kuis mahasiswa, mengidentifikasi miskonsepsi dan topik yang belum dipahami, lalu menghasilkan slide remedial yang dapat langsung digunakan sebelum sesi berikutnya."_ |

Kedua goal ini bersifat **terukur** (ada output konkret) dan **bounded** (ada kondisi selesai yang jelas), memenuhi syarat goal-driven agent.

---

### ✅ Kriteria 2 — Multi-step Reasoning (Chain of Reasoning)

Educator Copilot mengimplementasikan reasoning multi-langkah menggunakan **LangGraph state machine**. Setiap node graph adalah satu langkah reasoning yang eksplisit dan dapat di-trace.

**Chain of Reasoning untuk RPS Generation:**

```
[1] PARSE_INPUT
    └─► Validasi kelengkapan form, normalisasi data CPL/CPMK/bahan kajian
         │
[2] ANALYZE_CONSTRAINTS
    └─► Hitung slot minggu efektif, mapping CPL→CPMK→topik, estimasi bobot Bloom
         │
[3] DRAFT_SKELETON
    └─► Distribusikan topik ke 14 minggu efektif + 2 minggu UTS/UAS
         │
[4] GENERATE_WEEKS (iterasi per minggu)
    └─► Untuk tiap minggu: tentukan sub-CPMK, indikator, metode, referensi
         │
[5] VALIDATE_ALIGNMENT
    └─► Cek apakah semua CPMK sudah terwakili, bobot penilaian sudah benar
         │
[6] REVISE_IF_NEEDED
    └─► Jika ada gap → revisi minggu yang relevan (max 2 iterasi)
         │
[7] FINALIZE_OUTPUT
    └─► Format sebagai RPS terstruktur, simpan ke DB
```

**Chain of Reasoning untuk Quiz Analysis:**

```
[1] LOAD_CONTEXT
    └─► Baca materi minggu ini dari DB + kunci jawaban dosen
         │
[2] SCORE_RESPONSES
    └─► Hitung skor per mahasiswa per soal (PG: exact match; esai: rubrik LLM)
         │
[3] AGGREGATE_STATS
    └─► Hitung distribusi skor, identifikasi soal dengan error rate > 40%
         │
[4] DETECT_MISCONCEPTIONS
    └─► Analisis pola kesalahan → identifikasi miskonsepsi spesifik per topik
         │
[5] PRIORITIZE_GAPS
    └─► Urutkan topik bermasalah berdasarkan: (% salah × dampak ke CPMK)
         │
[6] GENERATE_SUMMARY
    └─► Buat ringkasan performa kelas dalam bahasa natural untuk dosen
         │
[7] GENERATE_REMEDIAL
    └─► Buat 5–8 slide remedial yang menarget gap yang ditemukan di step [4][5]
         │
[8] SAVE_STATE
    └─► Simpan analisis, skor, dan slide ke database
```

---

### ✅ Kriteria 3 — Tool Usage (Minimal 2 Tools)

Educator Copilot menggunakan **4 tools** yang dipanggil oleh agen secara kondisional:

| #      | Tool                   | Kategori              | Fungsi                                                                                                 |
| ------ | ---------------------- | --------------------- | ------------------------------------------------------------------------------------------------------ |
| **T1** | `document_reader_tool`      | File / Dataset        | Membaca dan mengekstrak teks dari PDF materi dosen menggunakan `PyMuPDF`                               |
| **T2** | `database_tool`        | Database              | Read/write ke SQLite — menyimpan dan memuat RPS, hasil kuis, state agen, histori sesi                  |
| **T3** | `quiz_calculator_tool` | Calculator / External | Menghitung skor, distribusi statistik (mean, median, std, error rate per soal)                         |
| **T4** | `web_search_tool`      | External Tool / API   | Mencari referensi pustaka tambahan yang relevan dengan topik minggu tertentu via DuckDuckGo Search API |

**Definisi Tool (LangGraph Tool Binding):**

```python
from langchain_core.tools import tool
import fitz  # PyMuPDF
import sqlite3, json, statistics
from duckduckgo_search import DDGS

@tool
def document_reader_tool(file_path: str) -> str:
    """
    Membaca dan mengekstrak teks dari file PDF materi dosen.
    Digunakan saat agent perlu memahami konten materi untuk review atau konteks analisis kuis.
    """
    doc = fitz.open(file_path)
    text = "\n".join(page.get_text() for page in doc)
    return text[:8000]  # Batasi konteks agar tidak overflow token

@tool
def database_tool(action: str, table: str, data: dict = None, query: str = None) -> str:
    """
    Baca atau tulis data ke SQLite database.
    action: 'read' | 'write' | 'update'
    Digunakan untuk menyimpan RPS, quiz results, agent state, dan histori keputusan.
    """
    conn = sqlite3.connect("Educator Copilot.db")
    if action == "read" and query:
        result = conn.execute(query).fetchall()
        return json.dumps(result)
    elif action == "write" and data:
        # Dynamic insert berdasarkan table dan data
        cols = ", ".join(data.keys())
        vals = ", ".join(["?" for _ in data])
        conn.execute(f"INSERT INTO {table} ({cols}) VALUES ({vals})", list(data.values()))
        conn.commit()
        return "OK"
    conn.close()

@tool
def quiz_calculator_tool(scores: list[float]) -> dict:
    """
    Menghitung statistik distribusi skor kuis kelas.
    Input: list skor semua mahasiswa (0–100).
    Output: mean, median, std_dev, min, max, pct_below_kkm.
    """
    kkm = 60
    return {
        "mean": round(statistics.mean(scores), 2),
        "median": round(statistics.median(scores), 2),
        "std_dev": round(statistics.stdev(scores), 2) if len(scores) > 1 else 0,
        "min": min(scores),
        "max": max(scores),
        "pct_below_kkm": round(sum(1 for s in scores if s < kkm) / len(scores) * 100, 1)
    }

@tool
def web_search_tool(query: str, max_results: int = 3) -> list[dict]:
    """
    Mencari referensi pustaka atau sumber belajar tambahan yang relevan.
    Digunakan saat agent perlu menyarankan referensi untuk topik tertentu dalam RPS.
    """
    with DDGS() as ddgs:
        results = list(ddgs.text(query + " academic reference textbook", max_results=max_results))
    return [{"title": r["title"], "url": r["href"], "snippet": r["body"]} for r in results]
```

---

### ✅ Kriteria 4 — Memory / State

Educator Copilot mengimplementasikan memori dua lapisan:

**Layer 1 — LangGraph In-Graph State (Short-term / Working Memory)**

```python
from typing import TypedDict, Annotated, List
from langgraph.graph.message import add_messages

class Educator CopilotState(TypedDict):
    # Konteks sesi aktif
    messages: Annotated[list, add_messages]   # Histori pesan dalam satu reasoning chain
    current_agent: str                          # "curriculum" | "learning_cycle"
    current_week: int                           # Minggu yang sedang diproses (1–16)

    # Konteks mata kuliah
    course_data: dict                           # Seluruh form input dosen
    cpmk_list: list                             # Daftar CPMK yang sudah diparse

    # State RPS
    rps_weeks: list                             # Draft 16 minggu (diisi bertahap)
    weeks_approved: list[int]                   # Minggu yang sudah di-approve dosen

    # State Quiz Analysis
    quiz_results: dict                          # Hasil kuis yang sedang dianalisis
    detected_gaps: list                         # Topik/miskonsepsi yang ditemukan
    remedial_generated: bool                    # Apakah slide remedial sudah dibuat

    # Tool call tracking
    tool_calls_log: list                        # Log semua tool yang dipanggil + hasilnya
    reasoning_steps: list                       # Log setiap langkah reasoning

    # Control flow
    error_message: str | None
    is_complete: bool
```

**Layer 2 — SQLite Persistent Memory (Long-term)**

```python
# Tabel-tabel yang menjadi long-term memory sistem

CREATE TABLE courses (
    course_id TEXT PRIMARY KEY,
    name TEXT, code TEXT, credits INTEGER,
    form_data TEXT,  -- JSON seluruh input dosen
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cpl_cpmk (
    id TEXT PRIMARY KEY,
    course_id TEXT,
    type TEXT,  -- 'cpl' | 'cpmk'
    code TEXT, description TEXT,
    bloom_level TEXT, cpl_refs TEXT  -- JSON array
);

CREATE TABLE rps_weeks (
    week_id TEXT PRIMARY KEY,
    course_id TEXT, week_number INTEGER,
    type TEXT,  -- 'materi' | 'uts' | 'uas'
    title TEXT, description TEXT,
    sub_cpmk TEXT, indicators TEXT,  -- JSON array
    teaching_method TEXT, topics TEXT,  -- JSON array
    status TEXT DEFAULT 'draft',  -- draft | disetujui | revisi_requested
    dosen_note TEXT,
    approved_at TIMESTAMP
);

CREATE TABLE materials (
    material_id TEXT PRIMARY KEY,
    course_id TEXT, week_number INTEGER,
    filename TEXT, file_path TEXT,
    extracted_text TEXT,
    ai_review TEXT  -- JSON review result
);

CREATE TABLE quiz_sessions (
    quiz_id TEXT PRIMARY KEY,
    course_id TEXT, week_number INTEGER,
    quiz_type TEXT,
    answer_key TEXT,  -- JSON
    question_mapping TEXT,  -- JSON: { q1: {topic, sub_cpmk} }
    rubric TEXT,  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE quiz_results (
    result_id TEXT PRIMARY KEY,
    quiz_id TEXT, student_id TEXT,
    answers TEXT,  -- JSON
    score REAL, ai_feedback TEXT
);

CREATE TABLE quiz_analysis (
    analysis_id TEXT PRIMARY KEY,
    quiz_id TEXT,
    class_stats TEXT,           -- JSON statistik kelas
    topic_performance TEXT,     -- JSON performa per topik
    misconceptions TEXT,        -- JSON miskonsepsi teridentifikasi
    summary_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE remedial_slides (
    slide_id TEXT PRIMARY KEY,
    quiz_id TEXT, for_week_number INTEGER,
    slide_data TEXT,  -- JSON array of slides
    is_approved INTEGER DEFAULT 0
);

CREATE TABLE agent_decision_log (
    log_id TEXT PRIMARY KEY,
    session_id TEXT, agent_name TEXT,
    step_name TEXT, input_summary TEXT,
    output_summary TEXT, tool_used TEXT,
    model_used TEXT, tokens_used INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Setiap keputusan agen dicatat di `agent_decision_log`**, memungkinkan dosen menelusuri _mengapa_ agen menghasilkan output tertentu (auditability).

---

### ✅ Kriteria 5 — Output yang Actionable

Seluruh output Educator Copilot bersifat actionable—bukan sekadar deskripsi:

| Output                    | Format                                    | Actionable karena...                                             |
| ------------------------- | ----------------------------------------- | ---------------------------------------------------------------- |
| Draft RPS per minggu      | Tabel terstruktur di Streamlit (editable) | Dosen langsung approve/edit/revisi tanpa perlu format ulang      |
| Performance Summary       | Dashboard dengan metrik + highlight gap   | Dosen tahu persis topik mana yang butuh remedial dan untuk siapa |
| Slide Remedial            | JSON (preview di Streamlit) + export PPTX | Dosen langsung bisa tampilkan di sesi berikutnya                 |
| Material Review           | Checklist gap vs Sub-CPMK                 | Dosen tahu persis bagian mana materi yang perlu ditambah         |
| Laporan Rekapitulasi CPMK | Tabel capaian (UTS/UAS)                   | Dapat langsung digunakan untuk laporan akreditasi                |

---

## 3. Studi Banding Template RPS Perguruan Tinggi Indonesia

> Riset ini memetakan struktur, komponen, dan kompleksitas RPS dari 10 PT ternama untuk memastikan Educator Copilot mampu menghasilkan output RPS yang valid lintas institusi.

### 3.1 Dasar Regulasi: SN-Dikti & Permendiktisaintek 39/2025

**10 Komponen Wajib RPS (SN-Dikti):**

| # | Komponen | Keterangan |
|---|----------|-----------|
| 1 | Identitas MK | Nama prodi, nama MK, kode MK, semester, SKS |
| 2 | Identitas Dosen | Nama dosen pengampu / tim |
| 3 | CPL | Capaian Pembelajaran Lulusan yang dibebankan ke MK |
| 4 | Kemampuan Akhir (CPMK) | Kemampuan akhir yang direncanakan per tahap |
| 5 | Bahan Kajian | Materi pembelajaran per tahap |
| 6 | Metode Pembelajaran | Strategi / model pembelajaran |
| 7 | Waktu | Alokasi waktu per tahap |
| 8 | Pengalaman Belajar | Deskripsi tugas mahasiswa selama 1 semester |
| 9 | Kriteria Penilaian | Kriteria, indikator, bobot penilaian |
| 10 | Daftar Pustaka | Referensi utama & pendukung |

**Pembaruan Permendiktisaintek 39/2025:**
- Orientasi "Pelampauan Standar" — PT didorong melampaui SN-Dikti menuju standar internasional
- Modularitas & Micro-credential — kurikulum modular, RPL, dan sertifikasi mikro diakui
- Integrasi Teknologi — pemanfaatan teknologi (termasuk AI) harus tercermin dalam RPS
- Transparansi — RPS harus terukur dan terdokumentasi di PD Dikti

### 3.2 Perbandingan Antar Universitas

| Komponen / Fitur | SN-Dikti | ITB | UI | UGM | ITS | UB | Unhas | UNDIP | UNAIR/UPI/UNPAD |
|:-----------------|:--------:|:---:|:--:|:---:|:---:|:--:|:-----:|:-----:|:---------------:|
| Identitas MK | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Dosen/Tim | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| CPL | ✅ | ✅ | ✅ | ✅⁴ | ✅ | ✅ | ✅ | ✅ | ✅ |
| CPMK | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Sub-CPMK | — | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Bahan Kajian | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Metode | ✅ | ✅ | ✅ | ✅ | ✅+Bentuk | ✅ | ✅ | ✅ | ✅ |
| Waktu TM | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Waktu PT+BM | — | — | — | — | ✅ | ✅ | — | — | — |
| Pengalaman Belajar | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ |
| Penilaian + Bobot | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Pustaka | ✅ | ✅ | ✅ | ✅ | — | ✅ | ✅ | ✅ | ✅ |
| Rumpun MK | — | — | — | — | ✅ | ✅ | ✅ | — | — |
| Jenis MK | — | ✅ | — | ✅ | — | — | — | — | — |
| MK Terkait | — | ✅ | — | — | — | — | — | — | — |
| RPMK terpisah | — | ✅ | — | — | — | — | — | — | — |
| Otorisasi formal | — | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅✅ | ✅ |
| Kebijakan AI | — | ✅ | — | — | — | — | — | — | — |
| Media Pembelajaran | — | ✅ | — | — | — | — | — | — | — |
| Deskripsi MK | — | ✅ | — | ✅ | ✅ | ✅ | ✅ | ✅ | — |

*UGM⁴ = 4 aspek CPL eksplisit (Sikap, Pengetahuan, Keterampilan Umum, Keterampilan Khusus)*

**Temuan kunci:**
- **ITB** adalah satu-satunya PT yang memisahkan RPMK (statis, terikat kurikulum) dan RPS (dinamis, per semester) → model paling kompleks (★★★★★)
- **ITS & UB** menambahkan alokasi waktu PT+BM di luar TM dan rumpun MK → kompleksitas tinggi (★★★★☆)
- **UGM** memecah CPL menjadi 4 aspek eksplisit → kompleksitas tinggi (★★★★☆)
- **UI, UNAIR, UPI, UNPAD, Unhas, UNDIP** mengikuti format standar SN-Dikti → kompleksitas sedang (★★★☆☆)

### 3.3 Analisis Kompleksitas (Jumlah Field Unik)

```
ITB      ████████████████████████████ 28+ fields (RPMK + RPS)  ★★★★★
ITS      ██████████████████████████   26  fields               ★★★★☆
UGM      █████████████████████████    25  fields               ★★★★☆
UB       █████████████████████████    25  fields               ★★★★☆
Unhas    ████████████████████████     24  fields               ★★★☆☆
UNDIP    ████████████████████████     24  fields               ★★★☆☆
UI       ██████████████████████       22  fields               ★★★☆☆
UNAIR    ██████████████████████       22  fields               ★★★☆☆
UPI      ██████████████████████       22  fields               ★★★☆☆
UNPAD    ██████████████████████       22  fields               ★★★☆☆
```

### 3.4 Model Input Superset untuk Educator Copilot

Berdasarkan analisis di atas, sistem menggunakan **model superset** — mencakup seluruh field yang ditemukan di semua PT, dengan field opsional yang aktif/nonaktif berdasarkan **preset template institusi**.

**Blok A — Identitas MK (12 fields):**

| # | Field | Wajib | Opsional Untuk |
|---|-------|:-----:|---------------|
| 1 | Nama Program Studi | ✅ | — |
| 2 | Nama MK (ID) | ✅ | — |
| 3 | Nama MK (EN) | — | ITB |
| 4 | Kode MK | ✅ | — |
| 5 | Rumpun MK | — | ITS, UB, Unhas |
| 6 | Bobot SKS | ✅ | — |
| 7 | Semester | ✅ | — |
| 8 | Jenis MK | — | ITB, UGM |
| 9 | Dosen Pengampu (tim) | ✅ | — |
| 10 | Tanggal Penyusunan | ✅ | — |
| 11 | MK Terkait (prereq/coreq) | — | ITB |
| 12 | Deskripsi MK | ✅ | — |

**Blok B — Capaian Pembelajaran (variable):**

| # | Field | Wajib | Keterangan |
|---|-------|:-----:|-----------|
| 1 | CPL yang dibebankan | ✅ | Multi-aspek (UGM: 4 aspek) |
| 2 | CPMK | ✅ | Turunan dari CPL |
| 3 | Sub-CPMK per minggu | ✅ | Turunan dari CPMK |
| 4 | Mapping CPL→CPMK→Sub-CPMK | ✅ | Auto-generated oleh agent |
| 5 | Level Bloom per CPMK | ✅ | C1–C6 |

**Blok C — Matriks Mingguan (per minggu × 10 fields):**

| # | Field | Wajib | Keterangan |
|---|-------|:-----:|-----------|
| 1 | Minggu ke- | ✅ | 1–16 |
| 2 | Sub-CPMK target | ✅ | Auto-mapped |
| 3 | Bahan Kajian / Topik | ✅ | — |
| 4 | Bentuk Pembelajaran | — | ITS, UB (kuliah, praktikum, dll.) |
| 5 | Metode Pembelajaran | ✅ | PBL, diskusi, dll. |
| 6 | Waktu TM (menit) | ✅ | SKS × 50 |
| 7 | Waktu PT (menit) | — | ITS, UB |
| 8 | Waktu BM (menit) | — | ITS, UB |
| 9 | Pengalaman Belajar / Tugas | ✅ | Deskripsi aktivitas mahasiswa |
| 10 | Referensi per minggu | ✅ | Auto-suggested via web_search_tool |

**Blok D — Penilaian (variable):**

| # | Field | Wajib | Keterangan |
|---|-------|:-----:|-----------|
| 1 | Indikator penilaian per Sub-CPMK | ✅ | — |
| 2 | Kriteria/rubrik penilaian | ✅ | — |
| 3 | Teknik penilaian (tes/non-tes) | — | ITS |
| 4 | Bobot per komponen (total=100%) | ✅ | — |
| 5 | Mapping penilaian→Sub-CPMK→CPMK→CPL | ✅ | Auto-generated |

**Blok E — Otorisasi & Tambahan:**

| # | Field | Wajib | Keterangan |
|---|-------|:-----:|-----------|
| 1 | Dosen Pengembang | ✅ | — |
| 2 | Koordinator RMK / Koordinator MK | — | ITS, UB, Unhas |
| 3 | Ka Prodi | — | Semua (untuk cetak) |
| 4 | Kebijakan AI | — | ITB |
| 5 | Media Pembelajaran | — | ITB |
| 6 | Pustaka Utama | ✅ | — |

### 3.5 Preset Template Institusi

Sistem menyediakan **4 preset** yang mengaktifkan/menonaktifkan field opsional:

| Preset | Universitas | Field Aktif | Fitur Khusus |
|--------|------------|:-----------:|-------------|
| **ITB Mode** | ITB | 28+ | RPMK+RPS terpisah, nama EN, kebijakan AI, jenis MK 5 kategori, media |
| **ITS/UB Mode** | ITS, UB | 26 | TM+PT+BM, rumpun MK, bentuk vs metode, teknik penilaian |
| **UGM Mode** | UGM | 25 | 4 aspek CPL eksplisit, Sub-CPMK detail, status MK |
| **Standard Mode** | UI, UNAIR, UPI, UNPAD, Unhas, UNDIP | 22 | Format SN-Dikti standar |

---

## 4. Arsitektur Sistem — Diagram Wajib

### 4.1 Arsitektur Berlapis (Format Standar)

```
┌─────────────────────────────────────────────────────────────────┐
│                    [INPUT DATA / ENVIRONMENT]                   │
│                                                                 │
│  Preset Template Institusi (ITB/ITS-UB/UGM/Standard Mode)      │
│  Form input dosen: Blok A (Identitas 12 fields)                │
│                    Blok B (CPL/CPMK/Bloom)                     │
│                    Blok C (Metode, Waktu TM/PT/BM)             │
│                    Blok D (Penilaian + Bobot)                  │
│                    Blok E (Otorisasi + Pustaka)                │
│  Upload PDF materi  |  File hasil kuis (CSV/JSON)  |  Kunci jwb│
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                      [PERCEPTION LAYER]                         │
│                                                                 │
│  • Form Validator: cek kelengkapan & konsistensi input         │
│  • PDF Parser (PyMuPDF): ekstraksi teks materi dosen           │
│  • Quiz Parser: normalisasi jawaban mahasiswa dari CSV/JSON    │
│  • Intent Classifier: tentukan task agent (RPS / Quiz / Review)│
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                [AGENT REASONING — LangGraph]                    │
│                                                                 │
│  ┌─────────────────────┐      ┌─────────────────────────────┐  │
│  │  CURRICULUM AGENT   │      │   LEARNING CYCLE AGENT      │  │
│  │                     │      │                             │  │
│  │  Nodes (steps):     │      │  Nodes (steps):             │  │
│  │  1. parse_input     │      │  1. load_context            │  │
│  │  2. analyze_constr  │      │  2. score_responses         │  │
│  │  3. draft_skeleton  │      │  3. aggregate_stats         │  │
│  │  4. generate_weeks  │      │  4. detect_misconceptions   │  │
│  │  5. validate_align  │      │  5. prioritize_gaps         │  │
│  │  6. revise_if_need  │      │  6. generate_summary        │  │
│  │  7. finalize_output │      │  7. generate_remedial       │  │
│  └─────────────────────┘      │  8. save_state              │  │
│                               └─────────────────────────────┘  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                        [TOOL USAGE]                             │
│                                                                 │
│  T1: document_reader_tool    → PyMuPDF  (file / dataset)            │
│  T2: database_tool      → SQLite   (database)                  │
│  T3: quiz_calculator_tool → Python stats (calculator)          │
│  T4: web_search_tool    → DuckDuckGo API (external tool)       │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                          [ACTION]                               │
│                                                                 │
│  • Simpan draft RPS ke SQLite                                  │
│  • Simpan skor & analisis kuis                                 │
│  • Generate JSON slide remedial                                │
│  • Export PPTX (pptx library)                                  │
│  • Kirim output ke Streamlit untuk ditampilkan ke dosen        │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    [OUTPUT — Streamlit Dashboard]               │
│                                                                 │
│  • Tabel RPS 16 minggu (editable, approve/revisi per baris)    │
│  • Dashboard performa kuis (chart + tabel gap)                 │
│  • Preview slide remedial + tombol export PPTX                 │
│  • Review materi (checklist gap vs Sub-CPMK)                   │
│  • Laporan rekapitulasi CPMK                                   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
              ┌────────────────┘
              │    (loop feedback)
              ▼
┌─────────────────────────────────────────────────────────────────┐
│                   [MEMORY & FEEDBACK]                           │
│                                                                 │
│  Short-term : LangGraph Educator CopilotState (working memory per sesi)  │
│  Long-term  : SQLite Educator Copilot.db                                  │
│               ├── rps_weeks (state RPS + approval history)    │
│               ├── quiz_analysis (histori analisis per minggu) │
│               ├── remedial_slides (slide yang pernah dibuat)  │
│               └── agent_decision_log (audit trail semua step) │
│                                                                 │
│  Feedback loop: hasil kuis → konteks analisis minggu berikutnya│
└─────────────────────────────────────────────────────────────────┘
```

---

### 4.2 Spesifikasi Input — Proses — Output (I-P-O)

**CURRICULUM AGENT (RPS Generation):**

| Tahap | Komponen | Detail |
|-------|----------|--------|
| **INPUT** | Form Blok A–E | 12+ field identitas, CPL/CPMK/Bloom, metode, penilaian, pustaka |
| | Preset Institusi | ITB/ITS-UB/UGM/Standard — menentukan field aktif |
| | PDF Silabus Lama (opsional) | Ekstraksi via `document_reader_tool` |
| **PROSES** | 1. `parse_input` | Validasi kelengkapan + normalisasi per preset |
| | 2. `analyze_constraints` | Hitung slot minggu efektif, mapping CPL→CPMK→topik, bobot Bloom |
| | 3. `draft_skeleton` | Distribusi topik ke 14 minggu + UTS/UAS |
| | 4. `generate_weeks` | LLM generate konten per minggu (Sub-CPMK, indikator, metode) |
| | 5. `validate_alignment` | Cek semua CPMK terwakili, bobot penilaian valid |
| | 6. `revise_if_needed` | Auto-revisi jika ada gap (max 2 iterasi) |
| | 7. `finalize_output` | Format sesuai preset, simpan ke DB |
| **OUTPUT** | Draft RPS 16 minggu | Tabel terstruktur editable di Streamlit |
| | Mapping CPL→CPMK→Sub-CPMK | Matriks alignment auto-generated |
| | Dokumen cetak (RPMK+RPS untuk ITB) | Export DOCX/PDF sesuai format institusi |

**LEARNING CYCLE AGENT (Quiz Analysis + Remedial):**

| Tahap | Komponen | Detail |
|-------|----------|--------|
| **INPUT** | Hasil kuis (CSV/JSON) | Jawaban mahasiswa per soal |
| | Kunci jawaban + rubrik | Dari dosen |
| | Mapping soal→topik→Sub-CPMK | Konteks kurikulum |
| | Materi minggu ini (PDF) | Ekstraksi via `document_reader_tool` |
| **PROSES** | 1. `load_context` | Baca materi + kunci dari DB |
| | 2. `score_responses` | Hitung skor per mahasiswa (PG: exact, Esai: rubrik LLM) |
| | 3. `aggregate_stats` | Statistik kelas (mean, median, std, error rate) |
| | 4. `detect_misconceptions` | Analisis pola kesalahan → miskonsepsi |
| | 5. `prioritize_gaps` | Urutkan berdasarkan (% salah × dampak CPMK) |
| | 6. `generate_summary` | Ringkasan performa dalam bahasa natural |
| | 7. `generate_remedial` | Buat 5–8 slide remedial target gap |
| | 8. `save_state` | Simpan semua ke DB |
| **OUTPUT** | Performance Dashboard | Chart distribusi + highlight gap per topik |
| | Miskonsepsi Report | Daftar miskonsepsi + topik terdampak |
| | Slide Remedial | JSON preview + export PPTX |
| | Laporan Rekapitulasi CPMK | Tabel capaian per CPMK (UTS/UAS) |

### 4.3 Daftar Fungsi Lengkap

**A. Fungsi Inti (Core Functions):**

| # | Fungsi | Deskripsi | Agent |
|---|--------|-----------|-------|
| F01 | `select_institution_preset()` | Pilih preset ITB/ITS-UB/UGM/Standard, aktifkan field terkait | — (UI) |
| F02 | `validate_form_input()` | Validasi kelengkapan semua field wajib per preset | Curriculum |
| F03 | `parse_cpl_cpmk()` | Parse CPL→CPMK→Sub-CPMK + mapping Bloom | Curriculum |
| F04 | `calculate_week_distribution()` | Distribusi topik ke 14 minggu berdasarkan bobot Bloom | Curriculum |
| F05 | `generate_week_content()` | Generate konten per minggu via LLM (loop 14×) | Curriculum |
| F06 | `validate_curriculum_alignment()` | Cek alignment CPMK↔minggu, bobot penilaian = 100% | Curriculum |
| F07 | `auto_revise_rps()` | Revisi otomatis jika ada gap alignment (max 2×) | Curriculum |
| F08 | `score_quiz_responses()` | Hitung skor PG (exact match) / Esai (rubrik LLM) | Learning |
| F09 | `calculate_class_statistics()` | Mean, median, std, error rate via `quiz_calculator_tool` | Learning |
| F10 | `detect_misconceptions()` | Identifikasi miskonsepsi dari pola jawaban salah | Learning |
| F11 | `prioritize_learning_gaps()` | Ranking gap berdasarkan dampak ke CPMK | Learning |
| F12 | `generate_remedial_slides()` | Buat slide remedial 5–8 halaman | Learning |
| F13 | `review_material_alignment()` | Review PDF materi vs Sub-CPMK minggu ini | Inline |

**B. Fungsi Pendukung (Support Functions):**

| # | Fungsi | Deskripsi |
|---|--------|----------|
| F14 | `search_references()` | Cari referensi pustaka via `web_search_tool` |
| F15 | `extract_pdf_text()` | Ekstraksi teks PDF via `document_reader_tool` |
| F15b| `generate_quiz_from_material()` | Generate kuis otomatis (PG/Esai) dari teks PDF |
| F16 | `save_to_database()` | Simpan state/hasil ke SQLite via `database_tool` |
| F17 | `load_from_database()` | Baca data dari SQLite |
| F18 | `export_rps_docx()` | Export RPS ke DOCX sesuai format institusi |
| F19 | `export_rps_pdf()` | Export RPS ke PDF sesuai format institusi |
| F20 | `export_slides_pptx()` | Export slide remedial ke PPTX |
| F21 | `log_agent_decision()` | Catat keputusan agent ke `agent_decision_log` |
| F22 | `route_llm_by_task()` | Routing model LLM berdasarkan task (heavy/light) |
| F23 | `fallback_to_ollama()` | Fallback ke Ollama jika API gagal |
| F24 | `generate_cpmk_report()` | Buat laporan rekapitulasi capaian CPMK |

**C. Fungsi UI (Streamlit Functions):**

| # | Fungsi | Halaman |
|---|--------|--------|
| F25 | `render_setup_form()` | Halaman 1 — Setup MK (form Blok A–E) |
| F26 | `render_rps_table()` | Halaman 2 — Tabel RPS editable per minggu |
| F27 | `render_week_approval()` | Halaman 2 — Approve/Edit/Revisi per baris |
| F28 | `render_material_upload()` | Halaman 3 — Upload PDF + review AI |
| F29 | `render_quiz_input()` | Halaman 4 — Input kuis (Manual/CSV/AI Generate) |
| F30 | `render_performance_dashboard()` | Halaman 5 — Chart + tabel gap + slide |
| F31 | `render_cpmk_report()` | Halaman 6 — Laporan rekapitulasi |
| F32 | `render_export_panel()` | Halaman 7 — Export DOCX/PDF/PPTX |

### 4.4 Workflow End-to-End (Diperkaya)

```
PHASE 0 — PEMILIHAN TEMPLATE INSTITUSI
═══════════════════════════════════════
Dosen pilih preset: [ITB] [ITS/UB] [UGM] [Standard]
           │
           ▼
Sistem aktifkan field sesuai preset
(contoh: ITB → aktifkan nama EN, kebijakan AI, RPMK terpisah)
(contoh: Standard → 22 field wajib saja)
           │
           ▼

PHASE 1 — SETUP MATA KULIAH
════════════════════════════
Dosen isi form Blok A–E di Streamlit
  Blok A: Identitas MK (12 fields, field opsional sesuai preset)
  Blok B: CPL/CPMK + Bloom level
  Blok C: Metode + Waktu (TM wajib; PT/BM opsional ITS/UB)
  Blok D: Komponen Penilaian (bobot harus = 100%)
  Blok E: Otorisasi + Pustaka
           │
           ▼
[Curriculum Agent — LangGraph]
  F02:validate → F03:parse_cpmk → F04:distribute
  → F05:generate_weeks [T1:pdf, T4:search]
  → F06:validate_alignment → F07:auto_revise? (max 2×)
  → finalize [T2:db write]
           │
           ▼
Streamlit: Tabel RPS 16 minggu (F26)
Dosen: Approve ✓ / Edit ✏️ / Revisi 🔄 per baris (F27)
           │
           ▼
Status semua minggu = "disetujui" → RPS Published
  └─ F18/F19: Export DOCX/PDF sesuai format institusi
     (ITB: 2 dokumen RPMK + RPS)
     (Standard: 1 dokumen RPS)


PHASE 2 — SIKLUS PER MINGGU (loop 14×)
════════════════════════════════════════
Dosen upload PDF materi minggu ke-N (F28)
           │
           ▼
[Material Review — inline call]
  F15:extract_pdf → F13:review_alignment vs Sub-CPMK
  → tampil di Streamlit (checklist gap)
           │
Sesi pertemuan berlangsung
           │
           ▼
Dosen input hasil kuis + kunci jawaban (F29)
           │
           ▼
[Learning Cycle Agent — LangGraph]
  F17:load_context [T2:db read]
  → F08:score_responses [T3:calculator]
  → F09:aggregate_stats → F10:detect_misconceptions [LLM]
  → F11:prioritize_gaps → generate_summary [LLM]
  → F12:generate_remedial [LLM] → F16:save_state [T2:db write]
           │
           ▼
Streamlit: Performance Dashboard (F30) + Preview Slide Remedial
Dosen: Approve slide / Edit / F20:Export PPTX
           │
           ▼
Loop ke minggu berikutnya (konteks kumulatif di DB)


PHASE 3 — UTS & UAS (Minggu 8 & 16)
══════════════════════════════════════
Pipeline sama dengan kuis biasa
+ Output tambahan: F24:Laporan Rekapitulasi CPMK
  → F31:render_cpmk_report → F19:export PDF
```

---

## 5. Arsitektur LangGraph — Graf Detail

### 5.1 Struktur Graf Keseluruhan

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

# Router utama: tentukan agent mana yang dipanggil
def route_to_agent(state: Educator CopilotState) -> str:
    task = state.get("current_agent")
    if task == "curriculum":
        return "curriculum_agent_entry"
    elif task == "learning_cycle":
        return "learning_cycle_entry"
    else:
        return "error_handler"

# ── CURRICULUM AGENT SUBGRAPH ─────────────────────────────
curriculum_graph = StateGraph(Educator CopilotState)
curriculum_graph.add_node("parse_input",        node_parse_input)
curriculum_graph.add_node("analyze_constraints", node_analyze_constraints)
curriculum_graph.add_node("draft_skeleton",     node_draft_skeleton)
curriculum_graph.add_node("generate_weeks",     node_generate_weeks)
curriculum_graph.add_node("validate_alignment", node_validate_alignment)
curriculum_graph.add_node("revise_if_needed",   node_revise_if_needed)
curriculum_graph.add_node("finalize_rps",       node_finalize_rps)

curriculum_graph.set_entry_point("parse_input")
curriculum_graph.add_edge("parse_input",        "analyze_constraints")
curriculum_graph.add_edge("analyze_constraints","draft_skeleton")
curriculum_graph.add_edge("draft_skeleton",     "generate_weeks")
curriculum_graph.add_edge("generate_weeks",     "validate_alignment")
curriculum_graph.add_conditional_edges(
    "validate_alignment",
    lambda s: "revise_if_needed" if s.get("needs_revision") else "finalize_rps",
    {"revise_if_needed": "revise_if_needed", "finalize_rps": "finalize_rps"}
)
curriculum_graph.add_edge("revise_if_needed",   "validate_alignment")  # loop max 2x
curriculum_graph.add_edge("finalize_rps",       END)

# ── LEARNING CYCLE AGENT SUBGRAPH ─────────────────────────
learning_graph = StateGraph(Educator CopilotState)
learning_graph.add_node("load_context",          node_load_context)
learning_graph.add_node("score_responses",       node_score_responses)
learning_graph.add_node("aggregate_stats",       node_aggregate_stats)
learning_graph.add_node("detect_misconceptions", node_detect_misconceptions)
learning_graph.add_node("prioritize_gaps",       node_prioritize_gaps)
learning_graph.add_node("generate_summary",      node_generate_summary)
learning_graph.add_node("generate_remedial",     node_generate_remedial)
learning_graph.add_node("save_state",            node_save_state)

learning_graph.set_entry_point("load_context")
learning_graph.add_edge("load_context",          "score_responses")
learning_graph.add_conditional_edges(
    "score_responses",
    lambda s: "aggregate_stats",  # selalu lanjut setelah scoring selesai
)
learning_graph.add_edge("aggregate_stats",       "detect_misconceptions")
learning_graph.add_edge("detect_misconceptions", "prioritize_gaps")
learning_graph.add_edge("prioritize_gaps",       "generate_summary")
learning_graph.add_edge("generate_summary",      "generate_remedial")
learning_graph.add_edge("generate_remedial",     "save_state")
learning_graph.add_edge("save_state",            END)

# ── MAIN GRAPH (Router) ───────────────────────────────────
main_graph = StateGraph(Educator CopilotState)
main_graph.add_node("router",                route_to_agent)
main_graph.add_node("curriculum_agent",      curriculum_graph.compile())
main_graph.add_node("learning_cycle_agent",  learning_graph.compile())
main_graph.add_node("error_handler",         node_error_handler)

main_graph.set_entry_point("router")
main_graph.add_conditional_edges("router", route_to_agent)

# Compile dengan checkpointing ke SQLite (persistent memory)
memory = SqliteSaver.from_conn_string("Educator Copilot.db")
Educator Copilot_app = main_graph.compile(checkpointer=memory)
```

### 5.2 Detail Setiap Node

```python
# ── NODE: parse_input ────────────────────────────────────
def node_parse_input(state: Educator CopilotState) -> Educator CopilotState:
    """
    Tujuan: Validasi dan normalisasi seluruh form input dosen.
    Tool: database_tool (baca template CPMK institusi)
    """
    course_data = state["course_data"]

    # Validasi: semua field wajib terisi
    required = ["name", "code", "credits", "cpl", "cpmk", "bahan_kajian",
                "teaching_methods", "assessment"]
    missing = [f for f in required if not course_data.get(f)]
    if missing:
        return {**state, "error_message": f"Field belum lengkap: {missing}"}

    # Validasi: total bobot penilaian harus = 100
    total_weight = sum(a["weight"] for a in course_data["assessment"])
    if total_weight != 100:
        return {**state, "error_message": f"Total bobot penilaian = {total_weight}%, harus 100%"}

    # Log reasoning step
    steps = state.get("reasoning_steps", [])
    steps.append({
        "step": "parse_input",
        "result": f"Form valid. {len(course_data['cpmk'])} CPMK, "
                  f"{len(course_data['bahan_kajian'])} bahan kajian."
    })
    return {**state, "cpmk_list": course_data["cpmk"], "reasoning_steps": steps}


# ── NODE: analyze_constraints ────────────────────────────
def node_analyze_constraints(state: Educator CopilotState) -> Educator CopilotState:
    """
    Tujuan: Hitung slot minggu efektif dan distribusi topik berdasarkan Bloom.
    Tool: quiz_calculator_tool (untuk kalkulasi slot)
    """
    credits = state["course_data"]["credits"]
    minutes_per_week = credits * 50  # 1 SKS = 50 menit TM

    # Bloom weight: C1-C2=1 slot, C3-C4=1.5 slot, C5-C6=2 slot
    bloom_weights = {"C1":1, "C2":1, "C3":1.5, "C4":1.5, "C5":2, "C6":2}

    cpmk_slots = []
    for cpmk in state["cpmk_list"]:
        bloom = cpmk.get("bloom_level", "C3")
        weight = bloom_weights.get(bloom, 1.5)
        cpmk_slots.append({"cpmk": cpmk["code"], "slots": weight})

    total_slots = sum(c["slots"] for c in cpmk_slots)
    # Skala ke 14 minggu efektif
    for cs in cpmk_slots:
        cs["weeks_allocated"] = round(cs["slots"] / total_slots * 14, 1)

    steps = state.get("reasoning_steps", [])
    steps.append({
        "step": "analyze_constraints",
        "result": f"Total slot terbobot: {total_slots:.1f}. "
                  f"Distribusi ke 14 minggu efektif selesai.",
        "detail": cpmk_slots
    })
    return {**state, "cpmk_slot_distribution": cpmk_slots,
            "reasoning_steps": steps}


# ── NODE: generate_weeks ─────────────────────────────────
def node_generate_weeks(state: Educator CopilotState) -> Educator CopilotState:
    """
    Tujuan: Generate konten tiap minggu menggunakan LLM.
    Tool: web_search_tool (referensi per topik), database_tool (simpan draft)
    Model: claude-haiku / gpt-4o-mini (cost-efficient, structured output)
    """
    from langchain_anthropic import ChatAnthropic

    llm = ChatAnthropic(model="claude-haiku-20240307")  # model ringan untuk loop 14x
    rps_weeks = []

    for week_num in range(1, 17):
        if week_num == 8:
            # UTS — tidak perlu generate konten materi
            rps_weeks.append({"week": 8, "type": "uts",
                "title": "Ujian Tengah Semester (UTS)",
                "description": "Evaluasi capaian CPMK 1–3 (Blok 1)",
                "status": "draft"})
            continue
        if week_num == 16:
            # UAS
            rps_weeks.append({"week": 16, "type": "uas",
                "title": "Ujian Akhir Semester (UAS)",
                "description": "Evaluasi capaian CPMK keseluruhan",
                "status": "draft"})
            continue

        # Tentukan topik untuk minggu ini dari skeleton
        topic = state["week_skeleton"][week_num - 1]

        # Search referensi via web_search_tool
        refs = web_search_tool.invoke(
            f"{topic['topic']} {state['course_data']['name']} textbook reference"
        )

        # Generate dengan LLM
        prompt = f"""
Kamu adalah asisten perancangan kurikulum perguruan tinggi Indonesia.
Buat konten RPS untuk SATU pertemuan dengan ketentuan berikut:

Mata Kuliah: {state['course_data']['name']} ({state['course_data']['credits']} SKS)
Minggu ke  : {week_num} dari 16
Topik      : {topic['topic']}
CPMK terkait: {topic['cpmk_ref']}
Level Bloom : {topic['bloom_level']}
Metode pembelajaran tersedia: {state['course_data']['teaching_methods']}

Output HARUS berupa JSON dengan struktur:
{{
  "title": "judul singkat pertemuan (maks 10 kata)",
  "description": "deskripsi 3-4 kalimat: tujuan, aktivitas, outcome yang diharapkan",
  "sub_cpmk": "indikator capaian spesifik minggu ini",
  "learning_indicators": ["indikator 1", "indikator 2", "indikator 3"],
  "teaching_method": "metode yang paling sesuai untuk topik dan Bloom level ini",
  "topics_covered": ["subtopik 1", "subtopik 2"],
  "references": ["ref dari pencarian yang relevan"]
}}
"""
        response = llm.invoke(prompt)
        week_data = json.loads(response.content)
        week_data["week"] = week_num
        week_data["type"] = "materi"
        week_data["status"] = "draft"
        rps_weeks.append(week_data)

        # Catat tool usage
        tool_log = state.get("tool_calls_log", [])
        tool_log.append({
            "week": week_num,
            "tool": "web_search_tool",
            "query": f"{topic['topic']} textbook reference",
            "results_count": len(refs)
        })

    # Simpan ke SQLite via database_tool
    database_tool.invoke({
        "action": "write",
        "table": "rps_weeks",
        "data": {"course_id": state["course_data"]["code"],
                 "weeks_json": json.dumps(rps_weeks)}
    })

    return {**state, "rps_weeks": rps_weeks,
            "tool_calls_log": state.get("tool_calls_log", [])}


# ── NODE: score_responses (Quiz PG) ──────────────────────
def node_score_responses(state: Educator CopilotState) -> Educator CopilotState:
    """
    Tujuan: Hitung skor setiap mahasiswa berdasarkan jawaban vs kunci.
    Tool: quiz_calculator_tool
    """
    quiz = state["quiz_results"]
    answer_key = quiz["answer_key"]
    responses = quiz["student_responses"]

    scored = []
    all_scores = []

    for student in responses:
        sid = student["student_id"]
        answers = student["answers"]

        correct = sum(1 for q, a in answers.items() if answer_key.get(q) == a)
        score = round(correct / len(answer_key) * 100, 1)
        all_scores.append(score)

        # Tandai soal yang salah
        wrong_questions = [q for q, a in answers.items() if answer_key.get(q) != a]
        scored.append({
            "student_id": sid,
            "score": score,
            "correct": correct,
            "total": len(answer_key),
            "wrong_questions": wrong_questions
        })

    # Hitung statistik kelas via quiz_calculator_tool
    stats = quiz_calculator_tool.invoke(all_scores)

    steps = state.get("reasoning_steps", [])
    steps.append({
        "step": "score_responses",
        "result": f"Scoring selesai. {len(scored)} mahasiswa. "
                  f"Rata-rata: {stats['mean']}, Di bawah KKM: {stats['pct_below_kkm']}%"
    })
    return {**state, "scored_students": scored,
            "class_stats": stats, "reasoning_steps": steps}


# ── NODE: detect_misconceptions ──────────────────────────
def node_detect_misconceptions(state: Educator CopilotState) -> Educator CopilotState:
    """
    Tujuan: Identifikasi miskonsepsi dari pola jawaban salah.
    Tool: LLM (claude-sonnet untuk kuis esai, claude-haiku untuk PG)
    """
    from langchain_anthropic import ChatAnthropic

    # Untuk PG: analisis soal mana yang paling banyak salah
    scored = state["scored_students"]
    answer_key = state["quiz_results"]["answer_key"]
    q_mapping = state["quiz_results"]["question_mapping"]

    # Hitung error rate per soal
    error_rates = {}
    for q in answer_key:
        wrong_count = sum(1 for s in scored if q in s["wrong_questions"])
        error_rates[q] = {
            "error_rate": round(wrong_count / len(scored) * 100, 1),
            "topic": q_mapping.get(q, {}).get("topic", "Unknown"),
            "sub_cpmk": q_mapping.get(q, {}).get("sub_cpmk", "")
        }

    # Soal dengan error rate > 40% = bermasalah
    problematic = {q: v for q, v in error_rates.items() if v["error_rate"] > 40}

    # Minta LLM analisis miskonsepsi berdasarkan pola
    llm = ChatAnthropic(model="claude-haiku-20240307")
    prompt = f"""
Analisis pola kesalahan mahasiswa pada kuis berikut.
Soal dengan error rate tinggi: {json.dumps(problematic, indent=2)}
Konteks materi minggu ini: {state.get('week_material_summary', 'N/A')}

Identifikasi 2–4 miskonsepsi yang kemungkinan besar menyebabkan kesalahan ini.
Output JSON: [{{"misconception": "...", "affected_topics": [...], "likely_cause": "..."}}]
"""
    response = llm.invoke(prompt)
    misconceptions = json.loads(response.content)

    steps = state.get("reasoning_steps", [])
    steps.append({
        "step": "detect_misconceptions",
        "result": f"{len(problematic)} soal bermasalah. "
                  f"{len(misconceptions)} miskonsepsi teridentifikasi.",
        "detail": misconceptions
    })
    return {**state, "error_rates": error_rates,
            "detected_gaps": misconceptions,
            "reasoning_steps": steps}
```

---

> **Catatan:** Alur sistem end-to-end yang lengkap (Phase 0–3) telah didokumentasikan di **Bagian 4.4 Workflow End-to-End (Diperkaya)** di atas.

---

## 6. Deliverable: Streamlit Dashboard

### 6.1 Struktur Halaman

```
Educator Copilot/
├── app.py                  # Entry point Streamlit
├── pages/
│   ├── 0_preset.py         # [BARU] Pemilihan preset template institusi
│   ├── 1_setup_mk.py       # Form input mata kuliah (Blok A–E, field dinamis per preset)
│   ├── 2_rps_review.py     # Tabel RPS + approve/edit per minggu
│   ├── 3_material_upload.py # Upload PDF + AI review
│   ├── 4_quiz_input.py     # Input hasil kuis + kunci jawaban
│   ├── 5_performance.py    # Dashboard analisis + slide remedial
│   ├── 6_reports.py        # Laporan rekapitulasi CPMK
│   └── 7_export.py         # [BARU] Export DOCX/PDF/PPTX sesuai format institusi
├── agents/
│   ├── curriculum_agent.py  # LangGraph subgraph + nodes
│   ├── learning_agent.py    # LangGraph subgraph + nodes
│   └── state.py             # Educator CopilotState TypedDict
├── tools/
│   ├── document_reader.py        # document_reader_tool
│   ├── database.py          # database_tool + SQLite setup
│   ├── calculator.py        # quiz_calculator_tool
│   ├── web_search.py        # web_search_tool
│   └── quiz_generator.py    # [BARU] AI Quiz Generator (PG & Esai)
├── lib/
│   ├── llm_router.py        # Tiered model routing + Ollama fallback
│   ├── slide_exporter.py    # JSON → PPTX via python-pptx
│   ├── template_presets.py  # [BARU] Definisi field per preset (ITB/ITS-UB/UGM/Standard)
│   └── docx_exporter.py    # [BARU] Export RPS → DOCX/PDF sesuai format institusi
├── Educator Copilot.db                 # SQLite database (auto-created)
└── requirements.txt
```

### 6.2 Halaman Utama per Fitur

**Halaman 1 — Setup Mata Kuliah (`1_setup_mk.py`)**

```python
import streamlit as st
from agents.curriculum_agent import run_curriculum_agent

st.title("⚙️ Setup Mata Kuliah")

with st.form("form_mk"):
    # Blok A: Identitas
    st.subheader("Identitas Mata Kuliah")
    col1, col2, col3 = st.columns(3)
    name = col1.text_input("Nama Mata Kuliah *")
    code = col2.text_input("Kode MK *")
    credits = col3.number_input("Jumlah SKS *", min_value=1, max_value=6)

    # Blok B: CPL/CPMK
    st.subheader("Capaian Pembelajaran")
    cpl_input = st.text_area("CPL yang Diemban MK * (satu per baris)")
    cpmk_input = st.text_area("CPMK * (format: CPMK-1 | deskripsi | CPL-ref | BloomLevel)")

    # Blok C: Pedagogi
    st.subheader("Metode & Modalitas")
    methods = st.multiselect("Metode Pembelajaran *",
        ["Ceramah", "Diskusi", "Studi Kasus", "PBL", "PjBL", "Praktikum"])
    modality = st.multiselect("Modalitas *",
        ["Sinkron Tatap Muka", "Sinkron Daring", "Asinkron", "Hybrid"])

    # Blok D: Penilaian
    st.subheader("Komponen Penilaian")
    st.info("Total bobot harus = 100%")
    assessment_data = st.data_editor(
        {"Komponen": ["Quiz", "UTS", "UAS", "Tugas"],
         "Bobot (%)": [20, 30, 35, 15],
         "CPMK": ["", "", "", ""]},
        num_rows="dynamic"
    )

    # Blok E: Referensi
    bahan_kajian = st.text_area("Bahan Kajian * (satu topik per baris)")
    references = st.text_area("Pustaka Utama")

    submitted = st.form_submit_button("🚀 Generate RPS")

if submitted:
    with st.spinner("Agent sedang menyusun RPS 16 minggu..."):
        result = run_curriculum_agent({...})  # form data
    st.success("✅ Draft RPS berhasil dibuat! Lanjut ke halaman Review RPS.")

    # Tampilkan reasoning steps untuk transparansi
    with st.expander("🔍 Lihat proses reasoning agent"):
        for step in result["reasoning_steps"]:
            st.write(f"**{step['step']}:** {step['result']}")
```

**Halaman 2 — Review RPS (`2_rps_review.py`)**

```python
st.title("📋 Review & Approval RPS")

# Status bar
col1, col2, col3 = st.columns(3)
col1.metric("Total Minggu", "16")
col2.metric("Sudah Disetujui", f"{approved_count}/16")
col3.metric("Status RPS", "Draft" if approved_count < 14 else "Siap Publish")

# Tabel RPS dengan aksi per baris
for week in rps_weeks:
    with st.expander(f"Minggu {week['week']} — {week['title']} [{week['status']}]"):

        # Edit mode
        new_title = st.text_input("Judul", week["title"], key=f"title_{week['week']}")
        new_desc  = st.text_area("Deskripsi", week["description"], key=f"desc_{week['week']}")

        col1, col2, col3 = st.columns(3)
        if col1.button("✅ Setujui", key=f"approve_{week['week']}"):
            approve_week(week["week"])
        if col2.button("✏️ Simpan Edit", key=f"edit_{week['week']}"):
            save_edit(week["week"], new_title, new_desc)

        # Request revisi ke agent
        revision_note = st.text_input("Instruksi revisi ke AI:", key=f"rev_{week['week']}")
        if col3.button("🔄 Minta Revisi AI", key=f"revise_{week['week']}"):
            with st.spinner("Agent merevisi..."):
                revise_week(week["week"], revision_note)

if st.button("📢 Publish RPS ke Mahasiswa", disabled=approved_count < 14):
    publish_rps()
    st.success("RPS berhasil dipublikasikan!")
```

**Halaman 5 — Performance & Remedial (`5_performance.py`)**

```python
import plotly.express as px

st.title("📊 Analisis Performa Kuis")

# Statistik kelas
stats = load_class_stats()
col1,col2,col3,col4 = st.columns(4)
col1.metric("Rata-rata", f"{stats['mean']}")
col2.metric("Nilai Tertinggi", f"{stats['max']}")
col3.metric("Nilai Terendah", f"{stats['min']}")
col4.metric("Di bawah KKM", f"{stats['pct_below_kkm']}%",
            delta_color="inverse")

# Distribusi nilai (histogram)
st.subheader("Distribusi Nilai Kelas")
fig = px.histogram(scores_df, x="score", nbins=10,
                   color_discrete_sequence=["#2E75B6"])
st.plotly_chart(fig)

# Performa per topik (bar chart)
st.subheader("Pemahaman per Topik")
topic_df = load_topic_performance()
fig2 = px.bar(topic_df, x="topic", y="pct_correct",
              color="status",  # Merah = < 60%, Kuning = 60-79%, Hijau = >= 80%
              color_discrete_map={"Perlu Remediasi":"#C00000",
                                  "Cukup":"#FFC000", "Dipahami":"#375623"})
st.plotly_chart(fig2)

# Miskonsepsi yang ditemukan
st.subheader("⚠️ Miskonsepsi Teridentifikasi")
for gap in detected_gaps:
    st.warning(f"**{gap['misconception']}** — Topik: {', '.join(gap['affected_topics'])}")

# Preview Slide Remedial
st.subheader("📑 Slide Remedial yang Disiapkan Agent")
slides = load_remedial_slides()
for slide in slides:
    with st.expander(f"Slide {slide['slide_number']}: {slide['title']}"):
        st.write(slide["content"])

col1, col2 = st.columns(2)
if col1.button("✅ Approve & Gunakan Slide"):
    approve_remedial()
if col2.button("⬇️ Export ke PPTX"):
    pptx_bytes = export_to_pptx(slides)
    st.download_button("Download PPTX", pptx_bytes,
                       file_name=f"remedial_week_{current_week}.pptx")
```

---

## 7. Rincian Tumpukan Teknologi

| Komponen            | Teknologi                                  | Versi    | Peran                                      |
| ------------------- | ------------------------------------------ | -------- | ------------------------------------------ |
| Dashboard           | Streamlit                                  | ≥ 1.35   | UI utama untuk dosen                       |
| Agent Framework     | LangGraph                                  | ≥ 0.2    | Orchestrasi multi-step reasoning           |
| LLM Primary (heavy) | Claude Sonnet / GPT-4o                     | latest   | Analisis esai, RPS generation              |
| LLM Primary (light) | Claude Haiku / GPT-4o-mini                 | latest   | Review materi, slide remedial, analisis PG |
| LLM Fallback        | Ollama (gemma4:e4b, mistral:7b)           | latest   | Offline fallback                           |
| LLM SDK             | `langchain-anthropic` + `langchain-openai` | latest   | Integrasi LangGraph ↔ LLM                  |
| Database            | SQLite (via `sqlite3`)                     | built-in | Persistent memory, state                   |
| PDF Parsing         | PyMuPDF (`fitz`)                           | ≥ 1.23   | Tool T1: ekstraksi teks materi             |
| Web Search          | `duckduckgo-search`                        | ≥ 5.0    | Tool T4: pencarian referensi               |
| Charts              | Plotly Express                             | ≥ 5.0    | Visualisasi performa kelas                 |
| PPTX Export         | `python-pptx`                              | ≥ 0.6    | Export slide remedial                      |
| DOCX Export         | `python-docx`                              | ≥ 1.1    | Export RPS ke DOCX sesuai format institusi  |
| Checkpointing       | `langgraph.checkpoint.sqlite`              | built-in | LangGraph state persistence                |

**`requirements.txt`:**

```
streamlit>=1.35.0
langgraph>=0.2.0
langchain-anthropic>=0.1.0
langchain-openai>=0.1.0
langchain-core>=0.2.0
langchain-community>=0.2.0
PyMuPDF>=1.23.0
duckduckgo-search>=5.0.0
plotly>=5.0.0
python-pptx>=0.6.21
python-docx>=1.1.0
pandas>=2.0.0
ollama>=0.2.0
python-dotenv>=1.0.0
```

---

## 8. Strategi LLM Routing & Cost Optimization

```python
# lib/llm_router.py

import os
from dotenv import load_dotenv

load_dotenv()

HEAVY_MODEL = os.getenv("LLM_HEAVY_MODEL")
LIGHT_MODEL = os.getenv("LLM_LIGHT_MODEL", "claude-haiku-4-20250414")

TASK_MODEL_MAP = {
    # Task berat → model pintar
    "rps_generation":       HEAVY_MODEL,
    "essay_scoring":        HEAVY_MODEL,
    "quiz_generation":      HEAVY_MODEL,
    # Task ringan → model murah
    "material_review":      LIGHT_MODEL,
    "pg_misconception":     LIGHT_MODEL,
    "remedial_generation":  LIGHT_MODEL,
    "reference_search":     LIGHT_MODEL,
    "summary_generation":   LIGHT_MODEL,
}

OLLAMA_MODEL_MAP = {
    "rps_generation":       "gemma4:e4b",
    "essay_scoring":        "gemma4:e4b",
    "quiz_generation":      "gemma4:e4b",
    "material_review":      "gemma4:e4b",
    "pg_misconception":     "gemma4:e4b",
    "remedial_generation":  "gemma4:e4b",
    "reference_search":     "gemma4:e4b",
    "summary_generation":   "gemma4:e4b",
}

def get_llm(task: str, force_local: bool = False):
    if force_local or os.getenv("FORCE_LOCAL_LLM", "").lower() == "true":
        try:
            from langchain_ollama import OllamaLLM
            model = OLLAMA_MODEL_MAP.get(task, "gemma4:e4b")
            return OllamaLLM(model=model)
        except ImportError:
            pass

    # Try OpenRouter
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key and openrouter_key.startswith("sk-or-"):
        try:
            from langchain_openai import ChatOpenAI
            raw_model = TASK_MODEL_MAP.get(task, LIGHT_MODEL)
            # Opsional: Map legacy name ke OpenRouter name jika belum diset di .env
            legacy_or_map = {
                "claude-gemma4:e4b-4-20250514": "anthropic/claude-3.5-sonnet",
                "claude-haiku-4-20250414": "anthropic/claude-3-haiku",
            }
            model = legacy_or_map.get(raw_model, raw_model)
            
            return ChatOpenAI(
                model=model,
                api_key=openrouter_key,
                base_url="https://openrouter.ai/api/v1",
                max_retries=2,
            )
        except ImportError:
            pass

    # Try standard Anthropic/OpenAI fallback di sini...

def call_llm_with_fallback(task: str, prompt: str) -> str:
    try:
        llm = get_llm(task, force_local=False)
        response = llm.invoke(prompt)
        return response.content if hasattr(response, "content") else str(response)
    except Exception as e:
        print(f"[LLM Router] Primary failed ({e}), falling back to Ollama...")
        try:
            llm = get_llm(task, force_local=True)
            response = llm.invoke(prompt)
            return response.content if hasattr(response, "content") else str(response)
        except Exception as e2:
            return f"[ERROR] All LLM backends failed: {e2}"
```

**Estimasi biaya per semester (1 mata kuliah):**

| Task               | Frekuensi | Model  | Est. Cost               |
| ------------------ | --------- | ------ | ----------------------- |
| RPS Generation     | 1×        | Sonnet | ~$0.08                  |
| Material Review    | 14×       | Haiku  | ~$0.01/mk = $0.14       |
| Quiz PG Analysis   | 10×       | Haiku  | ~$0.01/mk = $0.10       |
| Quiz Esai Scoring  | 4×        | Sonnet | ~$0.04/mk = $0.16       |
| Remedial Slide Gen | 14×       | Haiku  | ~$0.01/mk = $0.14       |
| **Total**          |           |        | **≈ $0.62/semester/MK** |

---

## 9. Mapping Kriteria Wajib → Implementasi

| Kriteria Wajib           | Implementasi di Educator Copilot                                                                                                            |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------- |
| **Goal-driven Agent**    | Curriculum Agent: _"Generate RPS 16 minggu selaras CPL"_. Learning Agent: _"Analisis gap kuis → slide remedial"_                            |
| **Multi-step Reasoning** | LangGraph: 7 node (Curriculum) + 8 node (Learning). Setiap node = satu langkah reasoning yang di-log ke `reasoning_steps`                   |
| **Tool Usage ≥ 2**       | T1: `document_reader_tool` (file), T2: `database_tool` (SQLite), T3: `quiz_calculator_tool` (calculator), T4: `web_search_tool` (DuckDuckGo API) |
| **Memory / State**       | Short-term: `Educator CopilotState` TypedDict + LangGraph checkpointer. Long-term: SQLite 8 tabel + `agent_decision_log` (audit trail)      |
| **Output Actionable**    | RPS editable langsung di Streamlit; Dashboard performa dengan highlight per-topik; Slide remedial siap pakai + export PPTX                  |

---

## 10. Deklarasi Penggunaan AI

> Claude AI (Anthropic) digunakan untuk eksplorasi ide, penulisan dokumen PRD ini, dan eksplorasi opsi arsitektur LangGraph. GitHub Copilot digunakan untuk code completion selama development. Seluruh keputusan teknis final, implementasi node LangGraph, desain schema SQLite, dan validasi logika bisnis dilakukan secara mandiri oleh tim. Seluruh output agen AI yang masuk ke platform telah melewati review dosen sebelum digunakan.

---

_PRD ini adalah living document. Update seiring perkembangan implementasi._
