# AttachIQ — Full Build Notes

**Started:** 2026-09-18
**Status:** MVP complete and frozen (branch `main`, tag `mvp-conference`). All work below happens on branch `full-build`.

---

## Why this document exists

The MVP (7-table schema, SupervisorIQ only, single conference demo) is done and verified end-to-end. This document captures the architecture decisions made for the _real_ production build that starts now. Nothing in the original pre-build design docs (16-table schema, 4-agent design, fixed API routes) is treated as final anymore — they were the pre-build plan, not a contract. Schema and architecture are open to grow, shrink, or restructure as real requirements emerge.

---

## Migration strategy

Fresh migrations, not incremental ALTERs on the MVP schema. The new design reshapes `users`, `institutions`, and `companies` at the root — splitting identity, adding an approval lifecycle, going global — so evolving the old migration chain in place is more error-prone than starting clean. MVP seed data was demo data only, nothing to preserve. The MVP remains fully intact and reachable via the `mvp-conference` tag on `main`.

---

## Portals

Four portals: **student**, **supervisor**, **coordinator**, **admin** (institution-level).

---

## Roles and onboarding flow

- **Platform admin** (global, not institution-scoped) approves each institution's initial access request. This must exist before any institution has its own admin, since institution admins are only created _after_ approval.
- **Institution** self-registers on the public landing page and requests portal access. Sits in a pending/approved/rejected state until a platform admin approves it.
- **Institution admin** — created after approval, one per institution. Registers the school setup and assigns coordinators.
- **Coordinator** — responsible for the students and companies they're placed at, within their institution.
- **Student** — does _not_ self-register. The school onboards students directly. Student login is **email + admission number as a first-login-only password**; on first successful login the student is force-redirected to set a real permanent password before they can use the portal (admission numbers aren't secret — printed on IDs/transcripts — so they can never be a standing password).
- **Supervisor** — does _not_ self-register either. After a student registers a company + names a supervisor as contact, the system **automatically** (no manual coordinator action) emails the supervisor a portal link, their email, and an auto-generated password — generated from name + phone/email at the moment of student registration. This has to scale to thousands of auto-fired emails, so a real transactional email provider (SendGrid / SES / Postmark — TBD) is needed from day one, not an afterthought, since a silently-failed email means a supervisor never learns they have an account.

### Student responsibilities after login

Students find their own attachment placements. After login, a student onboards their own company + placement:

- Company name + supervisor contact person
- Attachment duration: the school sets an overall time window, but the student enters their own specific ~3-month duration within it, since timing depends on when they secured a placement.

---

## Supervisor deduplication (the one non-trivial piece of onboarding logic)

If multiple students name the same supervisor as their contact, they should **share one supervisor record and login**, not get separate accounts each — a supervisor managing multiple students sees all of them in one dashboard rather than juggling logins.

- **Dedup key: `(email OR phone) + company_id`** — not email/phone alone, or two unrelated "Jane Wanjiru"s at different companies would incorrectly merge.
- **Companies and supervisors are global, not institution-scoped.** Students from _different institutions_ can be placed at the same company under the same supervisor — that supervisor sees and assesses all of them from one dashboard, across institutions. This is a deliberate asymmetry: most of the system is strictly tenant-scoped by `institution_id`, but `companies` and supervisor identity are shared/global tables with no `institution_id` filter at all. This needs to be explicit in code (comments, not just tribal knowledge) so nobody later slaps a blanket `institution_id` filter on a query touching these tables and silently breaks cross-institution supervisor visibility.

---

## Draft schema

### Identity & tenancy

- `platform_admins` — id, email, password_hash (global)
- `institutions` — id, name, status (pending/approved/rejected), requested_at, approved_at, approved_by → platform_admins
- `users` — id, institution_id, email, password_hash, full_name, role (STUDENT / SUPERVISOR / COORDINATOR / INSTITUTION_ADMIN), must_reset_password (bool), created_at
  - `full_name` and `email` live here, shared across all roles — not duplicated per role-profile table.

### Role profiles (1:1 extension of `users`, chosen over a fully split multi-table identity model)

- `student_profiles` — user_id (PK/FK), admission_number, department_id, programme_id
- `supervisor_profiles` — user_id (PK/FK), phone_number, company_id
- `coordinator_profiles` — user_id (PK/FK), department_id

Rationale: keeps every existing FK, JWT subject, and ADK tool lookup pointed at `users.id` — no churn there — while avoiding nullable-column sprawl on `users` itself. Role-specific fields only exist where the role exists.

### Academic structure (per institution)

- `departments` — id, institution_id, name
- `programmes` — id, department_id, name
- `competency_units` — id, programme_id, name/code
- `topics` — id, competency_unit_id, name

### Companies & placements

- `companies` — id, name, industry, sector (nullable), county, town, sublocation — **global, not institution-scoped**
- `placements` — id, student_id → users, company_id, supervisor_id → users, institution_id, start_date, end_date

### Assessment (carried over from MVP concept, now scoped by placement)

- `evidence_submissions`, `assessments` — as in the MVP schema, now tied to a placement rather than a flat student/unit pair

---

## Build order

1. **Institution registration + platform admin approval** (first vertical slice — nothing else can exist until an institution exists)
2. Institution admin flows (school setup, assigning coordinators)
3. Student onboarding (by school) + first-login password flow
4. Student self-service: company + supervisor + placement registration, including the dedup logic
5. Supervisor auto-provisioning + email delivery
6. Everything downstream (assessments, StudentIQ, CoordIQ, AttachIQ Core orchestrator) per the original design docs, revisited as needed once the above is real

---

## Open items / not yet decided

- Transactional email provider for supervisor auto-provisioning (SendGrid / SES / Postmark)
- Exact institution "overall attachment window" mechanism — how the school sets it, how the student's entered duration is validated against it

Session — 2026-09-19 — Phase 1: Institution Registration

Added InstitutionStatus enum (PENDING, APPROVED, REJECTED) and PlatformAdmin model (global, not institution-scoped). Institution gained status, approved_at, approved_by_id (FK → platform_admins.id).
Added registration fields to Institution: tvet_registration_number (unique), contact_person_name, phone_number, email (unique), county, town.
Two migrations applied and verified against real Postgres, both committed to full-build:
7da68bc6500b — platform_admins + institution approval lifecycle
d79fe7cb6e38 — registration fields on institutions
Recurring gotcha hit twice: Alembic autogenerate leaves FK/unique constraints unnamed (None) unless the model itself names them — breaks downgrade() since there's nothing to reference. Now a standing check on every migration: name every constraint explicitly before trusting a generated file.
Second gotcha: sa.Enum(...) auto-creates its Postgres type when used inside create_table(), but NOT when used in add_column() on an existing table — must call postgresql.ENUM(...).create(op.get_bind(), checkfirst=True) explicitly first.
Third gotcha: adding a NOT NULL column with no server_default fails outright if the table already has rows. Hit this against leftover MVP test data (one institution row) still sitting in institutions from before the fresh-migrations decision — resolved with TRUNCATE TABLE institutions CASCADE, confirming no real data existed to protect.
Built POST /institutions/register (public, unauthenticated) — validates uniqueness on tvet_registration_number and email before insert, returns 201 with the institution in PENDING status. Tested end-to-end via Postman, confirmed via psql. Known gap: the uniqueness pre-check has a theoretical race condition (two simultaneous identical registrations could both pass the check) — not handled, low risk at current scale, noted for later.
email-validator was missing as a dependency for Pydantic's EmailStr — installed and added to requirements.txt.
Confirmed decision: registration collects only institution-level details (no separate "admin" identity at registration time) — the institution's own contact_person_name + email becomes the first INSTITUTION_ADMIN user at approval time. full_name on that admin user = contact_person_name, not the institution's name.
Confirmed decision: no real email sending yet. Approval endpoint (not yet built) will generate a password and log/return it directly rather than emailing it, until Resend is wired in as its own separate task.
Confirmed decision: email provider will be Resend (free tier: 3,000/month, 100/day, one domain) — chosen over Postmark (no real free tier) and SES (sandbox approval friction not worth it at this stage).
Not yet built: platform admin seeding (no signup path exists for this role — needs a one-off manual script using hash_password() from security.py, since platform admins are provisioned out-of-band, not self-service), platform admin login endpoint, institution approval endpoint.

## 2026-09-19

- Added `create_platform_admin.py` — one-off interactive script (not an API endpoint) to seed platform admin accounts, reusing `hash_password()` from `security.py`. Platform admins have no self-service signup by design. First real platform admin seeded and confirmed in `psql`.
- Added `POST /platform-admin/auth/login` (`routers/platform_admin.py`), reuses `verify_password`/`create_access_token` as-is. Token payload uses hardcoded `"role": "PLATFORM_ADMIN"` string, not an enum — `PlatformAdmin` has no `role` column and isn't a `User`.
- Added `get_current_platform_admin` dependency in `dependencies.py`, separate from `get_current_user`. **Necessary, not optional**: `get_current_user` only queries `users`, and a platform admin token's `sub` is a `platform_admins.id` — would silently 401 forever if reused. Also checks `role == "PLATFORM_ADMIN"` explicitly in the payload, not just `sub` presence.
- Added `GET /institutions/pending` and `POST /institutions/{id}/approve`, both gated by `get_current_platform_admin`.
- Approval endpoint: rejects with `409` if institution isn't `PENDING` (blocks double-approval / duplicate admin creation), generates temp password via `secrets.choice` (never `random`), creates `INSTITUTION_ADMIN` user with `full_name = contact_person_name`, sets `status = APPROVED` + `approved_at` + `approved_by_id`.
- **DEV MODE flag, not a finished feature**: temp password is returned directly in the response since Resend isn't wired up yet. Must be pulled from the response once real email sending exists.
- Full loop tested end-to-end and cross-checked in `psql` at every step: register → shows in `/pending` → approve → institution `APPROVED` with correct `approved_by_id` → `users` row created with correct `email`/`full_name`/`institution_id`.
- Caught mid-session: `platform_admin.py`, the `dependencies.py` addition, and the `main.py` router registration sat **uncommitted for an extended stretch** before being caught by `git status`. Discipline note: commit right after each working piece, don't batch several steps before checking.
- **Verified**: institution admin (Jane Doe) login confirmed via existing `/auth/login` using temp password from approval response. Decoded JWT confirms correct claims: `role: INSTITUTION_ADMIN`, `institution_id` matches Kiambu's UUID, `sub` matches her `users.id`. **Phase 1 (institution registration → platform admin approval → working admin login) is fully closed.**
