#!/bin/bash
# Cursor Agent Consensus - Setup Script
# Run this to initialize the consensus directory structure

echo "Setting up Cursor Agent Consensus System..."

# Create directory structure
mkdir -p consensus/current
mkdir -p consensus/messages/inbox/{analyst,architect,tech_lead,developer,quality,devops}
mkdir -p consensus/messages/processed
mkdir -p consensus/artifacts
mkdir -p consensus/archive
mkdir -p consensus/templates

# Create initial state file
cat > consensus/current/state.yaml << 'EOF'
iteration: 1
phase: requirements_gathering
agents_completed: []
consensus_status: not_started
conflicts: []
last_updated: $(date -Iseconds)
EOF

# Create empty decision log
touch consensus/current/decision_log.jsonl

# Create message template
cat > consensus/templates/message_template.yaml << 'EOF'
from: AGENT_NAME
to: TARGET_AGENT
timestamp: TIMESTAMP
epic_id: EPIC_ID
iteration: ITERATION

type: request  # request|response|veto|approve
subject: SUBJECT_HERE

content:
  summary: "Brief description"
  details: []
  concerns: []

action_needed: WHAT_TARGET_SHOULD_DO
EOF

# Create veto template
cat > consensus/templates/veto_template.yaml << 'EOF'
from: AGENT_NAME
to: TARGET_AGENT
timestamp: TIMESTAMP
epic_id: EPIC_ID
iteration: ITERATION

type: veto
subject: VIOLATION_TYPE

content:
  violation: "Specific violation description"
  requirement: "What needs to be fixed"
  blocking: true

action_needed: FIX_REQUIRED
EOF

# Create approval template
cat > consensus/templates/approval_template.yaml << 'EOF'
from: AGENT_NAME
to: broadcast
timestamp: TIMESTAMP
epic_id: EPIC_ID
iteration: ITERATION

type: approve
subject: DELIVERABLE_APPROVED

content:
  approved_artifact: "ARTIFACT_NAME"
  conditions_met:
    - "Condition 1"
    - "Condition 2"
  notes: "Additional notes"

action_needed: none
EOF

# Create quick status script
cat > consensus/status.sh << 'EOF'
#!/bin/bash
echo "=== CONSENSUS STATUS ==="
echo "Epic: $(grep epic_id consensus/current/epic.yaml 2>/dev/null || echo 'No epic defined')"
echo "Iteration: $(grep iteration consensus/current/epic.yaml 2>/dev/null || echo 'N/A')"
echo "Phase: $(grep phase consensus/current/state.yaml 2>/dev/null || echo 'N/A')"
echo ""
echo "=== Recent Decisions ==="
if [ -f consensus/current/decision_log.jsonl ]; then
    tail -3 consensus/current/decision_log.jsonl 2>/dev/null | while read line; do
        echo $line | python3 -c "import sys, json; d=json.loads(sys.stdin.read()); print(f\"{d['agent']}: {d['decision']}\")" 2>/dev/null
    done
else
    echo "No decisions yet"
fi
echo ""
echo "=== Pending Messages ==="
for dir in consensus/messages/inbox/*/; do
    agent=$(basename "$dir")
    count=$(find "$dir" -name "*.yaml" 2>/dev/null | wc -l)
    if [ $count -gt 0 ]; then
        echo "  $agent: $count message(s)"
    fi
done
echo ""
echo "=== Artifacts Created ==="
ls -1 consensus/artifacts/ 2>/dev/null | head -5 || echo "  None yet"
EOF

chmod +x consensus/status.sh

# Create helper script for starting new epic
cat > consensus/new_epic.sh << 'EOF'
#!/bin/bash
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: ./new_epic.sh <EPIC_ID> <TITLE>"
    echo "Example: ./new_epic.sh EP-001 'Add health check endpoint'"
    exit 1
fi

EPIC_ID=$1
TITLE=$2

# Archive previous epic if exists
if [ -f consensus/current/epic.yaml ]; then
    OLD_EPIC=$(grep epic_id consensus/current/epic.yaml | cut -d: -f2 | tr -d ' ')
    if [ ! -z "$OLD_EPIC" ]; then
        echo "Archiving previous epic: $OLD_EPIC"
        mkdir -p consensus/archive/$OLD_EPIC
        mv consensus/current/* consensus/archive/$OLD_EPIC/ 2>/dev/null
        mv consensus/artifacts/* consensus/archive/$OLD_EPIC/ 2>/dev/null
        find consensus/messages/inbox -name "*.yaml" -exec mv {} consensus/archive/$OLD_EPIC/ \; 2>/dev/null
    fi
fi

# Create new epic
cat > consensus/current/epic.yaml << EOL
epic_id: $EPIC_ID
title: "$TITLE"
status: requirements_gathering
iteration: 1
max_iterations: 3
created_at: $(date -Iseconds)
EOL

# Reset state
cat > consensus/current/state.yaml << EOL
iteration: 1
phase: requirements_gathering
agents_completed: []
consensus_status: not_started
conflicts: []
last_updated: $(date -Iseconds)
EOL

# Clear decision log
> consensus/current/decision_log.jsonl

echo "New epic created: $EPIC_ID - $TITLE"
echo "Run ./consensus/status.sh to check status"
EOF

chmod +x consensus/new_epic.sh

# Create agent launcher helper
cat > consensus/run_agent.sh << 'EOF'
#!/bin/bash
AGENT=$1

if [ -z "$AGENT" ]; then
    echo "Usage: ./run_agent.sh <agent_name>"
    echo "Available agents: analyst, architect, tech_lead, developer, quality, devops"
    exit 1
fi

echo "=== Instructions for running $AGENT agent ==="
echo ""
echo "1. Open a new Cursor chat window"
echo "2. Copy and paste this prompt:"
echo ""
echo "----------------------------------------"
cat docs/roles/cursor_consensus/prompts/${AGENT}_prompt.md 2>/dev/null || echo "Prompt template not found for $AGENT"
echo "----------------------------------------"
echo ""
echo "3. The agent will read from: consensus/current/epic.yaml"
echo "4. The agent will write to: consensus/artifacts/ and consensus/messages/inbox/"
echo "5. After completion, run: ./consensus/status.sh"
EOF

chmod +x consensus/run_agent.sh

echo ""
echo "✅ Consensus system initialized successfully!"
echo ""
echo "Quick Start:"
echo "1. Create your first epic: ./consensus/new_epic.sh EP-001 'Your epic title'"
echo "2. Check status anytime: ./consensus/status.sh"
echo "3. Run an agent: ./consensus/run_agent.sh analyst"
echo ""
echo "Directory structure created at: ./consensus/"
