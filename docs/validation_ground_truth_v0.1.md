# Ground Truth Validation Checklist (v0.1)

This document defines the minimum validation checks for manually reconstructed DDR ground-truth YAML files.
These checks ensure the dataset is consistent, auditable, and usable as deterministic test cases for the
Legacy Well Digital Twin Reconstruction Engine.

## Scope

Applies to files under:

data/manual_ground_truth/

and expects the YAML structure defined by:

schema/ddr_event_schema_v0.1.yaml

The goal is not to be “complete.”
The goal is to be correct, consistent, and testable.

---

## 1. File and Schema Conformance

1.1 Required top-level keys exist:
- schema_version
- well
- section
- fluid_program
- events

1.2 `schema_version` matches the schema file version (v0.1).

1.3 `events` is a non-empty list.

1.4 Each event includes required keys:
- date
- operation
- depth_start_md
- depth_end_md
- summary
- sources

1.5 Null handling:
- Unknown numeric values must be null (not omitted, not -999.99).
- Unknown strings must be null or "unknown" only where schema permits.

---

## 2. Source Traceability

2.1 Every event has at least one source reference.

2.2 Each source reference includes:
- file
- page

2.3 Optional quote_snippet rules:
- Keep snippets short.
- Do not paste large excerpts.
- Snippets should be sufficient to re-locate the statement in the source file.

2.4 Source filenames should match the original DDR artifacts used for reconstruction.

---

## 3. Temporal Consistency

3.1 Dates must be valid and consistent with the DDR report window.

3.2 Events should be in chronological order by date.

3.3 If start_time/end_time are provided:
- Must be HH:MM format.
- Must not contradict the DDR day window.

---

## 4. Depth and Operational Logic

4.1 Depth fields:
- depth_start_md and depth_end_md must be numeric or null.
- Use meters MD.

4.2 Drilling progression sanity:
- For drill/orient/ream sequences, depth_end_md should generally not decrease across consecutive drilling days.
- If depth decreases (e.g., trip/POOH), operation must reflect that (trip_out, trip_in, etc.) and be explained in summary.

4.3 TD milestone:
- A "drill_to_td" (or "drill" with td_called=true, if you use that convention in the instance) must exist when the section reaches TD.
- TD depth must be explicitly stated in either depth_end_md or summary.

4.4 Verification milestones:
Where DDR indicates it, ensure at least one of these is captured:
- well_static_flowcheck
- toc_tagged
- bop_test
- gyro_confirmation
- td_survey
- casing_float_verified

---

## 5. Quality Rules (Human Readability)

5.1 Summary must be deterministic:
- Describe what happened, not opinions.
- Include at least one concrete operational action and one concrete result or next step.

5.2 Use consistent terminology:
- “POOH” and “RIH” can appear in summary but should be understandable.
- Prefer consistent phrasing across events.

5.3 Keep event granularity consistent:
- v0.1 is “daily event level” unless the DDR provides a major interruption worth logging.

---

## 6. Acceptance Criteria for Ground Truth v0.1

Ground truth is considered v0.1 complete when:

- The YAML files pass checks 1–4 above.
- Every event is traceable to at least one DDR source (file+page).
- The kickoff/build/TD/casing transition story is reconstructable from the events alone.
- Another engineer can read the YAML and understand the operational progression without opening the PDFs.
