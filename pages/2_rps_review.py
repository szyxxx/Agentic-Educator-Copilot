"""Halaman 2 — Review & Approval RPS"""

import streamlit as st
import json

from tools.database import load_courses, load_rps_weeks, update_week_status, get_connection

st.set_page_config(page_title="Review RPS", page_icon="📋", layout="wide")
st.title("📋 Review & Approval RPS")

# Course selector
courses = load_courses()
if not courses:
    st.warning("Belum ada mata kuliah. Silakan buat di halaman **Setup MK**.")
    st.stop()

course_options = {f"{c['name']} ({c['code']})": c['course_id'] for c in courses}
selected = st.selectbox("Pilih Mata Kuliah", list(course_options.keys()))
course_id = course_options[selected]

# Load weeks
weeks = load_rps_weeks(course_id)
if not weeks:
    st.info("RPS belum di-generate untuk mata kuliah ini.")
    st.stop()

# Status bar
total = len(weeks)
approved_count = sum(1 for w in weeks if w.get("status") == "disetujui")
col1, col2, col3 = st.columns(3)
col1.metric("Total Minggu", total)
col2.metric("Sudah Disetujui", f"{approved_count}/{total}")
col3.metric("Status", "✅ Siap Publish" if approved_count >= 14 else "📝 Draft")

# Progress bar
st.progress(approved_count / total if total > 0 else 0)
st.divider()

# Weekly review
for week in weeks:
    wnum = week.get("week_number", 0)
    title = week.get("title", "Untitled")
    status = week.get("status", "draft")
    wtype = week.get("type", "materi")

    status_icon = {"draft": "📝", "disetujui": "✅", "revisi_requested": "🔄"}.get(status, "❓")
    type_badge = {"uts": "🔵 UTS", "uas": "🔴 UAS", "materi": ""}.get(wtype, "")

    with st.expander(f"Minggu {wnum} — {title} {type_badge} [{status_icon} {status}]"):
        # Display details
        if week.get("description"):
            st.write(week["description"])

        c1, c2 = st.columns(2)
        with c1:
            if week.get("sub_cpmk"):
                subcpmk = week["sub_cpmk"]
                if isinstance(subcpmk, list):
                    subcpmk = ", ".join(subcpmk)
                st.write(f"**Sub-CPMK:** {subcpmk}")
            if week.get("teaching_method"):
                st.write(f"**Metode:** {week['teaching_method']}")
        with c2:
            indicators = week.get("learning_indicators", [])
            if isinstance(indicators, str):
                try:
                    indicators = json.loads(indicators)
                except (json.JSONDecodeError, TypeError):
                    indicators = [indicators]
            if indicators:
                st.write("**Indikator:**")
                for ind in indicators:
                    st.write(f"  - {ind}")

        topics = week.get("topics", [])
        if isinstance(topics, str):
            try:
                topics = json.loads(topics)
            except (json.JSONDecodeError, TypeError):
                topics = [topics]
        if topics:
            st.write(f"**Topik:** {', '.join(str(t) for t in topics)}")

        # Edit section
        if wtype == "materi":
            st.divider()
            new_title = st.text_input("Judul", title, key=f"title_{wnum}")
            new_desc = st.text_area("Deskripsi", week.get("description", ""), key=f"desc_{wnum}", height=80)

            bc1, bc2, bc3 = st.columns(3)
            week_id = week.get("week_id", f"{course_id}_w{wnum}")

            if bc1.button("✅ Setujui", key=f"approve_{wnum}"):
                update_week_status(week_id, "disetujui")
                st.success(f"Minggu {wnum} disetujui!")
                st.rerun()

            if bc2.button("✏️ Simpan Edit", key=f"edit_{wnum}"):
                conn = get_connection()
                conn.execute("UPDATE rps_weeks SET title = ?, description = ? WHERE week_id = ?",
                             (new_title, new_desc, week_id))
                conn.commit()
                conn.close()
                st.success("Perubahan disimpan!")
                st.rerun()

            revision_note = st.text_input("Instruksi revisi:", key=f"rev_{wnum}")
            if bc3.button("🔄 Minta Revisi", key=f"revise_{wnum}"):
                update_week_status(week_id, "revisi_requested", revision_note)
                st.info(f"Revisi diminta untuk Minggu {wnum}")
                st.rerun()

# Bulk actions
st.divider()
bc1, bc2 = st.columns(2)
if bc1.button("✅ Approve Semua Minggu", type="primary"):
    for w in weeks:
        wid = w.get("week_id", f"{course_id}_w{w.get('week_number', 0)}")
        update_week_status(wid, "disetujui")
    st.success("Semua minggu disetujui!")
    st.rerun()

if bc2.button("📢 Publish RPS", disabled=approved_count < 14):
    st.success("🎉 RPS berhasil dipublikasikan!")
    st.balloons()
