# 13 - Operational Loop: Scheduling, Matching, and Notifications

## Scope
This iteration adds the first operational loop for internal pilot usage:
1. scheduled source ingestion
2. change classification (created/updated/unchanged)
3. optional post-ingestion matching run
4. notification generation
5. dashboard/API visibility for operational runs

## Core components
- `OperationalJobConfig`: schedule configuration (`job_type`, interval, source/profile bindings).
- `OperationalJobRun`: persisted run records with status, trigger source, summaries, and errors.
- `MatchingRun`: persisted matching run summary metrics.
- `Notification`: internal notification feed model.

## Scheduler behavior
- `OperationalLoopService.run_due_jobs()` executes enabled jobs where `next_run_at <= now`.
- `run_operational_loop` worker continuously ticks using `OPERATIONAL_SCHEDULER_TICK_SECONDS`.
- Idempotency baseline:
  - ingestion deduplicates snapshots by source record + payload hash
  - unchanged source records classify as `unchanged` without new versions

## Source execution flow
- Source adapters remain responsible for normalization and optional record fetching.
- `funding_call_scaffold` adapter can pull dev fixtures from `OPERATIONAL_SOURCE_FIXTURE_PATH`.
- `eu_funding_tenders` adapter is the canonical live source path for Horizon and Erasmus+ opportunities from the Funding & Tenders portal.
- Operational ingestion emits run summary counts and optional change notifications.

## Live ingestion trigger
- `POST /operations/jobs/ingestion/live` runs the live official-source adapter on demand.
- Supports programme filters and record limits for pilot-safe ingestion.
- Uses existing ingestion persistence path (`opportunity_ingestion_snapshots` + `opportunity_versions`) so source/version traceability remains intact.

## Matching operational flow
- Matching can run:
  - manually (`POST /operations/jobs/matching`)
  - on schedule (`/operations/scheduler/tick`)
  - post-ingestion when configured (`run_matching_after=true`)
- Matching run summaries include opportunities scanned, matches created, recommendations, and red flags.

## Notification flow
- Initial delivery channel: in-app/internal notification feed.
- Triggered for:
  - `NEW_MATCH`
  - `OPPORTUNITY_CHANGED`
  - `JOB_FAILED`

## Pilot demo path
1. Seed profile and source fixture.
2. Trigger ingestion (`POST /operations/jobs/ingestion`).
3. Verify job run and change summary (`GET /operations/jobs`).
4. Verify matching run (`GET /operations/matching-runs`).
5. Verify notifications (`GET /operations/notifications?user_id=ops-admin`).
