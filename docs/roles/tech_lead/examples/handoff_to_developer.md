# Tech Lead → Developer Handoff Example

## EP23 Payment Service - Developer Package

```json
{
  "metadata": {
    "epic_id": "EP23",
    "tech_lead": "tech_lead_agent_v1",
    "handoff_date": "2025-11-17T09:00:00Z",
    "plan_version": "1.0"
  },
  
  "stages": [
    {
      "stage_id": "STAGE-2",
      "name": "Domain Layer Implementation",
      "duration_days": 7,
      "owner": "Developer A",
      "status": "ready",
      
      "tasks": [
        "Implement Payment entity (src/domain/entities/payment.py)",
        "Implement Transaction value objects",
        "Add validation logic (amount > 0, valid currency)",
        "Write unit tests (tests/unit/domain/)"
      ],
      
      "dod": [
        "Payment entity with __init__, validate() methods",
        "100% test coverage for domain layer",
        "All unit tests pass (pytest tests/unit/domain/ -v)",
        "Type hints: mypy src/domain/ --strict passes"
      ],
      
      "commands": {
        "setup": "pip install -r requirements.txt",
        "test": "pytest tests/unit/domain/ -v",
        "coverage": "pytest --cov=src/domain tests/unit/domain/",
        "typecheck": "mypy src/domain/ --strict"
      },
      
      "ci_gates": [
        {"name": "lint", "command": "make lint", "blocking": true},
        {"name": "typecheck", "command": "mypy src/domain/ --strict", "blocking": true},
        {"name": "unit_tests", "command": "pytest tests/unit/domain/", "blocking": true},
        {"name": "coverage", "threshold": "100%", "blocking": true}
      ],
      
      "acceptance_criteria": [
        "REQ-PAY-001: Payment entity validates amount > 0",
        "REQ-PAY-003: Payment entity validates currency in [USD, EUR, GBP]"
      ],
      
      "dependencies": [],
      "blockers": []
    }
  ],
  
  "environment_setup": {
    "local": {
      "command": "docker-compose up -d",
      "services": ["mongodb", "redis"],
      "verify": "docker-compose ps (all services 'Up')"
    },
    "env_vars": {
      "MONGODB_URI": "mongodb://localhost:27017/payments_test",
      "LOG_LEVEL": "DEBUG"
    }
  },
  
  "testing_guide": {
    "unit": "pytest tests/unit/ -v (run after each function)",
    "integration": "pytest tests/integration/ -v (run after adapter impl)",
    "e2e": "pytest tests/e2e/ -v (run before deployment)"
  },
  
  "code_standards": {
    "style": "Black formatting (line length: 88)",
    "type_hints": "100% coverage (mypy --strict)",
    "docstrings": "Required for all public functions",
    "tests": "TDD: Write test first, then implementation"
  },
  
  "rollback_plan": {
    "if_failed": "Revert to main branch (git reset --hard origin/main)",
    "notify": "Tech Lead via Slack #payments-dev"
  },
  
  "support": {
    "tech_lead": "Available 9am-5pm for questions",
    "architecture_ref": "docs/roles/architect/examples/EP23_architecture.md",
    "slack_channel": "#payments-dev"
  }
}
```

## Handoff Checklist

- [x] Stages defined with clear DoD
- [x] Commands documented (setup, test, typecheck)
- [x] CI gates specified
- [x] Environment setup instructions
- [x] Rollback plan included
- [x] Support channels listed

**Expected Developer Response Time:** Start within 24h, daily updates in Slack
