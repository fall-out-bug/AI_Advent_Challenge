# Cursor Agent Consensus - User Guide

## Quick Start (5 minutes)

### 1. Initial Setup
```bash
# Run setup script
chmod +x docs/roles/cursor_consensus/setup.sh
./docs/roles/cursor_consensus/setup.sh

# Create your first epic
./consensus/new_epic.sh EP-001 "Add health check endpoint"

# Check status
./consensus/status.sh
```

### 2. Open 6 Cursor Chat Windows
Arrange them in a grid or tabs for easy switching:
- **Chat 1**: Analyst
- **Chat 2**: Architect
- **Chat 3**: Tech Lead
- **Chat 4**: Developer
- **Chat 5**: Quality
- **Chat 6**: DevOps

### 3. Run Your First Consensus
Copy the prompt from `docs/roles/cursor_consensus/prompts/[agent]_prompt.md` into each chat window.

## Detailed Workflow

### Phase 1: Requirements & Architecture (Iteration 1)

#### Step 1: Analyst (Chat 1)
```markdown
1. Copy prompt from: docs/roles/cursor_consensus/prompts/analyst_prompt.md
2. Paste into Chat 1
3. Agent will create: consensus/artifacts/requirements.json
4. Check: ./consensus/status.sh
```

#### Step 2: Architect (Chat 2)
```markdown
1. Copy prompt from: docs/roles/cursor_consensus/prompts/architect_prompt.md
2. Paste into Chat 2
3. Agent reads requirements, may VETO if violations
4. Creates: consensus/artifacts/architecture.json
```

#### Step 3: Check for Vetoes
```bash
# See if any vetoes occurred
ls consensus/messages/inbox/*/veto_*.yaml 2>/dev/null

# If vetoes exist, read them:
cat consensus/messages/inbox/analyst/veto_*.yaml
```

### Phase 2: Planning (Iteration 1 or 2)

#### Step 4: Tech Lead (Chat 3)
```markdown
1. Only run after Architect approves
2. Copy prompt from: docs/roles/cursor_consensus/prompts/tech_lead_prompt.md
3. Creates: consensus/artifacts/plan.json
4. Breaks work into <4 hour tasks
```

### Phase 3: Implementation

#### Step 5: Developer (Chat 4)
```markdown
1. Only run after Tech Lead completes plan
2. Copy prompt from: docs/roles/cursor_consensus/prompts/developer_prompt.md
3. Implements according to plan
4. Creates: consensus/artifacts/implementation.json
```

### Phase 4: Verification

#### Step 6: Quality (Chat 5)
```markdown
1. Run after Developer completes
2. Copy prompt from: docs/roles/cursor_consensus/prompts/quality_prompt.md
3. Three-pass review
4. Creates: consensus/artifacts/review.json
```

#### Step 7: DevOps (Chat 6)
```markdown
1. Run after Quality approves
2. Copy prompt from: docs/roles/cursor_consensus/prompts/devops_prompt.md
3. Deployment planning
4. Creates: consensus/artifacts/deployment.json
```

## Handling Conflicts

### Iteration 2 (if needed)
If consensus not reached in iteration 1:

```bash
# 1. Update iteration
sed -i 's/iteration: 1/iteration: 2/' consensus/current/epic.yaml

# 2. Re-run conflicting agents with veto context
# Example: If Architect vetoed Analyst
```

In Analyst Chat:
```markdown
Previous iteration was vetoed. Check consensus/messages/inbox/analyst/ for veto details.
Revise requirements to address the architectural concern about [specific issue].
Update consensus/artifacts/requirements.json with fixes.
```

### Iteration 3 (final attempt)
If still no consensus:

```bash
# Check what's blocking
cat consensus/current/decision_log.jsonl | jq -r '.decision' | sort | uniq -c
```

Make a human decision:
1. Override the veto (rare)
2. Defer the epic
3. Split into smaller epics

## Tips for Efficient Operation

### 1. Parallel Execution
You can run non-dependent agents simultaneously:
- **Parallel Group 1**: Analyst → Architect (after Analyst)
- **Parallel Group 2**: Tech Lead (after Architect) + Quality prep
- **Sequential**: Developer → Quality → DevOps

### 2. Workspace Setup
```
┌─────────────────┬─────────────────┐
│                 │                 │
│  File Explorer  │  Terminal       │
│  (consensus/)   │  (status.sh)    │
│                 │                 │
├─────────────────┼─────────────────┤
│                 │                 │
│  Cursor Chat 1  │  Cursor Chat 2  │
│  (Analyst)      │  (Architect)    │
│                 │                 │
└─────────────────┴─────────────────┘
```

### 3. Quick Commands
Add to your `.bashrc` or `.zshrc`:
```bash
# Agent aliases
alias analyst="cat docs/roles/cursor_consensus/prompts/analyst_prompt.md | pbcopy && echo 'Analyst prompt copied!'"
alias architect="cat docs/roles/cursor_consensus/prompts/architect_prompt.md | pbcopy && echo 'Architect prompt copied!'"
alias techlead="cat docs/roles/cursor_consensus/prompts/tech_lead_prompt.md | pbcopy && echo 'Tech Lead prompt copied!'"
alias developer="cat docs/roles/cursor_consensus/prompts/developer_prompt.md | pbcopy && echo 'Developer prompt copied!'"
alias quality="cat docs/roles/cursor_consensus/prompts/quality_prompt.md | pbcopy && echo 'Quality prompt copied!'"
alias devops="cat docs/roles/cursor_consensus/prompts/devops_prompt.md | pbcopy && echo 'DevOps prompt copied!'"

# Consensus commands
alias cstatus="./consensus/status.sh"
alias cnew="./consensus/new_epic.sh"
alias cvetoes="find consensus/messages/inbox -name 'veto_*.yaml' -exec cat {} \;"
```

### 4. Monitoring Progress
Create a watch command:
```bash
# In a terminal, run:
watch -n 5 "./consensus/status.sh"
```

## Common Scenarios

### Scenario 1: Clean Approval (Happy Path)
```
Analyst → requirements.json
Architect → architecture.json (approved)
Tech Lead → plan.json
Developer → implementation.json
Quality → review.json (approved)
DevOps → deployment.json
```
**Time**: ~30-45 minutes

### Scenario 2: Architecture Veto
```
Analyst → requirements.json
Architect → VETO (layer violation)
[Iteration 2]
Analyst → requirements.json (revised)
Architect → architecture.json (approved)
... continues normally
```
**Time**: ~45-60 minutes

### Scenario 3: Quality Finds Issues
```
... implementation complete ...
Quality → review.json (changes_required)
Developer → implementation.json (fixes)
Quality → review.json (approved)
DevOps → deployment.json
```
**Time**: ~60-90 minutes

## Best Practices

### 1. Read Messages First
Always check inbox before running an agent:
```bash
ls consensus/messages/inbox/[agent]/*.yaml
```

### 2. Complete Iterations
Don't leave iterations half-done. Complete all agents for an iteration before moving to the next.

### 3. Document Deviations
If you manually override something, add to decision log:
```bash
echo '{"timestamp":"'$(date -Iseconds)'","agent":"human","decision":"override","epic_id":"EP-001","iteration":2,"details":{"reason":"time constraint"}}' >> consensus/current/decision_log.jsonl
```

### 4. Archive Completed Epics
```bash
# After epic completion
mkdir -p consensus/archive/EP-001
mv consensus/current/* consensus/archive/EP-001/
mv consensus/artifacts/* consensus/archive/EP-001/
```

## Troubleshooting

### Problem: Agent doesn't see files
**Solution**: Make sure you're in the workspace root directory, not in subdirectories.

### Problem: Agent creates wrong format
**Solution**: The prompt may need to be more specific. Add examples from this guide.

### Problem: Consensus taking too long
**Solution**: Check for circular vetoes:
```bash
grep veto consensus/current/decision_log.jsonl | tail -5
```

### Problem: Lost track of state
**Solution**: Run status to see where you are:
```bash
./consensus/status.sh
cat consensus/current/state.yaml
```

## Metrics to Track

Record these for process improvement:

| Metric | Target | How to Measure |
|--------|--------|----------------|
| Time to consensus | <60 min | Time from epic start to all approvals |
| Iterations needed | ≤2 | Count in decision_log.jsonl |
| Vetoes per epic | <2 | grep veto decision_log.jsonl |
| Agent response time | <5 min | Time to run each agent |
| Success rate | >80% | Epics completed / started |

## Advanced Usage

### Custom Veto Rules
Edit agent prompts to add domain-specific veto rules:
```yaml
# In architect_prompt.md, add:
CUSTOM VETO RULES:
- If API endpoint doesn't follow REST conventions
- If database access bypasses repository pattern
- If external service called from domain layer
```

### Batch Processing
Run multiple epics in sequence:
```bash
for epic in EP-001 EP-002 EP-003; do
    ./consensus/new_epic.sh $epic "Epic title"
    # Run agents...
    ./consensus/status.sh >> epic_results.log
done
```

### Integration with Git
Commit after each consensus:
```bash
git add consensus/
git commit -m "Consensus reached for EP-001"
git tag EP-001-consensus
```

## Support & Debugging

### Enable Debug Mode
Add to agent prompts:
```markdown
DEBUG MODE: Show your reasoning step by step.
Log every decision to decision_log.jsonl with detailed context.
```

### View Full History
```bash
# See all decisions for an epic
cat consensus/archive/EP-*/decision_log.jsonl | jq 'select(.epic_id=="EP-001")'

# See all vetoes
find consensus/archive -name "veto_*.yaml" -exec cat {} \;
```

### Reset Everything
```bash
rm -rf consensus/
./docs/roles/cursor_consensus/setup.sh
```

---

**Remember**: The system is designed for antagonistic consensus. Vetoes are good - they prevent problems. Trust the process.

**Questions?** Check `docs/roles/cursor_consensus/PROTOCOL.md` for detailed specifications.
