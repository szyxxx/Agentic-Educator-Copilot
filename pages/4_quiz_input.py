"""Halaman 4 — Input Kuis & Kunci Jawaban"""

import streamlit as st
import pandas as pd
import json

from tools.database import load_courses, get_connection, generate_id

st.set_page_config(page_title="Input Kuis", page_icon="📝", layout="wide")
st.title("📝 Input Hasil Kuis")

courses = load_courses()
if not courses:
    st.warning("Belum ada mata kuliah.")
    st.stop()

course_options = {f"{c['name']} ({c['code']})": c['course_id'] for c in courses}
selected = st.selectbox("Pilih Mata Kuliah", list(course_options.keys()))
course_id = course_options[selected]

week_num = st.number_input("Minggu ke-", min_value=1, max_value=16, value=1)
quiz_type = st.selectbox("Tipe Kuis", ["Pilihan Ganda", "Esai", "Campuran"])

st.divider()

# Answer key input
st.subheader("🔑 Kunci Jawaban")
num_questions = st.number_input("Jumlah Soal", min_value=1, max_value=50, value=10)

answer_key = {}
q_mapping = {}
cols = st.columns(5)
for i in range(num_questions):
    with cols[i % 5]:
        answer_key[f"q{i+1}"] = st.text_input(f"Soal {i+1}", key=f"ans_{i+1}", max_chars=5)
        q_mapping[f"q{i+1}"] = {"topic": "", "sub_cpmk": ""}

st.divider()

# Student responses
st.subheader("👥 Jawaban Mahasiswa")
st.caption("Upload CSV atau input manual. Format CSV: student_id, q1, q2, ..., qN")

input_method = st.radio("Metode Input", ["Upload CSV", "Input Manual"], horizontal=True)

student_responses = []

if input_method == "Upload CSV":
    csv_file = st.file_uploader("Upload CSV", type=["csv"])
    if csv_file:
        df = pd.read_csv(csv_file)
        st.dataframe(df, use_container_width=True)
        for _, row in df.iterrows():
            answers = {}
            for col in df.columns[1:]:
                answers[col] = str(row[col])
            student_responses.append({
                "student_id": str(row.iloc[0]),
                "answers": answers,
            })
        st.success(f"{len(student_responses)} mahasiswa terdeteksi.")
else:
    num_students = st.number_input("Jumlah Mahasiswa", min_value=1, max_value=100, value=5)
    for s in range(num_students):
        with st.expander(f"Mahasiswa {s+1}"):
            sid = st.text_input(f"ID/NIM", key=f"sid_{s}", value=f"MHS-{s+1:03d}")
            answers = {}
            scols = st.columns(5)
            for q in range(num_questions):
                with scols[q % 5]:
                    answers[f"q{q+1}"] = st.text_input(f"S{s+1}-Q{q+1}", key=f"s{s}_q{q+1}", max_chars=5)
            student_responses.append({"student_id": sid, "answers": answers})

st.divider()

if st.button("💾 Simpan & Analisis", type="primary", use_container_width=True):
    quiz_id = generate_id()
    conn = get_connection()

    # Save quiz session
    conn.execute(
        """INSERT INTO quiz_sessions (quiz_id, course_id, week_number, quiz_type, answer_key, question_mapping)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (quiz_id, course_id, week_num, quiz_type, json.dumps(answer_key), json.dumps(q_mapping))
    )

    # Save individual results
    for sr in student_responses:
        conn.execute(
            """INSERT INTO quiz_results (result_id, quiz_id, student_id, answers)
               VALUES (?, ?, ?, ?)""",
            (generate_id(), quiz_id, sr["student_id"], json.dumps(sr["answers"]))
        )

    conn.commit()
    conn.close()

    st.session_state["last_quiz_id"] = quiz_id
    st.session_state["last_quiz_data"] = {
        "quiz_id": quiz_id,
        "answer_key": answer_key,
        "question_mapping": q_mapping,
        "student_responses": student_responses,
    }

    st.success(f"✅ Kuis disimpan (ID: {quiz_id}). Lanjut ke halaman **Performance** untuk analisis.")
