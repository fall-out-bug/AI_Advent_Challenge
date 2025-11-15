# Handoff Contracts

## Purpose
Standardize input/output formats exchanged between roles to keep the agent
workflow predictable. Refer to `docs/specs/process/agent_workflow.md` for
sequence context.

## Analyst → Architect

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "AnalystToArchitect",
  "type": "object",
  "required": ["epic", "requirements", "acceptance", "open_questions"],
  "properties": {
    "epic": { "type": "string", "pattern": "^EP\\d+$" },
    "requirements": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "title", "must_have", "should_have", "out_of_scope"],
        "properties": {
          "id": { "type": "string" },
          "title": { "type": "string" },
          "must_have": { "type": "array", "items": { "type": "string" } },
          "should_have": { "type": "array", "items": { "type": "string" } },
          "out_of_scope": { "type": "array", "items": { "type": "string" } }
        }
      }
    },
    "acceptance": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "criterion", "evidence"],
        "properties": {
          "id": { "type": "string" },
          "criterion": { "type": "string" },
          "evidence": { "type": "string" }
        }
      }
    },
    "open_questions": { "type": "array", "items": { "type": "string" } },
    "attachments": { "type": "array", "items": { "type": "string", "format": "uri" } }
  }
}
```

## Architect → Tech Lead

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ArchitectToTechLead",
  "type": "object",
  "required": ["epic", "vision", "interfaces", "risks", "decisions"],
  "properties": {
    "epic": { "type": "string", "pattern": "^EP\\d+$" },
    "vision": { "type": "string" },
    "interfaces": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "purpose", "provider", "consumer"],
        "properties": {
          "name": { "type": "string" },
          "purpose": { "type": "string" },
          "provider": { "type": "string" },
          "consumer": { "type": "string" },
          "notes": { "type": "string" }
        }
      }
    },
    "risks": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["description", "impact", "mitigation"],
        "properties": {
          "description": { "type": "string" },
          "impact": { "type": "string", "enum": ["low", "medium", "high"] },
          "mitigation": { "type": "string" }
        }
      }
    },
    "decisions": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "status", "summary"],
        "properties": {
          "id": { "type": "string" },
          "status": { "type": "string", "enum": ["proposed", "accepted", "rejected"] },
          "summary": { "type": "string" },
          "link": { "type": "string", "format": "uri" }
        }
      }
    },
    "attachments": { "type": "array", "items": { "type": "string", "format": "uri" } }
  }
}
```

## Tech Lead → Developer

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "TechLeadToDeveloper",
  "type": "object",
  "required": ["epic", "stages", "ci_gates", "handoff"],
  "properties": {
    "epic": { "type": "string", "pattern": "^EP\\d+$" },
    "stages": {
      "type": "array",
      "minItems": 1,
      "items": {
        "type": "object",
        "required": ["order", "name", "tasks", "dod"],
        "properties": {
          "order": { "type": "integer", "minimum": 1 },
          "name": { "type": "string" },
          "tasks": { "type": "array", "items": { "type": "string" } },
          "dod": { "type": "array", "items": { "type": "string" } },
          "evidence": { "type": "array", "items": { "type": "string" } }
        }
      }
    },
    "ci_gates": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["name", "command", "coverage"],
        "properties": {
          "name": { "type": "string" },
          "command": { "type": "string" },
          "coverage": { "type": "number", "minimum": 0, "maximum": 100 }
        }
      }
    },
    "risks": { "$ref": "#/$defs/risk" },
    "handoff": {
      "type": "object",
      "required": ["owner", "date", "checklist"],
      "properties": {
        "owner": { "type": "string" },
        "date": { "type": "string", "format": "date" },
        "checklist": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["item", "status"],
            "properties": {
              "item": { "type": "string" },
              "status": { "type": "string", "enum": ["pending", "in_progress", "complete"] }
            }
          }
        }
      }
    }
  },
  "$defs": {
    "risk": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["description", "owner", "status"],
        "properties": {
          "description": { "type": "string" },
          "owner": { "type": "string" },
          "status": { "type": "string", "enum": ["open", "mitigating", "closed"] }
        }
      }
    }
  }
}
```

## Developer → Reviewer

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "DeveloperToReviewer",
  "type": "object",
  "required": ["epic", "changesets", "tests", "evidence"],
  "properties": {
    "epic": { "type": "string", "pattern": "^EP\\d+$" },
    "changesets": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["path", "summary"],
        "properties": {
          "path": { "type": "string" },
          "summary": { "type": "string" },
          "tickets": { "type": "array", "items": { "type": "string" } }
        }
      }
    },
    "tests": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["type", "command", "status", "coverage"],
        "properties": {
          "type": { "type": "string" },
          "command": { "type": "string" },
          "status": { "type": "string", "enum": ["pass", "fail", "skipped"] },
          "coverage": { "type": "number", "minimum": 0, "maximum": 100 },
          "artifacts": { "type": "array", "items": { "type": "string", "format": "uri" } }
        }
      }
    },
    "evidence": {
      "type": "array",
      "items": { "type": "string", "format": "uri" }
    },
    "notes": { "type": "string" }
  }
}
```

## Reviewer → Analyst (Closure Packet)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ReviewerToAnalyst",
  "type": "object",
  "required": ["epic", "decision", "findings", "follow_ups"],
  "properties": {
    "epic": { "type": "string", "pattern": "^EP\\d+$" },
    "decision": { "type": "string", "enum": ["approved", "rejected", "conditional"] },
    "findings": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "summary", "severity"],
        "properties": {
          "id": { "type": "string" },
          "summary": { "type": "string" },
          "severity": { "type": "string", "enum": ["info", "minor", "major", "critical"] },
          "evidence": { "type": "array", "items": { "type": "string", "format": "uri" } }
        }
      }
    },
    "follow_ups": { "type": "array", "items": { "type": "string" } },
    "archive_notes": { "type": "string" }
  }
}
```

## Integration Notes
- Embed schemas in CI validation routines before handoffs.
- Store rendered payloads under respective role `examples/` folders.
- Revisit schemas after each new epic to capture evolving needs.

