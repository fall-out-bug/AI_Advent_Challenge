# Cursor Agent Consensus Protocol v1.0
## File-Based Communication for Manual Orchestration

## Overview
This protocol enables consensus between Cursor agents using shared files, with manual user orchestration between separate chat windows.

## Directory Structure
```
workspace/
├── consensus/
│   ├── current/
│   │   ├── epic.json          # Current epic definition
│   │   ├── state.json         # Current consensus state
│   │   └── decision_log.jsonl # Decision history (append-only)
│   ├── messages/
│   │   ├── inbox/             # Incoming messages (msg_*.json)
│   │   │   ├── analyst/
│   │   │   ├── architect/
│   │   │   ├── tech_lead/
│   │   │   ├── developer/
│   │   │   ├── quality/
│   │   │   └── devops/
│   │   └── processed/         # Archived messages after reading
│   └── artifacts/
│       ├── requirements.json  # Analyst output
│       ├── architecture.json  # Architect output
│       ├── plan.json          # Tech Lead output
│       ├── implementation.json# Developer output
│       ├── review.json        # Quality output
│       └── deployment.json    # DevOps output
```

## Communication Flow

### Step 1: Initialize Epic
User creates initial epic file:
```json
// consensus/current/epic.json
{
  "epic_id": "EP-001",
  "title": "Add health check endpoint",
  "status": "requirements_gathering",
  "iteration": 1,
  "max_iterations": 3
}
```

### Step 2: Agent Reads State
Each agent starts by reading:
1. `consensus/current/epic.json` - Current task
2. `consensus/current/state.json` - Current consensus state
3. `consensus/messages/inbox/[agent]/` - Messages for them
4. `consensus/artifacts/` - Other agents' outputs

### Step 3: Agent Writes Response
Agent writes to their designated locations:
1. `consensus/artifacts/[output].json` - Their main deliverable
2. `consensus/messages/inbox/[target]/msg_[timestamp].json` - Messages to other agents
3. `consensus/current/decision_log.jsonl` - Log their decision

### Step 4: User Updates State
After each agent run, user updates:
```json
// consensus/current/state.json
{
  "iteration": 1,
  "phase": "requirements",
  "agents_completed": {
    "analyst": "approved",
    "architect": "pending",
    "tech_lead": "pending"
  },
  "consensus_status": "in_progress",
  "conflicts": []
}
```

## Message Format

### Agent-to-Agent Message
```json
// consensus/messages/inbox/architect/msg_001.json
{
  "header": {
    "id": "msg-001",
    "from": "analyst",
    "to": "architect",
    "timestamp": "2024-11-19T10:30:00Z",
    "epic_id": "EP-001",
    "iteration": 1,
    "type": "request"
  },
  "body": {
    "subject": "requirements_ready",
    "summary": "Health check endpoint needed",
    "key_points": [
      "User story: uptime visibility",
      "ROI: 2 hours implementation"
    ],
    "concerns": [
      "Must not impact existing endpoints",
      "Should follow REST conventions"
    ],
    "action_needed": "review_and_design_architecture"
  }
}
```

### Veto Message
```json
// consensus/messages/inbox/analyst/msg_002.json
{
  "header": {
    "id": "msg-002",
    "from": "architect",
    "to": "analyst",
    "timestamp": "2024-11-19T10:45:00Z",
    "epic_id": "EP-001",
    "iteration": 1,
    "type": "veto"
  },
  "body": {
    "subject": "layer_violation",
    "summary": "Health check proposed inside domain layer",
    "key_points": [
      "Infrastructure boundary must expose health endpoint",
      "Domain layer must remain pure"
    ],
    "concerns": [
      "Breaks Clean Architecture isolation"
    ],
    "action_needed": "revise_requirements"
  }
}
```

## Decision Log Format
```json
// consensus/current/decision_log.jsonl (one JSON object per line)
{"timestamp":"2024-11-19T10:30:00Z","agent":"analyst","decision":"propose","epic_id":"EP-001","iteration":1,"details":{"requirements_complete":true}}
{"timestamp":"2024-11-19T10:45:00Z","agent":"architect","decision":"veto","epic_id":"EP-001","iteration":1,"details":{"reason":"layer_violation"}}
```

## User Orchestration Workflow

### 1. Start New Epic
```bash
# Create epic file
cat <<'EOF' > consensus/current/epic.json
{
  "epic_id": "EP-001",
  "title": "Your epic title",
  "status": "requirements_gathering",
  "iteration": 1,
  "max_iterations": 3
}
EOF

# Clear previous artifacts
rm -f consensus/artifacts/*
rm -f consensus/messages/inbox/*/*
```

### 2. Run Analyst Agent
Open Cursor Chat #1:
```
@analyst Look at consensus/current/epic.json and create requirements.
Write output to consensus/artifacts/requirements.json
Send any messages to consensus/messages/inbox/[agent]/ as msg_<timestamp>.json
Log decision to consensus/current/decision_log.jsonl
```

### 3. Run Architect Agent
Open Cursor Chat #2:
```
@architect Review consensus/artifacts/requirements.json
Check consensus/messages/inbox/architect/ for messages
Create architecture in consensus/artifacts/architecture.json
Send feedback to consensus/messages/inbox/analyst/ if needed
```

### 4. Check for Consensus
```bash
# Count approvals vs vetoes
grep "veto" consensus/current/decision_log.jsonl | wc -l
grep "approve" consensus/current/decision_log.jsonl | wc -l
```

### 5. Handle Conflicts
If conflicts exist, run iteration 2:
```bash
# Update state for iteration 2
tmp=$(mktemp)
jq '.iteration = 2' consensus/current/state.json > "$tmp"
mv "$tmp" consensus/current/state.json

# Re-run conflicting agents with context of vetoes
```

## Agent Prompt Templates

### Analyst Template
```markdown
You are the ANALYST agent. Your epic is in consensus/current/epic.json.

1. Read the epic definition
2. Check consensus/messages/inbox/analyst/ for any feedback (msg_*.json files)
3. Create requirements in consensus/artifacts/requirements.json:
   - user_story (max 200 chars)
   - acceptance_criteria (list)
   - out_of_scope (list)
4. Send messages to other agents in consensus/messages/inbox/[agent]/
5. Log your decision to consensus/current/decision_log.jsonl

Focus on business value and minimal intervention.
```

### Architect Template
```markdown
You are the ARCHITECT agent.

1. Read consensus/artifacts/requirements.json
2. Check consensus/messages/inbox/architect/ for messages
3. Verify Clean Architecture compliance
4. Create architecture in consensus/artifacts/architecture.json:
   - components (with layers)
   - boundaries
   - contracts
5. VETO if layer violations detected (send to inbox/analyst/)
6. Log decision to consensus/current/decision_log.jsonl

Never compromise on Clean Architecture.
```

## Consensus Rules

### Automatic Approval Conditions
- No vetoes in current iteration
- All required agents have responded
- Core artifacts exist (requirements, architecture, plan)

### Automatic Escalation Triggers
- Iteration 3 reached without consensus
- Same veto repeated twice
- Circular dependencies detected

### Veto Priority
1. **Architecture violations** (architect) - Cannot override
2. **Security issues** (quality) - Cannot override
3. **No rollback plan** (devops) - Cannot override
4. **Untestable requirements** (tech_lead) - Can negotiate
5. **Scope creep** (analyst) - Can negotiate

## Quick Commands for User

### Check Current State
```bash
# See current iteration and phase
jq '{iteration, phase}' consensus/current/state.json

# Count messages pending
find consensus/messages/inbox -name "*.json" | wc -l

# View recent decisions
tail -5 consensus/current/decision_log.jsonl | jq '.'
```

### Move to Next Phase
```bash
# Archive processed messages
mv consensus/messages/inbox/*/*.json consensus/messages/processed/

# Increment iteration
tmp=$(mktemp)
jq '.iteration += 1' consensus/current/epic.json > "$tmp"
mv "$tmp" consensus/current/epic.json
```

### Reset for New Epic
```bash
# Archive current epic
mkdir -p consensus/archive/EP-001
mv consensus/current/* consensus/archive/EP-001/
mv consensus/artifacts/* consensus/archive/EP-001/

# Start fresh
cat <<'EOF' > consensus/current/epic.json
{
  "epic_id": "EP-002",
  "title": "Next epic title",
  "status": "requirements_gathering",
  "iteration": 1,
  "max_iterations": 3
}
EOF
```

## Example Consensus Flow

### Iteration 1
1. User: Creates epic.json
2. User: Runs Analyst → requirements.json
3. User: Runs Architect → VETO (layer violation)
4. User: Checks messages, sees veto

### Iteration 2
1. User: Updates epic.json (iteration: 2)
2. User: Runs Analyst with veto context → revised requirements
3. User: Runs Architect → architecture.json (approved)
4. User: Runs Tech Lead → plan.json
5. User: All approve → consensus reached

### Implementation
1. User: Runs Developer → implementation.json
2. User: Runs Quality → review.json
3. User: Runs DevOps → deployment.json
4. User: Epic complete

## Tips for Efficient Operation

1. **Use Split Terminal**:
   - Left: File explorer showing consensus/
   - Right: Terminal for commands

2. **Agent Shortcuts**: Create aliases
   ```bash
   alias run-analyst="cursor --chat 'Load analyst role from docs/roles/analyst/'"
   alias check-consensus="jq '{iteration,phase,consensus_status}' consensus/current/state.json"
   ```

3. **Message Templates**: Pre-create message templates
   ```bash
   # Create veto template
   cat <<'EOF' > consensus/messages/inbox/analyst/veto_template.json
   {
     "header": {
       "id": "msg-template",
       "from": "architect",
       "to": "analyst",
       "epic_id": "",
       "iteration": 0,
       "type": "veto",
       "timestamp": ""
     },
     "body": {
       "subject": "layer_violation",
       "summary": "",
       "key_points": [],
       "concerns": [],
       "action_needed": "revise_requirements"
     }
   }
   EOF
   ```

4. **Batch Operations**: Run related agents together
   - Morning: Analyst + Architect
   - Afternoon: Tech Lead + Developer
   - Evening: Quality + DevOps

## Monitoring Consensus Progress

### Visual Indicator Script
```bash
#!/bin/bash
# consensus_status.sh

echo "=== CONSENSUS STATUS ==="
echo "Epic: $(jq -r '.epic_id' consensus/current/epic.json)"
echo "Iteration: $(jq -r '.iteration' consensus/current/epic.json)"
echo ""
echo "Decisions:"
tail -3 consensus/current/decision_log.jsonl | jq -r '"\(.agent): \(.decision)"'
echo ""
echo "Pending Messages:"
find consensus/messages/inbox -name "*.json" -exec basename {} \; | head -5
```

## Success Metrics

Track these manually:
- Time to consensus (iterations × time per iteration)
- Number of vetoes per epic
- Agent response time (when you run each)
- File size growth in artifacts/

---

**Version**: 1.0
**Status**: Ready for Use
**Workflow**: Manual with File-Based Communication
