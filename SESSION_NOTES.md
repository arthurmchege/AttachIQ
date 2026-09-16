# AttachIQ — Quick Resume Note

Last updated: Aug 15, 2026, 00:23

## Status

Seed script fully working and verified in psql:

- 1 institution, 1 programme, 5 competency units, 1 supervisor, 2 students, 2 placements
- All committed to Postgres, confirmed via SELECT queries

## Next step (Day 5-6, per build plan)

Building POST /auth/login + get_current_user dependency.
Currently mid-explanation on: why bcrypt needs a dedicated verify function
(bcrypt.checkpw) instead of comparing two hash strings with ==, because
gensalt() produces a different salt every call, so hash_password(x) run
twice on the same password gives two DIFFERENT strings.

## To resume

Pick up right at: writing the /auth/login endpoint logic, starting with
password verification using bcrypt.checkpw().

## 2026-09-14

- Fixed unnamed FK constraint on User.programme_id (fk_users_programme_id) — migration applied
- Fixed seed.py: students now get programme_id assigned so agent tools have real relational data
- Implemented and verified get_pending_units(student_id, db) in agent_tools.py
  - Tested: happy path (Aaron, 5 pending CSC units), invalid UUID, non-existent UUID — all pass
- Cleaned up stray requiremnts.txt (merged into requirements.txt)
- Next: get_competency_detail

## 2026-09-15

- Truncated and re-seeded dev database; documented that seed.py is not idempotent (must truncate before re-running, or UUIDs/duplicates conflict)
- Added sample EvidenceSubmission to seed.py (Aaron, CSC101) with a placeholder
  local-storage file_url convention: "uploads/evidence/<filename>"
- Implemented and verified get_student_evidence(student_id, unit_id, db) in agent_tools.py
  - Tested: happy path (Aaron's CSC101 evidence), empty result (Aaron, CSC102, no evidence),
    invalid UUIDs, student with no placement — all pass
- Confirmed evidence submission does NOT affect get_pending_units — units only clear once
  an Assessment row exists, which is the correct separation between "submitted" and "assessed"
- Next: draft_assessment, then submit_assessment

## 2026-09-16

- Implemented and verified submit_assessment(student_id, unit_id, score, comments, db) —
  the final SupervisorIQ tool. Only tool that writes to the database.
- Added a guard against duplicate assessments: a second submission for the same
  placement + competency_unit returns an error rather than creating a duplicate row.
- Verified end-to-end integration: after submit_assessment writes a real row,
  get_pending_units correctly excludes that unit on the next call — confirms all
  five tools are correctly reading/writing shared state.

ALL FIVE SUPERVISORIQ TOOLS COMPLETE:
get_student_profile, get_pending_units, get_competency_detail,
get_student_evidence, draft_assessment, submit_assessment

Next: wire these tools into an actual ADK Agent + Runner (Phase 5 per master plan).
This is the part we do manually, together, slowly no shortcuts, since this is
what gets demoed live and defended in front of judges.
