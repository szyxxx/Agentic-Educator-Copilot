"""Halaman 5 — Dashboard Performance & Slide Remedial"""

import streamlit as st
import json
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from tools.database import get_connection
from agents.learning_agent import run_learning_agent
from lib.slide_exporter import export_to_pptx

st.set_page_config(page_title="Performance Dashboard", page_icon="📊", layout="wide")
st.title("📊 Performance Dashboard & Remedial")

quiz_data = st.session_state.get("last_quiz_data")
quiz_id = st.session_state.get("last_quiz_id")

if not quiz_data and not quiz_id:
    st.info("Pilih kuis di sidebar atau input kuis baru di halaman **Input Kuis**.")
    st.stop()

# Auto-run analysis if not yet run
if "learning_result" not in st.session_state or st.session_state.learning_result.get("quiz_results", {}).get("quiz_id") != quiz_id:
    with st.spinner("🤖 Menganalisis kuis dan men-generate remedial..."):
        try:
            result = run_learning_agent(quiz_data, week=1)
            st.session_state.learning_result = result
        except Exception as e:
            st.error(f"❌ Error saat analisis: {e}")
            st.stop()

result = st.session_state.learning_result
stats = result.get("class_stats", {})
error_rates = result.get("error_rates", {})
gaps = result.get("detected_gaps", [])
slides = result.get("remedial_slides", [])
scored = result.get("scored_students", [])

# ── Summary Metrics ────────────────────────────────────────────────
st.subheader("📈 Statistik Kelas")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Rata-rata Skor", f"{stats.get('mean', 0)}")
c2.metric("Median", f"{stats.get('median', 0)}")
c3.metric("Di Bawah KKM", f"{stats.get('pct_below_kkm', 0)}%")
c4.metric("Jumlah Mahasiswa", f"{stats.get('count', 0)}")

# ── Charts ─────────────────────────────────────────────────────────
col1, col2 = st.columns([1, 1])

with col1:
    st.write("**Distribusi Skor Mahasiswa**")
    if scored:
        df_scores = pd.DataFrame(scored)
        fig = px.histogram(df_scores, x="score", nbins=10, 
                           labels={"score": "Skor", "count": "Jumlah Mahasiswa"},
                           color_discrete_sequence=["#4361ee"])
        fig.add_vline(x=60, line_dash="dash", line_color="red", annotation_text="KKM 60")
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.write("**Error Rate per Soal**")
    if error_rates:
        df_errors = pd.DataFrame([{"Soal": k, "Error Rate (%)": v["error_rate"]} for k, v in error_rates.items()])
        df_errors = df_errors.sort_values("Error Rate (%)", ascending=False)
        fig2 = px.bar(df_errors, x="Soal", y="Error Rate (%)", color="Error Rate (%)",
                      color_continuous_scale="Reds")
        fig2.add_hline(y=40, line_dash="dash", line_color="orange", annotation_text="Threshold 40%")
        st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ── Misconceptions ─────────────────────────────────────────────────
st.subheader("⚠️ Analisis Miskonsepsi")
st.write(result.get("week_material_summary", ""))

if gaps:
    for g in gaps:
        with st.container():
            st.error(f"**{g.get('severity', 'high').upper()}**: {g.get('misconception')}")
            st.caption(f"Kemungkinan penyebab: {g.get('likely_cause')} | Topik terdampak: {', '.join(g.get('affected_topics', []))}")
else:
    st.success("Tidak ada miskonsepsi signifikan yang terdeteksi.")

st.divider()

# ── Remedial Slides ────────────────────────────────────────────────
st.subheader("📑 Slide Remedial Adaptif")
if slides:
    slide_tabs = st.tabs([f"Slide {s['slide_number']}" for s in slides])
    for i, slide in enumerate(slides):
        with slide_tabs[i]:
            st.markdown(f"### {slide.get('title', 'Untitled')}")
            st.write(slide.get('content', ''))
            if slide.get('key_points'):
                for point in slide['key_points']:
                    st.markdown(f"- {point}")

    # Export to PPTX
    if st.button("⬇️ Download PPTX Remedial", type="primary"):
        try:
            pptx_bytes = export_to_pptx(slides)
            st.download_button(
                label="Simpan File PPTX",
                data=pptx_bytes,
                file_name=f"remedial_quiz_{quiz_id}.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
            )
        except Exception as e:
            st.error(f"Gagal generate PPTX: {e}")
else:
    st.info("Tidak ada slide remedial yang di-generate (skor kelas di atas batas toleransi).")
