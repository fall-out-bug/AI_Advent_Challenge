"""Domain interface for secure storage operations.

This interface defines the contract for secure file system operations
in the domain layer. Implementations should be provided by infrastructure
layer.  # noqa: E501

Epic 21 · Stage 21_01c · Storage Abstraction
"""

# noqa: E501
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO, Optional, TextIO


# noqa: E501
# noqa: E501
class StorageService(ABC):
    """Service interface for secure storage operations.

    Purpose:
        Abstract file system operations to enable testing, security validation,
        and infrastructure flexibility. Provides secure temporary file handling,
        path validation, and cleanup.

    This interface ensures domain logic remains independent of
    specific storage implementations (local filesystem, cloud storage, etc.).

    Example:
        >>> service = SomeStorageService()
        >>> with service.create_temp_file('.zip') as temp_file:
        ...     temp_file.write(b'data')
        ...     path = temp_file.name
        >>> service.cleanup_temp_file(path)
    """

    @abstractmethod
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

    @abstractmethod
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

    @abstractmethod
    def validate_path_safe(self, path: Path) -> bool:
        """Validate that path is safe for operations.

        Args:
            path: Path to validate

        Returns:
            True if path is safe, False otherwise

        Security checks:
        - No path traversal (..)
        - Path within allowed directories
        - No symlinks to sensitive locations
        """

    @abstractmethod
    def cleanup_temp_file(self, path: Path, missing_ok: bool = True) -> None:
        """Securely cleanup temporary file.

        Args:
            path: Path to temporary file to remove
            missing_ok: Don't raise error if file doesn't exist

        Raises:
            StorageError: If cleanup fails
        """

    @abstractmethod
    def ensure_directory_exists(self, path: Path) -> None:
        """Ensure directory exists with proper permissions.

        Args:
            path: Directory path to create

        Raises:
            StorageError: If directory creation fails
        """

    @abstractmethod
    def get_secure_temp_dir(self) -> Path:
        """Get secure temporary directory path.

        Returns:
            Path to secure temporary directory

        Security:
        - Uses system temp directory or configured secure location
        - Validates directory permissions
        - Prefers shared volumes for multi-container setups
        """

    @abstractmethod
    def validate_file_access(self, path: Path, operation: str) -> bool:
        """Validate file access permissions for operation.

        Args:
            path: File path to check
            operation: Operation type ('read', 'write', 'execute')

        Returns:
            True if operation is allowed, False otherwise
        """


# noqa: E501
# noqa: E501
class StorageError(Exception):
    """Base exception for storage operations."""

    pass
