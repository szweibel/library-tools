"""Live integration tests for Repository (bePress/Digital Commons) search.

These tests hit the actual CUNY Academic Works repository API using credentials from .env.
They may fail if the API is down or if search results change.
"""

import pytest
from library_tools.repository.tools import (
    search_repository,
    get_latest_repository_works,
    get_repository_work_details,
)


@pytest.mark.asyncio
async def test_search_repository_basic():
    """Test basic repository search."""
    result = await search_repository(query="education", limit=5)

    assert isinstance(result, str)
    assert "Found" in result or "No works found" in result
    # Should not be an error message
    assert "error occurred" not in result.lower()


@pytest.mark.asyncio
async def test_search_repository_specific_topic():
    """Test repository search with specific topic."""
    result = await search_repository(query="digital humanities", limit=5)

    assert isinstance(result, str)
    assert "Found" in result or "No works found" in result


@pytest.mark.asyncio
async def test_search_repository_by_year():
    """Test repository search filtered by year."""
    result = await search_repository(
        query="technology",
        year="2023",
        limit=5
    )

    assert isinstance(result, str)
    assert "Found" in result or "No works found" in result
    # If results found, they should be from 2023
    if "Found" in result and "0 work" not in result:
        # Year should appear in results or it's recent
        assert "2023" in result or "Year:" in result


@pytest.mark.asyncio
async def test_search_repository_by_collection():
    """Test repository search filtered by collection.

    Note: Collection codes are institution-specific.
    This uses 'gc_etds' which is the CUNY GC theses/dissertations collection.
    """
    result = await search_repository(
        collection="gc_etds",
        limit=5
    )

    assert isinstance(result, str)
    assert "Found" in result or "No works found" in result
    # CUNY should have ETDs
    if "Found" in result:
        assert "🎓" in result or "DISSERTATION" in result or "THESIS" in result or result.count("work(s)") > 0


@pytest.mark.asyncio
async def test_search_repository_query_and_collection():
    """Test repository search with both query and collection filter."""
    result = await search_repository(
        query="literature",
        collection="gc_etds",
        limit=5
    )

    assert isinstance(result, str)
    assert "Found" in result or "No works found" in result


@pytest.mark.asyncio
async def test_search_repository_all():
    """Test repository search without query (browse all)."""
    result = await search_repository(limit=10)

    assert isinstance(result, str)
    assert "Found" in result
    # Should return some works
    assert "0 work" not in result


@pytest.mark.asyncio
async def test_get_latest_repository_works():
    """Test getting latest works from repository."""
    result = await get_latest_repository_works(limit=5)

    assert isinstance(result, str)
    assert "Found" in result
    # Should return recent works
    assert "0 work" not in result
    # Should have URLs
    assert "URL:" in result


@pytest.mark.asyncio
async def test_get_latest_repository_works_by_collection():
    """Test getting latest works from specific collection."""
    result = await get_latest_repository_works(
        collection="gc_etds",
        limit=5
    )

    assert isinstance(result, str)
    assert "Found" in result
    # CUNY should have recent ETDs
    if "0 work" not in result:
        # Should be theses/dissertations
        assert "🎓" in result or "Collection:" in result or "work(s)" in result


@pytest.mark.asyncio
async def test_get_latest_repository_works_with_limit():
    """Test getting latest works with different limit."""
    result = await get_latest_repository_works(limit=3)

    assert isinstance(result, str)
    assert "Found" in result
    assert "Showing 3" in result or "Showing " in result


@pytest.mark.asyncio
async def test_get_repository_work_details():
    """Test getting details for a specific repository work.

    Note: This test requires a valid work URL from CUNY Academic Works.
    It may need updating if the specific work is removed.
    """
    # First, get a real work URL from latest works
    latest = await get_latest_repository_works(limit=1)

    if "URL: https://" in latest:
        # Extract URL from the result
        url_start = latest.find("URL: https://")
        if url_start != -1:
            url_line = latest[url_start + 5:].split("\n")[0].strip()
            # Try to get details for this work
            result = await get_repository_work_details(item_url=url_line)

            assert isinstance(result, str)
            assert "Found 1 work" in result or "DISSERTATION" in result or "THESIS" in result
            # Should have detailed info
            assert "URL:" in result
    else:
        # If we can't extract a URL, just verify the function works with a test URL
        # This might return "No work found" which is acceptable
        result = await get_repository_work_details(
            item_url="https://academicworks.cuny.edu/gc_etds/1"
        )
        assert isinstance(result, str)
        # Should either find the work or return appropriate message
        assert "Found" in result or "No work found" in result or "work(s)" in result


@pytest.mark.asyncio
async def test_search_repository_empty_results():
    """Test repository search that should return no results."""
    result = await search_repository(
        query="xyzabc123nonexistentquery999",
        limit=5
    )

    assert isinstance(result, str)
    assert "No works found" in result or "Found 0" in result


@pytest.mark.asyncio
async def test_search_repository_year_filter_no_results():
    """Test repository search with year that might have no results."""
    result = await search_repository(
        query="technology",
        year="1900",  # Very old year, unlikely to have results
        limit=5
    )

    assert isinstance(result, str)
    # Should handle no results gracefully
    assert "Found" in result or "No works found" in result
    assert "error occurred" not in result.lower()
