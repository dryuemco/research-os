# 16 - Post-Deploy Test Checklist (Render + GitHub Pages)

Use this checklist after every pilot deployment.

## 1) Render web deploy checks
- [ ] `GET /health` returns 200
- [ ] `GET /health/ready` returns 200
- [ ] `GET /docs` loads API docs (if `DOCS_ENABLED=true`)
- [ ] `GET /ui` loads internal UI page
- [ ] logs show startup diagnostics and no immediate process exit

## 2) GitHub Pages deploy checks
- [ ] Main Pages URL loads the dashboard shell
- [ ] `docs/site-config.js` backend URL points to the intended Render API
- [ ] navigation works for all dashboard pages
- [ ] no broken links in header actions
- [ ] browser console has no CORS errors for dashboard API calls

## 3) Functional dashboard checks
- [ ] opportunities page loads and shows rows or explicit empty state
- [ ] matches page loads and shows rows or explicit empty state
- [ ] notifications page loads and shows rows or explicit empty state
- [ ] operational runs page loads and shows rows or explicit empty state
- [ ] proposal workspaces page loads and shows rows or explicit empty state
- [ ] export packages page loads and shows rows or explicit empty state
- [ ] intelligence page loads retrieval/partners (or explicit empty/error states)

## 4) Config/security checks
- [ ] `DATABASE_URL` is set from managed Render database
- [ ] `INTERNAL_API_KEY` is not default value
- [ ] `ARTIFACT_DOWNLOAD_SECRET` is not default value
- [ ] `ALLOWED_ORIGINS` includes the GitHub Pages origin
- [ ] backend does not expose secrets in logs

## 5) Failure-mode checks
- [ ] backend unavailable shows dashboard connection error banner
- [ ] empty datasets render clear empty states (not broken tables)
- [ ] permission-denied responses render readable error messages
- [ ] request timeout errors render readable connectivity guidance

## 6) Optional workflow smoke checks
- [ ] trigger `POST /operations/jobs/ingestion` from API docs
- [ ] confirm `GET /operations/jobs` has a run entry
- [ ] confirm notifications update for configured dashboard user

## 7) Signoff
- [ ] deployment timestamp recorded
- [ ] operator initials recorded
- [ ] known issues documented for next iteration
