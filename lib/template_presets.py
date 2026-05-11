"""
Educator Copilot — Institution Template Presets
================================================
Defines which form fields are active for each university preset.
Based on comparative analysis of 10 Indonesian universities.

Presets:
  - ITB Mode:     28+ fields (RPMK+RPS, nama EN, kebijakan AI)
  - ITS/UB Mode:  26 fields  (TM+PT+BM, rumpun MK, bentuk vs metode)
  - UGM Mode:     25 fields  (4 aspek CPL eksplisit)
  - Standard Mode: 22 fields (SN-Dikti minimum — UI, UNAIR, UPI, etc.)
"""

from dataclasses import dataclass, field
from typing import Optional


# ── Field Definitions ────────────────────────────────────────────

BLOK_A_FIELDS = {
    "nama_prodi":       {"label": "Nama Program Studi",         "required": True,  "type": "text"},
    "nama_mk_id":       {"label": "Nama Mata Kuliah (ID)",      "required": True,  "type": "text"},
    "nama_mk_en":       {"label": "Nama Mata Kuliah (EN)",      "required": False, "type": "text",    "presets": ["itb"]},
    "kode_mk":          {"label": "Kode Mata Kuliah",           "required": True,  "type": "text"},
    "rumpun_mk":        {"label": "Rumpun Mata Kuliah",         "required": False, "type": "text",    "presets": ["its_ub", "unhas"]},
    "bobot_sks":        {"label": "Bobot SKS",                  "required": True,  "type": "number",  "min": 1, "max": 6},
    "semester":         {"label": "Semester",                    "required": True,  "type": "number",  "min": 1, "max": 8},
    "jenis_mk":         {"label": "Jenis MK",                   "required": False, "type": "select",  "presets": ["itb", "ugm"],
                         "options": ["Wajib", "Pilihan", "MKWI", "MKWP", "MKOP", "MKPB", "MKPs"]},
    "dosen_pengampu":   {"label": "Dosen Pengampu (Tim)",       "required": True,  "type": "text_area"},
    "tanggal_penyusunan": {"label": "Tanggal Penyusunan",       "required": True,  "type": "date"},
    "mk_terkait":       {"label": "MK Terkait (Prereq/Coreq)", "required": False, "type": "text_area", "presets": ["itb"]},
    "deskripsi_mk":     {"label": "Deskripsi Mata Kuliah",      "required": True,  "type": "text_area"},
}

BLOK_B_FIELDS = {
    "cpl":              {"label": "CPL yang Dibebankan (satu per baris)",           "required": True, "type": "text_area"},
    "cpl_4aspek":       {"label": "CPL 4 Aspek (Sikap, Pengetahuan, KU, KK)",      "required": False, "type": "text_area", "presets": ["ugm"]},
    "cpmk":             {"label": "CPMK (format: kode | deskripsi | CPL-ref | Bloom)", "required": True, "type": "text_area"},
}

BLOK_C_FIELDS = {
    "metode_pembelajaran": {"label": "Metode Pembelajaran",     "required": True,  "type": "multiselect",
                            "options": ["Ceramah", "Diskusi", "Studi Kasus", "PBL", "PjBL", "Praktikum",
                                        "SGD", "Role-Play", "Discovery Learning", "SDL", "Cooperative Learning"]},
    "bentuk_pembelajaran": {"label": "Bentuk Pembelajaran",     "required": False, "type": "multiselect", "presets": ["its_ub"],
                            "options": ["Kuliah", "Responsi", "Tutorial", "Seminar", "Praktikum",
                                        "Praktik Studio", "Praktik Bengkel", "Praktik Lapangan", "Penelitian"]},
    "modalitas":          {"label": "Modalitas",                 "required": True,  "type": "multiselect",
                           "options": ["Sinkron Tatap Muka", "Sinkron Daring", "Asinkron", "Hybrid"]},
    "include_pt_bm":      {"label": "Sertakan Waktu PT & BM",   "required": False, "type": "checkbox", "presets": ["its_ub"]},
}

BLOK_D_FIELDS = {
    "assessment":        {"label": "Komponen Penilaian",         "required": True,  "type": "data_editor"},
    "teknik_penilaian":  {"label": "Teknik Penilaian (Tes/Non-tes)", "required": False, "type": "multiselect", "presets": ["its_ub"],
                          "options": ["Tes Tertulis", "Tes Lisan", "Observasi", "Penugasan", "Portofolio", "Proyek"]},
}

BLOK_E_FIELDS = {
    "bahan_kajian":      {"label": "Bahan Kajian (satu topik per baris)", "required": True, "type": "text_area"},
    "pustaka_utama":     {"label": "Pustaka Utama",              "required": True,  "type": "text_area"},
    "pustaka_pendukung": {"label": "Pustaka Pendukung",          "required": False, "type": "text_area"},
    "koordinator_rmk":   {"label": "Koordinator RMK/MK",        "required": False, "type": "text",    "presets": ["its_ub", "unhas"]},
    "ka_prodi":          {"label": "Ketua Program Studi",        "required": False, "type": "text"},
    "kebijakan_ai":      {"label": "Kebijakan Penggunaan AI",    "required": False, "type": "text_area", "presets": ["itb"]},
    "media_pembelajaran": {"label": "Media Pembelajaran (SW/HW)", "required": False, "type": "text_area", "presets": ["itb"]},
}


# ── Preset Configurations ───────────────────────────────────────

@dataclass
class InstitutionPreset:
    """Configuration for a university-specific RPS template."""
    id: str
    name: str
    universities: list[str]
    description: str
    active_fields: int
    complexity: str  # "★★★☆☆" etc.
    has_rpmk: bool = False
    has_pt_bm: bool = False
    has_4aspek_cpl: bool = False
    has_bentuk: bool = False
    has_teknik_penilaian: bool = False
    extra_presets: list[str] = field(default_factory=list)


PRESETS: dict[str, InstitutionPreset] = {
    "itb": InstitutionPreset(
        id="itb",
        name="ITB Mode",
        universities=["Institut Teknologi Bandung"],
        description="Model paling kompleks: RPMK + RPS terpisah, nama MK bilingual, kebijakan AI, media pembelajaran",
        active_fields=28,
        complexity="★★★★★",
        has_rpmk=True,
        extra_presets=["itb"],
    ),
    "its_ub": InstitutionPreset(
        id="its_ub",
        name="ITS / UB Mode",
        universities=["Institut Teknologi Sepuluh Nopember", "Universitas Brawijaya"],
        description="Waktu TM+PT+BM, rumpun MK, pemisahan bentuk vs metode, teknik penilaian",
        active_fields=26,
        complexity="★★★★☆",
        has_pt_bm=True,
        has_bentuk=True,
        has_teknik_penilaian=True,
        extra_presets=["its_ub"],
    ),
    "ugm": InstitutionPreset(
        id="ugm",
        name="UGM Mode",
        universities=["Universitas Gadjah Mada"],
        description="4 aspek CPL eksplisit (Sikap, Pengetahuan, KU, KK), Sub-CPMK detail",
        active_fields=25,
        complexity="★★★★☆",
        has_4aspek_cpl=True,
        extra_presets=["ugm"],
    ),
    "standard": InstitutionPreset(
        id="standard",
        name="Standard Mode (SN-Dikti)",
        universities=["Universitas Indonesia", "Universitas Airlangga", "Universitas Pendidikan Indonesia",
                       "Universitas Padjadjaran", "Universitas Hasanuddin", "Universitas Diponegoro",
                       "Universitas lainnya"],
        description="Format standar SN-Dikti — 22 field wajib, cocok untuk sebagian besar PT di Indonesia",
        active_fields=22,
        complexity="★★★☆☆",
    ),
}


def get_preset(preset_id: str) -> InstitutionPreset:
    """Get preset configuration by ID."""
    return PRESETS.get(preset_id, PRESETS["standard"])


def is_field_active(field_config: dict, preset_id: str) -> bool:
    """Check if a field should be shown for the given preset."""
    if field_config.get("required", False):
        return True
    allowed_presets = field_config.get("presets")
    if allowed_presets is None:
        return True  # No restriction → show for all
    return preset_id in allowed_presets


def get_active_fields_for_preset(preset_id: str) -> dict[str, dict]:
    """Return all active fields (across all blocks) for a given preset."""
    all_fields = {}
    for block_name, block_fields in [
        ("blok_a", BLOK_A_FIELDS),
        ("blok_b", BLOK_B_FIELDS),
        ("blok_c", BLOK_C_FIELDS),
        ("blok_d", BLOK_D_FIELDS),
        ("blok_e", BLOK_E_FIELDS),
    ]:
        for key, config in block_fields.items():
            if is_field_active(config, preset_id):
                all_fields[f"{block_name}.{key}"] = config
    return all_fields


# ── Bloom Taxonomy Helpers ──────────────────────────────────────

BLOOM_LEVELS = {
    "C1": {"label": "Mengingat (Remember)",      "weight": 1.0},
    "C2": {"label": "Memahami (Understand)",      "weight": 1.0},
    "C3": {"label": "Menerapkan (Apply)",         "weight": 1.5},
    "C4": {"label": "Menganalisis (Analyze)",     "weight": 1.5},
    "C5": {"label": "Mengevaluasi (Evaluate)",    "weight": 2.0},
    "C6": {"label": "Mencipta (Create)",          "weight": 2.0},
}

BLOOM_VERBS = {
    "C1": ["menyebutkan", "mendefinisikan", "mengidentifikasi", "mengenali", "mengingat"],
    "C2": ["menjelaskan", "membedakan", "menafsirkan", "merangkum", "mengklasifikasikan"],
    "C3": ["menerapkan", "menggunakan", "menghitung", "mendemonstrasikan", "mengimplementasikan"],
    "C4": ["menganalisis", "membandingkan", "mengevaluasi", "mengkritisi", "menguji"],
    "C5": ["menilai", "mempertahankan", "menyimpulkan", "merekomendasikan", "memvalidasi"],
    "C6": ["merancang", "mengembangkan", "merumuskan", "menyusun", "menciptakan"],
}
