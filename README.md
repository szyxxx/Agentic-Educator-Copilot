# EduCopilot

Prototipe tugas akhir II5003 Applied Artificial Intelligence untuk membantu dosen mengelola RPS, materi, kuis, jawaban mahasiswa, dan analitik kelas. Backend memakai FastAPI, SQLAlchemy/SQLite, dan LangGraph; frontend memakai Next.js, TypeScript, dan Tailwind CSS.

## Cakupan saat ini

- RPS dapat dibuat manual atau dengan LLM, diedit, dan diperiksa dengan katalog deterministik berisi 24 kriteria SN-Dikti. Skor katalog adalah pemeriksaan aplikasi, bukan sertifikasi kepatuhan institusi. Persetujuan memerlukan seluruh kriteria terpenuhi. Generasi gagal tidak menimpa RPS lama; RPS disetujui dilindungi dari generate/regenerate.
- Kuis pilihan ganda dan esai dapat dibuat manual atau dari teks materi yang dipilih dosen. Agen memakai hingga 4.000 karakter teks; pembuatan kuis tidak melakukan pencarian RAG. Soal yang tidak lengkap ditolak sebelum draft disimpan.
- Jawaban diimpor melalui CSV. Pilihan ganda dinilai secara deterministik; esai dinilai LLM dengan rubrik. Feedback esai disimpan pada submission. Jika penilaian esai gagal, nilai akhir tetap kosong dengan status `manual_review` dan dapat dinilai ulang setelah LLM pulih. Belum ada editor nilai manual.
- Knowledge Hub menyimpan materi dan menyediakan pencarian RAG melalui ChromaDB. Unggahan PDF, TXT, dan Markdown dapat diekstrak menjadi teks; DOCX belum memiliki ekstraktor. Status terindeks dicatat hanya setelah pengindeksan berhasil. Label indeks lama yang belum terbukti ditampilkan sebagai belum diverifikasi.
- Setelah penilaian lengkap, aplikasi mencoba membuat materi penguatan untuk minggu berikutnya jika ada RPS. Ini upaya tambahan yang dapat gagal tanpa membatalkan nilai. Tidak ada pencarian web Tavily yang terhubung dan Remedial Agent masih stub yang tidak dipakai alur aplikasi.
- Dashboard menghitung statistik dari data tersimpan dan menyediakan ekspor PDF analitik. Progres CPMK masih memakai rata-rata kelas, belum hasil pemetaan setiap soal ke CPMK. Tren industri pada generasi RPS berasal dari LLM, bukan pencarian sumber terkini.

## Prasyarat

- Python **3.11 atau lebih baru** dan `uv`.
- Node.js **20.9 atau lebih baru** dan npm (sesuai kebutuhan Next.js 16).
- Git. Dependensi backend, terutama PyTorch/model embedding, membutuhkan ruang beberapa GB; lingkungan uji sebelumnya sekitar 5,3 GB untuk `.venv`.

## Pemasangan lokal

```bash
git clone https://github.com/szyxxx/Agentic-Educator-Copilot.git
cd Agentic-Educator-Copilot
```

Perintah berikut dimulai dari akar repo. Untuk memakai checkout yang sudah ada, langsung masuk ke folder repo tersebut.

### Backend tanpa LLM berbayar

```bash
cd backend
uv sync --locked
cp .env.example .env

# Pakai salinan agar DB contoh yang dilacak Git tidak berubah.
cp educopilot.db /tmp/educopilot-demo.db
export DATABASE_URL=sqlite:////tmp/educopilot-demo.db
export CHROMA_PERSIST_DIR=/tmp/educopilot-demo-chroma
export OPENROUTER_API_KEY=
export ANTHROPIC_API_KEY=
export LLM_PROVIDER_ORDER=ollama
export OLLAMA_BASE_URL=http://127.0.0.1:9
export HF_HUB_OFFLINE=1

uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

API tersedia di `http://127.0.0.1:8000/docs`. Port 9 di atas sengaja tidak menyediakan LLM: alur manual, katalog kepatuhan, pilihan ganda, dan analitik tetap dapat dicoba. Generasi AI dan penilaian esai akan melaporkan kegagalan yang dapat dicoba ulang. Pengindeksan/pencarian RAG dapat gagal jika model embedding belum ada di cache.

`uv sync` memasang dependensi runtime dan grup dev (`pytest`, `httpx`); gunakan `uv sync --locked --no-dev` jika tidak membutuhkan alat uji. `backend/pyproject.toml` dan `uv.lock` adalah sumber pemasangan utama. `requirements.txt` mencantumkan dependensi runtime yang sama untuk pengguna pip; paket yang terkunci untuk pemasangan berulang ada di `uv.lock`.

Konfigurasi dibaca dari environment, lalu `.env` di folder backend jika tersedia. Environment menang atas `.env`. Tanpa `DATABASE_URL`, SQLite menggunakan `educopilot.db` relatif terhadap direktori kerja. DB baru akan dibuat dan diisi data contoh saat startup bila file belum ada; gunakan path salinan di atas untuk pengujian.

### Frontend

Di terminal kedua, mulai dari akar repo:

```bash
cd frontend
npm ci
npm run dev
```

Buka **`http://localhost:3000/dashboard`**. Gunakan host `localhost` karena CORS backend mengizinkan origin tersebut. Frontend mengakses backend `http://127.0.0.1:8000` secara bawaan. Jika alamat backend berbeda, atur `NEXT_PUBLIC_API_BASE` sebelum `npm run dev` atau sebelum build.

Untuk menjalankan hasil build:

```bash
npm run build
npm run start
```

Hentikan server dengan `Ctrl+C` pada masing-masing terminal.

## Mengaktifkan LLM dan RAG

Urutan bawaan `LLM_PROVIDER_ORDER` adalah `openrouter,anthropic,ollama`. Kode memilih penyedia pertama yang memiliki konfigurasi; ini **bukan perpindahan otomatis ketika panggilan penyedia gagal**. Lihat `backend/.env.example` untuk nama variabel kunci, model, dan alamat layanan. Jangan menyimpan kunci API di Git.

Untuk Ollama lokal yang sudah menyediakan model, ubah `OLLAMA_BASE_URL` ke layanan tersebut (bawaan `http://localhost:11434`) dan sesuaikan `OLLAMA_MODEL` (bawaan `gemma3:4b`). OpenRouter dan Anthropic memerlukan kredensial masing-masing dan dapat menimbulkan biaya.

RAG memakai `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`. Pemakaian pertama memerlukan unduhan model Hugging Face dan jaringan, atau cache model yang sudah lengkap. Lepaskan `HF_HUB_OFFLINE=1` jika ingin mengunduh. `CHROMA_PERSIST_DIR` dapat diatur melalui environment; bawaan lokasinya `backend/chroma_db`.

## Pengujian

```bash
cd backend
uv run pytest
```

Tes memakai DB sementara, LLM/RAG tiruan, memblokir jaringan, dan memeriksa hash DB repo. Tes ini memeriksa perilaku aplikasi; mutu keluaran model sungguhan dan keberhasilan embedding sungguhan memerlukan pengujian terpisah.

Dari akar repo, build frontend:

```bash
cd frontend
npm ci
npm run build
```

## Batas penggunaan

Prototipe belum menyediakan autentikasi, pembatasan peran, audit log, backup otomatis, maupun alur persetujuan nilai oleh manusia. Gunakan data sintetis/anonim untuk uji lokal. Jawaban esai dikirim ke penyedia LLM yang dipilih; jangan masukkan data sensitif tanpa penilaian dan izin yang sesuai. RPS, soal, referensi, dan feedback yang dihasilkan perlu diperiksa dosen; aplikasi belum membuktikan kualitas pedagogis atau efektivitas remedialnya.

## Lisensi

Berkas [LICENSE](LICENSE) memuat **GNU Affero General Public License versi 3 (AGPLv3)**. Ketentuan penggunaan, perubahan, distribusi, interaksi melalui jaringan, dan penyangkalan jaminan mengikuti berkas tersebut.
