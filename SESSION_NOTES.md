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
