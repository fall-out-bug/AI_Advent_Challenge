# Architecture Decision Records - Epic 21

## ADR-001: Clean Architecture Layering

### Context
The existing codebase had violations of Clean Architecture principles:
- Domain layer depended on infrastructure (MongoDB direct access)
- Business logic was scattered across layers
- No clear separation of concerns
- Tight coupling prevented safe refactoring

### Decision
Implement strict Clean Architecture with four layers:
- **Domain Layer**: Pure business logic, entities, value objects, interfaces
- **Application Layer**: Use cases orchestrating domain services
- **Infrastructure Layer**: External concerns (DB, APIs, file systems)
- **Presentation Layer**: API, CLI, bot interfaces

### Consequences
- ✅ **Positive**: Clear separation of concerns, testable components
- ✅ **Positive**: Easy to swap implementations (in-memory vs MongoDB)
- ✅ **Positive**: Domain logic isolated from external dependencies
- ⚠️ **Risk**: Initial complexity increase during transition
- ⚠️ **Mitigation**: Feature flags for gradual rollout

---

## ADR-002: Protocol-Based Interfaces

### Context
Traditional ABC interfaces create tight coupling and require inheritance.
The team needed flexible, composable interfaces that support dependency injection.

### Decision
Use `typing.Protocol` for structural typing instead of inheritance-based interfaces:
```python
class DialogContextRepository(Protocol):
    async def get_by_session(self, session_id: str) -> Optional[DialogContext]:
        ...

    async def save(self, context: DialogContext) -> None:
        ...
```

### Consequences
- ✅ **Positive**: Duck typing - any object with matching methods works
- ✅ **Positive**: No inheritance hierarchy required
- ✅ **Positive**: Easy mocking for testing
- ✅ **Positive**: Compatible with both sync and async implementations

---

## ADR-003: Manual Dependency Injection

### Context
The team considered several DI approaches:
- **Constructor Injection**: Manual, explicit dependencies
- **Framework-based DI**: Spring-like containers
- **Service Locator**: Global registry pattern

### Decision
Implement manual dependency injection with constructor injection:
```python
class ButlerOrchestrator:
    def __init__(
        self,
        mode_classifier: ModeClassifier,
        dialog_context_repository: DialogContextRepository,
        # ... other dependencies
    ):
        self.mode_classifier = mode_classifier
        self.dialog_context_repository = dialog_context_repository
```

### Rationale
- **Simplicity**: No framework dependencies or magic
- **Explicitness**: All dependencies visible in constructor
- **Testability**: Easy to inject mocks
- **Performance**: No runtime overhead
- **Debugging**: Clear dependency chains

### Consequences
- ✅ **Positive**: Zero runtime cost, full control
- ✅ **Positive**: Easy to understand and debug
- ✅ **Positive**: No external dependencies
- ⚠️ **Negative**: Manual wiring can be verbose
- ⚠️ **Mitigation**: Central container class for common configurations

---

## ADR-004: Feature Flags for Gradual Rollout

### Context
Epic 21 introduced significant architectural changes that needed safe deployment.
The team needed to avoid big-bang deployments and support rollback.

### Decision
Implement feature flags in environment configuration:
```python
class Settings(BaseSettings):
    use_new_dialog_context_repo: bool = False
    use_new_homework_review_service: bool = False
    use_new_storage_service: bool = False
    use_decomposed_use_case: bool = False
```

### Consequences
- ✅ **Positive**: Zero-downtime deployment capability
- ✅ **Positive**: Easy rollback if issues discovered
- ✅ **Positive**: Canary deployments per component
- ✅ **Positive**: Gradual migration without breaking changes

---

## ADR-005: Characterization Testing Strategy

### Context
Refactoring existing code without breaking functionality required capturing current behavior.
Traditional unit tests wouldn't catch subtle behavioral changes.

### Decision
Implement characterization tests that capture existing behavior before refactoring:
```python
def test_existing_behavior_preserved():
    # Capture current output/behavior
    result = existing_system.process(input)
    assert result == expected_current_behavior
```

### Consequences
- ✅ **Positive**: Safety net during refactoring
- ✅ **Positive**: Documents actual behavior, not intended behavior
- ✅ **Positive**: Prevents regressions during architectural changes
- ⚠️ **Negative**: Tests may capture bugs as "correct" behavior
- ⚠️ **Mitigation**: Code review of characterization test expectations

---

## ADR-006: Security-First Storage Abstraction

### Context
File operations in the legacy code had security vulnerabilities:
- No path traversal protection
- No permission validation
- Hardcoded temporary directories
- No size limits on file operations

### Decision
Create secure `StorageService` interface with comprehensive validation:
```python
class StorageService(Protocol):
    def validate_path_safe(self, path: Path) -> bool:
        """Check for path traversal attempts."""

    def create_temp_file(self, suffix: str = "", prefix: str = "temp_",
                        content: Optional[bytes] = None) -> BinaryIO:
        """Create secure temporary file with validation."""
```

### Implementation Features
- **Path Traversal Protection**: Blocks `..` and absolute paths outside allowed directories
- **Permission Validation**: Checks file access permissions before operations
- **Size Limits**: Prevents resource exhaustion attacks
- **Secure Defaults**: Uses system temporary directories with proper permissions

### Consequences
- ✅ **Positive**: Prevents common file system attacks
- ✅ **Positive**: Resource exhaustion protection
- ✅ **Positive**: Clear security boundaries
- ✅ **Positive**: Easy to audit and verify

---

## ADR-007: Error Handling Strategy

### Context
The existing error handling was inconsistent:
- Some places used bare `except:`
- Error messages leaked implementation details
- No structured error types
- Difficult to handle errors appropriately at different layers

### Decision
Implement structured error handling with custom exceptions:
```python
class StorageError(Exception):
    """Custom exception for storage service errors."""
    pass

class HomeworkReviewError(Exception):
    """Custom exception for homework review service errors."""
    pass
```

### Error Handling Patterns
- **Domain Layer**: Custom business exceptions
- **Application Layer**: Wraps domain exceptions with context
- **Infrastructure Layer**: Converts technical errors to domain exceptions
- **Presentation Layer**: User-friendly error messages

### Consequences
- ✅ **Positive**: Clear error contracts between layers
- ✅ **Positive**: Appropriate error handling at each layer
- ✅ **Positive**: User-friendly error messages
- ✅ **Positive**: Easy to add error monitoring/logging

---

## ADR-008: Pre-commit Quality Gates

### Context
Code quality issues were discovered late in the development process:
- Inconsistent formatting
- Missing type hints
- Poor docstring coverage
- Security vulnerabilities

### Decision
Implement comprehensive pre-commit hooks:
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 22.12.0
    hooks:
      - id: black
        args: [--line-length=88]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88]
```

### Consequences
- ✅ **Positive**: Catches issues before commit
- ✅ **Positive**: Consistent code formatting
- ✅ **Positive**: Automated quality checks
- ✅ **Positive**: Prevents technical debt accumulation

---

## ADR-009: Component Migration Strategy

### Context
Epic 21 required migrating existing functionality to new architecture without breaking production.

### Decision
Implement legacy adapters during transition:
```python
class LegacyDialogContextAdapter(DialogContextRepository):
    """Adapter providing new interface using old MongoDB code."""

    def __init__(self, mongodb):
        self.collection = mongodb.dialog_contexts

    async def get_by_session(self, session_id: str):
        # Use existing MongoDB logic
        doc = await self.collection.find_one({"session_id": session_id})
        # Convert to new format...
```

### Migration Phases
1. **Phase 1**: Implement new interfaces alongside existing code
2. **Phase 2**: Create legacy adapters for backward compatibility
3. **Phase 3**: Gradually enable new implementations via feature flags
4. **Phase 4**: Remove legacy code after successful rollout

### Consequences
- ✅ **Positive**: Zero downtime migration
- ✅ **Positive**: Easy rollback if issues discovered
- ✅ **Positive**: Can test new implementations in production
- ✅ **Positive**: Gradual confidence building

---

## ADR-010: Testing Pyramid Strategy

### Context
The team needed comprehensive testing coverage for architectural changes while maintaining fast feedback loops.

### Decision
Implement testing pyramid with clear responsibilities:

```
Characterization Tests (25)
├── Capture existing behavior
└── Prevent regressions during refactoring

Unit Tests (45)
├── Test individual components in isolation
├── Mock external dependencies
└── Fast feedback on logic changes

Integration Tests (25)
├── Test component interactions
├── Real dependencies where safe
└── End-to-end flows validation
```

### Test Organization
- **Unit Tests**: Pure logic, mocked dependencies
- **Integration Tests**: Component wiring, real databases
- **Characterization Tests**: Behavioral regression prevention
- **Performance Tests**: SLO validation (future)

### Consequences
- ✅ **Positive**: Fast feedback for development
- ✅ **Positive**: Confidence in refactoring
- ✅ **Positive**: Clear test responsibilities
- ✅ **Positive**: Easy to maintain and understand
