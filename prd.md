# PRODUCT REQUIREMENTS DOCUMENT (PRD) - v3.0

**Project Name:** PANDU (Platform Agen aNalitik dan Desain kurikulUm)
**Status:** Updated - MVP Phase
**Tech Stack Focus:** Next.js, Drizzle ORM, Multi-Agent System
**Last Updated:** April 2026
**Changelog v3.0:** Penambahan database schema lengkap, detail implementasi per-epic, strategi OCR, knowledge graph model, autentikasi, dan LLM fallback strategy.

---

## 1. Ringkasan Eksekutif

PANDU adalah ekosistem manajemen pembelajaran adaptif yang menggunakan *Agentic AI* untuk menjembatani standarisasi kurikulum dengan personalisasi belajar mahasiswa. Sistem ini mengotomatisasi tugas administratif dosen (RPS & materi) dan memberikan evaluasi mendalam terhadap tugas mahasiswa—baik digital maupun fisik—untuk menciptakan siklus perbaikan kurikulum yang berbasis data.

---

## 2. Tujuan Utama

- **Otomatisasi Kurikulum:** Mengubah kebijakan jurusan dan kalender akademik menjadi jadwal pertemuan dan materi yang siap pakai.
- **Evaluasi Subjektif Skala Besar:** Menggunakan OCR (PaddleOCR) dan LLM untuk menilai esai dan tugas tertulis secara objektif sesuai rubrik dosen.
- **Loop Evaluasi Berkelanjutan:** Menilai efektivitas materi berdasarkan performa nyata mahasiswa untuk saran revisi kurikulum di masa depan.

---

## 3. Rincian Tumpukan Teknologi

| Komponen | Pilihan | Alasan |
|---|---|---|
| **Framework Utama** | Next.js (App Router) | Performa dashboard, SSR, API Routes built-in |
| **Database** | PostgreSQL + Drizzle ORM | Integritas data akademik kompleks, kueri analitik |
| **LLM Primary** | Claude (claude-sonnet-4-20250514) / GPT-4o | Reasoning kompleks untuk evaluasi dan rekomendasi |
| **LLM Fallback** | Ollama (model lokal: `llama3.2`, `gemma4-e4b`) | Ketersediaan offline, zero API cost |
| **OCR Engine** | PaddleOCR | Open-source, akurasi tinggi untuk tulisan tangan & dokumen scan |
| **Auth** | NextAuth.js (Auth.js v5) | Integrasi Next.js native, support multiple providers |
| **File Storage** | Local filesystem / S3-compatible (MinIO untuk self-host) | Penyimpanan dokumen upload dosen & mahasiswa |
| **Orkestrasi** | Custom agent loop di Next.js API Routes | Tidak menggunakan n8n; orkestrasi langsung via server-side code |
| **Knowledge Graph** | JSON-based graph di PostgreSQL (JSONB) | Fleksibel, query-able dengan SQL, tanpa dependency graph DB |

> **Catatan penting:** Sistem **tidak menggunakan n8n**. Seluruh orkestrasi alur kerja agen diimplementasikan langsung sebagai server-side logic di Next.js API Routes (`/app/api/agents/`), menggunakan pattern agent loop dengan LangChain.js atau custom ReAct implementation.

---

## 4. Arsitektur Sistem

### 4.1 Diagram Alur Tingkat Tinggi

```
[Dosen]                    [Mahasiswa]
   |                            |
   v                            v
[Next.js Frontend — App Router]
   |
   v
[Next.js API Routes — Agent Orchestration Layer]
   |          |           |           |
   v          v           v           v
[Curriculum  [Lecturer   [Student    [Curriculum
 Architect]   Assistant]  Success]    Evaluator]
   |          |           |           |
   +----------+-----------+-----------+
                          |
                          v
              [PostgreSQL via Drizzle ORM]
                          |
                 +--------+--------+
                 |                 |
         [LLM Router]        [PaddleOCR]
         /         \
[Primary LLM]  [Ollama Fallback]
(Cloud API)    (Local Model)
```

### 4.2 LLM Routing & Fallback Strategy

Setiap pemanggilan LLM melewati sebuah **LLM Router** yang memutuskan apakah menggunakan primary LLM (cloud API) atau fallback ke model lokal via Ollama.

**Kondisi fallback ke Ollama:**
1. Primary API mengembalikan HTTP 429 (rate limit) atau 5xx (server error)
2. Waktu respons primary API > 30 detik (timeout)
3. Variabel environment `FORCE_LOCAL_LLM=true` diset (untuk development offline)

**Model Ollama yang digunakan:**

| Task | Model Lokal | Alasan |
|---|---|---|
| RPS generation, reasoning kompleks | `llama3.2:3b` | Cukup untuk structured output |
| Evaluasi esai pendek | `mistral:7b` | Lebih akurat untuk bahasa Indonesia |
| Knowledge gap analysis | `llama3.2:3b` | Task sederhana, cepat |
| Embedding (RAG) | `nomic-embed-text` | Ringan, tersedia di Ollama |

```typescript
// lib/llm-router.ts
export async function callLLM(prompt: string, task: LLMTask): Promise<string> {
  try {
    return await callPrimaryLLM(prompt, task);
  } catch (error) {
    if (isRetryableError(error)) {
      console.warn(`Primary LLM failed for task ${task}, falling back to Ollama`);
      return await callOllamaFallback(prompt, task);
    }
    throw error;
  }
}
```

### 4.3 Autentikasi & Multi-Tenancy

#### 4.3.1 Strategi Autentikasi

Menggunakan **NextAuth.js (Auth.js v5)** dengan credential-based login sederhana. Tidak mengimplementasikan SSO atau OAuth eksternal pada MVP.

```typescript
// Tiga role yang dikenali sistem
type UserRole = 'admin' | 'dosen' | 'mahasiswa';
```

#### 4.3.2 Definisi Role & Hak Akses

| Fitur | Admin | Dosen | Mahasiswa |
|---|---|---|---|
| Kelola user & program studi | ✅ | ❌ | ❌ |
| Upload dokumen CPL | ✅ | ✅ | ❌ |
| Generate & edit RPS | ❌ | ✅ | ❌ |
| Publish materi & soal | ❌ | ✅ | ❌ |
| Submit tugas | ❌ | ❌ | ✅ |
| Lihat nilai & rekomendasi diri sendiri | ❌ | ❌ | ✅ |
| Lihat analytics semua mahasiswa (kelas sendiri) | ❌ | ✅ | ❌ |
| Lihat analytics seluruh program studi | ✅ | ❌ | ❌ |
| Override nilai AI | ❌ | ✅ | ❌ |
| Lihat curriculum suggestions | ✅ | ✅ | ❌ |

#### 4.3.3 Multi-Tenancy (Simplified)

MVP menggunakan **single-tenant** deployment — satu instance PANDU per institusi. Isolasi data dilakukan melalui kolom `institution_id` di tabel-tabel utama. Tidak ada isolasi schema-per-tenant (schema Postgres terpisah) pada tahap MVP.

---

## 5. Arsitektur Multi-Agen & Kebutuhan Fungsional

### Epic 1: Curriculum Architect Agent (Fase Strategis)

#### FR-1.1 — Policy & Calendar Ingestion (RAG)

**Deskripsi:** Menggunakan teknik RAG (*Retrieval-Augmented Generation*) untuk mengekstrak poin penting dari dokumen kebijakan CPL dan jadwal akademik.

**Format Dokumen Input yang Didukung:**

| Format | Handling |
|---|---|
| PDF terstruktur (teks selectable) | Ekstraksi langsung via `pdf-parse` |
| PDF scan / gambar | PaddleOCR → teks → RAG |
| DOCX / DOC | `mammoth.js` → teks → RAG |
| Gambar (JPG/PNG) | PaddleOCR → teks → RAG |

**Proses Ingestion:**
1. Upload file → simpan ke storage, catat path di tabel `policy_documents`
2. Jalankan parser sesuai format → hasilkan plain text
3. Chunking: split per 500 token dengan overlap 50 token
4. Generate embedding tiap chunk via `nomic-embed-text` (Ollama) → simpan ke tabel `policy_chunks`
5. Saat agent butuh informasi kebijakan → vector similarity search di `policy_chunks`

**Schema Output Hasil Ekstraksi (disimpan ke `cpl_policies`):**
```typescript
{
  policyId: string,
  courseCode: string,
  cplCode: string,          // e.g. "CPL-1", "CPL-2"
  description: string,
  bloomLevel: BloomLevel,   // 'C1'|'C2'|'C3'|'C4'|'C5'|'C6'
  extractedFrom: string,    // document_id
  confidence: number        // 0.0 - 1.0
}
```

---

#### FR-1.2 — Intelligent RPS Builder

**Deskripsi:** Menghasilkan draf RPS (16 pertemuan) yang membagi beban materi secara proporsional sesuai CPL yang telah diekstrak.

**Sub-task & Detail Implementasi:**

##### 1. State Machine RPS

```
DRAFT → PENDING_REVIEW → REVISION_REQUESTED → PENDING_REVIEW → APPROVED → PUBLISHED
                                                                         ↓
                                                                    ARCHIVED
```

| Status | Deskripsi | Aktor |
|---|---|---|
| `draft` | Output awal dari agen, belum dilihat dosen | System |
| `pending_review` | Menunggu validasi dosen | Dosen |
| `revision_requested` | Dosen meminta perubahan | Dosen |
| `approved` | Dosen menyetujui | Dosen |
| `published` | Visible ke mahasiswa | Dosen |
| `archived` | Semester selesai | System |

##### 2. Logika Distribusi Beban Materi

Agen menggunakan heuristik berikut untuk membagi 16 pertemuan:
- **Pertemuan 1:** Orientasi & kontrak kuliah (bobot rendah)
- **Pertemuan 2–13:** Materi inti, dibagi merata sesuai jumlah CPL
- **Pertemuan 14–15:** Review & persiapan UAS
- **Pertemuan 16:** UAS / presentasi final

Kuantifikasi beban materi per-pertemuan menggunakan estimasi *cognitive load* dari Bloom level:
- C1-C2 (ingat, pahami): 1 topik/pertemuan
- C3-C4 (aplikasi, analisis): 0.75 topik/pertemuan (lebih banyak waktu)
- C5-C6 (evaluasi, cipta): 0.5 topik/pertemuan

##### 3. Iterasi Agen & Fallback

- **Max iterasi reasoning:** 5 putaran ReAct loop
- **Timeout per iterasi:** 45 detik
- **Fallback:** Jika setelah 5 iterasi output belum valid (gagal validasi schema), sistem menggunakan **template RPS statis** berdasarkan kode mata kuliah. Template disimpan di tabel `rps_templates` dan dapat dikustomisasi admin.

---

#### FR-1.3 — Academic Scheduling

**Deskripsi:** Menentukan tanggal pasti pertemuan, tenggat tugas, dan jadwal ujian berdasarkan kalender akademik yang diunggah.

**Aturan Penjadwalan:**
- Otomatis skip hari libur nasional (sumber: API kalender nasional atau JSON hardcoded per tahun)
- Jika pertemuan jatuh di hari libur → geser ke pertemuan berikutnya yang tersedia (tidak dilewati)
- UTS dijadwalkan di antara pertemuan ke-8 dan ke-9
- Jeda UTS minimal 1 minggu sebelum dan sesudah

---

### Epic 2: Lecturer Assistant Agent (Fase Operasional)

#### FR-2.1 — Material & Slide Generator

**Deskripsi:** Membuat kerangka modul dan slide untuk setiap pertemuan.

**Format Output:**

| Format | Keterangan | Library |
|---|---|---|
| JSON (primary) | Disimpan di DB, dirender oleh frontend renderer | Native |
| PPTX (export) | Export on-demand via tombol "Unduh PPTX" | `pptxgenjs` |
| Markdown | Alternatif untuk tampilan preview teks | Native |

**Struktur JSON Materi (disimpan di kolom `content` tabel `materials`):**
```json
{
  "title": "Pengantar Machine Learning",
  "week": 3,
  "learningObjectives": ["Mendefinisikan ML", "Membedakan supervised vs unsupervised"],
  "sections": [
    {
      "type": "explanation",
      "title": "Apa itu Machine Learning?",
      "body": "..."
    },
    {
      "type": "code_template",
      "language": "python",
      "title": "Template EDA Dasar",
      "code": "import pandas as pd\n# Load dataset\ndf = pd.read_csv('...')\ndf.describe()"
    },
    {
      "type": "diagram",
      "title": "Decision Tree Schema",
      "description": "..."
    }
  ],
  "references": ["..."],
  "estimatedDuration": 100
}
```

> Untuk mata kuliah teknis, `sections` dapat berisi `type: "code_template"` berisi templat EDA atau skema Decision Tree sebagai panduan praktikum.

---

#### FR-2.2 — Automated Assessment Creator

**Deskripsi:** Menghasilkan bank soal (pilihan ganda dan isian) yang selaras dengan Capaian Pembelajaran (CP) tiap minggu.

**Schema Item Soal (`assessment_items`):**

```typescript
type QuestionType = 'multiple_choice' | 'short_answer' | 'essay';
type BloomLevel = 'C1' | 'C2' | 'C3' | 'C4' | 'C5' | 'C6';

interface AssessmentItem {
  itemId: string;
  courseId: string;
  weekNumber: number;
  cplAlignment: string[];      // e.g. ["CPL-1", "CPL-3"]
  bloomLevel: BloomLevel;
  questionType: QuestionType;
  stem: string;                // Teks pertanyaan utama

  // Khusus multiple_choice:
  optionA?: string;
  optionB?: string;
  optionC?: string;
  optionD?: string;
  answerKey?: 'A' | 'B' | 'C' | 'D';
  explanation?: string;        // Penjelasan jawaban benar

  // Khusus essay/short_answer:
  rubricId?: string;           // FK ke tabel rubrics
  modelAnswer?: string;

  difficultyLevel: 'easy' | 'medium' | 'hard';
  contentHash: string;         // SHA-256 dari stem untuk de-duplikasi
  status: 'draft' | 'approved' | 'archived';
  createdAt: Date;
}
```

**De-duplikasi:** Sebelum menyimpan soal baru, sistem membandingkan `contentHash` (SHA-256 dari `stem`) dengan soal yang sudah ada di kelas/program studi yang sama. Jika duplikat ditemukan, agen diminta untuk regenerasi.

---

#### FR-2.3 — Human-in-the-Loop Validation

**Deskripsi:** Menyediakan antarmuka bagi dosen untuk mengedit dan menyetujui setiap konten sebelum dipublikasikan ke mahasiswa.

**Perilaku Sistem:**
- Validasi bersifat **blocking**: konten dengan status `draft` atau `pending_review` **tidak dapat diakses mahasiswa**
- Notifikasi dosen via in-app notification (badge di navbar) + email opsional (konfigurasi per-user)
- Setiap perubahan yang dilakukan dosen dicatat di tabel `content_audit_log` (siapa, kapan, field apa yang diubah, nilai lama vs baru)

---

### Epic 3: Student Success Agent (Fase Personalisasi & Evaluasi)

#### FR-3.1 — Document OCR Evaluator

**Deskripsi:** Menerima unggahan tugas berupa teks digital atau foto tulisan tangan, mengekstrak teks via PaddleOCR, lalu menilai berdasarkan rubrik dosen.

**Pipeline Lengkap:**

```
[Upload Mahasiswa]
       |
       v
[Format Detection]
   PDF teks?  →  pdf-parse → teks langsung
   PDF scan? ──┐
   Foto JPG?   ├→ PaddleOCR → teks mentah
   DOCX?    ──┘
                      |
                      v
            [OCR Confidence Check]
            confidence ≥ 0.75? → lanjut ke LLM Scoring
            confidence < 0.75? → flag ke Manual Review Queue
                      |
                      v
            [LLM Scoring Agent]
            Input: teks + rubrik dari tabel rubrics
            Output: skor per-kriteria + feedback tertulis
                      |
                      v
            [Simpan ke tabel scores]
                      |
                      v
            [Notifikasi Dosen untuk Validasi]
```

**Threshold OCR:** Minimum confidence score **0.75** (skala 0.0–1.0). Submission di bawah threshold masuk ke antrian `manual_review` dengan flag `ocr_low_confidence: true`.

**Schema Rubrik (`rubrics`):**

```typescript
interface Rubric {
  rubricId: string;
  courseId: string;
  assessmentType: string;      // e.g. "Esai Analisis", "Studi Kasus"
  totalWeight: number;         // Harus sum ke 100
  createdByDosen: string;      // FK users.userId
  sourceType: 'platform_form' | 'uploaded_pdf';
  sourcePath?: string;         // Path PDF jika sourceType = uploaded_pdf
  criteria: RubricCriterion[];
}

interface RubricCriterion {
  criterionId: string;
  name: string;                // e.g. "Kedalaman Analisis"
  weight: number;              // Bobot dalam persen (misal: 30)
  descriptors: {
    level: 1 | 2 | 3 | 4;
    label: string;             // "Kurang" | "Cukup" | "Baik" | "Sangat Baik"
    description: string;       // Deskripsi kriteria per level
    scoreRange: [number, number]; // e.g. [0, 24]
  }[];
}
```

**Input Rubrik oleh Dosen:**
- **Via form platform:** Dosen mengisi tabel kriteria langsung di UI (direkomendasikan untuk konsistensi)
- **Via upload PDF:** Dosen upload PDF rubrik → PaddleOCR ekstrak → agen parsing ke struktur `RubricCriterion[]` → dosen verifikasi hasil parsing

---

#### FR-3.2 — Knowledge Gap Analysis

**Deskripsi:** Mengidentifikasi topik mana yang belum dikuasai mahasiswa secara individu menggunakan model Knowledge Graph.

**Model Pengetahuan — Knowledge Graph:**

Knowledge Graph direpresentasikan sebagai directed acyclic graph (DAG) yang disimpan dalam kolom JSONB PostgreSQL. Setiap node adalah satu Knowledge Component (KC), setiap edge adalah relasi prerequisite.

```typescript
interface KnowledgeGraph {
  graphId: string;
  courseId: string;
  nodes: KCNode[];
  edges: KCEdge[];
}

interface KCNode {
  kcId: string;
  name: string;                // e.g. "Binary Search Tree"
  weekNumber: number;          // Diajarkan di minggu ke-berapa
  bloomLevel: BloomLevel;
  cplAlignment: string[];
}

interface KCEdge {
  from: string;                // kcId prerequisite
  to: string;                  // kcId yang membutuhkan prerequisite
  strength: 'required' | 'recommended';
}
```

**Threshold Penguasaan per-KC:**

| Skor | Kategori | Aksi |
|---|---|---|
| < 40% | **Review** | Harus mempelajari ulang dari dasar |
| 40% – 69% | **Improve** | Perlu pendalaman dan latihan tambahan |
| ≥ 70% | **Mastered** | Siap maju ke KC berikutnya |

Agen melakukan traversal DAG dari node yang belum dikuasai untuk mengidentifikasi **root cause gap** (KC mana yang, jika diperbaiki, akan membuka penguasaan KC-KC downstream).

---

#### FR-3.3 — Adaptive Recommendation

**Deskripsi:** Memberikan "Materi Pengayaan" atau "Latihan Remedial" otomatis di dashboard mahasiswa jika skor pada topik tertentu rendah.

**Sumber Konten Rekomendasi:**
1. **Internal:** Materi yang telah dibuat dosen di platform (tabel `materials`) — prioritas utama
2. **Curated eksternal:** URL resource yang dikurasi secara manual oleh dosen/admin, disimpan di tabel `curated_resources` (bukan auto-search) — mencegah dead-link
3. **AI-generated:** LLM menghasilkan ringkasan atau latihan soal singkat on-demand untuk gap yang sangat spesifik

**Mekanisme Pengecekan Dead-Link:** Untuk setiap URL di `curated_resources`, background job cron (setiap 24 jam) melakukan HTTP HEAD request. URL yang mengembalikan 4xx/5xx diset `is_active: false` dan tidak muncul di rekomendasi.

---

### Epic 4: Curriculum Evaluator Agent (Fase Analitik)

#### FR-4.1 — Course Performance Analytics

**Deskripsi:** Menyediakan visualisasi distribusi nilai dan tingkat kesulitan soal secara otomatis.

**Akses berdasarkan Role:**
- **Dosen:** Hanya bisa melihat analytics kelas yang diampu sendiri
- **Admin:** Bisa melihat analytics seluruh program studi, agregat lintas-kelas

**Metrik yang Ditampilkan:**
- Distribusi nilai per minggu (histogram)
- Rata-rata skor per KC (heatmap berbasis knowledge graph)
- Tingkat kesulitan soal (% mahasiswa gagal per soal)
- Tren perkembangan kelas dari minggu ke minggu

---

#### FR-4.2 — Curriculum Iteration Suggestion

**Deskripsi:** Memberikan rekomendasi perbaikan RPS berdasarkan performa nyata mahasiswa. Contoh: *"Materi Minggu ke-5 terlalu padat, 60% mahasiswa gagal di esai topik tersebut. Disarankan membagi materi menjadi dua pertemuan"*.

**Pipeline Triggering:**
Agen dipicu secara otomatis ketika salah satu kondisi berikut terpenuhi:
1. Rata-rata skor kelas pada suatu minggu < 60%
2. Lebih dari 40% mahasiswa memiliki gap di KC yang sama
3. Manual trigger oleh dosen ("Analisis minggu ini")

**Metric yang Digunakan sebagai Trigger:**

```typescript
type TriggerMetric =
  | 'class_avg_below_60'
  | 'gap_concentration_above_40pct'
  | 'fail_rate_above_50pct'
  | 'manual_trigger';
```

**Schema Tabel `curriculum_suggestions`:**

```typescript
interface CurriculumSuggestion {
  suggestionId: string;          // UUID
  rpsId: string;                 // FK ke rps.rpsId
  weekNumber: number;            // Minggu ke berapa yang dianalisis
  triggerMetric: TriggerMetric;  // Kondisi yang memicu analisis
  triggerValue: number;          // Nilai aktual yang memicu (e.g. 0.58 untuk avg 58%)
  suggestionText: string;        // Teks saran dari agen (dalam Bahasa Indonesia)
  suggestedAction: 'split_week' | 'add_remedial' | 'reorder_topic' | 'reduce_scope' | 'other';
  status: 'pending' | 'accepted' | 'rejected';
  dosenNote?: string;            // Catatan dosen saat accept/reject
  createdAt: Date;
  resolvedAt?: Date;
}
```

**Tracking Adoption Rate:**
Admin dan dosen dapat melihat statistik aggregate:
- Berapa banyak saran yang diterima vs ditolak
- Apakah performa mahasiswa meningkat setelah saran diterima (dibandingkan semester sebelumnya)

---

## 6. Schema Database Lengkap (Drizzle ORM)

### 6.1 Diagram Relasi Entitas (ERD Ringkas)

```
institutions ──< users ──< enrollments >── courses
                  |                           |
               (dosen)                   rps ─┤
                  |                       |   |
              rubrics              rps_sessions
                  |                           |
         assessment_items            materials
                  |
            submissions
                  |
           +------+------+
           |             |
         scores   manual_review
           |
    curriculum_suggestions
           |
       cpl_policies ──< policy_chunks
       knowledge_graphs
       curated_resources
       content_audit_log
```

### 6.2 Schema Drizzle Lengkap

```typescript
// schema/index.ts
import { pgTable, uuid, text, integer, real, boolean,
         timestamp, jsonb, pgEnum, varchar, index } from 'drizzle-orm/pg-core';

// ─── ENUMS ──────────────────────────────────────────────
export const userRoleEnum = pgEnum('user_role', ['admin', 'dosen', 'mahasiswa']);
export const rpsStatusEnum = pgEnum('rps_status',
  ['draft', 'pending_review', 'revision_requested', 'approved', 'published', 'archived']);
export const bloomLevelEnum = pgEnum('bloom_level', ['C1','C2','C3','C4','C5','C6']);
export const questionTypeEnum = pgEnum('question_type',
  ['multiple_choice', 'short_answer', 'essay']);
export const difficultyEnum = pgEnum('difficulty', ['easy', 'medium', 'hard']);
export const submissionStatusEnum = pgEnum('submission_status',
  ['uploaded', 'ocr_processing', 'ocr_failed', 'scoring', 'scored', 'manual_review', 'finalized']);
export const suggestionStatusEnum = pgEnum('suggestion_status',
  ['pending', 'accepted', 'rejected']);
export const triggerMetricEnum = pgEnum('trigger_metric',
  ['class_avg_below_60', 'gap_concentration_above_40pct', 'fail_rate_above_50pct', 'manual_trigger']);
export const suggestedActionEnum = pgEnum('suggested_action',
  ['split_week', 'add_remedial', 'reorder_topic', 'reduce_scope', 'other']);

// ─── INSTITUTIONS ────────────────────────────────────────
export const institutions = pgTable('institutions', {
  institutionId: uuid('institution_id').primaryKey().defaultRandom(),
  name: text('name').notNull(),
  code: varchar('code', { length: 20 }).notNull().unique(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
});

// ─── USERS ───────────────────────────────────────────────
export const users = pgTable('users', {
  userId: uuid('user_id').primaryKey().defaultRandom(),
  institutionId: uuid('institution_id').notNull().references(() => institutions.institutionId),
  name: text('name').notNull(),
  email: text('email').notNull().unique(),
  passwordHash: text('password_hash').notNull(),
  role: userRoleEnum('role').notNull(),
  isActive: boolean('is_active').default(true).notNull(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
});

// ─── COURSES ─────────────────────────────────────────────
export const courses = pgTable('courses', {
  courseId: uuid('course_id').primaryKey().defaultRandom(),
  institutionId: uuid('institution_id').notNull().references(() => institutions.institutionId),
  dosenId: uuid('dosen_id').notNull().references(() => users.userId),
  code: varchar('code', { length: 20 }).notNull(),
  name: text('name').notNull(),
  credits: integer('credits').notNull(),
  semester: varchar('semester', { length: 20 }).notNull(), // e.g. "2025/2026-Ganjil"
  isActive: boolean('is_active').default(true).notNull(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
});

// ─── ENROLLMENTS ─────────────────────────────────────────
export const enrollments = pgTable('enrollments', {
  enrollmentId: uuid('enrollment_id').primaryKey().defaultRandom(),
  courseId: uuid('course_id').notNull().references(() => courses.courseId),
  mahasiswaId: uuid('mahasiswa_id').notNull().references(() => users.userId),
  enrolledAt: timestamp('enrolled_at').defaultNow().notNull(),
});

// ─── CPL POLICIES ────────────────────────────────────────
export const cplPolicies = pgTable('cpl_policies', {
  policyId: uuid('policy_id').primaryKey().defaultRandom(),
  courseId: uuid('course_id').notNull().references(() => courses.courseId),
  cplCode: varchar('cpl_code', { length: 20 }).notNull(), // e.g. "CPL-1"
  description: text('description').notNull(),
  bloomLevel: bloomLevelEnum('bloom_level').notNull(),
  extractedFrom: uuid('extracted_from'),   // FK policy_documents.documentId
  confidence: real('confidence'),           // 0.0 – 1.0
  createdAt: timestamp('created_at').defaultNow().notNull(),
});

// ─── POLICY DOCUMENTS (for RAG) ──────────────────────────
export const policyDocuments = pgTable('policy_documents', {
  documentId: uuid('document_id').primaryKey().defaultRandom(),
  institutionId: uuid('institution_id').notNull().references(() => institutions.institutionId),
  filename: text('filename').notNull(),
  filePath: text('file_path').notNull(),
  fileType: varchar('file_type', { length: 10 }).notNull(), // 'pdf' | 'docx' | 'image'
  uploadedBy: uuid('uploaded_by').notNull().references(() => users.userId),
  uploadedAt: timestamp('uploaded_at').defaultNow().notNull(),
});

// ─── POLICY CHUNKS (RAG embeddings) ──────────────────────
export const policyChunks = pgTable('policy_chunks', {
  chunkId: uuid('chunk_id').primaryKey().defaultRandom(),
  documentId: uuid('document_id').notNull().references(() => policyDocuments.documentId),
  chunkIndex: integer('chunk_index').notNull(),
  content: text('content').notNull(),
  embedding: jsonb('embedding'),   // float[] — use pgvector extension if available
  createdAt: timestamp('created_at').defaultNow().notNull(),
});

// ─── RPS ─────────────────────────────────────────────────
export const rps = pgTable('rps', {
  rpsId: uuid('rps_id').primaryKey().defaultRandom(),
  courseId: uuid('course_id').notNull().references(() => courses.courseId),
  version: integer('version').default(1).notNull(),
  status: rpsStatusEnum('status').default('draft').notNull(),
  dosenNote: text('dosen_note'),
  agentIterations: integer('agent_iterations').default(0).notNull(), // jumlah iterasi ReAct
  usedFallbackTemplate: boolean('used_fallback_template').default(false).notNull(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
  publishedAt: timestamp('published_at'),
});

// ─── RPS SESSIONS (16 pertemuan per RPS) ─────────────────
export const rpsSessions = pgTable('rps_sessions', {
  sessionId: uuid('session_id').primaryKey().defaultRandom(),
  rpsId: uuid('rps_id').notNull().references(() => rps.rpsId),
  weekNumber: integer('week_number').notNull(),         // 1–16
  scheduledDate: timestamp('scheduled_date'),
  topic: text('topic').notNull(),
  subTopics: text('sub_topics').array(),
  learningActivities: text('learning_activities'),
  cplAlignments: text('cpl_alignments').array(),       // e.g. ["CPL-1", "CPL-2"]
  assessmentMethod: text('assessment_method'),
  references: text('references').array(),
  estimatedCognitiveLoad: real('estimated_cognitive_load'), // 0.5 – 1.0
  createdAt: timestamp('created_at').defaultNow().notNull(),
});

// ─── RPS TEMPLATES (fallback) ─────────────────────────────
export const rpsTemplates = pgTable('rps_templates', {
  templateId: uuid('template_id').primaryKey().defaultRandom(),
  institutionId: uuid('institution_id').notNull().references(() => institutions.institutionId),
  courseCode: varchar('course_code', { length: 20 }),
  name: text('name').notNull(),
  templateData: jsonb('template_data').notNull(), // full 16-week template as JSON
  createdAt: timestamp('created_at').defaultNow().notNull(),
});

// ─── MATERIALS ───────────────────────────────────────────
export const materials = pgTable('materials', {
  materialId: uuid('material_id').primaryKey().defaultRandom(),
  sessionId: uuid('session_id').notNull().references(() => rpsSessions.sessionId),
  courseId: uuid('course_id').notNull().references(() => courses.courseId),
  title: text('title').notNull(),
  content: jsonb('content').notNull(),       // Structured JSON (sections, code templates, etc.)
  contentMarkdown: text('content_markdown'), // Rendered markdown version
  pptxPath: text('pptx_path'),              // Path PPTX jika sudah di-export
  status: rpsStatusEnum('status').default('draft').notNull(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
});

// ─── RUBRICS ─────────────────────────────────────────────
export const rubrics = pgTable('rubrics', {
  rubricId: uuid('rubric_id').primaryKey().defaultRandom(),
  courseId: uuid('course_id').notNull().references(() => courses.courseId),
  assessmentType: text('assessment_type').notNull(),
  totalWeight: integer('total_weight').notNull(),       // Harus = 100
  createdByDosen: uuid('created_by_dosen').notNull().references(() => users.userId),
  sourceType: varchar('source_type', { length: 20 }).notNull(), // 'platform_form' | 'uploaded_pdf'
  sourcePath: text('source_path'),
  criteria: jsonb('criteria').notNull(),               // RubricCriterion[]
  createdAt: timestamp('created_at').defaultNow().notNull(),
});

// ─── ASSESSMENT ITEMS ────────────────────────────────────
export const assessmentItems = pgTable('assessment_items', {
  itemId: uuid('item_id').primaryKey().defaultRandom(),
  courseId: uuid('course_id').notNull().references(() => courses.courseId),
  weekNumber: integer('week_number').notNull(),
  cplAlignment: text('cpl_alignment').array().notNull(),
  bloomLevel: bloomLevelEnum('bloom_level').notNull(),
  questionType: questionTypeEnum('question_type').notNull(),
  stem: text('stem').notNull(),
  optionA: text('option_a'),
  optionB: text('option_b'),
  optionC: text('option_c'),
  optionD: text('option_d'),
  answerKey: varchar('answer_key', { length: 1 }),     // 'A'|'B'|'C'|'D'
  explanation: text('explanation'),
  rubricId: uuid('rubric_id').references(() => rubrics.rubricId),
  modelAnswer: text('model_answer'),
  difficultyLevel: difficultyEnum('difficulty_level').notNull(),
  contentHash: varchar('content_hash', { length: 64 }).notNull(), // SHA-256 untuk de-dup
  status: varchar('status', { length: 20 }).default('draft').notNull(),
  createdAt: timestamp('created_at').defaultNow().notNull(),
}, (table) => ({
  contentHashIdx: index('assessment_items_content_hash_idx').on(table.contentHash),
}));

// ─── SUBMISSIONS ─────────────────────────────────────────
export const submissions = pgTable('submissions', {
  submissionId: uuid('submission_id').primaryKey().defaultRandom(),
  courseId: uuid('course_id').notNull().references(() => courses.courseId),
  mahasiswaId: uuid('mahasiswa_id').notNull().references(() => users.userId),
  weekNumber: integer('week_number').notNull(),
  itemId: uuid('item_id').references(() => assessmentItems.itemId),
  originalFilePath: text('original_file_path').notNull(),
  fileType: varchar('file_type', { length: 10 }).notNull(),
  ocrText: text('ocr_text'),
  ocrConfidence: real('ocr_confidence'),               // 0.0 – 1.0
  status: submissionStatusEnum('status').default('uploaded').notNull(),
  submittedAt: timestamp('submitted_at').defaultNow().notNull(),
});

// ─── SCORES ──────────────────────────────────────────────
export const scores = pgTable('scores', {
  scoreId: uuid('score_id').primaryKey().defaultRandom(),
  submissionId: uuid('submission_id').notNull().references(() => submissions.submissionId),
  rubricId: uuid('rubric_id').notNull().references(() => rubrics.rubricId),
  criteriaScores: jsonb('criteria_scores').notNull(), // { criterionId: score }[]
  totalScore: real('total_score').notNull(),
  aiFeedback: text('ai_feedback').notNull(),
  isOverridden: boolean('is_overridden').default(false).notNull(),
  overriddenBy: uuid('overridden_by').references(() => users.userId),
  overrideNote: text('override_note'),
  finalScore: real('final_score').notNull(),
  scoredAt: timestamp('scored_at').defaultNow().notNull(),
});

// ─── MANUAL REVIEW QUEUE ─────────────────────────────────
export const manualReviews = pgTable('manual_reviews', {
  reviewId: uuid('review_id').primaryKey().defaultRandom(),
  submissionId: uuid('submission_id').notNull().references(() => submissions.submissionId),
  reason: text('reason').notNull(),                   // e.g. "ocr_low_confidence"
  assignedTo: uuid('assigned_to').references(() => users.userId),
  resolvedAt: timestamp('resolved_at'),
  resolution: text('resolution'),
  createdAt: timestamp('created_at').defaultNow().notNull(),
});

// ─── KNOWLEDGE GRAPHS ────────────────────────────────────
export const knowledgeGraphs = pgTable('knowledge_graphs', {
  graphId: uuid('graph_id').primaryKey().defaultRandom(),
  courseId: uuid('course_id').notNull().references(() => courses.courseId).unique(),
  graphData: jsonb('graph_data').notNull(),           // { nodes: KCNode[], edges: KCEdge[] }
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
});

// ─── STUDENT KC MASTERY ──────────────────────────────────
export const studentMastery = pgTable('student_mastery', {
  masteryId: uuid('mastery_id').primaryKey().defaultRandom(),
  mahasiswaId: uuid('mahasiswa_id').notNull().references(() => users.userId),
  courseId: uuid('course_id').notNull().references(() => courses.courseId),
  kcId: varchar('kc_id', { length: 50 }).notNull(),
  masteryScore: real('mastery_score').notNull(),       // 0.0 – 1.0
  category: varchar('category', { length: 20 }).notNull(), // 'review'|'improve'|'mastered'
  updatedAt: timestamp('updated_at').defaultNow().notNull(),
});

// ─── CURATED RESOURCES ───────────────────────────────────
export const curatedResources = pgTable('curated_resources', {
  resourceId: uuid('resource_id').primaryKey().defaultRandom(),
  courseId: uuid('course_id').references(() => courses.courseId),
  kcId: varchar('kc_id', { length: 50 }),
  title: text('title').notNull(),
  url: text('url').notNull(),
  resourceType: varchar('resource_type', { length: 20 }).notNull(), // 'video'|'article'|'exercise'
  addedBy: uuid('added_by').notNull().references(() => users.userId),
  isActive: boolean('is_active').default(true).notNull(),
  lastCheckedAt: timestamp('last_checked_at'),
  createdAt: timestamp('created_at').defaultNow().notNull(),
});

// ─── CURRICULUM SUGGESTIONS ──────────────────────────────
export const curriculumSuggestions = pgTable('curriculum_suggestions', {
  suggestionId: uuid('suggestion_id').primaryKey().defaultRandom(),
  rpsId: uuid('rps_id').notNull().references(() => rps.rpsId),
  weekNumber: integer('week_number').notNull(),
  triggerMetric: triggerMetricEnum('trigger_metric').notNull(),
  triggerValue: real('trigger_value').notNull(),
  suggestionText: text('suggestion_text').notNull(),
  suggestedAction: suggestedActionEnum('suggested_action').notNull(),
  status: suggestionStatusEnum('status').default('pending').notNull(),
  dosenNote: text('dosen_note'),
  createdAt: timestamp('created_at').defaultNow().notNull(),
  resolvedAt: timestamp('resolved_at'),
});

// ─── CONTENT AUDIT LOG ───────────────────────────────────
export const contentAuditLog = pgTable('content_audit_log', {
  logId: uuid('log_id').primaryKey().defaultRandom(),
  entityType: varchar('entity_type', { length: 30 }).notNull(), // 'rps'|'material'|'assessment_item'
  entityId: uuid('entity_id').notNull(),
  changedBy: uuid('changed_by').notNull().references(() => users.userId),
  fieldName: text('field_name').notNull(),
  oldValue: text('old_value'),
  newValue: text('new_value'),
  changedAt: timestamp('changed_at').defaultNow().notNull(),
});
```

---

## 7. Alur Kerja (Workflow) Evaluasi Tugas Subjektif

1. **Upload:** Mahasiswa mengunggah foto esai atau dokumen digital ke portal PANDU.
2. **Format Detection:** Sistem mendeteksi format file dan memilih parser yang sesuai (teks langsung, PaddleOCR, atau `mammoth.js`).
3. **OCR Confidence Check:** Jika hasil OCR memiliki confidence < 0.75 → masuk ke `manual_reviews`. Jika ≥ 0.75 → lanjut ke scoring.
4. **Agent Scoring:** *Student Success Agent* membaca teks tersebut, membandingkannya dengan rubrik dari tabel `rubrics`, dan memberikan skor beserta umpan balik tertulis. LLM yang digunakan melalui router (primary cloud API atau Ollama fallback).
5. **Validation:** Dosen menerima in-app notification, dapat melakukan *override* nilai AI beserta catatan.
6. **Feedback Loop:** Data skor masuk ke *Curriculum Evaluator Agent* — jika rata-rata kelas < 60%, agen otomatis menghasilkan entri baru di `curriculum_suggestions`.

---

## 8. Rubrik Evaluasi Tugas Besar

| Aspek | Bobot | Kriteria |
|---|---|---|
| Pemahaman masalah | 15% | Kedalaman analisis masalah nasional |
| Desain agentic AI | 20% | Kompleksitas reasoning & arsitektur |
| Implementasi | 20% | Fungsionalitas & integrasi tools |
| Evaluasi & validasi | 15% | Metode evaluasi & hasil |
| Inovasi | 10% | Kebaruan solusi |
| Etika & governance | 10% | Analisis risiko & mitigasi |
| Presentasi & demo | 10% | Kejelasan & delivery |

---

## 9. Batasan & Aturan Implementasi

- **Kelompok:** 3–4 mahasiswa
- **Durasi pengerjaan:** 4–6 minggu
- **Tidak menggunakan n8n** — orkestrasi dilakukan di Next.js API Routes
- **LLM Fallback wajib diimplementasikan** via Ollama untuk memastikan sistem tetap berjalan saat API cloud tidak tersedia
- **PaddleOCR** sebagai satu-satunya OCR engine (bukan Tesseract atau Google Vision)
- Wajib deklarasi penggunaan AI

---

## 10. Deklarasi Penggunaan AI

> Claude AI (Anthropic) digunakan untuk eksplorasi ide, review literatur, debugging, dan penulisan dokumen PRD ini. GitHub Copilot digunakan untuk code completion. Seluruh keputusan arsitektur, validasi logika bisnis, dan implementasi akhir dilakukan secara mandiri oleh tim.

---

*Dokumen ini adalah living document — update seiring perkembangan implementasi.*