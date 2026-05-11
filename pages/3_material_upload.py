"""Halaman 3 — Upload Materi & AI Review"""

import streamlit as st
import os
import tempfile

from tools.database import load_courses, get_connection, generate_id
from tools.document_reader import extract_pdf_text
from lib.llm_router import call_llm_with_fallback

st.set_page_config(page_title="Upload Materi", page_icon="📄", layout="wide")
st.title("📄 Upload Materi & AI Review")

courses = load_courses()
if not courses:
    st.warning("Belum ada mata kuliah.")
    st.stop()

course_options = {f"{c['name']} ({c['code']})": c['course_id'] for c in courses}
selected = st.selectbox("Pilih Mata Kuliah", list(course_options.keys()))
course_id = course_options[selected]

week_num = st.number_input("Minggu ke-", min_value=1, max_value=16, value=1)

uploaded = st.file_uploader("Upload PDF Materi", type=["pdf"])

if uploaded:
    # Save temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded.getbuffer())
        tmp_path = tmp.name

    st.success(f"📄 File **{uploaded.name}** berhasil diupload.")

    if st.button("🔍 Review Materi dengan AI", type="primary"):
        with st.spinner("Mengekstrak dan menganalisis materi..."):
            text = extract_pdf_text(tmp_path)

            if text.startswith("[ERROR]"):
                st.error(text)
            else:
                st.text_area("📝 Teks Terekstraksi (preview)", text[:2000], height=200)

                # Get Sub-CPMK for this week
                conn = get_connection()
                row = conn.execute(
                    "SELECT sub_cpmk, title FROM rps_weeks WHERE course_id = ? AND week_number = ?",
                    (course_id, week_num)
                ).fetchone()
                conn.close()

                sub_cpmk = dict(row)["sub_cpmk"] if row else "N/A"
                week_title = dict(row)["title"] if row else "N/A"

                prompt = f"""Review materi PDF berikut terhadap Sub-CPMK yang ditargetkan.

Minggu: {week_num} — {week_title}
Sub-CPMK: {sub_cpmk}

Materi (excerpt):
{text[:3000]}

Berikan review dalam format:
1. **Kesesuaian**: Apakah materi sudah sesuai dengan Sub-CPMK? (✅/⚠️/❌)
2. **Topik Tercakup**: Apa saja yang sudah dibahas?
3. **Gap**: Apa yang belum dibahas tapi diperlukan?
4. **Saran**: Rekomendasi perbaikan."""

                review = call_llm_with_fallback("material_review", prompt)
                st.markdown("### 🤖 Hasil Review AI")
                st.markdown(review)

                # Save to DB
                conn = get_connection()
                conn.execute(
                    """INSERT OR REPLACE INTO materials
                       (material_id, course_id, week_number, filename, file_path, extracted_text, ai_review)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (generate_id(), course_id, week_num, uploaded.name, tmp_path, text[:5000], review)
                )
                conn.commit()
                conn.close()
                st.success("Review disimpan ke database.")

    # Cleanup
    try:
        os.unlink(tmp_path)
    except Exception:
        pass
