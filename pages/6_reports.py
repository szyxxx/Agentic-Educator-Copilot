"""Halaman 6 — Laporan Rekapitulasi CPMK"""

import streamlit as st
import pandas as pd
from tools.database import load_courses, get_connection

st.set_page_config(page_title="Laporan CPMK", page_icon="📊", layout="wide")
st.title("📊 Laporan Rekapitulasi CPMK")

courses = load_courses()
if not courses:
    st.warning("Belum ada mata kuliah.")
    st.stop()

course_options = {f"{c['name']} ({c['code']})": c['course_id'] for c in courses}
selected = st.selectbox("Pilih Mata Kuliah", list(course_options.keys()))
course_id = course_options[selected]

st.info("Halaman ini akan menampilkan matriks ketercapaian CPMK vs Mahasiswa berdasarkan agregasi nilai Kuis, UTS, dan UAS.")
st.caption("Catatan: Implementasi penuh memerlukan integrasi dengan Sistem Informasi Akademik untuk data nilai lengkap.")

# Mock data for demonstration
data = {
    "NIM": ["13520001", "13520002", "13520003", "13520004", "13520005"],
    "Nama": ["Budi", "Siti", "Andi", "Rina", "Joko"],
    "CPMK-1 (%)": [85, 90, 75, 88, 60],
    "CPMK-2 (%)": [80, 85, 70, 92, 55],
    "CPMK-3 (%)": [90, 95, 80, 85, 65],
    "Total Ketercapaian": ["Lulus", "Lulus", "Lulus", "Lulus", "Remedial"]
}

df = pd.DataFrame(data)

# Style the dataframe
def highlight_low_scores(val):
    if isinstance(val, (int, float)) and val < 60:
        return 'background-color: #ffcccc; color: #cc0000'
    elif val == "Remedial":
        return 'background-color: #ffcccc; color: #cc0000; font-weight: bold'
    return ''

st.dataframe(df.style.map(highlight_low_scores), use_container_width=True)

st.download_button("⬇️ Download Rekap (CSV)", df.to_csv(index=False).encode('utf-8'), "rekap_cpmk.csv", "text/csv")
