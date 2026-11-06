"""Output contracts used to constrain Ollama's JSON grammar and validation."""
from typing import Annotated, Literal

from pydantic import BaseModel, Field, TypeAdapter

Text = Annotated[str, Field(min_length=1)]
Week = Annotated[int, Field(ge=1, le=16)]
Positive = Annotated[int, Field(ge=1)]


class Outcomes(BaseModel):
    cpl: list[Text]
    cpmk: list[Text]


class Meeting(BaseModel):
    week: Week
    bahan_kajian_topik: str
    sub_topic_title: Text
    sub_topic_description: str
    cpmk_number: Positive | None
    reference_indices: list[Positive]
    method: str
    evaluation: str


class Options(BaseModel):
    A: Text
    B: Text
    C: Text
    D: Text


class MCQ(BaseModel):
    id: Text
    type: Literal["multiple_choice"] = "multiple_choice"
    question: Text
    options: Options
    correct_answer: Literal["A", "B", "C", "D"]
    explanation: str = ""
    bloom_level: str = "understand"
    weight: Annotated[float, Field(gt=0)] = 10


class Essay(BaseModel):
    id: Text
    type: Literal["essay"] = "essay"
    question: Text
    rubric: Annotated[dict[str, str], Field(min_length=1)]
    bloom_level: str = "analyze"
    max_score: Annotated[float, Field(gt=0)] = 30


class EssayScore(BaseModel):
    id: Text
    score: Annotated[float, Field(ge=0, allow_inf_nan=False)]
    feedback: Text


class Description(BaseModel):
    week: Week
    description: Text


class Mismatch(BaseModel):
    week: Week
    current: Positive
    suggested: Positive
    reason: Text


class Alignment(BaseModel):
    mismatches: list[Mismatch]
    orphan_cpl_indices: list[Positive]


class Transition(BaseModel):
    from_week: Week
    to_week: Week
    severity: Literal["warning", "info"]
    issue: Text
    suggested_fix: str


class Fills(BaseModel):
    bahan_kajian_topik: str | None = None
    sub_topic_title: str | None = None
    sub_topic_description: str | None = None
    cpmk_number: Positive | None = None
    reference_indices: list[Positive] | None = None
    learning_method: str | None = None
    evaluation_method: str | None = None


class MeetingPatch(BaseModel):
    week: Week
    fills: Fills


def array_adapter(item, *, count: int | None = None) -> TypeAdapter:
    return TypeAdapter(Annotated[list[item], Field(min_length=count, max_length=count)])


STRINGS = TypeAdapter(Annotated[list[Text], Field(min_length=1)])
OUTCOMES = TypeAdapter(Outcomes)
MEETING = TypeAdapter(Meeting)
SCHEDULE = array_adapter(Meeting, count=16)
SCORES = array_adapter(EssayScore)
DESCRIPTIONS = array_adapter(Description)
ALIGNMENT = TypeAdapter(Alignment)
TRANSITIONS = array_adapter(Transition)
PATCHES = array_adapter(MeetingPatch)


def validate_meeting_mapping(item: dict, *, bahan_kajian: list[str], cpmk_count: int, reference_count: int) -> None:
    """Validate local output against the RPS catalog before coercion can erase it."""
    if item["week"] in (8, 16):
        from app.core.rps_constants import UTS_TITLE, UAS_TITLE
        if item["bahan_kajian_topik"] or item["cpmk_number"] is not None or item["reference_indices"]:
            raise ValueError("Pemetaan modul ujian harus kosong")
        if item["sub_topic_title"] != (UTS_TITLE if item["week"] == 8 else UAS_TITLE):
            raise ValueError("Judul modul ujian tidak sesuai")
        return
    if item["bahan_kajian_topik"] not in bahan_kajian:
        raise ValueError("Bahan kajian tidak ada dalam katalog RPS")
    if not item["cpmk_number"] or item["cpmk_number"] > cpmk_count:
        raise ValueError("CPMK tidak ada dalam katalog RPS")
    if not item["reference_indices"] or any(i > reference_count for i in item["reference_indices"]):
        raise ValueError("Referensi tidak ada dalam katalog RPS")
    if any(not item[key].strip() for key in ("sub_topic_description", "method", "evaluation")):
        raise ValueError("Deskripsi/metode/evaluasi pertemuan kosong")
