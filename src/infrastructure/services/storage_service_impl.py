"""Infrastructure implementation of StorageService with security focus.

Provides secure file system operations with path validation and access control.
Following Clean Architecture: Infrastructure layer implements domain interfaces.

Epic 21 · Stage 21_01c · Storage Abstraction
"""

# noqa: E501
import logging
import tempfile
from pathlib import Path
from typing import BinaryIO, Optional, TextIO

# noqa: E501
from src.domain.interfaces.storage_service import StorageError, StorageService

# noqa: E501
logger = logging.getLogger(__name__)


# noqa: E501
# noqa: E501
class StorageServiceImpl(StorageService):
    """Infrastructure implementation of StorageService with security focus.

    Purpose:
        Provides secure file system operations with comprehensive validation,
        path traversal prevention, and proper cleanup. Implements defense-in-depth
        security measures for file operations.

    Attributes:
        allowed_base_dirs: List of allowed base directories for operations
        max_temp_file_size: Maximum size for temporary files (bytes)
        secure_temp_dir: Preferred secure temporary directory
    """

    def __init__(
        self,
        allowed_base_dirs: Optional[list[Path]] = None,
        max_temp_file_size: int = 100 * 1024 * 1024,  # 100MB
        secure_temp_dir: Optional[Path] = None,
    ):
        """Initialize storage service with security configuration.

        Args:
            allowed_base_dirs: Allowed base directories (default: system temp + /app/archive)
            max_temp_file_size: Maximum temporary file size in bytes
            secure_temp_dir: Preferred secure temp directory (/app/archive if available)
        """
        self.allowed_base_dirs = allowed_base_dirs or [
            Path("/tmp"),
            (
                Path("/app/archive")
                if Path("/app/archive").exists()
                else Path(tempfile.gettempdir())
            ),
        ]
        self.max_temp_file_size = max_temp_file_size
        self.secure_temp_dir = secure_temp_dir or self._get_secure_temp_dir()

    def create_temp_file(
        self,
        suffix: str = "",
        prefix: str = "temp_",
        content: Optional[bytes] = None,
    ) -> BinaryIO:
        """Create secure temporary file with optional content.

        Args:
            suffix: File extension (e.g., '.zip', '.md')
            prefix: File prefix for identification
            content: Optional binary content to write

        Returns:
            Open binary file handle (caller responsible for closing)

        Raises:
            StorageError: If file creation fails or path is invalid
        """
        try:
            # Validate suffix for security
            if self._contains_path_traversal(suffix):
                raise StorageError(f"Invalid file suffix: {suffix}")

            # Create temp file in secure location
            temp_dir = self.get_secure_temp_dir()
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,  # We'll manage cleanup manually
                suffix=suffix,
                prefix=prefix,
                dir=str(temp_dir),
                mode="wb+",
            )

            # Validate created path
            temp_path = Path(temp_file.name)
            if not self.validate_path_safe(temp_path):
                temp_file.close()
                temp_path.unlink(missing_ok=True)
                raise StorageError(f"Created unsafe temporary file path: {temp_path}")

            # Write content if provided
            if content is not None:
                if len(content) > self.max_temp_file_size:
                    temp_file.close()
                    temp_path.unlink(missing_ok=True)
                    raise StorageError(
                        f"Content size {len(content)} exceeds maximum {self.max_temp_file_size}"
                    )

                temp_file.write(content)
                temp_file.flush()

            logger.debug(f"Created secure temp file: {temp_path}")
            return temp_file

        except Exception as e:
            logger.error(f"Failed to create temp file: {e}", exc_info=True)
            raise StorageError(f"Failed to create temporary file: {e}") from e

    def create_temp_text_file(
        self,
        suffix: str = ".txt",
        prefix: str = "temp_",
        content: Optional[str] = None,
        encoding: str = "utf-8",
    ) -> TextIO:
        """Create secure temporary text file with optional content.

        Args:
            suffix: File extension (e.g., '.md', '.txt')
            prefix: File prefix for identification
            content: Optional text content to write
            encoding: Text encoding

        Returns:
            Open text file handle (caller responsible for closing)

        Raises:
            StorageError: If file creation fails or path is invalid
        """
        try:
            # Validate suffix
            if self._contains_path_traversal(suffix):
                raise StorageError(f"Invalid file suffix: {suffix}")

            # Create temp file
            temp_dir = self.get_secure_temp_dir()
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=suffix,
                prefix=prefix,
                dir=str(temp_dir),
                mode="w+",
                encoding=encoding,
            )

            # Validate path
            temp_path = Path(temp_file.name)
            if not self.validate_path_safe(temp_path):
                temp_file.close()
                temp_path.unlink(missing_ok=True)
                raise StorageError(f"Created unsafe temporary file path: {temp_path}")

            # Write content if provided
            if content is not None:
                if len(content.encode(encoding)) > self.max_temp_file_size:
                    temp_file.close()
                    temp_path.unlink(missing_ok=True)
                    raise StorageError(
                        f"Content size exceeds maximum {self.max_temp_file_size}"
                    )

                temp_file.write(content)
                temp_file.flush()

            logger.debug(f"Created secure temp text file: {temp_path}")
            return temp_file

        except Exception as e:
            logger.error(
                f"Failed to create temp text file: {e}",
                exc_info=True,
            )
            raise StorageError(f"Failed to create temporary text file: {e}") from e

    def validate_path_safe(self, path: Path) -> bool:
        """Validate that path is safe for operations.

        Args:
            path: Path to validate

        Returns:
            True if path is safe, False otherwise
        """
        try:
            # Resolve any symlinks and relative components
            resolved_path = path.resolve()

            # Check for path traversal
            if self._contains_path_traversal(
                str(path)
            ) or self._contains_path_traversal(str(resolved_path)):
                logger.warning(f"Path traversal detected: {path}")
                return False

            # Check if path is within allowed directories
            for allowed_dir in self.allowed_base_dirs:
                try:
                    resolved_allowed = allowed_dir.resolve()
                    if resolved_path.is_relative_to(resolved_allowed):
                        return True
                except Exception:
                    continue

            logger.warning(f"Path outside allowed directories: {path}")
            return False

        except Exception as e:
            logger.error(f"Path validation failed for {path}: {e}")
            return False

    def cleanup_temp_file(self, path: Path, missing_ok: bool = True) -> None:
        """Securely cleanup temporary file.

        Args:
            path: Path to temporary file to remove
            missing_ok: Don't raise error if file doesn't exist

        Raises:
            StorageError: If cleanup fails
        """
        try:
            # Validate path before cleanup
            if not self.validate_path_safe(path):
                raise StorageError(f"Refusing to cleanup unsafe path: {path}")

            # Additional security: check if it's actually a temp file
            if not self._is_temp_file_pattern(path):
                logger.warning(f"Path doesn't match temp file pattern: {path}")
                # Still allow cleanup but log warning

            path.unlink(missing_ok=missing_ok)
            logger.debug(f"Cleaned up temp file: {path}")

        except Exception as e:
            logger.error(
                f"Failed to cleanup temp file {path}: {e}",
                exc_info=True,
            )
            if not missing_ok:
                raise StorageError(f"Failed to cleanup temporary file: {e}") from e

    def ensure_directory_exists(self, path: Path) -> None:
        """Ensure directory exists with proper permissions.

        Args:
            path: Directory path to create

        Raises:
            StorageError: If directory creation fails
        """
        try:
            # Validate path safety
            if not self.validate_path_safe(path):
                raise StorageError(
                    f"Refusing to create directory at unsafe path: {path}"
                )

            # Create directory with secure permissions
            path.mkdir(parents=True, exist_ok=True)

            # Validate permissions (should be writable by owner)
            if not self.validate_file_access(path, "write"):
                raise StorageError(f"Created directory lacks write permissions: {path}")

            logger.debug(f"Ensured directory exists: {path}")

        except Exception as e:
            logger.error(
                f"Failed to create directory {path}: {e}",
                exc_info=True,
            )
            raise StorageError(f"Failed to create directory: {e}") from e

    def get_secure_temp_dir(self) -> Path:
        """Get secure temporary directory path.

        Returns:
            Path to secure temporary directory
        """
        return self.secure_temp_dir

    def validate_file_access(self, path: Path, operation: str) -> bool:
        """Validate file access permissions for operation.

        Args:
            path: File path to check
            operation: Operation type ('read', 'write', 'execute')

        Returns:
            True if operation is allowed, False otherwise
        """
        try:
            # Check if path exists (for read/write operations)
            if operation in ("read", "write"):
                if not path.exists():
                    # For non-existent files, check parent directory
                    # permissions
                    path = path.parent

            # Check POSIX permissions
            stat_info = path.stat()

            # For simplicity, check if owner has permissions
            # In production, you'd want more sophisticated permission checking
            mode = stat_info.st_mode

            if operation == "read":
                return bool(mode & 0o400)  # Owner read permission
            elif operation == "write":
                return bool(mode & 0o200)  # Owner write permission
            elif operation == "execute":
                return bool(mode & 0o100)  # Owner execute permission
            else:
                return False

        except Exception as e:
            logger.error(f"File access validation failed for {path}: {e}")
            return False

    def _get_secure_temp_dir(self) -> Path:
        """Determine secure temporary directory."""
        # Prefer shared volume for multi-container setups
        shared_archive = Path("/app/archive")
        if shared_archive.exists() and shared_archive.is_dir():
            return shared_archive

        # Fallback to system temp
        return Path(tempfile.gettempdir())

    def _contains_path_traversal(self, path_str: str) -> bool:
        """Check if path contains traversal attempts."""
        # Check for .. components that could escape allowed directories
        if ".." in path_str:
            return True

        # Check for drive letters (Windows)
        if len(path_str) >= 3 and path_str[1:3] == ":\\":
            return True

        # Absolute paths are allowed if they are within allowed directories
        # The validation is done in validate_path_safe by checking
        # is_relative_to
        return False

    def _is_temp_file_pattern(self, path: Path) -> bool:
        """Check if path matches temporary file naming pattern."""
        filename = path.name

        # Check for common temp file prefixes
        temp_prefixes = ["temp_", "homework_review_", "tmp"]

        return any(filename.startswith(prefix) for prefix in temp_prefixes)
