"""Halaman 0 — Pemilihan Preset Template Institusi"""

import streamlit as st
from lib.template_presets import PRESETS, get_preset

st.set_page_config(page_title="Preset Template", page_icon="🏫", layout="wide")
st.title("🏫 Pilih Template Institusi")
st.markdown("Pilih preset yang sesuai dengan format RPS universitas Anda. "
            "Ini akan menentukan field mana yang aktif di form Setup MK.")

# Preset selection cards
for pid, preset in PRESETS.items():
    with st.container():
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown(f"### {preset.name}")
            st.caption(f"*{', '.join(preset.universities)}*")
            st.write(preset.description)
        with col2:
            st.metric("Fields", preset.active_fields)
        with col3:
            st.write(f"**Kompleksitas:** {preset.complexity}")
            if st.button("✅ Pilih", key=f"select_{pid}"):
                st.session_state["institution_preset"] = pid
                st.success(f"Preset **{preset.name}** dipilih!")
                st.balloons()

    st.divider()

# Show current selection
current = st.session_state.get("institution_preset", "standard")
p = get_preset(current)
st.info(f"**Preset aktif:** {p.name} ({p.active_fields} fields) — {p.complexity}")
