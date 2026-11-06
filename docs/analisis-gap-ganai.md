# Analisis Gap: Repo EduCopilot vs Panduan Tugas GanAI (KS5102)

Tanggal analisis: 6 November 2026.
Panduan: `Panduan Tugas Mahasiswa GanAI - SO.pdf` (13 halaman, dibaca seluruhnya termasuk gambar di hlm. 5).
Repo: kode dianalisis pada commit `ef9694d` (branch `main`). Pembaruan ini dibuat di branch `docs/analisis-gap-ganai` (`477d9bc`), dengan kode aplikasi yang sama.
Materi tambahan: template asesmen kematangan, slide `10-TradeOff_Resiliensi.pdf` (45 slide), dan dua catatan otomatis.

Cara baca rujukan: `path:baris` menunjuk ke kode di repo. `P5` berarti halaman 5 panduan. `S31` berarti slide 31 di `10-TradeOff_Resiliensi.pdf`.

Batas analisis: kode tidak dijalankan sebagai aplikasi dan tidak ada LLM yang dipanggil. `backend/educopilot.db` dibaca lewat salinan di luar repo. Yang dieksekusi hanya katalog SN-Dikti yang deterministik terhadap salinan DB itu, dan rumus template terhadap draf xlsx.

---

## 1. Ringkasan eksekutif

**Jawaban singkat.** Repo ini memberi modal bagus untuk paruh kedua tugas (solusi, arsitektur, demo), tetapi hampir tidak memberi apa pun untuk paruh pertama (masalah nyata, bukti lapangan). Panduan mewajibkan paruh pertama dikerjakan lebih dulu. Dari 182 kewajiban yang didaftar, hanya 12 yang bisa diisi sekarang dari repo, dan itu pun hanya menggambarkan prototipe, bukan kondisi kampus.

| Status | Jumlah baris | Arti singkat |
|---|---:|---|
| SIAP | 12 | Bisa diisi sekarang dari kode atau data repo |
| SEBAGIAN | 56 | Repo memberi sebagian |
| BUTUH LAPANGAN | 78 | Hanya bisa diisi dengan bukti nyata |
| BUTUH BANGUN | 36 | Perlu fitur atau pengujian baru |

Jumlah ini naik dari 158 karena 24 kewajiban baru dari slide resiliensi masuk ke matriks (bagian 5.12a).

**Lima gap terbesar**

1. **Tidak ada bukti lapangan sama sekali.** Tidak ada observasi, foto, wawancara, kuesioner, atau verifikasi pengelola. Tahap 1 dan 2, seluruh skor Antroposentris, serta target resiliensi seperti layanan minimum, RTO, dan RPO bergantung pada ini.
2. **"Sistem saat ini" di panduan bukan EduCopilot.** Tahap 1 sampai 3 dan lembar kerja meminta kondisi nyata kampus. EduCopilot belum dipakai di layanan kampus mana pun. Repo tidak bisa menjawab cara dosen bekerja sekarang.
3. **Feedback loop belum tertutup dan tidak ada proyeksi.** Tidak ada pengukuran apakah remedial mengubah hasil belajar, tidak ada prediksi (L3), tidak ada stock-flow, dan tindakan tidak sampai ke mahasiswa. Remedial Agent hanya stub yang tidak dipanggil (`backend/app/agents/remedial_agent.py:16-34`).
4. **Tidak ada autentikasi, peran, hak akses, atau audit.** Semua endpoint terbuka, termasuk approve dan delete (`backend/app/main.py:20-35`). Lembar kerja nomor 5 dan tata kelola tidak punya bukti untuk dirujuk. Aspek Trustworthiness di draf template berhenti di tingkat 0, dan kandidat syarat wajib privasi W1 belum terpenuhi.
5. **Tidak ada evaluasi AI dan uji ketahanan.** Tidak ada satu pun file tes. Nilai esai LLM tidak pernah dibandingkan dengan penilai manusia. Eksperimen gangguan, uji restore, dan log pengujian belum ada. Dari pembacaan kode, kegagalan LLM menghasilkan nilai esai 0 tanpa tanda (`backend/app/agents/grading_agent.py:122-130`), dan penyedia cadangan hanya dipilih dari kredensial, bukan saat penyedia gagal (`backend/app/core/llm.py:132-140`).

**Perkiraan maturity (hanya dari bukti kode, belum instrumen resmi)**

| Perspektif | Perkiraan | Catatan |
|---|---|---|
| Antroposentris | Tidak diberi skor | Wajib kuesioner Likert |
| Sistemik | Level 2 (Reactive) | Bekerja setelah dipicu manusia, input manual |
| Teknologi | Level 2 (dipakai di sebagian sistem) | Batas sistem: satu prodi |
| Digital Twin (lima level panduan) | Level 1 (Descriptive), dengan kemampuan Level 2 di kode | Level 2 belum terbukti pada data nyata |
| Template ISO/IEC 30186 (draf prototipe) | Skor 0,6 dari 5, label Awal | Skala berbeda, diisi terpisah (bagian 4) |

**Kluster.** Smart Education tetap kandidat terbaik, tetapi diterima bersyarat (lihat bagian 2). Syarat terpenting: panduan di Tahap 1 dan 2 ditulis untuk 13 kluster Smart Building, sehingga izin memakai kluster Smart Campus perlu dikonfirmasi ke dosen.

**Template kini tersedia.** Draf untuk prototipe ada di `docs/draf-asesmen-kematangan-prototipe.xlsx` dan belum diverifikasi tim. Delapan sumber acuan di bagian 7 panduan masih tidak ada secara lokal (lihat bagian 6).

---

## 2. Uji asumsi kluster

Asumsi yang diuji: Smart Campus > Smart Tridarma > Smart Education adalah kluster terdekat.

| Kandidat | Kecocokan dengan kode | Penilaian |
|---|---|---|
| Smart Education (Campus 1): platform pembelajaran, dashboard progres akademik | Tinggi. RPS, kuis, penilaian, analitik kelas (`backend/app/api/v1/dashboard.py:364-450`) | Terbaik, bersyarat |
| Smart Research (Campus 2): repositori, portal kolaborasi | Rendah. Hanya Knowledge Hub materi kuliah, bukan riset (`backend/app/api/v1/knowledge.py:23`) | Ditolak |
| Smart HR Management (Campus 8): beban kerja | Rendah. Tidak ada data kehadiran atau beban kerja di model | Ditolak |
| Smart Meeting, Occupancy (Campus 12, Building 6): utilisasi ruang | Tidak ada. Tidak ada data ruang atau jadwal | Ditolak |
| Cybersecurity & Data Privacy (Building 10): audit log | Tidak ada. Justru hal yang tidak dimiliki repo | Ditolak |
| Kluster Smart Building lain | Tidak ada. Tidak ada sensor atau perangkat | Ditolak |

Kesimpulan: **asumsi diterima bersyarat.** Tidak ada kandidat lain yang mendekati. Namun ada empat hal yang melemahkannya:

1. **Konflik di panduan.** Bagian 1 dan 2 (P1-2) mengizinkan Smart Campus atau Smart Building, tetapi Tahap 1 menyebut "13 kluster" dan Tahap 2 menyebut "satu kluster dari 13 pilihan" (P3). Contoh maturity di P4 justru memakai Smart Education. Perlu konfirmasi dosen.
2. **Sisi mahasiswa tidak ada.** Cakupan kluster menyebut dashboard progres akademik, tetapi antarmuka hanya untuk dosen (`frontend/src/app/dashboard/layout.tsx:8-16`). Mahasiswa tidak punya akses.
3. **Progres akademik belum nyata.** Progres per CPMK hanya rata-rata kelas yang disalin ke setiap CPMK (`backend/app/core/stats.py:139-149`).
4. **Pemilihan kluster harus berdasar bukti Tahap 1** (checklist P3). Memilih Smart Education sekarang, sebelum observasi, melanggar urutan itu. Sebaiknya kluster ini dicatat sebagai hipotesis sampai Tahap 1 selesai.

---

## 3. Kondisi nyata repo

### 3.1 Klaim README vs kode

| Klaim | Kenyataan di kode | Bukti |
|---|---|---|
| Tavily Search untuk informasi eksternal (`README.md:44`) | Tidak dipakai. Hanya tercantum sebagai dependensi. Tren industri diminta dari ingatan LLM | `backend/pyproject.toml:25`, `backend/app/agents/rps_agent.py:37-46` |
| Quiz Agent memakai RAG (`README.md:108`) | Tidak. Satu-satunya pemanggil `retrieve_materials` adalah endpoint pencarian. Kuis memakai teks yang dikirim form, dipotong 4000 karakter | `backend/app/api/v1/knowledge.py:249`, `backend/app/agents/quiz_agent.py:108` |
| Remedial Agent merekomendasikan tindakan (`README.md:110`) | Stub berisi nilai tetap, dan `build_remedial_graph` tidak dipanggil dari mana pun | `backend/app/agents/remedial_agent.py:16-34`, `backend/app/agents/remedial_agent.py:36` |
| Feedback personal per mahasiswa (`README.md:24`) | Yang disimpan hanya templat skor. Feedback esai dari LLM tidak ikut tersimpan | `backend/app/agents/grading_agent.py:143`, `backend/app/agents/grading_agent.py:178-186`, `backend/app/api/v1/grading.py:74` |
| Nilai direview manusia (`README.md:117`) | Tidak ada endpoint untuk mengubah nilai. Hasil langsung `graded`. Pesan "mohon dinilai manual" saat LLM gagal tidak punya jalur, karena skor 0 tidak dinilai ulang | `backend/app/agents/grading_agent.py:122-130`, `backend/app/api/v1/grading.py:27`, `backend/app/api/v1/grading.py:73-75` |
| Tidak ada angka tiruan (`backend/app/core/stats.py:4`) | Progres CPMK diakui placeholder di file yang sama | `backend/app/core/stats.py:139-141` |
| Loop perbaikan RPS "hingga valid" (`backend/app/agents/rps_agent.py:538`) | Loop semu. Node refine kosong, dan rute selalu `compliant` karena `draft_rps` selalu terisi | `backend/app/agents/rps_agent.py:439`, `backend/app/agents/rps_agent.py:492-494`, `backend/app/agents/rps_agent.py:500-504` |
| Validasi soal kuis | Selalu `True`, dan kedua cabang rute menuju node yang sama | `backend/app/agents/quiz_agent.py:235-243` |
| Aturan SN-Dikti diambil agen | Teks tetap, ditandai "Mock fetching" | `backend/app/agents/rps_agent.py:31-35` |
| 24 kriteria SN-Dikti (`README.md:15`) | **Benar.** Ada 24 kriteria deterministik | `backend/app/core/sndikti_catalog.py:428`, `backend/app/core/sndikti_catalog.py:710` |

Klaim yang keliru ini penting karena aturan bukti panduan. Jika README dikutip sebagai bukti, klaimnya akan runtuh saat diverifikasi.

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
- `courses.status` tetap "On Track" walau rata-rata 23,3, karena tidak pernah diperbarui (`backend/app/core/stats.py:269-285`, `backend/app/seed.py:78-79`).
- `quizzes.submissions` bernilai 0 padahal tiap kuis punya 3 baris submission.
- Folder `chroma_db` tidak ada, jadi indeks RAG tidak ikut di repo (`backend/app/core/rag.py:7`).

Hasil eksekusi katalog pada salinan DB: kedua RPS memperoleh 100 (bobot 250 dari 250, 102 baris penilaian, 0 gagal). Jadi skor 100 yang tersimpan cocok. Katalog hanya memeriksa kelengkapan struktur, bukan mutu pengajaran. Perlu diingat pula `approve_rps` menulis 100 tanpa memeriksa apa pun (`backend/app/api/v1/rps.py:623-625`), dan nilainya baru dihitung ulang saat halaman detail dibuka (`backend/app/api/v1/dashboard.py:232-236`).

Privasi: nama dan NIM di `backend/app/seed.py:96-98` dan `backend/educopilot.db` kini sintetis, begitu juga isi dua materi PDF di DB. Riwayat git masih menyimpan versi lama, jadi paket akhir ke Living Lab harus memakai kondisi terbaru tanpa riwayat itu. Keputusan pengguna: kuis dan RPS di DB yang diturunkan dari slide dibiarkan.

### 3.3 Lima siklus smart system

| Siklus | Yang benar-benar ada | Yang tidak ada | Nilai |
|---|---|---|---|
| Sensing | Unggah CSV jawaban (`backend/app/api/v1/quiz.py:404`), impor roster (`backend/app/api/v1/students.py:93`), unggah materi (`backend/app/api/v1/materials.py:121`) | Pengumpulan otomatis. Tidak ada konektor LMS atau SIAKAD, tidak ada penjadwal | Manual, batch |
| Understanding | Nilai MCQ dan esai (`backend/app/agents/grading_agent.py:46`, `backend/app/agents/grading_agent.py:73`), statistik kelas dan heatmap (`backend/app/core/stats.py:167`), katalog (`backend/app/core/sndikti_catalog.py:710`), review agent (`backend/app/agents/rps_review_agent.py:448-463`) | Analisis per CPMK. "Topik lemah" hanyalah 80 karakter awal teks soal (`backend/app/agents/grading_agent.py:199`) | Ada, terkuat |
| Decision | Aturan ambang: status kuis (`backend/app/api/v1/grading.py:96`), alert (`backend/app/api/v1/dashboard.py:89-107`). Keputusan manusia: approve, publish, apply, dismiss | Prediksi, prioritas, atau rekomendasi per mahasiswa | Sebagian, berbasis ambang |
| Action | Materi otomatis minggu berikutnya (`backend/app/agents/auto_material_agent.py:77`), terapkan temuan ke RPS (`backend/app/api/v1/rps.py:950`) | Tindakan yang sampai ke mahasiswa. Notifikasi stub (`backend/app/agents/remedial_agent.py:32-34`), dan toggle notifikasi tidak dibaca oleh proses apa pun (`backend/app/api/v1/dashboard.py:570-586`) | Sebagian, berhenti di dosen |
| Learning | Temuan yang di-dismiss tetap diingat antar-run (`backend/app/api/v1/rps.py:852-858`). Catatan dosen dipakai saat regenerasi (`backend/app/api/v1/rps.py:1282-1285`) | Evaluasi hasil, pembaruan model atau aturan, riwayat antar-semester | Hampir tidak ada |

### 3.4 Unsur sistem yang diminta panduan

| Unsur | Temuan | Bukti |
|---|---|---|
| Loop kepatuhan RPS | Tertutup di kode, dengan manusia, tanpa delay: temuan, apply, hitung ulang skor. Tidak ada jejak pemakaian (0 baris) | `backend/app/api/v1/rps.py:1004-1008` |
| Loop hasil belajar | **Terbuka.** Skor, topik lemah, materi minggu depan, lalu berhenti. Tidak ada pengukuran kondisi yang berubah. Materi tidak dikirim dan tidak otomatis dipakai kuis berikutnya, meski docstring menyiratkan demikian | `backend/app/api/v1/grading.py:109-115`, `backend/app/agents/auto_material_agent.py:6-8` |
| Loop manusia ke kuis | Dosen bisa memilih materi `AUTO` secara manual sebagai sumber kuis. Inilah satu-satunya jalur kembali | `frontend/src/app/dashboard/quiz/new/KnowledgeMaterialPicker.tsx:80-89` |
| Delay | Hanya struktur minggu (`week_number`), dan materi diarahkan ke minggu+1. Waktu penilaian tidak dicatat, `updated_at` berupa teks tanggal | `backend/app/agents/auto_material_agent.py:99`, `backend/app/models/submission.py:30`, `backend/app/api/v1/grading.py:97` |
| Stock-flow | Tidak ada persamaan atau laju. Yang mendekati stok hanya antrean belum dinilai dan jumlah temuan aktif | `backend/app/core/stats.py:279-284`, `backend/app/api/v1/rps.py:788` |
| Log | Hanya stdout lewat `print` dan `logging`, tidak disimpan | `backend/app/api/v1/grading.py:70`, `backend/app/agents/auto_material_agent.py:211` |
| Audit | Tidak ada. Tidak ada tabel audit, kolom pelaku, atau riwayat versi. Jadwal RPS dihapus lalu ditulis ulang | `backend/app/api/v1/rps.py:81` |
| Autentikasi dan peran | Tidak ada di backend maupun frontend, tidak ada middleware. Satu peran implisit: dosen | `backend/app/main.py:12-18`, `backend/app/main.py:20-35`, `frontend/src/lib/api.ts:21-26`, `frontend/src/app/page.tsx:3-5` |
| Human-in-the-loop | Ada di RPS dan kuis: approve, publish, apply, dismiss, RPS terkunci setelah disetujui. Tidak ada di nilai dan materi otomatis | `backend/app/api/v1/rps.py:618`, `backend/app/api/v1/rps.py:1090`, `backend/app/api/v1/quiz.py:134`, `backend/app/agents/auto_material_agent.py:182` |
| Tes | Tidak ada file tes, CI, atau Dockerfile, walau `pytest` tercantum | `backend/pyproject.toml:18` |

---

## 4. Perkiraan maturity

**Peringatan.** Ini perkiraan awal untuk **prototipe**, dari kode saja. Ini bukan hasil instrumen panduan, yang mewajibkan bukti dan konfirmasi pengelola kampus (P4). Jangan dikutip sebagai skor layanan kampus. Panduan hanya memberi nama level Sistemik (Impulsive, Reactive, Responsive, Initiative) tanpa definisi, dan artikel sumbernya tidak tersedia lokal, sehingga pemetaan di bawah adalah tafsiran. Sengaja tidak diberi angka desimal seperti contoh 2,89 di P4, karena angka itu berasal dari instrumen.

### Sistemik: Level 2 (Reactive)

| Pertanyaan bertingkat panduan (P4) | Jawaban | Alasan |
|---|---|---|
| Apakah data dikumpulkan sistem secara otomatis? | Tidak | Semua input lewat unggahan manual (`backend/app/api/v1/quiz.py:404`) |
| Apakah sistem mengolah dan menganalisis sehingga manusia tinggal memutuskan? | Ya, untuk sebagian | Penilaian, heatmap, dan temuan RPS tersedia. CPMK tidak (`backend/app/core/stats.py:149`) |
| Apakah sistem dapat mengambil keputusan dari analitik? | Terbatas | Skor final, status kuis, dan pembuatan materi berjalan otomatis (`backend/app/api/v1/grading.py:73-75`, `backend/app/api/v1/grading.py:96`, `backend/app/api/v1/grading.py:109`) |

Bukan Level 3 karena tidak ada penjadwal atau pemicu otomatis: setiap agen dijalankan oleh tombol manusia (`backend/app/api/v1/grading.py:14`), dan siklus learning hampir kosong. Bukan Level 1 karena alur penilaian sampai materi sudah terintegrasi dan konsisten.

### Teknologi: Level 2 (dipakai di sebagian sistem)

Batas sistem sudah diputuskan: satu prodi (K3). TI di prototipe hadir di RPS, kuis, penilaian, dan analitik, tetapi tidak di sisi mahasiswa, presensi, integrasi data akademik, atau notifikasi. Nilai resmi tetap harus diukur pada prodi yang dipilih, bukan dari repo.

### Digital Twin: Level 1 (Descriptive), kemampuan Level 2 ada di kode

- **Level 1 belum kuat.** Syaratnya model digital terhubung ke sistem nyata (P5). Modelnya ada (`backend/app/models/course.py:8`, `backend/app/models/rps_meeting.py:8`), tetapi koneksinya unggahan manual dan belum pernah memuat data operasional.
- **Level 2 ada kemampuannya.** Data diubah menjadi wawasan oleh LLM dan aturan (`backend/app/agents/grading_agent.py:96`, `backend/app/core/stats.py:244`). Gambar di P5 mengaitkan Level 2 dengan data sensor, yang di sini setara data aktivitas belajar. Data itu belum mengalir terus-menerus.
- **Level 3 tidak terpenuhi.** Tidak ada prediksi, hanya ambang atas data lampau (`backend/app/core/stats.py:224-228`).
- **Level 4 dan 5 tidak terpenuhi.** Tidak ada simulasi what-if atau otonomi.

Semua operasi memang human-in-the-loop, sesuai untuk Level 1 sampai 4.

### Template ISO/IEC 30186: draf prototipe, 0,6 dari 5 (Awal)

File: `docs/draf-asesmen-kematangan-prototipe.xlsx`. Status: draf dari bukti kode, belum diverifikasi tim. Entitasnya prototipe di repo, bukan prodi atau kampus. Asesmen batas satu prodi harus dibuat terpisah setelah bukti lapangan ada.

**Skala template berbeda dari model lima level di panduan, dan keduanya diisi terpisah.** Jangan mengonversi yang satu ke yang lain.

| Pembeda | Model lima level panduan (P5) | Template asesmen |
|---|---|---|
| Bentuk | Satu level keseluruhan | Lima aspek berbobot, 25 indikator Ya/Tidak |
| Nama level | Descriptive, Informative, Predictive, Comprehensive, Autonomous | Static / dasar, Connected, Integrated, Interactive, Autonomous |
| Nilai terendah | Level 1 | Tingkat 0 (Belum dasar) dari rumus |
| Syarat Level 2 | Data diubah menjadi wawasan | Data mengalir otomatis, bukan unggah manual |
| Dipakai untuk | T3-16, T3-17 | TG-05a, TG-05b |

Jadi Level 1 di panduan dan skor 0,6 di template tidak bertentangan.

| Aspek | Ya (dari 5) | Tingkat | Nama tingkat | Skor berbobot | Celah berikutnya |
|---|---:|---:|---|---:|---|
| Convergence | 1 | 1 | Static / dasar | 0,2 | Tingkat 2 |
| Capability | 0 | 0 | Belum dasar | 0,0 | Tingkat 1 |
| Integrated view | 1 | 1 | Static / dasar | 0,2 | Tingkat 2 |
| Time | 1 | 1 | Static / dasar | 0,2 | Tingkat 2 |
| Trustworthiness | 0 | 0 | Belum dasar | 0,0 | Tingkat 1 |
| **Total** | **3 dari 25** | | | **0,6 (Awal)** | |

| Syarat twin | Aturan | Hasil |
|---|---|---|
| Aliran otomatis fisik ke digital | Convergence ≥ 2 | Belum |
| Aliran balik digital ke fisik | Convergence ≥ 4 | Masih shadow atau model |
| Keputusan otonom | Capability = 5 | Masih butuh manusia |

Aturan pengisian: `Ya` hanya dengan bukti `file:baris`, klaim README tidak dihitung, dan kemampuan yang belum terbukti pada data nyata tidak dianggap `Ya`. Tiga `Ya` adalah C1, I1, dan T1, yang menyatakan keberadaan representasi, cakupan, dan dasar snapshot, bukan kemampuan.

Dua hal perlu dibaca bersama hasil ini:

- **P1 adalah penilaian paling tipis.** Tampilan keadaan ada di kode, tetapi hanya pernah memuat data sintetis, sehingga mengikuti aturan menjadi `Tidak`. Jika P1 diterima, Capability menjadi 1 dan skor 0,8.
- **Petunjuk dan rumus template berbeda.** Petunjuk berkata "tanpa bukti, skor tetap 1", sedangkan rumus memberi 0. Draf mengikuti rumus. Jika tingkat terendah 1 yang dipakai, skor menjadi 1,0.

Pada kedua kemungkinan itu label tetap Awal dan ketiga syarat twin tidak berubah.

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
| T2-03 | Peta stakeholder dengan peran | SEBAGIAN | Hanya dosen di kode (`frontend/src/app/dashboard/layout.tsx:8-16`), mahasiswa sebagai objek data (`backend/app/models/student.py:8`) | Kaprodi, penjamin mutu, pengelola sistem kampus, dan lain-lain |
| T2-04 | Minimal dua wawancara stakeholder berbeda | BUTUH LAPANGAN | Belum ada | Wawancara |
| T2-05 | Transkrip atau ringkasan wawancara | BUTUH LAPANGAN | Belum ada | Bergantung T2-04 |
| T2-06 | Kesimpulan berbentuk pengecekan kondisi saat ini | BUTUH LAPANGAN | Belum ada | Kalimat panduan tidak lengkap, lihat bagian 9 |

### 5.4 Tahap 3: Data & System Mapping (P3-4)

| ID | Kewajiban | Status | Bukti | Yang kurang |
|---|---|---|---|---|
| T3-01 | Inventaris sumber data internal prototipe | SIAP | `backend/app/models/submission.py:16-30`, `backend/app/models/material.py:8-25`, `backend/app/models/rps.py:8-27`, `backend/app/api/v1/quiz.py:404` | Tidak ada, sebatas prototipe |
| T3-02 | Inventaris sumber data kampus yang nyata | BUTUH LAPANGAN | Belum ada | LMS, SIAKAD, presensi, dokumen RPS, kuesioner layanan |
| T3-03 | Tiap sumber: format, frekuensi, pemilik, kualitas, cara akses | SEBAGIAN | Format dan cara akses prototipe dapat diisi dari kode | Pemilik, frekuensi, kualitas nyata |
| T3-04 | Peta alur data prototipe | SIAP | `backend/app/api/v1/quiz.py:404`, `backend/app/api/v1/grading.py:14`, `backend/app/agents/auto_material_agent.py:193-207`, `backend/app/api/v1/dashboard.py:364` | Tidak ada, sebatas prototipe |
| T3-05 | Peta sistem as-is sampai ke pengguna | BUTUH LAPANGAN | Belum ada | Alur kerja dosen dan sistem kampus saat ini |
| T3-06 | Checklist: pemilik dan waktu pencatatan tiap sumber | BUTUH LAPANGAN | `created_at` ada (`backend/app/models/submission.py:30`), kolom pemilik tidak | Konfirmasi pemilik data |
| T3-07 | Checklist: kesenjangan data ditandai | SEBAGIAN | Dikenali dari kode: pemetaan soal ke CPMK (`backend/app/core/stats.py:139-141`), waktu penilaian, presensi | Kebutuhan data tergantung masalah Tahap 4 |
| T3-08 | Instrumen Antroposentris: Likert ke mahasiswa, dosen, pejabat | BUTUH LAPANGAN | Belum ada | Kuesioner dan responden |
| T3-09 | Instrumen Sistemik: ya/tidak bertingkat | SEBAGIAN | Perkiraan di bagian 4 | Harus dijawab untuk sistem nyata dengan pengelola |
| T3-10 | Instrumen Teknologi: ya/tidak bertingkat | SEBAGIAN | Perkiraan di bagian 4 | Sama seperti T3-09 |
| T3-11 | Dokumentasi bukti jawaban (tangkapan layar, panduan pengguna) | SEBAGIAN | Tangkapan layar prototipe bisa dibuat, panduan pengguna hanya `README.md:48` | Bukti sistem nyata |
| T3-12 | Konfirmasi pengelola kampus | BUTUH LAPANGAN | Belum ada | Pengelola kampus |
| T3-13 | Sampling kunjungan kampus untuk verifikasi | BUTUH LAPANGAN | Belum ada | Kunjungan |
| T3-14 | Tabel rata-rata skor tiga perspektif | BUTUH LAPANGAN | Belum ada | Bergantung T3-08 sampai T3-13 |
| T3-15 | Kesimpulan tiga perspektif dan empat level | BUTUH LAPANGAN | Hanya perkiraan bagian 4 | Bergantung T3-14 |
| T3-16 | Penentuan level Digital Twin | SEBAGIAN | Perkiraan bagian 4, pada skala lima level panduan | Bukti koneksi nyata. Hasil template tidak dipakai di sini |
| T3-17 | Kesimpulan level Digital Twin | SEBAGIAN | Perkiraan bagian 4 | Bergantung T3-16 |

### 5.5 Lembar kerja system thinking dan situational awareness (P5-7)

| ID | Kewajiban | Status | Bukti | Yang kurang |
|---|---|---|---|---|
| LK1-01 | Tabel complicated: bagian yang rumit tetapi dapat dipetakan | SIAP | Pipeline dan aturan deterministik: `backend/app/agents/rps_agent.py:506-541`, `backend/app/core/sndikti_catalog.py:710` | Tidak ada, sebatas prototipe |
| LK1-02 | Tabel complex: perilaku yang muncul dari interaksi | BUTUH LAPANGAN | Belum ada | Perilaku dosen dan mahasiswa, keterlibatan, motivasi |
| LK2-E | Elements/boundary: aktor, lokasi, unit analisis, cakupan | SEBAGIAN | Unit analisis: mata kuliah, kuis, submission (`backend/app/models/course.py:8`, `backend/app/models/submission.py:8`) | Lokasi dan aktor nyata, batas sistem |
| LK2-I | Interconnections: relasi data, hierarki | SIAP | Relasi lewat `course_id`, `rps_id`, `quiz_id` (`backend/app/models/quiz.py:12`, `backend/app/models/submission.py:19`), graf (`backend/app/api/v1/knowledge.py:23`). Catatan: tanpa foreign key | Tidak ada, sebatas prototipe |
| LK2-G | Goal/decision rule: tujuan, ambang, prioritas | SIAP | Lulus 60 (`backend/app/core/stats.py:63`), band 75 dan 60 (`backend/app/core/stats.py:224-228`), kepatuhan 85 (`backend/app/api/v1/dashboard.py:257`), bobot katalog (`backend/app/core/sndikti_catalog.py:13`) | Dasar ambang perlu dicocokkan dengan aturan akademik |
| LK2-D | Delay/time | SEBAGIAN | Struktur 16 minggu dan jeda satu minggu (`backend/app/agents/auto_material_agent.py:99`) | Latensi terukur, horizon simulasi, data panel |
| LK2-F | Feedback: jalur tertutup | SEBAGIAN | Loop kepatuhan tertutup (`backend/app/api/v1/rps.py:1004-1008`), loop hasil belajar terbuka (`backend/app/api/v1/grading.py:109-115`) | Pengukuran kondisi setelah tindakan |
| LK2-S | Stock-flow dengan satuan stok dan laju | BUTUH BANGUN | Hanya kandidat stok (`backend/app/core/stats.py:279-284`) | Persamaan neraca dan laju, data waktu |
| LK2-a | Apakah semua komponen terpenuhi, dengan bukti | SEBAGIAN | Tabel bagian 3.4 | Pertanyaan ini tentang sistem saat ini, perlu bukti lapangan |
| LK2-b | Apakah D dan F perlu ada, dan mengapa | SEBAGIAN | Argumen dari kode: efek belajar selalu tertunda, jadi tanpa D dan F remedial tidak bisa dinilai | Kondisi D dan F di sistem nyata |
| LK3-01 | Reinforcing loop | SEBAGIAN | Kandidat: materi `AUTO` masuk RAG lalu menjadi sumber kuis berikutnya (`backend/app/agents/auto_material_agent.py:193-207`). Masih lewat pilihan manusia | Bukti perilaku |
| LK3-02 | Reinforcing negatif / keruntuhan | BUTUH LAPANGAN | Belum ada | Pengamatan lanjutan |
| LK3-03 | Balancing tanpa delay | SIAP | Perbaikan RPS langsung menghitung ulang skor (`backend/app/api/v1/rps.py:1004-1008`, `backend/app/api/v1/rps.py:231`) | Tidak ada, sebatas prototipe. Belum ada jejak pemakaian |
| LK3-04 | Balancing respons agresif | BUTUH LAPANGAN | Belum ada. Kode tidak punya parameter kekuatan respons | Pengamatan, atau definisi dari dosen |
| LK3-05 | Balancing dengan delay | SEBAGIAN | Kuis minggu N, penguatan minggu N+1 (`backend/app/agents/auto_material_agent.py:99`) | Efek belum diukur |
| LK3-06 | Rasio fiscal | BUTUH LAPANGAN | Belum ada | Definisi tidak ada di panduan (K6). Data biaya |
| LK3-07 | Sensitivitas | BUTUH BANGUN | Belum ada | Definisi (K6), lalu analisis parameter. Sensitivitas bobot di S35 dan titik sensitivitas di S33 adalah alat keputusan desain, bukan definisi baris ini |
| LK3-08 | Polaritas loop | SEBAGIAN | Tanda bisa ditulis untuk loop di bagian 3.4 | Diagram loop yang disepakati |
| LK3-09 | Polaritas loop panjang | BUTUH LAPANGAN | Belum ada | Definisi (K6), pengamatan antar-semester |
| LK3-10 | Kondisi Γ−W | BUTUH LAPANGAN | Belum ada | Definisi tidak ada di panduan (K6) |
| LK4-L1 | L1 Perception | SIAP | Data yang ditangkap: `backend/app/api/v1/quiz.py:404`, `backend/app/api/v1/dashboard.py:41-46` | Tidak ada, sebatas prototipe |
| LK4-L2 | L2 Comprehension | SIAP | Heatmap dan insight: `backend/app/core/stats.py:167`, `backend/app/core/stats.py:244`, `frontend/src/app/dashboard/analytics/page.tsx:179-181` | Pemahaman per CPMK lemah |
| LK4-L3 | L3 Projection | BUTUH BANGUN | Tidak ada prediksi (`backend/app/core/stats.py:224-228`) | Model proyeksi dan data historis |
| LK4-a | Apakah ketiga komponen perlu ada | SEBAGIAN | Argumen dari L1 dan L2 yang ada, dan L3 yang tidak | Rujukan Endsley belum tersedia lokal |
| LK4-b | Simulasi jika satu komponen ditiadakan | BUTUH BANGUN | Belum ada | Skenario pengujian di lingkungan uji |
| LK5-01 | In the loop: peran, bukti, kapan | SIAP | Approve (`backend/app/api/v1/rps.py:618`), publish (`backend/app/api/v1/quiz.py:134`), apply dan dismiss (`backend/app/api/v1/rps.py:950`, `backend/app/api/v1/rps.py:1021`), pemicu penilaian (`backend/app/api/v1/grading.py:14`) | Tidak ada, sebatas prototipe |
| LK5-02 | On the loop | SEBAGIAN | Alert dan dashboard (`backend/app/api/v1/dashboard.py:89-107`) | Tidak ada pemantauan proses berjalan atau hak interupsi |
| LK5-03 | Over the loop | BUTUH LAPANGAN | Tidak ada peran di kode | Kaprodi, penjamin mutu, kebijakan nyata |
| LK5-04 | Out the loop | SIAP | Berjalan tanpa persetujuan: skor final (`backend/app/api/v1/grading.py:73-75`), materi `ready` (`backend/app/agents/auto_material_agent.py:182`). Mahasiswa tidak punya akses (`frontend/src/app/dashboard/layout.tsx:8-16`) | Tidak ada, sebatas prototipe |
| LK5-a | Definisikan hak akses dari peran | BUTUH BANGUN | Tidak ada peran (`backend/app/main.py:20-35`) | Model peran dan autentikasi |
| LK5-b | Jelaskan dengan bukti hak akses | BUTUH BANGUN | Satu-satunya pembatasan berbasis status, bukan pengguna (`backend/app/api/v1/rps.py:1090`) | Bergantung LK5-a |

### 5.6 Tahap 4: Gap Analysis & Problem Definition (P7, P12)

| ID | Kewajiban | Status | Bukti | Yang kurang |
|---|---|---|---|---|
| T4-01 | Bandingkan kondisi saat ini dengan target, SOP, standar | SEBAGIAN | Standar RPS tersedia sebagai katalog (`backend/app/core/sndikti_catalog.py:1-21`) | Kondisi saat ini dan SOP kampus. Sumber regulasi juga tidak konsisten (`backend/app/agents/rps_agent.py:35`, `backend/app/agents/rps_agent.py:450`) |
| T4-02 | Problem statement satu paragraf | BUTUH LAPANGAN | Belum ada | Siapa, apa, seberapa besar, bukti |
| T4-03 | Canvas: Problem | BUTUH LAPANGAN | Belum ada | Dari Tahap 1 sampai 3 |
| T4-04 | Canvas: Data | SEBAGIAN | T3-01 | Data nyata yang tersedia |
| T4-05 | Canvas: AI / Intelligence | SEBAGIAN | Kemampuan yang ada: `backend/app/agents/grading_agent.py:73`, `backend/app/agents/rps_review_agent.py:448-463` | Harus ditentukan dari masalah |
| T4-06 | Canvas: Decision | SEBAGIAN | LK5-01 | Pengambil keputusan nyata |
| T4-07 | Canvas: Action | SEBAGIAN | `backend/app/agents/auto_material_agent.py:77` | Respons yang sampai ke mahasiswa |
| T4-08 | Canvas: Impact | BUTUH LAPANGAN | Belum ada | Indikator dan baseline |
| T4-09 | Checklist: bukti minimal dua sumber | BUTUH LAPANGAN | Belum ada | Triangulasi |
| T4-10 | Checklist: indikator keberhasilan terukur | BUTUH LAPANGAN | Belum ada | Bergantung T4-02 |

### 5.7 Tahap 5: Solution Design (P8)

| ID | Kewajiban | Status | Bukti | Yang kurang |
|---|---|---|---|---|
| T5-01 | Konsep solusi: apa dideteksi, diprediksi, dioptimalkan, dan tindakannya | SEBAGIAN | Deteksi ada (`backend/app/core/stats.py:167`), prediksi tidak | Harus menjawab masalah Tahap 4 |
| T5-02 | Arsitektur awal: sumber data, jaringan, penyimpanan, AI, dashboard, notifikasi | SEBAGIAN | Komponen ada: `backend/app/main.py:20-35`, `backend/app/core/rag.py:13`, `backend/app/core/llm.py:123`, `backend/app/core/database.py:23` | Notifikasi nihil, jaringan dan deployment tidak ada |
| T5-03 | KPI dan cara mengukur | BUTUH LAPANGAN | KPI aplikasi ada (`backend/app/api/v1/dashboard.py:421-442`) tetapi bukan KPI masalah | KPI dari Tahap 4 |
| T5-04 | Baseline dan target berdasar maturity | BUTUH LAPANGAN | Belum ada | Bergantung T3-14, T3-16 |
| T5-05 | Checklist: tiap komponen terhubung ke kebutuhan data Tahap 3 | SEBAGIAN | Pemetaan dari kode bisa dibuat | Bergantung T3-07 |
| T5-06 | Checklist: KPI punya baseline | BUTUH LAPANGAN | Belum ada | Bergantung T5-04 |
| T5-07 | Checklist: ada rencana pengujian | BUTUH BANGUN | Tidak ada tes atau rencana | Rencana uji dan alat uji |

### 5.8 Tahap 6: Data / AI Design (P8)

| ID | Kewajiban | Status | Bukti | Yang kurang |
|---|---|---|---|---|
| T6-01 | Tentukan dataset dan jelaskan sumber | SEBAGIAN | Hanya 6 submission uji (bagian 3.2) | Dataset nyata atau simulasi yang terdokumentasi |
| T6-02 | Pilih metode | SEBAGIAN | Aturan ambang (`backend/app/core/stats.py:224-228`), rubrik LLM (`backend/app/agents/grading_agent.py:96`) | Pembenaran terhadap masalah, metode prediksi |
| T6-03 | Rancang evaluasi: metrik, data uji, batas kelayakan | BUTUH BANGUN | Tidak ada | Mis. kesesuaian nilai LLM dengan penilai manusia |
| T6-04 | Checklist: metode sesuai masalah dan data | BUTUH LAPANGAN | Belum ada | Bergantung T4-02 |
| T6-05 | Checklist: metrik ditetapkan sebelum membangun | BUTUH BANGUN | Sudah terlanggar untuk fitur lama | Tetapkan metrik sebelum perubahan baru, bagian 7 |

### 5.9 Leverage points (P8-9)

Kolom bukti berisi titik yang bisa dirujuk untuk mengisi tabel. Penentuan LP nyata dan LP sasaran baru sah setelah Tahap 4.

| ID | Kewajiban | Status | Bukti | Yang kurang |
|---|---|---|---|---|
| LP-12 | Numbers | SIAP | Ambang 60, 75, 85 (`backend/app/core/stats.py:63`, `backend/app/api/v1/dashboard.py:257`) | Tidak ada, sebatas prototipe |
| LP-11 | Buffers | SEBAGIAN | Rantai penyedia LLM (`backend/app/core/config.py:39-43`) | Buffer belajar: mis. waktu dosen, jadwal remedial |
| LP-10 | Stock and Flow Structures | BUTUH BANGUN | Lihat LK2-S | Model stok dan aliran |
| LP-09 | Delay | SEBAGIAN | Jeda satu minggu (`backend/app/agents/auto_material_agent.py:99`) | Pengukuran jeda |
| LP-08 | Balancing feedback loops | SEBAGIAN | LK3-03, LK3-05 | Loop hasil belajar tertutup |
| LP-07 | Reinforcing feedback loops | BUTUH LAPANGAN | Belum ada | Bukti perilaku |
| LP-06 | Information Flows | SEBAGIAN | Dashboard dosen (`backend/app/api/v1/dashboard.py:364`) | Informasi tidak sampai ke mahasiswa |
| LP-05 | Rules | SEBAGIAN | Katalog dan penguncian RPS (`backend/app/core/sndikti_catalog.py:428`, `backend/app/api/v1/rps.py:1090`) | Aturan kewenangan dan insentif kampus |
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
| TG-05a | Pakai template xlsx asesmen kematangan Digital Twin | SEBAGIAN | Template tersedia. Draf prototipe `docs/draf-asesmen-kematangan-prototipe.xlsx`: 0,6, Awal (bagian 4) | Verifikasi tim. Asesmen batas satu prodi setelah bukti lapangan. Keputusan P1 dan aturan tingkat 0 (K11) |
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
| DIM-03 | Ekonomi | BUTUH LAPANGAN | Biaya LLM tidak dicatat (`backend/app/core/llm.py:123`) | Waktu dan biaya, pencatatan token |
| DIM-04 | Lingkungan | BUTUH LAPANGAN | Belum ada | Asumsi yang dinyatakan |
| DIM-05 | Teknis | SEBAGIAN | Indikator bisa diturunkan dari kode | Uptime, latensi, akurasi belum diukur |
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
| RS-01 | Definisikan pengguna | SEBAGIAN | Dosen (`frontend/src/app/dashboard/layout.tsx:8-16`) | Pengguna lain |
| RS-02 | Definisikan fungsi kritis | SEBAGIAN | Kandidat FK1 sampai FK6 di bagian 5.16, mis. penilaian (`backend/app/api/v1/grading.py:14`) | Validasi dari pengguna |
| RS-03 | Definisikan batas kualitas | BUTUH LAPANGAN | Belum ada | Batas waktu dan mutu yang diterima pengguna |
| RS-04 | Definisikan dependensi | SIAP | LLM (`backend/app/core/config.py:39-43`), embedding (`backend/app/core/rag.py:11`), ChromaDB (`backend/app/core/rag.py:13`), SQLite (`backend/app/core/config.py:25`), reportlab (`backend/app/services/pdf_generator.py:2`) | Tidak ada, sebatas prototipe |
| RS-05 | Tiga alternatif desain yang memenuhi syarat wajib | BUTUH BANGUN | Belum ada. Sketsa awal di bagian 5.16 | Dirancang setelah persyaratan jelas. Alternatif yang gagal syarat wajib gugur sebelum diskor (S9) |
| RS-06 | Bandingkan biaya | BUTUH LAPANGAN | Belum ada | Data atau asumsi yang dinyatakan |
| RS-07 | Bandingkan kontinuitas | BUTUH BANGUN | Belum ada | Hasil eksperimen |
| RS-08 | Bandingkan energi | BUTUH LAPANGAN | Belum ada | Asumsi yang dinyatakan |
| RS-09 | Bandingkan pemeliharaan | BUTUH LAPANGAN | Belum ada | Asumsi yang dinyatakan |
| RS-10 | Eksperimen gangguan 1 di lingkungan uji | BUTUH BANGUN | Belum dijalankan. Kandidat G1: LLM tidak tersedia, yang dari kode menghasilkan nilai esai 0 (`backend/app/agents/grading_agent.py:122-130`) | Lingkungan uji, LLM tiruan |
| RS-11 | Eksperimen gangguan 2 di lingkungan uji | BUTUH BANGUN | Belum dijalankan. Kandidat G4: DB hilang dan restore (`backend/app/core/database.py:26`, `backend/app/core/database.py:40`) | Lingkungan uji, prosedur backup |
| RS-12 | Laporan: diagram arsitektur | SEBAGIAN | T5-02 | Tiga alternatif |
| RS-13 | Laporan: skenario | SEBAGIAN | Kandidat G1 sampai G7 di bagian 5.16, dalam format S19 | Pemilihan final dan kriteria dari kebutuhan lapangan |
| RS-14 | Laporan: versi konfigurasi | SEBAGIAN | `backend/.env.example:1`, `backend/uv.lock:1` | Pencatatan per eksperimen |
| RS-15 | Laporan: matriks keputusan | BUTUH BANGUN | Belum ada | Bergantung RS-05 sampai RS-09 |
| RS-16 | Laporan: analisis sensitivitas | BUTUH BANGUN | Belum ada. S35 memberi contoh sensitivitas bobot | Bergantung RS-15 |
| RS-17 | Laporan: log pengujian | BUTUH BANGUN | Log tidak disimpan (`backend/app/api/v1/grading.py:70`) | Log tersimpan |
| RS-18 | Laporan: rekomendasi | BUTUH BANGUN | Belum ada | Bergantung RS-15 |
| RS-19 | Tiap kesimpulan terhubung ke bukti, keterbatasan dijelaskan | BUTUH BANGUN | Belum ada | Bergantung RS-10 sampai RS-17 |

### 5.12a Kewajiban tambahan dari slide resiliensi

Sumber: `10-TradeOff_Resiliensi.pdf`. S40 memuat tugas kelompok dan S41 memuat rubrik. Definisi fungsi kritis dan layanan minimum ada di S17, dan persyaratan wajib lawan preferensi di S9, jadi label sumbernya mengikuti slide itu. Luaran S40 (diagram, matriks, log, rekomendasi) sudah tercakup RS-12, RS-15, RS-17, dan RS-18, sehingga tidak dihitung ulang.

**Rubrik S41 hanya usulan.** Bobotnya 20/25/30/25 untuk fungsi dan gangguan, alternatif dan trade-off, pengujian resiliensi, serta keberlanjutan dan argumentasi. Slide menyatakan rubrik "usulan pembelajaran yang dapat disesuaikan". Rubrik ini tidak dihitung sebagai baris sampai dosen menetapkannya (K10).

| ID | Kewajiban | Status | Bukti | Yang kurang |
|---|---|---|---|---|
| RT-01 | Pilih jenis kasus: IoT, smart building, atau layanan AI [S40] | SEBAGIAN | Kandidat layanan AI (`backend/app/core/llm.py:123`) | Bergantung K2 dan masalah lapangan |
| RT-02 | Fungsi kritis berdasar dampak yang tidak dapat diterima [S17, S40] | BUTUH LAPANGAN | Kandidat di bagian 5.16 | Dampak ditetapkan pengguna |
| RT-03 | Layanan minimum per fungsi kritis [S17, S30] | BUTUH LAPANGAN | Kandidat di bagian 5.16 | Batas yang diterima pengguna |
| RT-04 | Pisahkan persyaratan wajib dari preferensi [S9] | SEBAGIAN | Kandidat W1 sampai W7 di bagian 5.16 | Pengesahan syarat, aturan kampus |
| RT-05 | Tiap skenario memuat pemicu, fungsi terdampak, kriteria, durasi, cakupan, kondisi awal [S19] | SEBAGIAN | Kandidat G1 sampai G7 di bagian 5.16 | Durasi dan kriteria final |
| RT-06 | Indikator fungsi minimum, dengan log dan hasil uji [S30] | BUTUH BANGUN | Belum ada | Log uji |
| RT-07 | Indikator waktu pemulihan, dengan timeline insiden [S30] | BUTUH BANGUN | Belum ada | Pencatatan waktu insiden |
| RT-08 | Indikator data hilang atau terlambat, dengan timestamp dan ID [S30] | SEBAGIAN | ID dan waktu rekam ada (`backend/app/models/submission.py:18`, `backend/app/models/submission.py:30`) | Waktu penilaian, log kejadian |
| RT-09 | Target RTO [S31] | BUTUH LAPANGAN | Belum ada. Contoh 30 menit di S31 hipotetis | Target dari dampak gangguan |
| RT-10 | Target RPO [S31] | BUTUH LAPANGAN | Belum ada. Contoh 5 menit di S31 hipotetis | Target dari dampak gangguan |
| RT-11 | Bandingkan hasil uji dengan RTO dan RPO [S31] | BUTUH BANGUN | Belum ada | Bergantung RT-09, RT-10, RS-10, RS-11 |
| RT-12 | Energi per fungsi berguna [S32] | BUTUH BANGUN | Belum ada | Alat ukur, unit fungsi mis. per submission dinilai |
| RT-13 | SCI dengan fungsi, batas sistem, dan asumsi yang sama [S32] | BUTUH BANGUN | Belum ada. Energi LLM cloud tidak terlihat dari kode | Batas sistem dan asumsi yang dinyatakan |
| RT-14 | Evaluasi berbasis skenario: risiko, titik sensitivitas, titik trade-off [S33] | BUTUH BANGUN | Belum ada | Bergantung RS-05 |
| RT-15 | Matriks berbobot dengan alasan bobot dan skala yang jelas [S34, S35] | BUTUH BANGUN | Belum ada. Contoh S34 adalah simulasi | Bobot dari kebutuhan stakeholder |
| RT-16 | Sensitivitas bobot keputusan [S35] | BUTUH BANGUN | Belum ada | Bergantung RT-15. Ini bukan definisi LK3-07 |
| RT-17 | Pemeriksaan Pareto antar-alternatif [S35] | BUTUH BANGUN | Belum ada | Bergantung RT-15 |
| RT-18 | Uji pemulihan: sinkronisasi, duplikasi, urutan, ID unik [S38] | BUTUH BANGUN | Belum ada | Lingkungan uji |
| RT-19 | Uji restore, bukan hanya keberadaan backup [S24, S38] | BUTUH BANGUN | Tidak ada backup | Prosedur backup dan restore |
| RT-20 | Manfaat dan konsekuensi keberlanjutan tiap alternatif [S13, S40] | BUTUH LAPANGAN | Belum ada | Data atau asumsi yang dinyatakan |
| RT-21 | Risiko residual tiap alternatif [S37, S40] | BUTUH BANGUN | Belum ada | Bergantung hasil uji |
| RT-22 | Tata kelola insiden: pemilik layanan, operator, jalur eskalasi [S39] | BUTUH LAPANGAN | Belum ada | Peran nyata di prodi |
| RT-23 | Prosedur pengambilalihan, restore, komunikasi status [S39] | BUTUH BANGUN | Belum ada | Dokumen prosedur dan uji |
| RT-24 | Tinjau penyebab dan ubah desain setelah perbaikan diuji [S39] | BUTUH BANGUN | Belum ada | Bergantung hasil uji |

### 5.13 Tahap 7: Finalization & UAS (P12)

| ID | Kewajiban | Status | Bukti | Yang kurang |
|---|---|---|---|---|
| T7-01 | Presentasi alur Problem sampai Impact | BUTUH LAPANGAN | Belum ada | Bergantung seluruh tahap |
| T7-02 | Demo prototipe | SEBAGIAN | Aplikasi ada, tetapi tidak dijalankan pada analisis ini. `backend/requirements.txt:1` tidak memuat beberapa paket yang ada di `backend/pyproject.toml:17` | Uji jalan penuh, data demo anonim |
| T7-03 | Jawaban atas pertanyaan penguji | SEBAGIAN | Bagian 3 dan 7 dokumen ini | Hasil lapangan |
| T7-04 | Paket akhir: seluruh artefak | BUTUH LAPANGAN | Belum ada | Bergantung seluruh tahap |
| T7-05 | Paket akhir: kode | SEBAGIAN | Repo ada. Data sudah dianonimkan dan `__pycache__` tidak lagi dilacak | Perbaiki README, putuskan penanganan riwayat git |
| T7-06 | Paket akhir: data uji | BUTUH BANGUN | Data uji kini sintetis (`backend/app/seed.py:96-98`) | Dokumentasikan data uji |
| T7-07 | Paket akhir: presentasi | BUTUH LAPANGAN | Belum ada | Bergantung T7-01 |
| T7-08 | Checklist: cerita utuh, demo berjalan, repo lengkap | BUTUH LAPANGAN | Belum ada | Bergantung seluruh tahap |

### 5.14 Aturan bukti (P12)

| ID | Kewajiban | Status | Bukti | Yang kurang |
|---|---|---|---|---|
| BK-01 | Alur Observe, Collect, Analyze, Identify Gap, Propose | BUTUH LAPANGAN | Repo dimulai dari Propose | Urutan harus dipulihkan, bagian 7 |
| BK-02 | Dapat diverifikasi pihak lain | SEBAGIAN | Rujukan kode dan riwayat git bisa diverifikasi | Bukti lapangan |
| BK-03 | Jelas sumber dan waktunya | SEBAGIAN | `created_at` di tabel, mis. `backend/app/models/submission.py:30` | Sumber lapangan |
| BK-04 | Relevan dengan masalah | BUTUH LAPANGAN | Belum ada | Bergantung T4-02 |
| BK-05 | Minimal dua sumber (triangulasi) | BUTUH LAPANGAN | Belum ada | Observasi dan wawancara |
| BK-06 | Terdokumentasi rapi | SEBAGIAN | Dokumen ini | Berkas bukti lapangan |

### 5.15 Canvas analisis bagian 6 (P12)

Canvas ini sama dengan T4-03 sampai T4-08, sehingga tidak dihitung dua kali dalam jumlah baris.

### 5.16 Bahan awal resiliensi EduCopilot sebagai layanan AI

**Semua isi subbagian ini kandidat.** Pemilihan final bergantung pada masalah dari lapangan. Kolom perilaku adalah perkiraan dari membaca kode, dan belum ada yang diuji.

**Dependensi nyata**

| Dependensi | Bukti | Perilaku saat gagal, dari kode |
|---|---|---|
| Penyedia LLM | `backend/app/core/config.py:39-43`, `backend/app/core/llm.py:132-140` | Penyedia dipilih dari kredensial, bukan dari keberhasilan panggilan. Jika penyedia pertama gagal, tidak ada perpindahan otomatis, walau komentar menyebut fallback (`backend/app/core/config.py:36`). Ollama selalu dianggap tersedia (`backend/app/core/llm.py:95-108`) |
| SQLite, satu file | `backend/app/core/config.py:25` | Tidak ada backup. Jika file hilang, start ulang membuat DB baru berisi seed tanpa peringatan (`backend/app/core/database.py:26`, `backend/app/core/database.py:40`) |
| ChromaDB lokal | `backend/app/core/rag.py:7`, `backend/app/core/rag.py:13` | Unggah materi tetap jalan (`backend/app/api/v1/materials.py:46-48`), pencarian mengembalikan 500 (`backend/app/api/v1/knowledge.py:256-257`). Status "Terindeks" ditulis sebelum indeks dicoba (`backend/app/api/v1/materials.py:174`, `backend/app/api/v1/materials.py:179`) |
| Model embedding | `backend/app/core/rag.py:11` | Perlu diuji saat tanpa jaringan |
| reportlab | `backend/app/services/pdf_generator.py:2` | Diimpor di level modul lewat dashboard (`backend/app/api/v1/dashboard.py:6`, `backend/app/main.py:4`). Jika paket hilang, aplikasi gagal start, bukan hanya ekspor PDF. Ini isolasi lemah menurut S21 |
| PyPDF2 | `backend/app/api/v1/materials.py:139-146` | Gagal lunak, teks materi kosong |
| Backend bagi frontend | `frontend/src/lib/api.ts:3-4`, `frontend/src/lib/api.ts:27-30` | Layout menangkap galat (`frontend/src/app/dashboard/layout.tsx:30-32`), halaman analitik tidak (`frontend/src/app/dashboard/analytics/page.tsx:20`) |
| Dosen sebagai pemicu dan pengunggah | `backend/app/api/v1/quiz.py:404`, `backend/app/api/v1/grading.py:14` | Tidak ada pemicu otomatis. Ini ketergantungan organisasi menurut S16 |

**Kandidat fungsi kritis dan layanan minimum**

| ID | Fungsi | Kandidat status | Butuh LLM? | Kandidat layanan minimum |
|---|---|---|---|---|
| FK1 | Penyimpanan jawaban dan nilai | Kritis | Tidak | Data tersimpan dan terbukti bisa dipulihkan |
| FK2 | Penilaian | Kritis | MCQ tidak (`backend/app/agents/grading_agent.py:46`), esai ya (`backend/app/agents/grading_agent.py:73`) | MCQ tetap dinilai, esai ditandai perlu dinilai manusia, bukan 0 |
| FK3 | Analitik dan alert kelas | Penting | Tidak (`backend/app/api/v1/dashboard.py:364`) | Tampil dengan penanda kesegaran data |
| FK4 | Kuis | Bisa ditunda | Pembuatan otomatis ya, manual tidak (`backend/app/api/v1/quiz.py:105`) | Input manual tetap tersedia |
| FK5 | RPS dan kepatuhan | Bisa ditunda | Pembuatan ya, katalog tidak (`backend/app/core/sndikti_catalog.py:710`) | Katalog tetap jalan |
| FK6 | RAG, materi otomatis, ekspor PDF | Tidak kritis | Sebagian | Boleh berhenti, dengan status jelas |

**Kandidat skenario gangguan, tanpa LLM berbayar**

Jalankan pada salinan DB sintetis di lingkungan uji, dengan LLM tiruan atau port mati. Durasi dan kriteria final ditetapkan tim. Dua skenario yang disarankan untuk memenuhi syarat minimum adalah G1 dan G4, karena mencakup sisi AI dan sisi data.

| ID | Pemicu | Fungsi | Kondisi awal dan cakupan | Kandidat kriteria penerimaan | Perkiraan saat ini |
|---|---|---|---|---|---|
| G1 | LLM tidak tersedia: `LLM_PROVIDER_ORDER=ollama`, `OLLAMA_BASE_URL` ke port mati (`backend/app/core/config.py:72`) | FK2 | Kuis campuran, submission belum dinilai | MCQ dinilai, esai ditandai perlu manusia, tidak ada nilai 0 final | Gagal. Esai 0, tanpa tanda di feedback, dan tidak dinilai ulang (`backend/app/agents/grading_agent.py:178-186`, `backend/app/api/v1/grading.py:27`) |
| G2 | LLM tiruan mengembalikan teks bukan JSON | FK2, FK5 | Penilaian dan pembuatan ulang RPS yang sudah ada | Data lama utuh, status gagal jelas | Gagal. Pertemuan kosong (`backend/app/agents/rps_agent.py:369`) lalu jadwal lama terhapus di `/generate` (`backend/app/api/v1/rps.py:485`, `backend/app/api/v1/rps.py:81`). Jalur `/regenerate` sudah dijaga (`backend/app/api/v1/rps.py:1353`) |
| G3 | Backend dihentikan saat penilaian batch | FK1, FK2 | LLM tiruan lambat, banyak submission | Tidak ada nilai setengah jadi, bisa diulang | Kemungkinan lulus. Commit setelah loop (`backend/app/api/v1/grading.py:98`), progres batch hilang tetapi bisa diulang |
| G4 | File DB salinan dihapus, lalu restore | FK1 | Backup dibuat sebelum uji | Data pulih, RTO dan RPO terukur, kehilangan terlihat | Gagal. Belum ada backup, dan aplikasi diam-diam mulai dari seed |
| G5 | Folder indeks RAG hilang | FK6 | Materi sudah terindeks | Fungsi utama jalan, status indeks jujur | Sebagian. Pencarian 500, status tetap "Terindeks" |
| G6 | CSV rusak, NIM asing, baris ganda | FK1 | Unggah jawaban | Data invalid ditandai, data baik masuk | Kemungkinan lulus (`backend/app/api/v1/quiz.py:437-446`, `backend/app/api/v1/quiz.py:466-470`) |
| G7 | Backend mati saat dashboard dibuka | FK3 | Frontend menyala | Status gangguan jelas | Perlu diuji |

Yang tidak bisa diuji murah: model drift, perubahan perilaku penyedia LLM, operator kurang, dan anggaran turun (S16, S27). Jika tidak terukur, nyatakan keterbatasan dan rencana pengukurannya, sesuai P11.

**Kandidat persyaratan wajib privasi**

Menurut S9, syarat wajib bersifat gugur dan skor tinggi tidak menggantikannya. Rumusan akhir perlu dicocokkan dengan aturan kampus (K8).

| ID | Kandidat syarat wajib | Kondisi prototipe | Bukti |
|---|---|---|---|
| W1 | Hanya pengguna berhak yang melihat nilai dan identitas mahasiswa | Belum terpenuhi | `backend/app/main.py:20-35`, `backend/app/api/v1/dashboard.py:402-410`, `backend/app/api/v1/students.py:40` |
| W2 | Identitas mahasiswa tidak dikirim ke LLM eksternal | Sebagian. Payload esai tanpa NIM dan nama, tetapi teks jawaban tetap terkirim dan penyedia awal cloud | `backend/app/agents/grading_agent.py:86-94`, `backend/app/core/config.py:39-43` |
| W3 | Data mahasiswa nyata tidak masuk repo | Terpenuhi untuk kondisi terbaru, tetapi DB tetap terlacak walau ada aturan `*.db` | `backend/app/seed.py:96-98`, `.gitignore:3` |
| W4 | Data dikumpulkan seperlunya | Sebagian. Kebutuhan kolom email belum dinilai | `backend/app/models/student.py:13-15` |
| W5 | Penghapusan terkendali, retensi jelas | Belum terpenuhi. Hapus tanpa autentikasi, retensi tidak ada | `backend/app/api/v1/students.py:175`, `backend/app/api/v1/quiz.py:551` |
| W6 | Nilai bisa diperiksa dan diubah manusia (S29) | Belum terpenuhi. Tidak ada endpoint ubah nilai | `backend/app/api/v1/grading.py:73-75` |
| W7 | Akses dan perubahan tercatat | Belum terpenuhi. Tidak ada audit (bagian 3.4) | `backend/app/api/v1/rps.py:81` |

Akibatnya, jika W1 disahkan, prototipe saat ini gugur sebelum masuk matriks keputusan, sampai A5 selesai.

Sketsa tiga alternatif, belum dinilai: A memakai LLM cloud dengan backup dan penanda gagal, B memakai model lokal dan aturan untuk fungsi kritis, C tanpa LLM untuk esai sehingga esai dinilai manusia.

---

## 6. Template dan sumber acuan

**Template tersedia** di `docs/template-asesmen-kematangan-digital-twinISOIEC 30186 - 2025.xlsx`, dengan lembar Ringkasan, Petunjuk, Identitas, dan Rubrik serta 25 indikator. File asli tidak diubah. Lembar Petunjuk menyatakan template ini adaptasi, bukan salinan resmi standar, dan keluarannya untuk roadmap, bukan sertifikasi.

**Draf** ada di `docs/draf-asesmen-kematangan-prototipe.xlsx`. Rumus, format, validasi, dan grafik dipertahankan, dengan penyesuaian tinggi baris supaya catatan terbaca. Kedua file diabaikan git dan tidak di-commit.

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

Panduan berprinsip "mulailah dari masalah nyata dan bukti lapangan, bukan dari teknologi" (P1). Repo ini kebalikannya: dibuat April sampai Juni 2026 untuk II5003 (`README.md:124`), sedangkan PDF panduan dibuat 2 November 2026.

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

Urutan besar: keputusan, lapangan buta, definisi masalah, desain dan metrik, bangun, uji, final. Pekerjaan "tanpa penyesalan" (A1 sampai A6) bisa berjalan paralel karena tidak mengunci masalah.

### (c) Keputusan pengguna, dikerjakan paling awal

| ID | Keputusan | Memblokir |
|---|---|---|
| K1 | Apakah kluster Smart Campus (Smart Education) diizinkan, mengingat Tahap 1 dan 2 menyebut 13 kluster? | Semua tahap |
| K2 | Apakah repo II5003 boleh dipakai ulang untuk KS5102? | Semua pekerjaan bangun |
| K3 | Batas sistem. **Sudah diputuskan: satu prodi.** Prodi mana yang dipilih masih perlu ditetapkan | Asesmen resmi, F1 |
| K4 | Siapa anggota tim, dan apakah roster di seed adalah anggota tim? | Pembagian kerja, anonimisasi |
| K5 | Minta artikel Imbar dkk. 2025 dan sumber acuan lain ke dosen. Template sudah ada | Definisi level Sistemik, A8 |
| K6 | Minta definisi Rasio fiscal, Sensitivitas, Polaritas loop panjang, Kondisi Γ−W | LK3 |
| K7 | Di mana repositori Living Lab, dan kapan tenggat tiap artefak? | Pengumpulan |
| K8 | Data apa yang akan dipakai, dan bagaimana izin atau persetujuan penggunaannya? | Tahap 6, F9 |
| K9 | Anggaran LLM, atau hanya model lokal? | Bangun dan uji |
| K10 | Apakah rubrik S41 dipakai, dan apakah tugas S40 sama dengan tugas nomor 7 panduan? | Bentuk laporan resiliensi |
| K11 | Untuk template: tanpa bukti bernilai 0 (rumus) atau 1 (Petunjuk), dan apakah tampilan data demo cukup untuk P1? | Skor draf |

Keputusan yang sudah ada: batas sistem satu prodi, serta kuis dan RPS turunan slide dibiarkan.

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
| A1 | Anonimkan DB dan seed, buang `__pycache__` terlacak | K4 | Selesai, kecuali riwayat git |
| A2 | Selaraskan README dengan kode (bagian 3.1) dan samakan daftar dependensi | Tidak ada | Sekarang |
| A3 | Uji jalan penuh aplikasi tanpa LLM berbayar, sebagai persiapan demo | Tidak ada | Sekarang |
| A4 | Alat uji: pytest dan LLM tiruan, tes jalur inti | Tidak ada | Sekarang |
| A5 | Autentikasi, peran, dan hak akses | K2, K3 | Sekarang atau setelah F4 |
| A6 | Log audit tersimpan: pelaku, waktu, versi, model | A5 | Sekarang atau setelah A5 |
| A7 | Draf pedoman observasi dan wawancara netral | K1 | Selesai: `docs/pedoman-lapangan-ganai.md` |
| A8 | Draf kuesioner Likert dan pertanyaan ya/tidak | K5 | Bisa mulai dari contoh P4, final setelah sumber tersedia |
| A9 | Isi draf baris SIAP: inventaris, peta alur data, I, G, L1, L2, in/out loop | K3 | Sekarang |
| A10 | Tinjauan manusia atas nilai: ubah nilai, status perlu review, gerbang persetujuan materi `AUTO` | K2 | Sekarang atau setelah F10 |
| A11 | Tetapkan metrik dan batas kelayakan, commit sebelum membangun | F10 | Setelah Tahap 4 |
| A12 | Pemetaan soal ke CPMK, ganti progres placeholder, simpan feedback esai | A11 | Setelah Tahap 4 |
| A13 | Tutup loop: ukur efek remedial, hidupkan atau hapus Remedial Agent, catat waktu kejadian | A11, A12 | Setelah Tahap 4 |
| A14 | Bangun L3: prediksi risiko dan what-if, sesuai sasaran maturity | A11, F9 | Setelah data ada |
| A15 | Model stock-flow dan skenario intervensi | F10 | Setelah Tahap 4 |
| A16 | Tiga alternatif desain, eksperimen gangguan, log, matriks, sensitivitas bobot, risiko residual | A4, A6, A19, K9, F13 | Setelah desain |
| A17 | Asesmen template batas satu prodi, susun presentasi dan paket akhir | F8, semua | Akhir. Draf prototipe selesai |
| A18 | Tim memeriksa draf template per indikator dan membuka bukti `file:baris` | K11 | Sekarang |
| A19 | Lingkungan uji gangguan: LLM tiruan, salinan DB sintetis, skrip backup dan restore, pencatat waktu | A4 | Sekarang |
| A20 | Perbaiki temuan ketahanan jika terbukti: tanda esai gagal, penjaga jadwal kosong, status indeks, perpindahan penyedia, peringatan DB baru | K2, A19 | Setelah G1 sampai G5 dijalankan |

### Urutan dan ketergantungan

1. **Minggu ini:** K1, K2, K4, K5, K6, K7, K10, K11, dan pemilihan prodi. Paralel: A2, A3, A4, A9, A18, A19. K8 dan K9 diputuskan sebelum fase bangun.
2. **Fase lapangan:** F1, F2, F3, F4, F5, F13. Paralel: A5, A6, A8.
3. **Fase ukur:** F6, F7, F8, lalu tabel maturity dan lembar kerja.
4. **Fase definisi:** F10, Tahap 4, leverage point. Di sini kriteria gugur diperiksa.
5. **Fase desain:** A11, Tahap 5, Tahap 6, A15.
6. **Fase bangun dan uji:** A10, A12, A13, A14, A16, A20, F9, F11.
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

## Lampiran: cara verifikasi

- Tabel dan isi DB: `sqlite3` mode baca pada salinan di luar repo. File asli diperiksa tetap identik dengan `cmp`.
- Skor katalog: `run_catalog` dijalankan pada salinan DB dengan objek sederhana, tanpa LLM, tanpa menulis bytecode.
- Pemakaian simbol: `grep` pada `backend/app` untuk `build_remedial_graph`, `retrieve_materials`, `tavily`, `notif.`, autentikasi, penjadwal.
- Rujukan `path:baris` di dokumen ini diperiksa keberadaannya dengan skrip.
- Draf xlsx: disunting langsung pada XML salinan template. Hash template asli diperiksa tetap sama. Rumus diverifikasi sama dengan template, lalu Ringkasan dihitung ulang dengan mesin rumus terpisah, dan hasilnya cocok dengan nilai tersimpan. `fullCalcOnLoad` aktif.
- Tidak diverifikasi: perilaku aplikasi saat berjalan, build frontend, mutu keluaran LLM, tampilan draf xlsx di Excel atau LibreOffice, dan seluruh perkiraan perilaku di bagian 5.16.
