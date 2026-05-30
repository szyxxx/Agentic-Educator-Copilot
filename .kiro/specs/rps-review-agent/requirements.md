# Requirements Document — rps-review-agent

## Introduction

When the dosen authors an RPS manually (or after AI generation), there is no agent that *reviews* the draft for quality and offers targeted, actionable feedback. Existing capabilities each fall short:

- `_validate_meetings` only catches schema violations (out-of-range CPMK number, exam-week content leak).
- `compliance_checks` returns a static SN-DIKTI checklist with pass/fail and a one-liner hint.
- `OverallFeedback` and `WeekFeedback` are free-text input boxes for the dosen, not output from any agent.
- `regenerate_rps` and `regenerate_week` both **overwrite** content; there is no way to keep what the dosen has already written and only patch the weak spots.

This feature introduces a dedicated review agent that produces structured findings against four lenses (CPL/CPMK alignment, SN-DIKTI compliance, content quality per week, week-to-week continuity), surfaces them in a non-destructive UI panel, and offers granular "Apply suggestion" actions plus a "Fill missing fields only" action that the dosen can use when running short on time.

Existing free-text feedback boxes are kept (so dosen notes don't get lost), but the primary review surface becomes the findings panel.

## Glossary

- **RPS**: The course-level lesson plan stored in the `rps` table.
- **RPS_Meeting**: One of the 16 weekly rows belonging to an RPS, identified by `(rps_id, week_number)`.
- **Review_Agent**: The new LangGraph pipeline at `app/backend/app/agents/rps_review_agent.py` that consumes an RPS + its meetings and returns a list of Findings.
- **Review_Run**: One invocation of the Review_Agent. Recorded in the database for audit and so the UI can show "last reviewed at".
- **Finding**: A structured record that flags one issue with the RPS draft. Fields: `id`, `severity`, `scope`, `target` (week_number or "rps"), `field`, `issue`, `suggested_fix`, `suggested_value`, `category`, `dismissed`, `applied`, `created_at`.
- **Severity**: One of `info`, `warning`, `critical`. Critical = the SN-DIKTI checklist would fail; Warning = quality concern (vague topic, weak alignment); Info = continuity nudge.
- **Scope**: One of `per_week` (target is a specific RPS_Meeting) or `cross_cutting` (target is the RPS as a whole).
- **Category**: One of `cpl_alignment`, `cpmk_alignment`, `sndikti_compliance`, `content_quality`, `continuity`. Drives the icon and grouping in the UI.
- **Apply_Action**: User action that takes one Finding's `suggested_value` and writes it to the targeted `(rps_id, field)` or `(rps_id, week_number, field)`.
- **Fill_Missing_Action**: A new agent run that only writes content into RPS_Meeting fields that are currently empty (`bahan_kajian_topik`, `sub_topic_title`, `sub_topic_description`, `cpmk_number`, `reference_indices`). It does NOT touch fields the dosen has already filled. Implemented as a new endpoint, distinct from `regenerate_rps` and `regenerate_week`.
- **Continuity_Pass**: A node in the Review_Agent graph that examines all 16 meetings as one ordered sequence and emits Findings about progression, abrupt jumps, or topic gaps.
- **Findings_Panel**: The new UI section on the RPS detail page that lists current Findings, supports Apply / Dismiss / Re-run, and groups them by category.
- **SN_DIKTI_Criterion**: One auditable rule against a Permendikbudristek 53/2023 component. Fields: `id` (e.g. `SND-001`), `title`, `regulation_ref` (pasal / article number cited), `severity` (`critical | warning | info`), `weight` (positive int, points contributed when the criterion passes), `validator` (a deterministic Python predicate that returns `(passed: bool, detail: str)`).
- **Compliance_Catalog**: The fixed registry of SN_DIKTI_Criterion entries, declared once in `app/backend/app/core/sndikti_catalog.py`. The score and the SN-DIKTI Findings group are both derived from it.
- **Compliance_Report**: The deterministic output of running every SN_DIKTI_Criterion validator against an RPS. Shape: `{ score: int, total_weight: int, earned_weight: int, criteria: [{ id, title, regulation_ref, severity, weight, passed, detail, contributed_weight }] }`. `score = round(earned_weight / total_weight * 100)`. Earned weight equals the sum of `weight` values for passed criteria, so 100% is only achievable when every catalog entry passes.

## Rules of Inference

1. The Review_Agent SHALL be read-only relative to the `rps` and `rps_meetings` tables. Any mutation happens through Apply_Action, Fill_Missing_Action, or the existing manual edit form — never as a side effect of running the review.
2. Each Review_Run replaces the *active* set of Findings for an RPS. Dismissed Findings from prior runs are preserved (not deleted) so the dosen does not see the same dismissed issue come back next run if the underlying state hasn't changed.
3. A Finding is uniquely identified by the tuple `(rps_id, scope, target, field, category, normalized_issue_hash)`. If the same issue is re-raised on a subsequent run, the existing row is updated (last_seen_at) rather than duplicated.
4. Severity SHALL be assigned by code based on the rule that triggered the Finding, not by the LLM. The LLM produces issue text and suggested_fix; the agent assigns severity deterministically.
5. The Review_Agent SHALL NOT introduce a new free-text feedback channel. The dosen's existing `WeekFeedback` and `OverallFeedback` notes remain orthogonal and are not consumed by the review prompt unless explicitly opted in (see Requirement 9).
6. Apply_Action SHALL only mutate the single field referenced by the Finding. It SHALL NOT regenerate or overwrite adjacent fields.
7. Fill_Missing_Action SHALL only write to RPS_Meeting fields whose current value is empty (string `""`, `None`, or empty list). It SHALL NOT touch any field the dosen has filled, regardless of perceived quality.

## Requirements

### Requirement 1: Review Agent and Findings Model

**User Story:** As a dosen, I want to ask an agent to review my RPS draft and tell me what's weak, so I can decide what to fix without the agent overwriting my work.

#### Acceptance Criteria

1. THE System SHALL define a new SQLAlchemy model `RPSFinding` with columns:
   `id` (string PK), `rps_id` (string FK), `severity` (string, one of `info|warning|critical`), `scope` (string, one of `per_week|cross_cutting`), `target_week` (integer nullable, only set when `scope=per_week`), `field` (string, the RPS_Meeting / RPS field name the finding refers to, e.g. `sub_topic_title`, `cpmk_number`, `reference_indices`, `bahan_kajian_topik`, `cpl_list`, `cpmk_list`), `category` (string, one of `cpl_alignment|cpmk_alignment|sndikti_compliance|content_quality|continuity`), `issue` (text), `suggested_fix` (text), `suggested_value` (JSON), `dismissed` (boolean default false), `applied` (boolean default false), `created_at`, `last_seen_at`.
2. THE System SHALL register `RPSFinding` in the SQLite ad-hoc migration so existing databases pick up the new table on next startup, idempotently.
3. THE System SHALL define a new module `app/backend/app/agents/rps_review_agent.py` with a `build_review_graph()` LangGraph pipeline whose entry point accepts the RPS row plus its 16 meetings and returns a list of Finding dicts.
4. THE Review_Agent SHALL have at minimum these nodes: `cpl_cpmk_alignment_node`, `sndikti_compliance_node`, `content_quality_node`, `continuity_node`, `aggregate_findings_node`. Each issue-producing node returns a list of Finding dicts; the aggregator merges and de-duplicates them.
5. THE Review_Agent SHALL be read-only — it SHALL NOT call any session method that mutates `rps`, `rps_meetings`, or `materials`.
6. THE Review_Agent SHALL complete in ≤ 90 seconds for an RPS with 16 meetings on the configured LLM provider; if it exceeds that timeout, the orchestrator SHALL cancel any pending node and return whatever Findings were already produced.

### Requirement 2: Review Endpoint

**User Story:** As a dosen, I want a single button on the RPS detail page that runs the review and produces a list of Findings I can act on.

#### Acceptance Criteria

1. THE System SHALL expose `POST /api/rps/{rps_id}/review` that runs the Review_Agent against the supplied RPS.
2. WHEN the endpoint is called, THE System SHALL:
   1. Load the RPS and its meetings.
   2. Invoke the Review_Agent.
   3. Persist the returned Findings — replacing prior non-dismissed Findings for the same RPS, preserving dismissed ones.
   4. Update each Finding's `last_seen_at` so the UI can sort by freshness.
   5. Return the full active set of Findings for the RPS, grouped by category.
3. THE endpoint SHALL accept an optional JSON body `{ "include_dismissed": false }`. WHEN `include_dismissed=true`, the response SHALL also include previously dismissed Findings (so the dosen can audit them).
4. IF the RPS does not exist, THE endpoint SHALL return HTTP 404 with `RPS not found`.
5. IF the LLM provider is unavailable, THE endpoint SHALL return HTTP 503 with the underlying error message and SHALL NOT persist any partial Findings.
6. THE response payload SHALL include `last_reviewed_at` (timestamp of this run) and `summary_counts` (counts per severity + per category) for quick rendering.

### Requirement 3: SN-DIKTI Compliance Findings

**User Story:** As a dosen, I want the review to call out concrete SN-DIKTI gaps in my RPS so I know exactly what to fix to meet institutional standards.

#### Acceptance Criteria

1. THE `sndikti_compliance_node` SHALL run every validator in the Compliance_Catalog (Requirement 14) against the RPS and emit one Finding per failed criterion.
2. EACH emitted Finding SHALL set `severity = criterion.severity`, `category = sndikti_compliance`, `field = criterion.field` (a static value declared on the catalog entry, e.g. `cpmk_list`, `meetings.evaluation_method`, `meetings.references`), `issue = criterion.title + ": " + criterion.detail` (the validator's `detail` string), and `regulation_ref = criterion.regulation_ref` so the UI can link to the cited article.
3. WHERE a criterion is `scope=per_week`, the Finding's `target_week` SHALL be the affected week number; for cross-cutting criteria the Finding SHALL be `scope=cross_cutting` with `target_week=null`.
4. WHERE a criterion's validator returns a `suggested_value` (e.g. the canonical UTS title for an exam-week criterion), the Finding SHALL include it so Apply_Action works.
5. THE node SHALL NOT issue a Finding for criteria that pass; passed criteria are surfaced only inside the Compliance_Report (Requirement 15), not as alerts.

### Requirement 4: CPL / CPMK Alignment Findings

**User Story:** As a dosen, I want the review to tell me when a meeting's CPMK number is plausibly mismatched with its sub-topic, so I can fix the alignment.

#### Acceptance Criteria

1. THE `cpl_cpmk_alignment_node` SHALL ask the LLM to evaluate, for each non-exam meeting that has both a `sub_topic_title` and a `cpmk_number`, whether the chosen CPMK is the most appropriate among the available CPMKs.
2. WHEN the LLM proposes a different CPMK, the node SHALL emit a Finding with `severity=warning`, `category=cpmk_alignment`, `scope=per_week`, `target_week=<n>`, `field=cpmk_number`, and `suggested_value=<the proposed integer>`.
3. THE node SHALL also emit a Finding with `severity=info` and `category=cpl_alignment` when one or more CPLs are not covered by ANY CPMK across the 16 meetings (i.e. the CPL is orphaned).
4. THE node SHALL pass the FULL CPMK list and FULL list of meetings as context in a single LLM call, so the model can reason about coverage without per-meeting context loss.

### Requirement 5: Content Quality Findings

**User Story:** As a dosen, I want the review to flag vague or low-quality `sub_topic_title` and `sub_topic_description` so I can sharpen them before publishing.

#### Acceptance Criteria

1. THE `content_quality_node` SHALL emit a Finding with `severity=warning`, `category=content_quality`, `scope=per_week`, `field=sub_topic_title` for each non-exam meeting whose title is blank, fewer than 4 words, or matches a deterministic blacklist of placeholder phrases (e.g. "Topik Belum Ditetapkan", "TBD", "Materi Minggu", "Lihat Slide").
2. THE node SHALL also emit a Finding with `severity=info`, `category=content_quality`, `field=sub_topic_description` for each non-exam meeting whose description is blank or fewer than 10 words.
3. WHEN the description fails the length test, the node SHALL ask the LLM to draft a one-paragraph candidate description aligned to the meeting's `sub_topic_title`, `bahan_kajian_topik`, and `cpmk_number`, and SHALL include that candidate as `suggested_value`.
4. THE node SHALL skip exam weeks (8 and 16) entirely — exam-week content is locked by the institutional template.

### Requirement 6: Week-to-Week Continuity Findings

**User Story:** As a dosen, I want the review to spot when consecutive weeks don't logically progress (an abrupt jump from W3 "intro" to W4 "advanced agentic AI" with no scaffold) so I can rearrange or insert connective topics.

#### Acceptance Criteria

1. THE `continuity_node` SHALL pass the ordered sequence of `(week, sub_topic_title, sub_topic_description, bahan_kajian_topik, cpmk_number)` for all 16 meetings (including exam weeks) to the LLM in a single call.
2. THE LLM SHALL return a JSON array of zero or more "transition concerns" with structure `{from_week, to_week, severity, issue, suggested_fix}`.
3. FOR each returned transition concern, the node SHALL emit a Finding with `severity` mapped from the LLM's value (clamped to `warning` or `info` — `critical` is reserved for SN-DIKTI), `category=continuity`, `scope=cross_cutting`, `target_week=null`, `field=null`, and `issue` containing the from→to context (e.g. "W3 → W4: Lompatan dari pengantar AI ke implementasi LLM tanpa scaffolding teknis").
4. WHERE the LLM proposes a corrective bridging topic, the node SHALL include the proposal in `suggested_fix` as readable prose; `suggested_value` SHALL be left null because the bridge is not a single-field patch.

### Requirement 7: Findings Panel UI

**User Story:** As a dosen, I want a dedicated panel on the RPS detail page that lists every Finding with one-click "Terapkan Saran" and "Tutup" actions, grouped by category, so I can triage quickly.

#### Acceptance Criteria

1. THE RPS_Detail_Page SHALL render a new `FindingsPanel` component above the meetings table.
2. THE FindingsPanel SHALL show a header with: total Finding count, count per severity (rendered as colored chips), `last_reviewed_at` timestamp, and a "Jalankan Review" button (primary CTA when no Findings exist; secondary when Findings exist).
3. THE FindingsPanel SHALL group active Findings by `category` in this fixed order: `sndikti_compliance`, `cpmk_alignment`, `cpl_alignment`, `content_quality`, `continuity`. Each group SHALL be collapsible.
4. EACH Finding row SHALL render: severity badge, `target` label (e.g. "Modul 5" or "RPS"), `field` chip, `issue` text, and (if present) `suggested_fix` text in a muted block.
5. WHERE a Finding's `suggested_value` is non-null and the Finding is `scope=per_week`, the row SHALL show a "✓ Terapkan Saran" button.
6. WHERE a Finding has no actionable `suggested_value` (e.g. continuity Findings whose fix needs the dosen's judgement), the row SHALL show only a "Tutup" button and a one-line reminder that the fix must be applied manually.
7. EVERY Finding row SHALL show a secondary "Tutup" button that marks the Finding as dismissed.
8. THE Panel SHALL show a "Tampilkan yang sudah ditutup" toggle that re-renders dismissed Findings in a muted style. Dismissed Findings SHALL show a "Buka Kembali" button.
9. WHEN there are no active Findings AND a review has been run, THE Panel SHALL show a positive empty state: "✓ Tidak ada temuan saat ini. RPS dianggap memadai." with a small re-run button.
10. WHEN no review has ever been run for this RPS, THE Panel SHALL show a hero CTA "Jalankan review otomatis untuk RPS ini" centered in the panel.

### Requirement 8: Apply Suggestion Endpoint

**User Story:** As a dosen, when I click "Terapkan Saran" on a Finding, I expect that exact field on that exact week (or RPS) to update without touching anything else.

#### Acceptance Criteria

1. THE System SHALL expose `POST /api/rps/{rps_id}/findings/{finding_id}/apply`.
2. WHEN called on a Finding with `scope=per_week`, the endpoint SHALL load the corresponding RPS_Meeting and write `suggested_value` into the column named by `field`. It SHALL NOT touch any other column on that meeting.
3. WHEN called on a Finding with `scope=cross_cutting` and a non-null `suggested_value`, the endpoint SHALL write to the RPS-level field named by `field` (e.g. `cpl_list`, `cpmk_list`).
4. THE endpoint SHALL run `_validate_meetings` for the affected meeting(s) after the write; if the patch would produce an invalid state (out-of-range CPMK, etc.), the endpoint SHALL return HTTP 400 with the validation message and SHALL roll the write back.
5. ON success, the endpoint SHALL set the Finding's `applied=true` and return the updated meeting/RPS row plus the Finding state.
6. IF the Finding's `suggested_value` is null (e.g. continuity Findings), the endpoint SHALL return HTTP 400 with `Saran ini tidak punya nilai siap-pakai; silakan terapkan manual.`.

### Requirement 9: Dismiss / Reopen Endpoints

**User Story:** As a dosen, I want to dismiss Findings I disagree with and have them stay dismissed when I re-run the review, but I also want the option to reopen them later.

#### Acceptance Criteria

1. THE System SHALL expose `POST /api/rps/{rps_id}/findings/{finding_id}/dismiss` that sets `dismissed=true`.
2. THE System SHALL expose `POST /api/rps/{rps_id}/findings/{finding_id}/reopen` that sets `dismissed=false`.
3. WHEN a Review_Run produces a Finding whose tuple `(rps_id, scope, target_week, field, category, normalized_issue_hash)` matches an existing dismissed Finding, the new run SHALL update `last_seen_at` on the existing row and SHALL NOT raise it as a fresh active Finding.
4. THE list endpoint at `GET /api/rps/{rps_id}/findings` SHALL by default return only `dismissed=false` Findings. WHEN called with `?include_dismissed=true`, it SHALL return both.

### Requirement 10: Fill Missing Fields Endpoint

**User Story:** As a dosen short on time, I want to fill in only the empty fields of my RPS with AI suggestions, without disturbing anything I've already written.

#### Acceptance Criteria

1. THE System SHALL expose `POST /api/rps/{rps_id}/fill-missing` that runs a focused agent pass over the supplied RPS.
2. THE endpoint SHALL identify, per RPS_Meeting, which of these fields are blank: `bahan_kajian_topik`, `sub_topic_title`, `sub_topic_description`, `cpmk_number`, `reference_indices`, `learning_method`, `evaluation_method`.
3. THE endpoint SHALL invoke an LLM call seeded with the FULL state of the RPS (including non-empty fields and lists like `bahan_kajian`, `cpmk_list`, `references_list`) and request fills for ONLY the blank fields.
4. THE endpoint SHALL run the same coercion helpers (`coerce_bahan_kajian`, `coerce_cpmk_number`, `coerce_reference_indices`) as the existing `draft_rps_node` so out-of-range values are normalized.
5. THE endpoint SHALL write back ONLY into fields that were blank at the start of the call. WHERE the LLM proposes a value for a field that was already filled, that proposal SHALL be discarded.
6. THE endpoint SHALL skip exam weeks (8 and 16) entirely.
7. ON success, the endpoint SHALL return `{ status: "success", patched: [{week, field, value}, ...] }` for the dosen to verify in the UI without a full reload.

### Requirement 11: Migration of Existing UI Surfaces

**User Story:** As a dosen, I don't want two parallel UIs trying to do the same thing on the RPS detail page.

#### Acceptance Criteria

1. THE existing `OverallFeedback` component SHALL remain on the RPS detail page but be relabeled "Catatan Dosen" and clarified as "free-form notes for yourself or the AI to consider in the next regeneration." It SHALL NOT be repurposed as a review output.
2. THE existing `WeekFeedback` per-row textarea in `MeetingsTable` SHALL be moved out of the institutional 5-column view and shown only inside the "Tampilkan kolom internal" disclosure. It keeps the same purpose (notes for AI regenerate) and the same endpoint.
3. THE existing `Compliance Checklist` card on the RPS detail page (driven by `compliance_checks`) SHALL be removed and replaced by the Compliance_Report card defined in Requirement 15. The replacement is a strict superset — every check the dosen sees today is preserved as a Compliance_Catalog entry plus more (Requirement 14).
4. The existing `regenerate_rps` and `regenerate_week` endpoints SHALL remain unchanged. The new `fill-missing` endpoint is an addition, not a replacement. UI copy SHALL be updated so the dosen understands the difference: "Regenerasi RPS = tulis ulang semua", "Fill Missing = isi yang kosong saja", "Review = analisis tanpa mengubah".

### Requirement 12: Cost & Concurrency Guards

**User Story:** As a dosen, I don't want to accidentally burn through LLM credits by spamming the review button.

#### Acceptance Criteria

1. THE `POST /api/rps/{rps_id}/review` endpoint SHALL refuse to run more than once every 30 seconds per RPS. WHEN called within the cooldown, it SHALL return HTTP 429 with the seconds remaining.
2. THE cooldown SHALL be tracked in-process using a simple dict keyed by `rps_id`; restarting the server resets it. (No need for a persistent cooldown for this iteration.)
3. WHILE a Review_Run is in progress for a given RPS, a concurrent `POST /api/rps/{rps_id}/review` for the same RPS SHALL return HTTP 409 with `Review sudah berjalan untuk RPS ini.`.

### Requirement 13: Telemetry & Audit

**User Story:** As an admin, I want to see how often the review agent runs and which Findings get applied vs dismissed, so I can tell whether the feature is useful.

#### Acceptance Criteria

1. THE System SHALL log each `POST /api/rps/{rps_id}/review` call with `rps_id`, `duration_ms`, `provider` (from `app.core.llm`), `findings_count_per_severity`. Logs SHALL go to stdout via `logging` (no new dependency).
2. THE System SHALL log Apply / Dismiss / Reopen actions with `rps_id`, `finding_id`, `category`, `severity`, `was_applied`, `was_dismissed`.
3. NO PII or LLM raw output SHALL appear in logs at default log level; raw LLM responses SHALL only appear at `DEBUG` for development.

### Requirement 14: SN-DIKTI Compliance Catalog

**User Story:** As a dosen, I want compliance scoring to be driven by a documented catalog of SN-DIKTI criteria — not a hand-rolled heuristic — so the score is auditable, defensible, and aligned with Permendikbudristek No. 53 Tahun 2023.

#### Acceptance Criteria

1. THE System SHALL define `app/backend/app/core/sndikti_catalog.py` exporting `SNDIKTI_CATALOG: list[SNDIKTI_Criterion]`. Each entry SHALL declare: `id` (string slug `SND-XXX`), `title` (display string), `regulation_ref` (e.g. `"Permendikbudristek 53/2023, Pasal 12 ayat (1) huruf c"`), `severity` (`critical|warning|info`), `weight` (positive int — points contributed when passed), `scope` (`rps_level|per_week`), `field` (the data column the criterion is about, e.g. `cpmk_list`, `meetings.bahan_kajian_topik`), and `validator(rps, meetings) -> CriterionResult`.
2. THE catalog SHALL cover at minimum these criteria, derived from Permendikbudristek 53/2023 Pasal 12 (RPS components) and the institutional template:

   **Identitas mata kuliah (rps_level, severity=critical, weight=4 each)**
   - `SND-001` Nama mata kuliah terisi.
   - `SND-002` Kode mata kuliah terisi.
   - `SND-003` SKS terisi (1–6).
   - `SND-004` Semester terisi (1–14).
   - `SND-005` Program studi terisi.

   **Capaian Pembelajaran (rps_level, severity=critical, weight=6 each)**
   - `SND-010` Minimal satu CPL.
   - `SND-011` Minimal tiga CPMK.
   - `SND-012` Setiap CPMK dipakai oleh minimal satu meeting (no orphan CPMK).
   - `SND-013` Setiap CPL ditutupi oleh minimal satu CPMK (no orphan CPL).

   **Bahan Kajian (rps_level, severity=warning, weight=3 each)**
   - `SND-020` Minimal tiga Bahan Kajian terdaftar.
   - `SND-021` Setiap Bahan Kajian dipakai minimal sekali.

   **Pertemuan (per_week, severity=critical/warning, weight varies)**
   - `SND-030` 16 pertemuan terdefinisi (rps_level, critical, weight=10).
   - `SND-031` Modul 8 = UTS (per_week, critical, weight=4).
   - `SND-032` Modul 16 = UAS (per_week, critical, weight=4).
   - `SND-033` Setiap pertemuan non-ujian punya `bahan_kajian_topik` valid (per_week, warning, weight=2 each).
   - `SND-034` Setiap pertemuan non-ujian punya `sub_topic_title` non-kosong (per_week, warning, weight=2 each).
   - `SND-035` Setiap pertemuan non-ujian punya `cpmk_number` valid (per_week, warning, weight=2 each).
   - `SND-036` Setiap pertemuan non-ujian punya minimal satu `reference_indices` (per_week, warning, weight=2 each).
   - `SND-037` Setiap pertemuan non-ujian punya `learning_method` non-kosong (per_week, warning, weight=2 each).
   - `SND-038` Setiap pertemuan non-ujian punya `evaluation_method` non-kosong (per_week, warning, weight=2 each).

   **Variasi metode & evaluasi (rps_level, severity=warning, weight=4 each)**
   - `SND-040` Minimal tiga `learning_method` unik di seluruh pertemuan.
   - `SND-041` Minimal dua `evaluation_method` unik di seluruh pertemuan.

   **Referensi (rps_level, severity=warning, weight=3 each)**
   - `SND-050` Minimal lima referensi terdaftar.
   - `SND-051` Modalitas pembelajaran terpilih (Tatap Muka / Daring Sinkron / Daring Asinkron / Hybrid).

3. EACH validator SHALL be a pure function returning `CriterionResult { passed: bool, detail: str, suggested_value: Any | None, target_week: int | None }`. Validators SHALL NOT mutate the database.
4. THE catalog SHALL be the single source of truth — both the Compliance_Report (Requirement 15) and the SN-DIKTI Findings group (Requirement 3) SHALL be derived from it. NO criterion SHALL exist in code outside the catalog.
5. THE old `_calc_compliance` heuristic in `app/backend/app/api/v1/rps.py` SHALL be removed; `RPS.compliance_score` SHALL be computed by running the catalog and storing `Compliance_Report.score`.
6. THE old `compliance_checks` function in `app/backend/app/core/stats.py` SHALL be removed in favor of running the catalog. The function's only caller (`/api/dashboard/rps/{id}` in `dashboard.py`) SHALL switch to the catalog.

### Requirement 15: Compliance Report Endpoint and UI

**User Story:** As a dosen, when I see "Compliance 100%", I want to know exactly which criteria were checked, which passed, and how each contributed to the score — no black-box numbers.

#### Acceptance Criteria

1. THE System SHALL expose `GET /api/rps/{rps_id}/compliance` that runs every catalog validator deterministically and returns a Compliance_Report. This endpoint SHALL NOT call any LLM and SHALL respond in under 200 ms for a fully populated RPS.
2. THE Compliance_Report response SHALL include:
   - `score: int` (0..100, rounded).
   - `total_weight: int`.
   - `earned_weight: int`.
   - `regulation_summary: str` listing the regulations the catalog cites (e.g. `"Permendikbudristek 53/2023 Pasal 12; SN-Dikti"`).
   - `criteria: [{ id, title, regulation_ref, severity, scope, weight, contributed_weight, passed, detail, target_week, suggested_value }]`.
   - `groups: [{ group: str, passed: int, total: int, earned: int, total_weight: int }]` — pre-aggregated by section header so the UI can render without computing.
3. THE Compliance_Report response SHALL be cacheable per `(rps_id, rps.updated_at)` for 60 seconds in-process, since validators are pure and inexpensive.
4. THE existing `compliance_score` column on the `RPS` model SHALL continue to be written, but its value SHALL come from the Compliance_Report endpoint logic. No code path SHALL set this column to anything other than the catalog-derived score.
5. THE RPS_Detail_Page SHALL replace the current "Compliance Checklist" card with a new `ComplianceReport` card containing:
   - A header showing `score%` (large), `earned_weight / total_weight` (fine print), and the regulation_summary as a tooltip.
   - A breakdown bar segmented by criterion group (one segment per group, segment width proportional to `total_weight`, fill proportional to `earned_weight / total_weight`).
   - A collapsible accordion grouped by section (Identitas, Capaian Pembelajaran, Bahan Kajian, Pertemuan, Metode & Evaluasi, Referensi). Each section header shows `passed/total` and the section's earned weight.
   - Each criterion row shows: pass/fail icon, title, regulation_ref as a small chip, weight as a numeric chip (`+N` if passed, `−N` muted if failed), and `detail` below. Failed `per_week` criteria SHALL link to the corresponding Modul number.
6. THE ComplianceReport card SHALL include a "Lihat semua kriteria" toggle. When OFF (default), only failed criteria SHALL be visible per section; when ON, both passed and failed are visible.
7. THE ComplianceReport card SHALL render even when the dosen has not yet run the LLM-driven Review_Agent — it is a static computation. The FindingsPanel and ComplianceReport SHALL coexist on the page; the ComplianceReport shows the deterministic skeleton, the FindingsPanel adds the LLM-driven judgment lenses (CPMK alignment, content quality, continuity).
8. WHEN the Review_Agent's `sndikti_compliance_node` runs (Requirement 3), it SHALL call the same catalog used by the Compliance_Report so the two surfaces never disagree about what passes.

## Open Decisions To Confirm With User

The draft adopts the recommended option in each of these. Confirm or overrule before we generate tasks.

1. **Findings persistence** — Draft keeps Findings in DB so dismissals survive review re-runs and the UI can show "last reviewed at." Alternative: ephemeral (recomputed every time), simpler but loses dismissal memory. **Recommend: keep persistent.**
2. **Apply granularity** — Draft has Apply patch a single field. Alternative: Apply could write a structured patch covering multiple fields per finding (e.g., a continuity finding could rewrite both W3 description and W4 title). The single-field rule keeps Apply easy to reason about; multi-field would need a confirmation modal. **Recommend: single field only.**
3. **Free-text feedback** — Draft demotes `OverallFeedback`/`WeekFeedback` rather than removing. Alternative: remove them entirely. **Recommend: keep, retitle, move WeekFeedback under the internal disclosure.**
4. **Continuity LLM call cost** — One call covers all 16 meetings. Alternative: per-pair calls (15 calls). The single-call approach is far cheaper and gives the model whole-course context. **Recommend: single call.**
5. **Severity assignment** — Draft assigns severity in code, not via LLM. Alternative: let the LLM choose severity. Code-assigned is more predictable. **Recommend: code-assigned.**
6. **Cooldown duration** — Draft uses 30 seconds. Could be lower (10s) or higher (2 min). **Recommend: 30 seconds.**
7. **Static compliance card** — Resolved by Requirement 14/15: replaced entirely by the deterministic catalog-driven `ComplianceReport` card. The catalog is a strict superset of the old static checklist, so nothing is lost.
8. **Catalog scope** — Draft includes ~24 criteria (Requirement 14.2). Could be expanded to also cover institutional house rules (specific bahan-kajian count, required references like "SN-Dikti minimum textbook list"). **Recommend: ship the 24, add a `house_rules.py` extension point later for institution-specific rules without amending the spec.**
9. **Score rendering when zero data** — A brand new RPS with no meetings would score `~0%`. Confirm that's the desired UX (recommended) or whether to show "Not yet measurable" until at least one CPMK is added. **Recommend: show the actual percentage so the dosen sees progress as they fill the form.**
