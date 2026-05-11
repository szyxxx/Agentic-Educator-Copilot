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
st.subheader("🔑 Kunci Jawaban & Soal")

key_method = st.radio("Metode Input Kunci Jawaban", ["Input Manual", "Generate dengan AI (dari Materi)", "Upload CSV Soal"], horizontal=True)

answer_key = {}
q_mapping = {}

if key_method == "Input Manual":
    num_questions = st.number_input("Jumlah Soal", min_value=1, max_value=50, value=10)
    cols = st.columns(5)
    for i in range(num_questions):
        with cols[i % 5]:
            answer_key[f"q{i+1}"] = st.text_input(f"Soal {i+1}", key=f"ans_{i+1}", max_chars=5)
            q_mapping[f"q{i+1}"] = {"topic": "", "sub_cpmk": ""}

elif key_method == "Generate dengan AI (dari Materi)":
    num_questions = st.number_input("Jumlah Soal yang Digenerate", min_value=1, max_value=50, value=5)
    
    generate_btn = st.button("✨ Generate Soal", type="primary")
    if generate_btn:
        with st.spinner("Membaca materi dan membuat soal..."):
            conn = get_connection()
            row = conn.execute("SELECT extracted_text FROM materials WHERE course_id = ? AND week_number = ?", (course_id, week_num)).fetchone()
            conn.close()
            
            if row and row["extracted_text"]:
                from tools.quiz_generator import generate_quiz_from_material
                generated = generate_quiz_from_material(row["extracted_text"], num_questions, quiz_type)
                if generated:
                    # Persist generated quiz to session state so it doesn't vanish on re-render
                    st.session_state[f"generated_quiz_{course_id}_{week_num}"] = generated
                    st.success("Berhasil generate soal!")
                else:
                    st.error("Gagal men-generate soal dari AI.")
            else:
                st.error("Belum ada materi yang diupload untuk minggu ini. Silakan upload materi di halaman 3 terlebih dahulu.")
                
    state_key = f"generated_quiz_{course_id}_{week_num}"
    if state_key in st.session_state:
        st.write("Edit soal dan kunci jawaban di bawah ini. Anda dapat mengubah isi, menambah baris, atau menghapus baris.")
        df_quiz = pd.DataFrame(st.session_state[state_key])
        
        edited_df = st.data_editor(df_quiz, use_container_width=True, num_rows="dynamic", key=f"editor_{state_key}")
        
        # Parse into answer_key and q_mapping
        for idx, row in edited_df.iterrows():
            q_id = f"q{idx+1}"
            answer_key[q_id] = str(row.get("correct_answer", ""))
            q_mapping[q_id] = {"topic": str(row.get("topic", "")), "sub_cpmk": ""}
            
        csv = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Download Soal (CSV)",
            data=csv,
            file_name=f'soal_kuis_{course_id}_w{week_num}.csv',
            mime='text/csv',
        )

elif key_method == "Upload CSV Soal":
    csv_soal = st.file_uploader("Upload CSV Soal & Kunci Jawaban", type=["csv"])
    if csv_soal:
        df_soal = pd.read_csv(csv_soal)
        st.dataframe(df_soal, use_container_width=True)
        for idx, row in df_soal.iterrows():
            q_id = f"q{idx+1}"
            answer_key[q_id] = str(row.get("correct_answer", ""))
            q_mapping[q_id] = {"topic": str(row.get("topic", "")), "sub_cpmk": ""}
        num_questions = len(df_soal)
        st.success(f"Berhasil memuat {num_questions} soal dari CSV.")

st.divider()

# Ensure num_questions matches the final answer key size
num_questions_final = len(answer_key) if answer_key else num_questions

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
    if num_questions_final == 0:
        st.warning("Tentukan kunci jawaban terlebih dahulu untuk menginput jawaban mahasiswa secara manual.")
    for s in range(num_students):
        with st.expander(f"Mahasiswa {s+1}"):
            sid = st.text_input(f"ID/NIM", key=f"sid_{s}", value=f"MHS-{s+1:03d}")
            answers = {}
            scols = st.columns(5)
            for q in range(num_questions_final):
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
