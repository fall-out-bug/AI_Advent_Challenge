# Epic 21 · Rollback Plan

**Purpose**: Define procedures to safely revert Epic 21 changes if issues arise during
or after deployment.

**Authority**: EP21 Tech Lead or designated On-call Engineer (per operations.md §5.2)

---

## Rollback Principles

1. **Feature Flag First**: All new interfaces behind feature flags, off by default
2. **Backward Compatible**: Support both old and new implementations during transition
3. **Data Safety**: Never destructive migrations, always dual-write during transition
4. **Time-Boxed**: Decision to rollback within 1 hour of detecting critical issue
5. **Documented**: All rollback steps tested in staging before production deployment

---

## Feature Flags Inventory

| Flag | Default | Purpose | Rollback Impact |
|------|---------|---------|----------------|
| `USE_NEW_DIALOG_CONTEXT_REPO` | `False` | Enable DialogContextRepository interface | Toggle off restores Mongo direct access |
| `USE_NEW_HOMEWORK_REVIEW_SERVICE` | `False` | Enable HomeworkReviewService interface | Toggle off restores HWCheckerClient direct calls |
| `USE_NEW_STORAGE_ADAPTER` | `False` | Enable ReviewArchiveStorage interface | Toggle off restores direct file I/O in routes |
| `USE_DECOMPOSED_USE_CASE` | `False` | Enable refactored ReviewSubmissionUseCase | Toggle off restores monolithic implementation |

### Flag Configuration

Flags sourced from environment variables (operations.md §2 pattern):

```bash
# In ~/work/infra/.env.infra
USE_NEW_DIALOG_CONTEXT_REPO=false
USE_NEW_HOMEWORK_REVIEW_SERVICE=false
USE_NEW_STORAGE_ADAPTER=false
USE_DECOMPOSED_USE_CASE=false
```

### Flag Validation

Before enabling any flag:
```bash
# Check flag status
poetry run python scripts/ops/check_feature_flags.py --epic 21

# Expected output (Stage 21_00 complete, pre-21_01):
# USE_NEW_DIALOG_CONTEXT_REPO: False (safe to enable after ARCH-21-01)
# USE_NEW_HOMEWORK_REVIEW_SERVICE: False (safe to enable after ARCH-21-02)
# ...
```

---

## Stage-by-Stage Rollback Procedures

### Stage 21_00: Preparation

**What Changed**:
- Feature flags added to settings
- Baseline metrics collected
- Test infrastructure created

**Rollback Steps**:
1. No production changes; rollback not applicable
2. Clean up test infrastructure if needed:
   ```bash
   poetry run pytest tests/integration/shared_infra/test_shared_infra_connectivity.py --cleanup
   ```

**Rollback Duration**: N/A  
**Risk**: None (no production impact)

---

### Stage 21_01a: Dialog Context Repository

**What Changed**:
- `DialogContextRepository` interface added to `src/domain/interfaces/`
- `MongoDialogContextRepository` implemented in `src/infrastructure/repositories/`
- `ButlerOrchestrator` updated to accept `DialogContextRepository` via DI
- Feature flag `USE_NEW_DIALOG_CONTEXT_REPO` controls old vs new path

**Deployment State**:
```python
# Before rollout (flag=False)
ButlerOrchestrator(mongodb=mongo_client.butler)  # Direct Mongo access

# After rollout (flag=True)  
ButlerOrchestrator(context_repo=MongoDialogContextRepository(...))  # Interface
```

**Rollback Triggers**:
- Dialog context retrieval failures >5% (Prometheus alert)
- Average latency >500ms (was <100ms baseline)
- User reports of lost conversation history

**Rollback Steps**:

1. **Immediate Action** (within 5 minutes):
   ```bash
   # SSH to production host
   cd ~/work/infra
   
   # Toggle flag off
   echo "USE_NEW_DIALOG_CONTEXT_REPO=false" >> .env.infra
   
   # Restart affected services
   make day-12-restart-butler
   ```

2. **Validation** (within 10 minutes):
   ```bash
   # Check Prometheus metrics
   curl -s http://127.0.0.1:9090/api/v1/query?query=butler_dialog_errors_total
   
   # Expected: Error rate drops to baseline
   # If not, escalate to EP21 Tech Lead
   ```

3. **Post-Rollback** (within 1 hour):
   - Update incident log: `docs/specs/epic_21/architect/incident_log.md`
   - Notify stakeholders via `#ops-shared`
   - Schedule post-mortem within 48 hours
   - Block re-enabling flag until root cause fixed

**Data Integrity Check**:
- No data loss: Both old and new code write to same Mongo collections
- Verify: `db.dialog_contexts.count()` unchanged before/after rollback

**Rollback Duration**: 15 minutes  
**Risk**: Low (backward compatible, no schema changes)

---

### Stage 21_01b: Homework Review Service

**What Changed**:
- `HomeworkReviewService` interface added to `src/domain/interfaces/`
- `HWCheckerServiceAdapter` implemented in `src/application/services/`
- `HomeworkHandler` updated to accept service via DI
- Feature flag `USE_NEW_HOMEWORK_REVIEW_SERVICE` controls routing

**Rollback Triggers**:
- HW checker API call failures >10%
- Timeout errors on `/homework/list` endpoint
- User reports homework submissions not appearing

**Rollback Steps**:

1. **Immediate Action**:
   ```bash
   echo "USE_NEW_HOMEWORK_REVIEW_SERVICE=false" >> ~/work/infra/.env.infra
   make day-12-restart-workers  # Restart background workers
   ```

2. **Validation**:
   ```bash
   # Test homework listing
   poetry run python scripts/ops/test_homework_flow.py --student-id test_user
   
   # Expected: Lists commits successfully
   ```

3. **External Dependency Check**:
   ```bash
   # Verify HW checker API still accessible
   curl -s https://hw-checker.example.com/health
   
   # If down, coordinate with external team
   ```

**Rollback Duration**: 10 minutes  
**Risk**: Low (external API unchanged, only internal routing)

---

### Stage 21_01c: Storage Abstraction

**What Changed**:
- `ReviewArchiveStorage` interface added to `src/application/interfaces/`
- `LocalFileSystemStorage` implemented in `src/infrastructure/storage/`
- `review_routes.create_review` refactored to use storage adapter
- Feature flag `USE_NEW_STORAGE_ADAPTER` controls I/O path
- **Security additions**: Checksum validation, optional AV scan

**Rollback Triggers** (⚠️ Higher Risk):
- File write failures >2% (was 0% baseline)
- Checksum validation false positives
- Storage path permission errors
- Archive files missing or corrupted

**Rollback Steps**:

1. **Immediate Action**:
   ```bash
   echo "USE_NEW_STORAGE_ADAPTER=false" >> ~/work/infra/.env.infra
   make day-12-restart-api
   ```

2. **Critical Validation**:
   ```bash
   # Verify storage directories accessible
   ls -lah /var/butler/review_archives/
   
   # Check recent uploads (last 10 minutes)
   find /var/butler/review_archives/ -mmin -10 -type f
   
   # Validate checksum integrity
   poetry run python scripts/ops/validate_archive_checksums.py --recent 1h
   ```

3. **Data Recovery** (if needed):
   ```bash
   # If new adapter wrote to different location, copy back
   cp /var/butler/review_archives_new/* /var/butler/review_archives/
   
   # Restore permissions
   chown -R butler:butler /var/butler/review_archives/
   ```

4. **Security Audit** (within 24 hours):
   - Review logs for checksum failures: may indicate malicious uploads
   - Check AV scan logs if enabled
   - Coordinate with security team if suspicious activity detected

**Rollback Duration**: 20 minutes + data recovery time  
**Risk**: Medium (file I/O critical path, potential data loss if misconfigured)

---

### Stage 21_01d: Use Case Decomposition

**What Changed**:
- `ReviewSubmissionUseCase` split into collaborators:
  - `RateLimiter` (extracted)
  - `LogAnalysisPipeline` (extracted)
  - `ReportPublisher` (extracted)
- Feature flag `USE_DECOMPOSED_USE_CASE` controls orchestration path

**Rollback Triggers**:
- Review submission failures >5%
- Rate limit logic broken (unexpected 429 errors)
- Log analysis not appearing in reports
- Report publishing failures

**Rollback Steps**:

1. **Immediate Action**:
   ```bash
   echo "USE_DECOMPOSED_USE_CASE=false" >> ~/work/infra/.env.infra
   make day-12-restart-workers
   ```

2. **Validation**:
   ```bash
   # Submit test review
   poetry run pytest tests/integration/test_review_submission_flow.py -k test_full_pipeline
   
   # Check all components executed
   grep "rate_limit_check" var/logs/butler.log | tail -5
   grep "log_analysis_complete" var/logs/butler.log | tail -5
   grep "report_published" var/logs/butler.log | tail -5
   ```

3. **Component Health Check**:
   ```bash
   # Verify each collaborator independently
   poetry run python scripts/ops/check_use_case_components.py
   
   # Expected: All components return healthy
   # If specific component broken, may require code hotfix
   ```

**Rollback Duration**: 15 minutes  
**Risk**: Medium (affects core review pipeline, but backward compatible)

---

### Stage 21_02: Code Quality & Docstrings

**What Changed**:
- Function decomposition (oversized functions split)
- Docstrings updated to template format
- Lint toolchain configured (pre-commit, make lint)

**Rollback Triggers**:
- Regression in functionality after function splits
- Lint CI blocking valid merges
- Pre-commit hooks causing developer friction

**Rollback Steps**:

1. **Code Changes**:
   - Revert specific problematic commits via Git:
     ```bash
     git revert <commit-hash>  # Revert function decomposition
     git push origin main
     ```

2. **Tooling Changes**:
   ```bash
   # Disable pre-commit hooks temporarily
   pre-commit uninstall
   
   # Comment out strict lint rules in pyproject.toml
   # [tool.flake8]
   # max-line-length = 88
   # # ignore = E203,W503  # ← uncomment to relax
   ```

3. **CI Bypass** (emergency only):
   ```yaml
   # .github/workflows/ci.yml
   # Comment out lint job temporarily
   # lint:
   #   runs-on: ubuntu-latest
   #   steps: ...
   ```

**Rollback Duration**: 30 minutes (code revert) to 2 hours (full CI rollback)  
**Risk**: Low (quality improvements, minimal functional impact)

---

### Stage 21_03: Testing & Observability

**What Changed**:
- New test suites added for interfaces
- Prometheus metrics updated
- Grafana dashboards refreshed
- Security hardening (checksum, AV scan hooks)

**Rollback Triggers**:
- Test suite failures blocking CI
- Prometheus scrape errors
- Grafana dashboard data gaps
- False positive security alerts

**Rollback Steps**:

1. **Test Suite**:
   ```bash
   # Disable new tests temporarily
   pytest tests/ -m "not epic21"  # Requires marking new tests
   
   # Or skip specific modules
   pytest tests/ --ignore=tests/unit/test_dialog_context_repository.py
   ```

2. **Monitoring**:
   ```bash
   # Restore previous Prometheus config
   cd ~/work/infra/prometheus
   git checkout HEAD~1 prometheus.yml
   docker restart shared-prometheus
   
   # Restore Grafana dashboards
   cd ~/work/infra/grafana/dashboards
   git checkout HEAD~1 slo-*.json
   curl -X POST http://admin:${GRAFANA_PASSWORD}@127.0.0.1:3000/api/admin/provisioning/dashboards/reload
   ```

3. **Security Controls**:
   ```bash
   # Disable checksum validation if causing issues
   echo "STORAGE_ENFORCE_CHECKSUM=false" >> ~/work/infra/.env.infra
   
   # Disable AV scanning
   echo "STORAGE_AV_SCAN_ENABLED=false" >> ~/work/infra/.env.infra
   
   make day-12-restart-api
   ```

**Rollback Duration**: 20 minutes  
**Risk**: Low (observability changes, no direct functionality impact)

---

## Emergency Rollback (Full Epic)

**When to Use**: Critical production issue affecting multiple components, unclear which
stage caused the problem.

**Triggers**:
- System-wide unavailability >15 minutes
- Data corruption detected
- Security breach suspected
- Multiple component failures simultaneously

**Procedure**:

### Step 1: Disable All Feature Flags (2 minutes)

```bash
cd ~/work/infra
cat >> .env.infra <<EOF
# Epic 21 emergency rollback - $(date)
USE_NEW_DIALOG_CONTEXT_REPO=false
USE_NEW_HOMEWORK_REVIEW_SERVICE=false
USE_NEW_STORAGE_ADAPTER=false
USE_DECOMPOSED_USE_CASE=false
EOF

# Restart all services
make day-12-down
make day-12-up
```

### Step 2: Validate Core Functionality (5 minutes)

```bash
# Run smoke tests
poetry run pytest tests/smoke/ -v

# Check Prometheus targets
curl -s http://127.0.0.1:9090/api/v1/targets | jq '.data.activeTargets[] | select(.health=="down")'

# Verify Grafana dashboards loading
curl -s http://127.0.0.1:3000/api/health
```

### Step 3: Communications (10 minutes)

```markdown
# Post to #ops-shared
🚨 Epic 21 Emergency Rollback Initiated

**Reason**: [Brief description of issue]
**Action Taken**: All Epic 21 feature flags disabled, services restarted
**Current Status**: [System available/degraded/unavailable]
**ETA for Resolution**: [Within 1 hour / escalated to tech lead]
**Incident ID**: INC-2025-11-XXX
```

### Step 4: Git Revert (if flags insufficient)

```bash
# Revert all Epic 21 commits
git log --oneline --grep="ARCH-21\|CODE-21\|TEST-21\|SEC-21\|OBS-21" > /tmp/epic21_commits.txt

# Review commits to revert
cat /tmp/epic21_commits.txt

# Create revert branch
git checkout -b emergency-rollback-epic21
git revert <commit-hash-1> <commit-hash-2> ...  # Oldest to newest
git push origin emergency-rollback-epic21

# Merge via fast-track approval
# (requires EP21 Tech Lead authorization)
```

### Step 5: Post-Incident (within 48 hours)

- Schedule post-mortem meeting
- Document root cause in `docs/specs/epic_21/architect/incident_log.md`
- Update rollback plan with lessons learned
- Block Epic 21 rollout until fixes validated in staging

**Full Rollback Duration**: 30 minutes to 2 hours (depending on git revert scope)  
**Escalation**: If rollback doesn't restore service within 1 hour, escalate to EP21 Tech Lead + on-call architect

---

## Rollback Validation Checklist

After any rollback, validate these before declaring success:

### Functional Validation

- [ ] Core workflows operational:
  - [ ] Dialog handling (Telegram bot responds)
  - [ ] Homework submission (file upload succeeds)
  - [ ] Review generation (modular reviewer executes)
  - [ ] Channel management (digest delivery works)

### Data Integrity Validation

- [ ] MongoDB collections unchanged (counts match pre-rollback)
- [ ] File storage accessible (recent archives present)
- [ ] No orphaned data in new locations

### Observability Validation

- [ ] Prometheus metrics collecting (no stale targets)
- [ ] Grafana dashboards displaying data
- [ ] Loki logs flowing (check last 5 minutes)
- [ ] Alert thresholds not breached

### Security Validation

- [ ] No exposed credentials in logs (check rollback output)
- [ ] File permissions correct (`/var/butler/review_archives/` 750)
- [ ] API authentication working (test with valid token)

### Performance Validation

- [ ] Response times at baseline:
  - [ ] Dialog context retrieval <100ms
  - [ ] Review submission <30s
  - [ ] MCP tool discovery <1.5s
- [ ] No error rate spikes in Prometheus

---

## Testing Rollback Procedures

**Requirement**: All rollback procedures must be tested in staging before production
deployment.

### Staging Rollback Drills

Schedule rollback drills during Stage 21_00 (Preparation):

```bash
# Stage 21_00 task: Practice rollback
# 1. Deploy Stage 21_01a to staging
# 2. Enable feature flag
# 3. Execute rollback procedure (timed)
# 4. Validate checklist
# 5. Document deviations from plan

poetry run python scripts/ops/rollback_drill.py \
  --stage 21_01a \
  --environment staging \
  --record-metrics
```

### Rollback Drill Schedule

| Stage | Drill Date | Owner | Status |
|-------|-----------|-------|--------|
| 21_01a | Before prod deploy | DevOps | ⏳ Scheduled |
| 21_01b | Before prod deploy | DevOps | ⏳ Scheduled |
| 21_01c | Before prod deploy | DevOps + Security | ⏳ Scheduled |
| 21_01d | Before prod deploy | DevOps | ⏳ Scheduled |

---

## Rollback Authority Matrix

| Scenario | Authority | Approval Required | Communication |
|----------|-----------|-------------------|---------------|
| Single stage rollback (within 1 hour of deploy) | On-call Engineer | No (notify after) | #ops-shared post |
| Single stage rollback (>1 hour after deploy) | On-call Engineer | EP21 Tech Lead approval | #ops-shared + email stakeholders |
| Multi-stage rollback | EP21 Tech Lead | Operations Manager approval | Incident report + stakeholder meeting |
| Emergency full rollback | On-call Engineer (initiate) | EP21 Tech Lead (authorize git revert) | Immediate escalation |

---

## Rollback Metrics

Track these metrics for each rollback to improve procedures:

| Metric | Target | Measurement |
|--------|--------|-------------|
| Time to decision (issue detected → rollback initiated) | <15 minutes | Timestamp in incident log |
| Time to execute rollback | <30 minutes | Timestamp in incident log |
| Time to validate success | <15 minutes | Checklist completion time |
| Data loss incidents | 0 | Post-rollback data integrity check |
| Repeat rollbacks (same issue) | 0 | Incident log analysis |

---

## Lessons Learned Repository

After each rollback, document:

1. **What went well** (e.g., feature flags worked as expected)
2. **What could improve** (e.g., validation checklist incomplete)
3. **Action items** (e.g., add metric X to monitoring)

Store in: `docs/specs/epic_21/architect/rollback_lessons_learned.md`

---

## References

- **Operations Guide**: `docs/specs/operations.md` §5 (Maintenance Procedures)
- **Feature Flags**: Epic 01 `stage_01_01_feature_flag_inventory.md` (pattern reference)
- **Incident Response**: Epic 03 `alerting_runbook.md` (escalation flow)
- **Deployment Windows**: `docs/specs/operations.md` §5.1

---

**Document Owner**: EP21 Tech Lead  
**Last Updated**: 2025-11-11  
**Next Review**: After each stage deployment

