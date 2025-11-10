"""Case tests for channel search functionality.

Purpose:
    Validate that channel search finds expected channels for real-world examples.
    These tests verify recall = 100% for the 3 main test cases.
"""

import os
import pytest
from dotenv import load_dotenv

# Load environment variables for tests
load_dotenv()

from src.infrastructure.clients.telegram_utils import search_channels_by_name


@pytest.fixture(scope="module", autouse=True)
def ensure_env_vars():
    """Ensure required environment variables are set."""
    required_vars = ["TELEGRAM_API_ID", "TELEGRAM_API_HASH", "TELEGRAM_SESSION_STRING"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        pytest.skip(f"Missing required environment variables: {missing_vars}")


@pytest.mark.asyncio
async def test_case_krupnokalibernyj_perepoloh():
    """Test case: крупнокалиберный_переполох should find @bolshiepushki."""
    query = "крупнокалиберный_переполох"
    expected_username = "bolshiepushki"

    results = await search_channels_by_name(query, limit=5)

    # Should find at least one result
    assert len(results) > 0, f"No results found for query: {query}"

    # Check if expected username is in results
    found_usernames = [r.get("username") for r in results]
    assert expected_username in found_usernames, (
        f"Expected username '{expected_username}' not found in results. "
        f"Found usernames: {found_usernames}, query: {query}"
    )

    # Find the matching result
    matching_result = next(
        (r for r in results if r.get("username") == expected_username), None
    )
    assert (
        matching_result is not None
    ), f"Could not find result with username '{expected_username}'"

    # Verify it has required fields
    assert matching_result.get("title"), "Result should have title"
    assert matching_result.get("username") == expected_username
    assert matching_result.get("chat_id"), "Result should have chat_id"


@pytest.mark.asyncio
async def test_case_krupnokalibernyj_perepoloh_with_spaces():
    """Test case: крупнокалиберный переполох (with spaces) should find @bolshiepushki."""
    query = "крупнокалиберный переполох"
    expected_username = "bolshiepushki"

    results = await search_channels_by_name(query, limit=5)

    assert len(results) > 0, f"No results found for query: {query}"

    found_usernames = [r.get("username") for r in results]
    assert expected_username in found_usernames, (
        f"Expected username '{expected_username}' not found in results. "
        f"Found usernames: {found_usernames}, query: {query}"
    )


@pytest.mark.asyncio
async def test_case_degradat_natsiya():
    """Test case: Деградат нация should find @degradat1."""
    query = "Деградат нация"
    expected_username = "degradat1"

    results = await search_channels_by_name(query, limit=5)

    assert len(results) > 0, f"No results found for query: {query}"

    found_usernames = [r.get("username") for r in results]
    assert expected_username in found_usernames, (
        f"Expected username '{expected_username}' not found in results. "
        f"Found usernames: {found_usernames}, query: {query}"
    )


@pytest.mark.asyncio
async def test_case_degradat_natsiya_lowercase():
    """Test case: деградат нация (lowercase) should find @degradat1."""
    query = "деградат нация"
    expected_username = "degradat1"

    results = await search_channels_by_name(query, limit=5)

    assert len(results) > 0, f"No results found for query: {query}"

    found_usernames = [r.get("username") for r in results]
    assert expected_username in found_usernames, (
        f"Expected username '{expected_username}' not found in results. "
        f"Found usernames: {found_usernames}, query: {query}"
    )


@pytest.mark.asyncio
async def test_case_lvd():
    """Test case: ЛВД should find @thinkaboutism."""
    query = "ЛВД"
    expected_username = "thinkaboutism"

    results = await search_channels_by_name(query, limit=5)

    assert len(results) > 0, f"No results found for query: {query}"

    found_usernames = [r.get("username") for r in results]
    assert expected_username in found_usernames, (
        f"Expected username '{expected_username}' not found in results. "
        f"Found usernames: {found_usernames}, query: {query}"
    )


@pytest.mark.asyncio
async def test_case_lvd_lowercase():
    """Test case: лвд (lowercase) should find @thinkaboutism."""
    query = "лвд"
    expected_username = "thinkaboutism"

    results = await search_channels_by_name(query, limit=5)

    assert len(results) > 0, f"No results found for query: {query}"

    found_usernames = [r.get("username") for r in results]
    assert expected_username in found_usernames, (
        f"Expected username '{expected_username}' not found in results. "
        f"Found usernames: {found_usernames}, query: {query}"
    )


@pytest.mark.asyncio
async def test_case_recall_coverage():
    """Test case: Verify recall = 100% for all 3 main test cases."""
    test_cases = [
        ("крупнокалиберный_переполох", "bolshiepushki"),
        ("деградат нация", "degradat1"),
        ("лвд", "thinkaboutism"),
    ]

    failed_cases = []

    for query, expected_username in test_cases:
        results = await search_channels_by_name(query, limit=5)
        found_usernames = [r.get("username") for r in results]

        if expected_username not in found_usernames:
            failed_cases.append((query, expected_username, found_usernames))

    assert len(failed_cases) == 0, f"Recall is not 100%. Failed cases: {failed_cases}"
