# Draf lembar kerja lengkap — A9

Versi draf: 7 November 2026. Acuan kode: branch `test/alat-uji`, HEAD `01b446d3e3231af2dbe3cae892f846167015b941`. Kerangka dan urutan mengikuti `docs/Panduan Tugas Mahasiswa GanAI - SO.pdf`, halaman 3–11, dibaca dengan `pdftotext -layout`. Canvas halaman 12 diletakkan pada Tahap 4 sebagaimana diperintahkan halaman 7. Acuan pendamping: `docs/analisis-gap-ganai.md`, terutama bagian 3, 4, 5, dan 8; serta `docs/pedoman-lapangan-ganai.md`.

**Keputusan yang ada: batas satu prodi, identitas prodi belum ditentukan. Smart Education masih kluster kandidat, belum dikonfirmasi dosen.** Tidak ada skor hasil pengumpulan, temuan prodi, manfaat, atau komitmen organisasi yang dinyatakan dalam draf ini.

“Sistem saat ini” selalu berarti kondisi prodi. Sel prototipe memuat kode HEAD dan bukti uji lokal sintetis, bukan jawaban tentang prodi atau bukti operasi/dampak kampus. Pengukuran Ollama lokal, E1/E2, lint/build dan audit produksi dibedakan dari asumsi rancangan. Pembaruan dokumen ini tidak menjalankan aplikasi ulang; backend HEAD identik dengan versi uji resiliensi 972ad7b. Rujukan file:baris diperiksa otomatis terhadap HEAD dan dibaca pada fungsi terkait.

Aturan label:

- `[PROTOTIPE]`: isi dari kode atau uji sintetis lokal, dengan rujukan `file:baris` pada setiap sel. Tidak boleh disalin menjadi keadaan prodi.
- `[BUTUH LAPANGAN]`: jawaban prodi kosong (`____`), diikuti bukti yang diminta dan peran sumbernya. Definisi, kategori, kode baris, dan judul kolom adalah kerangka; label pada kerangka menunjukkan status pengisian terkait, bukan temuan. **Semua sel tabel, termasuk judul kolom, memiliki tepat satu label.** Sel kerangka dibaca bersama permintaan bukti pada barisnya.
- `[TANYA DOSEN]`: definisi atau aturan belum tersedia; tidak diisi dengan tafsiran tim.

Kode bukti mengikuti pedoman lapangan: `OBS____` untuk sesi observasi, `OBS____-F____` untuk foto, `WWC____-MHS`, `WWC____-DSN`, `WWC____-TDK`, `WWC____-KPR`, `WWC____-PSD`, `DOK____`, `TKL____`, dan `SD____`. Masalah memakai `M____`. Semuanya pola isian, bukan bukti terkumpul. Peran: mahasiswa, dosen, tenaga kependidikan, koordinator prodi, pengelola sistem atau data. Jangan tulis nama orang.

Daftar bukti pedoman bagian 8.2 memuat ID, jenis, peran sumber, tanggal/jam, lokasi, letak berkas, dan kaitan masalah. Gunakan minimal dua sumber berbeda jenis atau stakeholder untuk masalah (bagian 8.3), minta konfirmasi pengelola, dan catat perbedaan. Bukti kode tidak menggantikan bukti lapangan. Persetujuan, rekaman, dan data pribadi tetap di penyimpanan terbatas di luar repo.

Bukti tambahan lokal: `docs/bukti-uji/ollama-20261106/` memakai qwen3.5:9b dan bge-m3; keberhasilan JSON dan nilai berulang tidak membuktikan kesesuaian dengan dosen. E1/E2 memakai tiruan. `docs/bukti-uji/frontend-20261107/laporan.md` mencatat lint 0 error/0 warning dan audit produksi 0; audit lengkap masih delapan entri sedang dari satu advisori minimatch dev. Backup CLI tidak berarti backup terjadwal/terenkripsi; replay jawaban tidak memulihkan seluruh riwayat nilai/audit dan mengubah created_at rekaman pascabackup.

Ringkasan label sel tabel (header ikut dihitung, baris pemisah tidak): PROTOTIPE 40 → 53, BUTUH LAPANGAN 409 → 402, TANYA DOSEN 21 → 21; total 470 → 476. Label pada penjelasan di luar tabel tidak dihitung. Seluruh sel tetap memiliki tepat satu label; perubahan hanya menambah/memperbarui keterangan prototipe.

## 1. Kematangan tiga perspektif — halaman 4

Nama level di bawah adalah kerangka panduan, bukan hasil prodi. Instrumen pengumpulan ada di `docs/kuesioner-maturity.md`.

| [BUTUH LAPANGAN] Perspektif (kerangka kolom) | [BUTUH LAPANGAN] Yang dinilai (kerangka kolom) | [BUTUH LAPANGAN] Level 1 (kerangka kolom) | [BUTUH LAPANGAN] Level 2 (kerangka kolom) | [BUTUH LAPANGAN] Level 3 (kerangka kolom) | [BUTUH LAPANGAN] Level 4 (kerangka kolom) | [BUTUH LAPANGAN] Isian prodi (kerangka kolom) |
| --- | --- | --- | --- | --- | --- | --- |
| [BUTUH LAPANGAN] Antroposentris | [BUTUH LAPANGAN] Kecerdasan manusia dalam melayani melalui layanan | [BUTUH LAPANGAN] Tidak memuaskan (Unsatisfactory) | [BUTUH LAPANGAN] Memadai (Sufficient) | [BUTUH LAPANGAN] Cakap (Proficient) | [BUTUH LAPANGAN] Teladan (Exemplary) | [BUTUH LAPANGAN] ____; Kumpulkan Likert mahasiswa, dosen, dan pejabat struktural untuk layanan serta periode yang sama. |
| [BUTUH LAPANGAN] Sistemik | [BUTUH LAPANGAN] Otomasi dan integrasi siklus sistem | [TANYA DOSEN] Impulsif (Impulsive); minta definisi operasional dosen. | [TANYA DOSEN] Reaktif (Reactive); minta definisi operasional dosen. | [TANYA DOSEN] Responsif (Responsive); minta definisi operasional dosen. | [TANYA DOSEN] Berinisiatif (Initiative); minta definisi operasional dosen. | [BUTUH LAPANGAN] ____; Minta jawaban bertingkat, alur, SOP, dan demonstrasi dari PSD/TDK; konfirmasi KPR. |
| [BUTUH LAPANGAN] Teknologi | [BUTUH LAPANGAN] Sejauh mana teknologi informasi dipakai | [BUTUH LAPANGAN] Tidak memakai teknologi | [BUTUH LAPANGAN] Dipakai di sebagian sistem | [BUTUH LAPANGAN] Dipakai sesuai kebutuhan | [BUTUH LAPANGAN] Dipakai di seluruh sistem | [BUTUH LAPANGAN] ____; Minta inventaris proses, kebutuhan, dan pemakaian aktual dari PSD/TDK; konfirmasi KPR. |

| [BUTUH LAPANGAN] Kluster (kerangka kolom) | [BUTUH LAPANGAN] Rata-rata Antroposentris (kerangka kolom) | [BUTUH LAPANGAN] Rata-rata Sistemik (kerangka kolom) | [BUTUH LAPANGAN] Rata-rata Teknologi (kerangka kolom) |
| --- | --- | --- | --- |
| [BUTUH LAPANGAN] ____; Kandidat Smart Education; perlu bukti masalah dari observasi/wawancara dan konfirmasi kluster oleh dosen. | [BUTUH LAPANGAN] ____; Rekap A8 dari mahasiswa/dosen/pejabat struktural; belum ada jawaban. | [TANYA DOSEN] ____; Minta rumus rata-rata dari ya/tidak kepada dosen; belum dihitung. | [TANYA DOSEN] ____; Minta rumus rata-rata dari ya/tidak kepada dosen; belum dihitung. |

Kesimpulan tiga perspektif: ____; Menunggu bukti, rumus, dan konfirmasi. Panduan tidak menjelaskan konversi rata-rata menjadi Level 1–4. Contoh 3,44 bukan hasil prodi dan bukan aturan konversi. Jangan memindahkan perkiraan prototipe dalam analisis gap ke asesmen prodi.

## 2. Kematangan digital twin — halaman 5

Lima level panduan terpisah dari skala template asesmen; jangan mengonversi salah satunya ke yang lain. Kolom Level, Nama, dan Kemampuan dipertahankan, dengan tambahan isian bukti.

| [BUTUH LAPANGAN] Level (kerangka kolom) | [BUTUH LAPANGAN] Nama (kerangka kolom) | [BUTUH LAPANGAN] Kemampuan menurut panduan (kerangka kolom) | [BUTUH LAPANGAN] Bukti kondisi prodi (kerangka kolom) |
| --- | --- | --- | --- |
| [BUTUH LAPANGAN] 1 | [BUTUH LAPANGAN] Deskriptif (Descriptive) | [BUTUH LAPANGAN] Model digital terhubung ke sistem nyata, tanpa kecerdasan, pembelajaran, atau otonomi. | [BUTUH LAPANGAN] ____; Minta hubungan model–kejadian nyata dan waktu pembaruan dari PSD/TDK. |
| [BUTUH LAPANGAN] 2 | [BUTUH LAPANGAN] Informatif (Informative) | [BUTUH LAPANGAN] Data diubah menjadi wawasan. | [BUTUH LAPANGAN] ____; Minta data operasional sampai analisis dan contoh pemakaian hasil dari PSD/TDK. |
| [BUTUH LAPANGAN] 3 | [BUTUH LAPANGAN] Prediktif (Predictive) | [BUTUH LAPANGAN] Data operasional dipakai untuk analitik dan prediksi. | [BUTUH LAPANGAN] ____; Minta riwayat, prediksi, horizon, dan pembanding aktual dari PSD/dosen. |
| [BUTUH LAPANGAN] 4 | [BUTUH LAPANGAN] Komprehensif (Comprehensive) | [BUTUH LAPANGAN] Belajar dari beragam sumber dan analitik waktu nyata melalui simulasi bagaimana-jika. | [BUTUH LAPANGAN] ____; Minta sumber, waktu pembaruan, skenario, dan validasi simulasi dari PSD/KPR. |
| [BUTUH LAPANGAN] 5 | [BUTUH LAPANGAN] Otonom (Autonomous) | [BUTUH LAPANGAN] Belajar dan mengurangi intervensi manusia melalui analitik dan keputusan otomatis. | [BUTUH LAPANGAN] ____; Minta riwayat keputusan/perubahan, batas kewenangan, pengecualian, dan pengawasan dari PSD/KPR. |

Kesimpulan level prodi: ____; Isi setelah verifikasi dan konfirmasi pengelola. Panduan menyatakan manusia aktif dalam operasi pada level 1–4 dan terutama mengawasi pada level 5. Model data atau tombol prototipe tidak membuktikan level prodi.

## 3. Complicated dan complex — soal 1, halaman 5–6

Kategori adalah arah penelusuran, bukan temuan. Complicated: dapat diurai menjadi langkah/aturan. Complex: perlu menelusuri interaksi dan adaptasi yang tidak cukup dijelaskan satu prosedur.

| [BUTUH LAPANGAN] No (kerangka kolom) | [BUTUH LAPANGAN] Kategori (kerangka kolom) | [BUTUH LAPANGAN] Complicated: kondisi prodi (kerangka kolom) | [BUTUH LAPANGAN] Complex: kondisi prodi (kerangka kolom) | [BUTUH LAPANGAN] Catatan prototipe terpisah (kerangka kolom) |
| --- | --- | --- | --- | --- |
| [BUTUH LAPANGAN] 1 | [BUTUH LAPANGAN] Alur dokumen pembelajaran | [BUTUH LAPANGAN] ____; Minta SOP, tahapan, pengecualian, dan observasi satu pengurusan dari dosen/TDK. | [BUTUH LAPANGAN] ____; Gali koordinasi, perubahan cara kerja, dan respons terhadap pengecualian dari dosen/TDK/KPR; cocokkan observasi. | [PROTOTIPE] Graf penyusunan mempunyai simpul dan urutan eksplisit di `backend/app/agents/rps_agent.py:450-482`; struktur ini tidak membuktikan mutu keluaran atau proses prodi. |
| [BUTUH LAPANGAN] 2 | [BUTUH LAPANGAN] Pengolahan dan penafsiran hasil belajar | [BUTUH LAPANGAN] ____; Minta aturan penilaian, alur pengolahan, dan contoh tersamar dari dosen/TDK. | [BUTUH LAPANGAN] ____; Gali interaksi umpan balik, strategi belajar, dan respons pengguna dari mahasiswa/dosen pada beberapa waktu. | [PROTOTIPE] Katalog menjalankan pemeriksa berbobot di `backend/app/core/sndikti_catalog.py:710`; kelompok skor memakai ambang di `backend/app/core/stats.py:221`. Ini aturan prototipe, bukan perilaku kelas. |

## 4. E/I/G/D/F/S — soal 2, halaman 6

Kolom Kode, Konstruk, dan Deskripsi mengikuti panduan dalam Bahasa Indonesia. Komponen sesuai kluster adalah isian prodi; bukti kode ditempatkan terpisah.

| [BUTUH LAPANGAN] Kode (kerangka kolom) | [BUTUH LAPANGAN] Konstruk (kerangka kolom) | [BUTUH LAPANGAN] Deskripsi (kerangka kolom) | [BUTUH LAPANGAN] Komponen sesuai kluster: prodi (kerangka kolom) | [BUTUH LAPANGAN] Catatan prototipe terpisah (kerangka kolom) |
| --- | --- | --- | --- | --- |
| [BUTUH LAPANGAN] E | [BUTUH LAPANGAN] Elemen / batas | [BUTUH LAPANGAN] Aktor, lokasi, unit analisis, dan cakupan proses dinyatakan. | [BUTUH LAPANGAN] ____; Minta peta aktor, lokasi, layanan, batas masuk/keluar, dan unit analisis dari KPR/TDK; konfirmasi pengguna. | [PROTOTIPE] Unit data mata kuliah ada di `backend/app/models/course.py:8`, kuis di `backend/app/models/quiz.py:8`, dan jawaban di `backend/app/models/submission.py:8`; bukan batas operasional prodi. |
| [BUTUH LAPANGAN] I | [BUTUH LAPANGAN] Interkoneksi | [BUTUH LAPANGAN] Relasi data, fisik, statistik, atau hierarki dinyatakan. | [BUTUH LAPANGAN] ____; Minta peta aliran informasi, contoh perpindahan berkas, dan struktur koordinasi dari PSD/TDK/KPR. | [PROTOTIPE] Kuis menyimpan course_id di `backend/app/models/quiz.py:12`; jawaban menyimpan quiz_id di `backend/app/models/submission.py:19`. Ini relasi logis, bukan bukti integrasi prodi. |
| [BUTUH LAPANGAN] G | [BUTUH LAPANGAN] Tujuan / aturan keputusan | [BUTUH LAPANGAN] Tujuan, ambang, prioritas, atau aturan optimasi dinyatakan. | [BUTUH LAPANGAN] ____; Minta SOP, target, dasar ambang, prioritas, dan contoh keputusan dari KPR/dosen/TDK. | [PROTOTIPE] Batas lulus bawaan 60 di `backend/app/core/stats.py:63`; kelompok skor memakai 75/60 di `backend/app/core/stats.py:224`; catatan kepatuhan memakai 85 di `backend/app/api/v1/dashboard.py:260`. Dasarnya belum diverifikasi pada prodi. |
| [BUTUH LAPANGAN] D | [BUTUH LAPANGAN] Jeda / waktu | [BUTUH LAPANGAN] Waktu bermakna: horizon, panel, latensi, atau perkembangan operasi. | [BUTUH LAPANGAN] ____; Minta cap waktu kejadian, pencatatan, keputusan, tindakan, dan hasil dari TDK/dosen/PSD; bukan perkiraan tim. | [PROTOTIPE] Materi diberi minggu kuis + 1 di `backend/app/agents/auto_material_agent.py:99`; reviewed_at dan waktu audit juga ada (`backend/app/models/submission.py:35-39`, `backend/app/models/audit.py:15-26`). Ini bukan ukuran jeda hasil belajar prodi. |
| [BUTUH LAPANGAN] F | [BUTUH LAPANGAN] Umpan balik | [BUTUH LAPANGAN] Jalur tertutup: observasi → keputusan/tindakan → kondisi berubah → observasi kembali. | [BUTUH LAPANGAN] ____; Minta jejak kasus sampai evaluasi hasil dari dosen/TDK/KPR, dengan ukuran sebelum/sesudah dan waktunya. | [PROTOTIPE] Penerapan temuan memanggil penghitungan ulang di `backend/app/api/v1/rps.py:1046`; penghitungan ada di `backend/app/api/v1/rps.py:233`. Ini bukan bukti perbaikan hasil belajar. |
| [BUTUH LAPANGAN] S | [BUTUH LAPANGAN] Stok–aliran | [BUTUH LAPANGAN] Akumulasi ditulis sebagai neraca, dengan satuan keadaan dan satuan laju. | [BUTUH LAPANGAN] ____; Minta jumlah pekerjaan masuk, selesai, dibatalkan, dan tersisa per periode dari TDK/PSD; sepakati batas hitung dengan KPR. | [PROTOTIPE] Antrean jawaban tanpa skor dihitung di `backend/app/core/stats.py:279`; kandidat stok dalam satuan jawaban, belum persamaan neraca atau laju. |

## 5. Pemenuhan komponen dan kebutuhan D/F — soal 2a–2b, halaman 6

| [BUTUH LAPANGAN] Komponen soal 2a (kerangka kolom) | [BUTUH LAPANGAN] Terpenuhi pada prodi? (kerangka kolom) | [BUTUH LAPANGAN] Bukti jelas yang perlu diminta (kerangka kolom) |
| --- | --- | --- |
| [BUTUH LAPANGAN] E — Elemen / batas | [BUTUH LAPANGAN] ____; Isi ada/tidak/sebagian setelah konfirmasi sumber pada kolom berikut. | [BUTUH LAPANGAN] ____; Minta peta aktor, lokasi, layanan, batas masuk/keluar, dan unit analisis dari KPR/TDK; konfirmasi pengguna. Catat ID bukti, waktu, dan konfirmasi. |
| [BUTUH LAPANGAN] I — Interkoneksi | [BUTUH LAPANGAN] ____; Isi ada/tidak/sebagian setelah konfirmasi sumber pada kolom berikut. | [BUTUH LAPANGAN] ____; Minta peta aliran informasi, contoh perpindahan berkas, dan struktur koordinasi dari PSD/TDK/KPR. Catat ID bukti, waktu, dan konfirmasi. |
| [BUTUH LAPANGAN] G — Tujuan / aturan keputusan | [BUTUH LAPANGAN] ____; Isi ada/tidak/sebagian setelah konfirmasi sumber pada kolom berikut. | [BUTUH LAPANGAN] ____; Minta SOP, target, dasar ambang, prioritas, dan contoh keputusan dari KPR/dosen/TDK. Catat ID bukti, waktu, dan konfirmasi. |
| [BUTUH LAPANGAN] D — Jeda / waktu | [BUTUH LAPANGAN] ____; Isi ada/tidak/sebagian setelah konfirmasi sumber pada kolom berikut. | [BUTUH LAPANGAN] ____; Minta cap waktu kejadian, pencatatan, keputusan, tindakan, dan hasil dari TDK/dosen/PSD; bukan perkiraan tim. Catat ID bukti, waktu, dan konfirmasi. |
| [BUTUH LAPANGAN] F — Umpan balik | [BUTUH LAPANGAN] ____; Isi ada/tidak/sebagian setelah konfirmasi sumber pada kolom berikut. | [BUTUH LAPANGAN] ____; Minta jejak kasus sampai evaluasi hasil dari dosen/TDK/KPR, dengan ukuran sebelum/sesudah dan waktunya. Catat ID bukti, waktu, dan konfirmasi. |
| [BUTUH LAPANGAN] S — Stok–aliran | [BUTUH LAPANGAN] ____; Isi ada/tidak/sebagian setelah konfirmasi sumber pada kolom berikut. | [BUTUH LAPANGAN] ____; Minta jumlah pekerjaan masuk, selesai, dibatalkan, dan tersisa per periode dari TDK/PSD; sepakati batas hitung dengan KPR. Catat ID bukti, waktu, dan konfirmasi. |

**Penalaran konseptual soal 2b.** D perlu direpresentasikan ketika jeda antara kejadian, keputusan, tindakan, dan hasil memengaruhi keputusan. Hasil yang belum tampak dapat disalahartikan sebagai kegagalan sehingga koreksi berulang menjadi berlebihan. F perlu diperiksa bila analisis menjelaskan pengaturan atau perbaikan berulang: hasil tindakan harus diamati kembali untuk menilai perubahan selisih terhadap tujuan. Elemen, hubungan, dan tujuan saja belum membuktikan umpan balik tertutup. Bentuk D/F harus mengikuti perilaku yang ditemukan. Rujukan umum: *Thinking in Systems* (Meadows) dan *Business Dynamics* (Sterman), tanpa klaim halaman tertentu.

| [BUTUH LAPANGAN] Soal 2b (kerangka kolom) | [BUTUH LAPANGAN] Jawaban empiris prodi (kerangka kolom) | [BUTUH LAPANGAN] Bukti dan pemberi (kerangka kolom) |
| --- | --- | --- |
| [BUTUH LAPANGAN] Apakah D perlu ada pada kasus? | [BUTUH LAPANGAN] ____; Putuskan setelah alur dan pengaruh jeda diketahui dari TDK/dosen/KPR. | [BUTUH LAPANGAN] ____; Minta cap waktu kejadian–tindakan–hasil dari PSD/TDK dan pengalaman menunggu dari pengguna. |
| [BUTUH LAPANGAN] Apakah F perlu ada pada kasus? | [BUTUH LAPANGAN] ____; Putuskan setelah tujuan dan evaluasi diketahui dari KPR/dosen/TDK. | [BUTUH LAPANGAN] ____; Minta catatan kondisi awal, keputusan, tindakan, hasil lanjutan, dan perubahan berikutnya dari pelaksana serta pengelola. |

## 6. Konsep loop — soal 3, halaman 6–7

Seluruh sepuluh baris termasuk kelanjutan halaman 7 dipertahankan. Empat istilah tanpa definisi tidak diisi dengan perkiraan.

| [BUTUH LAPANGAN] Konsep (kerangka kolom) | [BUTUH LAPANGAN] Pemetaan kluster: kondisi prodi (kerangka kolom) | [BUTUH LAPANGAN] Catatan prototipe atau batas pengisian (kerangka kolom) |
| --- | --- | --- |
| [BUTUH LAPANGAN] Loop penguatan (Reinforcing loop) | [BUTUH LAPANGAN] ____; Minta rangkaian ketika perubahan memperbesar perubahan berikutnya dari mahasiswa/dosen/TDK; kumpulkan variabel, satuan, perubahan lintas waktu, dan penjelasan alternatif. | [PROTOTIPE] AUTO disimpan pending_review (`backend/app/agents/auto_material_agent.py:171-194`), diindeks sesudah approve (`backend/app/api/v1/materials.py:270-291`); manusia dapat memilih materi di `frontend/src/app/dashboard/quiz/new/KnowledgeMaterialPicker.tsx:88`. Ini calon jalur pengulangan, belum bukti penguatan dampak. |
| [BUTUH LAPANGAN] Reinforcing negatif / keruntuhan | [BUTUH LAPANGAN] ____; Gali kemungkinan penurunan yang saling memperkuat dari mahasiswa/dosen/TDK; minta urutan kejadian dan ukuran berulang tanpa menganggap keruntuhan terjadi. | [BUTUH LAPANGAN] ____; Minta perilaku berulang dan sumber pembanding dari pengguna/pengelola; fitur tidak membuktikan keruntuhan layanan. |
| [BUTUH LAPANGAN] Penyeimbang tanpa jeda (Balancing tanpa delay) | [BUTUH LAPANGAN] ____; Minta penyimpangan, koreksi, dan hasil dari TDK/dosen; periksa apakah jeda dapat diabaikan pada skala analisis. | [PROTOTIPE] Perubahan diikuti penghitungan ulang pada jalur yang sama di `backend/app/api/v1/rps.py:1046`; fungsi di `backend/app/api/v1/rps.py:233`. Kandidat koreksi tanpa jeda yang dimodelkan; bukan latensi nol terukur. |
| [BUTUH LAPANGAN] Penyeimbang respons agresif | [BUTUH LAPANGAN] ____; Minta beberapa episode koreksi, besar perubahan tindakan, akibat, dan waktu dari TDK/dosen/KPR; jangan menganggap koreksi berlebihan sudah terjadi. | [BUTUH LAPANGAN] ____; Minta dasar kekuatan respons dan pengaruhnya dari pengelola/pelaksana; keberadaan ambang tidak cukup. |
| [BUTUH LAPANGAN] Penyeimbang dengan jeda | [BUTUH LAPANGAN] ____; Minta jeda tindakan–hasil dan ukuran sebelum/sesudah dari dosen/mahasiswa/TDK. | [PROTOTIPE] Pembuatan materi menunggu nilai final lengkap di `backend/app/core/grade_review.py:65-87` dan diberi minggu berikutnya di `backend/app/agents/auto_material_agent.py:99`; baru jalur tindakan, belum loop hasil belajar tertutup atau ukuran jeda aktual. |
| [TANYA DOSEN] Rasio fiscal — definisi belum tersedia. | [TANYA DOSEN] ____; Mohon definisi, rumus, pembilang/penyebut, satuan, dan contoh dari dosen. Jangan langsung menganggap rasio anggaran. | [TANYA DOSEN] ____; Minta dosen menetapkan bukti, pihak sumber, dan cara menghitung setelah definisi jelas. |
| [TANYA DOSEN] Sensitivitas — pada tabel loop; definisi belum tersedia. | [TANYA DOSEN] ____; Mohon variabel, keluaran, rentang, dan metode dari dosen. Jangan samakan dengan sensitivitas bobot matriks desain. | [TANYA DOSEN] ____; Minta contoh pengerjaan dan bukti dari dosen sebelum memilih data/perhitungan. |
| [BUTUH LAPANGAN] Polaritas loop | [BUTUH LAPANGAN] ____; Minta diagram bertanda, alasan setiap arah hubungan, dan bukti perubahan dari dosen/TDK/KPR; periksa seluruh lintasan tertutup. | [PROTOTIPE] Tindakan penerapan temuan → penghitungan ulang ada di `backend/app/api/v1/rps.py:1046`. Tanda seluruh loop belum terbukti; jangan menganggap skor selalu meningkat. |
| [TANYA DOSEN] Polaritas loop panjang — definisi belum tersedia. | [TANYA DOSEN] ____; Mohon arti panjang: jumlah hubungan, horizon waktu, atau makna lain, beserta cara menentukan tanda dan contoh dari dosen. | [TANYA DOSEN] ____; Minta dosen menetapkan horizon, diagram, serta bukti; jangan menganggap otomatis berarti antarsemester. |
| [TANYA DOSEN] Kondisi Gamma-W (Γ−W) — notasi panduan; definisi belum tersedia. | [TANYA DOSEN] ____; Mohon arti simbol, persamaan/kondisi, satuan, dan contoh dari dosen. | [TANYA DOSEN] ____; Minta dosen menetapkan kriteria pemenuhan dan data; jangan mengarang rumus/ambang. |

## 7. L1–L3 — soal 4, halaman 7

Kolom asli dipertahankan. Baris pertama untuk prodi, baris kedua hanya pembacaan prototipe.

| [BUTUH LAPANGAN] L1 — Persepsi (Perception) (kerangka kolom) | [BUTUH LAPANGAN] L2 — Pemahaman (Comprehension) (kerangka kolom) | [BUTUH LAPANGAN] L3 — Proyeksi (Projection) (kerangka kolom) |
| --- | --- | --- |
| [BUTUH LAPANGAN] ____; Minta informasi yang diterima, sumber, waktu, dan pengguna dari TDK/PSD/dosen; amati proses. | [BUTUH LAPANGAN] ____; Minta contoh penafsiran keadaan terhadap tujuan dan keputusan aktual dari dosen/TDK/KPR. | [BUTUH LAPANGAN] ____; Minta prakiraan keadaan mendatang, horizon, asumsi, dan pembanding aktual dari KPR/dosen/PSD. |
| [PROTOTIPE] Unggah CSV di `backend/app/api/v1/quiz.py:417` dan hitungan jawaban menunggu nilai di `backend/app/api/v1/dashboard.py:42`; bukan pengamatan prodi. | [PROTOTIPE] Kelompok skor di `backend/app/core/stats.py:221` dan ringkasan di `backend/app/core/stats.py:244`; progres CPMK dinyatakan sebagai pengganti sementara di `backend/app/core/stats.py:136`. | [PROTOTIPE] Kelompok pada `backend/app/core/stats.py:221` memakai skor tersedia; penetapan minggu di `backend/app/agents/auto_material_agent.py:99` juga bukan model prediksi. Kedua potongan ini tidak membuktikan L3. |

## 8. Kebutuhan L1–L3 dan penghilangan komponen — soal 4a–4b, halaman 7

**Penalaran soal 4a.** Dalam kerangka tiga tingkat kesadaran situasional, L1 menyediakan keadaan yang dipersepsi, L2 memberi makna terhadap tujuan, dan L3 memproyeksikan perkembangan yang relevan bagi keputusan. Untuk menyatakan cakupan ketiga tingkat, ketiganya perlu diperiksa. Tampilan data belum membuktikan pemahaman/proyeksi; otomasi atau kecepatan layanan juga bukan penggantinya. Kebutuhan horizon proyeksi mengikuti keputusan kasus. Rujukan umum: *Toward a Theory of Situation Awareness in Dynamic Systems* (Endsley), tanpa kutipan atau nomor halaman.

**Simulasi penalaran soal 4b, bukan hasil eksperimen.** Tanpa L1, informasi keadaan aktual tidak tersedia sebagai masukan memadai untuk pemahaman/proyeksi. Tanpa L2, data dapat terlihat tetapi makna dan prioritas terhadap tujuan tidak dijelaskan. Tanpa L3, keadaan sekarang dapat dipahami tetapi akibat lanjut tidak diproyeksikan secara eksplisit. Akibat pada prodi belum diketahui. Rancangan berikut menunggu data kasus serta izin lingkungan uji; jangan menghilangkan informasi dari layanan operasional.

| [BUTUH LAPANGAN] Skenario 4b (kerangka kolom) | [BUTUH LAPANGAN] Rancangan kasus prodi (kerangka kolom) | [BUTUH LAPANGAN] Ukuran / bukti (kerangka kolom) | [BUTUH LAPANGAN] Hasil (kerangka kolom) |
| --- | --- | --- | --- |
| [BUTUH LAPANGAN] Tanpa L1 | [BUTUH LAPANGAN] ____; Pilih kasus tersamar bersama dosen/TDK; bandingkan informasi lengkap dan keadaan yang disembunyikan dalam simulasi. | [BUTUH LAPANGAN] ____; Sepakati kecukupan informasi, ketepatan/waktu keputusan, dan pembanding dengan KPR/dosen. | [BUTUH LAPANGAN] ____; Belum diuji; minta catatan skenario, waktu, dan tanggapan peserta dari dosen/TDK. |
| [BUTUH LAPANGAN] Tanpa L2 | [BUTUH LAPANGAN] ____; Tampilkan data yang sama tanpa hubungan/konteks tujuan pada simulasi bersama dosen/TDK. | [BUTUH LAPANGAN] ____; Minta kriteria pemahaman, alasan keputusan, dan waktu dari dosen/KPR. | [BUTUH LAPANGAN] ____; Belum diuji; kumpulkan hasil dan alasan keputusan dari peserta dengan persetujuan. |
| [BUTUH LAPANGAN] Tanpa L3 | [BUTUH LAPANGAN] ____; Gunakan kasus masa lalu bersama KPR/dosen; bandingkan dukungan dengan/tanpa proyeksi memakai informasi yang tersedia saat itu. | [BUTUH LAPANGAN] ____; Minta horizon, akibat aktual, dan kriteria prakiraan dari KPR/dosen/PSD; cegah informasi masa depan masuk ke masukan. | [BUTUH LAPANGAN] ____; Belum diuji; minta keluaran simulasi dan pembanding aktual dari pemilik data. |

## 9. Peran manusia — soal 5, halaman 7

Keberadaan endpoint bukan bukti kewenangan. Batas peran pada prodi harus dibuktikan melalui proses dan kebijakan.

| [BUTUH LAPANGAN] Sudut pandang (kerangka kolom) | [BUTUH LAPANGAN] Peranan (kerangka kolom) | [BUTUH LAPANGAN] Bukti dan kapan berperan (kerangka kolom) | [BUTUH LAPANGAN] Catatan prototipe terpisah (kerangka kolom) |
| --- | --- | --- | --- |
| [BUTUH LAPANGAN] In the loop — di dalam proses | [BUTUH LAPANGAN] ____; Minta aktor pemberi keputusan/persetujuan per kejadian dari dosen/TDK/KPR. | [BUTUH LAPANGAN] ____; Minta SOP, contoh keputusan, waktu persetujuan, dan pelaksanaan dari pihak yang berperan. | [PROTOTIPE] Sesi/peran/scope memeriksa tindakan (`backend/app/core/auth.py:119-260`); admin/dosen edit/approve esai ber-versi (`backend/app/api/v1/grading.py:206-321`), AUTO perlu approve (`backend/app/api/v1/materials.py:270-291`). Belum mandat prodi. |
| [BUTUH LAPANGAN] On the loop — memantau | [BUTUH LAPANGAN] ____; Minta pemantau, pendeteksi penyimpangan, dan pihak yang dapat intervensi dari PSD/TDK/KPR. | [BUTUH LAPANGAN] ____; Minta jadwal pemantauan, peringatan aktual, catatan intervensi, dan hak penghentian dari pengelola. | [PROTOTIPE] Alert/dashboard dan audit dengan filter tersedia (`backend/app/api/v1/dashboard.py:89-107`, `backend/app/api/v1/audit.py:1-35`). Belum membuktikan jadwal pengawasan atau hak interupsi operasional. |
| [BUTUH LAPANGAN] Over the loop — mengarahkan tata kelola | [BUTUH LAPANGAN] ____; Minta penetap tujuan/aturan dan batas delegasi dari KPR serta pemilik kebijakan. | [BUTUH LAPANGAN] ____; Minta kebijakan, notula peninjauan, dan mandat dari KPR/pemilik kebijakan; jangan mengarang jabatan. | [PROTOTIPE] Admin mengelola akun/penugasan dan pengaturan; penjamin_mutu dapat membaca audit (`backend/app/core/auth.py:177-207`). Peran aplikasi belum menjadi mandat organisasi KPR/pemilik layanan. |
| [BUTUH LAPANGAN] Out the loop — tanpa keputusan manusia pada langkah tertentu | [BUTUH LAPANGAN] ____; Minta langkah tanpa keputusan manusia per kejadian, batas, dan penanggung jawab dari PSD/TDK/KPR. | [BUTUH LAPANGAN] ____; Minta log kejadian, aturan delegasi, dan penanganan pengecualian dari PSD; konfirmasi KPR. | [PROTOTIPE] MCQ murni dapat final otomatis (`backend/app/api/v1/grading.py:88-112`); esai sehat hanya needs_review, gagal manual_review. AUTO disimpan pending_review, belum diindeks (`backend/app/agents/auto_material_agent.py:171-199`). Bukan otonomi seluruh layanan. |

## 10. Hak akses dan bukti — soal 5a–5b, halaman 7

| [BUTUH LAPANGAN] Peran / pihak (kerangka kolom) | [BUTUH LAPANGAN] Hak melihat, membuat, mengubah, menyetujui, menghapus (kerangka kolom) | [BUTUH LAPANGAN] Lingkup dan kapan diberikan (kerangka kolom) | [BUTUH LAPANGAN] Bukti hak akses (kerangka kolom) |
| --- | --- | --- | --- |
| [BUTUH LAPANGAN] Pengguna layanan; peran aktual ____; Konfirmasi mahasiswa/dosen. | [BUTUH LAPANGAN] ____; Minta kebutuhan akses dan hak aktual dari pengguna serta pemilik layanan. | [BUTUH LAPANGAN] ____; Minta batas data sendiri/kelas/prodi dan masa akses dari KPR/PSD. | [BUTUH LAPANGAN] ____; Minta SOP, matriks, dan demonstrasi tersamar akun yang diizinkan termasuk penolakan di luar hak dari PSD. |
| [BUTUH LAPANGAN] Pelaksana; peran aktual ____; Konfirmasi TDK/dosen. | [BUTUH LAPANGAN] ____; Minta hak pencatatan/koreksi dan persetujuannya dari TDK/KPR. | [BUTUH LAPANGAN] ____; Minta batas proses, data, dan periode penugasan dari KPR/PSD. | [BUTUH LAPANGAN] ____; Minta surat tugas/SOP, pengaturan akun, dan jejak perubahan dari KPR/PSD. |
| [BUTUH LAPANGAN] Pengambil keputusan; peran aktual ____; Konfirmasi KPR/pemilik kebijakan. | [BUTUH LAPANGAN] ____; Minta dasar persetujuan, penolakan, delegasi, dan pencabutan dari pihak berwenang. | [BUTUH LAPANGAN] ____; Minta batas kewenangan, eskalasi, dan peninjauan akses dari pemilik kebijakan. | [BUTUH LAPANGAN] ____; Minta matriks kewenangan, bukti persetujuan, dan pemeriksaan akses dari KPR/PSD. |
| [BUTUH LAPANGAN] Pengelola teknis/data; peran aktual ____; Konfirmasi PSD. | [BUTUH LAPANGAN] ____; Minta hak konfigurasi, pemeliharaan, ekspor, pemulihan, dan pembatasan dari PSD/KPR. | [BUTUH LAPANGAN] ____; Minta batas data sensitif dan prosedur pemberian/pencabutan dari PSD. | [BUTUH LAPANGAN] ____; Minta prosedur, konfigurasi tersamar, dan jejak akses dari PSD; jangan meminta kredensial. |

| [BUTUH LAPANGAN] Pembacaan prototipe (kerangka kolom) | [BUTUH LAPANGAN] Bukti kode (kerangka kolom) | [BUTUH LAPANGAN] Implikasi terbatas (kerangka kolom) |
| --- | --- | --- |
| [PROTOTIPE] Admin (`backend/app/core/auth.py:24`). | [PROTOTIPE] Mengelola seluruh mata kuliah/akun/penugasan/pengaturan, membaca audit, edit/approve nilai dan materi (`backend/app/core/auth.py:177-207`, `backend/app/api/v1/grading.py:206-321`). | [PROTOTIPE] Hak aplikasi dan sesi diperiksa middleware (`backend/app/core/auth.py:119-260`); bukan pengesahan kewenangan prodi. |
| [PROTOTIPE] Dosen (`backend/app/core/auth.py:24`). | [PROTOTIPE] Data dibatasi mata kuliah tugas; edit/approve nilai; audit ditolak (`backend/app/core/auth.py:177-207`, `backend/app/core/auth.py:306-412`, `backend/app/api/v1/grading.py:206-321`). | [PROTOTIPE] E1 menguji akses/versi; kode pembatasan dan tes tersedia (`backend/tests/test_autentikasi.py:1-319`). Bukan daftar dosen/pemberian mandat nyata. |
| [PROTOTIPE] Penjamin mutu (`backend/app/core/auth.py:24`). | [PROTOTIPE] Baca data/audit, review/approve RPS dan approve AUTO; edit/approve nilai ditolak (`backend/app/core/auth.py:108-116`, `backend/app/core/auth.py:197-207`, `backend/app/api/v1/grading.py:277-281`). | [PROTOTIPE] Sesi HttpOnly dan pembatasan backend ada (`backend/app/api/v1/auth.py:1-140`); menu bukan satu-satunya pengaman. Kewenangan kampus tetap harus dikonfirmasi. |


## 11. Canvas analisis — Tahap 4 halaman 7; format halaman 12

Problem statement: ____; Isi setelah observasi/WWC pengguna, ukuran dampak, SOP/target dari KPR/TDK, dan triangulasi minimal dua sumber. Setiap jawaban prodi memerlukan ID masalah, ID bukti, waktu, serta konfirmasi; fitur prototipe tidak otomatis menjadi intervensi.

| [BUTUH LAPANGAN] Elemen (kerangka kolom) | [BUTUH LAPANGAN] Pertanyaan pemandu (kerangka kolom) | [BUTUH LAPANGAN] Jawaban tim: prodi (kerangka kolom) | [BUTUH LAPANGAN] Catatan prototipe terpisah (kerangka kolom) |
| --- | --- | --- | --- |
| [BUTUH LAPANGAN] Problem / Masalah | [BUTUH LAPANGAN] Apa yang terjadi? Siapa yang terdampak? | [BUTUH LAPANGAN] ____; Minta observasi dan WWC mahasiswa/dosen/TDK, ukuran kejadian/dampak, dan sumber pembanding. | [BUTUH LAPANGAN] ____; Minta bukti masalah dari pengguna, TDK, dan KPR; fitur tidak menggantikannya. |
| [BUTUH LAPANGAN] Data | [BUTUH LAPANGAN] Data apa yang tersedia dan apa yang dibutuhkan? | [BUTUH LAPANGAN] ____; Minta inventaris SD: format, frekuensi, pemilik, kualitas, akses, waktu, dan kesenjangan dari PSD/TDK. | [PROTOTIPE] Model menyimpan jawaban, final/usulan, per-soal/model/versi/reviewer/waktu di `backend/app/models/submission.py:23-39`; struktur bukan bukti ketersediaan data operasional. |
| [BUTUH LAPANGAN] AI / Intelligence — Kecerdasan | [BUTUH LAPANGAN] Apa yang perlu dideteksi, diprediksi, atau dioptimalkan? | [BUTUH LAPANGAN] ____; Minta kebutuhan keputusan, pola masalah, pembanding, dan kriteria evaluasi dari KPR/dosen/TDK. | [PROTOTIPE] Kelompok skor di `backend/app/core/stats.py:221` dan ringkasan di `backend/app/core/stats.py:244` adalah kemampuan prototipe; kebutuhan prodi belum ditetapkan. |
| [BUTUH LAPANGAN] Decision / Keputusan | [BUTUH LAPANGAN] Siapa yang mengambil keputusan, berdasarkan apa? | [BUTUH LAPANGAN] ____; Minta SOP, mandat, keputusan aktual, dan informasi yang dipakai dari KPR/dosen/TDK. | [PROTOTIPE] Status kuis membedakan review/pending/final di `backend/app/core/grade_review.py:47-61`; approve RPS di `backend/app/api/v1/rps.py:656`. |
| [BUTUH LAPANGAN] Action / Tindakan | [BUTUH LAPANGAN] Apa respons sistem atau manusia? | [BUTUH LAPANGAN] ____; Minta jejak pelaksanaan, penerima, waktu, dan penanggung jawab dari TDK/dosen/PSD. | [PROTOTIPE] Penerapan temuan di `backend/app/api/v1/rps.py:990` dan pembuatan materi setelah final lengkap di `backend/app/core/grade_review.py:65-87` bukan bukti penerimaan oleh pengguna prodi. |
| [BUTUH LAPANGAN] Impact / Dampak | [BUTUH LAPANGAN] Apa indikator keberhasilannya? | [BUTUH LAPANGAN] ____; Minta kondisi awal, target, sumber ukur, periode, serta hasil setelah tindakan dari KPR/pemilik data dan pengguna. | [BUTUH LAPANGAN] ____; Minta bukti manfaat/akibat dari pengguna, TDK, dan KPR; fitur tidak menggantikannya. |

## 12. Dua belas titik pengungkit — Tahap 6 soal 1, halaman 8–9

Urutan 12 ke 1 dipertahankan. Nomor LP adalah jenis intervensi, bukan skor kematangan. LP yang ditemukan dan LP sasaran pada prodi sama-sama kosong. Definisi diringkas dari panduan; rujukan konseptual umum: *Leverage Points: Places to Intervene in a System* (Meadows).

| [BUTUH LAPANGAN] LP (kerangka kolom) | [BUTUH LAPANGAN] Nama (kerangka kolom) | [BUTUH LAPANGAN] Definisi ringkas (kerangka kolom) | [BUTUH LAPANGAN] Keterangan: saat ini dan sasaran prodi (kerangka kolom) | [BUTUH LAPANGAN] Catatan prototipe (kerangka kolom) |
| --- | --- | --- | --- | --- |
| [BUTUH LAPANGAN] 12 | [BUTUH LAPANGAN] Angka (Numbers) | [BUTUH LAPANGAN] Nilai yang menyetel besaran operasi. | [BUTUH LAPANGAN] Saat ini ____; Sasaran ____; Minta aturan ambang dan dasarnya dari KPR/dosen/TDK. Hubungkan pilihan ke masalah tervalidasi. | [PROTOTIPE] Batas lulus bawaan 60 di `backend/app/core/stats.py:63` dan catatan kepatuhan 85 di `backend/app/api/v1/dashboard.py:260`; bukan target prodi. |
| [BUTUH LAPANGAN] 11 | [BUTUH LAPANGAN] Penyangga (Buffers) | [BUTUH LAPANGAN] Cadangan penstabil relatif terhadap arus yang dilayani. | [BUTUH LAPANGAN] Saat ini ____; Sasaran ____; Minta cadangan waktu, orang, atau sumber daya serta arus permintaan dari TDK/KPR. Hubungkan pilihan ke masalah tervalidasi. | [BUTUH LAPANGAN] ____; Minta bukti terkait dari peran pada kolom keterangan; jangan isi dari dugaan fitur. |
| [BUTUH LAPANGAN] 10 | [BUTUH LAPANGAN] Struktur stok dan aliran | [BUTUH LAPANGAN] Susunan aset serta jalur aliran material. | [BUTUH LAPANGAN] Saat ini ____; Sasaran ____; Minta neraca pekerjaan, jalur, kapasitas, dan satuan per periode dari TDK/PSD. Hubungkan pilihan ke masalah tervalidasi. | [PROTOTIPE] pending_grades di `backend/app/core/stats.py:279` baru kandidat stok, bukan model struktur stok–aliran. |
| [BUTUH LAPANGAN] 9 | [BUTUH LAPANGAN] Jeda (Delay) | [BUTUH LAPANGAN] Lama jeda relatif terhadap laju perubahan. | [BUTUH LAPANGAN] Saat ini ____; Sasaran ____; Minta cap waktu dan laju perubahan dari TDK/dosen/PSD. Hubungkan pilihan ke masalah tervalidasi. | [PROTOTIPE] Minggu materi berikutnya di `backend/app/agents/auto_material_agent.py:99` bukan pengukuran jeda nyata. |
| [BUTUH LAPANGAN] 8 | [BUTUH LAPANGAN] Loop penyeimbang | [BUTUH LAPANGAN] Kemampuan mengoreksi penyimpangan. | [BUTUH LAPANGAN] Saat ini ____; Sasaran ____; Minta selisih terhadap tujuan, koreksi, hasil, dan waktu berulang dari pelaksana/KPR. Hubungkan pilihan ke masalah tervalidasi. | [PROTOTIPE] Penerapan temuan menghitung ulang di `backend/app/api/v1/rps.py:1046`; bukan bukti perbaikan hasil belajar. |
| [BUTUH LAPANGAN] 7 | [BUTUH LAPANGAN] Loop penguatan | [BUTUH LAPANGAN] Proses yang memperbesar perubahan dirinya. | [BUTUH LAPANGAN] Saat ini ____; Sasaran ____; Minta hubungan bertanda dan perubahan berulang dari dosen/mahasiswa/TDK. Hubungkan pilihan ke masalah tervalidasi. | [BUTUH LAPANGAN] ____; Minta bukti terkait dari peran pada kolom keterangan; jangan isi dari dugaan fitur. |
| [BUTUH LAPANGAN] 6 | [BUTUH LAPANGAN] Aliran informasi | [BUTUH LAPANGAN] Informasi yang tersedia dan pihak yang mengakses. | [BUTUH LAPANGAN] Saat ini ____; Sasaran ____; Minta peta pengirim/penerima, waktu, dan akses dari PSD/TDK/pengguna. Hubungkan pilihan ke masalah tervalidasi. | [PROTOTIPE] Endpoint analitik di `backend/app/api/v1/dashboard.py:373` tidak membuktikan pengguna informasi pada prodi. |
| [BUTUH LAPANGAN] 5 | [BUTUH LAPANGAN] Aturan (Rules) | [BUTUH LAPANGAN] Ketentuan, kewenangan, insentif, batas tindakan. | [BUTUH LAPANGAN] Saat ini ____; Sasaran ____; Minta SOP, mandat, insentif, akses, dan pengecualian dari KPR/pemilik kebijakan. Hubungkan pilihan ke masalah tervalidasi. | [PROTOTIPE] Pengisian otomatis ditolak untuk RPS validated pada `backend/app/api/v1/rps.py:1129-1130`; batas ini spesifik jalur tersebut. |
| [BUTUH LAPANGAN] 4 | [BUTUH LAPANGAN] Pengorganisasian diri | [BUTUH LAPANGAN] Kemampuan menambah atau mengubah struktur. | [BUTUH LAPANGAN] Saat ini ____; Sasaran ____; Minta kasus perubahan pembagian kerja/proses dan persetujuan dari KPR/TDK. Hubungkan pilihan ke masalah tervalidasi. | [BUTUH LAPANGAN] ____; Minta bukti terkait dari peran pada kolom keterangan; jangan isi dari dugaan fitur. |
| [BUTUH LAPANGAN] 3 | [BUTUH LAPANGAN] Tujuan (Goals) | [BUTUH LAPANGAN] Hasil yang mengarahkan perilaku sistem. | [BUTUH LAPANGAN] Saat ini ____; Sasaran ____; Minta tujuan resmi dan prioritas saat target berkonflik dari KPR/pengguna. Hubungkan pilihan ke masalah tervalidasi. | [BUTUH LAPANGAN] ____; Minta bukti terkait dari peran pada kolom keterangan; jangan isi dari dugaan fitur. |
| [BUTUH LAPANGAN] 2 | [BUTUH LAPANGAN] Paradigma | [BUTUH LAPANGAN] Asumsi mendasar pembentuk tujuan dan struktur. | [BUTUH LAPANGAN] Saat ini ____; Sasaran ____; Minta wawancara lintas peran dan alasan kebijakan dari KPR/dosen/mahasiswa; tafsiran tim bukan keyakinan prodi. Hubungkan pilihan ke masalah tervalidasi. | [BUTUH LAPANGAN] ____; Minta bukti terkait dari peran pada kolom keterangan; jangan isi dari dugaan fitur. |
| [BUTUH LAPANGAN] 1 | [BUTUH LAPANGAN] Melampaui paradigma | [BUTUH LAPANGAN] Kemampuan melepaskan keterikatan pada satu paradigma. | [BUTUH LAPANGAN] Saat ini ____; Sasaran ____; Minta refleksi dan kasus peninjauan asumsi bersama pengambil keputusan serta pengguna. Hubungkan pilihan ke masalah tervalidasi. | [BUTUH LAPANGAN] ____; Minta bukti terkait dari peran pada kolom keterangan; jangan isi dari dugaan fitur. |

## 13. Intervensi, skenario, pembaruan, dan asesmen — Tahap 6 soal 2–5, halaman 9

Soal naratif di antara LP dan 5P juga disediakan. Belum ada intervensi final, prediksi hasil, atau sasaran level prodi.

| [BUTUH LAPANGAN] Soal (kerangka kolom) | [BUTUH LAPANGAN] Isian yang harus disiapkan (kerangka kolom) | [BUTUH LAPANGAN] Bukti dan pihak sumber (kerangka kolom) |
| --- | --- | --- |
| [BUTUH LAPANGAN] 2 — Intervensi dan sasaran perbaikan | [BUTUH LAPANGAN] ____; Nyatakan mekanisme, sasaran, kondisi awal, target, dan pemilik keputusan setelah masalah terkonfirmasi. | [BUTUH LAPANGAN] ____; Minta triangulasi masalah, SOP, kebutuhan, dan kesepakatan target dari KPR/dosen/TDK/mahasiswa. |
| [BUTUH LAPANGAN] 3 — Beberapa prediksi skenario | [BUTUH LAPANGAN] ____; Susun skenario manfaat tercapai, manfaat terbatas, dan akibat tak diharapkan; butuh variabel, asumsi, horizon, dan cara memeriksa. Ini kerangka, bukan prediksi kasus. | [BUTUH LAPANGAN] ____; Minta data historis, kapasitas, batas penggunaan, dan penilaian kewajaran asumsi dari PSD/TDK/KPR serta pengguna. |
| [BUTUH LAPANGAN] 4 — Pembaruan L2 dan/atau L3 | [BUTUH LAPANGAN] ____; Pilih berdasarkan kesalahan penafsiran atau ketidakcocokan proyeksi terhadap hasil; catat alasan, versi, dan pemeriksaan ulang. | [BUTUH LAPANGAN] ____; Minta keluaran skenario/uji, pembanding aktual, dan konfirmasi pemilik keputusan dari KPR/dosen/PSD. |
| [BUTUH LAPANGAN] 5 — Template dan sasaran kematangan | [BUTUH LAPANGAN] ____; Isi template untuk batas satu prodi setelah verifikasi; nyatakan model, indikator, sasaran, bukti kini, dan harapan secara terpisah. | [BUTUH LAPANGAN] ____; Minta inventaris nyata, A8, dokumentasi, dan konfirmasi PSD/TDK/KPR. Draf prototipe bukan skor prodi. |
| [TANYA DOSEN] 5 — Aturan template | [TANYA DOSEN] ____; Konfirmasi kepada dosen: tanpa bukti mengikuti 0 pada rumus atau 1 pada petunjuk? Apakah data demonstrasi cukup untuk P1? | [TANYA DOSEN] ____; Minta keputusan tertulis dan versi template dari dosen; jangan mengubah rumus atau mengarang skor. |

Penalaran umum soal 4: perubahan makna/hubungan informasi perlu peninjauan L2; perubahan asumsi terhadap keadaan mendatang atau ketidakcocokan prakiraan perlu peninjauan L3. Keduanya bisa berubah bersama. Keputusan kasus tetap memerlukan bukti. `docs/draf-asesmen-kematangan-prototipe.xlsx` hanya pembanding berentitas prototipe; draf workbook kini 0,8/5 Awal (sebelum 0,6): tingkat Convergence 1, Capability 0, Integrated view 1, Time 1, Trustworthiness 1. R1/R4 menjadi Ya; tingkat trust berhenti pada R2 yang Tidak. Rumus berjenjang tetap; ini bukan kepatuhan standar atau asesmen prodi. Rujukan: `backend/app/core/auth.py:119-260`, `backend/app/core/audit.py:76-129`.

## 14. 5P — soal 6a, halaman 10

Tujuan dan bukti manfaat belum ada. Petunjuk di bawah adalah arah pemeriksaan, bukan janji manfaat.

| [BUTUH LAPANGAN] Bidang perhatian (kerangka kolom) | [BUTUH LAPANGAN] Tujuan proyek (kerangka kolom) | [BUTUH LAPANGAN] Bukti manfaat (kerangka kolom) |
| --- | --- | --- |
| [BUTUH LAPANGAN] People / Manusia | [BUTUH LAPANGAN] ____; Rumuskan tujuan terkait kebutuhan, akses, dan beban pengguna bersama KPR dan pengguna setelah masalah terkonfirmasi. | [BUTUH LAPANGAN] ____; Minta pengalaman layanan, pengamatan tugas, dan waktu sebelum/sesudah dari mahasiswa/dosen/TDK. Tetapkan kondisi awal dan periode pembanding. |
| [BUTUH LAPANGAN] Planet / Bumi | [BUTUH LAPANGAN] ____; Rumuskan tujuan terkait pemakaian sumber daya sesuai kebutuhan kasus bersama KPR dan pengguna setelah masalah terkonfirmasi. | [BUTUH LAPANGAN] ____; Minta catatan energi, kertas, perangkat, dan batas pengukuran dari PSD/pengelola sarana; digitalisasi saja tidak membuktikan manfaat lingkungan. Tetapkan kondisi awal dan periode pembanding. |
| [BUTUH LAPANGAN] Prosperity / Kesejahteraan | [BUTUH LAPANGAN] ____; Rumuskan tujuan terkait waktu dan biaya layanan bersama KPR dan pengguna setelah masalah terkonfirmasi. | [BUTUH LAPANGAN] ____; Minta waktu kerja, biaya, dan kapasitas dari TDK/KPR serta pemilik anggaran bila diizinkan. Tetapkan kondisi awal dan periode pembanding. |
| [BUTUH LAPANGAN] Peace / Kedamaian | [BUTUH LAPANGAN] ____; Rumuskan tujuan terkait keadilan, kepercayaan, dan penyelesaian keberatan bersama KPR dan pengguna setelah masalah terkonfirmasi. | [BUTUH LAPANGAN] ____; Minta prosedur keberatan/akses, pengalaman lintas peran, dan penanganan kasus dari KPR/dosen/mahasiswa. Tetapkan kondisi awal dan periode pembanding. |
| [BUTUH LAPANGAN] Partnership / Kemitraan | [BUTUH LAPANGAN] ____; Rumuskan tujuan terkait pembagian peran kerja sama yang benar-benar ada bersama KPR dan pengguna setelah masalah terkonfirmasi. | [BUTUH LAPANGAN] ____; Minta kesepakatan, kontribusi, dan evaluasi dari KPR serta peran mitra yang dikonfirmasi. Tetapkan kondisi awal dan periode pembanding. |

## 15. Indikator lima dimensi — soal 6b, halaman 10

Aspek ukur belum menjadi indikator final, target, atau hasil. Sepakati definisi operasional, satuan, periode, serta penanggung jawab setelah kebutuhan diketahui.

| [BUTUH LAPANGAN] Dimensi (kerangka kolom) | [BUTUH LAPANGAN] Indikator (kerangka kolom) | [BUTUH LAPANGAN] Sumber bukti (kerangka kolom) |
| --- | --- | --- |
| [BUTUH LAPANGAN] Individual / Individu | [BUTUH LAPANGAN] ____; Definisikan ukuran terkait pengalaman, kemudahan, atau beban per pengguna bersama pemilik layanan dan pengguna; jangan isi target/hasil tanpa bukti. | [BUTUH LAPANGAN] ____; Minta kuesioner A8, WWC, dan pengamatan tugas dari mahasiswa/dosen/TDK. |
| [BUTUH LAPANGAN] Social / Sosial | [BUTUH LAPANGAN] ____; Definisikan ukuran terkait akses lintas kelompok, koordinasi, atau kepercayaan bersama pemilik layanan dan pengguna; jangan isi target/hasil tanpa bukti. | [BUTUH LAPANGAN] ____; Minta WWC lintas peran, catatan akses, dan prosedur keberatan dari pengguna/KPR/PSD. |
| [BUTUH LAPANGAN] Ekonomi | [BUTUH LAPANGAN] ____; Definisikan ukuran terkait waktu, biaya operasi, atau pemeliharaan per layanan bersama pemilik layanan dan pengguna; jangan isi target/hasil tanpa bukti. | [BUTUH LAPANGAN] ____; Minta catatan waktu/biaya dengan periode dan satuan sebanding dari TDK/KPR/pemilik anggaran. |
| [BUTUH LAPANGAN] Lingkungan | [BUTUH LAPANGAN] ____; Definisikan ukuran terkait energi, kertas, atau umur pakai perangkat sesuai batas sistem bersama pemilik layanan dan pengguna; jangan isi target/hasil tanpa bukti. | [BUTUH LAPANGAN] ____; Minta catatan sumber daya dari PSD/pengelola sarana; nyatakan sumber, asumsi, dan bagian belum terukur. |
| [BUTUH LAPANGAN] Teknis | [BUTUH LAPANGAN] ____; Definisikan ukuran terkait keberhasilan fungsi, latensi, ketersediaan, atau ketepatan keluaran bersama pemilik layanan dan pengguna; jangan isi target/hasil tanpa bukti. | [BUTUH LAPANGAN] ____; Minta log uji/operasi dengan lingkungan, versi, waktu, dan pembanding dari PSD/dosen/TDK. |

## 16. Dampak — soal 6c, halaman 10

Makna adalah kerangka analisis, bukan temuan. Dampak dapat menguntungkan, merugikan, atau berbeda antarkelompok.

| [BUTUH LAPANGAN] Tingkat (kerangka kolom) | [BUTUH LAPANGAN] Makna (kerangka kolom) | [BUTUH LAPANGAN] Contoh dan bukti prodi (kerangka kolom) |
| --- | --- | --- |
| [BUTUH LAPANGAN] Langsung | [BUTUH LAPANGAN] Perubahan yang berhubungan dekat dengan tindakan pada proses sasaran. Kerangka ini tidak menyatakan adanya dampak pada prodi. | [BUTUH LAPANGAN] ____; Minta catatan proses sebelum/sesudah, waktu, keluaran, dan pengalaman penerima dari pelaksana/pengguna. Catat periode dan hubungan dengan intervensi; korelasi bukan bukti sebab. |
| [BUTUH LAPANGAN] Tidak langsung | [BUTUH LAPANGAN] Perubahan lanjutan melalui perilaku atau proses lain. Kerangka ini tidak menyatakan adanya dampak pada prodi. | [BUTUH LAPANGAN] ____; Minta pengamatan lanjutan lintas peran, perpindahan beban, dan penjelasan alternatif dari dosen/TDK/mahasiswa. Catat periode dan hubungan dengan intervensi; korelasi bukan bukti sebab. |
| [BUTUH LAPANGAN] Sistemik | [BUTUH LAPANGAN] Perubahan lebih luas pada pola, aturan, tujuan, atau struktur. Kerangka ini tidak menyatakan adanya dampak pada prodi. | [BUTUH LAPANGAN] ____; Minta dokumen kebijakan, pola lintas periode, dan WWC lintas peran dari KPR/TDK/pengguna; satu kejadian tidak cukup. Catat periode dan hubungan dengan intervensi; korelasi bukan bukti sebab. |

## 17. Tata kelola — soal 6d, halaman 10

Kategori peran dari panduan belum menjadi penunjukan pihak nyata. Keberadaan kode atau dependensi teknis bukan komitmen organisasi.

| [BUTUH LAPANGAN] Peran (kerangka kolom) | [BUTUH LAPANGAN] Tanggung jawab (kerangka kolom) | [BUTUH LAPANGAN] Bukti komitmen (kerangka kolom) |
| --- | --- | --- |
| [BUTUH LAPANGAN] Pemilik layanan | [BUTUH LAPANGAN] ____; Konfirmasi tanggung jawab terkait tujuan, perubahan, dan pertanggungjawaban dengan pemilik layanan/pelaksana; belum menjadi pembagian tugas yang disepakati. | [BUTUH LAPANGAN] ____; Minta mandat tertulis, target, tanggung jawab per peran, dan jadwal peninjauan dari KPR/pemilik kewenangan. |
| [BUTUH LAPANGAN] Operator | [BUTUH LAPANGAN] ____; Konfirmasi tanggung jawab terkait operasi, pemantauan, dan gangguan dengan pemilik layanan/pelaksana; belum menjadi pembagian tugas yang disepakati. | [BUTUH LAPANGAN] ____; Minta SOP, jadwal, eskalasi, dan kesediaan menjalankan tugas dari TDK/PSD serta pengelola. |
| [BUTUH LAPANGAN] Pengembang / pemasok | [BUTUH LAPANGAN] ____; Konfirmasi tanggung jawab terkait pemeliharaan, dukungan, versi, dan batas layanan dengan pemilik layanan/pelaksana; belum menjadi pembagian tugas yang disepakati. | [BUTUH LAPANGAN] ____; Minta kesepakatan dukungan, akses data, pemeliharaan, dan prosedur keluar dari peran pengembang/pemasok yang dikonfirmasi pemilik layanan. |
| [BUTUH LAPANGAN] Pengguna / komunitas | [BUTUH LAPANGAN] ____; Konfirmasi tanggung jawab terkait kebutuhan, umpan balik, dan evaluasi sukarela dengan pemilik layanan/pelaksana; belum menjadi pembagian tugas yang disepakati. | [BUTUH LAPANGAN] ____; Minta kesepakatan partisipasi, kanal umpan balik, serta hak keberatan dari mahasiswa/dosen/perwakilan pengguna tanpa nama orang. |
| [BUTUH LAPANGAN] Mitra | [BUTUH LAPANGAN] ____; Konfirmasi tanggung jawab terkait kontribusi dan tanggung jawab lintas pihak dengan pemilik layanan/pelaksana; belum menjadi pembagian tugas yang disepakati. | [BUTUH LAPANGAN] ____; Minta kesepakatan peran, kontribusi, batas pertukaran data, dan evaluasi dari KPR serta pihak mitra yang dikonfirmasi. |

## 18. Kelengkapan resiliensi — soal 7, halaman 10–11

Tidak ada tabel baku untuk soal 7 pada PDF. Tabel tambahan ini menjaga kelengkapan halaman 11. Rancangan A/B/C, matriks asumsi dan hasil E1/E2 kini tersedia. Pilihan B masih kandidat bersyarat, bukan deployment yang lulus semua gerbang. Bukti utama adalah rancangan bagian 8.5/9 dan ringkasan resiliensi; laporan tata kelola adalah **laporan thread, bukan log asli**, karena log mentah hilang saat restart. Pembaruan ini tidak mengulang eksperimen aplikasi.

| [BUTUH LAPANGAN] Kewajiban (kerangka kolom) | [BUTUH LAPANGAN] Isian / hasil (kerangka kolom) | [BUTUH LAPANGAN] Bukti dan pihak sumber (kerangka kolom) |
| --- | --- | --- |
| [BUTUH LAPANGAN] Pengguna, fungsi kritis, batas kualitas, dependensi | [PROTOTIPE] Peran dan dependensi dapat dipetakan (`backend/app/core/auth.py:24`, `backend/app/core/config.py:71-82`); FK1–FK6 dan batas layanan masih kandidat, `docs/rancangan-resiliensi.md:13-51`. | [BUTUH LAPANGAN] ____; Minta kebutuhan kontinuitas, batas tunggu/kehilangan data, dan peta dependensi dari KPR/TDK/PSD serta pengguna. |
| [BUTUH LAPANGAN] Tiga alternatif desain memenuhi syarat wajib | [PROTOTIPE] A/B/C dan gerbang wajib telah dirancang (`docs/rancangan-resiliensi.md:86-194`); pengesahan kebutuhan dan pemenuhan deployment lengkap belum terbukti. | [BUTUH LAPANGAN] ____; Minta persyaratan yang disetujui, diagram tiap alternatif, dan alasan pemenuhan dari pemilik layanan/PSD. |
| [BUTUH LAPANGAN] Biaya, kontinuitas, energi, pemeliharaan | [PROTOTIPE] Perbandingan A/B/C memakai asumsi eksplisit (`docs/rancangan-resiliensi.md:196-241`); tidak ada pengukuran energi/biaya operasi nyata dan SCI belum dihitung. | [BUTUH LAPANGAN] ____; Minta data atau asumsi dengan sumber, satuan, horizon, dan batas sama dari PSD/KPR/pemilik anggaran. |
| [BUTUH LAPANGAN] Sedikitnya dua eksperimen gangguan di lingkungan uji | [PROTOTIPE] E1/E2 diulang masing-masing tiga run independen (`docs/rancangan-resiliensi.md:519-580`): esai gagal ditahan, review skrip dosen, startup aman, CLI restore, replay ID stabil. Bukan uji mutu model/manusia nyata. | [BUTUH LAPANGAN] ____; Minta skenario, izin lingkungan, versi konfigurasi, log waktu/perilaku/pemulihan dari PSD dan pelaksana uji; bukan gangguan layanan operasional. |
| [BUTUH LAPANGAN] Matriks keputusan, sensitivitas, rekomendasi | [PROTOTIPE] Matriks asumsi A 3,50/B 3,70/C 3,00, sensitivitas/Pareto dan kandidat B bersyarat tersedia (`docs/rancangan-resiliensi.md:243-293`, `docs/rancangan-resiliensi.md:583-604`). Belum keputusan prodi. | [BUTUH LAPANGAN] ____; Minta kriteria, bobot, rentang variasi, hasil eksperimen, dan risiko tersisa dari PSD/pemilik keputusan. |
| [BUTUH LAPANGAN] Indikator belum terukur dan rencana pengukuran | [PROTOTIPE] Backup belum terjadwal/terenkripsi/berdomain terpisah; created_at replay berubah; mutu qwen3.5:9b dan kesesuaian nilai dosen belum disahkan (`docs/rancangan-resiliensi.md:569-580`, `docs/bukti-uji/ollama-20261106/laporan-ollama.md:1-11`). | [BUTUH LAPANGAN] ____; Minta keterbatasan, alasan, kebutuhan data, penanggung jawab per peran, dan jadwal dari PSD/KPR. |

## 19. Lampiran A9: inventaris dan peta alur data

Tambahan untuk A9 pada analisis gap bagian 8. Inventaris prodi tetap mengikuti pedoman lapangan bagian 9. Tidak ada pembacaan basis data atau penyalinan data pribadi dalam penyusunan draf.

| [BUTUH LAPANGAN] Jenis sumber yang ditelusuri (kerangka kolom) | [BUTUH LAPANGAN] Format / mekanisme prototipe (kerangka kolom) | [BUTUH LAPANGAN] Atribut aktual prodi yang kosong (kerangka kolom) | [BUTUH LAPANGAN] Bukti dan pemberi (kerangka kolom) |
| --- | --- | --- | --- |
| [BUTUH LAPANGAN] Jawaban dan nilai; sumber prodi ____; Telusuri dosen/TDK/PSD. | [PROTOTIPE] CSV melalui `backend/app/api/v1/quiz.py:417`; answers, usulan/final, feedback per soal, model/versi/reviewer/waktu pada `backend/app/models/submission.py:23-39`. | [BUTUH LAPANGAN] ____; Minta format, frekuensi, pemilik, kualitas, akses, dan waktu dari dosen/PSD; unggahan tidak menentukan frekuensi nyata. | [BUTUH LAPANGAN] ____; Minta SD, contoh tersamar, panduan, cap waktu, dan konfirmasi pemilik dari dosen/TDK/PSD. |
| [BUTUH LAPANGAN] Mata kuliah dan RPS; sumber prodi ____; Telusuri dosen/TDK/PSD. | [PROTOTIPE] program_study dan academic_year pada `backend/app/models/course.py:16`; pertemuan dibaca pada `backend/app/api/v1/rps.py:240`. | [BUTUH LAPANGAN] ____; Minta format, frekuensi, pemilik, kualitas, akses, waktu, dan kesenjangan dari dosen/TDK/PSD. | [BUTUH LAPANGAN] ____; Minta SD, SOP, contoh RPS tersamar, riwayat, dan konfirmasi dari dosen/TDK/KPR. |
| [BUTUH LAPANGAN] Materi/tindak lanjut; sumber prodi ____; Telusuri dosen/PSD. | [PROTOTIPE] content_text, week, status pending_review/model disimpan pada `backend/app/agents/auto_material_agent.py:171-194`; indeks setelah approve pada `backend/app/api/v1/materials.py:270-291`. | [BUTUH LAPANGAN] ____; Minta format, frekuensi, pemilik, kualitas, akses, waktu, dan kesenjangan dari dosen/PSD. | [BUTUH LAPANGAN] ____; Minta SD, panduan, contoh tersamar, bukti distribusi/penerimaan dari dosen/pengguna. |

| [BUTUH LAPANGAN] Masukan prototipe (kerangka kolom) | [BUTUH LAPANGAN] Pengolahan / penyimpanan (kerangka kolom) | [BUTUH LAPANGAN] Keputusan / tindakan (kerangka kolom) | [BUTUH LAPANGAN] Alur prodi yang harus diperiksa (kerangka kolom) |
| --- | --- | --- | --- |
| [PROTOTIPE] CSV masuk di `backend/app/api/v1/quiz.py:417`. | [PROTOTIPE] quiz_id di `backend/app/models/submission.py:19`; pengolahan pada `backend/app/api/v1/grading.py:67`. | [PROTOTIPE] Skor esai berupa usulan, final menunggu persetujuan (`backend/app/api/v1/grading.py:88-138`, `backend/app/api/v1/grading.py:270-321`); kuis review dipisahkan (`backend/app/core/grade_review.py:47-61`). | [BUTUH LAPANGAN] ____; Amati asal kejadian, pencatat, penyimpanan, pembaca, dan penggunaan keputusan bersama dosen/TDK/PSD; bukan mengasumsikan alur prototipe dipakai. |
| [PROTOTIPE] Temuan diterapkan lewat `backend/app/api/v1/rps.py:990`. | [PROTOTIPE] Perubahan ditulis di `backend/app/api/v1/rps.py:1043`; penghitungan ulang di `backend/app/api/v1/rps.py:1046`. | [PROTOTIPE] Laporan katalog di `backend/app/api/v1/rps.py:246`; status persetujuan ditulis pada `backend/app/api/v1/rps.py:664`. | [BUTUH LAPANGAN] ____; Minta alur pemeriksaan, otorisasi, koreksi, dan evaluasi nyata dari dosen/TDK/KPR dengan bukti bertanggal. |

## 20. Pertanyaan untuk dosen dan batas penyelesaian

1. Apakah Smart Education diizinkan meskipun Tahap 1–2 menyebut 13 kluster? Batas satu prodi sudah diputuskan, tetapi identitasnya perlu ditetapkan sebelum pengumpulan. Lihat bagian 1.
2. Apa definisi operasional Sistemik, sumber instrumen, rumus rata-rata dari ya/tidak, pembobotan, dan konversi skor seperti 3,44 menjadi Level 1–4? Lihat bagian 1 dan A8 bagian 7.
3. Apa definisi, rumus/notasi, satuan, cakupan, dan contoh Rasio fiscal, Sensitivitas pada tabel loop, Polaritas loop panjang, serta Kondisi Gamma-W (Γ−W)? Lihat bagian 6.
4. Untuk template, apakah tanpa bukti mengikuti 0 pada rumus atau 1 pada petunjuk? Apakah tampilan data demonstrasi cukup untuk P1? Penilaian template dan lima level panduan tetap terpisah. Lihat bagian 2 dan 13.
5. Apakah soal naratif/resiliensi halaman 9–11 dikumpulkan bersama lembar kerja atau terpisah? Apa bentuk bukti simulasi soal 4b yang diharapkan? Lihat bagian 8, 13, dan 18.

Rujukan konseptual umum untuk penalaran, bukan bukti prodi: *Thinking in Systems* dan *Leverage Points: Places to Intervene in a System* (Meadows); *Business Dynamics: Systems Thinking and Modeling for a Complex World* (Sterman); *Toward a Theory of Situation Awareness in Dynamic Systems* (Endsley). Tidak ada kutipan langsung, nomor halaman, atau klaim pemeriksaan pustaka primer.

Sebelum menjadi jawaban final, semua isian prodi memerlukan pengumpulan dan konfirmasi, semua istilah belum jelas memerlukan jawaban dosen, dan rujukan prototipe perlu dibaca ulang bila kode berubah. Jangan menghapus label prototipe ketika memindahkan isi ke laporan. Penalaran konseptual dan simulasi penalaran bukan observasi atau eksperimen yang telah dilakukan.
