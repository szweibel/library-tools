"""Live integration tests for Primo search.

These tests hit the actual Primo API using credentials from .env.
They may fail if the API is down or if search results change.
"""

import pytest
from library_tools.primo.tool import search_primo


@pytest.mark.asyncio
async def test_search_primo_basic():
    """Test basic Primo search with a common query."""
    result = await search_primo(query="python programming", limit=5)

    assert isinstance(result, str)
    assert "Found" in result or "No results" in result
    # Should not be an error message
    assert "error occurred" not in result.lower()


@pytest.mark.asyncio
async def test_search_primo_by_title():
    """Test Primo search filtering by title field."""
    result = await search_primo(
        query="Introduction to Algorithms",
        field="title",
        limit=3
    )

    assert isinstance(result, str)
    assert "Found" in result or "No results" in result


@pytest.mark.asyncio
async def test_search_primo_by_author():
    """Test Primo search filtering by author/creator field."""
    result = await search_primo(
        query="Butler",
        field="creator",
        limit=5
    )

    assert isinstance(result, str)
    assert "Found" in result or "No results" in result


@pytest.mark.asyncio
async def test_search_primo_exact_match():
    """Test Primo search with exact match operator."""
    result = await search_primo(
        query="Python",
        operator="exact",
        limit=5
    )

    assert isinstance(result, str)
    # Exact matches might return fewer or no results
    assert "Found" in result or "No results" in result


@pytest.mark.asyncio
async def test_search_primo_journals_only():
    """Test Primo search limited to journals."""
    result = await search_primo(
        query="science",
        journals_only=True,
        limit=5
    )

    assert isinstance(result, str)
    assert "Found" in result or "No results" in result
    # If results found, they should be journals
    if "Found" in result and "0 work(s)" not in result:
        assert "JOURNAL" in result or "Journal" in result or result.count("📰") > 0


@pytest.mark.asyncio
async def test_search_primo_isbn():
    """Test Primo search by ISBN."""
    # Using a well-known ISBN (The Pragmatic Programmer)
    result = await search_primo(
        query="9780135957059",
        field="isbn",
        limit=1
    )

    assert isinstance(result, str)
    assert "Found" in result or "No results" in result


@pytest.mark.asyncio
async def test_search_primo_subject():
    """Test Primo search by subject."""
    result = await search_primo(
        query="Computer Science",
        field="subject",
        limit=5
    )

    assert isinstance(result, str)
    assert "Found" in result or "No results" in result


@pytest.mark.asyncio
async def test_search_primo_empty_results():
    """Test Primo search that should return no results."""
    result = await search_primo(
        query="xyzabc123nonexistentquery999",
        limit=5
    )

    assert isinstance(result, str)
    assert "No results" in result or "Found 0" in result
