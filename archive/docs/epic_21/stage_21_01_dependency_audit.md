# Stage 21_01 · Dependency Audit

## Purpose
Document cross-layer dependencies that violate Clean Architecture boundaries and
inform the refactor backlog for Stage 21_01.

## Domain Layer Findings
- **ButlerOrchestrator** binds directly to Mongo collections instead of using a domain
  repository abstraction.  
  ```7:56:src/domain/agents/butler_orchestrator.py
  from motor.motor_asyncio import AsyncIOMotorDatabase
  ...
      mongodb: AsyncIOMotorDatabase,
      ...
      self.context_collection = mongodb.dialog_contexts
  ```
- **HomeworkHandler** depends on the infrastructure homework checker client, mixing
  domain handler logic with external API access.  
  ```14:67:src/domain/agents/handlers/homework_handler.py
  from src.infrastructure.hw_checker.client import HWCheckerClient
  ...
      self.hw_checker_client = hw_checker_client
  ```
- **ChannelScorer** pulls runtime configuration directly from settings rather than an
  injected configuration interface, complicating deterministic tests.  
  ```1:63:src/domain/services/channel_scorer.py
  from src.infrastructure.config.settings import get_settings
  ...
      settings = get_settings()
  ```
- **Intent classifiers** import infrastructure logging, cache, and monitoring metrics,
  preventing pure-domain testing.

## Presentation Layer Findings
- **Review Routes** coroutine performs validation, disk IO, and queueing within a single
  function, violating SRP and security guidelines (no checksum, direct writes).  
  ```40:150:src/presentation/api/review_routes.py
  with open(new_submission_path, "wb") as f:
      content = await new_zip.read()
      f.write(content)
  ```
- Storage path is hardcoded to `review_archives/`, lacking configuration/DI hooks and
  controls required by `operations.md`.

## Application Layer Findings
- **ReviewSubmissionUseCase** contains large helper methods covering log analysis,
  persistence, and publishing logic with no separation of concerns.  
  ```223:330:src/application/use_cases/review_submission_use_case.py
  async def _append_log_analysis(...):
      ...
  async def _persist_report(...):
      ...
  ```

## Recommended Interface Extractions
| Component | Proposed Interface | Location | Notes |
|-----------|--------------------|----------|-------|
| Dialog context storage | `DialogContextRepository` | `src/domain/interfaces/dialog_context_repository.py` | Async CRUD for dialog contexts |
| Homework checker access | `HomeworkReviewService` | `src/application/interfaces/homework_review_service.py` | Handles list/review flows |
| Settings gateway | `ChannelResolutionConfig` | `src/domain/interfaces/config.py` | Provide stable config object |
| Archive storage | `ReviewArchiveStorage` | `src/application/interfaces/storage.py` | Abstract FS/S3/backends |

## Next Actions
1. Draft interface definitions and update DI container plan.
2. Create migration backlog entries (ARCH-21-01..03) with owner assignments.
3. Schedule pairing sessions with QA to define new test doubles for extracted interfaces.


