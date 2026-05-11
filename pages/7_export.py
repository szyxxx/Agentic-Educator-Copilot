"""Halaman 7 — Export Dokumen (DOCX/PDF)"""

import streamlit as st
from tools.database import load_courses, get_connection
from lib.docx_exporter import export_rps_to_docx
from lib.template_presets import get_preset

st.set_page_config(page_title="Export Dokumen", page_icon="📤", layout="wide")
st.title("📤 Export Dokumen RPS")

courses = load_courses()
if not courses:
    st.warning("Belum ada mata kuliah.")
    st.stop()

course_options = {f"{c['name']} ({c['code']})": c for c in courses}
selected = st.selectbox("Pilih Mata Kuliah", list(course_options.keys()))
course = course_options[selected]
course_id = course['course_id']

preset_id = course.get('preset', 'standard')
preset = get_preset(preset_id)

st.info(f"**Format Institusi:** {preset.name}")

if preset.has_rpmk:
    st.write("Sistem mendeteksi bahwa institusi ini mewajibkan **dua dokumen terpisah**: Rencana Pembelajaran Mata Kuliah (RPMK) dan Rencana Pembelajaran Semester (RPS).")
    doc_type = st.radio("Pilih Dokumen:", ["RPMK & RPS (Keduanya)", "Hanya RPMK", "Hanya RPS"])
else:
    doc_type = "RPS Standar"

if st.button("⬇️ Export ke DOCX", type="primary", use_container_width=True):
    with st.spinner("Menyusun dokumen..."):
        try:
            docx_bytes = export_rps_to_docx(course_id, preset_id)
            st.download_button(
                label="Simpan File DOCX",
                data=docx_bytes,
                file_name=f"RPS_{course['code']}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
            st.success("Dokumen siap diunduh!")
        except Exception as e:
            st.error(f"Gagal melakukan export: {e}")
