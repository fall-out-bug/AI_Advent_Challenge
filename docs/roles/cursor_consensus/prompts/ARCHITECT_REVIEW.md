# Architect Prompt Review - Clarity Analysis

**Status:** ✅ **UPDATED** - All clarifications have been applied to architect_prompt.md

## Overall Assessment

The Architect prompt has been **updated with all clarifications** and is now clear and consistent with the consensus system requirements.

## Issues Found

### 1. **Veto Target Ambiguity** ⚠️

**Current State:**
- Line 106: Veto example only shows sending to `analyst`
- Consensus mechanism (v2.yaml:82-87) shows architect can conflict with `tech_lead`

**Problem:**
Architect might need to veto:
- `analyst` (if requirements violate architecture)
- `tech_lead` (if plan violates architecture boundaries)
- `developer` (if implementation violates architecture - though developer has no veto rights)

**Recommendation:**
Clarify that architect can veto **any agent** that violates Clean Architecture principles, not just analyst.

```yaml
# Current (line 106):
to: analyst

# Should be:
to: [analyst|tech_lead|developer]  # Any agent violating architecture
```

### 2. **C4 Diagrams - Unclear Usage** ❓

**Current State:**
- Lines 88-103: Architect must update `c4_diagrams.yaml`
- No other agent mentions C4 diagrams
- Not clear if this is required or optional

**Questions:**
- Is this always required or only for complex epics?
- Who reads/uses these diagrams?
- Should this be optional with a note "if architecture changes significantly"?

**Recommendation:**
Add clarification:
```markdown
### 2. C4 Diagram Update (if architecture changes significantly)
Write to `docs/specs/epic_XX/consensus/artifacts/c4_diagrams.yaml`:
[Only update if new components are added or layer boundaries change]
```

### 3. **Message Sending Timing** ⚠️

**Current State:**
- Line 177: "Always send messages to relevant agents, even if expressing agreement"
- Line 181-184: Lists recipients (tech_lead, developer, quality)
- But unclear: **when** to send messages?

**Questions:**
- Send message after creating architecture.json?
- Send message only if veto?
- Send message to express approval?

**Recommendation:**
Add explicit timing:
```markdown
## Message Sending Rules

Send messages:
1. **After creating architecture.json** - Inform tech_lead that architecture is ready
2. **After veto** - Explain violation to the violating agent
3. **After approval** - Confirm architecture is ready (use `action_needed: "none"`)
```

### 4. **Architecture.json Creation Timing** ❓

**Current State:**
- Line 33: "Write to architecture.json"
- But unclear: Should architect create this:
  - **Before** checking for violations? (then veto if needed)
  - **After** approval? (only if no violations)

**Problem:**
If architect finds violations, should they:
- Option A: Create architecture.json with violations noted, then veto?
- Option B: Veto first, then create architecture.json after requirements are fixed?

**Recommendation:**
Clarify workflow:
```markdown
## Workflow

1. Read requirements
2. Check for architecture violations
3. **If violations found**: Send veto immediately, do NOT create architecture.json
4. **If no violations**: Create architecture.json, then send approval message
```

### 5. **Codebase Review Scope** ❓

**Current State:**
- Line 19: "Review current codebase architecture if needed"
- Unclear: When is it "needed"?

**Questions:**
- Always review existing architecture?
- Only if requirements suggest new components?
- How to determine if review is needed?

**Recommendation:**
Make it explicit:
```markdown
3. **Review current codebase** if:
   - Requirements suggest new components
   - Requirements modify existing components
   - You need to verify layer boundaries
   - Check `src/` directory structure for existing patterns
```

### 6. **Decision Log - Approval vs Veto** ✅

**Current State:**
- Line 140: `"decision": "approve|veto"`
- This is clear, but should emphasize:
  - If architect approves → `"decision": "approve"`
  - If architect vetoes → `"decision": "veto"`

**Status:** Clear, but could add example for both cases.

### 7. **Missing: What to Read from Previous Iterations** ⚠️

**Current State:**
- Line 20: "Determine current iteration from decision_log.jsonl"
- But unclear: Should architect read previous architecture.json if iteration > 1?

**Recommendation:**
Add:
```markdown
4. **If iteration > 1**: Read previous `architecture.json` to understand what changed
5. **If iteration > 1**: Read veto messages in inbox to understand what was rejected
```

### 8. **Interface with Tech Lead** ✅

**Current State:**
- Tech Lead reads architecture.json (tech_lead_prompt.md:18)
- Architect creates architecture.json
- Clear handoff

**Status:** Clear and consistent.

### 9. **Veto Resolution Authority** ✅

**Current State:**
- Consensus mechanism (v2.yaml:48-50) says architect has final say on layer violations
- Architect prompt (line 188) says "ABSOLUTE VETO POWER"
- Consistent

**Status:** Clear and consistent.

## Consistency Check with Other Agents

### ✅ Consistent Elements:
1. Directory structure format (`docs/specs/epic_XX/`)
2. Timestamp format (`YYYY_MM_DD_HH_MM_SS`)
3. Decision log format (source_document, previous_artifacts)
4. Message format (YAML structure)
5. Veto format (standardized across all agents with veto rights)

### ⚠️ Potential Inconsistencies:
1. **Analyst** (line 105): Says architect should receive messages ✅
2. **Tech Lead** (line 18): Reads architecture.json ✅
3. **Developer** (line 20): Reads architecture.json ✅
4. **Quality** (line 22): Reads architecture.json ✅
5. **DevOps**: Doesn't read architecture.json (might be intentional)

## Recommendations Summary

### ✅ Completed:
1. **✅ Clarify veto targets** - Updated: Architect can veto any agent (analyst, tech_lead, developer)
2. **✅ Clarify workflow** - Updated: Always create architecture.json, refine during consensus
3. **✅ Clarify message timing** - Updated: Send messages after each iteration
4. **✅ Clarify C4 diagrams** - Updated: Required for project, update when needed
5. **✅ Clarify codebase review** - Updated: Only when requested by project owner
6. **✅ Add iteration > 1 guidance** - Updated: Read previous architecture.json and veto messages

## Changes Applied

All clarifications have been implemented in `architect_prompt.md`:

1. **Veto Rights Section** - Clarified that Architect, Analyst, and Tech Lead can veto
2. **Workflow Section** - Added explicit workflow: always create architecture.json, refine during consensus
3. **Message Timing** - Made mandatory: send messages after each iteration
4. **C4 Diagrams** - Marked as required, update when needed
5. **Codebase Review** - Changed to "only if requested by project owner"
6. **Iteration Handling** - Added steps for reading previous artifacts when iteration > 1
