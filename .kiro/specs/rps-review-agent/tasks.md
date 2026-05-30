# Tasks — rps-review-agent

Sequence is top-to-bottom. Source of truth: `requirements.md` in the same folder.

## 1. SN-DIKTI Compliance Catalog (foundation)

- [ ] Create `app/backend/app/core/sndikti_catalog.py` declaring `SNDIKTI_Criterion` dataclass + `SNDIKTI_CATALOG: list[SNDIKTI_Criterion]` with all ~24 entries from Requirement 14.2 (SND-001 … SND-051), each with `id`, `title`, `regulation_ref`, `severity`, `weight`, `scope`, `field`, `group`, and a pure `validator(rps, meetings) -> CriterionResult`.
- [ ] Add a `CriterionResult` dataclass with `passed: bool`, `detail: str`, `suggested_value: Any | None`, `target_week: int | None`.
- [ ] Add `run_catalog(rps, meetings) -> ComplianceReport` that runs every validator and returns `score`, `total_weight`, `earned_weight`, `regulation_summary`, `criteria[]`, and `groups[]` (pre-aggregated by section).
- [ ] Smoke test: call `run_catalog` on the existing dev RPS via `python -c` and confirm the totals add up.
- Requirement IDs: 14, 15.1–15.4.
- Done when: every criterion has a pass/fail validator and `run_catalog` produces a Compliance_Report dict.

## 2. Compliance Report endpoint

- [ ] `GET /api/rps/{rps_id}/compliance` in `app/backend/app/api/v1/rps.py` that loads the RPS + meetings, calls `run_catalog`, and returns the report. Read-only, no LLM.
- [ ] In-process LRU cache keyed by `(rps_id, rps.updated_at)` with 60s TTL.
- [ ] Update `RPS.compliance_score` write-paths so the value comes from `run_catalog(...).score` instead of `_calc_compliance`. Apply this in `/generate`, `/`, and `/{rps_id}` (PUT) handlers.
- [ ] Remove `_calc_compliance` from `rps.py` after the four call sites are migrated.
- [ ] Update `dashboard.py /rps/{rps_id}` to swap `compliance_checks(...)` for `run_catalog(...)`. Drop the now-unused `compliance_checks` import.
- [ ] Remove `compliance_checks` and `_check` helpers from `app/backend/app/core/stats.py`.
- Requirement IDs: 14.5, 14.6, 15.1–15.4, 15.7, 15.8.
- Done when: hitting `/api/rps/{id}/compliance` returns a fully populated report and the existing detail page still loads (using the same data, mapped through the new shape in Task 7).

## 3. RPSFinding model and migration

- [ ] New SQLAlchemy model `RPSFinding` with the columns listed in Requirement 1.1 plus a stable `issue_hash` (sha1 of `(scope, target_week, field, category, normalized_issue_text)`) used to dedupe across review runs.
- [ ] Register the model in `app/backend/app/models/__init__.py`.
- [ ] Add `rps_findings` table to the `_ensure_columns` ad-hoc migration in `database.py` (idempotent — `CREATE TABLE IF NOT EXISTS`).
- [ ] Confirm migration runs cleanly twice via `python -c "from app.core.database import init_db; init_db(); init_db()"`.
- Requirement IDs: 1.1, 1.2.

## 4. Review agent

- [ ] New module `app/backend/app/agents/rps_review_agent.py` with:
  - `ReviewState` TypedDict (rps row dict, meetings list, findings list, messages annotated reducer).
  - `cpl_cpmk_alignment_node` — single LLM call over all meetings; emits `cpmk_alignment` + `cpl_alignment` Findings (Requirement 4).
  - `sndikti_compliance_node` — calls `run_catalog`, converts each *failed* criterion into a Finding (Requirement 3).
  - `content_quality_node` — deterministic blacklist + length checks for `sub_topic_title`/`sub_topic_description`; LLM call only for blank descriptions to draft a candidate (Requirement 5).
  - `continuity_node` — single LLM call over the whole 16-meeting sequence; emits cross-cutting `continuity` Findings with no `suggested_value` (Requirement 6).
  - `aggregate_findings_node` — merges, dedupes by `issue_hash`, sorts by severity then category.
- [ ] `build_review_graph()` wires all nodes; entry point fans out to the four issue-producing nodes in parallel where possible, joins at the aggregator.
- [ ] Severity is code-assigned per Requirement 4 (option D in open decisions).
- [ ] Hard deadline: each LLM call wrapped in a 30s timeout; aggregate hard-stop at 90s (Requirement 1.6).
- Requirement IDs: 1.3, 1.4, 1.5, 1.6, 3 (all sub-criteria), 4, 5, 6.

## 5. Review API + persistence

- [ ] `POST /api/rps/{rps_id}/review` in `rps.py`:
  - Load RPS + meetings.
  - Enforce 30s cooldown + concurrency lock (in-process dict guarded by a `threading.Lock`). Return 429 / 409 per Requirement 12.
  - Run review agent; receive Findings list.
  - Upsert by `issue_hash`: matching dismissed Findings get `last_seen_at` updated only; non-matching go in as fresh active rows; prior active Findings whose hash didn't reappear get pruned.
  - Return active Findings grouped by category, plus `last_reviewed_at` and `summary_counts`.
- [ ] `GET /api/rps/{rps_id}/findings?include_dismissed=false` for the FindingsPanel to read independently of triggering a new review.
- Requirement IDs: 1, 2, 9.4, 12, 13.
- Done when: clicking "Jalankan Review" twice in 30s returns 429; concurrent calls return 409.

## 6. Apply / Dismiss / Reopen / Fill-Missing endpoints

- [ ] `POST /api/rps/{rps_id}/findings/{finding_id}/apply` — load Finding, ensure non-dismissed and `applied=false`, write `suggested_value` to the targeted field via existing `_save_meetings` field-level helpers (or a small `_patch_meeting_field` extracted from there). Run `_validate_meetings` on the affected meeting set; rollback on failure.
- [ ] `POST /api/rps/{rps_id}/findings/{finding_id}/dismiss` and `/reopen` — flip the boolean.
- [ ] `POST /api/rps/{rps_id}/fill-missing` — load RPS + meetings, build a "blanks map" listing which fields per meeting are empty, ask the LLM to fill ONLY those fields (one batched call), run coercers, write back ONLY for fields that were blank at start. Skip exam weeks. Return `{ status, patched: [...] }`.
- Requirement IDs: 8, 9.1–9.3, 10, 13.

## 7. Frontend — ComplianceReport card

- [ ] New `frontend/src/app/dashboard/rps/[id]/ComplianceReport.tsx` (client component since it has the "show all criteria" toggle and section accordions).
- [ ] Replace the existing "Compliance Checklist" card on `[id]/page.tsx` with `<ComplianceReport rpsId={...} />`. The component fetches `/api/rps/{id}/compliance` on mount.
- [ ] Render: big score, `earned/total` weight fine print, regulation_summary tooltip, segmented progress bar by group, collapsible accordion per section, criterion rows with pass/fail icon + title + regulation_ref chip + weight chip + detail. Default hide passed criteria; toggle reveals them.
- [ ] Failed `per_week` criteria render their Modul number as a clickable anchor to the corresponding row in MeetingsTable.
- Requirement IDs: 15.5, 15.6, 15.7.

## 8. Frontend — FindingsPanel + Apply/Dismiss

- [ ] New `frontend/src/app/dashboard/rps/[id]/FindingsPanel.tsx`:
  - Fetches `/api/rps/{id}/findings` on mount.
  - Shows hero CTA "Jalankan review otomatis" when no run has happened.
  - `Jalankan Review` button calls `/api/rps/{id}/review`. Shows progress while running.
  - Groups Findings by category in fixed order; severity chips header.
  - Per row: severity badge, target label (`Modul N` or `RPS`), field chip, issue text, optional `suggested_fix` block, "Terapkan Saran" button (when `suggested_value != null`), "Tutup" button.
  - "Tampilkan yang sudah ditutup" toggle re-fetches with `include_dismissed=true`; muted style + "Buka Kembali" button.
  - Empty state: "✓ Tidak ada temuan saat ini." with re-run button.
- [ ] Mount above MeetingsTable on `[id]/page.tsx`.
- Requirement IDs: 7.

## 9. Frontend — copy and demotion

- [ ] Rename `OverallFeedback` heading to "Catatan Dosen" and update its description copy per Requirement 11.1.
- [ ] Move `WeekFeedback` per-row textarea inside the "Tampilkan kolom internal" disclosure in `MeetingsTable.tsx` (not visible by default).
- [ ] Update RPS detail page hero buttons / labels so dosen sees three distinct actions: "✨ Regenerasi RPS" (existing, destructive), "🪄 Isi yang Kosong" (new, fill-missing), "🔍 Jalankan Review" (lives inside FindingsPanel). Add tiny inline tooltips on each.
- Requirement IDs: 11.

## 10. Frontend — Fill Missing CTA

- [ ] On the RPS detail page hero, add the "🪄 Isi yang Kosong" button that calls `POST /api/rps/{id}/fill-missing` and refreshes the page on success. Disable when RPS status is `validated`.
- Requirement IDs: 10.

## 11. Verification gate

- [ ] Backend imports clean (`python -c "from app.main import app"`).
- [ ] DB migration runs twice without errors.
- [ ] Hit `/api/rps/{id}/compliance` against the existing dev RPS — confirm the score is no longer the heuristic 100% and that the breakdown lists every catalog entry.
- [ ] Run `/api/rps/{id}/review` once — confirm Findings persist; run again within 30s — confirm 429.
- [ ] Apply one Finding via `POST .../apply` — confirm only the targeted field changed and the Finding is `applied=true`.
- [ ] Dismiss one Finding, re-run review — confirm the dismissed Finding stays dismissed and is not re-raised.
- [ ] `POST /fill-missing` on a half-empty RPS — confirm only blanks were touched.
- [ ] Frontend `getDiagnostics` clean across the four new files.
