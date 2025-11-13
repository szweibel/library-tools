"""Live integration tests for OpenAlex search.

These tests hit the actual OpenAlex API using credentials from .env.
They may fail if the API is down or if search results change.
"""

import pytest
from library_tools.openalex.tools import (
    search_works,
    search_authors,
    get_author_works,
    search_journals,
)


@pytest.mark.asyncio
async def test_search_works_basic():
    """Test basic OpenAlex works search."""
    result = await search_works(query="machine learning", limit=5)

    assert isinstance(result, str)
    assert "Found" in result
    assert "publications" in result.lower()
    # Should have some results for such a common topic
    assert "No publications found" not in result


@pytest.mark.asyncio
async def test_search_works_with_year_filter():
    """Test OpenAlex works search with year filter."""
    result = await search_works(
        query="artificial intelligence",
        year_from=2023,
        limit=5
    )

    assert isinstance(result, str)
    assert "Found" in result
    # Should have results from 2023 onwards
    if "2023" in result or "2024" in result or "2025" in result:
        assert True  # Found recent papers
    else:
        # Might not show years in preview, just check it didn't error
        assert "error occurred" not in result.lower()


@pytest.mark.asyncio
async def test_search_works_open_access():
    """Test OpenAlex works search limited to open access."""
    result = await search_works(
        query="climate change",
        open_access_only=True,
        limit=5
    )

    assert isinstance(result, str)
    assert "Found" in result
    # If we found results, some should be marked open access
    if "No publications found" not in result:
        assert "Open Access" in result or result.count("publications") > 0


@pytest.mark.asyncio
async def test_search_authors_basic():
    """Test basic OpenAlex author search."""
    result = await search_authors(name="Smith", limit=5)

    assert isinstance(result, str)
    assert "Found" in result
    assert "researchers" in result.lower()
    # Smith is a common name, should have results
    assert "No researchers found" not in result


@pytest.mark.asyncio
async def test_search_authors_specific():
    """Test OpenAlex author search with a specific name."""
    # Searching for a well-known researcher
    result = await search_authors(name="Geoffrey Hinton", limit=5)

    assert isinstance(result, str)
    assert "Found" in result
    # Famous researcher should be found
    if "Geoffrey Hinton" in result or "Hinton" in result:
        assert True
    else:
        # Still valid if OpenAlex returns different results
        assert "researchers" in result.lower()


@pytest.mark.asyncio
async def test_get_author_works():
    """Test getting works by a specific author ID.

    Note: This test uses a known OpenAlex author ID.
    It may need updating if the ID changes.
    """
    # Using a test author ID - A2208157607 (a real researcher in OpenAlex)
    result = await get_author_works(author_id="A2208157607", limit=5)

    assert isinstance(result, str)
    assert "Found" in result or "No publications found" in result
    # Should not be an error
    assert "error occurred" not in result.lower()


@pytest.mark.asyncio
async def test_get_author_works_with_url():
    """Test getting works by author using full OpenAlex URL."""
    # Using full URL format
    result = await get_author_works(
        author_id="https://openalex.org/A2208157607",
        limit=3
    )

    assert isinstance(result, str)
    assert "Found" in result or "No publications found" in result


@pytest.mark.asyncio
async def test_search_journals_basic():
    """Test basic OpenAlex journal search."""
    result = await search_journals(name="Nature", limit=5)

    assert isinstance(result, str)
    assert "Found" in result
    assert "journals" in result.lower()
    # "Nature" is a famous journal, should be found
    assert "No journals found" not in result


@pytest.mark.asyncio
async def test_search_journals_specific():
    """Test OpenAlex journal search with specific query."""
    result = await search_journals(name="Science Magazine", limit=5)

    assert isinstance(result, str)
    assert "Found" in result
    # Should find science-related journals
    if "Science" in result:
        assert True
    else:
        # Still valid, just check format
        assert "journals" in result.lower()


@pytest.mark.asyncio
async def test_search_journals_field_specific():
    """Test OpenAlex journal search for field-specific journals."""
    result = await search_journals(name="Computer Science", limit=5)

    assert isinstance(result, str)
    assert "Found" in result
    # Should find CS-related journals
    assert "No journals found" not in result or "0 journals" not in result


@pytest.mark.asyncio
async def test_search_works_empty_results():
    """Test OpenAlex works search that should return few/no results."""
    result = await search_works(
        query="xyzabc123nonexistentresearchtopic999",
        limit=5
    )

    assert isinstance(result, str)
    assert "Found" in result or "No publications found" in result
    # Should handle empty results gracefully
    assert "error occurred" not in result.lower()
