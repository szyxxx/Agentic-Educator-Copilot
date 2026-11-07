# Analisis Gap: Repo EduCopilot vs Panduan Tugas GanAI (KS5102)

Tanggal pembaruan: 7 November 2026.
Panduan: `docs/Panduan Tugas Mahasiswa GanAI - SO.pdf` (13 halaman), slide `docs/10-TradeOff_Resiliensi.pdf` (45 slide), template kosong `docs/template-asesmen-kematangan-digital-twinISOIEC 30186 - 2025.xlsx`, `docs/kuesioner-maturity.md`, dan `docs/pedoman-lapangan-ganai.md`.
Acuan kode: branch `test/alat-uji`, HEAD `01b446d3e3231af2dbe3cae892f846167015b941` (diperiksa dengan `git rev-parse HEAD`). Seluruh rujukan kode `file:baris` menunjuk HEAD ini; hasil uji tetap menyebut versi yang benar-benar diuji. Backend HEAD identik dengan commit uji `972ad7b`.

Batas bukti: pembaruan ini memeriksa kode dan artefak lokal, bukan menjalankan pilot kampus. E1/E2 memakai DB/proses sintetis terpisah dan LLM tiruan; pengukuran Ollama memakai model lokal nyata pada dataset kecil. Tidak ada wawancara, foto, respon kuesioner, atau skor layanan prodi yang dibuat.

Sumber bukti utama:
- `docs/rancangan-resiliensi.md`, bagian 8.5 dan 9, serta `docs/bukti-uji/resiliensi-20261107T010337Z/ringkasan-terverifikasi.json`: tiga run E1 dan tiga run E2 pada `972ad7b`, log/manifest tersedia.
- `docs/bukti-uji/tata-kelola-20261107/laporan-akhir.md`: **laporan thread, bukan log asli**. Log mentah pemasangan/browser/pemulihan thread ini hilang karena restart; angka di dalamnya tidak dinaikkan menjadi observasi yang diverifikasi ulang. Mekanisme kode dan subsetnya diperiksa melalui bukti resiliensi yang masih tersedia.
- `docs/bukti-uji/frontend-20261107/laporan.md`: lint 0 error/0 warning, audit produksi 0; audit lengkap masih delapan entri sedang dari satu advisori akar minimatch pada dependensi dev. Bukan audit npm seluruhnya bersih.
- `docs/bukti-uji/ollama-20261106/laporan-ollama.md` beserta trace/hasil pengukuran: `qwen3.5:9b`, embedding `bge-m3`, format JSON dan pengulangan nilai. Perilaku finalisasi nilai pada laporan historis mendahului gerbang tinjauan terbaru.

Cara baca: `P5` adalah halaman PDF panduan; `S31` adalah slide resiliensi. SIAP selalu terbatas pada prototipe, bukan pengesahan kondisi kampus.

---

## 1. Ringkasan eksekutif

**Jawaban singkat.** Prototipe kini mempunyai alat uji, Ollama lokal, startup aman, backup/restore CLI, ID replay stabil, tinjauan manusia, autentikasi/peran dan audit. Bug B1–B18 dari baseline sudah diperbaiki; pemeriksaan implementasi dan tes tersedia, tetapi mutu pedagogis serta efektivitas layanan belum terbukti. Hambatan utama tugas tetap bukti masalah dan operasi prodi.

| Status | Sebelum | Sesudah | Arti singkat |
|---|---:|---:|---|
| SIAP | 12 | 35 | Bisa diisi untuk prototipe dari kode/bukti uji |
| SEBAGIAN | 56 | 63 | Ada bagian yang terbukti, sisanya masih terbuka |
| BUTUH LAPANGAN | 78 | 74 | Memerlukan bukti kondisi nyata |
| BUTUH BANGUN | 36 | 10 | Masih perlu fitur/pengukuran baru |

Total tetap 182 kewajiban unik; 24 berasal dari slide di bagian 5.12a. Hitungan diperoleh dari kolom Status matriks bagian 5, bukan daftar pekerjaan bagian 8.

**Lima gap terbesar**

1. **Belum ada bukti lapangan.** Observasi, foto, wawancara, kuesioner, konfirmasi pengelola, fungsi minimum, dan target RTO/RPO prodi tetap harus dikumpulkan.
2. **Kondisi prodi belum diketahui.** Prototipe uji sintetis tidak menjawab cara layanan kampus berjalan; kluster dan pemakaian ulang karya perlu pengesahan dosen.
3. **Loop hasil belajar dan L3 belum tersedia.** Belum ada pengukuran efek remedial, pemetaan soal–CPMK, prediksi atau stock-flow. Remedial Agent tetap stub (`backend/app/agents/remedial_agent.py:16-34`).
4. **Tata kelola teknis sudah ada, tata kelola organisasi belum.** Peran admin/dosen/penjamin mutu dan audit diterapkan (`backend/app/core/auth.py:24`, `backend/app/core/audit.py:76-129`); pemilik layanan, operator, retensi, eskalasi dan izin data prodi belum disahkan. Audit bukan antirusak terhadap pemilik SQLite.
5. **Mutu model dan pemulihan penuh belum terbukti.** Kesesuaian nilai model dengan dosen belum diukur. `qwen3.5:9b` masih menghasilkan kesalahan referensi/feedback/diagnosis; tinjauan manusia menahan publikasi, bukan menjamin kebenaran. Backup belum terjadwal/terenkripsi/berdomain fisik terpisah; `created_at` berubah saat replay, dan keputusan nilai/audit pascabackup tidak dipulihkan oleh CSV jawaban.

**Perkiraan maturity (kode dan uji sintetis, belum instrumen resmi)**

| Perspektif | Perkiraan | Catatan |
|---|---|---|
| Antroposentris | Tidak diberi skor | Wajib kuesioner Likert |
| Sistemik | Level 2 (Reactive) | Bekerja setelah dipicu manusia, input manual |
| Teknologi | Level 2 (dipakai di sebagian sistem) | Batas sistem: satu prodi |
| Digital Twin (lima level panduan) | Level 1 (Descriptive), dengan kemampuan Level 2 di kode | Level 2 belum terbukti pada data nyata |
| Template ISO/IEC 30186 (draf prototipe) | Skor 0,8 dari 5, label Awal | Skala berbeda, diisi terpisah (bagian 4) |

**Kluster.** Smart Education tetap kandidat terbaik, tetapi diterima bersyarat (lihat bagian 2). Syarat terpenting: panduan di Tahap 1 dan 2 ditulis untuk 13 kluster Smart Building, sehingga izin memakai kluster Smart Campus perlu dikonfirmasi ke dosen.

**Template kini tersedia.** Draf yang diperbarui untuk prototipe ada di `docs/draf-asesmen-kematangan-prototipe.xlsx` dan belum diverifikasi tim. Delapan sumber acuan di bagian 7 panduan masih tidak ada secara lokal (lihat bagian 6).

---

## 2. Uji asumsi kluster

Asumsi yang diuji: Smart Campus > Smart Tridarma > Smart Education adalah kluster terdekat.

| Kandidat | Kecocokan dengan kode | Penilaian |
|---|---|---|
| Smart Education (Campus 1): platform pembelajaran, dashboard progres akademik | Tinggi. RPS, kuis, penilaian, analitik kelas (`backend/app/api/v1/dashboard.py:373-459`) | Terbaik, bersyarat |
| Smart Research (Campus 2): repositori, portal kolaborasi | Rendah. Hanya Knowledge Hub materi kuliah, bukan riset (`backend/app/api/v1/knowledge.py:23`) | Ditolak |
| Smart HR Management (Campus 8): beban kerja | Rendah. Tidak ada data kehadiran atau beban kerja di model | Ditolak |
| Smart Meeting, Occupancy (Campus 12, Building 6): utilisasi ruang | Tidak ada. Tidak ada data ruang atau jadwal | Ditolak |
| Cybersecurity & Data Privacy (Building 10): audit log | Audit dan autentikasi kini tersedia sebagai kontrol pendukung, bukan layanan keamanan gedung (`backend/app/core/audit.py:76-129`) | Bukan fokus kluster |
| Kluster Smart Building lain | Tidak ada. Tidak ada sensor atau perangkat | Ditolak |

Kesimpulan: **asumsi diterima bersyarat.** Tidak ada kandidat lain yang mendekati. Namun ada empat hal yang melemahkannya:

1. **Konflik di panduan.** Bagian 1 dan 2 (P1-2) mengizinkan Smart Campus atau Smart Building, tetapi Tahap 1 menyebut "13 kluster" dan Tahap 2 menyebut "satu kluster dari 13 pilihan" (P3). Contoh maturity di P4 justru memakai Smart Education. Perlu konfirmasi dosen.
2. **Sisi mahasiswa tidak ada.** Cakupan kluster menyebut dashboard progres akademik, tetapi antarmuka untuk dosen/admin/penjamin mutu (`frontend/src/app/dashboard/layout.tsx:22-26`). Portal/peran mahasiswa belum ada (`backend/app/core/auth.py:24`).
3. **Progres akademik belum nyata.** Progres per CPMK hanya rata-rata kelas yang disalin ke setiap CPMK (`backend/app/core/stats.py:139-149`).
4. **Pemilihan kluster harus berdasar bukti Tahap 1** (checklist P3). Memilih Smart Education sekarang, sebelum observasi, melanggar urutan itu. Sebaiknya kluster ini dicatat sebagai hipotesis sampai Tahap 1 selesai.

---

## 3. Kondisi nyata repo

### 3.1 Klaim dan perilaku kode terbaru

README sudah diselaraskan; gunakan implementasi sebagai bukti utama.

| Kemampuan | Kenyataan HEAD | Bukti |
|---|---|---|
| Informasi eksternal | Tavily belum dipakai; tren diminta dari LLM | `backend/app/agents/rps_agent.py:39-48` |
| Kuis dan RAG | Kuis memakai teks pilihan manusia hingga 4.000 karakter; RAG hanya pencarian tersendiri | `backend/app/agents/quiz_agent.py:104-116`, `backend/app/api/v1/knowledge.py:243-265` |
| Remedial Agent | Masih stub, tidak dipanggil alur penilaian | `backend/app/agents/remedial_agent.py:16-36`, `backend/app/core/grade_review.py:65-87` |
| Nilai/feedback esai | Skor dan feedback per soal serta snapshot/model/versi tersimpan; esai sehat menjadi usulan `needs_review`, final kosong; gagal menjadi `manual_review` | `backend/app/api/v1/grading.py:88-138`, `backend/app/models/submission.py:30-39` |
| Tinjauan manusia | Admin/dosen mengedit dan menyetujui dengan versi; materi AUTO menunggu persetujuan dan baru diindeks sesudahnya | `backend/app/api/v1/grading.py:206-321`, `backend/app/api/v1/materials.py:270-291` |
| Progres CPMK | Masih placeholder rata-rata kelas, belum hasil pemetaan soal | `backend/app/core/stats.py:136-149` |
| Kepatuhan RPS | 24 kriteria deterministik; approve menghitung ulang dan menolak temuan; refine agent masih kosong, bukan loop perbaikan pedagogis otomatis | `backend/app/core/sndikti_catalog.py:428`, `backend/app/api/v1/rps.py:655-666`, `backend/app/agents/rps_agent.py:430-448` |
| Validasi generasi | Kuis memeriksa jumlah, ID, opsi/kunci dan rubrik; RPS memvalidasi hasil sebelum menyimpan jadwal | `backend/app/agents/quiz_agent.py:241-260`, `backend/app/api/v1/rps.py:253-263`, `backend/app/api/v1/rps.py:474-490` |
| Ollama lokal | Builder mendukung reasoning nonaktif dan konteks; JSON berskema dengan satu retry khusus Ollama; esai memakai temperatur 0 dan seed | `backend/app/core/llm.py:95-112`, `backend/app/core/llm_json.py:18-73`, `backend/app/agents/grading_agent.py:117-129` |
| Konfigurasi penyedia | Pengukuran memakai `ollama`/`qwen3.5:9b`; default kode masih urutan cloud dan model `gemma3:4b`. Pilihan lokal harus eksplisit; belum ada failover setelah invoke gagal | `backend/app/core/config.py:39-43`, `backend/app/core/config.py:71-82`, `backend/app/core/llm.py:127-145` |

Perbaikan B1–B18 tidak berarti seluruh risiko selesai. Tes mencakup penilaian MCQ/esai, kegagalan LLM, katalog, API inti, konfigurasi, JSON Ollama, migrasi, autentikasi, audit, tinjauan manusia dan pemulihan. Bukti dasar versi backend saat ini: 249 tes lulus dalam `docs/bukti-uji/resiliensi-20261107T010337Z/pytest-baseline.log`; pemeriksaan payload/format tidak mengukur akurasi akademik.

### 3.2 Data di `backend/educopilot.db`

| Tabel | Baris | Asal |
|---|---:|---|
| courses | 2 | 1 dari seed (II5003), 1 dibuat manual (II5005) |
| rps | 2 | Hasil pakai aplikasi, keduanya `validated` |
| rps_meetings | 32 | 16 per RPS |
| rps_findings | 0 | Tidak ada jejak Review Agent |
| materials | 4 | 2 materi teks sintetis (`TXT`, pengganti PDF kuliah), 2 hasil LLM (`AUTO`) |
| quizzes | 2 | Satu per mata kuliah |
| students | 3 | Seed (`backend/app/seed.py:95-99`) |
| submissions | 6 | Dari 3 NIM yang sama |
| settings | 10 | Seed (`backend/app/seed.py:15-26`) |

**Kesimpulan: seed dan uji coba manual, bukan data operasional.** Tidak bisa dipakai sebagai bukti kondisi nyata maupun evaluasi model. Nama, NIM, dan isi dua materi PDF di DB kini sintetis.

- Tiga jawaban esai kuis II5005 identik (hash sama), semuanya bernilai 61,7.
- Semua submission per kuis tercatat pada detik yang sama, yaitu hasil satu kali unggah CSV.
- Hanya ada satu kuis per mata kuliah, sehingga tren dan efek remedial tidak bisa dihitung.
- 9 dari 10 kunci jawaban kuis II5003 adalah "B", sinyal mutu soal LLM. Label kuis menyebut "MCQ + Esai" padahal 10 soalnya MCQ.
- Roster seed kini sintetis (`Mahasiswa 01` sampai `Mahasiswa 03`), jadi tidak lagi memuat nama orang. Keanggotaan tim tetap perlu konfirmasi pengguna (K4).
- Snapshot DB masih menyimpan status lama; kode kini memperbarui status berdasarkan metrik (`backend/app/core/stats.py:269-292`). Snapshot tidak dimigrasi pada pekerjaan dokumentasi ini.
- Snapshot `quizzes.submissions` bernilai 0 padahal tiap kuis punya 3 submission; impor sekarang menghitung ulang jumlah (`backend/app/api/v1/quiz.py:539-550`).
- Folder `chroma_db` tidak ada, jadi indeks RAG tidak ikut di repo (`backend/app/core/rag.py:8-27`).

Hasil katalog pada analisis lama atas salinan snapshot: kedua RPS memperoleh 100 (bobot 250/250, 102 baris penilaian, 0 gagal). Ini hasil historis pemeriksaan struktur, bukan mutu pengajaran. HEAD kini menghitung ulang katalog saat approve dan menolak temuan (`backend/app/api/v1/rps.py:655-666`); tidak lagi menulis 100 tanpa pemeriksaan. Startup melindungi DB repo dan memigrasi hanya salinan yang dipilih (`backend/app/core/database.py:66-92`). Skor esai lama tanpa bukti review dipindahkan ke usulan pada migrasi salinan (`backend/app/core/governance_migration.py:1-98`).

Privasi: nama dan NIM di `backend/app/seed.py:96-98` dan `backend/educopilot.db` kini sintetis, begitu juga isi dua materi PDF di DB. Riwayat git masih menyimpan versi lama, jadi paket akhir ke Living Lab harus memakai kondisi terbaru tanpa riwayat itu. Keputusan pengguna: kuis dan RPS di DB yang diturunkan dari slide dibiarkan.

### 3.3 Lima siklus smart system

| Siklus | Yang benar-benar ada | Yang tidak ada | Nilai |
|---|---|---|---|
| Sensing | Unggah CSV jawaban (`backend/app/api/v1/quiz.py:414`), impor roster (`backend/app/api/v1/students.py:93`), unggah materi (`backend/app/api/v1/materials.py:132`) | Pengumpulan otomatis. Tidak ada konektor LMS atau SIAKAD, tidak ada penjadwal | Manual, batch |
| Understanding | Nilai MCQ dan esai (`backend/app/agents/grading_agent.py:51`, `backend/app/agents/grading_agent.py:78`), statistik kelas dan heatmap (`backend/app/core/stats.py:167`), katalog (`backend/app/core/sndikti_catalog.py:710`), review agent (`backend/app/agents/rps_review_agent.py:443-458`) | Analisis per CPMK. "Topik lemah" hanyalah 80 karakter awal teks soal (`backend/app/agents/grading_agent.py:222`) | Ada, terkuat |
| Decision | Aturan ambang: status kuis (`backend/app/core/grade_review.py:47-61`), alert (`backend/app/api/v1/dashboard.py:89-107`). Keputusan manusia: approve, publish, apply, dismiss | Prediksi, prioritas, atau rekomendasi per mahasiswa | Sebagian, berbasis ambang |
| Action | Materi otomatis minggu berikutnya (`backend/app/agents/auto_material_agent.py:77`), terapkan temuan ke RPS (`backend/app/api/v1/rps.py:989`) | Tindakan yang sampai ke mahasiswa. Notifikasi stub (`backend/app/agents/remedial_agent.py:32-34`), dan toggle notifikasi tidak dibaca oleh proses apa pun (`backend/app/api/v1/dashboard.py:581-597`) | Sebagian, berhenti di dosen |
| Learning | Temuan yang di-dismiss tetap diingat antar-run (`backend/app/api/v1/rps.py:891-897`). Catatan dosen dipakai saat regenerasi (`backend/app/api/v1/rps.py:1330-1333`) | Evaluasi hasil, pembaruan model atau aturan, riwayat antar-semester | Hampir tidak ada |

### 3.4 Unsur sistem yang diminta panduan

| Unsur | Temuan HEAD dan batas bukti | Bukti |
|---

## 4. Perkiraan maturity

**Peringatan.** Ini perkiraan awal untuk **prototipe**, dari kode dan uji sintetis. Ini bukan hasil instrumen panduan, yang mewajibkan bukti dan konfirmasi pengelola kampus (P4). Jangan dikutip sebagai skor layanan kampus. Panduan hanya memberi nama level Sistemik (Impulsive, Reactive, Responsive, Initiative) tanpa definisi, dan artikel sumbernya tidak tersedia lokal, sehingga pemetaan di bawah adalah tafsiran. Sengaja tidak diberi angka desimal seperti contoh 2,89 di P4, karena angka itu berasal dari instrumen.

### Sistemik: Level 2 (Reactive)

| Pertanyaan bertingkat panduan (P4) | Jawaban | Alasan |
|---|---|---|
| Apakah data dikumpulkan sistem secara otomatis? | Tidak | Semua input lewat unggahan manual (`backend/app/api/v1/quiz.py:414`) |
| Apakah sistem mengolah dan menganalisis sehingga manusia tinggal memutuskan? | Ya, untuk sebagian | Penilaian, heatmap, dan temuan RPS tersedia. CPMK tidak (`backend/app/core/stats.py:149`) |
| Apakah sistem dapat mengambil keputusan dari analitik? | Terbatas | MCQ dapat final otomatis; esai menunggu dosen dan materi AUTO menunggu persetujuan (`backend/app/api/v1/grading.py:88-112`, `backend/app/api/v1/materials.py:270-291`) |

Bukan Level 3 karena tidak ada penjadwal atau pemicu otomatis: setiap agen dijalankan oleh tombol manusia (`backend/app/api/v1/grading.py:23`), dan siklus learning hampir kosong. Bukan Level 1 karena alur penilaian sampai materi sudah terintegrasi dan konsisten.

### Teknologi: Level 2 (dipakai di sebagian sistem)

Batas sistem sudah diputuskan: satu prodi (K3). TI di prototipe hadir di RPS, kuis, penilaian, dan analitik, tetapi tidak di sisi mahasiswa, presensi, integrasi data akademik, atau notifikasi. Nilai resmi tetap harus diukur pada prodi yang dipilih, bukan dari repo.

### Digital Twin: Level 1 (Descriptive), kemampuan Level 2 ada di kode

- **Level 1 belum kuat.** Syaratnya model digital terhubung ke sistem nyata (P5). Modelnya ada (`backend/app/models/course.py:8`, `backend/app/models/rps_meeting.py:8`), tetapi koneksinya unggahan manual dan belum pernah memuat data operasional.
- **Level 2 ada kemampuannya.** Data diubah menjadi wawasan oleh LLM dan aturan (`backend/app/agents/grading_agent.py:101`, `backend/app/core/stats.py:244`). Gambar di P5 mengaitkan Level 2 dengan data sensor, yang di sini setara data aktivitas belajar. Data itu belum mengalir terus-menerus.
- **Level 3 tidak terpenuhi.** Tidak ada prediksi, hanya ambang atas data lampau (`backend/app/core/stats.py:224-228`).
- **Level 4 dan 5 tidak terpenuhi.** Tidak ada simulasi what-if atau otonomi.

Keputusan esai dan publikasi AUTO mempunyai gerbang manusia; MCQ deterministik dapat final otomatis. Belum ada otonomi yang disahkan pada layanan nyata.

### Template ISO/IEC 30186: draf prototipe, 0,8 dari 5 (Awal)

File: `docs/draf-asesmen-kematangan-prototipe.xlsx`. Status: draf dari bukti kode, belum diverifikasi tim. Entitasnya prototipe di repo, bukan prodi atau kampus. Asesmen batas satu prodi harus dibuat terpisah setelah bukti lapangan ada.

**Skala template berbeda dari model lima level di panduan, dan keduanya diisi terpisah.** Jangan mengonversi yang satu ke yang lain.

| Pembeda | Model lima level panduan (P5) | Template asesmen |
|---|---|---|
| Bentuk | Satu level keseluruhan | Lima aspek berbobot, 25 indikator Ya/Tidak |
| Nama level | Descriptive, Informative, Predictive, Comprehensive, Autonomous | Static / dasar, Connected, Integrated, Interactive, Autonomous |
| Nilai terendah | Level 1 | Tingkat 0 (Belum dasar) dari rumus |
| Syarat Level 2 | Data diubah menjadi wawasan | Data mengalir otomatis, bukan unggah manual |
| Dipakai untuk | T3-16, T3-17 | TG-05a, TG-05b |

Skor template sebelumnya 0,6 dan sekarang 0,8; label tetap Awal. Kenaikan berasal dari pembatasan akses R1. Trace keputusan R4 juga menjadi Ya, tetapi tidak melompati celah R2/R3.

| Aspek | Ya sebelum → sesudah | Tingkat sebelum → sesudah | Skor berbobot sebelum → sesudah | Alasan |
|---|---:|---:|---:|---|
| Convergence | 1 → 1 | 1 → 1 | 0,2 → 0,2 | Masih unggah manual, belum aliran otomatis |
| Capability | 0 → 0 | 0 → 0 | 0,0 → 0,0 | P1/P2 tetap konservatif: demo sintetis bukan data lapangan |
| Integrated view | 1 → 1 | 1 → 1 | 0,2 → 0,2 | Belum integrasi layanan/entitas nyata |
| Time | 1 → 1 | 1 → 1 | 0,2 → 0,2 | T3 tetap Tidak: audit dan replay jawaban belum replay seluruh riwayat; `created_at` berubah |
| Trustworthiness | 0 → 2 | 0 → 1 | 0,0 → 0,2 | R1 dan R4 menjadi Ya; R2/R3 belum terpenuhi |
| **Total** | **3 → 5 dari 25** | | **0,6 → 0,8 (Awal)** | Bobot masing-masing 0,2 tetap |

R1 berubah karena sumber sintetis diketahui dan akses dibatasi sesi/peran/scope (`backend/app/core/auth.py:119-260`, `backend/tests/test_autentikasi.py:1-319`). R4 berubah karena snapshot soal/rubrik, skor per soal, model, versi, reviewer dan audit dapat ditelusuri (`backend/app/models/submission.py:30-39`, `backend/app/core/audit.py:76-129`; audit review diperiksa pada E1). Tinjauan manusia dan restore memperkuat catatan R4/T3/R5 tetapi tidak otomatis memenuhi indikator validasi lapangan, histori penuh atau audit berkala.

| Syarat twin | Aturan | Hasil tetap |
|---|---|---|
| Aliran otomatis fisik ke digital | Convergence ≥ 2 | Belum |
| Aliran balik digital ke fisik | Convergence ≥ 4 | Masih shadow atau model |
| Keputusan otonom | Capability = 5 | Masih butuh manusia |

Aturan Ya/Tidak dan rumus berjenjang template dipertahankan. P1/P2/I2 tetap Tidak karena belum bukti keadaan operasional; R2 belum pemantauan kualitas lengkap, R3 belum kalibrasi terhadap dosen/lapangan, R5 belum audit berkala. Jika dosen kelak menerima demo untuk P1 atau memakai tingkat minimum 1 dari Petunjuk, asesmen harus dihitung ulang; pekerjaan ini mengikuti rumus tingkat 0 yang sudah dipakai sebelumnya (K11).

### Antroposentris: tidak diberi skor

Wajib kuesioner Likert kepada mahasiswa, dosen, dan pejabat struktural (P4). Belum ada data.

**Usulan sasaran (belum keputusan):** Sistemik Level 3 dan Digital Twin Level 3 masuk akal untuk satu semester, tetapi hanya layak ditetapkan setelah masalah di Tahap 4 jelas. Sasaran template ditetapkan terpisah per aspek.

---

## 5. Matriks gap lengkap

Aturan status:

- SIAP berarti bisa diisi untuk **prototipe** dari repo. Ini tidak membuktikan kondisi kampus.
- Jika sebuah baris terhambat dua hal, status yang dipakai adalah hambatan utamanya.
- "Belum ada" berarti tidak ada bukti di repo maupun folder lokal yang diperiksa.
- Label sumber `[S..]` menandai kewajiban yang berasal dari slide, bukan dari panduan.

### 5.1 Ketentuan umum dan pilihan kluster (P1-2)

| ID | Kewajiban | Status | Bukti | Yang kurang |
|---|---|---|---|---|
| U-01 | Tim 3 sampai 5 mahasiswa | BUTUH LAPANGAN | Belum ada data tim | Pengguna perlu menyebut anggota tim |
| U-02 | Satu tim satu kluster | SEBAGIAN | Hipotesis Smart Education (bagian 2) | Konfirmasi dosen, bukti Tahap 1 |
| U-03 | Satu artefak per pertemuan, PDF atau format disepakati | BUTUH LAPANGAN | Belum ada artefak | Jadwal pertemuan, format |
| U-04 | Artefak dikumpulkan ke repositori Living Lab | BUTUH LAPANGAN | Belum ada | Lokasi repositori tidak disebut panduan |
| U-05 | Semua klaim didukung bukti terverifikasi | SEBAGIAN | Dokumen ini memberi rujukan kode | Bukti lapangan |

### 5.2 Tahap 1: Observation & Problem Discovery (P3)

| ID | Kewajiban | Status | Bukti | Yang kurang |
|---|---|---|---|---|
| T1-01 | Kunjungi minimal satu gedung atau area | BUTUH LAPANGAN | Belum ada | Kunjungan |
| T1-02 | Foto kondisi aktual | BUTUH LAPANGAN | Belum ada | Foto |
| T1-03 | Catatan lapangan | BUTUH LAPANGAN | Belum ada | Catatan |
| T1-04 | Checklist waktu, lokasi, kondisi | BUTUH LAPANGAN | Belum ada | Form bisa disiapkan AI, isinya tidak |
| T1-05 | Minimal 5 masalah dengan perkiraan dampak | BUTUH LAPANGAN | Belum ada | Tidak boleh diturunkan dari fitur repo |
| T1-06 | Checklist: tiap masalah punya lokasi dan waktu | BUTUH LAPANGAN | Belum ada | Bergantung T1-05 |
| T1-07 | Checklist: ada foto atau bukti pendukung | BUTUH LAPANGAN | Belum ada | Bergantung T1-02 |
| T1-08 | Checklist: tanpa asumsi solusi teknologi | BUTUH LAPANGAN | Belum ada | Risiko tertinggi, lihat bagian 7 |

### 5.3 Tahap 2: Cluster & Stakeholder (P3)

| ID | Kewajiban | Status | Bukti | Yang kurang |
|---|---|---|---|---|
| T2-01 | Petakan masalah Tahap 1 ke kluster | BUTUH LAPANGAN | Belum ada | Bergantung T1-05 |
| T2-02 | Pilih satu kluster beserta alasan berbasis bukti | SEBAGIAN | Analisis kecocokan di bagian 2 | Alasan harus dari bukti Tahap 1 |
| T2-03 | Peta stakeholder dengan peran | SEBAGIAN | Peran aplikasi admin/dosen/penjamin mutu (`backend/app/core/auth.py:24`); mahasiswa objek data | Peta stakeholder dan kewenangan organisasi nyata |
| T2-04 | Minimal dua wawancara stakeholder berbeda | BUTUH LAPANGAN | Belum ada | Wawancara |
| T2-05 | Transkrip atau ringkasan wawancara | BUTUH LAPANGAN | Belum ada | Bergantung T2-04 |
| T2-06 | Kesimpulan berbentuk pengecekan kondisi saat ini | BUTUH LAPANGAN | Belum ada | Kalimat panduan tidak lengkap, lihat bagian 9 |

### 5.4 Tahap 3: Data & System Mapping (P3-4)

| ID | Kewajiban | Status | Bukti | Yang kurang |
|---|---|---|---|---|
| T3-01 | Inventaris sumber data internal prototipe | SIAP | `backend/app/models/submission.py:16-39`, `backend/app/models/material.py:8-31`, `backend/app/models/rps.py:8-27`, `backend/app/api/v1/quiz.py:414` | Tidak ada, sebatas prototipe |
| T3-02 | Inventaris sumber data kampus yang nyata | BUTUH LAPANGAN | Belum ada | LMS, SIAKAD, presensi, dokumen RPS, kuesioner layanan |
| T3-03 | Tiap sumber: format, frekuensi, pemilik, kualitas, cara akses | SEBAGIAN | Format dan cara akses prototipe dapat diisi dari kode | Pemilik, frekuensi, kualitas nyata |
| T3-04 | Peta alur data prototipe | SIAP | CSV → usulan → review → final → AUTO pending → approve → indeks (`backend/app/api/v1/grading.py:88-138`, `backend/app/api/v1/materials.py:270-291`) | Tidak ada, sebatas prototipe |
| T3-05 | Peta sistem as-is sampai ke pengguna | BUTUH LAPANGAN | Belum ada | Alur kerja dosen dan sistem kampus saat ini |
| T3-06 | Checklist: pemilik dan waktu pencatatan tiap sumber | BUTUH LAPANGAN | Waktu pembuatan/persetujuan dan audit ada (`backend/app/models/submission.py:35-39`) | Pemilik sumber dan waktu kejadian lapangan; created_at replay berubah |
| T3-07 | Checklist: kesenjangan data ditandai | SEBAGIAN | Pemetaan soal–CPMK belum ada (`backend/app/core/stats.py:136-149`); reviewed_at dan audit kini tersedia | Kebutuhan data masalah prodi dan panel hasil belajar |
| T3-08 | Instrumen Antroposentris: Likert ke mahasiswa, dosen, pejabat | BUTUH LAPANGAN | Draf instrumen `docs/kuesioner-maturity.md`, belum ada jawaban | Pengumpulan Likert tiga kelompok |
| T3-09 | Instrumen Sistemik: ya/tidak bertingkat | SEBAGIAN | Draf A8 `docs/kuesioner-maturity.md`, bukan hasil ukur | Definisi/rubrik dosen dan konfirmasi pengelola |
| T3-10 | Instrumen Teknologi: ya/tidak bertingkat | SEBAGIAN | Draf A8 `docs/kuesioner-maturity.md`, bukan hasil ukur | Jawaban nyata dan rumus dosen |
| T3-11 | Dokumentasi bukti jawaban (tangkapan layar, panduan pengguna) | SEBAGIAN | Panduan lokal `README.md:23-140`; browser dilaporkan thread tata kelola, log asli hilang | Dokumentasi sistem nyata; jangan menganggap laporan thread sebagai screenshot/log asli |
| T3-12 | Konfirmasi pengelola kampus | BUTUH LAPANGAN | Belum ada | Pengelola kampus |
| T3-13 | Sampling kunjungan kampus untuk verifikasi | BUTUH LAPANGAN | Belum ada | Kunjungan |
| T3-14 | Tabel rata-rata skor tiga perspektif | BUTUH LAPANGAN | Belum ada | Bergantung T3-08 sampai T3-13 |
| T3-15 | Kesimpulan tiga perspektif dan empat level | BUTUH LAPANGAN | Hanya perkiraan bagian 4 | Bergantung T3-14 |
| T3-16 | Penentuan level Digital Twin | SEBAGIAN | Perkiraan bagian 4, pada skala lima level panduan | Bukti koneksi nyata. Hasil template tidak dipakai di sini |
| T3-17 | Kesimpulan level Digital Twin | SEBAGIAN | Perkiraan bagian 4 | Bergantung T3-16 |

### 5.5 Lembar kerja system thinking dan situational awareness (P5-7)

| ID | Kewajiban | Status | Bukti | Yang kurang |
|---|---|---|---|---|
| LK1-01 | Tabel complicated: bagian yang rumit tetapi dapat dipetakan | SIAP | Pipeline dan aturan deterministik: `backend/app/agents/rps_agent.py:450-485`, `backend/app/core/sndikti_catalog.py:710` | Tidak ada, sebatas prototipe |
| LK1-02 | Tabel complex: perilaku yang muncul dari interaksi | BUTUH LAPANGAN | Belum ada | Perilaku dosen dan mahasiswa, keterlibatan, motivasi |
| LK2-E | Elements/boundary: aktor, lokasi, unit analisis, cakupan | SEBAGIAN | Unit analisis: mata kuliah, kuis, submission (`backend/app/models/course.py:8`, `backend/app/models/submission.py:8`) | Lokasi dan aktor nyata, batas sistem |
| LK2-I | Interconnections: relasi data, hierarki | SIAP | Relasi lewat `course_id`, `rps_id`, `quiz_id` (`backend/app/models/quiz.py:12`, `backend/app/models/submission.py:19`), graf (`backend/app/api/v1/knowledge.py:23`). Catatan: tanpa foreign key | Tidak ada, sebatas prototipe |
| LK2-G | Goal/decision rule: tujuan, ambang, prioritas | SIAP | Lulus 60 (`backend/app/core/stats.py:63`), band 75 dan 60 (`backend/app/core/stats.py:224-228`), kepatuhan 85 (`backend/app/api/v1/dashboard.py:260`), bobot katalog (`backend/app/core/sndikti_catalog.py:13`) | Dasar ambang perlu dicocokkan dengan aturan akademik |
| LK2-D | Delay/time | SEBAGIAN | Struktur minggu+1, reviewed_at/audit dan waktu uji E1/E2 tersedia (`backend/app/models/submission.py:35-39`) | Latensi operasional dan panel hasil belajar |
| LK2-F | Feedback: jalur tertutup | SEBAGIAN | Loop katalog; esai/AUTO lewat review (`backend/app/core/grade_review.py:65-87`) | Pengukuran kondisi belajar setelah tindakan |
| LK2-S | Stock-flow dengan satuan stok dan laju | BUTUH BANGUN | Hanya kandidat stok (`backend/app/core/stats.py:279-284`) | Persamaan neraca dan laju, data waktu |
| LK2-a | Apakah semua komponen terpenuhi, dengan bukti | SEBAGIAN | Tabel bagian 3.4 | Pertanyaan ini tentang sistem saat ini, perlu bukti lapangan |
| LK2-b | Apakah D dan F perlu ada, dan mengapa | SEBAGIAN | Argumen dari kode: efek belajar selalu tertunda, jadi tanpa D dan F remedial tidak bisa dinilai | Kondisi D dan F di sistem nyata |
| LK3-01 | Reinforcing loop | SEBAGIAN | AUTO baru bisa diindeks sesudah persetujuan (`backend/app/api/v1/materials.py:270-291`); pemilihan sumber kuis tetap manusia | Bukti penguatan perilaku |
| LK3-02 | Reinforcing negatif / keruntuhan | BUTUH LAPANGAN | Belum ada | Pengamatan lanjutan |
| LK3-03 | Balancing tanpa delay | SIAP | Apply temuan lalu hitung ulang katalog (`backend/app/api/v1/rps.py:1036-1048`) | Tidak ada, sebatas mekanisme prototipe; bukan bukti pengaruh belajar |
| LK3-04 | Balancing respons agresif | BUTUH LAPANGAN | Belum ada. Kode tidak punya parameter kekuatan respons | Pengamatan, atau definisi dari dosen |
| LK3-05 | Balancing dengan delay | SEBAGIAN | Kuis minggu N, penguatan minggu N+1 (`backend/app/agents/auto_material_agent.py:99`) | Efek belum diukur |
| LK3-06 | Rasio fiscal | BUTUH LAPANGAN | Belum ada | Definisi tidak ada di panduan (K6). Data biaya |
| LK3-07 | Sensitivitas | BUTUH BANGUN | Belum ada | Definisi (K6), lalu analisis parameter. Sensitivitas bobot di S35 dan titik sensitivitas di S33 adalah alat keputusan desain, bukan definisi baris ini |
| LK3-08 | Polaritas loop | SEBAGIAN | Tanda bisa ditulis untuk loop di bagian 3.4 | Diagram loop yang disepakati |
| LK3-09 | Polaritas loop panjang | BUTUH LAPANGAN | Belum ada | Definisi (K6), pengamatan antar-semester |
| LK3-10 | Kondisi Γ−W | BUTUH LAPANGAN | Belum ada | Definisi tidak ada di panduan (K6) |
| LK4-L1 | L1 Perception | SIAP | Data yang ditangkap: `backend/app/api/v1/quiz.py:414`, `backend/app/api/v1/dashboard.py:41-46` | Tidak ada, sebatas prototipe |
| LK4-L2 | L2 Comprehension | SIAP | Heatmap dan insight: `backend/app/core/stats.py:167`, `backend/app/core/stats.py:244`, `frontend/src/app/dashboard/analytics/page.tsx:179-181` | Pemahaman per CPMK lemah |
| LK4-L3 | L3 Projection | BUTUH BANGUN | Tidak ada prediksi (`backend/app/core/stats.py:224-228`) | Model proyeksi dan data historis |
| LK4-a | Apakah ketiga komponen perlu ada | SEBAGIAN | Argumen dari L1 dan L2 yang ada, dan L3 yang tidak | Rujukan Endsley belum tersedia lokal |
| LK4-b | Simulasi jika satu komponen ditiadakan | BUTUH BANGUN | Belum ada | Skenario pengujian di lingkungan uji |
| LK5-01 | In the loop: peran, bukti, kapan | SIAP | RPS/kuis dan edit/approve esai, approve AUTO (`backend/app/api/v1/grading.py:206-321`, `backend/app/api/v1/materials.py:270-291`) | Tidak ada, sebatas mekanisme prototipe |
| LK5-02 | On the loop | SEBAGIAN | Dashboard, alert dan pembacaan audit (`backend/app/api/v1/audit.py:1-35`) | Jadwal pemantauan, hak interupsi dan penggunaan nyata |
| LK5-03 | Over the loop | BUTUH LAPANGAN | Admin/penjamin mutu ada di aplikasi (`backend/app/core/auth.py:24`) | Mandat kaprodi/pemilik layanan dan kebijakan nyata |
| LK5-04 | Out the loop | SIAP | MCQ murni dapat final otomatis; esai/AUTO ditahan (`backend/app/api/v1/grading.py:88-112`, `backend/app/agents/auto_material_agent.py:182-184`) | Tidak ada, sebatas identifikasi langkah prototipe; belum otonomi layanan |
| LK5-a | Definisikan hak akses dari peran | SIAP | Admin/dosen/penjamin mutu dan scope mata kuliah (`backend/app/core/auth.py:119-260`, `backend/app/core/auth.py:306-412`) | Matriks prototipe tersedia; kewenangan prodi tetap perlu konfirmasi |
| LK5-b | Jelaskan dengan bukti hak akses | SIAP | Tes akses dan E1: anonim 401, penjamin mutu menilai 403, versi lama 409; `backend/tests/test_autentikasi.py:1-319` | Tidak ada untuk bukti mekanisme prototipe; belum kebijakan kampus |

### 5.6 Tahap 4: Gap Analysis & Problem Definition (P7, P12)

| ID | Kewajiban | Status | Bukti | Yang kurang |
|---|---|---|---|---|
| T4-01 | Bandingkan kondisi saat ini dengan target, SOP, standar | SEBAGIAN | Katalog lokal (`backend/app/core/sndikti_catalog.py:1-21`); aturan agen masih teks tetap (`backend/app/agents/rps_agent.py:34-37`) | Kondisi/SOP kampus dan validasi acuan regulasi |
| T4-02 | Problem statement satu paragraf | BUTUH LAPANGAN | Belum ada | Siapa, apa, seberapa besar, bukti |
| T4-03 | Canvas: Problem | BUTUH LAPANGAN | Belum ada | Dari Tahap 1 sampai 3 |
| T4-04 | Canvas: Data | SEBAGIAN | T3-01 | Data nyata yang tersedia |
| T4-05 | Canvas: AI / Intelligence | SEBAGIAN | Kemampuan yang ada: `backend/app/agents/grading_agent.py:78`, `backend/app/agents/rps_review_agent.py:443-458` | Harus ditentukan dari masalah |
| T4-06 | Canvas: Decision | SEBAGIAN | LK5-01 | Pengambil keputusan nyata |
| T4-07 | Canvas: Action | SEBAGIAN | `backend/app/agents/auto_material_agent.py:77` | Respons yang sampai ke mahasiswa |
| T4-08 | Canvas: Impact | BUTUH LAPANGAN | Belum ada | Indikator dan baseline |
| T4-09 | Checklist: bukti minimal dua sumber | BUTUH LAPANGAN | Belum ada | Triangulasi |
| T4-10 | Checklist: indikator keberhasilan terukur | BUTUH LAPANGAN | Belum ada | Bergantung T4-02 |

### 5.7 Tahap 5: Solution Design (P8)

| ID | Kewajiban | Status | Bukti | Yang kurang |
|---|---|---|---|---|
| T5-01 | Konsep solusi: apa dideteksi, diprediksi, dioptimalkan, dan tindakannya | SEBAGIAN | Deteksi ada (`backend/app/core/stats.py:167`), prediksi tidak | Harus menjawab masalah Tahap 4 |
| T5-02 | Arsitektur awal: sumber data, jaringan, penyimpanan, AI, dashboard, notifikasi | SEBAGIAN | API, SQLite, LLM/RAG, proxy, audit/review dan tiga diagram rancangan tersedia (`backend/app/main.py:12-46`); `docs/rancangan-resiliensi.md` bagian 4 | Notifikasi/distribusi nyata dan deployment kampus |
| T5-03 | KPI dan cara mengukur | BUTUH LAPANGAN | KPI aplikasi ada (`backend/app/api/v1/dashboard.py:430-451`) tetapi bukan KPI masalah | KPI dari Tahap 4 |
| T5-04 | Baseline dan target berdasar maturity | BUTUH LAPANGAN | Belum ada | Bergantung T3-14, T3-16 |
| T5-05 | Checklist: tiap komponen terhubung ke kebutuhan data Tahap 3 | SEBAGIAN | Pemetaan dari kode bisa dibuat | Bergantung T3-07 |
| T5-06 | Checklist: KPI punya baseline | BUTUH LAPANGAN | Belum ada | Bergantung T5-04 |
| T5-07 | Checklist: ada rencana pengujian | SIAP | Alat uji backend dan protokol E1/E2, `docs/rancangan-resiliensi.md` bagian 8; `backend/tests/conftest.py:1-100` | Rencana uji prototipe tersedia; pilot prodi terpisah |

### 5.8 Tahap 6: Data / AI Design (P8)

| ID | Kewajiban | Status | Bukti | Yang kurang |
|---|---|---|---|---|
| T6-01 | Tentukan dataset dan jelaskan sumber | SIAP | Fixture sintetis dan sumber/skenario terdokumentasi dalam `backend/tests/conftest.py:1-100`, manifest E1/E2 dan bahan-ukur Ollama | Tidak ada untuk dataset uji sintetis; data prodi belum terkumpul |
| T6-02 | Pilih metode | SEBAGIAN | Aturan ambang (`backend/app/core/stats.py:224-228`), rubrik LLM (`backend/app/agents/grading_agent.py:101`) | Pembenaran terhadap masalah, metode prediksi |
| T6-03 | Rancang evaluasi: metrik, data uji, batas kelayakan | SEBAGIAN | Metrik mekanisme E1/E2 dan variasi 10×3 jawaban Ollama tersedia | Kesesuaian nilai model dengan dosen, mutu pedagogis dan batas kelayakan belum diukur/disahkan |
| T6-04 | Checklist: metode sesuai masalah dan data | BUTUH LAPANGAN | Belum ada | Bergantung T4-02 |
| T6-05 | Checklist: metrik ditetapkan sebelum membangun | BUTUH BANGUN | Sudah terlanggar untuk fitur lama | Tetapkan metrik sebelum perubahan baru, bagian 7 |

### 5.9 Leverage points (P8-9)

Kolom bukti berisi titik yang bisa dirujuk untuk mengisi tabel. Penentuan LP nyata dan LP sasaran baru sah setelah Tahap 4.

| ID | Kewajiban | Status | Bukti | Yang kurang |
|---|---|---|---|---|
| LP-12 | Numbers | SIAP | Ambang 60, 75, 85 (`backend/app/core/stats.py:63`, `backend/app/api/v1/dashboard.py:260`) | Tidak ada, sebatas prototipe |
| LP-11 | Buffers | SEBAGIAN | Snapshot/restore CLI (`backend/app/core/recovery.py:109-216`), bukan failover LLM | Buffer offline dan cadangan waktu/operator; backup terjadwal/terenkripsi |
| LP-10 | Stock and Flow Structures | BUTUH BANGUN | Lihat LK2-S | Model stok dan aliran |
| LP-09 | Delay | SEBAGIAN | Jeda satu minggu (`backend/app/agents/auto_material_agent.py:99`) | Pengukuran jeda |
| LP-08 | Balancing feedback loops | SEBAGIAN | LK3-03, LK3-05 | Loop hasil belajar tertutup |
| LP-07 | Reinforcing feedback loops | BUTUH LAPANGAN | Belum ada | Bukti perilaku |
| LP-06 | Information Flows | SEBAGIAN | Dashboard dosen (`backend/app/api/v1/dashboard.py:373`) | Informasi tidak sampai ke mahasiswa |
| LP-05 | Rules | SEBAGIAN | Katalog, kunci RPS, sesi/peran dan review (`backend/app/core/auth.py:119-260`) | Mandat/insentif/aturan prodi |
| LP-04 | Self Organization | BUTUH LAPANGAN | Belum ada | Pengamatan kemampuan organisasi |
| LP-03 | Goals | BUTUH LAPANGAN | Belum ada | Tujuan layanan nyata |
| LP-02 | Paradigms | BUTUH LAPANGAN | Belum ada | Wawancara |
| LP-01 | Transcending Paradigms | BUTUH LAPANGAN | Belum ada | Refleksi berbasis bukti |
| LP-A | Jelaskan level LP nyata dan LP sasaran | BUTUH LAPANGAN | Belum ada | Bergantung T4-02 |

### 5.10 Tugas Tahap 6 nomor 2 sampai 5 (P9)

| ID | Kewajiban | Status | Bukti | Yang kurang |
|---|---|---|---|---|
| TG-02 | Usulan intervensi dan sasaran perbaikan | BUTUH LAPANGAN | Belum ada | Bergantung LP-A |
| TG-03 | Beberapa prediksi skenario akibat intervensi | BUTUH BANGUN | Tidak ada model simulasi | Model skenario, data awal |
| TG-04 | Analisis update L2 atau L3, dengan bukti | BUTUH BANGUN | Bergantung LK4-L3 | L3 belum ada |
| TG-05a | Pakai template xlsx asesmen kematangan Digital Twin | SEBAGIAN | Draf xlsx diperbarui: 0,8, Awal; R1/R4 Ya, bagian 4 | Verifikasi tim/dosen K11 dan asesmen prodi terpisah |
| TG-05b | Sebutkan sasaran maturity, dengan bukti saat ini dan harapan | SEBAGIAN | Usulan awal dan draf prototipe di bagian 4 | Bergantung T3-14 dan asesmen batas satu prodi |

### 5.11 Lima dimensi keberlanjutan (P9-10)

| ID | Kewajiban | Status | Bukti | Yang kurang |
|---|---|---|---|---|
| 5P-01 | People | SEBAGIAN | Tujuan terbaca dari fitur (`README.md:3`) | Bukti manfaat nyata |
| 5P-02 | Planet | BUTUH LAPANGAN | Belum ada. Tidak ada data energi atau kertas | Data dan pengukuran |
| 5P-03 | Prosperity | BUTUH LAPANGAN | Belum ada | Data waktu dan biaya |
| 5P-04 | Peace | BUTUH LAPANGAN | Belum ada | Keadilan penilaian, kepercayaan pengguna |
| 5P-05 | Partnership | BUTUH LAPANGAN | Belum ada | Mitra nyata |
| DIM-01 | Individual | BUTUH LAPANGAN | Belum ada | Kuesioner |
| DIM-02 | Social | BUTUH LAPANGAN | Belum ada | Wawancara |
| DIM-03 | Ekonomi | BUTUH LAPANGAN | Biaya LLM tidak dicatat (`backend/app/core/llm.py:127`) | Waktu dan biaya, pencatatan token |
| DIM-04 | Lingkungan | BUTUH LAPANGAN | Belum ada | Asumsi yang dinyatakan |
| DIM-05 | Teknis | SEBAGIAN | Latensi/pemulihan mekanisme lokal diukur pada E1/E2 dan Ollama | Uptime/latensi operasi nyata, akurasi terhadap dosen dan energi belum diukur |
| DMP-01 | Dampak langsung | BUTUH LAPANGAN | Belum ada | Uji di lapangan |
| DMP-02 | Dampak tidak langsung | BUTUH LAPANGAN | Belum ada | Uji di lapangan |
| DMP-03 | Dampak sistemik | BUTUH LAPANGAN | Belum ada | Uji di lapangan |
| TK-01 | Pemilik layanan | BUTUH LAPANGAN | Belum ada | Komitmen tertulis |
| TK-02 | Operator | BUTUH LAPANGAN | Belum ada | Komitmen tertulis |
| TK-03 | Pengembang/pemasok | SEBAGIAN | Penyedia LLM (`backend/app/core/config.py:39-43`), pengembang tampak di git | Bukti komitmen |
| TK-04 | Pengguna/komunitas | BUTUH LAPANGAN | Belum ada | Komitmen pengguna |
| TK-05 | Mitra | BUTUH LAPANGAN | Belum ada | Mitra nyata |

### 5.12 Resiliensi (P10-11)

| ID | Kewajiban | Status | Bukti | Yang kurang |
|---|---|---|---|---|
| RS-01 | Definisikan pengguna | SEBAGIAN | Peran aplikasi admin/dosen/penjamin mutu (`backend/app/core/auth.py:24`) | Pengguna dan penanggung jawab nyata |
| RS-02 | Definisikan fungsi kritis | SEBAGIAN | Kandidat FK1 sampai FK6 di bagian 5.16, mis. penilaian (`backend/app/api/v1/grading.py:23`) | Validasi dari pengguna |
| RS-03 | Definisikan batas kualitas | BUTUH LAPANGAN | Belum ada | Batas waktu dan mutu yang diterima pengguna |
| RS-04 | Definisikan dependensi | SIAP | LLM/RAG/SQLite, cookie/peran, backup/restore (`backend/app/core/config.py:71-82`, `backend/app/core/recovery.py:109-216`); bagian 5.16 | Tidak ada untuk inventaris prototipe; domain kegagalan lapangan belum diketahui |
| RS-05 | Tiga alternatif desain yang memenuhi syarat wajib | SEBAGIAN | Tiga arsitektur A/B/C dan gerbang wajib, `docs/rancangan-resiliensi.md` bagian 2 dan 4 | Syarat wajib prodi dan pemenuhan arsitektur lengkap belum terbukti |
| RS-06 | Bandingkan biaya | SEBAGIAN | Model biaya eksplisit A/B/C di rancangan bagian 5 | Biaya/operator/beban nyata |
| RS-07 | Bandingkan kontinuitas | SEBAGIAN | Kontinuitas dibandingkan sebagai asumsi; E1/E2 mengukur prototipe saja | Uji seluruh arsitektur A/B/C dan domain kegagalan terpisah |
| RS-08 | Bandingkan energi | SEBAGIAN | Model energi dengan asumsi dan batas di rancangan bagian 5 | Pengukuran daya/fungsi berguna dan SCI |
| RS-09 | Bandingkan pemeliharaan | SEBAGIAN | Perbandingan beban pemeliharaan asumsi di rancangan bagian 5 | Kompetensi/biaya operator nyata |
| RS-10 | Eksperimen gangguan 1 di lingkungan uji | SIAP | E1: tiga run independen; 503/manual_review → needs_review → edit/approve skrip dosen. Bukti resiliensi 20261107T010337Z | Lulus mekanisme sintetis; bukan akurasi model atau tinjauan manusia nyata |
| RS-11 | Eksperimen gangguan 2 di lingkungan uji | SIAP | E2: tiga run independen startup aman, CLI backup/verify/restore, sesi dicabut dan replay ID stabil. Bukti resiliensi 20261107T010337Z | Backup terjadwal/terenkripsi dan created_at replay belum tuntas |
| RS-12 | Laporan: diagram arsitektur | SIAP | Diagram kondisi HEAD dan tiga alternatif, rancangan bagian 4 | Tidak ada untuk artefak rancangan; deployment alternatif belum teruji |
| RS-13 | Laporan: skenario | SIAP | Skenario G1–G8 dan protokol/hasil E1/E2, rancangan bagian 3 dan 8 | Batas/durasi tetap asumsi; skenario lain belum seluruhnya dijalankan |
| RS-14 | Laporan: versi konfigurasi | SIAP | Manifest/lock/hash/commit 972ad7b per eksperimen; backend identik HEAD | Tidak ada untuk konfigurasi uji tercatat |
| RS-15 | Laporan: matriks keputusan | SIAP | Matriks 3,50/3,70/3,00 dan skala/bobot asumsi, rancangan bagian 6 | Bobot harus disahkan prodi sebelum menjadi keputusan layanan |
| RS-16 | Laporan: analisis sensitivitas | SIAP | Sensitivitas bobot dan Pareto terhitung, rancangan bagian 6 | Hanya model asumsi, bukan hasil perbandingan arsitektur terpasang |
| RS-17 | Laporan: log pengujian | SIAP | Log, timeline, manifest dan verifikasi resiliensi 20261107T010337Z tersedia | Log mentah thread tata kelola hilang; laporannya sumber sekunder |
| RS-18 | Laporan: rekomendasi | SEBAGIAN | Kandidat B bersyarat, rancangan bagian 9 | Pengesahan stakeholder dan uji seluruh gerbang wajib |
| RS-19 | Tiap kesimpulan terhubung ke bukti, keterbatasan dijelaskan | SIAP | Rujukan hasil mentah, keterbatasan serta rencana ukur di rancangan bagian 8.5/9 | Tidak ada untuk keterlacakan laporan prototipe; bukan bukti operasi |

### 5.12a Kewajiban tambahan dari slide resiliensi

Sumber: `10-TradeOff_Resiliensi.pdf`. S40 memuat tugas kelompok dan S41 memuat rubrik. Definisi fungsi kritis dan layanan minimum ada di S17, dan persyaratan wajib lawan preferensi di S9, jadi label sumbernya mengikuti slide itu. Luaran S40 (diagram, matriks, log, rekomendasi) sudah tercakup RS-12, RS-15, RS-17, dan RS-18, sehingga tidak dihitung ulang.

**Rubrik S41 hanya usulan.** Bobotnya 20/25/30/25 untuk fungsi dan gangguan, alternatif dan trade-off, pengujian resiliensi, serta keberlanjutan dan argumentasi. Slide menyatakan rubrik "usulan pembelajaran yang dapat disesuaikan". Rubrik ini tidak dihitung sebagai baris sampai dosen menetapkannya (K10).

| ID | Kewajiban | Status | Bukti | Yang kurang |
|---|---|---|---|---|
| RT-01 | Pilih jenis kasus: IoT, smart building, atau layanan AI [S40] | SEBAGIAN | Kandidat layanan AI (`backend/app/core/llm.py:127`) | Bergantung K2 dan masalah lapangan |
| RT-02 | Fungsi kritis berdasar dampak yang tidak dapat diterima [S17, S40] | BUTUH LAPANGAN | Kandidat di bagian 5.16 | Dampak ditetapkan pengguna |
| RT-03 | Layanan minimum per fungsi kritis [S17, S30] | BUTUH LAPANGAN | Kandidat di bagian 5.16 | Batas yang diterima pengguna |
| RT-04 | Pisahkan persyaratan wajib dari preferensi [S9] | SEBAGIAN | Kandidat W1 sampai W7 di bagian 5.16 | Pengesahan syarat, aturan kampus |
| RT-05 | Tiap skenario memuat pemicu, fungsi terdampak, kriteria, durasi, cakupan, kondisi awal [S19] | SIAP | Skenario dan enam run independen tercatat; rancangan bagian 3/8.5 | Batas asumsi; E2 verifikasi stabil 5 menit, belum 15 menit skenario umum G4 |
| RT-06 | Indikator fungsi minimum, dengan log dan hasil uji [S30] | SIAP | E1: MCQ bertahan, final esai ditahan; E2 baca/tulis pulih, ringkasan terverifikasi | Tidak ada untuk subset fungsi uji; layanan prodi penuh belum terbukti |
| RT-07 | Indikator waktu pemulihan, dengan timeline insiden [S30] | SIAP | Timeline UTC/monotonic; E1 RTO teknis 905,482–905,607 dtk; E2 305,859–305,922 dtk | Bukan waktu tinjauan manusia/operator nyata |
| RT-08 | Indikator data hilang atau terlambat, dengan timestamp dan ID [S30] | SEBAGIAN | ID/relasi/jawaban stabil, audit/waktu review tersedia; replay mengubah created_at (`backend/app/api/v1/quiz.py:598-611`) | Waktu asal dan keputusan nilai/audit pascabackup belum pulih |
| RT-09 | Target RTO [S31] | BUTUH LAPANGAN | Belum ada. Contoh 30 menit di S31 hipotetis | Target dari dampak gangguan |
| RT-10 | Target RPO [S31] | BUTUH LAPANGAN | Belum ada. Contoh 5 menit di S31 hipotetis | Target dari dampak gangguan |
| RT-11 | Bandingkan hasil uji dengan RTO dan RPO [S31] | SEBAGIAN | RTO/RPO dibandingkan dengan target asumsi 1.800/300 dtk di rancangan bagian 8.5 | Target prodi dari RT-09/10 belum disahkan |
| RT-12 | Energi per fungsi berguna [S32] | BUTUH BANGUN | Belum ada | Alat ukur, unit fungsi mis. per submission dinilai |
| RT-13 | SCI dengan fungsi, batas sistem, dan asumsi yang sama [S32] | BUTUH BANGUN | Batas dan model energi asumsi sudah dinyatakan; rancangan bagian 5 | SCI belum dihitung; perlu daya, intensitas karbon, embodied emissions dan fungsi berguna sebanding |
| RT-14 | Evaluasi berbasis skenario: risiko, titik sensitivitas, titik trade-off [S33] | SEBAGIAN | Risiko/titik sensitivitas/trade-off per skenario dibahas di rancangan bagian 9 | Validasi skenario arsitektur lengkap |
| RT-15 | Matriks berbobot dengan alasan bobot dan skala yang jelas [S34, S35] | SIAP | Skala, alasan bobot dan matriks asumsi, rancangan bagian 6 | Elicitation kebutuhan prodi sebelum dipakai operasional |
| RT-16 | Sensitivitas bobot keputusan [S35] | SIAP | Sensitivitas bobot terhitung, rancangan bagian 6.2; bukan definisi LK3-07 | Tidak ada untuk analisis asumsi; validasi bobot prodi terpisah |
| RT-17 | Pemeriksaan Pareto antar-alternatif [S35] | SIAP | Pareto tiga alternatif dan batas kriterianya, rancangan bagian 6.3 | Tidak ada untuk perhitungan asumsi |
| RT-18 | Uji pemulihan: sinkronisasi, duplikasi, urutan, ID unik [S38] | SEBAGIAN | E2 ID/jawaban/relasi stabil, ulang CSV tambah 0, duplikasi 0 | created_at berubah dan riwayat penilaian/audit pascabackup tidak ikut replay |
| RT-19 | Uji restore, bukan hanya keberadaan backup [S24, S38] | SIAP | E2 menguji CLI verify/restore, integritas, manifest, lock, sesi dan baca/tulis | Tidak membuktikan enkripsi/jadwal/domain backup terpisah |
| RT-20 | Manfaat dan konsekuensi keberlanjutan tiap alternatif [S13, S40] | SEBAGIAN | Manfaat/konsekuensi A/B/C berdasarkan asumsi, rancangan bagian 5 dan 9 | Dampak keberlanjutan nyata |
| RT-21 | Risiko residual tiap alternatif [S37, S40] | SEBAGIAN | Risiko residual per alternatif tercatat, rancangan bagian 9 | Validasi probabilitas/dampak dan semua gerbang arsitektur |
| RT-22 | Tata kelola insiden: pemilik layanan, operator, jalur eskalasi [S39] | BUTUH LAPANGAN | Belum ada | Peran nyata di prodi |
| RT-23 | Prosedur pengambilalihan, restore, komunikasi status [S39] | SEBAGIAN | Runbook restore/komunikasi/eskalasi usulan dan CLI teruji, rancangan bagian 8/9 | Pengambilalihan lintas lokasi, latihan operator dan komunikasi nyata |
| RT-24 | Tinjau penyebab dan ubah desain setelah perbaikan diuji [S39] | SIAP | Perbaikan B1–B18/tata kelola diikuti regresi dan uji ulang E1/E2; rancangan bagian 8.4–8.5 | Proses pembelajaran insiden organisasi nyata belum diukur |

### 5.13 Tahap 7: Finalization & UAS (P12)

| ID | Kewajiban | Status | Bukti | Yang kurang |
|---|---|---|---|---|
| T7-01 | Presentasi alur Problem sampai Impact | BUTUH LAPANGAN | Belum ada | Bergantung seluruh tahap |
| T7-02 | Demo prototipe | SIAP | Demo lokal sintetis/Ollama, lint/build di bukti lokal; alur browser terbaru dilaporkan thread tata kelola (log asli hilang) | Demo UAS tetap perlu latihan; bukan bukti pilot prodi |
| T7-03 | Jawaban atas pertanyaan penguji | SEBAGIAN | Bagian 3 dan 7 dokumen ini | Hasil lapangan |
| T7-04 | Paket akhir: seluruh artefak | BUTUH LAPANGAN | Belum ada | Bergantung seluruh tahap |
| T7-05 | Paket akhir: kode | SEBAGIAN | Kode/README/dependensi selaras, seed sintetis, pycache tidak terlacak (`README.md:5-13`) | Paket final tanpa riwayat data lama, penanganan minimatch dev |
| T7-06 | Paket akhir: data uji | SIAP | Data sintetis, fixture, bahan-ukur, manifest dan replay E1/E2 terdokumentasi | Tidak ada untuk data uji prototipe; bukan dataset kampus |
| T7-07 | Paket akhir: presentasi | BUTUH LAPANGAN | Belum ada | Bergantung T7-01 |
| T7-08 | Checklist: cerita utuh, demo berjalan, repo lengkap | BUTUH LAPANGAN | Belum ada | Bergantung seluruh tahap |

### 5.14 Aturan bukti (P12)

| ID | Kewajiban | Status | Bukti | Yang kurang |
|---|---|---|---|---|
| BK-01 | Alur Observe, Collect, Analyze, Identify Gap, Propose | BUTUH LAPANGAN | Repo dimulai dari Propose | Urutan harus dipulihkan, bagian 7 |
| BK-02 | Dapat diverifikasi pihak lain | SEBAGIAN | Rujukan kode dan riwayat git bisa diverifikasi | Bukti lapangan |
| BK-03 | Jelas sumber dan waktunya | SEBAGIAN | Commit/manifest/waktu uji tersedia; `created_at` replay berubah | Sumber/waktu lapangan dan waktu asal rekaman replay |
| BK-04 | Relevan dengan masalah | BUTUH LAPANGAN | Belum ada | Bergantung T4-02 |
| BK-05 | Minimal dua sumber (triangulasi) | BUTUH LAPANGAN | Belum ada | Observasi dan wawancara |
| BK-06 | Terdokumentasi rapi | SEBAGIAN | Dokumen ini | Berkas bukti lapangan |

### 5.15 Canvas analisis bagian 6 (P12)

Canvas ini sama dengan T4-03 sampai T4-08, sehingga tidak dihitung dua kali dalam jumlah baris.

### 5.16 Resiliensi prototipe setelah perbaikan

Pemilihan final kasus/fungsi dan batas mutu tetap menunggu lapangan. Hasil teknis di bawah diperiksa terhadap HEAD dan bukti lokal; tidak lagi perkiraan seluruhnya. Rancangan lengkap ada di `docs/rancangan-resiliensi.md`, terutama bagian 8.5 dan 9.

| Dependensi / kontrol | Perilaku HEAD | Bukti kode |
|---|---|---|
| LLM lokal | Pengukuran memakai Ollama `qwen3.5:9b`, tanpa provider berbayar. JSON berskema, satu retry; tidak ada failover invoke. Default cloud masih bisa dipilih jika tidak dioverride | `backend/app/core/config.py:39-43`, `backend/app/core/llm.py:95-145`, `backend/app/core/llm_json.py:18-73` |
| SQLite/startup | DB hilang ditolak, tanpa seed otomatis; init/seed eksplisit; DB repo dilindungi | `backend/app/core/database.py:46-106`, `backend/app/main.py:49-80` |
| Backup/restore CLI | Snapshot online, checksum/manifest/integritas, 0600, lease, verifikasi restore dan pencabutan sesi; jadwal/enkripsi/retensi/domain terpisah belum ada | `backend/app/core/recovery.py:109-216`, `backend/app/cli.py:85-95` |
| Replay | Ekspor membawa ID; tanpa ID UUID5 kuis/identitas sintetis; konflik ditolak. Jawaban/relasi pulih, bukan seluruh metadata/riwayat | `backend/app/api/v1/quiz.py:469-535`, `backend/app/api/v1/quiz.py:598-611` |
| RAG/embedding | Pilihan Ollama `bge-m3` CPU atau Hugging Face; indeks disiapkan terpisah. Status indeks setelah hasil nyata; pencarian gagal 503; AUTO perlu approve | `backend/app/core/rag.py:8-62`, `backend/app/api/v1/materials.py:185-197`, `backend/app/api/v1/knowledge.py:243-265` |
| PDF | reportlab masih diimpor dari dashboard saat startup; isolasi fitur tambahan belum menyeluruh | `backend/app/api/v1/dashboard.py:6`, `backend/app/services/pdf_generator.py:1-5` |
| Frontend/backend | Proxy satu origin meneruskan sesi HttpOnly; galat koneksi API ditangani. Lint/build lulus pada laporan frontend | `frontend/src/lib/api.ts:1-18`, `frontend/src/app/api/backend/[...path]/route.ts:1-46` |
| Manusia | Esai usulan dan AUTO memerlukan persetujuan. Peran aplikasi bukan bukti ketersediaan/mandat dosen atau operator kampus | `backend/app/api/v1/grading.py:206-321`, `backend/app/api/v1/materials.py:270-291` |

Kandidat fungsi tetap FK1 penyimpanan jawaban/nilai (kritis), FK2 penilaian (MCQ deterministik, esai dengan review), FK3 analitik final, FK4 kuis manual/AI, FK5 RPS/katalog, FK6 RAG/materi/PDF. Tingkat kritis, layanan minimum, RTO dan RPO prodi belum disahkan; angka target di rancangan adalah asumsi.

| Skenario | Hasil yang dapat dinyatakan | Batas |
|---|---|---|
| G1 / E1, LLM mati | Tiga run independen: HTTP 503, masing-masing 100 manual_review tanpa final salah, 200/200 keputusan MCQ benar; retry menjadi usulan, edit/approve skrip dosen menghasilkan 100 final per run, audit/versi/akses diperiksa | Pemulihan memakai tiruan, bukan qwen nyata; RTO teknis 905,482–905,607 dtk dan RTO alur skrip 1208,452–1208,572 dtk, bukan waktu penilai manusia |
| G4 / E2, DB hilang | Tiga run independen: startup exit 3 tanpa DB baru; backup/verify/restore exit 0; restore saat aktif ditolak; cookie lama 401; replay tambah 3 lalu 0, ID/relasi stabil, duplikasi 0 | RTO 305,859–305,922 dtk termasuk stabil 5 menit; RPO sebelum replay 180,154–180,203 dtk; tiga jawaban sementara hilang/run lalu pulih. created_at tiga rekaman berubah/run; riwayat nilai/audit pascabackup tidak dipulihkan |
| G2, JSON invalid | Validator dan tes menolak keluaran rusak/tidak lengkap sebelum jadwal disimpan; RPS tervalidasi dilindungi | Bukti regresi, bukan uji gangguan arsitektur penuh (`backend/app/api/v1/rps.py:253-263`, `backend/tests/test_ollama_lokal.py:1-35`) |
| G3/G5/G6/G7 | Tes transaksi/CSV/indeks dan galat frontend tersedia; jangan menganggap semuanya sudah diuji sebagai eksperimen durasi penuh | PDF/embedding/offline klien dan kehilangan host/lokasi belum dicakup E1/E2 |

Sumber hasil: `docs/bukti-uji/resiliensi-20261107T010337Z/ringkasan-terverifikasi.json`. Enam run lulus mekanisme inti; 0 upaya koneksi eksternal hanya untuk proses harness itu. Uji dilakukan pada `972ad7b`, backend identik HEAD. Target pembanding 1.800/300 dtk adalah asumsi, bukan janji layanan. Hasil historis sebelum tata kelola tetap ada di rancangan bagian 8.4 dan tidak dipakai sebagai perilaku HEAD.

| ID | Kandidat syarat privasi/tata kelola | Kondisi sekarang | Yang belum selesai |
|---|---|---|---|
| W1 | Akses hanya pengguna berhak | Mekanisme sesi/peran/scope ada dan diuji (`backend/app/core/auth.py:119-260`) | Matriks hak sah/izin kampus |
| W2 | Identitas/jawaban tidak ke LLM eksternal | Eksperimen memaksa Ollama; prompt tetap memuat teks bebas (`backend/app/agents/grading_agent.py:85-113`) | Kebijakan egress/klasifikasi deployment; default kode bukan lokal eksklusif |
| W3 | Data nyata tidak masuk repo | Snapshot/seed sintetis; DB tidak diubah | Riwayat lama perlu dikecualikan dari paket akhir |
| W4 | Minimisasi data | Kolom yang tersedia diketahui (`backend/app/models/student.py:13-15`) | Kebutuhan kolom dan izin prodi |
| W5 | Hapus terkendali/retensi | Hapus kini melalui autentikasi/scope/audit | Retensi kampus dan backup terenkripsi/terjadwal |
| W6 | Nilai diperiksa/dikoreksi manusia | Edit dan approve ber-versi tersedia (`backend/app/api/v1/grading.py:206-321`) | Akurasi/keadilan/kesesuaian dosen dan beban review nyata |
| W7 | Akses/perubahan tercatat | Mutasi, login gagal, penolakan dan galat diaudit (`backend/app/core/audit.py:76-183`) | Audit berkala organisasi; log bukan antirusak terhadap pemilik DB |

W1/W6/W7 tidak lagi dicatat sebagai fitur yang belum dibangun. Pemenuhan kebijakan kampus tetap belum disahkan. A/B/C di rancangan adalah alternatif desain, bukan tiga deployment yang telah lulus seluruh syarat. Kandidat B bersyarat tetap, bobot/skor tetap asumsi.

---

## 6. Template dan sumber acuan

**Template tersedia** di `docs/template-asesmen-kematangan-digital-twinISOIEC 30186 - 2025.xlsx`, dengan lembar Ringkasan, Petunjuk, Identitas, dan Rubrik serta 25 indikator. File asli tidak diubah. Lembar Petunjuk menyatakan template ini adaptasi, bukan salinan resmi standar, dan keluarannya untuk roadmap, bukan sertifikasi.

**Draf** ada di `docs/draf-asesmen-kematangan-prototipe.xlsx`. Rumus, format, validasi, dan grafik dipertahankan, dengan penyesuaian tinggi baris supaya catatan terbaca. Kedua file diabaikan git; hanya draf yang disunting dan tidak ada commit. Struktur, 68 rumus, validasi, format dan grafik template dipertahankan; nilai cache dihitung ulang dan dibuka kembali dengan openpyxl.

**Materi resiliensi**

| File | Status sumber | Pemakaian |
|---|---|---|
| `10-TradeOff_Resiliensi.pdf` | Materi kuliah, 45 slide | Dasar baris 5.12a |
| `Designing a Resilient and Sustainable System.pdf` | Catatan otomatis, lebih lemah dari slide | Pelengkap saja |
| `Trade-offs and Resilience of IT Systems.pdf` | Catatan otomatis, lebih lemah dari slide | Pelengkap saja |

Jika berbeda, slide yang dipakai. Contohnya, catatan menyebut RTO mengukur waktu pemulihan, sedangkan S31 menyebutnya target. Catatan juga menyebut perbandingan alternatif belum selesai di transkrip, jadi tidak ada kesimpulan yang bisa diambil darinya.

**Sumber acuan bagian 7 panduan: masih tidak ada secara lokal.** Pencarian pada analisis awal lewat nama file dan judul pada dua halaman awal PDF di `~/Documents` dan `~/Downloads` (PDF di bawah 40 MB) tidak menemukan Imbar dkk. 2025, Wang dkk. 2024, Meadows 2008, Sterman 2000, Sterman 1994, Sterman 2006, Endsley 1995, atau Endsley 2015. Tidak ada yang diunduh, sesuai brief. Rujukan di slide (NIST, ISO, ATAM) juga tidak tersedia lokal.

Yang paling dibutuhkan adalah Imbar dkk. 2025, karena memuat definisi level Sistemik dan instrumen.

---

## 7. Risiko: solusi lebih dulu daripada masalah

Panduan berprinsip "mulailah dari masalah nyata dan bukti lapangan, bukan dari teknologi" (P1). Repo ini kebalikannya: dibuat April sampai Juni 2026 untuk II5003 (`README.md:3`), sedangkan PDF panduan dibuat 2 November 2026.

| Risiko | Akibat | Tingkat |
|---|---|---|
| Observasi bias: tim hanya melihat masalah yang cocok dengan fitur | Melanggar checklist T1-08, dan masalah terasa dibuat-buat saat diuji | Tinggi |
| Pemakaian ulang karya II5003 | Bisa bermasalah secara akademik jika tidak diizinkan dosen | Tinggi, perlu dijawab dulu |
| Metrik dibuat setelah fitur | Melanggar checklist T6-05, dan evaluasi jadi tidak jujur | Tinggi |
| Prototipe dinilai seakan-akan layanan kampus | Skor maturity menggelembung | Sedang |
| Masalah nyata ternyata bukan yang diselesaikan repo | Sebagian besar kode tidak relevan | Sedang, dan hasil ini sah |
| Klaim README ikut masuk artefak | Runtuh saat verifikasi (bagian 3.1) | Sedang |

Cara menangani:

1. **Tanya dosen lebih dulu** apakah EduCopilot boleh dipakai ulang (K2). Jika tidak, Tahap 1 sampai 6 tetap bisa berjalan, dan repo hanya menjadi rujukan pembelajaran.
2. **Nyatakan asal repo di setiap artefak**: dibuat untuk II5003, berstatus kandidat solusi, belum diuji di kampus.
3. **Lakukan Tahap 1 dan 2 secara buta.** Pedoman observasi dan wawancara tidak menyebut EduCopilot atau AI. Pertanyaan bersifat terbuka tentang pekerjaan, hambatan, dan waktu.
4. **Pisahkan as-is dan to-be** di semua tabel. Kondisi saat ini adalah kampus, bukan repo.
5. **Tulis kriteria gugur sebelum observasi.** Contoh: jika tidak ada masalah prioritas yang terkait pembelajaran, tim berganti kluster atau hanya memakai sebagian kode.
6. **Bekukan repo sebagai baseline**, misalnya dengan tag, sebelum perubahan fitur baru.
7. **Tetapkan metrik sebelum membangun lagi** dan commit dokumennya lebih dulu, sehingga riwayat git menjadi bukti urutan.
8. **Sertakan satu alternatif desain tanpa LLM** di RS-05, supaya perbandingannya jujur.
9. **Laporkan fitur yang gugur.** Hasil "fitur X tidak menjawab masalah" adalah temuan valid.

---

## 8. Daftar pekerjaan prioritas

Urutan besar: keputusan, lapangan buta, definisi masalah, desain dan metrik, bangun, uji, final. Status A di bawah memisahkan penyelesaian teknis prototipe dari pengesahan kebijakan dan pengukuran prodi. F1–F13 seluruhnya masih menunggu lapangan; pedoman/instrumen kosong bukan hasil pengumpulan.

### (c) Keputusan pengguna, dikerjakan paling awal

| ID | Keputusan | Memblokir |
|---|---|---|
| K1 | Apakah kluster Smart Campus (Smart Education) diizinkan, mengingat Tahap 1 dan 2 menyebut 13 kluster? | Semua tahap |
| K2 | Apakah repo II5003 boleh dipakai ulang untuk KS5102? | Semua pekerjaan bangun |
| K3 | Batas sistem. **Sudah diputuskan: satu prodi.** Prodi mana yang dipilih masih perlu ditetapkan | Asesmen resmi, F1 |
| K4 | Keanggotaan tim belum dikonfirmasi; roster sudah sintetis dan bukan daftar tim | Pembagian kerja lapangan |
| K5 | Minta artikel Imbar dkk. 2025 dan sumber acuan lain ke dosen. Template sudah ada | Definisi level Sistemik, A8 |
| K6 | Minta definisi Rasio fiscal, Sensitivitas, Polaritas loop panjang, Kondisi Γ−W | LK3 |
| K7 | Di mana repositori Living Lab, dan kapan tenggat tiap artefak? | Pengumpulan |
| K8 | Data apa yang akan dipakai, dan bagaimana izin atau persetujuan penggunaannya? | Tahap 6, F9 |
| K9 | Uji/prototipe memakai Ollama lokal qwen3.5:9b tanpa provider berbayar; anggaran operasional belum diputuskan | Pilot dan operasi nyata |
| K10 | Apakah rubrik S41 dipakai, dan apakah tugas S40 sama dengan tugas nomor 7 panduan? | Bentuk laporan resiliensi |
| K11 | Untuk template: tanpa bukti bernilai 0 (rumus) atau 1 (Petunjuk), dan apakah tampilan data demo cukup untuk P1? | Skor draf |

Keputusan yang sudah ada: batas satu prodi, kuis/RPS turunan slide dibiarkan, uji tanpa LLM berbayar melalui Ollama lokal. K1/K2/K5/K6/K7/K8/K10/K11 masih terbuka; tidak ada keputusan dosen atau izin lapangan yang diasumsikan.

### (b) Dikerjakan tim di lapangan

| ID | Pekerjaan | Bergantung pada |
|---|---|---|
| F1 | Urus izin, tentukan lokasi dan narasumber | K1, K3 |
| F2 | Observasi: foto, catatan, checklist | F1, A7 |
| F3 | Susun minimal 5 masalah dengan dampak | F2 |
| F4 | Minimal 2 wawancara stakeholder berbeda | F1, A7 |
| F5 | Inventaris sistem dan data kampus, peta as-is | F4 |
| F6 | Sebar kuesioner Likert ke tiga kelompok | A8 |
| F7 | Jawab ya/tidak bertingkat bersama pengelola, minta dokumentasi | F5, A8 |
| F8 | Verifikasi oleh pengelola, sampling kunjungan | F7 |
| F9 | Kumpulkan data nyata atau historis, dengan izin | K8, F5 |
| F10 | Kumpulkan SOP dan target, tulis problem statement dan canvas | F3 sampai F7 |
| F11 | Pilot terbatas di kampus, ukur KPI terhadap baseline | A13, A14 |
| F12 | Bukti komitmen tata kelola dan mitra | F4 |
| F13 | Gali dari pengguna: fungsi yang tidak boleh berhenti, batas tunggu, kehilangan data yang masih diterima, peran saat insiden. Pertanyaan tetap netral | F4 |

### (a) Bisa dikerjakan AI atau kode

| ID | Pekerjaan | Bergantung pada | Kapan |
|---|---|---|---|
| A1 | Anonimkan DB dan seed, buang `__pycache__` terlacak | Tidak menunggu identitas tim; seed sintetis | Selesai, kecuali riwayat git |
| A2 | Selaraskan README dengan kode (bagian 3.1) dan samakan daftar dependensi | Tidak ada | Selesai: README/dependensi diselaraskan; batas embedding default tetap dijelaskan |
| A3 | Uji jalan penuh aplikasi tanpa LLM berbayar, sebagai persiapan demo | Tidak ada | Selesai untuk demo sintetis lokal: bukti Ollama; pemasangan/browser terbaru hanya laporan thread, log asli hilang |
| A4 | Alat uji: pytest dan LLM tiruan, tes jalur inti | Tidak ada | Selesai: 249 lulus pada bukti backend identik HEAD; jaringan diblok/DB sementara |
| A5 | Autentikasi, peran, dan hak akses | Kebijakan prodi K2/K3 tetap terpisah | Selesai teknis: sesi, tiga peran, scope dan tes; bukan mandat organisasi |
| A6 | Log audit tersimpan: pelaku, waktu, versi, model | A5 | Selesai teknis: audit transaksional, versi/model/pelaku/waktu; belum audit berkala/antirusak |
| A7 | Draf pedoman observasi dan wawancara netral | K1 | Selesai: `docs/pedoman-lapangan-ganai.md` |
| A8 | Draf kuesioner Likert dan pertanyaan ya/tidak | K5 | Draf selesai di docs/kuesioner-maturity.md; final instrumen/rumus menunggu dosen |
| A9 | Isi draf baris SIAP: inventaris, peta alur data, I, G, L1, L2, in/out loop | K3 | Draf selesai di docs/draf-lembar-kerja.md dan diperbarui; prodi tetap kosong |
| A10 | Tinjauan manusia atas nilai: ubah nilai, status perlu review, gerbang persetujuan materi `AUTO` | Kebijakan penilaian prodi tetap menunggu F10 | Selesai teknis: edit/approve esai dan gerbang AUTO, kontrol versi dan peran |
| A11 | Tetapkan metrik dan batas kelayakan, commit sebelum membangun | F10 | Setelah Tahap 4 |
| A12 | Pemetaan soal ke CPMK, ganti progres placeholder, simpan feedback esai | A11 | Sebagian: feedback/per-soal sudah disimpan; pemetaan CPMK dan progres spesifik belum |
| A13 | Tutup loop: ukur efek remedial, hidupkan atau hapus Remedial Agent, catat waktu kejadian | A11, A12 | Belum tuntas: waktu audit/review ada; efek remedial, data panel dan agen stub belum diselesaikan |
| A14 | Bangun L3: prediksi risiko dan what-if, sesuai sasaran maturity | A11, F9 | Setelah data ada |
| A15 | Model stock-flow dan skenario intervensi | F10 | Setelah Tahap 4 |
| A16 | Tiga alternatif desain, eksperimen gangguan, log, matriks, sensitivitas bobot, risiko residual | A4, A6, K9; F13 untuk keputusan final | Sebagian: A/B/C, matriks/sensitivitas, risiko dan E1/E2 tersedia; asumsi/batas prodi serta deployment lengkap belum |
| A17 | Asesmen template batas satu prodi, susun presentasi dan paket akhir | F8, semua | Draf xlsx dinilai ulang 0,8 Awal; asesmen resmi/paket final menunggu lapangan |
| A18 | Tim memeriksa draf template per indikator dan membuka bukti `file:baris` | K11 | Pemeriksaan otomatis rujukan/rumus selesai; verifikasi tim/dosen belum |
| A19 | Lingkungan uji gangguan: LLM tiruan, salinan DB sintetis, skrip backup dan restore, pencatat waktu | A4 | Selesai untuk E1/E2: DB sintetis terpisah, tiruan dan CLI backup/restore teruji |
| A20 | Perbaiki temuan ketahanan jika terbukti: tanda esai gagal, penjaga jadwal kosong, status indeks, perpindahan penyedia, peringatan DB baru | A19 | Perbaikan B1–B18 dan tata kelola diuji ulang; failover invoke tetap tidak ada (Ollama dipilih eksplisit); sisa jadwal/enkripsi backup, metadata replay dan mutu model |

### Urutan dan ketergantungan

1. **Minggu ini:** K1, K2, K4, K5, K6, K7, K10, K11, dan pemilihan prodi. A2/A3/A4/A9/A19 sudah memiliki hasil prototipe; A18 menunggu tim/dosen. K8 dan anggaran operasi K9 tetap perlu diputuskan.
2. **Fase lapangan:** F1, F2, F3, F4, F5, F13. A5/A6 sudah ada secara teknis; draf A8 menunggu finalisasi dosen.
3. **Fase ukur:** F6, F7, F8, lalu tabel maturity dan lembar kerja.
4. **Fase definisi:** F10, Tahap 4, leverage point. Di sini kriteria gugur diperiksa.
5. **Fase desain:** A11, Tahap 5, Tahap 6, A15.
6. **Fase bangun dan uji lanjutan:** sisa A12, A13, A14, validasi A16/A20, F9, F11. A10 dan mekanisme inti A20 sudah teruji sintetis.
7. **Fase akhir:** A17, F12, Tahap 7.

Jalur kritis: K1 dan K2, lalu F1 sampai F5, lalu F10, lalu A11, lalu A13 dan A14, lalu F11, lalu A17. Pekerjaan kode tidak memperpendek jalur ini. Bottleneck-nya kerja lapangan.

---

## 9. Ketidakjelasan di panduan

| Lokasi | Masalah | Tindakan |
|---|---|---|
| P1 | Merujuk bukti ke "bagian 6", padahal aturan bukti ada di bagian 5 | Pakai bagian 5 |
| P1-3 | 12 dan 13 kluster di awal, hanya 13 di Tahap 1 dan 2 | K1 |
| P3 | Kalimat "harus disimpulkan ke dalam bentuk pengecekan" terputus | Tanya dosen |
| P4 | Artefak Tahap 3 hanya menyebut tabel maturity, padahal pekerjaannya juga inventaris dan peta sistem | Kumpulkan semuanya |
| P4 | Definisi level Sistemik tidak diberikan | K5 |
| P6-7 | Rasio fiscal, Sensitivitas, Polaritas loop panjang, Kondisi Γ−W tidak didefinisikan. Sensitivitas di S33 dan S35 adalah alat keputusan desain, bukan definisi ini | K6 tetap terbuka |
| P8 | Tahap 5 menyebut masalah Tahap 1, padahal rumusan masalah ada di Tahap 4 | Pakai Tahap 4 |
| P8 | Tugas Tahap 6 mencakup resiliensi dan keberlanjutan yang besar, tetapi artefaknya hanya disebut desain data dan model | Tanya bentuk pengumpulannya |
| P9 | Nama template di panduan memuat `/`, sedangkan file yang diterima memakai `ISOIEC` | Terselesaikan, file sudah ada |
| P5 dan template | Lima level panduan berbeda dari skala tingkat dan aspek template | Isi terpisah (bagian 4) |
| Template | Petunjuk berkata tanpa bukti skor tetap 1, sedangkan rumus memberi 0 | Draf mengikuti rumus, K11 |
| P10-11 dan S40 | Daftar laporan panduan lebih panjang dari luaran S40 | Pakai daftar panduan, K10 |
| S41 | Rubrik 20/25/30/25 disebut usulan | Jangan dianggap final, K10 |

---

## Lampiran: pembaruan dan verifikasi

Hasil pemeriksaan akhir: **312 kemunculan rujukan (166 rujukan unik, 51 berkas), 0 galat rentang/berkas; 182 ID kewajiban unik; 476 sel berlabel; 68 rumus dihitung dan dibuka ulang, 0 error rumus.** Hanya R1/R4 berubah Ya/Tidak; cache grafik cocok tingkat [1, 0, 1, 1, 1].

Batas pemeriksaan: kode HEAD dan semua rujukan file:baris pada dua markdown serta sel teks workbook diperiksa otomatis terhadap isi lokal; rujukan kode juga dicocokkan ke `git show HEAD:path`. Nomor/rentang harus ada, tidak terbalik, dan kutipan diperiksa pada fungsi yang relevan. Pemeriksaan keberadaan baris tidak menggantikan pembacaan makna klaim.

- Matriks bagian 5 dihitung dari 182 ID unik; perubahan status tercantum di bawah. Baris pekerjaan K/F/A dan tabel ringkasan tidak dihitung sebagai kewajiban baru.
- Label lembar kerja dihitung dari setiap sel tabel (termasuk header, kecuali pemisah). Setiap sel tepat satu label. Ringkasan label berada di awal draf lembar kerja, sehingga tidak ikut dihitung.
- Workbook dibongkar hanya dalam folder `mktemp -d`, disunting pada XML salinan supaya formula/struktur/style/validasi/grafik tetap. Semua rumus dihitung ulang memakai mesin `formulas`, kemudian workbook dibuka ulang dengan `openpyxl` dalam mode formula dan data_only; hasil dibandingkan dengan hitungan berjenjang independen. Tidak ada error rumus. Tidak mengklaim inspeksi visual Excel/LibreOffice.
- DB repo tetap SHA-256 `d078bef9c3ac7fa38872f11b9dd310b3683ed68b76689ef45f173e4f40e7d3a8`; snapshot DB tidak dimigrasi. Hanya dua markdown dan draf xlsx ini berubah; template/PDF/rancangan resiliensi/kode tidak disentuh. Tidak commit, push, atau pindah branch.
- E1/E2, backend 249 tes dan laporan frontend adalah bukti eksekusi sebelumnya pada versi tercatat, bukan pengujian aplikasi baru oleh pembaruan dokumen ini. Backend versi uji identik HEAD; frontend HEAD memuat perbaikan lint/dependensi. Angka laporan tata kelola tetap berstatus laporan thread tanpa log asli.

### Perubahan status kewajiban

| Sebelum | Sesudah | ID kewajiban |
|---|---|---|
| BUTUH BANGUN | SIAP | LK5-a, LK5-b, T5-07, RS-10, RS-11, RS-15, RS-16, RS-17, RS-19, RT-06, RT-07, RT-15, RT-16, RT-17, RT-19, RT-24, T7-06 |
| SEBAGIAN | SIAP | T6-01, RS-12, RS-13, RS-14, RT-05, T7-02 |
| BUTUH BANGUN | SEBAGIAN | T6-03, RS-05, RS-07, RS-18, RT-11, RT-14, RT-18, RT-21, RT-23 |
| BUTUH LAPANGAN | SEBAGIAN | RS-06, RS-08, RS-09, RT-20 |

### Yang tetap menunggu lapangan atau dosen

Observasi/foto/checklist minimal lima masalah, minimal dua wawancara stakeholder, triangulasi, inventaris/SOP/baseline nyata, Likert tiga kelompok, konfirmasi pengelola, izin data, pemilik/operator/eskalasi/retensi, target layanan, pilot dan manfaat 5P tetap [BUTUH LAPANGAN]. Skor maturity prodi belum ada. Kesesuaian nilai model dengan dosen dan beban/waktu review manusia harus diukur, bukan disimpulkan dari skor fixture.

Dosen masih perlu memutuskan izin Smart Education dan pemakaian ulang karya, definisi/rumus Sistemik, empat istilah loop, aturan skor minimum/P1 template, rubrik S41, format dan repositori/tenggat. Instrumen A8 dan pedoman lapangan sudah siap sebagai draf, belum menjadi jawaban atau pengesahan. Pekerjaan bangun yang tersisa meliputi pemetaan CPMK, loop hasil belajar, L3/stock-flow, SCI, backup terjadwal/terenkripsi, pemulihan metadata/riwayat dan skenario arsitektur yang belum diuji.
