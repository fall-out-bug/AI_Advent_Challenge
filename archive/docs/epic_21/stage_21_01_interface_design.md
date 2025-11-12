# Stage 21_01 · Interface Design Notes

## Dialog Context Repository
- **Motivation**: `ButlerOrchestrator` currently depends on MongoDB collections directly, violating Clean Architecture.
- **Interface Name**: `DialogContextRepository`
- **Location**: `src/domain/interfaces/dialog_context_repository.py`
- **Operations**:
  - `async def get_by_session(session_id: str) -> DialogContext | None`
  - `async def save(context: DialogContext) -> None`
  - `async def delete(session_id: str) -> None`
  - `async def list_active(user_id: str) -> list[DialogContext]` (future enhancement)
- **Implementation Notes**:
  - Primary adapter: `MongoDialogContextRepository` in `src/infrastructure/repositories/`.
  - Provide in-memory fake for unit tests.
  - Ensure DTO ↔ domain conversion isolated within adapter.

## Homework Review Service
- **Motivation**: `HomeworkHandler` mixes handler logic with infrastructure client.
- **Interface Name**: `HomeworkReviewService`
- **Location**: `src/application/interfaces/homework_review_service.py`
- **Operations**:
  - `async def list_recent_commits(days: int) -> HomeworkCommitList`
  - `async def request_review(commit_hash: str) -> ReviewResult`
  - `async def get_status(commit_hash: str) -> ReviewStatus` (optional)
- **Implementation Notes**:
  - Wrap existing `HWCheckerClient` logic.
  - Provide error translation into domain-specific exceptions.
  - Add caching hook for frequently requested lists (future Stage 21_02).

## Channel Resolution Config
- **Motivation**: `ChannelScorer` loads weights via infrastructure settings, hindering determinism.
- **Interface Name**: `ChannelResolutionConfig`
- **Location**: `src/domain/interfaces/config.py`
- **Operations**:
  - Accessor properties for each weight (exact, prefix, token overlap, Levenshtein, description).
  - Optional method `def as_dict() -> dict[str, float]`.
- **Implementation Notes**:
  - Application layer composes concrete config from settings/environment.
  - Testing strategy: provide fixture returning static weights.

## Review Archive Storage
- **Motivation**: API route writes files directly to disk, conflicting with security guidelines.
- **Interface Name**: `ReviewArchiveStorage`
- **Location**: `src/application/interfaces/storage.py`
- **Operations**:
  - `async def save_new(student_id: str, assignment_id: str, filename: str, data: bytes) -> StoredArtifact`
  - `async def save_previous(...) -> StoredArtifact`
  - `async def save_logs(...) -> StoredArtifact`
  - `async def open(path: str) -> AsyncIterator[bytes]` (optional)
  - `async def purge(path: str) -> None`
- **Implementation Notes**:
  - Adapters for local FS, S3, or other backends.
  - Enforce size thresholds, checksum verification, optional malware scanning.
  - Return value should encapsulate storage path and metadata (size, checksum).

## Dependency Injection Updates
- Update DI container (infrastructure/adapters) to register new interfaces.
- Provide factory functions for tests to supply in-memory or stub implementations.
- Document wiring in `docs/specs/epic_21/stage_21_01.md` once implemented.

## Testing Strategy
- Create domain-level tests using in-memory repositories/services.
- For storage adapter, leverage temporary directories and checksum fixtures.
- Integration tests should confirm wiring via FastAPI dependency overrides.


