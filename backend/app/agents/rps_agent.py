import operator
from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, END
from app.core.llm import get_llm
from langchain_core.messages import SystemMessage, HumanMessage

class CurriculumState(TypedDict):
    course_name: str
    course_code: str
    sks: int
    program_study: str
    semester: int
    cpl_list: List[str]
    sndikti_rules: str
    trend_data: str
    references: str
    bahan_kajian: List[str]
    learning_methods: List[str]
    learning_modality: str
    description: str
    user_cpl: List[str]
    user_cpmk: List[str]
    user_references: List[str]
    draft_rps: str
    validated_rps: str
    meetings_list: list
    compliance_score: float
    compliance_issues: list
    messages: Annotated[list, operator.add]

# Nodes (Placeholder implementations)
def fetch_sndikti_rules_node(state: CurriculumState):
    print("Fetching SN-Dikti Rules...")
    # Mock fetching
    return {"sndikti_rules": "Permendiktisaintek No. 39 Tahun 2025: 16 Pertemuan, Evaluasi terstruktur."}

def fetch_trends_node(state: CurriculumState):
    print("Fetching Industry Trends...")
    llm = get_llm("simple")
    prompt = f"Berikan 3 tren teknologi atau industri terkini (tahun 2026) di Indonesia yang relevan dengan mata kuliah {state.get('course_name')}. Jawab dalam bentuk list singkat tanpa markdown format."
    try:
        response = llm.invoke(prompt)
        trend_data = response.content
    except Exception as e:
        trend_data = f"Gagal mengambil tren: {str(e)}"
    return {"trend_data": trend_data}

def generate_cpl_cpmk_node(state: CurriculumState):
    print("Generating CPL & CPMK...")

    user_cpl = [c.strip() for c in (state.get("user_cpl") or []) if c and c.strip()]
    user_cpmk = [c.strip() for c in (state.get("user_cpmk") or []) if c and c.strip()]

    # If the dosen already provided BOTH lists, respect them verbatim.
    if user_cpl and user_cpmk:
        combined = [f"CPL:{c}" for c in user_cpl] + [f"CPMK:{c}" for c in user_cpmk]
        return {"cpl_list": combined}

    llm = get_llm("complex")

    bahan_kajian = state.get("bahan_kajian") or []
    bahan_kajian_text = (
        "\n".join(f"- {b}" for b in bahan_kajian) if bahan_kajian else "(belum ditentukan)"
    )

    description = (state.get("description") or "").strip()
    description_block = (
        f"Konteks tambahan dari dosen (PRIORITAS UTAMA, gunakan untuk mengarahkan output):\n{description}\n"
        if description
        else ""
    )

    # Tell the LLM exactly which side to fill. If one of the two lists is
    # already provided we keep it and only ask for the missing list.
    if user_cpl and not user_cpmk:
        instruction = (
            "Dosen sudah menyediakan CPL berikut, JANGAN ubah:\n"
            + "\n".join(f"- {c}" for c in user_cpl)
            + "\n\nBuat 4-6 CPMK saja yang selaras dengan CPL di atas dan menutupi seluruh bahan kajian."
        )
        need = "cpmk"
    elif user_cpmk and not user_cpl:
        instruction = (
            "Dosen sudah menyediakan CPMK berikut, JANGAN ubah:\n"
            + "\n".join(f"- {c}" for c in user_cpmk)
            + "\n\nBuat 3-4 CPL saja yang menjadi induk CPMK di atas."
        )
        need = "cpl"
    else:
        instruction = (
            "Buat 3-4 CPL DAN 4-6 CPMK yang saling selaras."
        )
        need = "both"

    prompt = f"""
    Anda adalah pakar kurikulum pendidikan tinggi di Indonesia.
    Mata Kuliah: {state.get('course_name')}
    Program Studi: {state.get('program_study')}
    SKS: {state.get('sks')}
    Tren industri: {state.get('trend_data')}
    Bahan kajian utama:
    {bahan_kajian_text}

    {description_block}{instruction}

    Output HARUS JSON murni tanpa markdown, dengan struktur PERSIS:
    {{"cpl": ["..."], "cpmk": ["..."]}}
    Jika dosen sudah menyediakan salah satu list, kosongkan list itu dengan [].
    Hanya keluarkan JSON.
    """
    import json
    raw_response_text = ""
    try:
        response = llm.invoke(prompt)
        raw_response_text = response.content or ""
        text = raw_response_text.replace("```json", "").replace("```", "").strip()
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            text = text[start:end]
        parsed = json.loads(text)
        cpl_items = parsed.get("cpl") or []
        cpmk_items = parsed.get("cpmk") or []
    except Exception as e:
        print(f"CPL/CPMK JSON parse error: {e}, raw: {raw_response_text[:300]}")
        cpl_items, cpmk_items = [], []

    # Merge: keep whatever the dosen typed, append AI suggestions for the rest.
    final_cpl = list(user_cpl) if user_cpl else [str(c).strip() for c in cpl_items if c]
    final_cpmk = list(user_cpmk) if user_cpmk else [str(c).strip() for c in cpmk_items if c]

    combined = [f"CPL:{c}" for c in final_cpl] + [f"CPMK:{c}" for c in final_cpmk]
    return {"cpl_list": combined}

def synthesize_bahan_kajian_node(state: CurriculumState):
    """If the dosen left bahan_kajian empty, ask the LLM to propose a small set
    based on the course brief. The proposed list is then fed to draft_rps_node
    so per-week `bahan_kajian_topik` values can pick from a real catalog.
    """
    user_bahan = [b for b in (state.get("bahan_kajian") or []) if (b or "").strip()]
    if user_bahan:
        return {"bahan_kajian": user_bahan}

    print("Synthesizing Bahan Kajian / Topik categories...")
    llm = get_llm("simple")

    raw_list = state.get("cpl_list") or []
    cpmk_clean = [
        l[5:].strip() for l in raw_list if l.startswith("CPMK:")
    ]
    cpmk_text = "\n".join(f"- {c}" for c in cpmk_clean) or "(belum ada)"
    description = (state.get("description") or "").strip()

    prompt = f"""
    Anda merancang daftar "Bahan Kajian / Topik" tingkat tinggi untuk RPS.
    Daftar ini akan diulang lintas minggu di tabel pertemuan (mis. "AI dalam Industri dan Masyarakat" muncul di Modul 1, 3, 4, 12).

    Mata Kuliah: {state.get('course_name')} ({state.get('sks')} SKS)
    Konteks dari dosen:
    {description or "(tidak ada)"}

    CPMK terkait:
    {cpmk_text}

    Buat 4-6 kategori Bahan Kajian yang ringkas (3-7 kata per item), unik, mencakup seluruh topik perkuliahan.
    JANGAN buat sub-topik mingguan; hanya kategori payung.

    Output HARUS JSON array murni: ["Kategori 1", "Kategori 2", ...]. Hanya JSON.
    """
    import json
    try:
        response = llm.invoke(prompt)
        text = (response.content or "").replace("```json", "").replace("```", "").strip()
        start = text.find("[")
        end = text.rfind("]") + 1
        if start < 0 or end <= start:
            return {"bahan_kajian": []}
        parsed = json.loads(text[start:end])
        cleaned = [str(b).strip() for b in parsed if str(b).strip()]
        # De-duplicate while preserving order
        seen, out = set(), []
        for b in cleaned:
            key = b.lower()
            if key not in seen:
                seen.add(key)
                out.append(b)
        return {"bahan_kajian": out[:6]}
    except Exception as e:
        print(f"[rps_agent] bahan_kajian synth failed: {e}")
        return {"bahan_kajian": []}


def synthesize_references_node(state: CurriculumState):
    """If the dosen left the references list empty, ask the LLM to propose a
    short numbered bibliography (real textbooks, key papers, official docs)
    so per-week `reference_indices` can cite something concrete.
    """
    user_refs = [r for r in (state.get("user_references") or []) if (r or "").strip()]
    if user_refs:
        return {"user_references": user_refs}

    print("Synthesizing reference list...")
    llm = get_llm("simple")

    bahan_kajian = state.get("bahan_kajian") or []
    bahan_text = "\n".join(f"- {b}" for b in bahan_kajian) or "(tidak ada)"

    raw_list = state.get("cpl_list") or []
    cpmk_clean = [l[5:].strip() for l in raw_list if l.startswith("CPMK:")]
    cpmk_text = "\n".join(f"- {c}" for c in cpmk_clean) or "(belum ada)"

    description = (state.get("description") or "").strip()

    prompt = f"""
    Susun daftar pustaka untuk RPS mata kuliah {state.get('course_name')} ({state.get('sks')} SKS).
    Bahan Kajian:
    {bahan_text}

    CPMK:
    {cpmk_text}

    Konteks dari dosen:
    {description or "(tidak ada)"}

    ATURAN:
    - Buat 5-8 referensi akademik nyata (textbook, paper konferensi top-tier, dokumentasi resmi).
    - Format setiap entri: "Penulis, Tahun. Judul. Penerbit/Konferensi." (atau URL resmi untuk dokumentasi).
    - JANGAN gunakan placeholder seperti "Materi Minggu", "Buku Panduan", "Slide Dosen".
    - Pastikan referensi nyata-nyata ada (bukan halusinasi judul).

    Output HARUS JSON array murni: ["Referensi 1", "Referensi 2", ...]. Hanya JSON.
    """
    import json
    try:
        response = llm.invoke(prompt)
        text = (response.content or "").replace("```json", "").replace("```", "").strip()
        start = text.find("[")
        end = text.rfind("]") + 1
        if start < 0 or end <= start:
            return {"user_references": []}
        parsed = json.loads(text[start:end])
        cleaned = [str(r).strip() for r in parsed if str(r).strip() and len(str(r).strip()) > 10]
        seen, out = set(), []
        for r in cleaned:
            key = r.lower()
            if key not in seen:
                seen.add(key)
                out.append(r)
        return {"user_references": out[:8]}
    except Exception as e:
        print(f"[rps_agent] references synth failed: {e}")
        return {"user_references": []}


def draft_rps_node(state: CurriculumState):
    print("Drafting RPS...")
    llm = get_llm("complex")
    raw_list = state.get('cpl_list', [])
    # Strip internal prefixes added for parsing
    cpl_clean = [l[4:].strip() if l.startswith("CPL:") else l for l in raw_list if l.startswith("CPL:")]
    cpmk_clean = [l[5:].strip() if l.startswith("CPMK:") else l for l in raw_list if l.startswith("CPMK:")]
    # Fallback: no prefixes used
    if not cpl_clean and not cpmk_clean:
        cpl_clean = raw_list

    cpl_text = "\n".join([f"CPL-{i+1}: {c}" for i, c in enumerate(cpl_clean)])
    cpmk_text = "\n".join([f"{i+1}. {c}" for i, c in enumerate(cpmk_clean)])

    bahan_kajian = state.get("bahan_kajian") or []
    bahan_kajian_text = (
        "\n".join(f'- "{b}"' for b in bahan_kajian)
        if bahan_kajian
        else '(belum ditentukan — gunakan deskripsi singkat seperti "Pengantar")'
    )
    learning_methods = state.get("learning_methods") or []
    methods_text = (
        ", ".join(learning_methods)
        if learning_methods
        else "Bebas (Ceramah, Diskusi, Studi Kasus, dst.)"
    )
    modality = (state.get("learning_modality") or "").strip() or "Tidak ditentukan"

    # Build the numbered references list the LLM will cite by index. Prefer
    # the dosen's typed list; otherwise fall back to whatever blob (links + PDF
    # excerpt) was passed in via `references`.
    user_references = [
        r for r in (state.get("user_references") or []) if (r or "").strip()
    ]
    if user_references:
        references_list_lines = list(user_references)
    else:
        references_raw = state.get("references") or ""
        references_list_lines = [
            line.strip().lstrip("- ")
            for line in references_raw.splitlines()
            if line.strip() and not line.strip().startswith("---")
        ][:30]
    if not references_list_lines:
        references_list_lines = ["Referensi belum disediakan."]
    references_numbered = "\n".join(
        f"{i + 1}. {ref}" for i, ref in enumerate(references_list_lines)
    )

    description = (state.get("description") or "").strip()
    description_block = (
        f"\nKonteks & arahan utama dari dosen (PRIORITAS — gunakan untuk menentukan topik mingguan):\n{description}\n"
        if description
        else ""
    )

    prompt = f"""
    Buat rencana 16 pertemuan (14 minggu perkuliahan + 2 minggu ujian) untuk mata kuliah {state.get('course_name')} ({state.get('sks')} SKS).
    Gunakan format institusi: dua kolom topik (Bahan Kajian/Topik tingkat tinggi + Sub-Topik spesifik per minggu),
    satu nomor CPMK per baris, dan kutipan referensi sebagai daftar angka.
    {description_block}
    CPL yang harus dicapai:
    {cpl_text}

    CPMK yang harus dicapai (gunakan ANGKA 1, 2, 3, ... untuk merujuk ke list ini):
    {cpmk_text}

    Bahan Kajian/Topik yang tersedia (HARUS dipakai verbatim, BOLEH diulang lintas minggu):
    {bahan_kajian_text}

    Daftar Referensi bernomor (kutip dengan ANGKA, bukan teks):
    {references_numbered}

    Metode pembelajaran yang dipilih dosen (gunakan kombinasi dari daftar ini saja):
    {methods_text}

    Modalitas perkuliahan:
    {modality}

    ATURAN KETAT:
    - Minggu ke-8 HARUS bernilai persis: bahan_kajian_topik="", sub_topic_title="Ujian Tengah Semester (UTS)", sub_topic_description="", cpmk_number=null, reference_indices=[].
    - Minggu ke-16 HARUS bernilai persis: bahan_kajian_topik="", sub_topic_title="Ujian Akhir Semester (UAS)", sub_topic_description="", cpmk_number=null, reference_indices=[].
    - Untuk minggu non-ujian: `bahan_kajian_topik` HARUS salah satu dari daftar Bahan Kajian di atas, ditulis verbatim. Bahan Kajian boleh diulang lintas minggu.
    - `sub_topic_title` HARUS spesifik & bervariasi antar minggu, mencerminkan konteks dosen di atas.
    - `cpmk_number` adalah satu integer (bukan string, bukan list) yang merujuk nomor CPMK di atas.
    - `reference_indices` adalah list integer 1-based yang merujuk Daftar Referensi di atas (minimal 1 indeks per minggu non-ujian).

    Output HARUS berupa JSON array murni 16 elemen (tanpa markdown, tanpa teks pengantar):
    [
      {{
        "week": 1,
        "bahan_kajian_topik": "...",
        "sub_topic_title": "...",
        "sub_topic_description": "...",
        "cpmk_number": 1,
        "reference_indices": [1, 3, 8],
        "method": "Ceramah & Diskusi",
        "evaluation": "Tanya Jawab"
      }},
      ...
    ]
    Hanya outputkan JSON array.
    """
    import json
    try:
        response = llm.invoke(prompt)
        text = response.content.replace("```json", "").replace("```", "").strip()
        # Find JSON array boundaries
        start = text.find("[")
        end = text.rfind("]") + 1
        if start >= 0 and end > start:
            text = text[start:end]
        meetings = json.loads(text)
    except Exception as e:
        meetings = []
        print(f"Error parsing JSON from LLM: {str(e)}")

    # Coerce each entry against the constraints. The agent intentionally does
    # NOT validate strictly here — that happens in the API layer when the
    # meetings are persisted. We only normalize types so the downstream
    # consumers see consistent shapes.
    from app.core.rps_constants import (
        UAS_MODULE,
        UAS_TITLE,
        UTS_MODULE,
        UTS_TITLE,
        is_exam_week,
    )
    from app.core.rps_coerce import (
        coerce_bahan_kajian,
        coerce_cpmk_number,
        coerce_reference_indices,
    )

    normalized: list[dict] = []
    cpmk_len = len(cpmk_clean)
    refs_len = len(references_list_lines)
    for m in meetings if isinstance(meetings, list) else []:
        if not isinstance(m, dict):
            continue
        try:
            week = int(m.get("week", 0))
        except (TypeError, ValueError):
            continue

        if is_exam_week(week):
            normalized.append(
                {
                    "week": week,
                    "bahan_kajian_topik": "",
                    "sub_topic_title": (
                        UTS_TITLE if week == UTS_MODULE else UAS_TITLE
                    ),
                    "sub_topic_description": "",
                    "cpmk_number": None,
                    "reference_indices": [],
                    "method": "",
                    "evaluation": "",
                }
            )
            continue

        bahan_topik = coerce_bahan_kajian(
            m.get("bahan_kajian_topik", ""), bahan_kajian
        )
        cpmk_num = coerce_cpmk_number(m.get("cpmk_number"), cpmk_len)
        ref_indices, _ = coerce_reference_indices(
            m.get("reference_indices"), refs_len
        )
        normalized.append(
            {
                "week": week,
                "bahan_kajian_topik": bahan_topik,
                "sub_topic_title": str(m.get("sub_topic_title") or "").strip(),
                "sub_topic_description": str(
                    m.get("sub_topic_description") or ""
                ).strip(),
                "cpmk_number": cpmk_num,
                "reference_indices": ref_indices,
                "method": str(m.get("method") or "").strip(),
                "evaluation": str(m.get("evaluation") or "").strip(),
            }
        )

    return {"draft_rps": "JSON generated", "meetings_list": normalized}

def validate_compliance_node(state: CurriculumState):
    print("Validating Compliance with SN-DIKTI...")
    llm = get_llm("complex")
    
    meetings = state.get("meetings_list", [])
    import json
    meetings_str = json.dumps(meetings, indent=2)
    
    prompt = f"""
    Evaluasi rencana pembelajaran (RPS) berikut berdasarkan standar SN-DIKTI (Permendikbudristek No. 53 Tahun 2023 / peraturan terkait).
    Syarat utama SN-DIKTI:
    1. Harus ada 16 minggu/pertemuan (termasuk UTS dan UAS).
    2. Minggu ke-8 harus dialokasikan untuk UTS (Ujian Tengah Semester).
    3. Minggu ke-16 harus dialokasikan untuk UAS (Ujian Akhir Semester).
    4. Adanya penjabaran metode pembelajaran dan evaluasi yang jelas.

    RPS yang akan dievaluasi:
    {meetings_str}

    Berikan skor kepatuhan (0-100) dan daftar isu jika ada yang tidak sesuai.
    PENTING: Output HARUS dalam format JSON murni:
    {{
        "score": integer (0-100),
        "issues": ["isu 1", "isu 2"] (kosongkan list jika 100)
    }}
    Hanya outputkan JSON.
    """
    
    score = 80.0
    issues = []
    
    try:
        response = llm.invoke(prompt)
        text = response.content.replace("```json", "").replace("```", "").strip()
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            text = text[start:end]
        
        parsed = json.loads(text)
        score = float(parsed.get("score", 80))
        issues = parsed.get("issues", [])
    except Exception as e:
        print(f"Error validating compliance: {str(e)}")
        
    return {
        "validated_rps": state.get("draft_rps", ""),
        "compliance_score": score,
        "compliance_issues": issues
    }

def refine_rps_node(state: CurriculumState):
    print("Refining RPS...")
    return {}

def export_rps_node(state: CurriculumState):
    print("Exporting RPS...")
    return {}

def route_after_validation(state: CurriculumState):
    # Conditional logic based on validation
    if state.get("validated_rps"):
        return "compliant"
    return "needs_refinement"

def build_curriculum_graph():
    graph = StateGraph(CurriculumState)
    
    # Nodes
    graph.add_node("fetch_sndikti_rules", fetch_sndikti_rules_node)
    graph.add_node("fetch_industry_trends", fetch_trends_node)
    graph.add_node("generate_cpl_cpmk", generate_cpl_cpmk_node)
    graph.add_node("synthesize_bahan_kajian", synthesize_bahan_kajian_node)
    graph.add_node("synthesize_references", synthesize_references_node)
    graph.add_node("draft_rps", draft_rps_node)
    graph.add_node("validate_compliance", validate_compliance_node)
    graph.add_node("refine_rps", refine_rps_node)
    graph.add_node("export_rps", export_rps_node)
    
    # Edges
    graph.set_entry_point("fetch_sndikti_rules")
    graph.add_edge("fetch_sndikti_rules", "fetch_industry_trends")
    graph.add_edge("fetch_industry_trends", "generate_cpl_cpmk")
    graph.add_edge("generate_cpl_cpmk", "synthesize_bahan_kajian")
    graph.add_edge("synthesize_bahan_kajian", "synthesize_references")
    graph.add_edge("synthesize_references", "draft_rps")
    graph.add_edge("draft_rps", "validate_compliance")
    
    # Conditional edge — jika tidak compliant, refine dulu
    graph.add_conditional_edges(
        "validate_compliance",
        route_after_validation,
        {
            "compliant": "export_rps",
            "needs_refinement": "refine_rps"
        }
    )
    graph.add_edge("refine_rps", "validate_compliance")  # Loop hingga valid
    graph.add_edge("export_rps", END)
    
    return graph.compile()
