"""
Tests for API key management functionality.
"""

from unittest.mock import patch, mock_open
from pathlib import Path

from shared_package.config.api_keys import (
    load_api_key_from_file,
    get_api_key,
    is_api_key_configured,
    get_available_external_apis,
)


class TestAPIKeyFileLoading:
    """Test API key loading from file."""

    def test_load_api_key_from_file_success(self):
        """Test successful API key loading from file."""
        file_content = "perplexity:test_key_123\nchadgpt:another_key_456\n"

<<<<<<< HEAD
        with patch("pathlib.Path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=file_content)):
=======
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data=file_content)),
        ):
>>>>>>> origin/master
            result = load_api_key_from_file(Path("test.txt"), "perplexity")
            assert result == "test_key_123"

    def test_load_api_key_from_file_chadgpt(self):
        """Test loading ChadGPT API key from file."""
        file_content = "perplexity:test_key_123\nchadgpt:another_key_456\n"

<<<<<<< HEAD
        with patch("pathlib.Path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data=file_content)):
=======
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("builtins.open", mock_open(read_data=file_content)),
        ):
>>>>>>> origin/master
            result = load_api_key_from_file(Path("test.txt"), "chadgpt")
            assert result == "another_key_456"

    def test_load_api_key_from_file_not_found(self):
        """Test API key loading when key not found."""
        file_content = "perplexity:test_key_123\n"

        with patch("builtins.open", mock_open(read_data=file_content)):
            result = load_api_key_from_file(Path("test.txt"), "chadgpt")
            assert result is None

    def test_load_api_key_from_file_empty_key(self):
        """Test API key loading with empty key."""
        file_content = "perplexity:\nchadgpt:another_key_456\n"

        with patch("builtins.open", mock_open(read_data=file_content)):
            result = load_api_key_from_file(Path("test.txt"), "perplexity")
            assert result is None

    def test_load_api_key_from_file_missing_file(self):
        """Test API key loading when file doesn't exist."""
        with patch("pathlib.Path.exists", return_value=False):
            result = load_api_key_from_file(Path("nonexistent.txt"), "perplexity")
            assert result is None

    def test_load_api_key_from_file_io_error(self):
        """Test API key loading with IO error."""
        with patch("builtins.open", side_effect=IOError("Permission denied")):
            result = load_api_key_from_file(Path("test.txt"), "perplexity")
            assert result is None


class TestAPIKeyManagement:
    """Test API key management functions."""

<<<<<<< HEAD
    @patch('shared_package.config.api_keys.load_api_key_from_file')
    @patch('shared_package.config.api_keys.os.getenv')
=======
    @patch("shared_package.config.api_keys.load_api_key_from_file")
    @patch("shared_package.config.api_keys.os.getenv")
>>>>>>> origin/master
    def test_get_api_key_from_file(self, mock_getenv, mock_load_file):
        """Test getting API key from file."""
        mock_load_file.return_value = "file_key_123"
        mock_getenv.return_value = None

        result = get_api_key("perplexity")
        assert result == "file_key_123"

<<<<<<< HEAD
    @patch('shared_package.config.api_keys.load_api_key_from_file')
    @patch('shared_package.config.api_keys.os.getenv')
=======
    @patch("shared_package.config.api_keys.load_api_key_from_file")
    @patch("shared_package.config.api_keys.os.getenv")
>>>>>>> origin/master
    def test_get_api_key_from_env(self, mock_getenv, mock_load_file):
        """Test getting API key from environment variable."""
        mock_load_file.return_value = None
        mock_getenv.return_value = "env_key_456"

        result = get_api_key("perplexity")
        assert result == "env_key_456"

<<<<<<< HEAD
    @patch('shared_package.config.api_keys.load_api_key_from_file')
    @patch('shared_package.config.api_keys.os.getenv')
=======
    @patch("shared_package.config.api_keys.load_api_key_from_file")
    @patch("shared_package.config.api_keys.os.getenv")
>>>>>>> origin/master
    def test_get_api_key_file_priority(self, mock_getenv, mock_load_file):
        """Test that file has priority over environment variable."""
        mock_load_file.return_value = "file_key_123"
        mock_getenv.return_value = "env_key_456"

        result = get_api_key("perplexity")
        assert result == "file_key_123"

<<<<<<< HEAD
    @patch('shared_package.config.api_keys.load_api_key_from_file')
    @patch('shared_package.config.api_keys.os.getenv')
=======
    @patch("shared_package.config.api_keys.load_api_key_from_file")
    @patch("shared_package.config.api_keys.os.getenv")
>>>>>>> origin/master
    def test_get_api_key_not_found(self, mock_getenv, mock_load_file):
        """Test getting API key when not found anywhere."""
        mock_load_file.return_value = None
        mock_getenv.return_value = None

        result = get_api_key("perplexity")
        assert result is None

<<<<<<< HEAD
    @patch('shared_package.config.api_keys.load_api_key_from_file')
    @patch('shared_package.config.api_keys.os.getenv')
    def test_get_api_key_chadgpt_env_var(self, mock_getenv, mock_load_file):
        """Test getting ChadGPT API key from environment variable."""
        mock_load_file.return_value = None
        mock_getenv.side_effect = lambda var: "chad_key_789" if var == "CHADGPT_API_KEY" else None
=======
    @patch("shared_package.config.api_keys.load_api_key_from_file")
    @patch("shared_package.config.api_keys.os.getenv")
    def test_get_api_key_chadgpt_env_var(self, mock_getenv, mock_load_file):
        """Test getting ChadGPT API key from environment variable."""
        mock_load_file.return_value = None
        mock_getenv.side_effect = lambda var: (
            "chad_key_789" if var == "CHADGPT_API_KEY" else None
        )
>>>>>>> origin/master

        result = get_api_key("chadgpt")
        assert result == "chad_key_789"

<<<<<<< HEAD
    @patch('shared_package.config.api_keys.get_api_key')
=======
    @patch("shared_package.config.api_keys.get_api_key")
>>>>>>> origin/master
    def test_is_api_key_configured_true(self, mock_get_key):
        """Test API key configuration check when key is configured."""
        mock_get_key.return_value = "test_key_123"

        result = is_api_key_configured("perplexity")
        assert result is True

<<<<<<< HEAD
    @patch('shared_package.config.api_keys.get_api_key')
=======
    @patch("shared_package.config.api_keys.get_api_key")
>>>>>>> origin/master
    def test_is_api_key_configured_false(self, mock_get_key):
        """Test API key configuration check when key is not configured."""
        mock_get_key.return_value = None

        result = is_api_key_configured("perplexity")
        assert result is False

<<<<<<< HEAD
    @patch('shared_package.config.api_keys.get_api_key')
=======
    @patch("shared_package.config.api_keys.get_api_key")
>>>>>>> origin/master
    def test_is_api_key_configured_empty(self, mock_get_key):
        """Test API key configuration check when key is empty."""
        mock_get_key.return_value = ""

        result = is_api_key_configured("perplexity")
        assert result is False

<<<<<<< HEAD
    @patch('shared_package.config.api_keys.get_api_key')
=======
    @patch("shared_package.config.api_keys.get_api_key")
>>>>>>> origin/master
    def test_is_api_key_configured_whitespace(self, mock_get_key):
        """Test API key configuration check when key is whitespace only."""
        mock_get_key.return_value = "   "

        result = is_api_key_configured("perplexity")
        assert result is False


class TestExternalAPIAvailability:
    """Test external API availability functions."""

<<<<<<< HEAD
    @patch('shared_package.config.api_keys.is_api_key_configured')
=======
    @patch("shared_package.config.api_keys.is_api_key_configured")
>>>>>>> origin/master
    def test_get_available_external_apis_all_configured(self, mock_is_configured):
        """Test getting available external APIs when all are configured."""
        mock_is_configured.side_effect = lambda api: api in ["perplexity", "chadgpt"]

        result = get_available_external_apis()

<<<<<<< HEAD
        assert result == {
            "perplexity": True,
            "chadgpt": True
        }

    @patch('shared_package.config.api_keys.is_api_key_configured')
=======
        assert result == {"perplexity": True, "chadgpt": True}

    @patch("shared_package.config.api_keys.is_api_key_configured")
>>>>>>> origin/master
    def test_get_available_external_apis_none_configured(self, mock_is_configured):
        """Test getting available external APIs when none are configured."""
        mock_is_configured.return_value = False

        result = get_available_external_apis()

<<<<<<< HEAD
        assert result == {
            "perplexity": False,
            "chadgpt": False
        }

    @patch('shared_package.config.api_keys.is_api_key_configured')
=======
        assert result == {"perplexity": False, "chadgpt": False}

    @patch("shared_package.config.api_keys.is_api_key_configured")
>>>>>>> origin/master
    def test_get_available_external_apis_partial(self, mock_is_configured):
        """Test getting available external APIs when only some are configured."""
        mock_is_configured.side_effect = lambda api: api == "perplexity"

        result = get_available_external_apis()

<<<<<<< HEAD
        assert result == {
            "perplexity": True,
            "chadgpt": False
        }
=======
        assert result == {"perplexity": True, "chadgpt": False}
>>>>>>> origin/master
