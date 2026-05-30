# Requirements Document

## Introduction

EduCopilot currently models each RPS meeting as a single free-text `topic` plus free-text `learning_method`, `evaluation_method`, and `references` columns. The user's institution requires a different RPS layout for each weekly module (Modul 1..16):

| Modul | Bahan Kajian/Topik | Sub-Topik | CPMK Terkait | No. Referensi |
| --- | --- | --- | --- | --- |
| 1 | AI dalam Industri dan Masyarakat | **Pengantar AI Terapan dan Agentic AI:** Peran AI dalam sistem bisnis... | 1 | 1, 3, 8 |
| 8 | _Ujian Tengah Semester (UTS)_ | _Ujian Tengah Semester (UTS)_ | — | — |
| 16 | _Ujian Akhir Semester (UAS)_ | _Ujian Akhir Semester (UAS)_ | — | — |

The institutional template introduces a two-level topic hierarchy (Bahan Kajian/Topik → Sub-Topik with `Title: description`), a single CPMK number per row (not a comma-separated string), and references cited by integer index against an RPS-level numbered reference list. It removes the per-meeting Metode and Evaluasi columns.

This feature aligns the EduCopilot data model, AI generation, manual edit form, RPS detail page, and persistence layer with that institutional layout. It must do so without breaking existing features that depend on per-meeting method and evaluation data (compliance checks, knowledge graph indexing, per-week regeneration, auto-grading, auto-material generation), and it must migrate existing RPS rows that already have free-text `topic`, `cpmk`, and `references` values.

## Glossary

- **RPS**: Rencana Pembelajaran Semester. The course-level lesson plan that owns CPL, CPMK, the references list, bahan kajian, learning methods, modality, and 16 weekly meetings.
- **RPS_Meeting**: A single row in the 16-row weekly schedule belonging to one RPS. Identified by `(rps_id, week_number)`.
- **Bahan_Kajian**: The course-level list of higher-level subject areas (e.g. "AI dalam Industri dan Masyarakat"). Stored on the RPS in `bahan_kajian: string[]`.
- **Bahan_Kajian_Topik** (per meeting): The specific Bahan Kajian value assigned to one weekly meeting, chosen from the parent RPS's `bahan_kajian` list. The same value may repeat across multiple meetings.
- **Sub_Topik**: The week-specific topic in `Title: description` form. The title (bold portion in the institutional template) names the weekly subject; the description elaborates on it.
- **Sub_Topic_Title**: The bold title portion of Sub_Topik.
- **Sub_Topic_Description**: The descriptive portion of Sub_Topik that follows the title and colon.
- **CPMK_List**: The course-level ordered list of CPMK descriptions stored on the RPS as `cpmk_list: string[]`. CPMK numbering is 1-based and follows list order (`cpmk_list[0]` ↔ CPMK 1).
- **Meeting_CPMK_Number**: The 1-based integer index into `CPMK_List` that the meeting maps to (institutional template uses a single number per row).
- **References_List**: The course-level ordered list of full reference strings stored on the RPS as `references_list: string[]`. Reference numbering is 1-based and follows list order.
- **Meeting_Reference_Indices**: The list of 1-based integer indices into `References_List` cited by a single meeting (e.g. `[1, 3, 8]` rendered as "1, 3, 8").
- **UTS_Module**: The fixed module reserved for Ujian Tengah Semester. By institutional template, this is Modul 8.
- **UAS_Module**: The fixed module reserved for Ujian Akhir Semester. By institutional template, this is Modul 16.
- **Exam_Module**: A meeting whose week_number is either UTS_Module or UAS_Module. Has no Bahan_Kajian_Topik, Sub_Topik content beyond the exam label, CPMK, or references.
- **Institutional_Export_View**: The display layout that shows only the five institutional columns (Modul, Bahan Kajian/Topik, Sub-Topik, CPMK, No. Referensi) without per-meeting method/evaluation.
- **Internal_Pedagogy_Fields**: Per-meeting `learning_method` and `evaluation_method` values used internally by compliance checks, the knowledge graph indexer, the per-week regenerate agent, the auto-material agent, and the grading agent. These are not part of the institutional template but remain in the data model.
- **RPS_Agent**: The LangGraph pipeline in `app/backend/app/agents/rps_agent.py` that drafts CPL, CPMK, and 16 meetings from a course brief.
- **Per_Week_Regenerate_Agent**: The single-meeting LLM call invoked by `POST /api/rps/{rps_id}/meetings/{week}/regenerate`.
- **Compliance_Checks**: The function `app.core.stats.compliance_checks` that scores method variety and evaluation coverage from per-meeting data.

## Rules of Inference

The following invariants are derived from the requirements below and used by validators, the AI agent, and the migration:

1. For every RPS, the meeting set is exactly `{week_number ∈ 1..16}` with no duplicates and no gaps.
2. For every meeting where `week_number ∉ {UTS_Module, UAS_Module}`:
   - `bahan_kajian_topik` SHALL be one of the strings in the parent RPS's `bahan_kajian` list, or empty (only allowed during draft state).
   - `meeting_cpmk_number` SHALL be an integer in `[1, len(cpmk_list)]`, or null (only allowed during draft state).
   - Every entry in `meeting_reference_indices` SHALL be an integer in `[1, len(references_list)]`.
3. For every meeting where `week_number ∈ {UTS_Module, UAS_Module}`:
   - `bahan_kajian_topik` SHALL be empty.
   - `meeting_cpmk_number` SHALL be null.
   - `meeting_reference_indices` SHALL be empty.
   - `sub_topic_title` SHALL be `"Ujian Tengah Semester (UTS)"` for week 8 and `"Ujian Akhir Semester (UAS)"` for week 16.
   - `sub_topic_description` SHALL be empty.
4. UTS_Module is fixed to 8 and UAS_Module is fixed to 16 for the institutional template; these are constants in the codebase, not user-configurable.
5. The institutional Sub-Topik display string is the concatenation `<sub_topic_title>: <sub_topic_description>` when the description is non-empty, otherwise just `<sub_topic_title>`.
6. The institutional No. Referensi display string is `meeting_reference_indices` joined by `", "`. The actual reference text is resolved from `references_list[idx-1]` at display time.
7. Internal_Pedagogy_Fields (`learning_method`, `evaluation_method`) are preserved on every meeting (including exam modules where they may be empty) and are NOT shown in the Institutional_Export_View.

## Requirements

### Requirement 1: Two-Level Topic Hierarchy Per Meeting

**User Story:** As a dosen, I want each meeting to carry both a Bahan Kajian/Topik (chosen from the course-level list) and a Sub-Topik with a bold title and description, so that my RPS matches the institutional template.

#### Acceptance Criteria

1. THE RPS_Meeting SHALL store a field `bahan_kajian_topik` of type string for the higher-level subject area assigned to that week.
2. THE RPS_Meeting SHALL store a field `sub_topic_title` of type string for the bold weekly title.
3. THE RPS_Meeting SHALL store a field `sub_topic_description` of type string for the elaboration following the title.
4. WHEN a meeting is rendered in the Institutional_Export_View, THE RPS_Detail_Page SHALL display `sub_topic_title` in bold followed by `": "` and `sub_topic_description`, omitting the colon and description if `sub_topic_description` is empty.
5. WHEN the RPS form presents the Bahan Kajian/Topik field for a non-exam meeting, THE RPS_Form SHALL render it as a single-select control whose options are exactly the entries of the parent RPS's `bahan_kajian` list, plus an empty option.
6. IF the dosen submits a meeting whose `bahan_kajian_topik` is non-empty and not present in the parent RPS's `bahan_kajian` list, THEN THE RPS_API SHALL reject the request with HTTP 400 and a message identifying the offending week and value.
7. WHILE the parent RPS's `bahan_kajian` list is empty, THE RPS_Form SHALL display an inline notice on the meetings section instructing the dosen to add Bahan Kajian entries before assigning per-week topics.

### Requirement 2: Numbered References List With Per-Meeting Index Citations

**User Story:** As a dosen, I want each meeting to cite references by their numbers (e.g. "1, 3, 8") against my course-level numbered reference list, so that my RPS matches the institutional citation style and stays consistent when references are reordered.

#### Acceptance Criteria

1. THE RPS SHALL retain `references_list` as an ordered list of strings; the 1-based position of each entry SHALL be its citation number.
2. THE RPS_Meeting SHALL store a field `reference_indices` of type list of integers, each in the range `[1, len(parent_rps.references_list)]`.
3. WHEN a meeting is rendered in the Institutional_Export_View, THE RPS_Detail_Page SHALL display `reference_indices` joined by `", "` in the No. Referensi column.
4. WHEN the dosen hovers or focuses the No. Referensi cell of a meeting, THE RPS_Detail_Page SHALL display a tooltip listing each cited index alongside the resolved reference text from `references_list`.
5. THE RPS_Form SHALL present the No. Referensi field for a non-exam meeting as a multi-select control whose options are the parent RPS's `references_list` entries labeled `"<index>. <reference text>"`.
6. IF the dosen removes or reorders entries in `references_list` after meetings have been saved, THEN THE RPS_API SHALL re-validate every meeting's `reference_indices` and SHALL reject the save with HTTP 400 if any index is now out of range, identifying the affected weeks.
7. THE RPS_Form SHALL provide a "Referensi & Pustaka" editor that displays each entry with its current 1-based number and that supports adding, editing, removing, and reordering entries.
8. WHEN the dosen reorders entries in the references editor, THE RPS_Form SHALL automatically remap every meeting's `reference_indices` so that the cited reference text is preserved.

### Requirement 3: Single CPMK Number Per Meeting

**User Story:** As a dosen, I want each meeting to map to a single CPMK number (1, 2, 3, ...) matching the institutional template, instead of a free-text string like "CPMK-1, CPMK-2".

#### Acceptance Criteria

1. THE RPS_Meeting SHALL store a field `cpmk_number` of type integer or null, where a non-null value is in the range `[1, len(parent_rps.cpmk_list)]`.
2. WHEN a meeting is rendered in the Institutional_Export_View, THE RPS_Detail_Page SHALL display `cpmk_number` as a plain integer (e.g. `1`) in the CPMK column, or an em-dash `—` if null.
3. THE RPS_Form SHALL present the CPMK field for a non-exam meeting as a single-select control whose options are the integers `1..len(cpmk_list)` labeled `"<n>. <cpmk text>"`.
4. IF the dosen submits a meeting whose `cpmk_number` is non-null and outside `[1, len(cpmk_list)]`, THEN THE RPS_API SHALL reject the request with HTTP 400 and identify the offending week.
5. WHILE the parent RPS's `cpmk_list` is empty, THE RPS_Form SHALL disable the CPMK field for every non-exam meeting and display an inline notice instructing the dosen to add CPMK entries first.

### Requirement 4: Auto-Skipping of UTS and UAS Modules

**User Story:** As a dosen, I want Modul 8 and Modul 16 to be locked to UTS and UAS without Bahan Kajian, CPMK, or references, so that the institutional template is followed exactly.

#### Acceptance Criteria

1. THE System SHALL define UTS_Module as the constant integer `8` and UAS_Module as the constant integer `16` in shared backend and frontend constants.
2. WHEN a new RPS is created (manual or AI), THE RPS_API SHALL initialize the meeting at `week_number = 8` with `sub_topic_title = "Ujian Tengah Semester (UTS)"`, `sub_topic_description = ""`, `bahan_kajian_topik = ""`, `cpmk_number = null`, and `reference_indices = []`.
3. WHEN a new RPS is created (manual or AI), THE RPS_API SHALL initialize the meeting at `week_number = 16` with `sub_topic_title = "Ujian Akhir Semester (UAS)"`, `sub_topic_description = ""`, `bahan_kajian_topik = ""`, `cpmk_number = null`, and `reference_indices = []`.
4. WHILE a meeting's `week_number` is in `{UTS_Module, UAS_Module}`, THE RPS_Form SHALL hide the Bahan Kajian/Topik, CPMK, and No. Referensi inputs for that row and SHALL render `sub_topic_title` as a read-only label.
5. IF the RPS_Agent or Per_Week_Regenerate_Agent emits non-exam content for `week_number ∈ {UTS_Module, UAS_Module}`, THEN THE RPS_API SHALL discard that content and SHALL substitute the canonical exam values defined in 4.2 and 4.3.
6. IF the dosen submits a save where any meeting at `week_number ∈ {UTS_Module, UAS_Module}` has non-empty `bahan_kajian_topik`, non-null `cpmk_number`, or non-empty `reference_indices`, THEN THE RPS_API SHALL reject the request with HTTP 400 and identify the offending week.

### Requirement 5: Drop Method and Evaluation From the Institutional View While Preserving Internal Use

**User Story:** As a dosen, I want the institutional RPS view and form to omit per-meeting Metode and Evaluasi columns (since the institutional template does not contain them), while keeping the data available for compliance, the knowledge graph, and the per-week AI agents that depend on it.

#### Acceptance Criteria

1. THE RPS_Meeting SHALL retain `learning_method` and `evaluation_method` fields as Internal_Pedagogy_Fields with the same column types as today.
2. THE Institutional_Export_View SHALL NOT render columns for `learning_method` or `evaluation_method`.
3. THE RPS_Form SHALL NOT render per-meeting inputs for `learning_method` or `evaluation_method` in its default layout.
4. WHERE the dosen toggles an "Advanced (Internal)" disclosure on a meeting row, THE RPS_Form SHALL reveal editable inputs for `learning_method` and `evaluation_method` for that single meeting.
5. WHEN a new meeting is created (manual or AI), THE RPS_API SHALL populate `learning_method` from the parent RPS's `learning_methods` list (joined by `", "`) and SHALL populate `evaluation_method` with a sensible default chosen by the RPS_Agent or with `"Tanya Jawab"` for manual creation if the agent does not supply one.
6. THE Compliance_Checks function SHALL continue to read `learning_method` and `evaluation_method` from each meeting and SHALL keep its existing scoring behavior unchanged by this feature.
7. THE Knowledge_Graph_Indexer SHALL continue to read `learning_method` and `evaluation_method` from each meeting for embedding metadata.
8. THE Per_Week_Regenerate_Agent SHALL continue to read and write `learning_method` and `evaluation_method` on the targeted meeting.

### Requirement 6: AI Generation Aligned to the Institutional Schema

**User Story:** As a dosen using "Auto-Generate AI", I want the LLM to produce meetings in the institutional shape (`bahan_kajian_topik`, `sub_topic_title`, `sub_topic_description`, `cpmk_number`, `reference_indices`), so that the generated RPS already matches the institutional template without manual rework.

#### Acceptance Criteria

1. WHEN the RPS_Agent's `draft_rps_node` is invoked, THE RPS_Agent SHALL prompt the LLM to emit a JSON array where each element has the keys `week` (int 1..16), `bahan_kajian_topik` (string), `sub_topic_title` (string), `sub_topic_description` (string), `cpmk_number` (int or null), `reference_indices` (list of int), `method` (string, internal), and `evaluation` (string, internal).
2. THE RPS_Agent SHALL pass the parent RPS's `bahan_kajian` list, the numbered `cpmk_list`, and the numbered `references_list` into the prompt, with explicit instructions that `bahan_kajian_topik` MUST be drawn verbatim from the supplied `bahan_kajian` list, that `cpmk_number` MUST be an integer index into the supplied CPMK list, and that `reference_indices` MUST be integer indices into the supplied references list.
3. THE RPS_Agent SHALL prompt the LLM to repeat the same `bahan_kajian_topik` value across multiple weekly entries when the underlying subject area spans more than one week, mirroring the institutional pattern (e.g. "AI dalam Industri dan Masyarakat" appearing on Modul 1, 3, 4, 12).
4. THE RPS_Agent SHALL emit `bahan_kajian_topik = ""`, `sub_topic_title = "Ujian Tengah Semester (UTS)"`, `sub_topic_description = ""`, `cpmk_number = null`, and `reference_indices = []` for the entry at `week = 8`.
5. THE RPS_Agent SHALL emit `bahan_kajian_topik = ""`, `sub_topic_title = "Ujian Akhir Semester (UAS)"`, `sub_topic_description = ""`, `cpmk_number = null`, and `reference_indices = []` for the entry at `week = 16`.
6. IF the LLM returns a `bahan_kajian_topik` that is not present in the supplied `bahan_kajian` list (case-insensitive match), THEN THE RPS_API SHALL coerce the value to the closest match by normalized string equality, falling back to empty string if no match is found within Levenshtein distance 3.
7. IF the LLM returns a `cpmk_number` outside `[1, len(cpmk_list)]` or returns `cpmk` as a free-text string for a non-exam week, THEN THE RPS_API SHALL parse the first integer it finds in the string and coerce it; if no valid integer can be coerced, the value SHALL be set to null and the meeting SHALL be flagged with `status = "needs_review"`.
8. IF the LLM returns `reference_indices` containing values outside `[1, len(references_list)]`, THEN THE RPS_API SHALL drop the out-of-range indices and SHALL flag the meeting with `status = "needs_review"`.
9. WHEN the Per_Week_Regenerate_Agent regenerates a single meeting, THE Per_Week_Regenerate_Agent SHALL emit the same institutional schema as in 6.1 and SHALL apply the same coercion rules in 6.6, 6.7, and 6.8.

### Requirement 7: Institutional Display Layout on the RPS Detail Page

**User Story:** As a dosen reviewing my RPS, I want the detail page to show meetings in the institutional five-column layout (Modul, Bahan Kajian/Topik, Sub-Topik, CPMK Terkait Topik atau Sub-Topik, No. Referensi), so that I can verify at a glance that my RPS matches what my institution expects.

#### Acceptance Criteria

1. THE RPS_Detail_Page SHALL render the meetings section as a table with columns in this exact order: Modul, Bahan Kajian/Topik, Sub-Topik, CPMK Terkait Topik atau Sub-Topik, No. Referensi.
2. WHEN rendering the Bahan Kajian/Topik cell, THE RPS_Detail_Page SHALL display `bahan_kajian_topik` in italic typography.
3. WHERE a meeting has `week_number ∉ {UTS_Module, UAS_Module}`, THE RPS_Detail_Page SHALL render the Sub-Topik cell as `sub_topic_title` in bold followed by `": "` and `sub_topic_description` in normal weight, omitting the colon and description if `sub_topic_description` is empty; this formatting rule applies immediately whenever the meeting is non-exam, independent of any prior rendering state of the table.
4. WHERE a meeting has `week_number ∈ {UTS_Module, UAS_Module}`, THE RPS_Detail_Page SHALL render the Sub-Topik cell as `sub_topic_title` in italic on its own.
5. WHEN rendering the CPMK Terkait cell, THE RPS_Detail_Page SHALL display the integer `cpmk_number` or `—` if null.
6. WHEN rendering the No. Referensi cell, THE RPS_Detail_Page SHALL display `reference_indices` joined by `", "`, or `—` if empty.
7. WHERE the dosen toggles an "Tampilkan kolom internal" disclosure on the detail page, THE RPS_Detail_Page SHALL append two extra columns (Metode, Evaluasi) sourced from the Internal_Pedagogy_Fields.
8. THE RPS_Detail_Page SHALL display the parent RPS's numbered references list ("Referensi & Pustaka") as a numbered list `1.`, `2.`, ... separately from the meetings table, so that the No. Referensi numbers in the table can be cross-referenced.

### Requirement 8: Manual Edit Form Adopting the Institutional Layout

**User Story:** As a dosen editing my RPS manually, I want the edit form to use the same institutional column layout as the detail page, so that I can author and verify in one consistent shape.

#### Acceptance Criteria

1. THE RPS_Form SHALL render each of the 16 meeting rows with controls for Bahan Kajian/Topik (single-select), Sub-Topik Title (text input), Sub-Topik Description (textarea), CPMK (single-select integer), and No. Referensi (multi-select indices).
2. WHEN the dosen edits the parent RPS's `bahan_kajian`, `cpmk_list`, or `references_list`, THE RPS_Form SHALL immediately update the option sets of the corresponding per-meeting controls without requiring a page reload.
3. IF the dosen removes a `bahan_kajian` entry that is currently referenced by one or more meetings, THEN THE RPS_Form SHALL display a confirmation dialog naming the affected weeks and SHALL clear `bahan_kajian_topik` on those meetings on confirm.
4. IF the dosen removes a `cpmk_list` entry that is currently referenced by one or more meetings, THEN THE RPS_Form SHALL display a confirmation dialog naming the affected weeks and SHALL clear `cpmk_number` on those meetings on confirm.
5. IF the dosen removes a `references_list` entry that is currently cited by one or more meetings, THEN THE RPS_Form SHALL display a confirmation dialog naming the affected weeks and SHALL remove that index from each affected meeting's `reference_indices` on confirm, while remapping remaining indices to preserve cited reference text.
6. THE RPS_Form SHALL preserve the existing "Auto-Generate AI" entry point and the existing course-level controls for CPL, CPMK, References, Bahan Kajian, Learning Methods, and Modality without changing their core user workflows; minor adjustments to error handling and validation flows are permitted where required to support the confirmation dialogs in 8.3, 8.4, and 8.5.

### Requirement 9: Backward-Compatible Migration of Existing RPS Rows

**User Story:** As a dosen with RPS data already saved under the old free-text schema, I want my existing meetings to migrate cleanly into the institutional schema without losing information.

#### Acceptance Criteria

1. WHEN the application starts and detects a database row in `rps_meetings` lacking the new columns, THE Migration SHALL add columns `bahan_kajian_topik` (VARCHAR(255), nullable), `sub_topic_title` (VARCHAR(500), nullable), `sub_topic_description` (TEXT, nullable), `cpmk_number` (INTEGER, nullable), and `reference_indices` (JSON, nullable) to the `rps_meetings` table.
2. WHEN migrating an existing meeting row, THE Migration SHALL parse the legacy `topic` field as follows: if `topic` matches the regex `^(?P<title>[^:]+):\s*(?P<desc>.+)$`, then set `sub_topic_title = title.strip()` and `sub_topic_description = desc.strip()`; otherwise set `sub_topic_title = topic.strip()` and `sub_topic_description = ""`.
3. WHEN migrating an existing meeting row whose `week_number ∉ {UTS_Module, UAS_Module}`, THE Migration SHALL leave `bahan_kajian_topik` empty (`""`), to be filled by the dosen on next edit.
4. WHEN migrating an existing meeting row, THE Migration SHALL parse the legacy `cpmk` string by extracting the first integer found in any token of the form `CPMK-N` or `N`; if a valid integer in `[1, len(parent_rps.cpmk_list)]` is found it SHALL be stored as `cpmk_number`, otherwise `cpmk_number` SHALL be null.
5. WHEN migrating an existing meeting row, THE Migration SHALL attempt to derive `reference_indices` by matching the legacy `references` string against the parent RPS's `references_list` (case-insensitive substring match against each entry); each matched entry's 1-based index SHALL be added to `reference_indices` in ascending order.
6. WHEN the legacy `references` string yields no matches in 9.5, THE Migration SHALL leave `reference_indices` empty and SHALL retain the original `references` string in the existing column as a fallback shown in a "Legacy Referensi" badge on the affected meeting until the dosen edits the row.
7. THE Migration SHALL set `sub_topic_title = "Ujian Tengah Semester (UTS)"` and SHALL leave `bahan_kajian_topik`, `cpmk_number`, and `reference_indices` cleared (without populating them first) for any existing meeting at `week_number = 8`, regardless of legacy `topic` content; the Migration SHALL apply this UTS rule only when `week_number` equals exactly 8 and SHALL NOT apply it to any other week even if its legacy `topic` mentions UTS or Ujian Tengah Semester.
8. THE Migration SHALL set `sub_topic_title = "Ujian Akhir Semester (UAS)"` and SHALL leave `bahan_kajian_topik`, `cpmk_number`, and `reference_indices` cleared (without populating them first) for any existing meeting at `week_number = 16`, regardless of legacy `topic` content; the Migration SHALL apply this UAS rule only when `week_number` equals exactly 16 and SHALL NOT apply it to any other week even if its legacy `topic` mentions UAS or Ujian Akhir Semester.
9. THE Migration SHALL be idempotent: running it more than once on a database that already has the new columns SHALL leave existing data unchanged.

### Requirement 10: Compliance Score Adjusted for the Institutional Schema

**User Story:** As a dosen, I want the compliance score to reflect adherence to the institutional template (UTS at week 8, UAS at week 16, every non-exam week has Bahan Kajian/Topik, Sub-Topik, CPMK number, and at least one reference index), so that the displayed score is meaningful for my institution.

#### Acceptance Criteria

1. THE Compliance_Checks SHALL include a check named "UTS at Modul 8" that passes when the meeting at `week_number = 8` has `sub_topic_title` containing `"UTS"` or `"Tengah Semester"` (case-insensitive).
2. THE Compliance_Checks SHALL include a check named "UAS at Modul 16" that passes when the meeting at `week_number = 16` has `sub_topic_title` containing `"UAS"` or `"Akhir Semester"` (case-insensitive).
3. THE Compliance_Checks SHALL include a check named "Bahan Kajian/Topik populated" that passes when every non-exam meeting has a non-empty `bahan_kajian_topik` that is present in the parent RPS's `bahan_kajian` list.
4. THE Compliance_Checks SHALL include a check named "Sub-Topik populated" that passes when every non-exam meeting has a non-empty `sub_topic_title`.
5. THE Compliance_Checks SHALL include a check named "CPMK number assigned" that passes when every non-exam meeting has a non-null `cpmk_number` in `[1, len(cpmk_list)]`.
6. THE Compliance_Checks SHALL include a check named "References cited" that passes when every non-exam meeting has at least one entry in `reference_indices`.
7. THE Compliance_Checks SHALL retain its existing checks for method variety and evaluation coverage, sourced from Internal_Pedagogy_Fields.

## Open Decisions To Confirm With User

The following design points are captured here so they can be locked down during requirements review. The current draft adopts the recommended option in each case, but the dosen may overrule before we move to design.

1. **Sub-Topik split vs combined string.** Draft adopts split fields (`sub_topic_title` + `sub_topic_description`) because it lets the UI bold the title without parsing, makes export rendering deterministic, and avoids brittle regex round-trips. Confirm: keep split, or store one combined `sub_topik` string instead?
2. **Per-meeting reference picker UX.** Draft adopts a multi-select against the numbered references list (Requirement 2.5). Confirm: keep multi-select, or also allow free-text "1, 3, 8" entry as a fallback?
3. **Method and evaluation retention.** Draft keeps Internal_Pedagogy_Fields and hides them behind an "Advanced (Internal)" disclosure (Requirement 5). Removing them entirely would break Compliance_Checks (`method_variety_ok`, `eval_ok` in `app/backend/app/core/stats.py`), the knowledge graph indexer (`app/backend/app/api/v1/knowledge.py` writes `method` and `evaluation` into vector metadata), and the Per_Week_Regenerate_Agent (`app/backend/app/api/v1/rps.py` reads them in the prompt and writes them back). Confirm: keep + hide as drafted, or accept the breakage cost and drop entirely?
4. **UTS/UAS lock vs default.** Draft hard-locks Modul 8 and Modul 16 to UTS and UAS (Requirement 4). Confirm: hard-lock, or treat as suggested defaults the dosen can override?
5. **Numbered references editor.** Draft requires an explicit numbered editor on the RPS form (Requirement 2.7). Confirm: include the editor, or keep the existing plain list and synthesize numbers at display time only?
6. **AI grouping of repeated Bahan Kajian.** Draft asks the LLM to repeat the same `bahan_kajian_topik` across weeks where it applies (Requirement 6.3). Confirm: instruct the LLM explicitly as drafted, or leave grouping unconstrained?
