"""
Tests for lazy loading utilities.
"""

import pytest
import sys
import os
from unittest.mock import patch

from utils.lazy_imports import (
    LazyImport, 
    lazy_import, 
    conditional_import,
    get_shared_sdk_path,
    add_shared_sdk_to_path
)


class TestLazyImport:
    """Test LazyImport functionality."""
    
    def test_lazy_import_initialization(self):
        """Test LazyImport initialization."""
        lazy = LazyImport('os')
        assert lazy._module_name == 'os'
        assert lazy._module is None
    
    def test_lazy_import_attribute_access(self):
        """Test lazy import attribute access."""
        lazy = LazyImport('os')
        
        # First access should load the module
        path_sep = lazy.pathsep
        assert lazy._module is not None
        assert path_sep == os.pathsep
    
    def test_lazy_import_multiple_access(self):
        """Test multiple attribute access on same lazy import."""
        lazy = LazyImport('os')
        
        # Multiple accesses should use same module instance
        path_sep1 = lazy.pathsep
        path_sep2 = lazy.pathsep
        
        assert path_sep1 == path_sep2
        assert lazy._module is not None
    
    def test_lazy_import_nonexistent_module(self):
        """Test lazy import with nonexistent module."""
        lazy = LazyImport('nonexistent_module_12345')
        
        with pytest.raises(ImportError):
            _ = lazy.some_attribute


class TestLazyImportFunction:
    """Test lazy_import function."""
    
    def test_lazy_import_function(self):
        """Test lazy_import function."""
        lazy = lazy_import('os')
        assert isinstance(lazy, LazyImport)
        assert lazy._module_name == 'os'
    
    def test_lazy_import_function_usage(self):
        """Test lazy_import function usage."""
        lazy = lazy_import('sys')
        version = lazy.version
        assert isinstance(version, str)


class TestConditionalImport:
    """Test conditional_import function."""
    
    def test_conditional_import_success(self):
        """Test conditional import with existing module."""
        module = conditional_import('os')
        assert module is not None
        assert hasattr(module, 'path')
    
    def test_conditional_import_failure(self):
        """Test conditional import with nonexistent module."""
        module = conditional_import('nonexistent_module_12345')
        assert module is None
    
    def test_conditional_import_fallback(self):
        """Test conditional import with fallback."""
        fallback = "fallback_value"
        module = conditional_import('nonexistent_module_12345', fallback)
        assert module == fallback


class TestSharedSDKPath:
    """Test shared SDK path utilities."""
    
    def test_get_shared_sdk_path(self):
        """Test getting shared SDK path."""
        path = get_shared_sdk_path()
        assert isinstance(path, str)
        assert 'shared' in path
        assert os.path.isabs(path)
    
    def test_add_shared_sdk_to_path(self):
        """Test adding shared SDK to path."""
        original_path = sys.path.copy()
        
        try:
            add_shared_sdk_to_path()
            
            shared_path = get_shared_sdk_path()
            assert shared_path in sys.path
        finally:
            # Restore original path
            sys.path = original_path
    
    def test_add_shared_sdk_to_path_idempotent(self):
        """Test that adding shared SDK to path is idempotent."""
        original_path = sys.path.copy()
        
        try:
            add_shared_sdk_to_path()
            first_length = len(sys.path)
            
            add_shared_sdk_to_path()
            second_length = len(sys.path)
            
            assert first_length == second_length
        finally:
            sys.path = original_path


class TestLazyImportsIntegration:
    """Test lazy imports integration."""
    
    def test_lazy_imports_module_attributes(self):
        """Test that lazy imports module has expected attributes."""
        from utils import lazy_imports
        
        # These should be LazyImport instances
        assert isinstance(lazy_imports.httpx, LazyImport)
        assert isinstance(lazy_imports.asyncio, LazyImport)
        assert isinstance(lazy_imports.unicodedata, LazyImport)
        assert isinstance(lazy_imports.shutil, LazyImport)
        assert isinstance(lazy_imports.textwrap, LazyImport)
        assert isinstance(lazy_imports.functools, LazyImport)
        assert isinstance(lazy_imports.dataclasses, LazyImport)
    
    def test_lazy_imports_actual_usage(self):
        """Test actual usage of lazy imports."""
        from utils import lazy_imports
        
        # Test that we can access attributes
        assert hasattr(lazy_imports.httpx, 'AsyncClient')
        assert hasattr(lazy_imports.asyncio, 'run')
        assert hasattr(lazy_imports.unicodedata, 'normalize')
        assert hasattr(lazy_imports.shutil, 'get_terminal_size')
        assert hasattr(lazy_imports.textwrap, 'fill')
        assert hasattr(lazy_imports.functools, 'wraps')
        assert hasattr(lazy_imports.dataclasses, 'dataclass')
