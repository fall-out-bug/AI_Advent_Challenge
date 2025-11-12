# Component Design Specifications - Epic 21

## 1. Dialog Context Repository

### Overview
The Dialog Context Repository provides persistent storage for conversation state, enabling the bot to maintain context across messages and sessions.

### Interface Design
```python
class DialogContextRepository(Protocol):
    """Abstract repository for DialogContext persistence."""

    async def get_by_session(self, session_id: str) -> Optional[DialogContext]:
        """Retrieve dialog context by session identifier."""

    async def save(self, context: DialogContext) -> None:
        """Persist dialog context to storage."""

    async def delete(self, session_id: str) -> None:
        """Remove dialog context from storage."""
```

### Implementation: MongoDB Repository
```python
class MongoDialogContextRepository(DialogContextRepository):
    """MongoDB implementation of DialogContextRepository.

    Attributes:
        database: MongoDB database instance
        collection_name: Collection for dialog contexts
    """

    Features:
    - Automatic serialization/deserialization of DialogContext
    - Error handling with custom RepositoryError
    - Upsert operations for atomic saves
    - Structured logging for operations
```

### Data Model
```python
@dataclass
class DialogContext:
    user_id: str
    session_id: str
    state: DialogState
    data: Dict[str, Any]
    step_count: int

class DialogState(Enum):
    IDLE = "idle"
    TASK_CREATE_TITLE = "task_create_title"
    TASK_CREATE_DESC = "task_create_desc"
    HOMEWORK_REVIEW = "homework_review"
    # ... other states
```

### Security Considerations
- Session IDs used as primary keys
- No sensitive data stored in context
- MongoDB connection pooling for performance
- Input validation for session_id format

---

## 2. Homework Review Service

### Overview
The Homework Review Service orchestrates the complete homework review workflow, coordinating between external homework checker, MCP review tools, and secure file storage.

### Interface Design
```python
class HomeworkReviewService(Protocol):
    """Abstract service for homework review operations."""

    async def list_homeworks(self, days: int) -> Dict[str, Any]:
        """List recent homework submissions."""

    async def review_homework(self, context: DialogContext,
                            commit_hash: str) -> str:
        """Review homework by commit hash."""
```

### Implementation Architecture
```
HomeworkReviewServiceImpl
├── hw_checker: HomeworkCheckerProtocol
├── tool_client: ToolClientProtocol
└── storage_service: StorageService
```

### Workflow Sequence
1. **Download Archive**: Use HomeworkCheckerProtocol to fetch ZIP
2. **Secure Storage**: Save to temporary file via StorageService
3. **Review Execution**: Call MCP tool with archive path
4. **Result Processing**: Format markdown report for file sending
5. **Cleanup**: Remove temporary files securely

### Error Handling
- **404 Errors**: Commit not found → user-friendly message
- **Connection Errors**: Network issues → retry suggestions
- **Timeout Errors**: Long-running reviews → timeout handling
- **File Errors**: Storage issues → cleanup and retry

### Performance Considerations
- Streaming downloads to avoid memory exhaustion
- Configurable timeouts for external calls
- Secure temporary file cleanup
- Base64 encoding for file transmission

---

## 3. Storage Service

### Overview
The Storage Service provides secure file system operations with comprehensive security validation and resource protection.

### Interface Design
```python
class StorageService(Protocol):
    """Abstract service for secure storage operations."""

    def create_temp_file(self, suffix: str = "", prefix: str = "temp_",
                        content: Optional[bytes] = None) -> BinaryIO:
        """Create secure temporary binary file."""

    def create_temp_text_file(self, suffix: str = ".txt",
                             prefix: str = "temp_",
                             content: Optional[str] = None,
                             encoding: str = "utf-8") -> TextIO:
        """Create secure temporary text file."""

    def validate_path_safe(self, path: Path) -> bool:
        """Validate path is safe for operations."""

    def cleanup_temp_file(self, path: Path, missing_ok: bool = True) -> None:
        """Securely delete temporary file."""

    def ensure_directory_exists(self, path: Path) -> None:
        """Ensure directory exists with validation."""

    def get_secure_temp_dir(self) -> Path:
        """Return secure temporary directory."""

    def validate_file_access(self, path: Path,
                           operation: Literal["read", "write", "delete"]) -> None:
        """Validate file access permissions."""
```

### Security Features

#### Path Traversal Protection
- Blocks `..` components in paths
- Validates paths within allowed directories
- Prevents absolute path attacks
- Resolves symbolic links safely

#### Resource Limits
- Maximum file size limits (100MB default)
- Temporary directory quotas
- Permission validation before operations
- Secure cleanup with validation

#### Permission Validation
```python
def validate_file_access(self, path: Path, operation: str) -> None:
    """Check POSIX permissions for operation."""
    if operation == "read":
        if not os.access(path, os.R_OK):
            raise StorageError(f"Permission denied for read: {path}")
    # ... similar for write/delete
```

### Implementation Strategy
- Uses system temporary directories by default
- Prefers `/app/archive` for Docker environments
- Automatic cleanup with error handling
- Comprehensive logging for security events

---

## 4. Review Homework Use Case

### Overview
The Review Homework Use Case orchestrates the homework review business logic at the application layer, coordinating domain services according to Clean Architecture principles.

### Interface Design
```python
class ReviewHomeworkCleanUseCase:
    """Orchestrates homework review business logic."""

    def __init__(self, homework_review_service: HomeworkReviewService):
        self.homework_review_service = homework_review_service

    async def execute_review(self, context: DialogContext,
                           commit_hash: str) -> HomeworkReviewResult:
        """Execute homework review with validation and error handling."""
```

### Business Logic Flow
1. **Input Validation**: Validate commit hash format
2. **Service Orchestration**: Delegate to HomeworkReviewService
3. **Result Transformation**: Convert service output to DTO
4. **Error Handling**: Wrap exceptions with business context

### Data Transfer Objects
```python
@dataclass
class HomeworkReviewResult:
    success: bool
    markdown_report: Optional[str] = None
    filename: Optional[str] = None
    total_findings: int = 0

@dataclass
class HomeworkSubmissionList:
    total: int
    commits: List[Dict[str, Any]]
```

### Error Handling Strategy
- **ValueError**: Invalid input parameters
- **HomeworkReviewError**: Domain service failures
- **RuntimeError**: Unexpected system errors
- **Exception Chaining**: Preserve root cause information

### Testing Strategy
- **Unit Tests**: Mock HomeworkReviewService
- **Integration Tests**: Real service implementations
- **Error Path Tests**: All exception scenarios
- **Input Validation Tests**: Edge cases and invalid inputs

---

## 5. Dependency Injection Container

### Overview
The DI Container provides centralized dependency wiring with feature flag support for gradual rollout of new implementations.

### Configuration Management
```python
class Settings(BaseSettings):
    """Application settings with feature flags."""

    # Database
    mongodb_url: str = "mongodb://localhost:27017"

    # Epic 21 Feature Flags
    use_new_dialog_context_repo: bool = False
    use_new_homework_review_service: bool = False
    use_new_storage_service: bool = False
    use_decomposed_use_case: bool = False

    # HW Checker settings
    hw_checker_base_url: str = "http://hw_checker-mcp-server-1:8005"
```

### Component Wiring
```python
class DIContainer:
    """Manual dependency injection container."""

    @cached_property
    def dialog_context_repository(self) -> DialogContextRepository:
        """Dialog context repository with feature flag support."""
        if self.settings.use_new_dialog_context_repo:
            return MongoDialogContextRepository(self.mongodb)
        else:
            return LegacyDialogContextAdapter(self.mongodb)

    @cached_property
    def homework_review_service(self) -> HomeworkReviewService:
        """Homework review service with migration support."""
        if self.settings.use_new_homework_review_service:
            return HomeworkReviewServiceImpl(
                hw_checker=self.hw_checker_client,
                tool_client=self.tool_client,
                storage_service=self.storage_service,
            )
        else:
            return LegacyHomeworkReviewAdapter(
                hw_checker=self.hw_checker_client,
                tool_client=self.tool_client,
            )
```

### Legacy Adapters
During migration, legacy adapters provide new interfaces using existing code:
- **LegacyDialogContextAdapter**: Wraps direct MongoDB access
- **LegacyHomeworkReviewAdapter**: Uses existing HomeworkHandler logic
- **LegacyStorageAdapter**: Provides StorageService interface for direct file operations

### Benefits
- **Zero Downtime**: Gradual migration with feature flags
- **Testability**: Easy to inject test doubles
- **Maintainability**: Centralized dependency management
- **Flexibility**: Runtime configuration changes

---

## 6. Butler Orchestrator

### Overview
The Butler Orchestrator routes user messages to appropriate handlers based on conversation mode classification, coordinating all bot functionality.

### Refactored Architecture
```python
class ButlerOrchestrator:
    """Main orchestrator for Butler Agent."""

    def __init__(
        self,
        mode_classifier: ModeClassifier,
        task_handler: TaskHandler,
        data_handler: DataHandler,
        homework_handler: HomeworkHandler,
        chat_handler: ChatHandler,
        dialog_context_repository: DialogContextRepository,
    ):
        # Dependency injection of all handlers
        pass

    async def handle_user_message(self, message: str, user_id: str,
                                session_id: str) -> str:
        """Route message to appropriate handler based on context."""
        # 1. Load or create dialog context
        # 2. Classify message mode
        # 3. Route to appropriate handler
        # 4. Save updated context
        pass
```

### Message Routing Logic
```
Input: message, user_id, session_id
├── Load DialogContext from repository
├── Classify message mode (TASK/DATA/HOMEWORK/IDLE)
├── Route to handler:
│   ├── TASK → TaskHandler
│   ├── DATA → DataHandler
│   ├── HOMEWORK → HomeworkHandler (refactored)
│   └── IDLE → ChatHandler
├── Save updated context
└── Return response
```

### State Management
- **Context Persistence**: All state changes saved to repository
- **Session Continuity**: Context maintained across messages
- **Error Recovery**: Graceful fallback on context load failures
- **Performance**: Efficient context loading/caching

### Testing Strategy
- **Unit Tests**: Mock all dependencies, test routing logic
- **Integration Tests**: Real repository, mock handlers
- **Characterization Tests**: Preserve existing behavior
- **Error Path Tests**: Repository failures, invalid contexts

---

## 7. Security Assessment

### Threat Model
- **Path Traversal**: File system access outside allowed directories
- **Resource Exhaustion**: Large file uploads, memory exhaustion
- **Information Disclosure**: Error messages leaking sensitive data
- **Injection Attacks**: Command injection via file paths

### Security Controls Implemented

#### Input Validation
- **Path Validation**: `validate_path_safe()` blocks traversal attempts
- **Size Limits**: Maximum file sizes prevent resource exhaustion
- **Format Validation**: Commit hashes, session IDs validated
- **Permission Checks**: File access permissions verified

#### Secure Operations
- **Temporary Files**: Secure creation with proper permissions
- **Cleanup**: Automatic cleanup prevents resource leaks
- **Error Handling**: No sensitive data in error messages
- **Logging**: Security events logged without sensitive data

#### Defense in Depth
- **Multiple Validation Layers**: Client, service, and storage validation
- **Fail-Safe Defaults**: Secure fallbacks for all operations
- **Audit Trail**: Comprehensive logging for security events
- **Access Control**: Permission validation before operations

### Security Testing
- **Path Traversal Tests**: Attempted `../../../etc/passwd` attacks
- **Resource Limit Tests**: Large file upload attempts
- **Injection Tests**: Malformed input validation
- **Permission Tests**: Access control verification

---

## 8. Performance Considerations

### Scalability Targets
- **Response Time**: <500ms for typical operations
- **Concurrent Users**: Support 100+ simultaneous sessions
- **Storage Growth**: Efficient cleanup prevents disk exhaustion
- **Memory Usage**: Streaming for large file operations

### Optimization Strategies
- **Connection Pooling**: MongoDB connection reuse
- **Async Operations**: Non-blocking I/O for all external calls
- **Caching**: Context caching for frequent sessions
- **Streaming**: Large file downloads without memory buffering

### Monitoring Points
- **Service Metrics**: Response times, error rates
- **Resource Usage**: Memory, disk, connection pools
- **Business Metrics**: Reviews completed, files processed
- **Security Events**: Failed validation attempts, access denials

### Performance Testing
- **Load Testing**: Concurrent user simulation
- **Stress Testing**: Resource limit validation
- **Endurance Testing**: Long-running stability
- **Spike Testing**: Sudden load increases
