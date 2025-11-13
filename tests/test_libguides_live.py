"""Live integration tests for LibGuides search.

These tests hit the actual LibGuides API using credentials from .env.
They may fail if the API is down or if search results change.
"""

import pytest
from library_tools.libguides.tools import search_databases, search_guides


@pytest.mark.asyncio
async def test_search_databases_basic():
    """Test basic LibGuides database search."""
    result = await search_databases(search="JSTOR", limit=5)

    assert isinstance(result, str)
    assert "Found" in result or "No databases found" in result
    # Should not be an error message
    assert "error occurred" not in result.lower()


@pytest.mark.asyncio
async def test_search_databases_by_subject():
    """Test LibGuides database search by subject."""
    result = await search_databases(search="psychology", limit=5)

    assert isinstance(result, str)
    assert "Found" in result or "No databases found" in result
    # Common subject should have some databases
    if "Found" in result and "0 database" not in result:
        assert "URL:" in result  # Should have database URLs


@pytest.mark.asyncio
async def test_search_databases_specific():
    """Test LibGuides database search for specific database."""
    result = await search_databases(search="ProQuest", limit=5)

    assert isinstance(result, str)
    assert "Found" in result or "No databases found" in result


@pytest.mark.asyncio
async def test_search_databases_all():
    """Test LibGuides database search without filter (all databases)."""
    result = await search_databases(limit=10)

    assert isinstance(result, str)
    assert "Found" in result
    # Should return some databases (not "Found 0 databases")
    assert not result.startswith("Found 0")


@pytest.mark.asyncio
async def test_search_databases_with_limit():
    """Test LibGuides database search with different limit."""
    result = await search_databases(search="science", limit=3)

    assert isinstance(result, str)
    assert "Found" in result or "No databases found" in result


@pytest.mark.asyncio
async def test_search_guides_basic():
    """Test basic LibGuides research guide search."""
    result = await search_guides(search="english", limit=5)

    assert isinstance(result, str)
    assert "Found" in result or "No guides found" in result
    # Should not be an error message
    assert "error occurred" not in result.lower()


@pytest.mark.asyncio
async def test_search_guides_by_subject():
    """Test LibGuides research guide search by subject."""
    result = await search_guides(search="history", limit=5)

    assert isinstance(result, str)
    assert "Found" in result or "No guides found" in result
    # Common subject should have guides
    if "Found" in result and "0 guide" not in result:
        assert "Guide URL:" in result or "URL:" in result


@pytest.mark.asyncio
async def test_search_guides_with_pages():
    """Test that LibGuides guides include page information."""
    result = await search_guides(search="research", limit=3)

    assert isinstance(result, str)
    assert "Found" in result or "No guides found" in result
    # If guides found, they should have pages
    if "Found" in result and "0 guide" not in result:
        # Pages/tabs should be listed
        assert "Pages" in result or "tabs" in result or len(result) > 100


@pytest.mark.asyncio
async def test_search_guides_all():
    """Test LibGuides guide search without filter (all guides)."""
    result = await search_guides(limit=5)

    assert isinstance(result, str)
    assert "Found" in result
    # Should return some guides
    assert "0 guide" not in result


@pytest.mark.asyncio
async def test_search_guides_specific_course():
    """Test LibGuides guide search for course guides."""
    result = await search_guides(search="ENG 101", limit=5)

    assert isinstance(result, str)
    assert "Found" in result or "No guides found" in result
    # Course guides might or might not exist
    assert "error occurred" not in result.lower()


@pytest.mark.asyncio
async def test_search_guides_by_id():
    """Test LibGuides guide search by specific guide ID.

    Note: This test uses a placeholder ID and may need adjustment
    based on actual guide IDs in the system.
    """
    # Try searching with guide_id if available
    # This test might fail if the ID doesn't exist - that's okay
    result = await search_guides(guide_id=1, limit=1)

    assert isinstance(result, str)
    # Should either find the guide or return "not found"
    assert "Found" in result or "No guides found" in result or "error" in result.lower()


@pytest.mark.asyncio
async def test_search_databases_empty_results():
    """Test LibGuides database search that should return no results."""
    result = await search_databases(
        search="xyzabc123nonexistentdatabase999",
        limit=5
    )

    assert isinstance(result, str)
    assert "No databases found" in result or "Found 0" in result


@pytest.mark.asyncio
async def test_search_guides_empty_results():
    """Test LibGuides guide search that should return no results."""
    result = await search_guides(
        search="xyzabc123nonexistentguide999",
        limit=5
    )

    assert isinstance(result, str)
    assert "No guides found" in result or "Found 0" in result
