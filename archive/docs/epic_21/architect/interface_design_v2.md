# Stage 21_01 · Interface Design Notes (v2)

**Version**: 2.0  
**Updated**: 2025-11-11 (Response to Tech Lead feedback)  
**Changes**: Added `StoredArtifact` dataclass, streaming API, usage examples

---

## Dialog Context Repository

### Interface Definition

```python
# src/domain/interfaces/dialog_context_repository.py

from typing import Protocol
from src.domain.entities.dialog_context import DialogContext


class DialogContextRepository(Protocol):
    """Repository for dialog context persistence.
    
    Purpose:
        Abstract dialog context storage to isolate domain logic from
        infrastructure (MongoDB, Redis, etc.).
    
    Design Principles:
        - Async interface (all operations are I/O-bound)
        - Returns domain entities (DialogContext), not DTOs
        - No infrastructure concerns (connection strings, collections)
    """
    
    async def get_by_session(self, session_id: str) -> DialogContext | None:
        """Retrieve dialog context by session ID.
        
        Args:
            session_id: Unique session identifier.
        
        Returns:
            DialogContext if found, None otherwise.
        
        Example:
            >>> repo = MongoDialogContextRepository(...)
            >>> context = await repo.get_by_session("session_123")
            >>> print(context.user_id if context else "Not found")
        """
        ...
    
    async def save(self, context: DialogContext) -> None:
        """Save dialog context (create or update).
        
        Args:
            context: Dialog context to persist.
        
        Raises:
            RepositoryError: If persistence fails.
        
        Example:
            >>> context = DialogContext(session_id="s1", user_id="alice", turn=1)
            >>> await repo.save(context)
        """
        ...
    
    async def delete(self, session_id: str) -> None:
        """Delete dialog context.
        
        Args:
            session_id: Session to delete.
        
        Note:
            Idempotent: no error if session doesn't exist.
        
        Example:
            >>> await repo.delete("session_123")
        """
        ...
    
    async def list_active(self, user_id: str) -> list[DialogContext]:
        """List active sessions for user (future enhancement).
        
        Args:
            user_id: User identifier.
        
        Returns:
            List of active dialog contexts (may be empty).
        """
        ...
```

### Implementation Example

```python
# src/infrastructure/repositories/mongo_dialog_context_repository.py

from motor.motor_asyncio import AsyncIOMotorClient
from src.domain.interfaces.dialog_context_repository import DialogContextRepository
from src.domain.entities.dialog_context import DialogContext


class MongoDialogContextRepository:
    """MongoDB implementation of DialogContextRepository."""
    
    def __init__(self, mongo_client: AsyncIOMotorClient):
        """Initialize repository.
        
        Args:
            mongo_client: Async MongoDB client.
        """
        self._collection = mongo_client.butler.dialog_contexts
    
    async def get_by_session(self, session_id: str) -> DialogContext | None:
        """Retrieve dialog context from MongoDB."""
        document = await self._collection.find_one({"session_id": session_id})
        return self._map_to_domain(document) if document else None
    
    async def save(self, context: DialogContext) -> None:
        """Save dialog context to MongoDB."""
        document = self._map_to_dto(context)
        await self._collection.update_one(
            {"session_id": context.session_id},
            {"$set": document},
            upsert=True
        )
    
    async def delete(self, session_id: str) -> None:
        """Delete dialog context from MongoDB."""
        await self._collection.delete_one({"session_id": session_id})
    
    def _map_to_domain(self, doc: dict) -> DialogContext:
        """Convert MongoDB document to domain entity."""
        return DialogContext(
            session_id=doc["session_id"],
            user_id=doc["user_id"],
            turn=doc.get("turn", 0),
            # ... other fields
        )
    
    def _map_to_dto(self, context: DialogContext) -> dict:
        """Convert domain entity to MongoDB document."""
        return {
            "session_id": context.session_id,
            "user_id": context.user_id,
            "turn": context.turn,
            # ... other fields
        }
```

### Usage Example (Domain → Infrastructure)

```python
# Step 1: Domain defines interface (no infrastructure knowledge)
class ButlerOrchestrator:
    def __init__(self, context_repo: DialogContextRepository):  # ← interface
        self._context_repo = context_repo
    
    async def handle_message(self, user_id: str, message: str) -> str:
        # Domain logic uses interface
        context = await self._context_repo.get_by_session(self._session_id)
        if not context:
            context = self._create_new_context(user_id)
        
        # Process message...
        response = await self._llm_client.generate(context, message)
        
        # Save updated context
        context.turn += 1
        await self._context_repo.save(context)
        
        return response

# Step 2: DI container wires implementation
class DIContainer:
    @cached_property
    def dialog_context_repo(self) -> DialogContextRepository:
        return MongoDialogContextRepository(mongo_client=self.mongo_client)
    
    @cached_property
    def butler_orchestrator(self) -> ButlerOrchestrator:
        return ButlerOrchestrator(context_repo=self.dialog_context_repo)  # ← injected

# Step 3: Presentation layer uses via DI
@router.post("/dialog")
async def handle_dialog(
    request: DialogRequest,
    container: DIContainer = Depends(get_container)
):
    orchestrator = container.butler_orchestrator  # ← fully wired
    response = await orchestrator.handle_message(request.user_id, request.message)
    return {"response": response}
```

---

## Homework Review Service

### Interface Definition

```python
# src/domain/interfaces/homework_review_service.py  (CORRECTED LOCATION)
# (Originally proposed in application/interfaces, but domain layer should define it)

from typing import Protocol
from dataclasses import dataclass


@dataclass
class HomeworkCommit:
    """Homework commit metadata."""
    hash: str
    date: str
    student_id: str
    assignment_id: str


@dataclass
class ReviewResult:
    """Review request result."""
    status: str  # "success" | "error" | "pending"
    review_id: str | None
    error_message: str | None


class HomeworkReviewService(Protocol):
    """Service for homework review operations.
    
    Purpose:
        Abstract external homework checker API to isolate domain logic.
    
    Design Notes:
        - Interface in domain (HomeworkHandler is domain layer)
        - Implementation in application (adapter wraps HWCheckerClient)
    """
    
    async def list_recent_commits(self, days: int = 7) -> list[HomeworkCommit]:
        """List recent homework commits.
        
        Args:
            days: Number of days to look back.
        
        Returns:
            List of commits (may be empty).
        
        Raises:
            HomeworkServiceError: If API call fails.
        
        Example:
            >>> service = HWCheckerServiceAdapter(...)
            >>> commits = await service.list_recent_commits(days=3)
            >>> for commit in commits:
            ...     print(f"{commit.student_id}: {commit.hash}")
        """
        ...
    
    async def request_review(self, commit_hash: str) -> ReviewResult:
        """Request review for commit.
        
        Args:
            commit_hash: Git commit hash.
        
        Returns:
            Review result with status and review_id.
        
        Raises:
            HomeworkServiceError: If API call fails.
        
        Example:
            >>> result = await service.request_review("abc123")
            >>> if result.status == "success":
            ...     print(f"Review ID: {result.review_id}")
        """
        ...
```

### Implementation Example

```python
# src/application/services/hw_checker_service_adapter.py

from src.domain.interfaces.homework_review_service import (
    HomeworkReviewService,
    HomeworkCommit,
    ReviewResult,
)
from src.infrastructure.hw_checker.client import HWCheckerClient


class HWCheckerServiceAdapter:
    """Adapter wrapping HWCheckerClient for domain interface."""
    
    def __init__(self, hw_client: HWCheckerClient):
        """Initialize adapter.
        
        Args:
            hw_client: Infrastructure HW checker client.
        """
        self._client = hw_client
    
    async def list_recent_commits(self, days: int = 7) -> list[HomeworkCommit]:
        """List commits via HW checker API."""
        try:
            raw_commits = await self._client.list_commits(days=days)
            return [self._map_commit(c) for c in raw_commits]
        except Exception as e:
            # Translate infrastructure exception to domain exception
            raise HomeworkServiceError(f"Failed to list commits: {e}")
    
    async def request_review(self, commit_hash: str) -> ReviewResult:
        """Request review via HW checker API."""
        try:
            result = await self._client.submit_review(commit_hash)
            return ReviewResult(
                status="success",
                review_id=result["review_id"],
                error_message=None
            )
        except Exception as e:
            return ReviewResult(
                status="error",
                review_id=None,
                error_message=str(e)
            )
    
    def _map_commit(self, raw: dict) -> HomeworkCommit:
        """Map API response to domain entity."""
        return HomeworkCommit(
            hash=raw["commit_hash"],
            date=raw["timestamp"],
            student_id=raw["student_id"],
            assignment_id=raw["assignment_id"],
        )
```

---

## Review Archive Storage

### `StoredArtifact` Dataclass (NEW)

```python
# src/application/entities/stored_artifact.py

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class StoredArtifact:
    """Metadata for stored archive.
    
    Purpose:
        Immutable record of stored file with integrity information.
    
    Attributes:
        path: Storage path (relative or absolute, depends on backend).
        size_bytes: File size in bytes.
        checksum_sha256: SHA-256 checksum for integrity verification.
        storage_backend: Backend type ("local_fs", "s3", etc.).
        stored_at: Upload timestamp (UTC).
    
    Example:
        >>> artifact = StoredArtifact(
        ...     path="student_123/hw01/submission.zip",
        ...     size_bytes=1024000,
        ...     checksum_sha256="a1b2c3...",
        ...     storage_backend="local_fs",
        ...     stored_at=datetime.utcnow()
        ... )
        >>> print(f"Stored {artifact.size_bytes} bytes at {artifact.path}")
    """
    path: str
    size_bytes: int
    checksum_sha256: str
    storage_backend: str
    stored_at: datetime
    
    def to_dict(self) -> dict:
        """Convert to dictionary for persistence."""
        return {
            "path": self.path,
            "size_bytes": self.size_bytes,
            "checksum_sha256": self.checksum_sha256,
            "storage_backend": self.storage_backend,
            "stored_at": self.stored_at.isoformat(),
        }
```

### Interface Definition (with Streaming)

```python
# src/application/interfaces/storage.py

from typing import Protocol, AsyncIterator
from src.application.entities.stored_artifact import StoredArtifact


class ReviewArchiveStorage(Protocol):
    """Abstract storage for review archives.
    
    Purpose:
        Isolate file storage from business logic. Supports multiple backends
        (local FS, S3, etc.) with security controls (checksum, AV scan).
    
    Security Requirements:
        - Credentials MUST be sourced from environment variables
        - For S3: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
        - For local: REVIEW_ARCHIVE_ROOT_PATH (default: ./review_archives)
        - Never log file contents or checksums
        - Apply size limits from operations.md (max 100MB per archive)
    
    Design Notes:
        - Small files (<10MB): Use `save_new()` with in-memory bytes
        - Large files (>10MB): Use `save_new_streaming()` to avoid memory overhead
    """
    
    async def save_new(
        self,
        student_id: str,
        assignment_id: str,
        filename: str,
        data: bytes
    ) -> StoredArtifact:
        """Save new submission archive (in-memory).
        
        Purpose:
            Store archive with checksum validation and optional AV scan.
        
        Args:
            student_id: Student identifier.
            assignment_id: Assignment identifier.
            filename: Original filename.
            data: File content (fully loaded in memory).
        
        Returns:
            StoredArtifact with path, checksum, and metadata.
        
        Raises:
            StorageSizeError: If file exceeds size limit (100MB).
            StorageChecksumError: If provided checksum doesn't match calculated.
            StorageSecurityError: If AV scan detects malware.
            StoragePermissionError: If write permission denied.
        
        Example:
            >>> storage = LocalFileSystemStorage(root="/var/butler/archives")
            >>> artifact = await storage.save_new(
            ...     student_id="alice",
            ...     assignment_id="hw01",
            ...     filename="submission.zip",
            ...     data=archive_bytes
            ... )
            >>> print(f"Saved to {artifact.path}, checksum {artifact.checksum_sha256[:8]}...")
        """
        ...
    
    async def save_new_streaming(
        self,
        student_id: str,
        assignment_id: str,
        filename: str,
        data_stream: AsyncIterator[bytes],
        expected_size: int | None = None
    ) -> StoredArtifact:
        """Save new submission archive (streaming, for large files).
        
        Purpose:
            Store archive without loading entire file into memory.
            Suitable for files >10MB.
        
        Args:
            student_id: Student identifier.
            assignment_id: Assignment identifier.
            filename: Original filename.
            data_stream: Async iterator yielding chunks.
            expected_size: Expected file size (for progress tracking).
        
        Returns:
            StoredArtifact with path, checksum, and metadata.
        
        Raises:
            Same exceptions as save_new().
        
        Example:
            >>> async def stream_from_upload(request):
            ...     async for chunk in request.stream():
            ...         yield chunk
            >>> 
            >>> artifact = await storage.save_new_streaming(
            ...     student_id="bob",
            ...     assignment_id="hw02",
            ...     filename="large_submission.zip",
            ...     data_stream=stream_from_upload(request),
            ...     expected_size=50_000_000  # 50MB
            ... )
        """
        ...
    
    async def save_previous(
        self,
        student_id: str,
        assignment_id: str,
        filename: str,
        data: bytes
    ) -> StoredArtifact:
        """Save previous submission archive (for comparison)."""
        ...
    
    async def save_logs(
        self,
        student_id: str,
        assignment_id: str,
        filename: str,
        data: bytes
    ) -> StoredArtifact:
        """Save review logs."""
        ...
    
    async def open(self, path: str) -> AsyncIterator[bytes]:
        """Open stored file for reading (streaming).
        
        Args:
            path: Storage path (from StoredArtifact.path).
        
        Yields:
            File chunks (typically 64KB each).
        
        Raises:
            StorageNotFoundError: If file doesn't exist.
        
        Example:
            >>> async for chunk in storage.open(artifact.path):
            ...     process_chunk(chunk)
        """
        ...
    
    async def purge(self, path: str) -> None:
        """Delete stored file.
        
        Args:
            path: Storage path.
        
        Note:
            Idempotent: no error if file doesn't exist.
        """
        ...
```

### Implementation Example (Local FS)

```python
# src/infrastructure/storage/local_filesystem_storage.py

import hashlib
from pathlib import Path
from datetime import datetime
from typing import AsyncIterator


class LocalFileSystemStorage:
    """Local file system implementation of ReviewArchiveStorage."""
    
    def __init__(self, root_path: str, max_size_bytes: int = 100_000_000):
        """Initialize storage.
        
        Args:
            root_path: Root directory for archives.
            max_size_bytes: Maximum file size (default 100MB).
        """
        self._root = Path(root_path)
        self._root.mkdir(parents=True, exist_ok=True)
        self._max_size = max_size_bytes
    
    async def save_new(
        self,
        student_id: str,
        assignment_id: str,
        filename: str,
        data: bytes
    ) -> StoredArtifact:
        """Save file to local filesystem."""
        # Validate size
        if len(data) > self._max_size:
            raise StorageSizeError(f"File too large: {len(data)} > {self._max_size}")
        
        # Calculate checksum
        checksum = hashlib.sha256(data).hexdigest()
        
        # Build safe path (prevent traversal)
        safe_path = self._build_safe_path(student_id, assignment_id, filename)
        full_path = self._root / safe_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file
        full_path.write_bytes(data)
        
        # Return metadata
        return StoredArtifact(
            path=str(safe_path),
            size_bytes=len(data),
            checksum_sha256=checksum,
            storage_backend="local_fs",
            stored_at=datetime.utcnow()
        )
    
    async def save_new_streaming(
        self,
        student_id: str,
        assignment_id: str,
        filename: str,
        data_stream: AsyncIterator[bytes],
        expected_size: int | None = None
    ) -> StoredArtifact:
        """Save file via streaming (chunk by chunk)."""
        safe_path = self._build_safe_path(student_id, assignment_id, filename)
        full_path = self._root / safe_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Stream to disk + calculate checksum
        hasher = hashlib.sha256()
        total_size = 0
        
        with open(full_path, "wb") as f:
            async for chunk in data_stream:
                f.write(chunk)
                hasher.update(chunk)
                total_size += len(chunk)
                
                # Check size limit
                if total_size > self._max_size:
                    full_path.unlink()  # Clean up
                    raise StorageSizeError(f"File too large: {total_size} > {self._max_size}")
        
        return StoredArtifact(
            path=str(safe_path),
            size_bytes=total_size,
            checksum_sha256=hasher.hexdigest(),
            storage_backend="local_fs",
            stored_at=datetime.utcnow()
        )
    
    def _build_safe_path(self, student_id: str, assignment_id: str, filename: str) -> Path:
        """Build safe path (prevent directory traversal)."""
        # Sanitize inputs
        safe_student = student_id.replace("..", "").replace("/", "_")
        safe_assignment = assignment_id.replace("..", "").replace("/", "_")
        safe_filename = Path(filename).name  # Only basename, no directories
        
        return Path(safe_student) / safe_assignment / safe_filename
```

### Usage Example (Application → Infrastructure)

```python
# Step 1: Application layer uses interface
class ReviewSubmissionUseCase:
    def __init__(self, storage: ReviewArchiveStorage):  # ← interface
        self._storage = storage
    
    async def execute(self, request: ReviewSubmissionRequest) -> ReviewResult:
        # Save new submission
        new_artifact = await self._storage.save_new(
            student_id=request.student_id,
            assignment_id=request.assignment_id,
            filename=request.filename,
            data=request.archive_bytes
        )
        
        # Save logs (after review)
        logs_artifact = await self._storage.save_logs(
            student_id=request.student_id,
            assignment_id=request.assignment_id,
            filename="review_logs.txt",
            data=review_logs.encode()
        )
        
        return ReviewResult(artifacts=[new_artifact, logs_artifact])

# Step 2: Presentation layer uses streaming for large files
@router.post("/review/upload")
async def upload_review(
    student_id: str,
    assignment_id: str,
    file: UploadFile,
    container: DIContainer = Depends(get_container)
):
    storage = container.review_archive_storage
    
    # Stream large file (avoid loading into memory)
    async def stream_chunks():
        async for chunk in file.stream():
            yield chunk
    
    artifact = await storage.save_new_streaming(
        student_id=student_id,
        assignment_id=assignment_id,
        filename=file.filename,
        data_stream=stream_chunks(),
        expected_size=file.size
    )
    
    return {"path": artifact.path, "checksum": artifact.checksum_sha256}
```

---

## Testing Strategy for Interfaces

### Unit Tests (with Test Doubles)

```python
# tests/doubles/in_memory_storage.py

class InMemoryReviewArchiveStorage:
    """Fake storage for fast unit tests."""
    
    def __init__(self):
        self._store: dict[str, bytes] = {}
        self._metadata: dict[str, StoredArtifact] = {}
    
    async def save_new(self, student_id, assignment_id, filename, data):
        key = f"{student_id}/{assignment_id}/{filename}"
        self._store[key] = data
        
        artifact = StoredArtifact(
            path=key,
            size_bytes=len(data),
            checksum_sha256=hashlib.sha256(data).hexdigest(),
            storage_backend="in_memory",
            stored_at=datetime.utcnow()
        )
        self._metadata[key] = artifact
        return artifact

# tests/unit/application/test_review_submission_use_case.py

@pytest.mark.asyncio
async def test_use_case_saves_artifacts():
    """Unit: Use case saves new submission and logs."""
    # Arrange
    storage = InMemoryReviewArchiveStorage()  # ← fast fake
    use_case = ReviewSubmissionUseCase(storage=storage)
    
    # Act
    result = await use_case.execute(request)
    
    # Assert
    assert len(storage._store) == 2  # submission + logs
    assert "alice/hw01/submission.zip" in storage._store
```

### Integration Tests (with Real Storage)

```python
# tests/integration/infrastructure/test_local_filesystem_storage.py

@pytest.mark.asyncio
async def test_storage_saves_file_to_disk(tmp_path):
    """Integration: Storage writes file to disk."""
    # Arrange
    storage = LocalFileSystemStorage(root_path=str(tmp_path))
    data = b"test archive content"
    
    # Act
    artifact = await storage.save_new(
        student_id="alice",
        assignment_id="hw01",
        filename="test.zip",
        data=data
    )
    
    # Assert
    assert (tmp_path / artifact.path).exists()
    assert (tmp_path / artifact.path).read_bytes() == data
    assert artifact.checksum_sha256 == hashlib.sha256(data).hexdigest()
```

---

## Summary of Changes (v2)

### Added (per Tech Lead feedback):

1. **`StoredArtifact` dataclass** — immutable metadata record
2. **Streaming API** — `save_new_streaming()` for large files (>10MB)
3. **Usage examples** — domain → application → infrastructure chains
4. **Security requirements** — explicit in interface docstrings
5. **Test doubles** — in-memory fakes for fast unit tests

### Clarified:

- `HomeworkReviewService` interface location: **domain** (not application)
- Storage path safety (prevent directory traversal)
- Streaming use case (avoid memory overhead for large files)

---

**Document Owner**: EP21 Architect  
**Last Updated**: 2025-11-11  
**Version**: 2.0

