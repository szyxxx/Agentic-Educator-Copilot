"""
Educator Copilot — Main Streamlit Entry Point
================================================
Dashboard interaktif untuk dosen mengelola RPS, kuis, dan remedial.
"""

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langchain")
warnings.filterwarnings("ignore", message=".*allowed_objects.*")

import streamlit as st
from dotenv import load_dotenv
from tools.database import init_database

load_dotenv()
init_database()

st.set_page_config(
    page_title="Educator Copilot",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.main-header {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    padding: 2rem 2.5rem;
    border-radius: 16px;
    color: white;
    margin-bottom: 2rem;
    box-shadow: 0 8px 32px rgba(0,0,0,0.15);
}

.main-header h1 {
    font-size: 2.2rem;
    font-weight: 700;
    margin: 0;
    letter-spacing: -0.5px;
}

.main-header p {
    font-size: 1rem;
    opacity: 0.85;
    margin-top: 0.5rem;
}

.feature-card {
    background: linear-gradient(145deg, #ffffff 0%, #f8f9ff 100%);
    border: 1px solid #e8ecf4;
    border-radius: 12px;
    padding: 1.5rem;
    transition: all 0.3s ease;
    height: 100%;
}

.feature-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.08);
    border-color: #4361ee;
}

.feature-card h3 {
    font-size: 1.1rem;
    font-weight: 600;
    color: #1a1a2e;
    margin-bottom: 0.5rem;
}

.feature-card p {
    font-size: 0.85rem;
    color: #666;
    line-height: 1.5;
}

.stat-card {
    background: linear-gradient(135deg, #4361ee 0%, #3a0ca3 100%);
    border-radius: 12px;
    padding: 1.2rem;
    color: white;
    text-align: center;
}

.stat-card h2 {
    font-size: 2rem;
    font-weight: 700;
    margin: 0;
}

.stat-card p {
    font-size: 0.8rem;
    opacity: 0.85;
    margin: 0.3rem 0 0;
}
</style>
""", unsafe_allow_html=True)

# ── Main Page ───────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🎓 Educator Copilot</h1>
    <p>Sistem Agentic AI untuk mengelola siklus pembelajaran semester — dari perancangan RPS hingga analisis kuis & remediasi adaptif.</p>
</div>
""", unsafe_allow_html=True)

# Quick stats
from tools.database import load_courses, get_connection

courses = load_courses()
conn = get_connection()
total_weeks = conn.execute("SELECT COUNT(*) FROM rps_weeks").fetchone()[0]
approved = conn.execute("SELECT COUNT(*) FROM rps_weeks WHERE status = 'disetujui'").fetchone()[0]
quizzes = conn.execute("SELECT COUNT(*) FROM quiz_sessions").fetchone()[0]
conn.close()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<div class="stat-card"><h2>{len(courses)}</h2><p>Mata Kuliah</p></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="stat-card"><h2>{total_weeks}</h2><p>Minggu RPS</p></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="stat-card"><h2>{approved}</h2><p>Disetujui</p></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="stat-card"><h2>{quizzes}</h2><p>Kuis Dianalisis</p></div>', unsafe_allow_html=True)

st.divider()

# Feature cards
st.subheader("📌 Fitur Utama")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown("""
    <div class="feature-card">
        <h3>📝 RPS Generator</h3>
        <p>Generate draft RPS 16 minggu otomatis berdasarkan CPL/CPMK dengan alignment Bloom Taxonomy.</p>
    </div>
    """, unsafe_allow_html=True)
with c2:
    st.markdown("""
    <div class="feature-card">
        <h3>📊 Quiz Analyzer</h3>
        <p>Analisis hasil kuis, deteksi miskonsepsi, dan identifikasi gap pembelajaran per topik.</p>
    </div>
    """, unsafe_allow_html=True)
with c3:
    st.markdown("""
    <div class="feature-card">
        <h3>📑 Remedial Generator</h3>
        <p>Generate slide remedial adaptif yang menarget gap spesifik, siap export ke PPTX.</p>
    </div>
    """, unsafe_allow_html=True)

st.divider()
st.caption("Gunakan sidebar untuk navigasi ke halaman fitur. Mulai dari **Preset Template** → **Setup MK** → **Review RPS**.")
