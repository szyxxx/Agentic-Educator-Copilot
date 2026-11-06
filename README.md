# EduCopilot

Prototipe tugas akhir II5003 Applied Artificial Intelligence untuk membantu dosen mengelola RPS, materi, kuis, jawaban mahasiswa, dan analitik kelas. Backend memakai FastAPI, SQLAlchemy/SQLite, dan LangGraph; frontend memakai Next.js, TypeScript, dan Tailwind CSS.

## Cakupan saat ini

- RPS dapat dibuat manual atau dengan LLM, diedit, dan diperiksa dengan katalog deterministik berisi 24 kriteria SN-Dikti. Skor katalog adalah pemeriksaan aplikasi, bukan sertifikasi kepatuhan institusi. Persetujuan memerlukan seluruh kriteria terpenuhi. Generasi gagal tidak menimpa RPS lama; RPS disetujui dilindungi dari generate/regenerate.
- Kuis pilihan ganda dan esai dapat dibuat manual atau dari teks materi yang dipilih dosen. Agen memakai hingga 4.000 karakter teks; pembuatan kuis tidak melakukan pencarian RAG. Soal yang tidak lengkap ditolak sebelum draft disimpan.
- Jawaban diimpor melalui CSV. Pilihan ganda dinilai secara deterministik; esai dinilai LLM dengan rubrik. Feedback dan skor per soal disimpan pada submission. Jika penilaian esai gagal, nilai akhir tetap kosong dengan status `manual_review` dan dapat dinilai ulang setelah LLM pulih. Usulan LLM selalu `needs_review`, terpisah dari nilai final dan analitik. Dosen dapat mengubah skor serta feedback setiap esai, lalu menyetujui versi tersimpan. Konflik versi ditolak.
- Knowledge Hub menyimpan materi dan menyediakan pencarian RAG melalui ChromaDB. Unggahan PDF, TXT, dan Markdown dapat diekstrak menjadi teks; DOCX belum memiliki ekstraktor. Status terindeks dicatat hanya setelah pengindeksan berhasil. Label indeks lama yang belum terbukti ditampilkan sebagai belum diverifikasi.
- Setelah penilaian lengkap, aplikasi mencoba membuat materi penguatan untuk minggu berikutnya jika ada RPS. Materi `AUTO` berstatus `pending_review`, belum diindeks atau dipakai pencarian, sampai admin/dosen/penjamin mutu membaca dan menyetujuinya. Ini upaya tambahan yang dapat gagal tanpa membatalkan nilai. Tidak ada pencarian web Tavily yang terhubung dan Remedial Agent masih stub yang tidak dipakai alur aplikasi.
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
export AUTH_COOKIE_SECURE=false # Hanya untuk HTTP lokal
export CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
export OPENROUTER_API_KEY=
export ANTHROPIC_API_KEY=
export LLM_PROVIDER_ORDER=ollama
export OLLAMA_BASE_URL=http://127.0.0.1:9
export HF_HUB_OFFLINE=1

# Buat admin tanpa password bawaan; password diminta secara interaktif (≥12 karakter).
uv run python -m app.cli create-user --username admin --role admin

uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Health publik tersedia di `http://127.0.0.1:8000/health`. Endpoint lain, termasuk dokumentasi API, memerlukan sesi login. Gunakan frontend di bawah untuk login. Port 9 di atas sengaja tidak menyediakan LLM: alur manual, katalog kepatuhan, pilihan ganda, dan analitik tetap dapat dicoba. Generasi AI dan penilaian esai akan melaporkan kegagalan yang dapat dicoba ulang. Pengindeksan/pencarian RAG dapat gagal jika model embedding belum ada di cache.

`uv sync` memasang dependensi runtime dan grup dev (`pytest`, `httpx`); gunakan `uv sync --locked --no-dev` jika tidak membutuhkan alat uji. `backend/pyproject.toml` dan `uv.lock` adalah sumber pemasangan utama. `requirements.txt` mencantumkan dependensi runtime yang sama untuk pengguna pip; paket yang terkunci untuk pemasangan berulang ada di `uv.lock`.

Konfigurasi dibaca dari environment, lalu `.env` di folder backend jika tersedia. Environment menang atas `.env`. Tanpa `DATABASE_URL`, SQLite menggunakan `educopilot.db` relatif terhadap direktori kerja. Jika DB hilang atau belum diinisialisasi, backend gagal start dengan pesan jelas. Tidak ada seed diam-diam. `uv run python -m app.cli init-db` membuat DB kosong pada `DATABASE_URL`; `init-db --seed-demo` secara eksplisit mengisi contoh. Alternatif env eksplisit adalah `EDUCOPILOT_INIT_DB=true` dan `EDUCOPILOT_SEED_DEMO=true`. Jangan biarkan env seed aktif pada layanan operasional. DB yang dilacak Git dilindungi dari migrasi/tulisan; gunakan salinan di luar repo.

### Frontend

Di terminal kedua, mulai dari akar repo:

```bash
cd frontend
npm ci
cp .env.example .env.local
npm run dev
```

Buka **`http://localhost:3000/dashboard`**. Login memakai akun admin yang baru dibuat. Frontend meneruskan cookie HttpOnly melalui proxy API satu origin; token tidak disimpan di localStorage. `frontend/.env.local` memakai `API_BASE=http://127.0.0.1:8000` untuk alamat backend sisi server dan `APP_ORIGIN=http://localhost:3000` untuk origin publik. Sesuaikan `APP_ORIGIN` dan `CORS_ORIGINS` backend bersama-sama; jangan memakai wildcard. `NEXT_PUBLIC_API_BASE` tidak dipakai lagi. Untuk HTTPS, gunakan `AUTH_COOKIE_SECURE=true` (bawaan).

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

## Akun, hak akses, dan audit

Semua endpoint selain login dan health memerlukan sesi. Password di-hash Argon2id; sesi acak berlaku delapan jam dan hanya hash token disimpan di DB. Logout, reset password, perubahan penugasan, dan penonaktifan akun mencabut sesi. Permintaan yang mengubah data wajib mengirim `Origin` yang diizinkan (termasuk klien API langsung). Login salah dibatasi sepuluh percobaan per sumber/akun selama 15 menit.

| Peran | Hak akses |
|---|---|
| `admin` | Seluruh mata kuliah, akun/penugasan, pengaturan, tinjauan, dan audit |
| `dosen` | Hanya mata kuliah yang ditugaskan; membuat mata kuliah baru sekaligus mendapat penugasan; mengelola pengajaran, mengubah skor esai dan menyetujui nilai/materi miliknya |
| `penjamin_mutu` | Membaca data pengajaran seluruh mata kuliah dan audit, menjalankan review/approve RPS dan approve materi; tidak mengubah nilai, publish, delete, atau mengelola akun |

Admin membuat akun dan penugasan di **Akun & Penugasan**. Alternatif operator: `uv run python -m app.cli create-user --username nama --role dosen --course-id ID_MK` (opsi mata kuliah dapat diulang). Password diminta; untuk otomasi gunakan secret env `EDUCOPILOT_ACCOUNT_PASSWORD`, bukan argumen command line. Bootstrap admin saat DB belum memiliki akun juga tersedia melalui pasangan env `EDUCOPILOT_ADMIN_USERNAME` dan `EDUCOPILOT_ADMIN_PASSWORD`; tidak ada kredensial bawaan. Hapus secret bootstrap dari lingkungan setelah akun dibuat.

Tinjau nilai melalui detail kuis → **Tinjau nilai esai** → simpan perubahan bila perlu → **Setujui nilai tersimpan**. Baca dan setujui materi otomatis melalui **Knowledge Hub**. Penjamin mutu hanya dapat membaca nilai. Nilai pilihan ganda murni tetap deterministik dan dapat final otomatis.

**Jejak Audit** tersedia bagi admin/penjamin mutu, dengan filter dan paginasi. Log tersimpan dalam transaksi perubahan data: pelaku, waktu UTC, aksi, objek, revisi objek, fingerprint/versi aplikasi, model LLM, dan ID permintaan. Model diwariskan sebagai asal-usul objek bila diperlukan; `details.llm_called` membedakan pemanggilan pada operasi tersebut. Login gagal juga dicatat. Tidak ada endpoint menghapus audit. Ini bukan bukti log antirusak terhadap operator yang memiliki akses langsung ke file SQLite.

## Backup, restore, dan migrasi

Jalankan dari `backend`; contoh memakai DB aktif di luar repo:

```bash
uv run python -m app.cli backup --source /tmp/educopilot-demo.db --output-dir /tmp/educopilot-backups
# Ganti BACKUP.db dengan path hasil perintah di atas.
uv run python -m app.cli verify-backup /tmp/educopilot-backups/BACKUP.db
# Hentikan backend dahulu. Target tidak boleh ada, kecuali --replace dipilih eksplisit.
uv run python -m app.cli restore /tmp/educopilot-backups/BACKUP.db --target /tmp/educopilot-demo.db --replace
```

Backup online memakai API SQLite, file berizin 0600, pemeriksaan integritas, checksum SHA-256, serta manifest skema/isi per tabel. Backup dan target restore wajib di luar repo. Restore memakai lock eksklusif, verifikasi sebelum dan sesudah salin, membersihkan jurnal target lama, dan mencabut seluruh sesi snapshot. Backend memegang lock sepanjang startup/layanan; restore ditolak saat backend aktif. Mulai ulang dan login kembali sesudah restore. Penjadwalan, enkripsi, retensi, serta penyimpanan di domain kegagalan terpisah tetap tanggung jawab operator; skrip tidak menjanjikan RPO/RTO tertentu.

Ekspor `GET /api/quiz/{id}/replay.csv` membawa **Submission ID**. Replay CSV yang sama mempertahankan ID lama dan menjadi no-op; ID sama dengan isi berbeda ditolak 409. Unggahan baru tanpa ID memakai UUID5 stabil dari ID kuis dan NIM. Replay ini memulihkan jawaban, bukan keputusan nilai yang hilang sesudah titik backup; tinjau ulang nilai bila perlu.

Migrasi startup idempoten menambah tabel akun/sesi/penugasan, audit/revisi, penanda migrasi, serta kolom usulan nilai/per soal/versi/persetujuan dan status indeks. ID akademik lama tetap. Nilai esai lama yang belum memiliki bukti tinjauan dipindahkan ke usulan (`legacy:unknown`), final dikosongkan; dosen perlu mengisi skor per soal sebelum persetujuan. Materi AUTO lama kembali menunggu persetujuan. Indeks Chroma lama disaring memakai ID materi SQL yang masih sah dan sudah disetujui.

## Batas penggunaan

Prototipe menyediakan gerbang tinjauan dan alat backup terverifikasi, tetapi belum menyediakan backup terjadwal atau validasi mutu model. Gunakan data sintetis/anonim untuk uji lokal. Jawaban esai dikirim ke penyedia LLM yang dipilih; jangan masukkan data sensitif tanpa penilaian dan izin yang sesuai. RPS, soal, referensi, dan feedback yang dihasilkan perlu diperiksa dosen; aplikasi belum membuktikan kualitas pedagogis atau efektivitas remedialnya.

## Lisensi

Berkas [LICENSE](LICENSE) memuat **GNU Affero General Public License versi 3 (AGPLv3)**. Ketentuan penggunaan, perubahan, distribusi, interaksi melalui jaringan, dan penyangkalan jaminan mengikuti berkas tersebut.
