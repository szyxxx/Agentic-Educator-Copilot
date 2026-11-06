"""Kontrak payload Ollama dan JSON lokal; transport diganti tanpa jaringan."""
import json

import pytest
from langchain_core.messages import AIMessage
from langchain_ollama import ChatOllama
from pydantic import BaseModel, TypeAdapter

from app.core import config, llm


class Jawaban(BaseModel):
    nilai: int


def test_ollama_mematikan_thinking_dan_mengirim_konteks_keepalive(monkeypatch):
    monkeypatch.setattr(config, "OLLAMA_NUM_CTX", 8192, raising=False)
    monkeypatch.setattr(config, "OLLAMA_KEEP_ALIVE", "2m", raising=False)
    model = llm._build_ollama("complex")
    params = model._chat_params([])
    assert params["think"] is False
    assert params["options"]["num_ctx"] == 8192
    assert params["keep_alive"] == "2m"


def test_json_ollama_memvalidasi_dan_mencoba_ulang_sekali(monkeypatch):
    from app.core.llm_json import invoke_json

    calls = []
    def invoke(self, prompt, **kwargs):
        calls.append((prompt, self._chat_params([], **kwargs)))
        return AIMessage(content='{"nilai":"rusak"}' if len(calls) == 1 else '{"nilai":23}')
    monkeypatch.setattr(ChatOllama, "invoke", invoke)
    result = invoke_json(llm._build_ollama("complex"), "Nilai jawaban", adapter=TypeAdapter(Jawaban))
    assert result == {"nilai": 23}
    assert len(calls) == 2
    assert calls[0][1]["format"]["properties"]["nilai"]["type"] == "integer"
    assert "rusak" not in calls[1][0]  # Jangan menyuntikkan kembali keluaran model ke prompt.


def test_json_ollama_gagal_setelah_dua_percobaan(monkeypatch):
    from app.core.llm_json import invoke_json

    calls = []
    def invoke(self, prompt, **kwargs):
        calls.append(prompt)
        return AIMessage(content="bukan JSON")
    monkeypatch.setattr(ChatOllama, "invoke", invoke)
    with pytest.raises(ValueError):
        invoke_json(llm._build_ollama("complex"), "Nilai", adapter=TypeAdapter(Jawaban))
    assert len(calls) == 2


def test_json_provider_lain_tidak_diubah_atau_diulang(llm):
    from app.core.llm_json import invoke_json

    llm.reply('{"nilai":"tetap"}')
    assert invoke_json(llm, "Nilai", adapter=TypeAdapter(Jawaban)) == {"nilai": "tetap"}
    assert llm.prompts == ["Nilai"]


def test_penilaian_ollama_mengirim_temperatur_nol_dan_seed(monkeypatch, soal):
    from app.agents import grading_agent

    params = []
    model = llm._build_ollama("complex")
    monkeypatch.setattr(grading_agent, "get_llm", lambda task: model)
    def invoke(self, prompt, **kwargs):
        params.append(self._chat_params([], **kwargs))
        return AIMessage(content='[{"id":"Q003","score":24,"feedback":"Baik"}]')
    monkeypatch.setattr(ChatOllama, "invoke", invoke)
    result = grading_agent.grade_essay_node({"questions": [soal.esai1], "student_answers": {}})
    assert result["essay_scores"][0]["score"] == 24
    assert params[0]["options"]["temperature"] == 0
    assert params[0]["options"]["seed"] == 42


@pytest.mark.parametrize("response,metadata", [('{"nilai":1}', {"done_reason":"length"}), ('[]', {}), ('{"nilai":true}', {}), ('```json\n{"nilai":3}\n```', {})])
def test_json_lokal_invalid_atau_terpotong_diulang_dan_tidak_diterima(monkeypatch, response, metadata):
    from app.core.llm_json import invoke_json

    calls = []
    def invoke(self, prompt, **kwargs):
        calls.append(prompt)
        return AIMessage(content=response, response_metadata=metadata)
    monkeypatch.setattr(ChatOllama, "invoke", invoke)
    with pytest.raises(ValueError):
        invoke_json(llm._build_ollama("complex"), "Nilai", adapter=TypeAdapter(Jawaban))
    assert len(calls) == 2


def test_skor_esai_lokal_parsial_diulang_sebelum_nilai_final(monkeypatch, soal):
    from app.agents import grading_agent

    model = llm._build_ollama("complex")
    monkeypatch.setattr(grading_agent, "get_llm", lambda task: model)
    calls = []
    def invoke(self, prompt, **kwargs):
        calls.append(prompt)
        data = [{"id":"Q003","score":24,"feedback":"Baik"}]
        if len(calls) == 2:
            data.append({"id":"Q004","score":15,"feedback":"Cukup"})
        return AIMessage(content=json.dumps(data))
    monkeypatch.setattr(ChatOllama, "invoke", invoke)
    result = grading_agent.grade_essay_node({"questions": [soal.esai1,soal.esai2], "student_answers": {}})
    assert [s["score"] for s in result["essay_scores"]] == [24,15]
    assert len(calls) == 2


def test_embedding_ollama_memakai_model_dan_melepas_model_setelah_panggilan(monkeypatch):
    from app.core import rag
    from langchain_ollama import OllamaEmbeddings

    monkeypatch.setattr(config, "EMBEDDING_PROVIDER", "ollama", raising=False)
    monkeypatch.setattr(config, "OLLAMA_EMBEDDING_MODEL", "bge-m3", raising=False)
    monkeypatch.setattr(config, "OLLAMA_EMBEDDING_BASE_URL", "http://127.0.0.1:11434", raising=False)
    embeddings = rag.get_embeddings()
    assert isinstance(embeddings, OllamaEmbeddings)
    calls = []
    def embed(model, texts, **kwargs):
        calls.append({"model": model, "texts": texts, **kwargs})
        return {"embeddings":[[0.1,0.2]]}
    monkeypatch.setattr(embeddings._client, "embed", embed)
    assert embeddings.embed_query("Regresi") == [0.1,0.2]
    assert calls[0]["model"] == "bge-m3"
    assert calls[0]["keep_alive"] == 0
    assert calls[0]["options"]["num_gpu"] == 0


def test_embedding_huggingface_tetap_jalur_bawaan(monkeypatch):
    from app.core import rag

    monkeypatch.setattr(config, "EMBEDDING_PROVIDER", "huggingface", raising=False)
    sentinel=object()
    monkeypatch.setattr(rag,"HuggingFaceEmbeddings",lambda **kwargs:sentinel)
    assert rag.get_embeddings() is sentinel


def test_provider_embedding_tidak_dikenal_ditolak(monkeypatch):
    from app.core import rag

    monkeypatch.setattr(config, "EMBEDDING_PROVIDER", "salah", raising=False)
    with pytest.raises(ValueError):
        rag.get_embeddings()


def test_id_soal_lokal_ganda_diulang_sebelum_draft_disimpan(client, monkeypatch):
    from app.agents import quiz_agent

    model=llm._build_ollama("simple")
    monkeypatch.setattr(quiz_agent,"get_llm",lambda task:model)
    calls=[]
    def invoke(self,prompt,**kwargs):
        calls.append(prompt)
        data=[{"id":"Q001","type":"multiple_choice","question":"Satu?","options":{"A":"satu","B":"dua","C":"tiga","D":"empat"},"correct_answer":"A"}, {"id":"Q001" if len(calls)==1 else "Q002","type":"multiple_choice","question":"Dua?","options":{"A":"satu","B":"dua","C":"tiga","D":"empat"},"correct_answer":"B"}]
        return AIMessage(content=json.dumps(data))
    monkeypatch.setattr(ChatOllama,"invoke",invoke)
    res=client.post("/api/quiz/generate",json={"course_id":"c1","quiz_type":"multiple_choice","num_questions":2,"material_content":"Materi"})
    assert res.status_code==200,res.text
    assert [q["id"] for q in res.json()["data"]["questions"]]==["Q001","Q002"]
    assert len(calls)==2


def test_regenerasi_minggu_lokal_mengulang_pemetaan_di_luar_katalog(client, monkeypatch, rps_lengkap):
    from app.core import llm as llm_module

    rid=client.post('/api/rps/',json=rps_lengkap).json()['rps_id']
    model=llm_module._build_ollama('complex')
    monkeypatch.setattr(llm_module,'get_llm',lambda task:model)
    calls=[]
    def invoke(self,prompt,**kwargs):
        calls.append(prompt)
        meeting=dict(rps_lengkap['meetings'][2])
        meeting['cpmk_number']=99 if len(calls)==1 else 1
        return AIMessage(content=json.dumps(meeting))
    monkeypatch.setattr(ChatOllama,'invoke',invoke)
    res=client.post(f'/api/rps/{rid}/meetings/3/regenerate',json={'feedback':'Perbaiki'})
    assert res.status_code==200,res.text
    detail=client.get(f'/api/dashboard/rps/{rid}').json()
    assert detail['meetings'][2]['cpmk_number']==1
    assert len(calls)==2


def test_fill_missing_lokal_tidak_melaporkan_sukses_kosong(client, monkeypatch, rps_lengkap):
    from app.core import llm as llm_module

    rps_lengkap['meetings'][0]['sub_topic_description']=''
    rid=client.post('/api/rps/',json=rps_lengkap).json()['rps_id']
    model=llm_module._build_ollama('complex')
    monkeypatch.setattr(llm_module,'get_llm',lambda task:model)
    calls=[]
    def invoke(self,prompt,**kwargs):
        calls.append(prompt)
        return AIMessage(content=json.dumps([{'week':1,'fills':{'sub_topic_description':None if len(calls)==1 else 'Deskripsi pengganti yang benar.'}}]))
    monkeypatch.setattr(ChatOllama,'invoke',invoke)
    res=client.post(f'/api/rps/{rid}/fill-missing')
    assert res.status_code==200,res.text
    assert res.json()['patched']==[{'week':1,'field':'sub_topic_description','value':'Deskripsi pengganti yang benar.'}]
    assert len(calls)==2


def test_retry_lokal_memberi_alasan_validasi_tanpa_menyalin_keluaran(monkeypatch):
    from app.core.llm_json import invoke_json

    prompts=[]
    def invoke(self,prompt,**kwargs):
        prompts.append(prompt)
        return AIMessage(content='{"nilai":99,"noise":"INSTRUKSI_DARI_MODEL"}' if len(prompts)==1 else '{"nilai":23}')
    def validate(value):
        if value['nilai']>30:
            raise ValueError('Skor melebihi maksimum rubrik 30')
    monkeypatch.setattr(ChatOllama,'invoke',invoke)
    result=invoke_json(llm._build_ollama('complex'),'Nilai',adapter=TypeAdapter(Jawaban),validate=validate)
    assert result=={'nilai':23}
    assert 'Skor melebihi maksimum rubrik 30' in prompts[1]
    assert 'INSTRUKSI_DARI_MODEL' not in prompts[1]
