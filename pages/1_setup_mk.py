"""Halaman 1 — Setup Mata Kuliah (Form Blok A–E)"""

import streamlit as st
import pandas as pd
from datetime import date

from lib.template_presets import (
    BLOK_A_FIELDS, BLOK_B_FIELDS, BLOK_C_FIELDS, BLOK_D_FIELDS, BLOK_E_FIELDS,
    is_field_active, get_preset,
)
from agents.curriculum_agent import run_curriculum_agent

st.set_page_config(page_title="Setup Mata Kuliah", page_icon="⚙️", layout="wide")
st.title("⚙️ Setup Mata Kuliah")

preset_id = st.session_state.get("institution_preset", "standard")
preset = get_preset(preset_id)
st.info(f"**Template aktif:** {preset.name} ({preset.active_fields} fields)")

with st.form("form_mk"):
    # ── BLOK A: Identitas ────────────────────────────────
    st.subheader("Blok A — Identitas Mata Kuliah")
    col1, col2, col3 = st.columns(3)
    name = col1.text_input("Nama Mata Kuliah *")
    code = col2.text_input("Kode MK *")
    credits = col3.number_input("Jumlah SKS *", min_value=1, max_value=6, value=3)

    col4, col5 = st.columns(2)
    nama_prodi = col4.text_input("Nama Program Studi *")
    semester = col5.number_input("Semester", min_value=1, max_value=8, value=1)

    dosen = st.text_input("Dosen Pengampu (Tim) *")
    deskripsi = st.text_area("Deskripsi Mata Kuliah *", height=80)

    # Optional fields based on preset
    name_en = ""
    if is_field_active(BLOK_A_FIELDS["nama_mk_en"], preset_id):
        name_en = st.text_input("Nama MK (English)")

    jenis_mk = ""
    if is_field_active(BLOK_A_FIELDS["jenis_mk"], preset_id):
        jenis_mk = st.selectbox("Jenis MK", BLOK_A_FIELDS["jenis_mk"]["options"])

    rumpun = ""
    if is_field_active(BLOK_A_FIELDS["rumpun_mk"], preset_id):
        rumpun = st.text_input("Rumpun MK")

    mk_terkait = ""
    if is_field_active(BLOK_A_FIELDS["mk_terkait"], preset_id):
        mk_terkait = st.text_area("MK Terkait (Prereq/Coreq)", height=60)

    # ── BLOK B: Capaian Pembelajaran ─────────────────────
    st.subheader("Blok B — Capaian Pembelajaran")
    cpl_input = st.text_area("CPL yang Dibebankan * (satu per baris)", height=100)

    if is_field_active(BLOK_B_FIELDS.get("cpl_4aspek", {}), preset_id):
        st.text_area("CPL 4 Aspek (Sikap, Pengetahuan, KU, KK)", height=100)

    cpmk_input = st.text_area(
        "CPMK * (format per baris: KODE | deskripsi | CPL-ref | BloomLevel)",
        height=120,
        help="Contoh: CPMK-1 | Mampu menjelaskan konsep dasar AI | CPL-3 | C2",
    )

    # ── BLOK C: Pedagogi ─────────────────────────────────
    st.subheader("Blok C — Metode & Waktu")
    methods = st.multiselect("Metode Pembelajaran *",
                             BLOK_C_FIELDS["metode_pembelajaran"]["options"],
                             default=["Ceramah", "Diskusi"])

    if is_field_active(BLOK_C_FIELDS["bentuk_pembelajaran"], preset_id):
        st.multiselect("Bentuk Pembelajaran", BLOK_C_FIELDS["bentuk_pembelajaran"]["options"])

    modality = st.multiselect("Modalitas *",
                              BLOK_C_FIELDS["modalitas"]["options"],
                              default=["Sinkron Tatap Muka"])

    # ── BLOK D: Penilaian ────────────────────────────────
    st.subheader("Blok D — Komponen Penilaian")
    st.caption("Total bobot harus = 100%")

    default_assessment = pd.DataFrame({
        "Komponen": ["Kuis", "UTS", "UAS", "Tugas"],
        "Bobot (%)": [20, 30, 35, 15],
        "CPMK Terkait": ["", "", "", ""],
    })
    assessment_df = st.data_editor(default_assessment, num_rows="dynamic", key="assessment_editor")

    if is_field_active(BLOK_D_FIELDS.get("teknik_penilaian", {}), preset_id):
        st.multiselect("Teknik Penilaian", BLOK_D_FIELDS["teknik_penilaian"]["options"])

    # ── BLOK E: Bahan Kajian & Referensi ─────────────────
    st.subheader("Blok E — Bahan Kajian & Referensi")
    bahan_kajian = st.text_area("Bahan Kajian * (satu topik per baris)", height=150)
    pustaka = st.text_area("Pustaka Utama *", height=80)

    if is_field_active(BLOK_E_FIELDS.get("koordinator_rmk", {}), preset_id):
        st.text_input("Koordinator RMK/MK")
    if is_field_active(BLOK_E_FIELDS.get("kebijakan_ai", {}), preset_id):
        st.text_area("Kebijakan Penggunaan AI", height=60)

    submitted = st.form_submit_button("🚀 Generate RPS", type="primary", use_container_width=True)

if submitted:
    # Build assessment list
    assessment_list = []
    if assessment_df is not None:
        for _, row in assessment_df.iterrows():
            assessment_list.append({
                "component": row.get("Komponen", ""),
                "weight": float(row.get("Bobot (%)", 0)),
                "cpmk": row.get("CPMK Terkait", ""),
            })

    course_data = {
        "name": name, "name_en": name_en, "code": code, "credits": credits,
        "semester": semester, "prodi": nama_prodi, "dosen": dosen,
        "description": deskripsi, "jenis_mk": jenis_mk, "rumpun_mk": rumpun,
        "mk_terkait": mk_terkait, "preset": preset_id,
        "cpl": cpl_input, "cpmk": cpmk_input, "bahan_kajian": bahan_kajian,
        "teaching_methods": methods, "modality": modality,
        "assessment": assessment_list, "pustaka": pustaka,
    }

    with st.spinner("🤖 Agent sedang menyusun RPS 16 minggu..."):
        try:
            result = run_curriculum_agent(course_data, preset=preset_id)

            if result.get("error_message"):
                st.error(f"❌ {result['error_message']}")
            else:
                st.success("✅ Draft RPS berhasil dibuat! Lanjut ke halaman **Review RPS**.")
                st.session_state["last_course_id"] = result.get("course_data", {}).get("course_id")

                with st.expander("🔍 Lihat proses reasoning agent", expanded=True):
                    for step in result.get("reasoning_steps", []):
                        st.write(f"**{step['step']}:** {step['result']}")
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")
            st.exception(e)
