# Epic 21 · Deployment Checklist

**Purpose**: Step-by-step checklist for deploying Epic 21 stages to production, aligned
with `operations.md` maintenance procedures.

**Authority**: EP21 Tech Lead + On-call Engineer  
**Schedule**: Saturday 02:00–06:00 UTC (per operations.md §5.1)

---

## Pre-Deployment (Friday before deployment window)

### Planning & Communication

- [ ] **Deployment window confirmed** (Saturday 02:00–06:00 UTC)
- [ ] **Stakeholders notified** (ops chat `#ops-shared`, email to tech leads)
- [ ] **Change ticket created** (incident tracker: CHG-2025-11-XXX)
- [ ] **Rollback authority assigned** (EP21 Tech Lead or designated on-call engineer)
- [ ] **Emergency contact list updated** (phone numbers, escalation matrix)

### Technical Preparation

- [ ] **Staging deployment successful** (all tests pass, no issues for 48 hours)
- [ ] **Rollback drill completed** (tested in staging, timing documented)
- [ ] **Backups verified**:
  ```bash
  # MongoDB backup
  mongodump --uri="$MONGODB_URL" --out=/backup/epic21-pre-deploy-$(date +%Y%m%d)
  
  # Config snapshots
  cp ~/work/infra/.env.infra ~/work/infra/.env.infra.backup.$(date +%Y%m%d)
  cp ~/work/infra/prometheus/prometheus.yml ~/work/infra/prometheus/prometheus.yml.backup.$(date +%Y%m%d)
  ```

- [ ] **Feature flags verified** (all off by default):
  ```bash
  grep -E "USE_NEW_.*=false" ~/work/infra/.env.infra
  # Expected: All Epic 21 flags = false
  ```

- [ ] **Monitoring baselines captured**:
  ```bash
  # Save Prometheus metrics snapshot
  curl -s http://127.0.0.1:9090/api/v1/query?query=up > /tmp/prometheus_baseline_epic21.json
  
  # Save Grafana dashboard state
  curl -s http://admin:${GRAFANA_PASSWORD}@127.0.0.1:3000/api/dashboards/db/butler-slo \
    > /tmp/grafana_baseline_epic21.json
  ```

- [ ] **CI pipeline green** (all tests pass on main branch)
- [ ] **Security scan clean** (no new vulnerabilities):
  ```bash
  poetry run bandit src/ -r --severity-level medium
  ```

- [ ] **Documentation updated**:
  - [ ] `docs/specs/operations.md` reflects new services
  - [ ] `README.md` updated with Epic 21 changes
  - [ ] Runbooks updated (if monitoring changes)

---

## During Deployment Window (Saturday 02:00–06:00 UTC)

### Stage 21_00: Preparation

**Duration**: 15 minutes  
**Risk**: None (no production impact)

#### Checklist

- [ ] **Feature flag configuration added** to `.env.infra`:
  ```bash
  cat >> ~/work/infra/.env.infra <<EOF
  # Epic 21 feature flags (added $(date))
  USE_NEW_DIALOG_CONTEXT_REPO=false
  USE_NEW_HOMEWORK_REVIEW_SERVICE=false
  USE_NEW_STORAGE_ADAPTER=false
  USE_DECOMPOSED_USE_CASE=false
  EOF
  ```

- [ ] **Baseline metrics collected**:
  ```bash
  poetry run python scripts/ops/collect_baseline_metrics.py --epic 21 --output /tmp/epic21_baseline.json
  ```

- [ ] **Test infrastructure validated**:
  ```bash
  poetry run pytest tests/integration/shared_infra/test_shared_infra_connectivity.py -v
  # Expected: All pass
  ```

- [ ] **Services restarted** (to load new feature flags):
  ```bash
  cd ~/work/infra
  make day-12-restart-all
  ```

- [ ] **Validate no impact** (all services healthy):
  ```bash
  # Prometheus targets
  curl -s http://127.0.0.1:9090/api/v1/targets | jq '.data.activeTargets[] | select(.health=="down")'
  # Expected: No down targets
  
  # Grafana dashboards
  curl -s http://127.0.0.1:3000/api/health
  # Expected: {"database":"ok","version":"..."}
  ```

#### Exit Gate

- [ ] All feature flags present and set to `false`
- [ ] Services running normally (no error spike in logs)
- [ ] Baseline metrics captured

---

### Stage 21_01a: Dialog Context Repository

**Duration**: 30 minutes  
**Risk**: Medium (affects dialog persistence)

#### Pre-Flight Checks

- [ ] **Characterization tests pass in production environment** (staging):
  ```bash
  poetry run pytest tests/characterization/test_butler_orchestrator_dialog_context.py -v
  ```

- [ ] **Rollback plan reviewed** (`docs/specs/epic_21/architect/rollback_plan.md`)

#### Deploy Code

- [ ] **Merge deployment PR** (contains interface + adapter + orchestrator changes)
- [ ] **Deploy to production**:
  ```bash
  cd ~/studies/AI_Challenge
  git pull origin main
  poetry install --no-dev
  ```

- [ ] **Restart services**:
  ```bash
  cd ~/work/infra
  make day-12-restart-butler
  ```

#### Gradual Rollout

- [ ] **Validate with feature flag off** (old behavior):
  ```bash
  # Send test message to Butler bot
  poetry run python scripts/ops/test_butler_dialog.py --user-id test_user --message "Hello"
  # Expected: Response received, no errors
  
  # Check Mongo collections (old direct access still working)
  poetry run python scripts/ops/check_mongo_collections.py --collection dialog_contexts
  # Expected: Documents present
  ```

- [ ] **Enable feature flag** (new behavior):
  ```bash
  sed -i 's/USE_NEW_DIALOG_CONTEXT_REPO=false/USE_NEW_DIALOG_CONTEXT_REPO=true/' ~/work/infra/.env.infra
  make day-12-restart-butler
  ```

- [ ] **Smoke test with flag on**:
  ```bash
  # Send test message (should use new repository)
  poetry run python scripts/ops/test_butler_dialog.py --user-id test_user_flag_on --message "Testing new repo"
  
  # Verify context saved via repository
  poetry run python scripts/ops/check_dialog_context_repo.py --session-id <session_from_test>
  # Expected: Context retrieved successfully
  ```

#### Monitor for 15 Minutes

- [ ] **Watch Prometheus metrics**:
  ```promql
  # Error rate (should be zero)
  rate(dialog_context_repository_operations_total{status="error"}[5m])
  
  # Latency (should be <100ms p95)
  histogram_quantile(0.95, rate(dialog_context_repository_latency_seconds_bucket[5m]))
  ```

- [ ] **Check application logs**:
  ```bash
  docker logs butler-bot --since 15m | grep -E "ERROR|WARN"
  # Expected: No new errors related to dialog context
  ```

- [ ] **User-facing validation** (manual test in Telegram):
  - [ ] Send message to Butler bot
  - [ ] Verify response
  - [ ] Check conversation history maintained

#### Exit Gate

- [ ] Feature flag enabled successfully
- [ ] No error rate increase (Prometheus)
- [ ] Latency within SLO (<100ms p95)
- [ ] Manual validation successful
- [ ] **If any check fails** → Execute rollback (see rollback_plan.md §21_01a)

---

### Stage 21_01b: Homework Review Service

**Duration**: 25 minutes  
**Risk**: Low (external API, isolated component)

#### Deploy Code

- [ ] **Merge deployment PR**
- [ ] **Deploy to production**:
  ```bash
  cd ~/studies/AI_Challenge
  git pull origin main
  poetry install --no-dev
  make day-12-restart-workers
  ```

#### Gradual Rollout

- [ ] **Validate with flag off**:
  ```bash
  poetry run python scripts/ops/test_homework_flow.py --student-id test_user
  # Expected: Lists commits, old HWCheckerClient path
  ```

- [ ] **Enable feature flag**:
  ```bash
  sed -i 's/USE_NEW_HOMEWORK_REVIEW_SERVICE=false/USE_NEW_HOMEWORK_REVIEW_SERVICE=true/' ~/work/infra/.env.infra
  make day-12-restart-workers
  ```

- [ ] **Smoke test with flag on**:
  ```bash
  poetry run python scripts/ops/test_homework_flow.py --student-id test_user_flag_on --request-review
  # Expected: Review requested successfully via new service
  ```

#### Monitor for 10 Minutes

- [ ] **Prometheus metrics**:
  ```promql
  rate(homework_review_service_requests_total{status="error"}[5m])
  histogram_quantile(0.95, rate(homework_review_service_latency_seconds_bucket[5m]))
  ```

- [ ] **External API health**:
  ```bash
  curl -s https://hw-checker.example.com/health
  # Expected: {"status":"ok"}
  ```

#### Exit Gate

- [ ] No increase in HW checker errors
- [ ] Latency <2s (p95)
- [ ] Manual homework submission tested

---

### Stage 21_01c: Storage Abstraction

**Duration**: 45 minutes (⚠️ Critical)  
**Risk**: High (data integrity, security-sensitive)

#### Pre-Flight Checks

- [ ] **Storage directories prepared**:
  ```bash
  sudo mkdir -p /var/butler/review_archives/
  sudo chown butler:butler /var/butler/review_archives/
  sudo chmod 750 /var/butler/review_archives/
  ```

- [ ] **Checksum validation tested in staging**
- [ ] **AV scan hook configured** (if enabled):
  ```bash
  grep "STORAGE_AV_SCAN_ENABLED" ~/work/infra/.env.infra
  # If true, verify ClamAV running
  systemctl status clamav-daemon
  ```

#### Deploy Code

- [ ] **Merge deployment PR**
- [ ] **Deploy to production**:
  ```bash
  cd ~/studies/AI_Challenge
  git pull origin main
  poetry install --no-dev
  make day-12-restart-api
  ```

#### Gradual Rollout (⚠️ Extra Caution)

- [ ] **Validate with flag off**:
  ```bash
  # Upload test archive (old path)
  poetry run python scripts/ops/test_review_upload.py --student-id test_user --assignment-id hw01
  
  # Verify file in old location
  ls -lh /var/butler/review_archives/ | grep hw01
  ```

- [ ] **Enable feature flag**:
  ```bash
  sed -i 's/USE_NEW_STORAGE_ADAPTER=false/USE_NEW_STORAGE_ADAPTER=true/' ~/work/infra/.env.infra
  make day-12-restart-api
  ```

- [ ] **Smoke test with flag on**:
  ```bash
  # Upload test archive (new adapter)
  poetry run python scripts/ops/test_review_upload.py --student-id test_user_flag_on --assignment-id hw02
  
  # Verify:
  # 1. File saved
  ls -lh /var/butler/review_archives/ | grep hw02
  
  # 2. Checksum recorded
  poetry run python scripts/ops/check_archive_checksum.py --assignment hw02
  # Expected: Checksum matches calculated value
  
  # 3. Metadata persisted
  poetry run python scripts/ops/check_archive_metadata.py --assignment hw02
  # Expected: Size, checksum, upload timestamp present
  ```

#### Security Validation

- [ ] **Test checksum rejection**:
  ```bash
  # Upload file, then tamper with it
  poetry run python scripts/ops/test_corrupted_archive.py
  # Expected: Upload rejected, error logged
  ```

- [ ] **Test path traversal blocking**:
  ```bash
  poetry run python scripts/ops/test_path_traversal.py
  # Expected: Blocked, security event logged
  ```

- [ ] **Test oversized file rejection**:
  ```bash
  poetry run python scripts/ops/test_oversized_archive.py --size 150MB
  # Expected: Rejected with 413 error
  ```

#### Monitor for 20 Minutes

- [ ] **Prometheus metrics**:
  ```promql
  rate(review_archive_storage_operations_total{status="error"}[5m])
  review_archive_storage_checksum_failures_total
  ```

- [ ] **Check logs for security events**:
  ```bash
  docker logs butler-api --since 20m | grep -E "checksum_failed|path_traversal|av_scan_reject"
  # Expected: No unexpected security events
  ```

- [ ] **Disk usage**:
  ```bash
  df -h /var/butler/
  # Expected: Sufficient space (>10GB free)
  ```

#### Exit Gate

- [ ] No file write errors
- [ ] Checksum validation working
- [ ] Security tests pass
- [ ] Disk usage normal
- [ ] **If any check fails** → Execute rollback immediately

---

### Stage 21_01d: Use Case Decomposition

**Duration**: 30 minutes  
**Risk**: Medium (core review pipeline)

#### Deploy Code

- [ ] **Merge deployment PR**
- [ ] **Deploy to production**:
  ```bash
  cd ~/studies/AI_Challenge
  git pull origin main
  poetry install --no-dev
  make day-12-restart-workers
  ```

#### Gradual Rollout

- [ ] **Validate with flag off**:
  ```bash
  # Submit test review (old monolithic use case)
  poetry run python scripts/ops/test_review_submission.py --student-id test_user --assignment hw03
  
  # Verify:
  # - Rate limit checked
  # - Log analysis appended
  # - Report persisted
  # - Report published
  ```

- [ ] **Enable feature flag**:
  ```bash
  sed -i 's/USE_DECOMPOSED_USE_CASE=false/USE_DECOMPOSED_USE_CASE=true/' ~/work/infra/.env.infra
  make day-12-restart-workers
  ```

- [ ] **Smoke test with flag on**:
  ```bash
  poetry run python scripts/ops/test_review_submission.py --student-id test_user_flag_on --assignment hw04
  
  # Verify all components executed (check structured logs)
  ```

#### Monitor for 15 Minutes

- [ ] **Prometheus metrics**:
  ```promql
  rate(review_submission_use_case_errors_total[5m])
  histogram_quantile(0.95, rate(review_submission_duration_seconds_bucket[5m]))
  review_submission_rate_limit_hits_total
  ```

- [ ] **Component health**:
  ```bash
  # Verify each collaborator operational
  poetry run python scripts/ops/check_use_case_components.py
  # Expected: RateLimiter, LogAnalysisPipeline, ReportPublisher all healthy
  ```

#### Exit Gate

- [ ] No errors in review pipeline
- [ ] All collaborators operational
- [ ] End-to-end latency <30s (p95)
- [ ] Manual review submission tested

---

## Post-Deployment (Within 1 Hour After Window)

### Validation

- [ ] **Run full smoke test suite**:
  ```bash
  poetry run pytest tests/smoke/ -v
  # Expected: All pass
  ```

- [ ] **Check Prometheus alerts** (no new firing alerts):
  ```bash
  curl -s http://127.0.0.1:9090/api/v1/alerts | jq '.data.alerts[] | select(.state=="firing")'
  # Expected: Empty or only pre-existing alerts
  ```

- [ ] **Verify Grafana dashboards** (data flowing, no gaps):
  - Open http://127.0.0.1:3000
  - Check "Butler SLO" dashboard
  - Verify metrics updated in last 5 minutes

- [ ] **Check Loki logs** (no error spikes):
  ```bash
  # Query Loki for errors
  curl -G -s "http://127.0.0.1:3100/loki/api/v1/query" \
    --data-urlencode 'query={stream="butler"} |= "ERROR"' \
    --data-urlencode 'start=1h' \
    | jq '.data.result | length'
  # Expected: Low count (baseline level)
  ```

- [ ] **User-facing validation** (manual tests):
  - [ ] Send message to Butler bot → Response received
  - [ ] Upload homework submission → Review generated
  - [ ] Check digest delivery → Digest sent
  - [ ] Query channel info → Data returned

### Documentation

- [ ] **Update deployment log** (`docs/specs/epic_21/architect/deployment_log.md`):
  ```markdown
  ## Deployment: 2025-11-XX Stage 21_01a-d
  
  - **Date**: 2025-11-XX 02:00–04:30 UTC
  - **Duration**: 2h 30min (planned: 2h 10min)
  - **Issues**: None / [Description if any]
  - **Rollbacks**: None / [Details if any]
  - **Deployed by**: [Name]
  - **Validated by**: [Name]
  ```

- [ ] **Post to `#ops-shared`**:
  ```markdown
  ✅ Epic 21 Stage 21_01 Deployment Complete
  
  - All feature flags enabled successfully
  - No errors detected in monitoring
  - Smoke tests pass
  - User-facing validation successful
  
  **Next deployment**: Stage 21_02 (planned: 2025-11-XX)
  ```

### Backup Cleanup

- [ ] **Retain backups for 7 days**:
  ```bash
  # Backups in /backup/epic21-pre-deploy-YYYYMMDD
  # Auto-cleanup via cron or manual after 7 days if all stable
  ```

---

## Post-Deployment (Within 24 Hours)

### Monitoring Review

- [ ] **Review Prometheus metrics** (compare to baseline):
  ```bash
  poetry run python scripts/ops/compare_metrics.py \
    --baseline /tmp/epic21_baseline.json \
    --current http://127.0.0.1:9090
  
  # Expected: No significant regressions
  ```

- [ ] **Check for anomalies** (unexpected patterns):
  - [ ] Error rate stable or decreased
  - [ ] Latency within SLO
  - [ ] Resource usage (CPU, memory, disk) normal

### Stakeholder Communication

- [ ] **Send deployment summary email**:
  ```markdown
  Subject: Epic 21 Stage 21_01 Deployment Summary
  
  Stakeholders,
  
  Epic 21 Stage 21_01 (Architecture & Layering Remediation) was successfully
  deployed on 2025-11-XX during the scheduled maintenance window.
  
  **What Changed**:
  - Dialog context repository abstraction
  - Homework review service interface
  - Storage adapter with security hardening
  - Use case decomposition (collaborators)
  
  **Results**:
  - No errors or rollbacks required
  - All SLOs maintained
  - User-facing functionality validated
  
  **Next Steps**:
  - Monitor for 7 days before Stage 21_02
  - Collect feedback from ops team
  
  Details: docs/specs/epic_21/architect/deployment_log.md
  
  Thanks,
  EP21 Tech Lead
  ```

### Retrospective (Scheduled Within 48 Hours)

- [ ] **Schedule retro meeting** (30 minutes)
- [ ] **Agenda**:
  - What went well?
  - What could be improved?
  - Action items for next deployment

---

## Rollback Trigger Checklist

If any of these occur during deployment, **initiate rollback immediately**:

- [ ] Error rate >5% for any component
- [ ] Latency >2x baseline (e.g., dialog context >200ms)
- [ ] Data corruption detected (checksum failures, missing files)
- [ ] Security incident (path traversal, unauthorized access)
- [ ] Services fail to restart after flag enable
- [ ] User-facing functionality broken (manual test fails)
- [ ] Prometheus alerts firing (new, not pre-existing)

**Rollback Procedure**: See `docs/specs/epic_21/architect/rollback_plan.md`

---

## Special Considerations

### If Deployment Window Overruns

- **Plan**: 4 hours allocated (02:00–06:00 UTC)
- **If exceed 06:00**: 
  - Pause deployment
  - Assess risk of continuing vs rolling back
  - Notify stakeholders of delay
  - Get approval from EP21 Tech Lead to continue or rollback

### If Partial Failure

- **Example**: Stage 21_01a succeeds, but 21_01b fails
- **Action**:
  - Keep successful stages enabled (if stable)
  - Rollback failed stage only
  - Reschedule failed stage for next window
  - Document dependencies (does 21_01c depend on 21_01b?)

### If External Dependency Down

- **Example**: HW checker API unavailable during 21_01b deployment
- **Action**:
  - Skip 21_01b (keep feature flag off)
  - Continue with 21_01c and 21_01d (if independent)
  - Reschedule 21_01b when external service stable

---

## Acceptance Criteria

Deployment considered successful if:

- [ ] All planned stages deployed without rollback
- [ ] All feature flags enabled successfully
- [ ] No error rate increase in Prometheus
- [ ] Latency within SLOs
- [ ] Security validations pass
- [ ] User-facing functionality tested and working
- [ ] Monitoring dashboards updated and displaying data
- [ ] Stakeholders notified of completion
- [ ] Deployment log updated

---

## References

- **Operations Guide**: `docs/specs/operations.md` §5 (Maintenance Procedures)
- **Rollback Plan**: `docs/specs/epic_21/architect/rollback_plan.md`
- **Testing Strategy**: `docs/specs/epic_21/architect/testing_strategy.md`
- **Monitoring**: Epic 03 `alerting_runbook.md`

---

**Document Owner**: EP21 Tech Lead + DevOps  
**Last Updated**: 2025-11-11  
**Next Review**: After each deployment (lessons learned)

