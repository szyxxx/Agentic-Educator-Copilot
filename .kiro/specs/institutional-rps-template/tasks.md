# Tasks — institutional-rps-template

Sequence is top-to-bottom. Each task lists the requirement IDs it satisfies and the done criteria. Source of truth: `requirements.md` in the same folder.

## 1. Shared constants and coercion helpers

- [ ] Add `app/backend/app/core/rps_constants.py` exporting `UTS_MODULE = 8`, `UAS_MODULE = 16`, `UTS_TITLE = "Ujian Tengah Semester (UTS)"`, `UAS_TITLE = "Ujian Akhir Semester (UAS)"`, and a helper `is_exam_week(week_number: int) -> bool`.
- [ ] Add `app/backend/app/core/rps_coerce.py` with three pure helpers used by both the API and the AI agent:
  - `coerce_bahan_kajian(value: str, allowed: list[str]) -> str` (case-insensitive verbatim match, fall back to closest match within Levenshtein distance 3, else `""`).
  - `coerce_cpmk_number(value, list_len: int) -> int | None` (parse first integer from string-or-int input; clamp to `[1, list_len]`; else `None`).
  - `coerce_reference_indices(values, list_len: int) -> tuple[list[int], bool]` (drop out-of-range; return `(indices, had_invalid)` so the caller can flag `status="needs_review"`).
- Requirement IDs: 4 (constants), 6.6, 6.7, 6.8.
- Done when: smoke import passes; pure-function unit smoke (one inline call from `_csv_smoke`-style script) returns expected coercions.

## 2. RPSMeeting schema + idempotent migration

- [ ] Extend `RPSMeeting` model with `bahan_kajian_topik` (VARCHAR(255), nullable), `sub_topic_title` (VARCHAR(500), nullable), `sub_topic_description` (TEXT, nullable), `cpmk_number` (INTEGER, nullable), `reference_indices` (JSON, nullable). Keep `topic`, `cpmk`, `references` in place as legacy/fallback.
- [ ] Extend `_ensure_columns` in `app/backend/app/core/database.py` to add the five new columns to `rps_meetings` if they are missing (idempotent ALTERs).
- [ ] Add `app/backend/app/core/rps_migration.py` with `migrate_legacy_meetings(session_factory)`:
  - For each meeting, skip if any new column is already populated (idempotent).
  - For weeks 8/16: set `sub_topic_title` to UTS/UAS title, leave the rest cleared. Do not consult legacy `topic`.
  - For other weeks: split legacy `topic` on the first `:` into `(sub_topic_title, sub_topic_description)`; if no colon, title=topic, description="".
  - Parse legacy `cpmk` for the first integer in `[1, len(parent_rps.cpmk_list)]` → `cpmk_number`.
  - Match legacy `references` substring (case-insensitive) against parent RPS's `references_list`; collect 1-based indices in ascending order → `reference_indices`. Leave empty if no match.
- [ ] Call `migrate_legacy_meetings(SessionLocal)` from `init_db()` after `_ensure_columns()` and before `seed_data(...)`.
- Requirement IDs: 9 (all sub-criteria).
- Done when: running the app twice in a row leaves migrated values stable (idempotency verified by a quick `python -c` script that prints meeting counts and a sample row).

## 3. API payload, persistence, and validation

- [ ] Extend `RPSPayload` (in `app/backend/app/api/v1/rps.py`) with optional `bahan_kajian_topik`, `sub_topic_title`, `sub_topic_description`, `cpmk_number`, `reference_indices` per meeting (keep `topic`, `cpmk`, `references` accepted but mark as legacy-fallback).
- [ ] Update `_save_meetings` to write the new columns. For exam weeks, force the canonical exam values regardless of incoming payload (Req 4.5, 4.6).
- [ ] Add `_validate_meetings(payload, parent_rps)` invoked by the manual create + update endpoints:
  - Reject HTTP 400 when `bahan_kajian_topik` is non-empty and not in the parent RPS's `bahan_kajian` list. Identify offending weeks.
  - Reject when `cpmk_number` is non-null and outside `[1, len(cpmk_list)]`.
  - Reject when any entry in `reference_indices` is outside `[1, len(references_list)]`.
  - Reject when an exam-week meeting has any non-empty content in those four fields.
- Requirement IDs: 1.6, 2.6, 3.4, 4.5, 4.6.
- Done when: posting a request that violates each rule returns 400 with the offending week called out; valid posts persist the new columns.

## 4. API GET shape

- [ ] Extend `/api/dashboard/rps/{rps_id}` to surface `bahan_kajian_topik`, `sub_topic_title`, `sub_topic_description`, `cpmk_number`, `reference_indices` per meeting, plus a top-level `references_list` (already returned) used for index resolution.
- [ ] Keep `topic`, `cpmk`, `references` in the response as legacy fallback for one release; the frontend will stop consuming them in Task 11.
- Requirement IDs: 7 (display reads from these fields).

## 5. AI generation alignment

- [ ] Update `draft_rps_node` in `app/backend/app/agents/rps_agent.py`:
  - Accept the parent's `bahan_kajian`, numbered `cpmk_list`, numbered `references_list` from the state.
  - Prompt the LLM to emit objects with keys: `week`, `bahan_kajian_topik`, `sub_topic_title`, `sub_topic_description`, `cpmk_number`, `reference_indices`, `method`, `evaluation`.
  - Explicitly instruct: "`bahan_kajian_topik` MUST be drawn verbatim from the supplied list", "the same value MAY repeat across multiple weeks", "`cpmk_number` is an integer index", "`reference_indices` is a list of integer indices".
  - Emit canonical exam values for `week=8` and `week=16`.
- [ ] After invocation, run each meeting through the coercion helpers from Task 1 and flag `status="needs_review"` on any meeting that had its `cpmk_number` coerced to null or any reference index dropped.
- Requirement IDs: 6.1–6.8.

## 6. Per-week regenerate agent

- [ ] Update the prompt in `regenerate_week` (in `app/backend/app/api/v1/rps.py`) to emit the institutional schema (Req 6.9). Apply the same coercion helpers from Task 1. Continue reading and writing `learning_method` and `evaluation_method` on the targeted meeting (Req 5.8).
- Requirement IDs: 6.9, 5.8.

## 7. Compliance checks update

- [ ] Extend `compliance_checks` in `app/backend/app/core/stats.py` with six institutional checks: UTS at 8, UAS at 16, Bahan Kajian populated (non-exam), Sub-Topik populated (non-exam), CPMK assigned (non-exam), at least one reference cited (non-exam). Keep the existing method-variety and evaluation-coverage checks.
- Requirement IDs: 10.

## 8. Frontend types and Advanced disclosure

- [ ] Extend `RpsFormData` and `RpsMeeting` in `app/frontend/src/app/dashboard/rps/rps-form.tsx` with the new fields. Drop the per-meeting `topic` field from the type (keep `method`, `evaluation` for the Advanced disclosure).
- [ ] Add a small reusable `<AdvancedDisclosure>` toggling visibility of the per-meeting `method` and `evaluation` controls. Closed by default.
- Requirement IDs: 5.3, 5.4.

## 9. Numbered references editor

- [ ] Replace the existing `<PlainList items={data.references_list}>` with a `<NumberedReferencesEditor>` that:
  - Renders each entry prefixed with its 1-based number.
  - Supports add, edit, remove, drag-reorder.
  - On reorder/remove, returns both the new list AND a remap function `oldIndex -> newIndex|null`. The form uses that remap to rewrite every meeting's `reference_indices` so cited reference text stays stable. A removal triggers a confirmation dialog naming affected weeks.
- Requirement IDs: 2.7, 2.8, 8.5.

## 10. Manual edit form institutional layout

- [ ] Replace the single-input Topic block in each meeting row with:
  - Bahan Kajian/Topik: single-select sourced from `data.bahan_kajian`. Disabled when `bahan_kajian` is empty, with an inline notice.
  - Sub-Topik Title: `<input type="text">`.
  - Sub-Topik Description: `<textarea>`.
  - CPMK: single-select sourced from `data.cpmk_list` rendered as `1. <text>`. Disabled when the list is empty.
  - No. Referensi: multi-select sourced from `data.references_list` rendered as `1. <text>`.
- [ ] When `data.cpmk_list` shrinks and clears existing `cpmk_number`s, show a single confirmation dialog naming the affected weeks (Req 8.4).
- [ ] When `data.bahan_kajian` shrinks and clears existing `bahan_kajian_topik`s, show a confirmation dialog naming the affected weeks (Req 8.3).
- [ ] For weeks 8 and 16, render the row read-only with a fixed UTS/UAS label and hide the four institutional inputs.
- Requirement IDs: 1, 2.5, 3.3, 4.4, 8.1–8.5.

## 11. RPS detail page institutional table

- [ ] Update `app/frontend/src/app/dashboard/rps/[id]/page.tsx`:
  - Render the meetings table with five columns in this order: Modul, Bahan Kajian/Topik, Sub-Topik, CPMK Terkait Topik atau Sub-Topik, No. Referensi.
  - Italic Bahan Kajian; bold Sub-Topik title followed by `: <description>` when description is non-empty.
  - Em-dash for empty CPMK or empty reference indices.
  - Tooltip on the No. Referensi cell listing each cited index alongside the resolved reference text (`title="1. Foo\n3. Bar\n8. Baz"`).
  - Add a "Tampilkan kolom internal" disclosure (closed by default) that appends Metode and Evaluasi columns sourced from the meeting payload.
  - Render the parent RPS's references list as a separate numbered list `1.`, `2.`, ... above or below the meetings table (Req 7.8).
- Requirement IDs: 2.4, 7 (all sub-criteria).

## 12. Auto-material agent compatibility

- [ ] In `app/backend/app/agents/auto_material_agent.py`, replace the use of `meeting.topic` with `meeting.sub_topic_title + (": " + meeting.sub_topic_description if meeting.sub_topic_description else "")`. Add `bahan_kajian_topik` to the prompt as additional context.
- Requirement IDs: keeps Req 5 features intact.

## 13. Knowledge graph indexer compatibility

- [ ] In `app/backend/app/api/v1/knowledge.py`, swap any `meeting.topic` reads to the same combined string as Task 12. Keep `meeting.learning_method` and `meeting.evaluation_method` reads (Req 5.7).
- Requirement IDs: 5.7.

## 14. Verification gate

- [ ] Run the existing Python import smoke test (`from app.main import app`).
- [ ] Run the migration twice on the existing `backend/educopilot.db` and inspect one RPS via SQL to confirm the new columns are populated and idempotent.
- [ ] Manually exercise one round-trip flow (create RPS manually with new fields, save, edit, re-save, run AI auto-generate on a fresh RPS) and confirm:
  - Detail page shows the institutional 5-column layout.
  - Compliance checklist now includes the six new checks.
  - Auto-grading + auto-material flow still produces a Material attached to the next week.
- Requirement IDs: 9.9 (idempotency), end-to-end smoke for everything else.
