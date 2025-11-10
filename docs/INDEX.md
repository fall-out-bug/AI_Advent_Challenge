# AI Challenge Documentation Index

## Main Documentation

### Getting Started
- [README.md](../README.md) - Project overview and quick start
- [DEVELOPMENT.md](DEVELOPMENT.md) - Development, deployment, and operations guide
- [USER_GUIDE.md](USER_GUIDE.md) - Comprehensive user guide

### Architecture & Development
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture overview
- [TESTING.md](TESTING.md) - Testing strategy and guidelines

### API Reference
- [API_DOCUMENTATION.md](API_DOCUMENTATION.md) - Complete API reference
- [API_MCP.md](API_MCP.md) - Model Context Protocol tool matrix and workflows
- [MCP_GUIDE.md](MCP_GUIDE.md) - Model Context Protocol guide (integration, API, troubleshooting)
- [AGENT_INTEGRATION.md](AGENT_INTEGRATION.md) - MCP-aware agent integration guide (English)
- [AGENT_INTEGRATION.ru.md](AGENT_INTEGRATION.ru.md) - MCP-aware agent integration guide (Russian)

### Security & Operations
- [SECURITY.md](SECURITY.md) - Security policies and practices
- [MONITORING.md](MONITORING.md) - Monitoring setup and Grafana dashboards
- [ML_MONITORING.md](ML_MONITORING.md) - ML-specific monitoring and metrics
- [shared_infra_cutover.md](shared_infra_cutover.md) - Shared infrastructure hand-off notes
- [scripts/start_shared_infra.sh](../scripts/start_shared_infra.sh) - Wrapper script for external infra (executable)

### Epic 04 — Legacy Archive & Cleanup
- [Stage 04_01](specs/epic_04/stage_04_01.md) - Archive scope confirmation
- [Stage 04_02](specs/epic_04/stage_04_02.md) - Migration execution log & validation
- [Stage 04_03](specs/epic_04/stage_04_03.md) - Repository hygiene and sign-off checklist
- [Known Issues](specs/epic_04/known_issues.md) - Deferred items and follow-ups
- [Archive Manifest](../archive/ep04_2025-11/ARCHIVE_MANIFEST.md) - Inventory of archived assets

### Day 15 - Quality Assessment & Fine-tuning (Current)
- [README](day15/README.md) - Self-improving LLM system overview
- [API Documentation](day15/api.md) - Evaluation and fine-tuning API reference
- [Migration Guide](day15/MIGRATION_FROM_DAY12.md) - Migration from Day 12 to Day 15

### Day 12 - PDF Digest System
- [User Guide](day12/USER_GUIDE.md) - PDF digest usage guide
- [API Documentation](day12/api.md) - MCP tools API reference
- [Architecture](day12/ARCHITECTURE.md) - System architecture with diagrams
- [Testing and Launch](day12/TESTING_AND_LAUNCH.md) - Testing and deployment guide
- [Quick Start](day12/QUICK_START.ru.md) - Quick start guide (Russian)
- [Deployment](day12/DEPLOYMENT.md) - Deployment instructions

### Day 14 - Multi-Pass Code Review
- [Multi-Pass Architecture](MULTI_PASS_ARCHITECTURE.md) - 3-pass code review architecture
- [Component Detection Strategy](COMPONENT_DETECTION_STRATEGY.md) - Component detection algorithms
- [Context Compression Strategy](CONTEXT_COMPRESSION_STRATEGY.md) - Token optimization strategies
- [Phase 1 Implementation](PHASE_1_IMPLEMENTATION.md) - Implementation details
- [MCP Homework Review](MCP_HOMEWORK_REVIEW.md) - Homework review via MCP tools

### Day 11 - Butler Bot
- [Quick Start Guide](QUICK_START_DAY11.md) - Butler Bot quick start
- [Architecture FSM](ARCHITECTURE_FSM.md) - FSM conversation flow architecture

### Day 13 - Butler Agent (Refactored)
- [Architecture](ARCHITECTURE.md#butler-agent-architecture-day-13-refactoring) - Complete Butler Agent architecture with Clean Architecture layers
- [API Reference](API.md) - Butler Agent API documentation: dialog modes, state machine, use cases
- [Deployment Guide](DEPLOYMENT.md) - Step-by-step deployment instructions for local, Docker, and production
- [Contributing Guidelines](../CONTRIBUTING.md#butler-agent-development-guidelines) - Development guidelines for Butler Agent components

### Code Review & Quality
- [Multi-Pass Architecture](MULTI_PASS_ARCHITECTURE.md) - 3-pass code review system
- [Component Detection Strategy](COMPONENT_DETECTION_STRATEGY.md) - Component detection
- [Context Compression Strategy](CONTEXT_COMPRESSION_STRATEGY.md) - Token optimization
- [Testing Fixtures Guide](TESTING_FIXTURES_GUIDE.md) - Test fixture organization

### Project History
- [CHANGELOG.md](../CHANGELOG.md) - Project version history

## Quick Links

### For Developers
- Start here: [README.md](../README.md)
- Setup: [DEVELOPMENT.md](DEVELOPMENT.md)
- Architecture: [ARCHITECTURE.md](ARCHITECTURE.md) (includes Butler Agent architecture)
- Testing: [TESTING.md](TESTING.md)
- API Reference: [API_DOCUMENTATION.md](API_DOCUMENTATION.md) (general API) | [API.md](API.md) (Butler Agent API)
- MCP Integration: [MCP_GUIDE.md](MCP_GUIDE.md)
- Butler Agent: [API.md](API.md) | [Deployment](DEPLOYMENT.md) | [Contributing](../CONTRIBUTING.md#butler-agent-development-guidelines)
- **Day 15 - Quality & Fine-tuning**: [README](day15/README.md) | [API](day15/api.md) | [Migration](day15/MIGRATION_FROM_DAY12.md)
- **AI Assistant Support**: [AI_CONTEXT.md](../AI_CONTEXT.md) - Complete project context | [.cursorrules](../.cursorrules) - Coding standards

### For Users
- Quick start: [README.md](../README.md)
- User guide: [USER_GUIDE.md](USER_GUIDE.md)
- Deployment: [DEVELOPMENT.md](DEVELOPMENT.md)
- Troubleshooting: [DEVELOPMENT.md](DEVELOPMENT.md#troubleshooting)
- MCP Guide: [MCP_GUIDE.md](MCP_GUIDE.md)

### For Operations
- Monitoring: [MONITORING.md](MONITORING.md)
- Security: [SECURITY.md](SECURITY.md)
- ML Monitoring: [ML_MONITORING.md](ML_MONITORING.md)
- Butler Agent Deployment: [DEPLOYMENT.md](DEPLOYMENT.md)
