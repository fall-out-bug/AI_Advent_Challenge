# Docstring FAQ · Epic 21

**Purpose**: Answer edge-case questions about docstring template requirements.

**Status**: Draft (awaiting Tech Lead decision on Option A/B/C)

---

## Quick Reference

| Question | Answer | Option |
|----------|--------|--------|
| Function doesn't raise exceptions — what to write in `Raises:`? | Omit section | B, C |
| Internal/private function — what to write in `Example:`? | Link to tests | B |
| Function with 10+ parameters — how to document `Args:`? | Group by category | All |
| Async function — special docstring format? | No, standard template | All |
| Property/attribute — needs docstring? | Yes, brief only | All |

---

## Template Reminder

```python
def function_name(param: type) -> return_type:
    """Brief description (one line, no period).

    Purpose:
        Detailed explanation of what the function does and why.

    Args:
        param: Parameter description with semantic meaning.

    Returns:
        Return value description (structure and semantics).

    Raises:
        ExceptionType: When this exception is raised.

    Example:
        >>> result = function_name("example")
        >>> result
        'expected_output'
    """
```

---

## FAQ by Section

### Q1: Brief Summary

**Q**: How brief is "brief"?  
**A**: ≤80 characters, one line, no period at end.

**Good**:
```python
"""Calculate checksum for file content"""
```

**Bad**:
```python
"""This function calculates a SHA-256 checksum for the provided file content 
and returns it as a hexadecimal string."""  # Too long, multiple lines
```

---

### Q2: Purpose Section

**Q**: What if "Brief" already explains everything?  
**A**: Still include `Purpose:` if function is public. Expand on "why" (not just "what").

**Example**:
```python
def validate_archive_size(data: bytes, max_size: int) -> None:
    """Validate archive size against limit.
    
    Purpose:
        Prevent disk exhaustion attacks by rejecting oversized archives
        before writing to storage. Complies with operations.md §4 security
        requirements (max 100MB per archive).
    
    Args:
        data: Archive content.
        max_size: Maximum allowed size in bytes.
    
    Raises:
        StorageSizeError: If data exceeds max_size.
    """
```

---

### Q3: Args Section

**Q**: Function has 10+ parameters — how to avoid bloat?  
**A**: Group by category or use `**kwargs` with reference.

**Option 1: Group semantically**
```python
def create_review(
    student_id: str,
    assignment_id: str,
    new_zip: bytes,
    previous_zip: bytes,
    logs: bytes,
    enable_pass4: bool,
    enable_caching: bool,
    timeout_seconds: int
) -> ReviewResult:
    """Create review with multiple artifacts.
    
    Args:
        Student/Assignment identifiers:
            student_id: Student identifier.
            assignment_id: Assignment identifier.
        
        Artifacts:
            new_zip: New submission archive.
            previous_zip: Previous submission for comparison.
            logs: Review execution logs.
        
        Options:
            enable_pass4: Enable Pass 4 (log analysis).
            enable_caching: Cache intermediate results.
            timeout_seconds: Review timeout.
    """
```

**Option 2: Extract options object**
```python
@dataclass
class ReviewOptions:
    """Options for review creation."""
    enable_pass4: bool = True
    enable_caching: bool = False
    timeout_seconds: int = 300

def create_review(
    student_id: str,
    assignment_id: str,
    artifacts: ReviewArtifacts,
    options: ReviewOptions = ReviewOptions()
) -> ReviewResult:
    """Create review with artifacts.
    
    Args:
        student_id: Student identifier.
        assignment_id: Assignment identifier.
        artifacts: Submission artifacts (new, previous, logs).
        options: Review options (see ReviewOptions for details).
    """
```

---

### Q4: Returns Section

**Q**: Function returns `None` — what to write?  
**A**: Describe side effect instead.

**Example**:
```python
async def save(self, context: DialogContext) -> None:
    """Save dialog context.
    
    Returns:
        None. Context is persisted to storage.
    """
```

**Q**: Function returns complex structure — how much detail?  
**A**: Describe structure, link to type for full details.

**Example**:
```python
def analyze_logs(logs: str) -> LogAnalysisResult:
    """Analyze review logs.
    
    Returns:
        LogAnalysisResult with:
        - errors: List of detected errors
        - warnings: List of warnings
        - metrics: Dict of extracted metrics
        
        See LogAnalysisResult dataclass for field details.
    """
```

---

### Q5: Raises Section

**Q**: Function doesn't raise exceptions — what to write?  
**A**: **Depends on chosen option** (Tech Lead decides):

#### Option A: Strict (all sections mandatory)
```python
def safe_operation() -> None:
    """Operation that never fails.
    
    Raises:
        None
    """
```

#### Option B: Pragmatic (recommended)
```python
def safe_operation() -> None:
    """Operation that never fails.
    
    Purpose:
        ... (no Raises section if no exceptions)
    """
```

#### Option C: Flexible
- Omit `Raises:` section entirely if no exceptions

**Current status**: Awaiting Tech Lead decision.

**Q**: Function raises multiple exceptions — how to organize?  
**A**: Group by category if >3 exceptions.

**Example**:
```python
async def save_archive(data: bytes) -> StoredArtifact:
    """Save archive to storage.
    
    Raises:
        Validation errors:
            StorageSizeError: If data exceeds max size.
            StorageChecksumError: If checksum validation fails.
        
        Security errors:
            StorageSecurityError: If malware detected.
        
        I/O errors:
            StoragePermissionError: If write permission denied.
            StorageDiskFullError: If insufficient disk space.
    """
```

---

### Q6: Example Section

**Q**: What if function is internal/private (`_function`)?  
**A**: **Depends on chosen option**:

#### Option A: Strict
```python
def _internal_helper() -> None:
    """Internal helper.
    
    Example:
        Internal use only. No public example provided.
    """
```

#### Option B: Pragmatic (recommended)
```python
def _internal_helper() -> None:
    """Internal helper.
    
    Purpose:
        Used by PublicClass.public_method() for X processing.
    
    Note:
        Internal use only.
        See tests/unit/test_module.py::test_internal_helper for usage.
    """
```

#### Option C: Flexible
- Omit `Example:` for private functions

**Current status**: Awaiting Tech Lead decision.

**Q**: Example is too long (>10 lines) — what to do?  
**A**: Extract to separate doc or link to integration test.

**Example**:
```python
async def create_review_with_all_options(...) -> ReviewResult:
    """Create review with comprehensive options.
    
    Example:
        Basic usage:
        >>> result = await create_review(student_id="alice", ...)
        
        For advanced examples with all options, see:
        tests/integration/test_review_creation_advanced.py
    """
```

**Q**: Example code can't be run in REPL (requires async, database, etc.) — what to do?  
**A**: Mark as pseudo-code or reference tests.

**Example**:
```python
async def database_operation() -> Result:
    """Perform database operation.
    
    Example:
        Pseudo-code (requires database setup):
        >>> async with database.session() as session:
        ...     result = await database_operation()
        ...     print(result)
        
        For runnable example, see:
        tests/integration/test_database_operations.py
    """
```

---

### Q7: Async Functions

**Q**: Do async functions need special docstring format?  
**A**: No, use standard template. Mention async nature in `Purpose` if important.

**Example**:
```python
async def fetch_data(url: str) -> dict:
    """Fetch data from URL.
    
    Purpose:
        Async HTTP request to external service.
        Use `await` when calling this function.
    
    Args:
        url: Target URL.
    
    Returns:
        Parsed JSON response.
    
    Raises:
        httpx.HTTPError: If request fails.
    
    Example:
        >>> result = await fetch_data("https://api.example.com/data")
        >>> print(result['status'])
    """
```

---

### Q8: Properties and Attributes

**Q**: Do class properties need docstrings?  
**A**: Yes, but brief format is acceptable.

**Example**:
```python
class Container:
    @property
    def mongo_client(self) -> AsyncIOMotorClient:
        """MongoDB client (cached)."""
        return self._mongo_client
    
    @property
    def dialog_context_repo(self) -> DialogContextRepository:
        """Dialog context repository.
        
        Returns:
            Repository implementation based on feature flag
            USE_NEW_DIALOG_CONTEXT_REPO.
        """
        if self._settings.USE_NEW_DIALOG_CONTEXT_REPO:
            return MongoDialogContextRepository(...)
        return LegacyMongoAdapter(...)
```

**Q**: Dataclass fields — docstring format?  
**A**: Inline comments or class docstring.

**Example**:
```python
@dataclass
class StoredArtifact:
    """Metadata for stored archive.
    
    Attributes:
        path: Storage path (relative or absolute).
        size_bytes: File size in bytes.
        checksum_sha256: SHA-256 checksum.
        storage_backend: Backend type ("local_fs", "s3").
        stored_at: Upload timestamp (UTC).
    """
    path: str
    size_bytes: int
    checksum_sha256: str
    storage_backend: str
    stored_at: datetime
```

---

### Q9: Type Hints and Docstrings

**Q**: Should `Args:` repeat type hints?  
**A**: No, focus on semantic meaning (type hints cover types).

**Bad**:
```python
def process(data: bytes) -> str:
    """Process data.
    
    Args:
        data (bytes): Input data in bytes format.
    
    Returns:
        str: Processed data as string.
    """
```

**Good**:
```python
def process(data: bytes) -> str:
    """Process data.
    
    Args:
        data: Raw input data (will be decoded as UTF-8).
    
    Returns:
        Processed data with normalization applied.
    """
```

---

### Q10: Deprecation Warnings

**Q**: How to document deprecated functions?  
**A**: Add `Deprecated:` section after `Purpose:`.

**Example**:
```python
def old_function(x: int) -> int:
    """Legacy function.
    
    Purpose:
        Kept for backward compatibility.
    
    Deprecated:
        Since version 2.0.0. Use new_function() instead.
        Will be removed in version 3.0.0.
    
    Args:
        x: Input value.
    
    Returns:
        Processed value.
    
    Example:
        >>> # Old way (deprecated)
        >>> result = old_function(42)
        >>> 
        >>> # New way (recommended)
        >>> result = new_function(value=42)
    """
    warnings.warn(
        "old_function is deprecated, use new_function",
        DeprecationWarning,
        stacklevel=2
    )
    return new_function(value=x)
```

---

## Validation Tools

### Automated Checks (CI)

```bash
# Check docstring format (pydocstyle)
pydocstyle src/ --convention=google

# Check type hints present
mypy src/ --strict

# Custom linter (check all sections present)
poetry run python scripts/quality/check_docstrings.py --require-examples
```

### Manual Review Checklist

When reviewing PR with new/updated docstrings:

- [ ] Brief summary ≤80 chars, no period
- [ ] `Purpose:` explains "why", not just "what"
- [ ] `Args:` describe semantic meaning (not types)
- [ ] `Returns:` describes structure/semantics
- [ ] `Raises:` documents exceptions [per chosen option]
- [ ] `Example:` is runnable or links to tests [per chosen option]
- [ ] Type hints match docstring descriptions
- [ ] No typos or grammar errors

---

## Decision Points for Tech Lead

### Raises Section (Item 3 from feedback)

**Question**: What to write in `Raises:` if function doesn't raise exceptions?

- [ ] **Option A**: Write `Raises: None` (strict, uniform)
- [ ] **Option B**: Omit `Raises:` section (pragmatic, recommended)
- [ ] **Option C**: Flexible per developer judgment

**Architect recommendation**: Option B

---

### Example Section (Item 3 from feedback)

**Question**: What to write in `Example:` for internal/private functions?

- [ ] **Option A**: Write "Internal use only" (strict)
- [ ] **Option B**: Link to tests: "See tests/unit/..." (pragmatic, recommended)
- [ ] **Option C**: Omit `Example:` for private functions

**Architect recommendation**: Option B

---

## References

- **Docstring Template**: `.cursor/rules/cursorrules-unified.md` (Python Zen Writer, Technical Writer)
- **PEP 257**: Docstring Conventions
- **Google Style Guide**: Python docstrings
- **Stage 21_02**: `stage_21_02_docstring_plan.md`

---

## Appendix: Full Example (Recommended Style)

```python
async def save_review_archive(
    storage: ReviewArchiveStorage,
    student_id: str,
    assignment_id: str,
    archive_data: bytes,
    options: StorageOptions | None = None
) -> StoredArtifact:
    """Save review submission archive to storage.
    
    Purpose:
        Persist student submission with integrity verification
        (checksum, optional AV scan). Supports multiple storage
        backends (local FS, S3) via adapter pattern.
    
    Args:
        storage: Storage adapter (injected via DI).
        student_id: Student identifier.
        assignment_id: Assignment identifier.
        archive_data: Submission archive content.
        options: Storage options (checksum, AV scan flags).
    
    Returns:
        StoredArtifact with:
        - path: Relative storage path
        - checksum_sha256: Calculated checksum
        - size_bytes: File size
        - stored_at: Upload timestamp
    
    Raises:
        StorageSizeError: If archive exceeds 100MB limit.
        StorageSecurityError: If AV scan detects malware.
        StoragePermissionError: If write permission denied.
    
    Example:
        >>> storage = LocalFileSystemStorage(root="/var/archives")
        >>> artifact = await save_review_archive(
        ...     storage=storage,
        ...     student_id="alice",
        ...     assignment_id="hw01",
        ...     archive_data=b"...",
        ...     options=StorageOptions(enable_av_scan=True)
        ... )
        >>> print(f"Saved to {artifact.path}")
        Saved to alice/hw01/submission.zip
    """
    opts = options or StorageOptions()
    
    artifact = await storage.save_new(
        student_id=student_id,
        assignment_id=assignment_id,
        filename="submission.zip",
        data=archive_data
    )
    
    logger.info(
        "Archive saved",
        extra={
            "student_id": student_id,
            "assignment_id": assignment_id,
            "checksum": artifact.checksum_sha256,
            "size_bytes": artifact.size_bytes,
        }
    )
    
    return artifact
```

---

**Document Owner**: EP21 Architect + Tech Lead  
**Status**: Draft (awaiting decisions on Options A/B/C)  
**Last Updated**: 2025-11-11

